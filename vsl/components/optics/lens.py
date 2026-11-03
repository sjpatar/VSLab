import math
import pygame
from pygame.math import Vector2
from vsl.components.optics.base import OpticalObject
from vsl.components.optics.utils import point_in_polygon

class LensElement(OpticalObject):
    def __init__(self, x, y, width=132, height=160):
        super().__init__(x, y, width, height)
        self.width = width
        self.height = height
        self.shape_type = "convex" # Options: "concave", "flat", "convex"
        self.refractive_index = 1.52
        self.attenuation = 0.0025
        self.label = "Lens"
        self.segment_count = 28
        self._cached_vertices = []

    def local_profile_half_thickness(self, y_ratio):
        thick_half = self.width * 0.34
        thin_half = self.width * 0.12
        profile = math.sqrt(max(0.0, 1.0 - y_ratio * y_ratio))
        
        if self.shape_type == 'convex':
            return thin_half + (thick_half - thin_half) * profile
        elif self.shape_type == 'concave':
            return thick_half - (thick_half - thin_half) * profile
        else: # flat
            return thick_half * 0.6

    def vertices(self):
        if not self.geometry_dirty() and self._cached_vertices:
            return self._cached_vertices

        half_height = self.height * 0.5
        local_points = []
        for index in range(self.segment_count + 1):
            t = index / self.segment_count
            y = -half_height + self.height * t
            half_thickness = self.local_profile_half_thickness(y / max(half_height, 1.0))
            local_points.append(Vector2(-half_thickness, y))
            
        for index in range(self.segment_count, -1, -1):
            t = index / self.segment_count
            y = -half_height + self.height * t
            half_thickness = self.local_profile_half_thickness(y / max(half_height, 1.0))
            local_points.append(Vector2(half_thickness, y))

        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        self._cached_vertices = [
            self.pos + Vector2(p.x * cos_a - p.y * sin_a, p.x * sin_a + p.y * cos_a)
            for p in local_points
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
        fill_color = (102, 190, 255, 42) if self.shape_type == 'convex' else (118, 204, 255, 38)
        
        pygame.draw.polygon(glass, fill_color, points)
        pygame.draw.polygon(glass, (216, 242, 255, 28), points[: len(points) // 2])
        surface.blit(glass, (0, 0))

        edge_color = (126, 220, 255) if self.shape_type == 'convex' else (154, 232, 255)
        pygame.draw.polygon(surface, edge_color, points, 3)
        self.draw_selection(surface, points=points)
