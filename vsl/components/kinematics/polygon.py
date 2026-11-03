import math
import pygame
from pygame.math import Vector2
from vsl.components.kinematics.block import PhysicsBlock
from vsl.components.kinematics.utils import draw_drop_shadow

class RegularPolygon(PhysicsBlock):
    def __init__(self, x: float, y: float, radius: int = 34, sides: int = 6, mass: float = 10.0):
        super().__init__(
            x, y, radius * 2, radius * 2, mass,
            fill_color=(184, 124, 220), edge_color=(110, 64, 142),
            accent_color=(255, 240, 255), material_name="Composite Polygon"
        )
        self.radius = radius
        self.sides = max(3, sides)
        self.inertia = (0.5 * self.mass * (self.radius ** 2)) * 1.5 
        self.inv_inertia = 1.0 / self.inertia if self.inertia > 0 else 0.0
        self.restitution = 0.2

    def get_vertices(self) -> list[Vector2]:
        center = self.get_center()
        vertices = []
        angle_step = (2 * math.pi) / self.sides
        for index in range(self.sides):
            current_angle = self.angle + index * angle_step
            vertices.append(
                Vector2(
                    center.x + math.cos(current_angle) * self.radius,
                    center.y + math.sin(current_angle) * self.radius,
                )
            )
        return vertices

    def render(self, surface: pygame.Surface):
        points = [(vertex.x, vertex.y) for vertex in self.get_vertices()]
        draw_drop_shadow(surface, "polygon", points=points)
        pygame.draw.polygon(surface, self.fill_color, points)
        pygame.draw.polygon(surface, self.edge_color, points, 3)
        if points:
            center = self.get_center()
            pygame.draw.line(surface, self.accent_color, (center.x, center.y), points[0], 3)
            pygame.draw.circle(surface, self.accent_color, (int(center.x), int(center.y)), 4)
        if self.selected or self.is_dragging:
            pygame.draw.polygon(surface, self.selection_color, points, 3)
        self.rect.x, self.rect.y = int(self.pos.x), int(self.pos.y)