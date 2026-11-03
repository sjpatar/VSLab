import math
import pygame
from pygame.math import Vector2

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def lerp_color(color_a, color_b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))

def point_segment_distance(point: Vector2, start: Vector2, end: Vector2) -> float:
    segment = end - start
    length_squared = segment.length_squared()
    if length_squared <= 1e-9:
        return (point - start).length()
    t = clamp((point - start).dot(segment) / length_squared, 0.0, 1.0)
    projection = start + segment * t
    return (point - projection).length()

def point_in_polygon(point, vertices):
    inside = False
    px, py = point
    if len(vertices) < 3:
        return False
    for index, vertex in enumerate(vertices):
        next_vertex = vertices[(index + 1) % len(vertices)]
        x1, y1 = vertex.x, vertex.y
        x2, y2 = next_vertex.x, next_vertex.y
        intersects = ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / ((y2 - y1) or 1e-9) + x1)
        if intersects:
            inside = not inside
    return inside