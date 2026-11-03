import pygame
from vsl.core.experiment_base import ElectricalComponent

class Bulb(ElectricalComponent):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 80)
        self.resistance = 15.0
        self.terminals = [{'x': 20, 'y': 75}, {'x': 40, 'y': 75}]
        self.brightness = 0.0

    def update(self):
        pass

    def render(self, surface: pygame.Surface):
        # Base of the bulb
        pygame.draw.rect(surface, (120, 120, 120), (self.rect.x + 15, self.rect.y + 50, 30, 25), border_radius=3)
        self.draw_terminals(surface)
        
        # Calculate power to determine brightness
        power = (self.current ** 2) * self.resistance
        brightness = min(255, int(power * 15)) 
        self.brightness = brightness / 255.0
        
        bulb_color = (255, 255, 255 - brightness) if brightness > 0 else (220, 220, 220)
        
        # Outer glow if lit
        if brightness > 30:
            glow_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 255, 100, 80), (50, 50), 40)
            surface.blit(glow_surface, (self.rect.x - 20, self.rect.y - 20))
        
        # Glass bulb
        pygame.draw.circle(surface, bulb_color, (self.rect.x + 30, self.rect.y + 30), 25)
        pygame.draw.circle(surface, (150, 150, 150), (self.rect.x + 30, self.rect.y + 30), 25, 2)
