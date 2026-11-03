import pygame
from vsl.core.experiment_base import ElectricalComponent

class Battery(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 80, 100)
        self.voltage = 9.0  # 9V Battery
        self.terminal_voltage = self.voltage
        # Left and right terminals
        self.terminals = [{'x': 15, 'y': 10}, {'x': 65, 'y': 10}]
        self.font = pygame.font.SysFont('Arial', 18, bold=True)

    def update(self):
        pass # The circuit solver handles the math

    def render(self, surface: pygame.Surface):
        # Draw battery body (Black and Gold like a standard 9V)
        pygame.draw.rect(surface, (40, 40, 40), self.rect, border_radius=8)
        pygame.draw.rect(surface, (218, 165, 32), (self.rect.x, self.rect.y + 40, 80, 60), border_radius=8)
        
        # Draw positive/negative markers
        pygame.draw.rect(surface, (200, 50, 50), (self.rect.x + 10, self.rect.y - 5, 10, 5))
        pygame.draw.rect(surface, (100, 100, 100), (self.rect.x + 60, self.rect.y - 5, 10, 5))

        self.draw_terminals(surface)
        
        text = self.font.render(f"{self.voltage:.1f}V", True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 40 - text.get_width()//2, self.rect.y + 55))
