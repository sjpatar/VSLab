import math
import pygame
from pygame.math import Vector2
from vsl.core.experiment_base import LabObject

class OpticalObject(LabObject):
    def __init__(self, x, y, width, height):
        super().__init__(int(x - width / 2), int(y - height / 2), width, height)
        self.pos = Vector2(x, y)
        self.angle = 0.0
        self.selection_color = (104, 214, 255)
        self.label_color = (232, 238, 245)
        self.caption_font = pygame.font.SysFont("Arial", 12, bold=True)
        self._geometry_dirty = True
        self.drag_offset = Vector2()

    def update(self):
        pass

    def rotate(self, delta_radians):
        self.angle = (self.angle + delta_radians) % (2 * math.pi)
        self.invalidate_geometry()

    def update_rect(self):
        min_x, min_y, max_x, max_y = self.get_bounds()
        self.rect = pygame.Rect(int(min_x), int(min_y), max(1, int(max_x - min_x)), max(1, int(max_y - min_y)))

    def invalidate_geometry(self):
        self._geometry_dirty = True
        self.update_rect()

    def geometry_dirty(self):
        return self._geometry_dirty

    def mark_geometry_clean(self):
        self._geometry_dirty = False

    def get_bounds(self):
        return self.rect.left, self.rect.top, self.rect.right, self.rect.bottom

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hit_test(event.pos):
                if event.button == 3:
                    self.on_context_click()
                    return True
                if event.button == 1:
                    self.is_dragging, self.selected = True, True
                    self.drag_offset = self.pos - Vector2(event.pos)
                    self.drag_start_mouse = event.pos
                    self.drag_moved = False
                    return True
            else:
                self.selected = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.is_dragging:
            self.is_dragging = False
            if not self.drag_moved:
                self.on_click()
            self.drag_start_mouse = None
            self.drag_moved = False
            return True
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            if self.drag_start_mouse and math.hypot(event.pos[0] - self.drag_start_mouse[0], event.pos[1] - self.drag_start_mouse[1]) > 3:
                self.drag_moved = True
            new_pos = Vector2(event.pos) + self.drag_offset
            if (new_pos - self.pos).length_squared() > 1e-9:
                self.pos = new_pos
                self.invalidate_geometry()
            return True
        return False

    def draw_selection(self, surface, points=None, radius=None):
        if not (self.selected or self.is_dragging):
            return
        if radius is not None:
            pygame.draw.circle(surface, self.selection_color, (int(self.pos.x), int(self.pos.y)), int(radius), 2)
        elif points:
            pygame.draw.polygon(surface, self.selection_color, points, 2)
        else:
            pygame.draw.rect(surface, self.selection_color, self.rect.inflate(8, 8), 2, border_radius=10)

    def get_emitters(self):
        return []

    def get_optical_surfaces(self):
        return []

    def reset_solver_state(self):
        pass
