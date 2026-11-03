import math
import pygame
from pygame.math import Vector2
from vsl.components.optics.base import OpticalObject
from vsl.components.optics.utils import point_segment_distance

class MirrorElement(OpticalObject):
    def __init__(self, x, y, length=150):
        super().__init__(x, y, int(length), 40)
        self.length = length
        self.angle = math.radians(24)
        self.shape_type = "flat"  # Options: "concave", "flat", "convex"
        self.segment_count = 32
        self.label = "Mirror"
        self.reflectivity = 0.96
        self.thickness = 14.0
        self._cached_front_vertices = []
        self._cached_back_vertices = []
        self._cached_draw_polygon = []

    def _local_front_profile_x(self, y):
        half_length = max(self.length * 0.5, 1.0)
        normalized_y = y / half_length
        depth = min(28.0, max(10.0, self.length * 0.16))
        if self.shape_type == 'flat':
            return 0.0
        if self.shape_type == 'concave':
            return -depth * (normalized_y ** 2)
        return depth * (normalized_y ** 2)

    def _transform_local_points(self, local_points):
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        return [
            self.pos + Vector2(p.x * cos_a - p.y * sin_a, p.x * sin_a + p.y * cos_a)
            for p in local_points
        ]

    def _rebuild_geometry(self):
        local_front_points = []
        local_back_points = []
        for i in range(self.segment_count + 1):
            t = i / self.segment_count - 0.5
            y = t * self.length
            front_x = self._local_front_profile_x(y)
            local_front_points.append(Vector2(front_x, y))
            local_back_points.append(Vector2(front_x - self.thickness, y))

        self._cached_front_vertices = self._transform_local_points(local_front_points)
        self._cached_back_vertices = self._transform_local_points(local_back_points)
        self._cached_draw_polygon = self._cached_front_vertices + list(reversed(self._cached_back_vertices))
        self.mark_geometry_clean()

    def reflective_vertices(self):
        if self.geometry_dirty() or not self._cached_front_vertices:
            self._rebuild_geometry()
        return self._cached_front_vertices

    def draw_polygon(self):
        if self.geometry_dirty() or not self._cached_draw_polygon:
            self._rebuild_geometry()
        return self._cached_draw_polygon

    def contains_point(self, point):
        verts = self.reflective_vertices()
        for i in range(len(verts) - 1):
            if point_segment_distance(Vector2(point), verts[i], verts[i+1]) <= 12.0:
                return True
        return False

    def get_optical_surfaces(self):
        surfaces = []
        verts = self.reflective_vertices()
        reflective_normal = -Vector2(math.cos(self.angle), math.sin(self.angle))
        for i in range(len(verts) - 1):
            p1 = verts[i]
            p2 = verts[i+1]
            normal = Vector2(-(p2 - p1).y, (p2 - p1).x)
            if normal.length_squared() > 1e-9:
                normal = normal.normalize()
            if normal.dot(reflective_normal) < 0:
                normal = -normal
            surfaces.append({
                "owner": self,
                "kind": "segment",
                "material": "mirror",
                "p1": p1,
                "p2": p2,
                "normal": normal,
                "reflectivity": self.reflectivity,
            })
        return surfaces

    def get_bounds(self):
        verts = self.draw_polygon()
        margin = 16
        xs = [v.x for v in verts]
        ys = [v.y for v in verts]
        return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin

    def render(self, surface):
        reflective_points = [(v.x, v.y) for v in self.reflective_vertices()]
        back_points = [(v.x, v.y) for v in self._cached_back_vertices]
        body_points = [(v.x, v.y) for v in self.draw_polygon()]

        body_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(body_surface, (82, 88, 102, 210), body_points)
        surface.blit(body_surface, (0, 0))

        pygame.draw.lines(surface, (58, 64, 76), False, back_points, 6)
        pygame.draw.lines(surface, (188, 204, 224), False, reflective_points, 8)
        pygame.draw.lines(surface, (242, 247, 255), False, reflective_points, 4)
        pygame.draw.lines(surface, (120, 214, 255), False, reflective_points, 1)

        front_normal = -Vector2(math.cos(self.angle), math.sin(self.angle))
        tangent = Vector2(-front_normal.y, front_normal.x)
        highlight_start = self.pos + front_normal * 5 - tangent * (self.length * 0.22)
        highlight_end = self.pos + front_normal * 5 + tangent * (self.length * 0.22)
        pygame.draw.line(surface, (245, 248, 255), highlight_start, highlight_end, 2)

        self.draw_selection(surface, points=reflective_points)
