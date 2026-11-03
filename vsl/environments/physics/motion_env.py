import math
import pygame
from pygame.math import Vector2

from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.components.kinematics import (
    PhysicsBlock,
    PhysicsCircle,
    PhysicsWedge,
    Anchor,
    Rope,
)
from vsl.core.kinematics_solver import KinematicsSolver
from vsl.core.kinematics_config import (
    FLOOR_HEIGHT_PX,
    METERS_PER_PIXEL,
    PIXELS_PER_METER,
)


class MotionEnvironment(BaseEnvironment):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.background_color = (23, 28, 38)
        self.grid_color = (42, 50, 66)
        self.floor_color = (54, 61, 72)
        self.floor_stripe_color = (72, 81, 94)
        self.toolbar = Toolbar(0, app_ref.screen.get_height() - 60, app_ref.screen.get_width(), 60, self.build_tool_defs())

        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 15, bold=True)
        self.caption_font = pygame.font.SysFont("Arial", 14)
        self.mono_font = pygame.font.SysFont("Consolas", 14, bold=True)

        self.current_tool = "select"
        self.link_mode = None
        self.link_start_obj = None
        self.objects = []
        self.links = []
        self.is_simulating = True

        self.solver = KinematicsSolver()
        self.pixels_per_meter = PIXELS_PER_METER
        self.last_time = pygame.time.get_ticks() / 1000.0

        self.slingshot_target = None
        self.slingshot_pull_pos = None
        self.slingshot_grab_offset = Vector2()
        self.max_slingshot_pull = 2.2 * self.pixels_per_meter
        self.min_launch_speed = 4.0 * self.pixels_per_meter
        self.max_launch_speed = 14.0 * self.pixels_per_meter

        self.btn_mass_down_rect = None
        self.btn_mass_up_rect = None

        self.set_mode("select")

    def build_tool_defs(self):
        return [
            ("Select", "select_tool", (132, 154, 184), "Move and arrange objects"),
            ("Ball", "spawn_ball", (64, 188, 140), "Spawn a lively sphere"),
            ("Ramp", "spawn_wedge", (108, 132, 180), "Spawn a static ramp"),
            ("Anchor", "spawn_anchor", (216, 86, 86), "Spawn a fixed anchor"),
            ("Slingshot", "toggle_slingshot", (240, 152, 72), "Pull back and launch an object"),
            ("Rope", "toggle_rope", (180, 144, 108), "Connect two objects with a rope"),
            ("Play/Pause", "toggle_sim", (84, 214, 112), "Pause or resume the world"),
            ("Delete", "delete_tool", (230, 96, 96), "Delete an object"),
            ("Clear", "clear_scene", (230, 96, 96), "Clear the scene"),
            ("Menu", "exit_to_menu", (58, 66, 80), "Return to the physics menu"),
        ]

    def update_layout(self, w, h):
        self.toolbar.update_layout(x=0, y=h - 60, width=w, height=60)

    def set_mode(self, tool="select", *, link_mode=None):
        self.current_tool = tool
        self.link_mode = link_mode
        self.link_start_obj = None
        self.slingshot_target = None
        self.slingshot_pull_pos = None
        self.slingshot_grab_offset = Vector2()

        if link_mode == "rope":
            active_tool = "toggle_rope"
        elif tool == "slingshot":
            active_tool = "toggle_slingshot"
        elif tool == "delete":
            active_tool = "delete_tool"
        else:
            active_tool = "select_tool"

        self.toolbar.set_active_tool(active_tool)

    def spawn_point(self):
        width, height = self.app.screen.get_size()
        center = Vector2(width * 0.5, height * 0.32)
        count = len(self.objects)
        angle = count * 0.85
        radius = min(160, 18 + count * 10)
        return Vector2(center.x + math.cos(angle) * radius, center.y + math.sin(angle) * radius * 0.55)

    def add_object(self, obj):
        self.objects.append(obj)
        if hasattr(obj, "wake"):
            obj.wake()

    def selected_object(self):
        return next((obj for obj in reversed(self.objects) if getattr(obj, "selected", False)), None)

    def clear_selection(self):
        for obj in self.objects:
            obj.selected = False

    def object_under_point(self, point, *, dynamic_only=False):
        for obj in reversed(self.objects):
            if dynamic_only and getattr(obj, "is_static", False):
                continue
            if obj.hit_test(point):
                return obj
        return None

    def remove_object(self, obj_to_delete):
        if not obj_to_delete:
            return
        if obj_to_delete in self.objects:
            self.objects.remove(obj_to_delete)
        self.links = [link for link in self.links if link.obj_a != obj_to_delete and link.obj_b != obj_to_delete]
        if self.link_start_obj == obj_to_delete:
            self.link_start_obj = None
        if self.slingshot_target == obj_to_delete:
            self.slingshot_target = None
            self.slingshot_pull_pos = None
            self.slingshot_grab_offset = Vector2()
        if getattr(obj_to_delete, "selected", False):
            obj_to_delete.selected = False

    def link_exists(self, obj_a, obj_b, link_type):
        return any(
            isinstance(link, link_type)
            and ((link.obj_a == obj_a and link.obj_b == obj_b) or (link.obj_a == obj_b and link.obj_b == obj_a))
            for link in self.links
        )

    def update_object_mass(self, obj, new_mass):
        if getattr(obj, "is_static", False):
            return

        obj.mass = max(1.0, min(new_mass, 999.0))
        if hasattr(obj, "apply_mass_visual_scale"):
            obj.apply_mass_visual_scale()
        if hasattr(obj, "recompute_mass_properties"):
            obj.recompute_mass_properties()
        else:
            obj.inv_mass = 1.0 / obj.mass

        if hasattr(obj, "wake"):
            obj.wake()

    def object_world_bounds(self, obj):
        if isinstance(obj, PhysicsCircle):
            center = obj.get_center()
            return (
                center.x - obj.radius,
                center.y - obj.radius,
                center.x + obj.radius,
                center.y + obj.radius,
            )
        if isinstance(obj, PhysicsBlock):
            return self.solver.get_world_bounds(obj)
        return (
            obj.rect.left,
            obj.rect.top,
            obj.rect.right,
            obj.rect.bottom,
        )

    def camera_frame_bounds(self, viewport_width, viewport_height):
        padding = 44.0
        min_left = 0.0
        min_top = 0.0
        max_right = float(viewport_width)
        max_bottom = float(viewport_height)
        for obj in self.objects:
            left, top, right, bottom = self.object_world_bounds(obj)
            min_left = min(min_left, left - padding)
            min_top = min(min_top, top - padding)
            max_right = max(max_right, right + padding)
            max_bottom = max(max_bottom, bottom + padding)
        return min_left, min_top, max_right, max_bottom

    def shifted_world_render(self, surface, offset):
        if offset.length_squared() <= 1e-6:
            self.draw_background(surface)
            self.draw_floor(surface)
            for link in self.links:
                link.render(surface)
            self.render_link_preview(surface)
            self.render_slingshot_preview(surface)
            static_objects = [obj for obj in self.objects if getattr(obj, "is_static", False)]
            dynamic_objects = [obj for obj in self.objects if not getattr(obj, "is_static", False)]
            for obj in static_objects + dynamic_objects:
                obj.render(surface)
            return

        saved_state = []
        for obj in self.objects:
            pos = Vector2(obj.pos) if hasattr(obj, "pos") else None
            rect = obj.rect.copy()
            saved_state.append((obj, pos, rect))
            if pos is not None:
                obj.pos += offset
            obj.rect = obj.rect.move(int(round(offset.x)), int(round(offset.y)))

        saved_pull = Vector2(self.slingshot_pull_pos) if self.slingshot_pull_pos is not None else None
        if self.slingshot_pull_pos is not None:
            self.slingshot_pull_pos += offset

        try:
            self.draw_background(surface)
            self.draw_floor(surface, floor_y=(self.app.screen.get_height() - FLOOR_HEIGHT_PX) + offset.y)
            for link in self.links:
                link.render(surface)
            self.render_link_preview(surface)
            self.render_slingshot_preview(surface)
            static_objects = [obj for obj in self.objects if getattr(obj, "is_static", False)]
            dynamic_objects = [obj for obj in self.objects if not getattr(obj, "is_static", False)]
            for obj in static_objects + dynamic_objects:
                obj.render(surface)
        finally:
            if saved_pull is not None:
                self.slingshot_pull_pos = saved_pull
            for obj, pos, rect in saved_state:
                if pos is not None:
                    obj.pos = pos
                obj.rect = rect

    def render_world(self, surface):
        viewport_width, viewport_height = surface.get_size()
        min_left, min_top, max_right, max_bottom = self.camera_frame_bounds(viewport_width, viewport_height)
        frame_width = max_right - min_left
        frame_height = max_bottom - min_top

        if frame_width <= viewport_width + 1 and frame_height <= viewport_height + 1:
            self.shifted_world_render(surface, Vector2())
            return

        world_width = max(1, int(math.ceil(frame_width)))
        world_height = max(1, int(math.ceil(frame_height)))
        world_surface = pygame.Surface((world_width, world_height))
        self.shifted_world_render(world_surface, Vector2(-min_left, -min_top))

        zoom = min(viewport_width / world_width, viewport_height / world_height)
        scaled_size = (
            max(1, int(round(world_width * zoom))),
            max(1, int(round(world_height * zoom))),
        )
        scaled = pygame.transform.smoothscale(world_surface, scaled_size)
        surface.fill(self.background_color)
        self.draw_background(surface)
        surface.blit(
            scaled,
            ((viewport_width - scaled_size[0]) // 2, (viewport_height - scaled_size[1]) // 2),
        )

    def handle_ui(self, action):
        spawn = self.spawn_point()

        if action == "select_tool":
            self.set_mode("select")
        elif action == "spawn_ball":
            self.add_object(PhysicsCircle(spawn.x, spawn.y, radius=30, mass=8.0))
            self.set_mode("select")
        elif action == "spawn_wedge":
            ramp = PhysicsWedge(spawn.x - 40, spawn.y + 110, width=280, height=140, mass=100.0)
            ramp.set_static(True)
            self.add_object(ramp)
            self.set_mode("select")
        elif action == "spawn_anchor":
            self.add_object(Anchor(spawn.x, spawn.y - 80))
            self.set_mode("select")
        elif action == "toggle_slingshot":
            self.set_mode("slingshot" if self.current_tool != "slingshot" else "select")
        elif action == "toggle_rope":
            self.set_mode("select", link_mode=None if self.link_mode == "rope" else "rope")
        elif action == "toggle_sim":
            self.is_simulating = not self.is_simulating
            self.last_time = pygame.time.get_ticks() / 1000.0
            if not self.is_simulating:
                self.cancel_transient_actions()
        elif action == "delete_tool":
            self.set_mode("delete" if self.current_tool != "delete" else "select")
        elif action == "clear_scene":
            self.cancel_transient_actions()
            self.objects.clear()
            self.links.clear()
            self.set_mode("select")
        elif action == "exit_to_menu":
            self.cancel_transient_actions()
            self.clear_selection()
            self.app.switch_environment("PhysicsMenu")

    def cancel_transient_actions(self):
        self.link_start_obj = None
        self.slingshot_target = None
        self.slingshot_pull_pos = None
        self.slingshot_grab_offset = Vector2()

    def clamp_pull_vector(self, pull_vector: Vector2) -> Vector2:
        if pull_vector.length_squared() > self.max_slingshot_pull * self.max_slingshot_pull:
            pull_vector.scale_to_length(self.max_slingshot_pull)
        return pull_vector

    def launch_velocity_from_pull(self, pull_vector: Vector2) -> Vector2:
        if pull_vector.length_squared() <= 1e-6:
            return Vector2()
        clamped_pull = self.clamp_pull_vector(Vector2(pull_vector))
        power_ratio = clamp(clamped_pull.length() / self.max_slingshot_pull, 0.0, 1.0)
        strength = self.min_launch_speed + (self.max_launch_speed - self.min_launch_speed) * (power_ratio ** 0.8)
        return clamped_pull.normalize() * strength

    def object_height_above_floor_m(self, obj) -> float:
        floor_y = self.app.screen.get_height() - FLOOR_HEIGHT_PX
        if isinstance(obj, PhysicsCircle):
            bottom = obj.get_center().y + obj.radius
        elif hasattr(obj, "get_vertices"):
            vertices = obj.get_vertices()
            bottom = max((vertex.y for vertex in vertices), default=obj.rect.bottom)
        else:
            bottom = obj.rect.bottom
        return max(0.0, (floor_y - bottom) * METERS_PER_PIXEL)

    def inertia_si(self, obj) -> float:
        inertia = getattr(obj, "inertia", 0.0)
        if math.isinf(inertia):
            return float("inf")
        return inertia * (METERS_PER_PIXEL ** 2)

    def object_stat_lines(self, obj):
        lines = []
        if isinstance(obj, PhysicsCircle):
            lines.append(f"Radius:   {obj.radius * METERS_PER_PIXEL:6.2f} m")
        elif isinstance(obj, PhysicsWedge):
            lines.append(f"Ramp:     {obj.width * METERS_PER_PIXEL:4.2f} x {obj.height * METERS_PER_PIXEL:4.2f} m")
            lines.append(f"Slope:    {math.degrees(math.atan2(obj.height, obj.width)):6.1f} deg")
        elif isinstance(obj, PhysicsBlock):
            lines.append(f"Size:     {obj.width * METERS_PER_PIXEL:4.2f} x {obj.height * METERS_PER_PIXEL:4.2f} m")

        lines.append(f"Height:   {self.object_height_above_floor_m(obj):6.2f} m")
        lines.append(f"                        s/mu_k:{getattr(obj, 'static_friction', 0.0):4.2f}/{getattr(obj, 'dynamic_friction', 0.0):4.2f}")
        return lines

    def attached_link_lines(self, obj):
        ropes = [link for link in self.links if isinstance(link, Rope) and (link.obj_a is obj or link.obj_b is obj)]
        lines = []

        if ropes:
            taut_count = sum(1 for link in ropes if link.is_taut())
            total_slack = sum(link.slack_meters() for link in ropes)
            lines.append(f"Ropes:    {len(ropes):2d}  Taut {taut_count:2d}")
            lines.append(f"Slack:    {total_slack:6.2f} m")

        return lines

    def handle_event(self, event):
        action = self.toolbar.handle_event(event)
        if action:
            self.handle_ui(action)
            return

        if event.type == pygame.MOUSEWHEEL:
            selected = self.selected_object()
            if selected and not getattr(selected, "is_static", False):
                self.update_object_mass(selected, selected.mass + event.y)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.cancel_transient_actions()
            if self.current_tool != "select" or self.link_mode:
                self.set_mode("select")
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            selected = self.selected_object()

            if self.btn_mass_down_rect and self.btn_mass_down_rect.collidepoint(event.pos):
                if selected:
                    self.update_object_mass(selected, selected.mass - 1.0)
                return

            if self.btn_mass_up_rect and self.btn_mass_up_rect.collidepoint(event.pos):
                if selected:
                    self.update_object_mass(selected, selected.mass + 1.0)
                return

            self.clear_selection()

            if self.current_tool == "slingshot":
                target = self.object_under_point(event.pos, dynamic_only=True)
                if target:
                    self.slingshot_target = target
                    self.slingshot_pull_pos = Vector2(event.pos)
                    self.slingshot_grab_offset = Vector2(event.pos) - target.get_link_anchor()
                    target.vel = Vector2(0, 0)
                    target.angular_vel = 0.0
                    if hasattr(target, "wake"):
                        target.wake()
                    return

            if self.current_tool == "delete":
                self.remove_object(self.object_under_point(event.pos))
                return

            if self.link_mode:
                clicked_obj = self.object_under_point(event.pos)
                if clicked_obj:
                    if self.link_start_obj is None:
                        self.link_start_obj = clicked_obj
                    elif clicked_obj != self.link_start_obj:
                        start = self.link_start_obj.get_link_anchor()
                        end = clicked_obj.get_link_anchor()
                        distance = (end - start).length()
                        if self.link_mode == "rope":
                            if not self.link_exists(self.link_start_obj, clicked_obj, Rope):
                                self.links.append(Rope(self.link_start_obj, clicked_obj, length=distance))
                        self.link_start_obj = None
                    return
                self.link_start_obj = None
                return

        elif event.type == pygame.MOUSEMOTION and self.current_tool == "slingshot" and self.slingshot_target:
            self.slingshot_pull_pos = Vector2(event.pos)
            return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.current_tool == "slingshot" and self.slingshot_target:
            anchor = self.slingshot_target.get_link_anchor()
            pull_vector = self.clamp_pull_vector(anchor - Vector2(event.pos))
            launch_velocity = self.launch_velocity_from_pull(pull_vector)
            self.slingshot_target.vel = launch_velocity
            inv_mass = getattr(self.slingshot_target, "inv_mass", 0.0)
            if inv_mass > 1e-9 and getattr(self.slingshot_target, "inv_inertia", 0.0) > 0.0:
                launch_impulse = launch_velocity / inv_mass
                delta_omega = self.slingshot_grab_offset.cross(launch_impulse) * self.slingshot_target.inv_inertia
                self.slingshot_target.angular_vel += delta_omega
            if hasattr(self.slingshot_target, "wake"):
                self.slingshot_target.wake()
            self.slingshot_target = None
            self.slingshot_pull_pos = None
            self.slingshot_grab_offset = Vector2()
            return

        if self.current_tool == "select" and self.link_mode is None:
            for obj in reversed(self.objects):
                if obj.handle_event(event):
                    break

    def update(self):
        current_time = pygame.time.get_ticks() / 1000.0
        frame_time = current_time - self.last_time
        self.last_time = current_time

        for obj in self.objects:
            obj.update()

        floor_y = self.app.screen.get_height() - FLOOR_HEIGHT_PX
        screen_width = self.app.screen.get_width()

        if self.is_simulating:
            self.solver.solve(self.objects, self.links, frame_time, screen_width, floor_y)
        else:
            for obj in self.objects:
                if isinstance(obj, PhysicsBlock):
                    if obj.is_dragging:
                        obj.pos.x, obj.pos.y = obj.rect.x, obj.rect.y
                        obj.last_pos = Vector2(obj.pos)
                    obj.vel *= 0.0
                    obj.angular_vel = 0.0
            self.solver.accumulator = 0.0

    def draw_background(self, surface):
        width, height = surface.get_size()
        for row in range(height):
            blend = row / max(height - 1, 1)
            color = (
                int(23 + 24 * blend),
                int(28 + 22 * blend),
                int(38 + 18 * blend),
            )
            pygame.draw.line(surface, color, (0, row), (width, row))

        spotlight = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(spotlight, (180, 220, 255, 18), pygame.Rect(width * 0.14, height * 0.06, width * 0.72, height * 0.45))
        surface.blit(spotlight, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.grid_color, (x, 0), (x, height), 1)
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.grid_color, (0, y), (width, y), 1)

    def draw_floor(self, surface, floor_y=None):
        if floor_y is None:
            floor_y = surface.get_height() - FLOOR_HEIGHT_PX
        floor_rect = pygame.Rect(0, floor_y, surface.get_width(), FLOOR_HEIGHT_PX)
        pygame.draw.rect(surface, self.floor_color, floor_rect)
        pygame.draw.line(surface, (122, 222, 156), (0, floor_y), (surface.get_width(), floor_y), 4)
        for stripe_x in range(-40, surface.get_width() + 80, 54):
            pygame.draw.line(surface, self.floor_stripe_color, (stripe_x, floor_y + FLOOR_HEIGHT_PX), (stripe_x + 54, floor_y), 2)
        return floor_y

    def render_link_preview(self, surface):
        if self.link_mode and self.link_start_obj:
            mouse_pos = pygame.mouse.get_pos()
            start = self.link_start_obj.get_link_anchor()
            color = (208, 190, 164)
            pygame.draw.line(surface, color, (start.x, start.y), mouse_pos, 3)
            pygame.draw.circle(surface, color, (int(start.x), int(start.y)), 7, 2)

    def render_slingshot_preview(self, surface):
        if not (self.current_tool == "slingshot" and self.slingshot_target and self.slingshot_pull_pos):
            return

        anchor = self.slingshot_target.get_link_anchor()
        pull_pos = Vector2(self.slingshot_pull_pos)
        pull_vector = self.clamp_pull_vector(anchor - pull_pos)
        pouch = anchor - pull_vector
        direction = pull_vector.normalize() if pull_vector.length_squared() > 1e-6 else Vector2(1, 0)
        normal = Vector2(-direction.y, direction.x)
        radius = getattr(self.slingshot_target, "radius", max(self.slingshot_target.width, self.slingshot_target.height) * 0.35)

        attach_left = anchor + normal * radius
        attach_right = anchor - normal * radius
        pygame.draw.line(surface, (112, 66, 44), (attach_left.x, attach_left.y), (pouch.x, pouch.y), 5)
        pygame.draw.line(surface, (112, 66, 44), (attach_right.x, attach_right.y), (pouch.x, pouch.y), 5)
        pygame.draw.circle(surface, (176, 112, 72), (int(pouch.x), int(pouch.y)), 11)
        pygame.draw.circle(surface, (252, 214, 166), (int(pouch.x), int(pouch.y)), 4)

        preview_velocity = self.launch_velocity_from_pull(pull_vector)
        preview_pos = Vector2(anchor)
        preview_step = 1.0 / 30.0
        for step in range(1, 19):
            t = preview_step * step
            point = preview_pos + preview_velocity * t + 0.5 * self.solver.gravity * (t * t) * getattr(self.slingshot_target, "gravity_scale", 1.0)
            alpha = max(30, 180 - step * 8)
            dot_surface = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, (112, 212, 255, alpha), (5, 5), max(2, 5 - step // 5))
            surface.blit(dot_surface, (point.x - 5, point.y - 5))

        power_ratio = clamp(pull_vector.length() / self.max_slingshot_pull, 0.0, 1.0)
        self.draw_meter(surface, 20, surface.get_height() - 154, 172, 18, power_ratio, "Launch")

    def draw_meter(self, surface, x, y, width, height, ratio, label):
        pygame.draw.rect(surface, (24, 29, 36), (x, y, width, height), border_radius=8)
        pygame.draw.rect(surface, (82, 92, 110), (x, y, width, height), 1, border_radius=8)
        fill_width = int((width - 4) * clamp(ratio, 0.0, 1.0))
        fill_color = (92, 196, 255) if ratio < 0.7 else (255, 182, 92)
        pygame.draw.rect(surface, fill_color, (x + 2, y + 2, fill_width, height - 4), border_radius=6)
        label_surface = self.caption_font.render(label, True, (226, 232, 240))
        surface.blit(label_surface, (x, y - 18))

    def render_hud(self, surface):
        pad = 16
        card = pygame.Rect(18, 18, 360, 128)
        overlay = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(overlay, (13, 18, 25, 220), overlay.get_rect(), border_radius=14)
        pygame.draw.rect(overlay, (70, 82, 98, 255), overlay.get_rect(), 1, border_radius=14)
        surface.blit(overlay, card.topleft)

        content_x = card.x + pad
        surface.blit(self.title_font.render("Motion Lab", True, (242, 247, 252)), (content_x, card.y + 12))
        subtitle = self.caption_font.render("Build, launch, collide, and measure rigid-body systems.", True, (176, 188, 204))
        surface.blit(subtitle, (content_x, card.y + 46))

        mode_label = "Rope Link" if self.link_mode == "rope" else self.current_tool.title()
        sim_label = "Running" if self.is_simulating else "Paused"
        hud_lines = [
            f"Mode: {mode_label}",
            f"Simulation: {sim_label}",
            f"Objects: {len(self.objects)}    Links: {len(self.links)}",
        ]
        for index, line in enumerate(hud_lines):
            surface.blit(self.hud_font.render(line, True, (226, 232, 240)), (content_x, card.y + 74 + index * 18))

        self.btn_mass_down_rect = None
        self.btn_mass_up_rect = None

        selected = self.selected_object()

        if selected:
            stat_lines = []
            if getattr(selected, "is_static", False):
                stat_lines.extend(self.object_stat_lines(selected))
                stat_lines.append("Fixed Object - Infinite Mass")
            else:
                speed_px = getattr(selected, "vel", Vector2()).length()
                speed = speed_px * METERS_PER_PIXEL
                accel = getattr(selected, "acc", Vector2()).length() * METERS_PER_PIXEL
                angular = abs(getattr(selected, "angular_vel", 0.0))
                mass = getattr(selected, "mass", 0.0)
                inertia_si = self.inertia_si(selected)
                linear_ke = 0.5 * mass * (speed ** 2)
                rotational_ke = 0.0 if math.isinf(inertia_si) else 0.5 * inertia_si * (angular ** 2)
                grav_pe = mass * 9.81 * self.object_height_above_floor_m(selected)
                angular_momentum = 0.0 if math.isinf(inertia_si) else inertia_si * angular

                stat_lines.extend(self.object_stat_lines(selected))
                stat_lines.extend([
                    f"Speed:    {speed:6.2f} m/s",
                    f"Accel:    {accel:6.2f} m/s2",
                    f"Spin:     {angular:6.2f} rad/s",
                    f"Inertia:  {inertia_si:6.3f} kg*m2",
                    f"Momentum: {mass * speed:6.2f} kg*m/s",
                    f"Ang Mom:  {angular_momentum:6.2f} kg*m2/s",
                    f"Lin KE:   {linear_ke:6.2f} J",
                    f"Rot KE:   {rotational_ke:6.2f} J",
                    f"Grav PE:  {grav_pe:6.2f} J",
                ])

            stat_lines.extend(self.attached_link_lines(selected))

            mass_controls_height = 38 if not getattr(selected, "is_static", False) else 0
            stats_rect = pygame.Rect(18, 154, 352, 70 + mass_controls_height + len(stat_lines) * 22)
            stats_surface = pygame.Surface(stats_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(stats_surface, (13, 18, 25, 210), stats_surface.get_rect(), border_radius=14)
            pygame.draw.rect(stats_surface, (70, 82, 98, 255), stats_surface.get_rect(), 1, border_radius=14)
            surface.blit(stats_surface, stats_rect.topleft)

            title_text = getattr(selected, "material_name", selected.__class__.__name__)
            stats_x = stats_rect.x + pad
            surface.blit(self.hud_font.render(title_text, True, (242, 247, 252)), (stats_x, stats_rect.y + 12))

            if not getattr(selected, "is_static", False):
                mass_y = stats_rect.y + 42
                self.btn_mass_down_rect = pygame.Rect(stats_x, mass_y, 34, 28)
                self.btn_mass_up_rect = pygame.Rect(stats_rect.right - pad - 34, mass_y, 34, 28)

                pygame.draw.rect(surface, (230, 96, 96), self.btn_mass_down_rect, border_radius=6)
                surface.blit(self.hud_font.render("-", True, (255, 255, 255)), (self.btn_mass_down_rect.x + 12, self.btn_mass_down_rect.y + 3))

                pygame.draw.rect(surface, (84, 214, 112), self.btn_mass_up_rect, border_radius=6)
                surface.blit(self.hud_font.render("+", True, (255, 255, 255)), (self.btn_mass_up_rect.x + 10, self.btn_mass_up_rect.y + 3))

                mass_text = f"Mass: {getattr(selected, 'mass', 0):>5.1f} kg"
                surface.blit(self.mono_font.render(mass_text, True, (255, 230, 140)), (stats_x + 52, mass_y + 5))
                content_y = mass_y + 42
            else:
                content_y = stats_rect.y + 42

            for index, line in enumerate(stat_lines):
                surface.blit(self.mono_font.render(line, True, (184, 196, 214)), (stats_x, content_y + index * 22))

    def render(self, surface):
        self.render_world(surface)
        self.render_hud(surface)


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))
