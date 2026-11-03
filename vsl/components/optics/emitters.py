import math
import pygame
from pygame.math import Vector2
from vsl.components.optics.base import OpticalObject

class LaserEmitter(OpticalObject):
    def __init__(self, x, y):
        super().__init__(x, y, 56, 28)
        self.angle = 0.0
        self.beam_color = (255, 86, 86)
        self.glow_color = (255, 164, 164)
        self.label = "Laser"
        self.beam_count = 3

    def contains_point(self, point):
        local = Vector2(point) - self.pos
        cos_a, sin_a = math.cos(-self.angle), math.sin(-self.angle)
        rotated = Vector2(local.x * cos_a - local.y * sin_a, local.x * sin_a + local.y * cos_a)
        return abs(rotated.x) <= 28 and abs(rotated.y) <= 14

    def get_emitters(self):
        direction = Vector2(math.cos(self.angle), math.sin(self.angle))
        normal = Vector2(-direction.y, direction.x)
        emitter_origin = self.pos + direction * 28
        rays = []
        offsets = [0.0] if self.beam_count == 1 else [-4.0, 0.0, 4.0]
        for offset in offsets:
            rays.append({
                "origin": emitter_origin + normal * offset,
                "direction": direction,
                "color": self.beam_color,
                "intensity": 1.0 if offset == 0 else 0.68,
            })
        return rays

    def render(self, surface):
        body = pygame.Surface((60, 32), pygame.SRCALPHA)
        pygame.draw.rect(body, (78, 90, 106), (0, 4, 60, 24), border_radius=8)
        pygame.draw.rect(body, (118, 132, 152), (0, 4, 60, 24), 2, border_radius=8)
        pygame.draw.rect(body, (34, 38, 48), (8, 10, 24, 12), border_radius=5)
        pygame.draw.circle(body, self.beam_color, (49, 16), 5)
        pygame.draw.circle(body, self.glow_color, (49, 16), 9, 2)

        rotated = pygame.transform.rotate(body, math.degrees(-self.angle))
        rect = rotated.get_rect(center=(self.pos.x, self.pos.y))
        surface.blit(rotated, rect.topleft)

        direction = Vector2(math.cos(self.angle), math.sin(self.angle))
        nozzle = self.pos + direction * 31
        pygame.draw.circle(surface, self.glow_color, (int(nozzle.x), int(nozzle.y)), 3)
        self.draw_selection(surface, points=None)

class LampEmitter(OpticalObject):
    def __init__(self, x, y):
        super().__init__(x, y, 48, 48)
        self.angle = -math.pi / 8
        self.spread = math.radians(52)
        self.ray_count = 11
        self.beam_color = (255, 222, 118)
        self.label = "Lamp"

    def contains_point(self, point):
        return (Vector2(point) - self.pos).length() <= 24

    def get_emitters(self):
        angles = [self.angle] if self.ray_count <= 1 else [self.angle - self.spread * 0.5 + (self.spread * index / (self.ray_count - 1)) for index in range(self.ray_count)]
        return [{
            "origin": self.pos + Vector2(math.cos(angle), math.sin(angle)) * 18,
            "direction": Vector2(math.cos(angle), math.sin(angle)),
            "color": (255, 248, 236),
            "intensity": 0.78,
            "spectrum_enabled": True,
        } for angle in angles]

    def render(self, surface):
        pygame.draw.circle(surface, (82, 94, 112), (int(self.pos.x), int(self.pos.y)), 22)
        pygame.draw.circle(surface, (255, 214, 94), (int(self.pos.x), int(self.pos.y)), 12)
        pygame.draw.circle(surface, (255, 244, 186), (int(self.pos.x), int(self.pos.y)), 6)
        arc_rect = pygame.Rect(self.pos.x - 36, self.pos.y - 36, 72, 72)
        pygame.draw.arc(surface, (255, 226, 138), arc_rect, self.angle - self.spread * 0.5, self.angle + self.spread * 0.5, 2)
        self.draw_selection(surface, radius=28)
