from abc import ABC, abstractmethod
import pygame
import math

class LabObject(ABC):
    def __init__(self, x: int, y: int, width: int, height: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_dragging, self.selected = False, False
        self.drag_offset_x, self.drag_offset_y = 0, 0
        self.drag_start_mouse = None
        self.drag_moved = False

    @abstractmethod
    def update(self): pass

    @abstractmethod
    def render(self, surface: pygame.Surface): pass

    def hit_test(self, point) -> bool:
        if hasattr(self, "contains_point"):
            return self.contains_point(point)
        return self.rect.collidepoint(point)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hit_test(event.pos):
                if event.button == 3: 
                    self.on_context_click()
                    return True
                if event.button == 1:
                    # If a subclass has terminals, check them first before dragging
                    if hasattr(self, 'get_hit_terminal') and self.get_hit_terminal(event.pos): 
                        return False
                    
                    self.is_dragging, self.selected = True, True
                    self.drag_offset_x = self.rect.x - event.pos[0]
                    self.drag_offset_y = self.rect.y - event.pos[1]
                    self.drag_start_mouse = event.pos
                    self.drag_moved = False
                    if hasattr(self, "wake"):
                        self.wake()
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
            self.rect.x, self.rect.y = event.pos[0] + self.drag_offset_x, event.pos[1] + self.drag_offset_y
            return True
        return False

    def on_click(self): pass
    def on_context_click(self): pass

class ElectricalComponent(LabObject):
    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.receiving_power, self.voltage, self.v_drop, self.current = False, 0.0, 0.0, 0.0
        self.terminals = [] 

    def draw_terminals(self, surface: pygame.Surface):
        for term in self.terminals:
            wx, wy = self.rect.x + term['x'], self.rect.y + term['y']
            pygame.draw.circle(surface, (50, 50, 50), (wx, wy), 6)
            pygame.draw.circle(surface, (200, 200, 200), (wx, wy), 4)
            pygame.draw.circle(surface, (0, 0, 0), (wx, wy), 2)

    def get_hit_terminal(self, mouse_pos):
        for term in self.terminals:
            wx, wy = self.rect.x + term['x'], self.rect.y + term['y']
            if math.hypot(mouse_pos[0] - wx, mouse_pos[1] - wy) <= 12:
                return (term['x'], term['y'])
        return None
