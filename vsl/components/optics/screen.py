import math
import pygame
from pygame.math import Vector2
from vsl.components.optics.base import OpticalObject
from vsl.components.optics.utils import point_segment_distance

class ScreenElement(OpticalObject):
    def __init__(self, x, y, length=150):
        super().__init__(x, y, int(length), 18)
        self.length = length
        self.angle = math.radians(90)
        self.hits = []
        self.total_intensity = 0.0
        self.peak_intensity = 0.0
        self.label = "Screen"
        self._cached_endpoints = None

    def endpoints(self):
        if not self.geometry_dirty() and self._cached_endpoints is not None:
            return self._cached_endpoints

        direction = Vector2(math.cos(self.angle), math.sin(self.angle))
        self._cached_endpoints = (
            self.pos - direction * (self.length * 0.5),
            self.pos + direction * (self.length * 0.5),
        )
        self.mark_geometry_clean()
        return self._cached_endpoints

    def contains_point(self, point):
        start, end = self.endpoints()
        return point_segment_distance(Vector2(point), start, end) <= 8.0

    def get_optical_surfaces(self):
        start, end = self.endpoints()
        normal = Vector2(-(end - start).y, (end - start).x)
        if normal.length_squared() > 1e-9: normal = normal.normalize()
        return [{
            "owner": self,
            "kind": "segment",
            "material": "absorber",
            "p1": start,
            "p2": end,
            "normal": normal,
        }]

    def reset_solver_state(self):
        self.hits = []
        self.total_intensity = 0.0
        self.peak_intensity = 0.0

    def register_hit(self, point, intensity, color):
        self.hits.append((Vector2(point), intensity, color))
        self.total_intensity += intensity
        self.peak_intensity = max(self.peak_intensity, intensity)

    def get_bounds(self):
        start, end = self.endpoints()
        return min(start.x, end.x) - 14, min(start.y, end.y) - 14, max(start.x, end.x) + 14, max(start.y, end.y) + 14

    def render(self, surface):
        start, end = self.endpoints()
        pygame.draw.line(surface, (132, 144, 160), (start.x, start.y), (end.x, end.y), 12)
        pygame.draw.line(surface, (238, 242, 248), (start.x, start.y), (end.x, end.y), 4)
        for point, intensity, color in self.hits:
            radius = max(3, int(5 * intensity))
            glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, 110), (glow.get_width() // 2, glow.get_height() // 2), radius * 2)
            surface.blit(glow, (point.x - glow.get_width() / 2, point.y - glow.get_height() / 2))
            pygame.draw.circle(surface, color, (int(point.x), int(point.y)), radius)
        self.draw_selection(surface, points=[(start.x, start.y), (end.x, end.y)])
