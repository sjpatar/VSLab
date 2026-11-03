import math
import pygame

class Wire:
    def __init__(self, start_obj, start_offset, end_obj, end_offset):
        self.start_obj = start_obj
        self.start_offset = start_offset
        self.end_obj = end_obj
        self.end_offset = end_offset
        self.has_power = False
        self.current = 0.0
        self.voltage = 0.0

    def endpoints(self):
        return (
            (self.start_obj.rect.x + self.start_offset[0], self.start_obj.rect.y + self.start_offset[1]),
            (self.end_obj.rect.x + self.end_offset[0], self.end_obj.rect.y + self.end_offset[1]),
        )

    def matches_connection(self, start_obj, start_offset, end_obj, end_offset):
        forward = (
            self.start_obj is start_obj and
            self.start_offset == start_offset and
            self.end_obj is end_obj and
            self.end_offset == end_offset
        )
        reverse = (
            self.start_obj is end_obj and
            self.start_offset == end_offset and
            self.end_obj is start_obj and
            self.end_offset == start_offset
        )
        return forward or reverse

    def contains_point(self, point, tolerance=10.0):
        (start_x, start_y), (end_x, end_y) = self.endpoints()
        dx = end_x - start_x
        dy = end_y - start_y
        length_sq = dx * dx + dy * dy
        if length_sq <= 1e-9:
            return math.hypot(point[0] - start_x, point[1] - start_y) <= tolerance

        t = ((point[0] - start_x) * dx + (point[1] - start_y) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        closest_x = start_x + t * dx
        closest_y = start_y + t * dy
        return math.hypot(point[0] - closest_x, point[1] - closest_y) <= tolerance

    def render(self, surface):
        (start_x, start_y), (end_x, end_y) = self.endpoints()

        # Use bright colors for dark backgrounds
        if abs(self.current) > 0.001 or self.has_power:
            color = (255, 80, 80)  # Bright Red/Orange for live wires
            thickness = 4
        else:
            color = (200, 200, 200)  # Light Gray for dead wires (visible on dark BG)
            thickness = 2

        pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), thickness)
