import math
import pygame
from pygame.math import Vector2
from vsl.core.experiment_base import LabObject
from vsl.components.kinematics.utils import lerp_color, draw_drop_shadow, point_in_polygon

class PhysicsBlock(LabObject):
    def __init__(
        self,
        x: float,
        y: float,
        width: int = 64,
        height: int = 64,
        mass: float = 10.0,
        *,
        fill_color=(102, 146, 198),
        edge_color=(48, 78, 122),
        accent_color=(224, 128, 92),
        material_name="Alloy Block",
    ):
        super().__init__(x, y, width, height)
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.acc = Vector2(0, 0)
        self.mass = mass
        self.inv_mass = 1.0 / mass if mass > 0 else 0.0
        self.width = width
        self.height = height
        self.base_mass = max(mass, 1.0)
        self.base_width = width
        self.base_height = height
        
        self.restitution = 0.08
        self.surface_friction = 0.62
        self.dynamic_friction = 0.46
        self.static_friction = 0.58
        self.air_drag = 0.02
        self.angular_drag = 0.08
        self.gravity_scale = 1.0
        self.is_static = False
        self.is_sleeping = False
        self.sleep_timer = 0.0

        self.angle = 0.0
        self.angular_vel = 0.0
        self.angular_acc = 0.0
        self.torque = 0.0

        self.inertia = 0.0
        self.inv_inertia = 0.0
        self.recompute_mass_properties()
        self.last_pos = Vector2(x, y)

        self.fill_color = fill_color
        self.edge_color = edge_color
        self.accent_color = accent_color
        self.highlight_color = lerp_color(fill_color, (255, 255, 255), 0.35)
        self.shadow_color = lerp_color(fill_color, (18, 20, 24), 0.55)
        self.selection_color = (112, 212, 255)
        self.material_name = material_name

    def wake(self):
        self.is_sleeping = False
        self.sleep_timer = 0.0

    def set_static(self, is_static=True):
        self.is_static = is_static
        if is_static:
            self.mass = float("inf")
            self.inv_mass = 0.0
            self.inertia = float("inf")
            self.inv_inertia = 0.0
            self.vel = Vector2(0, 0)
            self.angular_vel = 0.0
        else:
            if math.isinf(self.mass) or self.mass <= 0:
                self.mass = 10.0
            self.recompute_mass_properties()
        self.wake()

    def compute_inertia(self) -> float:
        return (self.mass / 12.0) * (self.width ** 2 + self.height ** 2)

    def recompute_mass_properties(self):
        if math.isinf(self.mass) or self.mass <= 0:
            self.inv_mass = 0.0
            self.inertia = float("inf")
            self.inv_inertia = 0.0
            return

        self.inv_mass = 1.0 / self.mass
        self.inertia = self.compute_inertia()
        self.inv_inertia = 1.0 / self.inertia if self.inertia > 0 else 0.0

    def apply_mass_visual_scale(self):
        if math.isinf(self.mass) or self.mass <= 0:
            return

        scale = max(0.78, min(1.75, (self.mass / self.base_mass) ** 0.18))
        new_width = max(28, int(round(self.base_width * scale)))
        new_height = max(28, int(round(self.base_height * scale)))
        center = self.get_center()
        self.width = new_width
        self.height = new_height
        self.pos = Vector2(center.x - self.width / 2, center.y - self.height / 2)
        self.rect.width = self.width
        self.rect.height = self.height
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def get_center(self) -> Vector2:
        return Vector2(self.pos.x + self.width / 2, self.pos.y + self.height / 2)

    def get_link_anchor(self) -> Vector2:
        return self.get_center()

    def contains_point(self, point) -> bool:
        return point_in_polygon(point, self.get_vertices())

    def get_vertices(self) -> list[Vector2]:
        center = self.get_center()
        half_w, half_h = self.width / 2, self.height / 2
        corners = [Vector2(-half_w, -half_h), Vector2(half_w, -half_h), Vector2(half_w, half_h), Vector2(-half_w, half_h)]
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        vertices = []
        for corner in corners:
            rotated_x = corner.x * cos_a - corner.y * sin_a
            rotated_y = corner.x * sin_a + corner.y * cos_a
            vertices.append(Vector2(center.x + rotated_x, center.y + rotated_y))
        return vertices

    def update(self):
        pass

    def _render_selection(self, surface, points):
        if self.selected or self.is_dragging:
            pygame.draw.polygon(surface, self.selection_color, points, 3)

    def render(self, surface: pygame.Surface):
        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for row in range(self.height):
            tone = row / max(self.height - 1, 1)
            row_color = lerp_color(self.highlight_color, self.fill_color, tone)
            pygame.draw.line(panel, row_color, (0, row), (self.width, row))

        pygame.draw.rect(panel, self.fill_color, (0, 0, self.width, self.height), border_radius=8)
        pygame.draw.rect(panel, self.highlight_color, (4, 4, self.width - 8, max(8, self.height // 5)), border_radius=6)
        pygame.draw.rect(panel, self.edge_color, (0, 0, self.width, self.height), 3, border_radius=8)
        pygame.draw.line(panel, self.shadow_color, (6, self.height - 8), (self.width - 8, self.height - 8), 3)
        bolt_y = max(12, self.height // 2)
        inset = max(12, self.width // 5)
        pygame.draw.circle(panel, self.accent_color, (inset, bolt_y), 4)
        pygame.draw.circle(panel, self.accent_color, (self.width - inset, bolt_y), 4)
        pygame.draw.circle(panel, self.edge_color, (inset, bolt_y), 2)
        pygame.draw.circle(panel, self.edge_color, (self.width - inset, bolt_y), 2)

        rotated = pygame.transform.rotate(panel, math.degrees(-self.angle))
        center = (int(self.get_center().x), int(self.get_center().y))
        rotated_rect = rotated.get_rect(center=center)

        draw_drop_shadow(surface, "rect", rect=rotated_rect)
        surface.blit(rotated, rotated_rect.topleft)
        self._render_selection(surface, [(vertex.x, vertex.y) for vertex in self.get_vertices()])
        self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
