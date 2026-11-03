import math
import pygame
from pygame.math import Vector2
from vsl.components.optics.base import OpticalObject
from vsl.components.optics.utils import point_in_polygon

class PrismElement(OpticalObject):
    def __init__(self, x, y, size=120):
        super().__init__(x, y, size, size)
        self.size = size
        self.angle = math.radians(-18)
        self.refractive_index = 1.58
        self.attenuation = 0.003
        self.label = "Prism"
        self._cached_vertices = []

    def vertices(self):
        if not self.geometry_dirty() and self._cached_vertices:
            return self._cached_vertices

        radius = self.size * 0.58
        base_angles = [-math.pi / 2, math.pi / 6, 5 * math.pi / 6]
        self._cached_vertices = [
            self.pos + Vector2(math.cos(self.angle + a), math.sin(self.angle + a)) * radius
            for a in base_angles
        ]
        self.mark_geometry_clean()
        return self._cached_vertices

    def contains_point(self, point):
        return point_in_polygon(point, self.vertices())

    def get_optical_surfaces(self):
        vertices = self.vertices()
        surfaces = []
        center = Vector2(self.pos)
        for index, vertex in enumerate(vertices):
            next_vertex = vertices[(index + 1) % len(vertices)]
            edge = next_vertex - vertex
            normal = Vector2(edge.y, -edge.x)
            if normal.length_squared() > 1e-9: normal = normal.normalize()
            if normal.dot((vertex + next_vertex) * 0.5 - center) < 0: normal = -normal
                
            surfaces.append({
                "owner": self,
                "kind": "segment",
                "material": "refractive",
                "p1": vertex,
                "p2": next_vertex,
                "normal": normal,
                "refractive_index": self.refractive_index,
            })
        return surfaces

    def get_bounds(self):
        vertices = self.vertices()
        xs = [v.x for v in vertices]
        ys = [v.y for v in vertices]
        return min(xs) - 12, min(ys) - 12, max(xs) + 12, max(ys) + 12

    def render(self, surface):
        points = [(v.x, v.y) for v in self.vertices()]
        glass = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(glass, (150, 212, 255, 54), points)
        pygame.draw.polygon(glass, (220, 242, 255, 42), [points[0], ((points[0][0] + points[1][0]) / 2, (points[0][1] + points[1][1]) / 2), points[1]])
        surface.blit(glass, (0, 0))
        pygame.draw.polygon(surface, (122, 214, 255), points, 3)
        self.draw_selection(surface, points=points)
