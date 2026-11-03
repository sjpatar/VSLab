import pygame

def _lighten(color, amount):
    return tuple(min(channel + amount, 255) for channel in color)

def _text_color_for(color):
    return (24, 28, 34) if sum(color) > 420 else (245, 247, 250)

class ButtonPanel:
    def __init__(
        self,
        rect,
        button_defs,
        *,
        layout="horizontal",
        button_height=40,
        padding=12,
        gap=10,
        min_button_width=64,
        max_button_width=112,
        show_panel=True,
        show_tooltips=True,
        panel_color=(26, 31, 38),
        border_color=(58, 67, 79),
        outline_color=(96, 176, 255),
        font_size=13,
        border_radius=10,
    ):
        self.rect = pygame.Rect(rect)
        self.layout = layout
        self.button_height = button_height
        self.padding = padding
        self.gap = gap
        self.min_button_width = min_button_width
        self.max_button_width = max_button_width
        self.show_panel = show_panel
        self.show_tooltips = show_tooltips
        self.panel_color = panel_color
        self.border_color = border_color
        self.outline_color = outline_color
        self.border_radius = border_radius
        self.font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.tooltip_font = pygame.font.SysFont("Arial", 12)
        self.active_action = None
        self.button_defs = []
        self.buttons = []
        self.set_buttons(button_defs)

    def set_buttons(self, button_defs):
        self.button_defs = []
        if button_defs:
            # Type-Agnostic dictionary/tuple normalization fix
            for btn in button_defs:
                if isinstance(btn, dict):
                    self.button_defs.append((
                        btn.get("label", ""),
                        btn.get("action", btn.get("target")),
                        btn.get("color", (100, 100, 100)),
                        btn.get("tooltip", "")
                    ))
                else:
                    self.button_defs.append(btn)
        self._rebuild_buttons()

    def export_button_defs(self):
        return [
            (button["label"], button["action"], button["color"], button["tooltip"])
            for button in self.buttons
        ]

    def update_layout(self, x=None, y=None, width=None, height=None):
        if x is not None:
            self.rect.x = x
        if y is not None:
            self.rect.y = y
        if width is not None:
            self.rect.width = width
        if height is not None:
            self.rect.height = height
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        self.buttons = []
        if not self.button_defs:
            return

        if self.layout == "vertical":
            self._build_vertical_buttons()
        else:
            self._build_horizontal_buttons()

    def _build_horizontal_buttons(self):
        count = len(self.button_defs)
        available_width = max(self.rect.width - (self.padding * 2) - (self.gap * (count - 1)), 1)
        button_width = available_width // count
        if available_width >= self.min_button_width * count:
            button_width = max(self.min_button_width, button_width)
        button_width = max(1, min(self.max_button_width, button_width))
        row_width = (button_width * count) + (self.gap * (count - 1))
        start_x = self.rect.x + max((self.rect.width - row_width) // 2, self.padding)
        y = self.rect.y + max((self.rect.height - self.button_height) // 2, 0)

        for index, (label, action, color, tooltip) in enumerate(self.button_defs):
            x = start_x + index * (button_width + self.gap)
            self.buttons.append(
                {
                    "rect": pygame.Rect(x, y, button_width, self.button_height),
                    "label": label,
                    "action": action,
                    "color": color,
                    "tooltip": tooltip,
                }
            )

    def _build_vertical_buttons(self):
        count = len(self.button_defs)
        available_width = max(self.rect.width - (self.padding * 2), 1)
        button_width = min(available_width, self.max_button_width)
        if available_width >= self.min_button_width:
            button_width = max(button_width, self.min_button_width)
        total_height = (self.button_height * count) + (self.gap * (count - 1))
        start_y = self.rect.y + max((self.rect.height - total_height) // 2, self.padding)
        x = self.rect.x + (self.rect.width - button_width) // 2

        for index, (label, action, color, tooltip) in enumerate(self.button_defs):
            y = start_y + index * (self.button_height + self.gap)
            self.buttons.append(
                {
                    "rect": pygame.Rect(x, y, button_width, self.button_height),
                    "label": label,
                    "action": action,
                    "color": color,
                    "tooltip": tooltip,
                }
            )

    def render(self, surface: pygame.Surface):
        if self.show_panel:
            pygame.draw.rect(surface, self.panel_color, self.rect, border_radius=self.border_radius)
            pygame.draw.rect(surface, self.border_color, self.rect, 1, border_radius=self.border_radius)

        mouse_pos = pygame.mouse.get_pos()
        tooltip_data = None

        for button in self.buttons:
            hover = button["rect"].collidepoint(mouse_pos)
            is_active = button["action"] == self.active_action
            color = button["color"]

            if hover:
                color = _lighten(color, 24)
                if self.show_tooltips and button["tooltip"]:
                    tooltip_data = (button["tooltip"], mouse_pos)
            elif is_active:
                color = _lighten(color, 12)

            if is_active:
                pygame.draw.rect(surface, self.outline_color, button["rect"].inflate(6, 6), border_radius=8, width=2)

            pygame.draw.rect(surface, color, button["rect"], border_radius=7)
            pygame.draw.rect(surface, (70, 78, 90), button["rect"], 1, border_radius=7)

            label = self.font.render(button["label"], True, _text_color_for(color))
            surface.blit(label, label.get_rect(center=button["rect"].center))

        if tooltip_data:
            tooltip, position = tooltip_data
            rendered = self.tooltip_font.render(tooltip, True, (244, 246, 249))
            tooltip_rect = rendered.get_rect(topleft=(position[0] + 16, position[1] + 16))
            tooltip_rect.inflate_ip(12, 8)
            
            # Viewport off-screen tooltip fix 
            screen_rect = surface.get_rect()
            if tooltip_rect.right > screen_rect.right:
                tooltip_rect.right = screen_rect.right - 8
            if tooltip_rect.bottom > screen_rect.bottom:
                tooltip_rect.bottom = screen_rect.bottom - 8
            if tooltip_rect.left < screen_rect.left:
                tooltip_rect.left = screen_rect.left + 8
            if tooltip_rect.top < screen_rect.top:
                tooltip_rect.top = screen_rect.top + 8
            
            pygame.draw.rect(surface, (18, 22, 28), tooltip_rect, border_radius=6)
            pygame.draw.rect(surface, (82, 92, 108), tooltip_rect, 1, border_radius=6)
            surface.blit(rendered, (tooltip_rect.x + 6, tooltip_rect.y + 4))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button["rect"].collidepoint(event.pos):
                    return button["action"]
        return None

    def set_active_action(self, action):
        self.active_action = action

class MenuButtonPanel(ButtonPanel):
    def __init__(self, rect, button_defs):
        super().__init__(
            rect,
            button_defs,
            layout="vertical",
            button_height=60,
            padding=24,
            gap=20,
            min_button_width=320,
            max_button_width=420,
            show_panel=False,
            show_tooltips=False,
            font_size=24,
            border_radius=12,
        )