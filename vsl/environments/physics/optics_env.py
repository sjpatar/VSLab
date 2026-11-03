import math
import pygame
from pygame.math import Vector2

from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.core.optics_solver import OpticsSolver

# Use our new modularized imports
from vsl.components.optics import (
    LaserEmitter,
    LampEmitter,
    MirrorElement,
    LensElement,
    PrismElement,
    ScreenElement,
)

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

class OpticsEnvironment(BaseEnvironment):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.background_color = (16, 20, 28)
        self.grid_color = (34, 42, 56)
        self.play_rect = pygame.Rect(0, 0, app_ref.screen.get_width(), app_ref.screen.get_height() - 60)
        self.toolbar = Toolbar(0, app_ref.screen.get_height() - 60, app_ref.screen.get_width(), 60, self.build_tool_defs())
        
        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 15, bold=True)
        self.caption_font = pygame.font.SysFont("Arial", 14)
        self.mono_font = pygame.font.SysFont("Consolas", 13, bold=True)

        self.current_tool = "select"
        self.solver = OpticsSolver()
        self.ray_segments = []
        self.needs_retrace = True
        self.last_time = pygame.time.get_ticks() / 1000.0
        self.objects = []
        
        # UI Hitboxes
        self.btn_shape_left_rect = None
        self.btn_shape_right_rect = None
        self.btn_ior_down_rect = None
        self.btn_ior_up_rect = None
        
        self.populate_default_scene()
        self.set_mode("select")

    def build_tool_defs(self):
        return [
            ("Select", "select_tool", (132, 154, 184), "Move and rotate optical components"),
            ("Laser", "spawn_laser", (232, 92, 92), "Add a laser emitter"),
            ("Lamp", "spawn_lamp", (248, 206, 104), "Add a cone light source"),
            ("Mirror", "spawn_mirror", (160, 200, 255), "Add a reflective mirror"),
            ("Lens", "spawn_lens", (104, 190, 255), "Add a refractive lens"),
            ("Prism", "spawn_prism", (138, 208, 255), "Add a dispersive glass prism"),
            ("Screen", "spawn_screen", (226, 232, 240), "Add a beam screen"),
            ("Delete", "delete_tool", (232, 96, 96), "Delete a component"),
            ("Clear", "clear_scene", (232, 96, 96), "Clear all optical components"),
            ("Menu", "exit_to_menu", (58, 66, 80), "Return to the physics menu"),
        ]

    def populate_default_scene(self):
        width, height = self.app.screen.get_size()
        
        convex = LensElement(width * 0.38, height * 0.44)
        convex.shape_type = "convex"
        
        concave = LensElement(width * 0.55, height * 0.48)
        concave.shape_type = "concave"
        
        self.objects = [
            LampEmitter(86, height * 0.44),
            MirrorElement(width * 0.72, height * 0.62),
            convex,
            concave,
            PrismElement(width * 0.62, height * 0.34),
            ScreenElement(width * 0.87, height * 0.34),
        ]
        self.objects[0].angle = math.radians(-12)
        self.objects[1].angle = math.radians(-26)
        self.objects[1].shape_type = "flat"
        self.objects[5].angle = math.radians(90)

    def update_layout(self, w, h):
        self.play_rect = pygame.Rect(0, 0, w, h - 60)
        self.toolbar.update_layout(x=0, y=h - 60, width=w, height=60)

    def set_mode(self, tool):
        self.current_tool = tool
        active_map = {
            "delete": "delete_tool",
            "select": "select_tool",
            "laser": "spawn_laser",
            "lamp": "spawn_lamp",
            "mirror": "spawn_mirror",
            "lens": "spawn_lens",
            "prism": "spawn_prism",
            "screen": "spawn_screen",
        }
        self.toolbar.set_active_tool(active_map.get(tool, "select_tool"))

    def spawn_point(self):
        width, height = self.play_rect.size
        center = Vector2(width * 0.5, height * 0.44)
        radius = min(180, 24 + len(self.objects) * 12)
        angle = len(self.objects) * 0.72
        return Vector2(center.x + math.cos(angle) * radius, center.y + math.sin(angle) * radius * 0.45)

    def add_object(self, obj):
        self.objects.append(obj)
        self.needs_retrace = True
        self.set_mode("select")

    def handle_ui(self, action):
        spawn = self.spawn_point()
        if action == "select_tool": self.set_mode("select")
        elif action == "spawn_laser": self.add_object(LaserEmitter(spawn.x, spawn.y))
        elif action == "spawn_lamp": self.add_object(LampEmitter(spawn.x, spawn.y))
        elif action == "spawn_mirror": self.add_object(MirrorElement(spawn.x, spawn.y))
        elif action == "spawn_lens": self.add_object(LensElement(spawn.x, spawn.y))
        elif action == "spawn_prism": self.add_object(PrismElement(spawn.x, spawn.y))
        elif action == "spawn_screen": self.add_object(ScreenElement(spawn.x, spawn.y))
        elif action == "delete_tool": self.set_mode("delete" if self.current_tool != "delete" else "select")
        elif action == "clear_scene":
            self.objects.clear()
            self.ray_segments = []
            self.set_mode("select")
        elif action == "exit_to_menu":
            self.app.switch_environment("PhysicsMenu")

    def selected_object(self):
        for obj in reversed(self.objects):
            if getattr(obj, "selected", False):
                return obj
        return None

    def object_under_point(self, point):
        for obj in reversed(self.objects):
            if obj.hit_test(point): return obj
        return None

    def remove_object(self, obj_to_delete):
        if obj_to_delete and obj_to_delete in self.objects:
            self.objects.remove(obj_to_delete)
            self.needs_retrace = True

    def clear_selection(self):
        for obj in self.objects:
            obj.selected = False

    def cycle_shape(self, obj, direction):
        if not hasattr(obj, "shape_type") or obj is None:
            return
        shapes = ["concave", "flat", "convex"]
        current = shapes.index(obj.shape_type) if obj.shape_type in shapes else 1
        obj.shape_type = shapes[(current + direction) % 3]
        if hasattr(obj, "invalidate_geometry"):
            obj.invalidate_geometry()
        self.needs_retrace = True

    def adjust_ior(self, obj, amount):
        if hasattr(obj, "refractive_index"):
            obj.refractive_index = clamp(obj.refractive_index + amount, 1.0, 3.0)
            self.needs_retrace = True

    def handle_event(self, event):
        action = self.toolbar.handle_event(event)
        if action:
            self.handle_ui(action)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            selected = self.selected_object()
            
            # Interactive HUD Actions
            if self.btn_shape_left_rect and self.btn_shape_left_rect.collidepoint(event.pos):
                self.cycle_shape(selected, -1)
                return
            if self.btn_shape_right_rect and self.btn_shape_right_rect.collidepoint(event.pos):
                self.cycle_shape(selected, 1)
                return
            if self.btn_ior_down_rect and self.btn_ior_down_rect.collidepoint(event.pos):
                self.adjust_ior(selected, -0.05)
                return
            if self.btn_ior_up_rect and self.btn_ior_up_rect.collidepoint(event.pos):
                self.adjust_ior(selected, 0.05)
                return

            self.clear_selection()

            if self.current_tool == "delete":
                self.remove_object(self.object_under_point(event.pos))
                return

        if event.type == pygame.MOUSEWHEEL:
            selected = self.selected_object()
            if selected and hasattr(selected, "rotate"):
                selected.rotate(math.radians(event.y * 6))
                self.needs_retrace = True
                return

        if event.type == pygame.KEYDOWN:
            selected = self.selected_object()
            if selected and hasattr(selected, "rotate"):
                if event.key == pygame.K_q:
                    selected.rotate(math.radians(-6))
                    self.needs_retrace = True
                if event.key == pygame.K_e:
                    selected.rotate(math.radians(6))
                    self.needs_retrace = True

        if self.current_tool == "select":
            for obj in reversed(self.objects):
                if obj.handle_event(event):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and obj in self.objects:
                        self.objects.remove(obj)
                        self.objects.append(obj)
                    self.needs_retrace = True
                    break

    def update(self):
        current_time = pygame.time.get_ticks() / 1000.0
        self.last_time = current_time
        for obj in self.objects:
            obj.update()
        any_dragging = any(getattr(obj, "is_dragging", False) for obj in self.objects)
        geometry_changed = any(hasattr(obj, "geometry_dirty") and obj.geometry_dirty() for obj in self.objects)
        if self.needs_retrace or any_dragging or geometry_changed:
            self.ray_segments = self.solver.solve(self.objects, self.play_rect)
            self.needs_retrace = False

    def draw_background(self, surface):
        width, height = self.play_rect.size
        for row in range(height):
            blend = row / max(height - 1, 1)
            color = (int(16 + 18 * blend), int(20 + 14 * blend), int(28 + 28 * blend))
            pygame.draw.line(surface, color, (0, row), (width, row))

        haze = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(haze, (86, 124, 255, 20), pygame.Rect(width * 0.1, height * 0.08, width * 0.8, height * 0.55))
        surface.blit(haze, (0, 0))

        for x in range(0, width, 48):
            pygame.draw.line(surface, self.grid_color, (x, 0), (x, height), 1)
        for y in range(0, height, 48):
            pygame.draw.line(surface, self.grid_color, (0, y), (width, y), 1)

    def draw_rays(self, surface):
        glow_surface = pygame.Surface(self.play_rect.size, pygame.SRCALPHA)
        core_surface = pygame.Surface(self.play_rect.size, pygame.SRCALPHA)
        for segment in self.ray_segments:
            color = segment["color"]
            intensity = clamp(segment["intensity"], 0.0, 1.0)
            start = (segment["start"].x, segment["start"].y)
            end = (segment["end"].x, segment["end"].y)
            glow_color = (*color, int(36 + 124 * intensity))
            core_color = (*color, int(100 + 140 * intensity))
            pygame.draw.line(glow_surface, glow_color, start, end, max(4, int(8 * intensity)))
            pygame.draw.line(core_surface, core_color, start, end, max(1, int(2 + 2 * intensity)))
        surface.blit(glow_surface, (0, 0))
        surface.blit(core_surface, (0, 0))

    def draw_hud(self, surface):
        card = pygame.Rect(18, 18, 354, 124)
        overlay = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(overlay, (12, 16, 24, 220), overlay.get_rect(), border_radius=14)
        pygame.draw.rect(overlay, (72, 88, 108), overlay.get_rect(), 1, border_radius=14)
        surface.blit(overlay, card.topleft)

        surface.blit(self.title_font.render("Optics Lab", True, (244, 247, 252)), (card.x + 16, card.y + 12))
        subtitle = self.caption_font.render("Trace and disperse light through mirrors, lenses, prisms, and screens.", True, (180, 192, 208))
        surface.blit(subtitle, (card.x + 16, card.y + 46))
        surface.blit(self.hud_font.render(f"Objects: {len(self.objects)}", True, (226, 232, 240)), (card.x + 16, card.y + 74))
        surface.blit(self.hud_font.render("Rotate selected: mouse wheel or Q / E", True, (226, 232, 240)), (card.x + 16, card.y + 94))

        # Reset Interactive Hitboxes
        self.btn_shape_left_rect = None
        self.btn_shape_right_rect = None
        self.btn_ior_down_rect = None
        self.btn_ior_up_rect = None

        selected = self.selected_object()
        
        if selected:
            # Dynamically size HUD based on available properties
            has_shape = hasattr(selected, "shape_type")
            has_ior = hasattr(selected, "refractive_index")
            stats_height = 80 + (32 if has_shape else 0) + (32 if has_ior else 0)
            
            stats_rect = pygame.Rect(18, 152, 282, stats_height)
            stats = pygame.Surface(stats_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(stats, (12, 16, 24, 208), stats.get_rect(), border_radius=14)
            pygame.draw.rect(stats, (72, 88, 108), stats.get_rect(), 1, border_radius=14)
            surface.blit(stats, stats_rect.topleft)
            
            label = getattr(selected, "label", selected.__class__.__name__.replace("Element", ""))
            surface.blit(self.hud_font.render(label, True, (244, 247, 252)), (stats_rect.x + 14, stats_rect.y + 12))
            
            current_y = stats_rect.y + 40
            angle_str = f"Angle: {math.degrees(getattr(selected, 'angle', 0.0)):6.1f} deg"
            surface.blit(self.mono_font.render(angle_str, True, (184, 196, 214)), (stats_rect.x + 14, current_y))
            current_y += 24

            if hasattr(selected, "hits"):
                flux_str = f"Hits: {len(selected.hits):3d}  Peak: {getattr(selected, 'peak_intensity', 0.0):4.2f}"
                surface.blit(self.mono_font.render(flux_str, True, (184, 196, 214)), (stats_rect.x + 14, current_y))
                current_y += 24
                energy_str = f"Flux: {getattr(selected, 'total_intensity', 0.0):5.2f}"
                surface.blit(self.mono_font.render(energy_str, True, (184, 196, 214)), (stats_rect.x + 14, current_y))
                current_y += 24

            # Interactive Shape Chooser
            if has_shape:
                self.btn_shape_left_rect = pygame.Rect(stats_rect.x + 14, current_y, 24, 24)
                self.btn_shape_right_rect = pygame.Rect(stats_rect.x + 148, current_y, 24, 24)
                
                pygame.draw.rect(surface, (100, 120, 140), self.btn_shape_left_rect, border_radius=4)
                pygame.draw.rect(surface, (100, 120, 140), self.btn_shape_right_rect, border_radius=4)
                surface.blit(self.hud_font.render("<", True, (255, 255, 255)), (self.btn_shape_left_rect.x + 6, self.btn_shape_left_rect.y + 2))
                surface.blit(self.hud_font.render(">", True, (255, 255, 255)), (self.btn_shape_right_rect.x + 6, self.btn_shape_right_rect.y + 2))
                
                shape_str = f"{selected.shape_type.capitalize()}"
                surface.blit(self.mono_font.render(f"Type: {shape_str:^9}", True, (255, 230, 140)), (stats_rect.x + 44, current_y + 4))
                current_y += 32

            # Interactive Index of Refraction Chooser
            if has_ior:
                self.btn_ior_down_rect = pygame.Rect(stats_rect.x + 14, current_y, 24, 24)
                self.btn_ior_up_rect = pygame.Rect(stats_rect.x + 148, current_y, 24, 24)
                
                pygame.draw.rect(surface, (230, 96, 96), self.btn_ior_down_rect, border_radius=4)
                pygame.draw.rect(surface, (84, 214, 112), self.btn_ior_up_rect, border_radius=4)
                surface.blit(self.hud_font.render("-", True, (255, 255, 255)), (self.btn_ior_down_rect.x + 8, self.btn_ior_down_rect.y + 2))
                surface.blit(self.hud_font.render("+", True, (255, 255, 255)), (self.btn_ior_up_rect.x + 6, self.btn_ior_up_rect.y + 2))
                
                ior_str = f"IOR:   {selected.refractive_index:4.2f}"
                surface.blit(self.mono_font.render(ior_str, True, (255, 230, 140)), (stats_rect.x + 44, current_y + 4))

    def render(self, surface):
        self.draw_background(surface)
        self.draw_rays(surface)
        for obj in self.objects:
            obj.render(surface)
        self.draw_hud(surface)
