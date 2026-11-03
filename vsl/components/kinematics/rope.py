import math
import pygame
from pygame.math import Vector2
from vsl.components.kinematics.utils import clamp, draw_polyline
from vsl.core.kinematics_config import METERS_PER_PIXEL

class Rope:
    def __init__(self, obj_a, obj_b, length=None):
        self.obj_a = obj_a
        self.obj_b = obj_b
        self.length = length if length is not None else self.current_length()

    def endpoints(self):
        return self.obj_a.get_link_anchor(), self.obj_b.get_link_anchor()

    def current_length(self):
        p1, p2 = self.endpoints()
        return (p2 - p1).length()

    def stretch_meters(self):
        return max(0.0, self.current_length() - self.length) * METERS_PER_PIXEL

    def slack_meters(self):
        return max(0.0, self.length - self.current_length()) * METERS_PER_PIXEL

    def is_taut(self):
        return self.current_length() >= self.length - 1e-6

    def solve_constraint(self):
        p1, p2 = self.endpoints()
        diff = p2 - p1
        dist = diff.length()
        if dist <= self.length or dist <= 1e-6:
            return

        direction = diff / dist
        stretch = dist - self.length
        inv_mass_a = 0.0 if getattr(self.obj_a, "is_static", False) else self.obj_a.inv_mass
        inv_mass_b = 0.0 if getattr(self.obj_b, "is_static", False) else self.obj_b.inv_mass
        total_inv_mass = inv_mass_a + inv_mass_b
        if total_inv_mass <= 0:
            return

        correction = direction * stretch
        if not getattr(self.obj_a, "is_static", False):
            self.obj_a.pos += correction * (inv_mass_a / total_inv_mass)
            if hasattr(self.obj_a, "wake"):
                self.obj_a.wake()
        if not getattr(self.obj_b, "is_static", False):
            self.obj_b.pos -= correction * (inv_mass_b / total_inv_mass)
            if hasattr(self.obj_b, "wake"):
                self.obj_b.wake()

    def render(self, surface: pygame.Surface):
        p1, p2 = self.endpoints()
        diff = p2 - p1
        length = diff.length()
        if length <= 1e-6:
            return

        direction = diff.normalize()
        normal = Vector2(-direction.y, direction.x)
        slack = max(self.length - length, 0.0)
        sag_amount = clamp(slack * 0.12, 0.0, 16.0)
        midpoint = (p1 + p2) * 0.5 + normal * math.sin(pygame.time.get_ticks() * 0.001) * 2 + Vector2(0, sag_amount)

        points = []
        for step in range(17):
            t = step / 16
            curve_point = ((1 - t) ** 2) * p1 + 2 * (1 - t) * t * midpoint + (t**2) * p2
            points.append((curve_point.x, curve_point.y))

        draw_polyline(surface, (48, 34, 18), points, 6)
        draw_polyline(surface, (150, 112, 74), points, 2)
