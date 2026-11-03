import pygame
from vsl.core.experiment_base import ElectricalComponent

class Switch(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 70, 40)
        self.closed = False
        self.resistance = 0.01 if self.closed else float('inf')
        self.terminals = [{'x': 10, 'y': 20}, {'x': 60, 'y': 20}]

    def on_click(self):
        self.closed = not self.closed
        self.resistance = 0.01 if self.closed else float('inf')

    def update(self):
        pass

    def render(self, surface: pygame.Surface):
        # Base
        pygame.draw.rect(surface, (180, 180, 180), self.rect, border_radius=4)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2, border_radius=4)
        
        self.draw_terminals(surface)
        
        # Draw the switch lever
        start_pos = (self.rect.x + 15, self.rect.y + 20)
        if self.closed:
            end_pos = (self.rect.x + 55, self.rect.y + 20)
        else:
            end_pos = (self.rect.x + 45, self.rect.y + 5)
            
        pygame.draw.line(surface, (50, 50, 50), start_pos, end_pos, 4)