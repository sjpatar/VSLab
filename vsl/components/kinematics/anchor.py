import pygame
from pygame.math import Vector2
from vsl.core.experiment_base import LabObject
from vsl.components.kinematics.utils import draw_drop_shadow

class Anchor(LabObject):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 28, 28)
        self.pos = Vector2(x + 14, y + 14)
        self.is_static = True
        self.mass = float("inf")
        self.inv_mass = 0.0
        self.vel = Vector2(0, 0)
        self.angular_vel = 0.0
        self.inv_inertia = 0.0
        self.restitution = 0.02
        self.surface_friction = 0.74
        self.dynamic_friction = 0.55
        self.static_friction = 0.68
        self.material_name = "Fixed Anchor"
        self.selection_color = (112, 212, 255)

    def get_center(self):
        return Vector2(self.rect.center)

    def get_link_anchor(self):
        return self.get_center()

    def contains_point(self, point) -> bool:
        return self.get_center().distance_to(Vector2(point)) <= 14

    def update(self):
        if self.is_dragging:
            self.pos = Vector2(self.rect.center)

    def render(self, surface: pygame.Surface):
        center = self.rect.center
        draw_drop_shadow(surface, "circle", center=center, radius=14, alpha=110)
        pygame.draw.circle(surface, (88, 96, 108), center, 14)
        pygame.draw.circle(surface, (156, 164, 176), center, 9)
        pygame.draw.circle(surface, (34, 38, 44), center, 5)
        pygame.draw.circle(surface, (210, 214, 220), center, 2)
        if self.selected or self.is_dragging:
            pygame.draw.circle(surface, self.selection_color, center, 18, 3)
