import pygame
from vsl.core.base_env import BaseEnvironment
from vsl.ui import MenuButtonPanel

class MenuEnvironment(BaseEnvironment):
    def __init__(self, app_ref, title, buttons):
        super().__init__(app_ref)
        self.background_color = (30, 30, 35)
        self.font_title = pygame.font.SysFont('Arial', 48, bold=True)
        self.title = title
        self.buttons = buttons
        self.menu_panel = MenuButtonPanel(pygame.Rect(0, 0, 0, 0), buttons)
            
        w, h = self.app.screen.get_size()
        self.update_layout(w, h)

    def update_layout(self, w, h):
        self.menu_panel.update_layout(x=0, y=150, width=w, height=max(h - 150, 1))

    def update(self):
        pass # Static menu, no continuous logic needed

    def render(self, surface: pygame.Surface):
        surface.fill(self.background_color)
        
        # Draw Title
        title_txt = self.font_title.render(self.title, True, (240, 240, 240))
        surface.blit(title_txt, title_txt.get_rect(center=(surface.get_width()//2, 100)))
        self.menu_panel.render(surface)

    def handle_event(self, event: pygame.event.Event):
        action = self.menu_panel.handle_event(event)
        if action == "Exit":
            self.app.show_exit_dialog = True
        elif action:
            self.app.switch_environment(action)
