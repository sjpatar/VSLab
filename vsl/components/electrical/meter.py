import pygame
from vsl.core.experiment_base import ElectricalComponent

class Ammeter(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60)
        self.resistance = 0.01 # Ammeters have near-zero resistance
        self.terminals = [{'x': 0, 'y': 30}, {'x': 60, 'y': 30}]
        self.font = pygame.font.SysFont('Arial', 14, bold=True)
        self.value = 0.0

    def update(self): pass

    def render(self, surface: pygame.Surface):
        pygame.draw.circle(surface, (200, 220, 255), (self.rect.x + 30, self.rect.y + 30), 30)
        pygame.draw.circle(surface, (50, 50, 50), (self.rect.x + 30, self.rect.y + 30), 30, 2)
        self.draw_terminals(surface)
        
        lbl = self.font.render("A", True, (100, 100, 100))
        text = self.font.render(f"{abs(self.value):.2f} A", True, (0, 0, 0))
        
        surface.blit(lbl, (self.rect.x + 30 - lbl.get_width()//2, self.rect.y + 10))
        surface.blit(text, (self.rect.x + 30 - text.get_width()//2, self.rect.y + 30))

class Voltmeter(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60)
        self.resistance = 1000000.0 # Voltmeters have massive resistance
        self.terminals = [{'x': 0, 'y': 30}, {'x': 60, 'y': 30}]
        self.font = pygame.font.SysFont('Arial', 14, bold=True)
        self.value = 0.0

    def update(self): pass

    def render(self, surface: pygame.Surface):
        pygame.draw.circle(surface, (255, 200, 200), (self.rect.x + 30, self.rect.y + 30), 30)
        pygame.draw.circle(surface, (50, 50, 50), (self.rect.x + 30, self.rect.y + 30), 30, 2)
        self.draw_terminals(surface)
        
        lbl = self.font.render("V", True, (100, 100, 100))
        text = self.font.render(f"{abs(self.value):.2f} V", True, (0, 0, 0))
        
        surface.blit(lbl, (self.rect.x + 30 - lbl.get_width()//2, self.rect.y + 10))
        surface.blit(text, (self.rect.x + 30 - text.get_width()//2, self.rect.y + 30))
