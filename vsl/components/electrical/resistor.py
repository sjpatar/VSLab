import pygame
from vsl.core.experiment_base import ElectricalComponent


class Resistor(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 90, 30)
        self.resistance = 100.0  # 100 ohms
        self.terminals = [{"x": 0, "y": 15}, {"x": 90, "y": 15}]
        self.font = pygame.font.SysFont("Arial", 14)

    def update(self):
        pass

    def render(self, surface: pygame.Surface):
        body_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 5, 60, 20)
        pygame.draw.rect(surface, (210, 180, 140), body_rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), body_rect, 1, border_radius=5)

        pygame.draw.line(surface, (139, 69, 19), (self.rect.x + 25, self.rect.y + 6), (self.rect.x + 25, self.rect.y + 23), 3)
        pygame.draw.line(surface, (0, 0, 0), (self.rect.x + 35, self.rect.y + 6), (self.rect.x + 35, self.rect.y + 23), 3)
        pygame.draw.line(surface, (139, 69, 19), (self.rect.x + 45, self.rect.y + 6), (self.rect.x + 45, self.rect.y + 23), 3)

        self.draw_terminals(surface)

        text = self.font.render(f"{self.resistance} Ohm", True, (240, 240, 240))
        surface.blit(text, (self.rect.x + 45 - text.get_width() // 2, self.rect.y - 15))
