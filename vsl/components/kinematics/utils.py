import pygame

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def lerp_color(color_a, color_b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))

def draw_drop_shadow(
    surface: pygame.Surface,
    shape_type: str,
    rect: pygame.Rect = None,
    center: tuple = None,
    radius: int = None,
    points: list = None,
    alpha: int = 92,
):
    shadow_color = (10, 14, 20, alpha)
    offset_x, offset_y = 5, 7

    if shape_type == "rect" and rect:
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, (rect.x + offset_x, rect.y + offset_y))
        
    elif shape_type == "circle" and center and radius:
        shadow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, shadow_color, (radius, radius), radius)
        surface.blit(shadow_surf, (center[0] - radius + offset_x, center[1] - radius + offset_y))
        
    elif shape_type == "polygon" and points:
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        width, height = int(max_x - min_x), int(max_y - min_y)
        
        if width > 0 and height > 0:
            shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(shadow_surf, shadow_color, local_points)
            surface.blit(shadow_surf, (min_x + offset_x, min_y + offset_y))

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

def draw_polyline(surface, color, points, width):
    if len(points) >= 2:
        pygame.draw.lines(surface, color, False, points, width)