import pygame


def clamp(value, low, high):
    return max(low, min(high, value))


def lerp_color(color_a, color_b, t):
    t = clamp(t, 0.0, 1.0)
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))


def draw_gradient(surface, rect, top_color, bottom_color):
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return

    for row in range(rect.height):
        blend = row / max(rect.height - 1, 1)
        color = lerp_color(top_color, bottom_color, blend)
        pygame.draw.line(
            surface,
            color,
            (rect.x, rect.y + row),
            (rect.right - 1, rect.y + row),
        )


def draw_grid(surface, rect, spacing, color):
    rect = pygame.Rect(rect)
    if rect.width <= 0 or rect.height <= 0:
        return

    for x in range(rect.x, rect.right + 1, spacing):
        pygame.draw.line(surface, color, (x, rect.y), (x, rect.bottom), 1)
    for y in range(rect.y, rect.bottom + 1, spacing):
        pygame.draw.line(surface, color, (rect.x, y), (rect.right, y), 1)


def draw_card(surface, rect, fill_color, border_color, *, alpha=220, radius=16):
    rect = pygame.Rect(rect)
    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(overlay, (*fill_color, alpha), overlay.get_rect(), border_radius=radius)
    pygame.draw.rect(overlay, border_color, overlay.get_rect(), 1, border_radius=radius)
    surface.blit(overlay, rect.topleft)


def wrap_text(font, text, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_text(font, text, max_width):
    if max_width <= 0:
        return ""
    if font.size(text)[0] <= max_width:
        return text
    ellipsis = "..."
    if font.size(ellipsis)[0] > max_width:
        return ""

    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed.rstrip() + ellipsis) if trimmed else ellipsis


def draw_text_block(surface, font, text, color, rect, *, line_gap=5):
    rect = pygame.Rect(rect)
    y = rect.y
    for line in wrap_text(font, text, rect.width):
        rendered = font.render(line, True, color)
        if y + rendered.get_height() > rect.bottom:
            break
        surface.blit(rendered, (rect.x, y))
        y += rendered.get_height() + line_gap
    return y


def clamp_scroll(scroll_y, viewport_height, content_height):
    max_scroll = max(content_height - viewport_height, 0)
    return max(0, min(int(scroll_y), max_scroll))


def blit_scroll_surface(surface, content_surface, viewport_rect, scroll_y):
    viewport_rect = pygame.Rect(viewport_rect)
    scroll_y = clamp_scroll(scroll_y, viewport_rect.height, content_surface.get_height())
    previous_clip = surface.get_clip()
    surface.set_clip(viewport_rect)
    surface.blit(content_surface, (viewport_rect.x, viewport_rect.y - scroll_y))
    surface.set_clip(previous_clip)
    return scroll_y
