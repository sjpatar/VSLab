import math
import pygame
from pygame.math import Vector2

class PinJoint:
    def __init__(self, obj_a, obj_b, anchor_a=(0, 0), anchor_b=(0, 0)):
        self.obj_a, self.obj_b = obj_a, obj_b
        self.local_anchor_a, self.local_anchor_b = Vector2(anchor_a), Vector2(anchor_b)

    def get_world_anchors(self):
        cos_a, sin_a = math.cos(self.obj_a.angle), math.sin(self.obj_a.angle)
        center_a = self.obj_a.get_link_anchor()
        wa = Vector2(
            center_a.x + self.local_anchor_a.x * cos_a - self.local_anchor_a.y * sin_a,
            center_a.y + self.local_anchor_a.x * sin_a + self.local_anchor_a.y * cos_a,
        )

        cos_b, sin_b = math.cos(self.obj_b.angle), math.sin(self.obj_b.angle)
        center_b = self.obj_b.get_link_anchor()
        wb = Vector2(
            center_b.x + self.local_anchor_b.x * cos_b - self.local_anchor_b.y * sin_b,
            center_b.y + self.local_anchor_b.x * sin_b + self.local_anchor_b.y * cos_b,
        )
        return wa, wb

    def render(self, surface: pygame.Surface):
        wa, wb = self.get_world_anchors()
        pygame.draw.line(surface, (126, 136, 152), (wa.x, wa.y), (wb.x, wb.y), 3)
        pygame.draw.circle(surface, (54, 60, 68), (int(wa.x), int(wa.y)), 7)
        pygame.draw.circle(surface, (186, 194, 202), (int(wa.x), int(wa.y)), 4)
        pygame.draw.circle(surface, (54, 60, 68), (int(wb.x), int(wb.y)), 7)
        pygame.draw.circle(surface, (186, 194, 202), (int(wb.x), int(wb.y)), 4)

class SliderJoint:
    def __init__(self, obj_a, axis=(1, 0)):
        self.obj_a = obj_a
        self.axis = Vector2(axis).normalize()
        self.perp_axis = Vector2(-self.axis.y, self.axis.x)
        self.locked_angle = obj_a.angle

    def render(self, surface: pygame.Surface):
        center = self.obj_a.get_link_anchor()
        p1 = (center.x - self.axis.x * 100, center.y - self.axis.y * 100)
        p2 = (center.x + self.axis.x * 100, center.y + self.axis.y * 100)
        pygame.draw.line(surface, (82, 86, 94), p1, p2, 8)
        pygame.draw.line(surface, (204, 210, 216), p1, p2, 3)