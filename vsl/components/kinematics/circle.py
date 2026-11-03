import math
import pygame
from pygame.math import Vector2
from vsl.components.kinematics.block import PhysicsBlock
from vsl.components.kinematics.utils import draw_drop_shadow

class PhysicsCircle(PhysicsBlock):
    def __init__(self, x: float, y: float, radius: int = 28, mass: float = 10.0):
        self.radius = radius
        self.base_radius = radius
        super().__init__(
            x, y, radius * 2, radius * 2, mass,
            fill_color=(52, 173, 132), edge_color=(18, 98, 76),
            accent_color=(236, 255, 247), material_name="Polymer Sphere"
        )
        self.radius = radius
        self.recompute_mass_properties()
        self.restitution = 0.78
        self.surface_friction = 0.18
        self.dynamic_friction = 0.10
        self.static_friction = 0.16
        self.air_drag = 0.015
        self.angular_drag = 0.03

    def compute_inertia(self) -> float:
        return 0.5 * self.mass * (self.radius ** 2)

    def contains_point(self, point) -> bool:
        return self.get_center().distance_to(Vector2(point)) <= self.radius

    def get_vertices(self) -> list:
        return []

    def apply_mass_visual_scale(self):
        if math.isinf(self.mass) or self.mass <= 0:
            return

        scale = max(0.82, min(1.8, (self.mass / self.base_mass) ** 0.18))
        center = self.get_center()
        self.radius = max(16, int(round(self.base_radius * scale)))
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.pos = Vector2(center.x - self.radius, center.y - self.radius)
        self.rect.width = self.width
        self.rect.height = self.height
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def render(self, surface: pygame.Surface):
        center = (int(self.get_center().x), int(self.get_center().y))
        draw_drop_shadow(surface, "circle", center=center, radius=self.radius)

        pygame.draw.circle(surface, self.fill_color, center, self.radius)
        pygame.draw.circle(surface, self.highlight_color, (center[0] - int(self.radius * 0.28), center[1] - int(self.radius * 0.32)), max(8, self.radius // 3))
        pygame.draw.circle(surface, self.edge_color, center, self.radius, 3)

        stripe_end = (
            int(center[0] + math.cos(self.angle) * (self.radius - 3)),
            int(center[1] + math.sin(self.angle) * (self.radius - 3)),
        )
        pygame.draw.line(surface, self.accent_color, center, stripe_end, 3)
        pygame.draw.circle(surface, self.accent_color, center, 4)

        if self.selected or self.is_dragging:
            pygame.draw.circle(surface, self.selection_color, center, self.radius + 5, 3)

        self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
