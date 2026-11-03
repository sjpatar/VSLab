import math
import pygame
from pygame.math import Vector2
from vsl.components.kinematics.utils import clamp, lerp_color, draw_polyline
from vsl.core.kinematics_config import (
    DEFAULT_SPRING_DAMPING_N_PER_MS,
    DEFAULT_SPRING_STIFFNESS_N_PER_M,
    METERS_PER_PIXEL,
    PIXELS_PER_METER,
)

class Spring:
    def __init__(self, obj_a, obj_b, k=DEFAULT_SPRING_STIFFNESS_N_PER_M, rest_length=None, damping=DEFAULT_SPRING_DAMPING_N_PER_MS):
        self.obj_a = obj_a
        self.obj_b = obj_b
        self.k = k
        self.damping = damping
        self.rest_length = rest_length if rest_length is not None else self.current_length()
        self.coils = 9

    def endpoints(self):
        return self.obj_a.get_link_anchor(), self.obj_b.get_link_anchor()

    def current_length(self):
        p1, p2 = self.endpoints()
        return (p2 - p1).length()

    def stretch_meters(self):
        return (self.current_length() - self.rest_length) * METERS_PER_PIXEL

    def relative_speed_mps(self):
        p1, p2 = self.endpoints()
        diff = p2 - p1
        dist = diff.length()
        if dist <= 1e-6:
            return 0.0
        direction = diff / dist
        rel_vel = self.obj_b.vel - self.obj_a.vel
        return rel_vel.dot(direction) * METERS_PER_PIXEL

    def force_newtons(self):
        return self.k * self.stretch_meters() + self.damping * self.relative_speed_mps()

    def apply_force(self):
        p1, p2 = self.endpoints()
        diff = p2 - p1
        dist = diff.length()
        if dist <= 1e-6:
            return

        direction = diff / dist
        force = direction * (self.force_newtons() * PIXELS_PER_METER)

        if not getattr(self.obj_a, "is_static", False):
            self.obj_a.acc += force * self.obj_a.inv_mass
            if hasattr(self.obj_a, "wake"):
                self.obj_a.wake()
        if not getattr(self.obj_b, "is_static", False):
            self.obj_b.acc -= force * self.obj_b.inv_mass
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
        coils = max(6, min(14, int(length / 26)))
        amplitude = clamp(length * 0.08, 8.0, 18.0)
        start = p1 + direction * 12
        end = p2 - direction * 12
        spring_length = (end - start).length()
        step = spring_length / max(coils * 2, 1)
        points = [start]
        for index in range(1, coils * 2):
            point_on_line = start + direction * (step * index)
            offset = normal * amplitude if index % 2 == 0 else -normal * amplitude
            points.append(point_on_line + offset)
        points.append(end)

        stretch_ratio = clamp((length - self.rest_length) / max(self.rest_length, 1.0), -1.0, 1.0)
        mid_color = lerp_color((134, 202, 255), (255, 164, 92), (stretch_ratio + 1.0) * 0.5)
        draw_polyline(surface, (74, 86, 102), [(p.x, p.y) for p in [p1, start]], 4)
        draw_polyline(surface, (74, 86, 102), [(p.x, p.y) for p in [end, p2]], 4)
        draw_polyline(surface, (84, 96, 114), [(p.x, p.y) for p in points], 5)
        draw_polyline(surface, mid_color, [(p.x, p.y) for p in points], 2)
