import math
import pygame
from pygame.math import Vector2
from vsl.components.kinematics.block import PhysicsBlock
from vsl.components.kinematics.utils import draw_drop_shadow, draw_polyline

class PhysicsWedge(PhysicsBlock):
    def __init__(self, x: float, y: float, width: int = 240, height: int = 120, mass: float = 10.0):
        super().__init__(
            x, y, width, height, mass,
            fill_color=(118, 132, 154), edge_color=(60, 72, 92),
            accent_color=(220, 230, 255), material_name="Steel Ramp"
        )
        self.restitution = 0.04
        self.surface_friction = 0.72
        self.dynamic_friction = 0.52
        self.static_friction = 0.68
        self.air_drag = 0.0
        self.angular_drag = 0.0
        self.recompute_mass_properties()
        
    def get_center(self) -> Vector2:
        return Vector2(self.pos.x + self.width / 3.0, self.pos.y + (2.0 * self.height / 3.0))

    def compute_inertia(self) -> float:
        return (self.mass / 18.0) * (self.width ** 2 + self.height ** 2)

    def get_vertices(self) -> list[Vector2]:
        center = self.get_center()
        corners = [
            Vector2(-self.width / 3.0, self.height / 3.0),
            Vector2(2.0 * self.width / 3.0, self.height / 3.0),
            Vector2(-self.width / 3.0, -2.0 * self.height / 3.0),
        ]

        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        vertices = []
        for corner in corners:
            rotated_x = corner.x * cos_a - corner.y * sin_a
            rotated_y = corner.x * sin_a + corner.y * cos_a
            vertices.append(Vector2(center.x + rotated_x, center.y + rotated_y))
        return vertices

    def render(self, surface: pygame.Surface):
        points = [(vertex.x, vertex.y) for vertex in self.get_vertices()]
        draw_drop_shadow(surface, "polygon", points=points)
        pygame.draw.polygon(surface, self.fill_color, points)
        pygame.draw.polygon(surface, self.edge_color, points, 3)
        draw_polyline(surface, self.highlight_color, [points[2], points[1]], 4)
        if self.selected or self.is_dragging:
            pygame.draw.polygon(surface, self.selection_color, points, 3)
        self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)
