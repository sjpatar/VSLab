import pygame
import sys
import json
import os

# Ensure the 'vsl' package can be found
sys.path.append(os.getcwd())
vendor_path = os.path.join(os.getcwd(), "_vendor", "pygame")
if os.path.isdir(vendor_path) and vendor_path not in sys.path:
    sys.path.append(vendor_path)

# Import our environments
from vsl.environments.menu_env import MenuEnvironment
from vsl.environments.physics.electricity_env import ElectricityEnvironment
from vsl.environments.physics.motion_env import MotionEnvironment
from vsl.environments.physics.optics_env import OpticsEnvironment
from vsl.environments.chemistry.titration_env import TitrationEnvironment
from vsl.environments.chemistry.reactions_env import ReactionEnvironment
from vsl.environments.chemistry.carbon_env import CarbonLabEnvironment

PREFS_FILE = "window_prefs.json"

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("VSLab - Virtual Scientific Laboratory")
        
        self.window_size = (1200, 800)
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, 'r') as f:
                    data = json.load(f)
                    self.window_size = tuple(data.get('size', [1200, 800]))
            except: pass

        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        
        self.running = True
        self.show_exit_dialog = False
        
        # FIX: Instantiate all environments once to preserve state between menu swaps
        self.environments = {
            "MainMenu": MenuEnvironment(
                self, 
                title="VSLab - Select Subject",
                buttons=[
                    {"label": "Physics", "target": "PhysicsMenu", "color": (100, 150, 200)},
                    {"label": "Chemistry", "target": "ChemistryMenu", "color": (150, 100, 200)},
                    {"label": "Exit Application", "target": "Exit", "color": (200, 100, 100)}
                ]
            ),
            "PhysicsMenu": MenuEnvironment(
                self, 
                title="Physics Labs",
                buttons=[
                    {"label": "Electricity Lab", "target": "Electricity", "color": (220, 180, 50)},
                    {"label": "Motion Lab", "target": "Motion", "color": (100, 200, 150)},
                    {"label": "Optics Lab", "target": "Optics", "color": (110, 180, 255)},
                    {"label": "Back to Main Menu", "target": "MainMenu", "color": (100, 100, 100)}
                ]
            ),
            "ChemistryMenu": MenuEnvironment(
                self, 
                title="Chemistry Labs",
                buttons=[
                    {"label": "Titration Lab", "target": "Titration", "color": (110, 180, 255)},
                    {"label": "Reaction Lab", "target": "ReactionLab", "color": (120, 208, 160)},
                    {"label": "Carbon Compounds Lab", "target": "CarbonLab", "color": (245, 184, 96)},
                    {"label": "Back to Main Menu", "target": "MainMenu", "color": (100, 100, 100)}
                ]
            ),
            "Electricity": ElectricityEnvironment(self),
            "Motion": MotionEnvironment(self),
            "Optics": OpticsEnvironment(self),
            "Titration": TitrationEnvironment(self),
            "ReactionLab": ReactionEnvironment(self),
            "CarbonLab": CarbonLabEnvironment(self)
        }

        self.current_env = self.environments["MainMenu"]

    def switch_environment(self, env_name):
        """Dynamically swap labs and menus without destroying state."""
        if env_name in self.environments:
            self.current_env = self.environments[env_name]
            
            # Ensure the new environment adapts to the current window size
            w, h = self.screen.get_size()
            if hasattr(self.current_env, 'update_layout'):
                self.current_env.update_layout(w, h)

    def save_prefs(self):
        try:
            with open(PREFS_FILE, 'w') as f:
                json.dump({'size': self.screen.get_size()}, f)
        except: pass

    def toggle_maximize(self):
        # FIX: Use Pygame's native maximized display flag instead of guessing resolution
        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE | pygame.MAXIMIZED)
        w, h = self.screen.get_size()
        if hasattr(self.current_env, 'update_layout'):
            self.current_env.update_layout(w, h)

    def draw_exit_dialog(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        cw, ch = self.screen.get_size()
        box_rect = pygame.Rect((cw - 400)//2, (ch - 200)//2, 400, 200)
        pygame.draw.rect(self.screen, (240, 240, 240), box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (50, 50, 50), box_rect, 2, border_radius=10)
        
        font = pygame.font.SysFont('Arial', 24, bold=True)
        t = font.render("Exit Application?", True, (50, 50, 50))
        self.screen.blit(t, (box_rect.centerx - t.get_width()//2, box_rect.y + 40))
        
        y_rect = pygame.Rect(box_rect.x + 50, box_rect.bottom - 60, 120, 40)
        n_rect = pygame.Rect(box_rect.right - 170, box_rect.bottom - 60, 120, 40)
        
        pygame.draw.rect(self.screen, (220, 80, 80), y_rect, border_radius=5)
        pygame.draw.rect(self.screen, (100, 200, 100), n_rect, border_radius=5)
        
        yt = font.render("Exit", True, (255,255,255))
        nt = font.render("Cancel", True, (255,255,255))
        self.screen.blit(yt, (y_rect.centerx - yt.get_width()//2, y_rect.centery - yt.get_height()//2))
        self.screen.blit(nt, (n_rect.centerx - nt.get_width()//2, n_rect.centery - nt.get_height()//2))
        
        return y_rect, n_rect

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    if hasattr(self.current_env, 'update_layout'):
                        self.current_env.update_layout(event.w, event.h)
            
            if not self.show_exit_dialog:
                for event in events:
                    if event.type == pygame.QUIT: self.show_exit_dialog = True
                    self.current_env.handle_event(event)
                
                self.current_env.update()
            else:
                y_rect, n_rect = self.draw_exit_dialog()
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if y_rect.collidepoint(event.pos):
                            self.save_prefs()
                            self.running = False
                        elif n_rect.collidepoint(event.pos):
                            self.show_exit_dialog = False

            self.current_env.render(self.screen)
            
            if hasattr(self.current_env, 'toolbar') and self.current_env.toolbar:
                self.current_env.toolbar.render(self.screen)
                
            if self.show_exit_dialog: 
                self.draw_exit_dialog()
                
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    App().run()
