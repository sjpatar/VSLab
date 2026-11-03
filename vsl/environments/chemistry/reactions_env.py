import math

import pygame

from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.environments.chemistry.common import blit_scroll_surface, clamp, clamp_scroll, draw_card, draw_gradient, draw_text_block, fit_text
from vsl.environments.chemistry.chemistry_models import (
    ELEMENTS_BY_SYMBOL,
    analyze_reaction,
    classify_compound,
    compound_formula,
    describe_formula_counts,
)

REACTION_PRESETS = [
    ("HCl", {"H": 1, "Cl": 1}),
    ("NaOH", {"Na": 1, "O": 1, "H": 1}),
    ("AgNO3", {"Ag": 1, "N": 1, "O": 3}),
    ("NaCl", {"Na": 1, "Cl": 1}),
    ("H2SO4", {"H": 2, "S": 1, "O": 4}),
    ("BaCl2", {"Ba": 1, "Cl": 2}),
    ("KI", {"K": 1, "I": 1}),
    ("Pb(NO3)2", {"Pb": 1, "N": 2, "O": 6}),
    ("CuSO4", {"Cu": 1, "S": 1, "O": 4}),
    ("Fe", {"Fe": 1}),
    ("Zn", {"Zn": 1}),
    ("NaHCO3", {"Na": 1, "H": 1, "C": 1, "O": 3}),
]


def draw_label(surface, font, text, color, rect, *, align="left"):
    rendered = font.render(text, True, color)
    if align == "center":
        target = rendered.get_rect(center=pygame.Rect(rect).center)
    elif align == "right":
        target = rendered.get_rect(midright=pygame.Rect(rect).midright)
    else:
        target = rendered.get_rect(topleft=pygame.Rect(rect).topleft)
    surface.blit(rendered, target)


class ReactionEnvironment(BaseEnvironment):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.toolbar = Toolbar(0, 0, 0, 60, self.build_tool_defs())

        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.caption_font = pygame.font.SysFont("Arial", 14)
        self.body_font = pygame.font.SysFont("Arial", 15)
        self.small_font = pygame.font.SysFont("Arial", 12, bold=True)
        self.mono_font = pygame.font.SysFont("Consolas", 14, bold=True)

        self.play_rect = pygame.Rect(0, 0, 0, 0)
        self.side_panel_rect = pygame.Rect(0, 0, 0, 0)
        self.apparatus_rect = pygame.Rect(0, 0, 0, 0)
        self.table_rect = pygame.Rect(0, 0, 0, 0)

        self.flasks = {
            "A": {"counts": {}, "state": "aq", "manual_state": False},
            "B": {"counts": {}, "state": "aq", "manual_state": False},
        }
        self.active_flask = "A"
        self.heat_level = 0
        self.mixed = False
        self.mix_progress = 0.0
        self.visual_time = 0.0
        self.last_tick = pygame.time.get_ticks()
        self.status_message = "Left click an element to add it to the active flask. Right click subtracts."

        self.periodic_hitboxes = []
        self.flask_hitboxes = {}
        self.side_hitboxes = []
        self.reaction = analyze_reaction({}, {}, 0)
        self.side_scroll = 0
        self.side_content_height = 0

        self.update_layout(*self.app.screen.get_size())
        self.recompute_reaction()
        self.toolbar.set_active_tool("select_a")

    def build_tool_defs(self):
        return [
            ("Flask A", "select_a", (122, 166, 224), "Edit Flask A"),
            ("Flask B", "select_b", (122, 166, 224), "Edit Flask B"),
            ("State", "cycle_state", (242, 190, 112), "Cycle the active flask state"),
            ("Clear", "clear_active", (232, 116, 116), "Clear the active flask"),
            ("Mix", "mix_now", (92, 214, 162), "Pour both flasks into the beaker"),
            ("Burner -", "burner_down", (246, 156, 96), "Lower the Bunsen burner intensity"),
            ("Burner +", "burner_up", (246, 156, 96), "Raise the Bunsen burner intensity"),
            ("Reset", "reset_all", (236, 116, 116), "Reset both flasks and the beaker"),
            ("Menu", "exit_to_menu", (70, 78, 92), "Return to Chemistry Labs"),
        ]

    def update_layout(self, w, h):
        toolbar_height = 60
        panel_width = min(380, max(320, int(w * 0.31)))
        self.play_rect = pygame.Rect(0, 0, max(w - panel_width, 1), max(h - toolbar_height, 1))
        self.side_panel_rect = pygame.Rect(self.play_rect.right, 0, panel_width, max(h - toolbar_height, 1))
        self.toolbar.update_layout(x=0, y=h - toolbar_height, width=w, height=toolbar_height)

        apparatus_height = int(self.play_rect.height * 0.48)
        self.apparatus_rect = pygame.Rect(self.play_rect.x + 18, self.play_rect.y + 18, self.play_rect.width - 36, apparatus_height)
        self.table_rect = pygame.Rect(
            self.play_rect.x + 18,
            self.apparatus_rect.bottom + 18,
            self.play_rect.width - 36,
            max(self.play_rect.bottom - self.apparatus_rect.bottom - 36, 180),
        )
        self.rebuild_periodic_hitboxes()

    def rebuild_periodic_hitboxes(self):
        self.periodic_hitboxes = []
        tile_width = max(28, min(42, self.table_rect.width // 18))
        tile_height = max(26, min(36, self.table_rect.height // 7))
        start_x = self.table_rect.x + max((self.table_rect.width - tile_width * 18) // 2, 0)
        start_y = self.table_rect.y + 52

        for element in ELEMENTS_BY_SYMBOL.values():
            rect = pygame.Rect(
                start_x + (element["col"] - 1) * tile_width,
                start_y + (element["row"] - 1) * tile_height,
                tile_width - 2,
                tile_height - 2,
            )
            self.periodic_hitboxes.append({"rect": rect, "element": element})

    def active_counts(self):
        return self.flasks[self.active_flask]["counts"]

    def set_status(self, message):
        self.status_message = message

    def load_preset(self, counts):
        self.flasks[self.active_flask]["counts"] = dict(counts)
        self.flasks[self.active_flask]["manual_state"] = False
        self.update_default_state(self.active_flask)
        self.recompute_reaction()
        self.mixed = False
        self.mix_progress = 0.0
        self.set_status(f"Loaded preset into Flask {self.active_flask}: {classify_compound(counts)['formula']}.")

    def update_default_state(self, flask_key):
        flask = self.flasks[flask_key]
        if flask["manual_state"]:
            return
        flask["state"] = classify_compound(flask["counts"]).get("state", "aq")

    def recompute_reaction(self):
        self.reaction = analyze_reaction(self.flasks["A"]["counts"], self.flasks["B"]["counts"], self.heat_level)

    def cycle_state(self):
        states = ["aq", "liquid", "solid", "gas"]
        flask = self.flasks[self.active_flask]
        current_index = states.index(flask["state"]) if flask["state"] in states else 0
        flask["state"] = states[(current_index + 1) % len(states)]
        flask["manual_state"] = True
        self.set_status(f"Flask {self.active_flask} state set to {flask['state']}.")

    def adjust_active_element(self, symbol, delta):
        flask = self.flasks[self.active_flask]
        counts = dict(flask["counts"])
        counts[symbol] = max(0, counts.get(symbol, 0) + delta)
        counts = {key: value for key, value in counts.items() if value > 0}
        flask["counts"] = counts
        self.update_default_state(self.active_flask)
        self.recompute_reaction()
        self.mixed = False
        self.mix_progress = 0.0
        action = "added to" if delta > 0 else "removed from"
        self.set_status(f"{symbol} {action} Flask {self.active_flask}.")

    def handle_ui(self, action):
        if action == "select_a":
            self.active_flask = "A"
        elif action == "select_b":
            self.active_flask = "B"
        elif action.startswith("preset:"):
            preset_index = int(action.split(":", 1)[1])
            self.load_preset(REACTION_PRESETS[preset_index][1])
        elif action == "cycle_state":
            self.cycle_state()
        elif action == "clear_active":
            self.flasks[self.active_flask] = {"counts": {}, "state": "aq", "manual_state": False}
            self.recompute_reaction()
            self.mixed = False
            self.mix_progress = 0.0
            self.set_status(f"Flask {self.active_flask} cleared.")
        elif action == "mix_now":
            self.mixed = True
            self.mix_progress = 0.0
            self.recompute_reaction()
            self.set_status("The reagents are pouring into the beaker.")
        elif action == "burner_down":
            self.heat_level = max(0, self.heat_level - 1)
            self.recompute_reaction()
        elif action == "burner_up":
            self.heat_level = min(5, self.heat_level + 1)
            self.recompute_reaction()
        elif action == "reset_all":
            self.flasks = {
                "A": {"counts": {}, "state": "aq", "manual_state": False},
                "B": {"counts": {}, "state": "aq", "manual_state": False},
            }
            self.active_flask = "A"
            self.heat_level = 0
            self.mixed = False
            self.mix_progress = 0.0
            self.recompute_reaction()
            self.set_status("Both flasks and the burner were reset.")
        elif action == "exit_to_menu":
            self.app.switch_environment("ChemistryMenu")

        self.toolbar.set_active_tool("select_a" if self.active_flask == "A" else "select_b")

    def handle_event(self, event):
        action = self.toolbar.handle_event(event)
        if action:
            self.handle_ui(action)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for hitbox in self.side_hitboxes:
                    if hitbox["rect"].collidepoint(event.pos):
                        self.handle_ui(hitbox["action"])
                        return
                for flask_key, rect in self.flask_hitboxes.items():
                    if rect.collidepoint(event.pos):
                        self.active_flask = flask_key
                        self.toolbar.set_active_tool("select_a" if flask_key == "A" else "select_b")
                        self.set_status(f"Editing Flask {flask_key}.")
                        return
            if event.button in {1, 3}:
                for tile in self.periodic_hitboxes:
                    if tile["rect"].collidepoint(event.pos):
                        self.adjust_active_element(tile["element"]["symbol"], 1 if event.button == 1 else -1)
                        return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.active_flask = "B" if self.active_flask == "A" else "A"
                self.toolbar.set_active_tool("select_a" if self.active_flask == "A" else "select_b")
            elif event.key == pygame.K_SPACE:
                self.handle_ui("mix_now")
            elif event.key == pygame.K_LEFTBRACKET:
                self.handle_ui("burner_down")
            elif event.key == pygame.K_RIGHTBRACKET:
                self.handle_ui("burner_up")
            elif event.key == pygame.K_BACKSPACE:
                self.handle_ui("clear_active")
        elif event.type == pygame.MOUSEWHEEL and self.side_panel_rect.collidepoint(pygame.mouse.get_pos()):
            viewport_height = max(self.side_panel_rect.height - 28, 1)
            self.side_scroll = clamp_scroll(self.side_scroll - event.y * 32, viewport_height, self.side_content_height)

    def update(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_tick) / 1000.0
        self.last_tick = now
        self.visual_time += dt

        if self.mixed:
            self.mix_progress = clamp(self.mix_progress + dt * (0.55 + self.heat_level * 0.16), 0.0, 1.0)

    def draw_flask(self, surface, rect, flask_key):
        flask = self.flasks[flask_key]
        compound = classify_compound(flask["counts"])
        outline = (126, 208, 255) if self.active_flask == flask_key else (78, 96, 126)
        header_rect = pygame.Rect(rect.x - 8, rect.y - 42, rect.width + 16, 34)
        draw_card(surface, header_rect, (14, 22, 36), outline, alpha=232, radius=12)
        pygame.draw.rect(surface, (214, 224, 236), rect, 3, border_radius=18)

        liquid_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill_height = int(rect.height * 0.58)
        liquid_rect = pygame.Rect(12, rect.bottom - rect.y - fill_height - 10, rect.width - 24, fill_height)
        pygame.draw.rect(liquid_surface, (*compound["color"], 190), liquid_rect, border_radius=14)
        surface.blit(liquid_surface, rect.topleft)

        label = self.hud_font.render(f"Flask {flask_key}", True, (244, 247, 252))
        surface.blit(label, (header_rect.x + 12, header_rect.y + 7))
        formula_text = self.mono_font.render(compound_formula(compound), True, (134, 224, 178))
        formula_target = formula_text.get_rect(midright=(header_rect.right - 10, header_rect.centery))
        surface.blit(formula_text, formula_target)

        state_rect = pygame.Rect(rect.x + 22, rect.bottom + 10, rect.width - 44, 22)
        draw_card(surface, state_rect, (16, 24, 38), (72, 90, 120), alpha=220, radius=10)
        state_label = fit_text(self.caption_font, f"State: {flask['state']}", state_rect.width - 12)
        state_render = self.caption_font.render(state_label, True, (206, 216, 232))
        surface.blit(state_render, state_render.get_rect(center=state_rect.center))

        self.flask_hitboxes[flask_key] = rect.union(header_rect).union(state_rect)

    def draw_burner(self, surface, center_x, bottom_y):
        base_rect = pygame.Rect(center_x - 52, bottom_y - 14, 104, 18)
        stem_rect = pygame.Rect(center_x - 12, bottom_y - 104, 24, 90)
        head_rect = pygame.Rect(center_x - 18, bottom_y - 116, 36, 18)

        pygame.draw.rect(surface, (90, 102, 122), base_rect, border_radius=9)
        pygame.draw.rect(surface, (78, 86, 102), stem_rect, border_radius=8)
        pygame.draw.rect(surface, (118, 126, 144), head_rect, border_radius=8)

        if self.heat_level > 0:
            flame_height = 26 + self.heat_level * 16
            flame_outer = [
                (center_x, bottom_y - 118 - flame_height),
                (center_x - 26, bottom_y - 96),
                (center_x, bottom_y - 56),
                (center_x + 26, bottom_y - 96),
            ]
            flame_inner = [
                (center_x, bottom_y - 112 - flame_height * 0.62),
                (center_x - 12, bottom_y - 92),
                (center_x, bottom_y - 66),
                (center_x + 12, bottom_y - 92),
            ]
            pygame.draw.polygon(surface, (252, 150, 82), flame_outer)
            pygame.draw.polygon(surface, (255, 218, 116), flame_inner)

    def draw_beaker(self, surface, rect):
        pygame.draw.rect(surface, (214, 224, 236), rect, 3, border_radius=18)

        compound_a = classify_compound(self.flasks["A"]["counts"])
        compound_b = classify_compound(self.flasks["B"]["counts"])
        preview_color = (
            int((compound_a["color"][0] + compound_b["color"][0]) / 2),
            int((compound_a["color"][1] + compound_b["color"][1]) / 2),
            int((compound_a["color"][2] + compound_b["color"][2]) / 2),
        )
        final_color = self.reaction.get("product_color", preview_color)
        mix_ratio = self.mix_progress if self.mixed else 0.0
        color = (
            int(preview_color[0] + (final_color[0] - preview_color[0]) * mix_ratio),
            int(preview_color[1] + (final_color[1] - preview_color[1]) * mix_ratio),
            int(preview_color[2] + (final_color[2] - preview_color[2]) * mix_ratio),
        )

        liquid_rect = pygame.Rect(rect.x + 12, rect.bottom - int(rect.height * 0.48), rect.width - 24, int(rect.height * 0.48) - 12)
        pygame.draw.rect(surface, color, liquid_rect, border_radius=14)
        pygame.draw.ellipse(surface, (236, 244, 250), (liquid_rect.x, liquid_rect.y - 8, liquid_rect.width, 18), 1)

        if self.mixed and self.mix_progress < 0.90:
            stream_surface = pygame.Surface(self.play_rect.size, pygame.SRCALPHA)
            left = self.flask_hitboxes["A"].centerx
            right = self.flask_hitboxes["B"].centerx
            top_y = self.apparatus_rect.y + 114
            pygame.draw.line(
                stream_surface,
                (*compound_a["color"], int(168 * (1.0 - self.mix_progress * 0.7))),
                (left, top_y),
                (rect.centerx - 28, rect.y + 26),
                6,
            )
            pygame.draw.line(
                stream_surface,
                (*compound_b["color"], int(168 * (1.0 - self.mix_progress * 0.7))),
                (right, top_y),
                (rect.centerx + 28, rect.y + 26),
                6,
            )
            surface.blit(stream_surface, (0, 0))

        reaction_type = self.reaction.get("type")
        if reaction_type == "gas" and self.mixed and self.mix_progress > 0.15:
            for index in range(16):
                phase = self.visual_time * (1.0 + index * 0.06) + index
                x = liquid_rect.x + 16 + (index * 21) % max(liquid_rect.width - 22, 1)
                y = liquid_rect.bottom - int((math.sin(phase) * 0.5 + 0.5) * liquid_rect.height)
                pygame.draw.circle(surface, (236, 246, 255), (x, y), 3 + index % 3, 1)
        elif reaction_type == "precipitation" and self.mixed and self.mix_progress > 0.12:
            precip_color = self.reaction.get("accent", (244, 244, 244))
            settle_height = int(liquid_rect.height * clamp(self.mix_progress * 0.34, 0.0, 0.34))
            pygame.draw.rect(
                surface,
                precip_color,
                pygame.Rect(liquid_rect.x + 6, liquid_rect.bottom - settle_height, liquid_rect.width - 12, settle_height),
                border_radius=10,
            )
            for index in range(20):
                px = liquid_rect.x + 10 + (index * 19) % max(liquid_rect.width - 18, 1)
                py = liquid_rect.y + 18 + (index * 17) % max(liquid_rect.height - 24, 1)
                pygame.draw.circle(surface, precip_color, (px, py), 2)
        elif reaction_type == "displacement" and self.mixed and self.mix_progress > 0.18:
            strip_rect = pygame.Rect(rect.centerx - 10, rect.y + 34, 20, rect.height - 70)
            pygame.draw.rect(surface, (164, 170, 182), strip_rect, border_radius=7)
            deposit_color = self.reaction.get("accent", (212, 126, 72))
            for index in range(14):
                px = strip_rect.x - 6 + (index % 2) * 28
                py = strip_rect.y + 12 + (index * 13) % max(strip_rect.height - 18, 1)
                pygame.draw.circle(surface, deposit_color, (px, py), 4)
        elif reaction_type == "neutralization" and self.mixed and self.mix_progress > 0.10:
            aura = pygame.Surface((rect.width + 80, rect.height + 80), pygame.SRCALPHA)
            pygame.draw.ellipse(aura, (*self.reaction.get("accent", (250, 168, 94)), 44), aura.get_rect())
            surface.blit(aura, (rect.x - 40, rect.y - 52))

    def draw_periodic_table(self, surface):
        draw_card(surface, self.table_rect, (10, 18, 32), (72, 90, 120))
        surface.blit(self.hud_font.render("Periodic Table Builder", True, (244, 247, 252)), (self.table_rect.x + 14, self.table_rect.y + 10))
        surface.blit(
            self.caption_font.render("Left click adds to the active flask. Right click subtracts.", True, (196, 208, 224)),
            (self.table_rect.x + 14, self.table_rect.y + 30),
        )

        for tile in self.periodic_hitboxes:
            rect = tile["rect"]
            element = tile["element"]
            pygame.draw.rect(surface, element["color"], rect, border_radius=6)
            pygame.draw.rect(surface, (58, 68, 84), rect, 1, border_radius=6)
            draw_label(surface, self.small_font, element["symbol"], (16, 22, 30), rect.inflate(-4, -2), align="center")

    def draw_apparatus(self, surface):
        draw_card(surface, self.apparatus_rect, (10, 18, 32), (72, 90, 120))
        inner = self.apparatus_rect.inflate(-28, -28)
        status_rect = pygame.Rect(inner.x, inner.y + 6, inner.width, 72)
        draw_card(surface, status_rect, (16, 24, 38), (78, 96, 126), alpha=232, radius=14)
        surface.blit(self.hud_font.render("Reaction Lab", True, (244, 247, 252)), (status_rect.x + 12, status_rect.y + 8))
        burner_text = self.caption_font.render(f"Bunsen burner intensity: {self.heat_level}/5", True, (208, 220, 234))
        surface.blit(burner_text, (status_rect.right - burner_text.get_width() - 12, status_rect.y + 10))
        draw_text_block(
            surface,
            self.caption_font,
            self.reaction.get("observation", "Ready for a reaction"),
            (138, 216, 255),
            pygame.Rect(status_rect.x + 12, status_rect.y + 32, status_rect.width - 24, 16),
            line_gap=1,
        )
        draw_text_block(
            surface,
            self.caption_font,
            self.status_message,
            (206, 216, 232),
            pygame.Rect(status_rect.x + 12, status_rect.y + 50, status_rect.width - 24, 16),
            line_gap=1,
        )

        flask_top = status_rect.bottom + 52
        flask_rect_a = pygame.Rect(inner.x + 30, flask_top, 118, 160)
        flask_rect_b = pygame.Rect(inner.right - 148, flask_top, 118, 160)
        beaker_rect = pygame.Rect(inner.centerx - 102, status_rect.bottom + 94, 204, 170)

        self.flask_hitboxes = {}
        self.draw_flask(surface, flask_rect_a, "A")
        self.draw_flask(surface, flask_rect_b, "B")
        self.draw_beaker(surface, beaker_rect)
        self.draw_burner(surface, beaker_rect.centerx, beaker_rect.bottom + 72)

    def draw_compound_block(self, surface, rect, title, flask_key):
        flask = self.flasks[flask_key]
        compound = classify_compound(flask["counts"])
        draw_card(surface, rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        surface.blit(self.hud_font.render(title, True, (244, 247, 252)), (rect.x + 12, rect.y + 10))
        surface.blit(self.mono_font.render(compound_formula(compound), True, (134, 224, 178)), (rect.x + 12, rect.y + 34))
        surface.blit(self.caption_font.render(f"State: {flask['state']}", True, (206, 216, 232)), (rect.x + 12, rect.y + 58))
        name_text = fit_text(self.caption_font, compound["name"], rect.width - 24)
        surface.blit(self.caption_font.render(name_text, True, (206, 216, 232)), (rect.x + 12, rect.y + 78))
        draw_text_block(
            surface,
            self.caption_font,
            describe_formula_counts(flask["counts"]),
            (196, 208, 224),
            pygame.Rect(rect.x + 12, rect.y + 102, rect.width - 24, 52),
            line_gap=2,
        )
        draw_text_block(
            surface,
            self.caption_font,
            compound["reading"],
            (196, 208, 224),
            pygame.Rect(rect.x + 12, rect.y + 154, rect.width - 24, rect.height - 168),
            line_gap=2,
        )

    def draw_side_button(self, surface, rect, label, action, color):
        if hasattr(self, "_side_interaction_origin"):
            ox, oy = self._side_interaction_origin
            self.side_hitboxes.append({"rect": rect.move(ox, oy), "action": action})
        else:
            self.side_hitboxes.append({"rect": rect, "action": action})
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (64, 76, 94), rect, 1, border_radius=8)
        text_color = (18, 22, 28) if sum(color) > 420 else (244, 247, 252)
        text = self.caption_font.render(fit_text(self.caption_font, label, rect.width - 10), True, text_color)
        surface.blit(text, text.get_rect(center=rect.center))

    def draw_side_panel(self, surface):
        draw_gradient(surface, self.side_panel_rect, (16, 22, 36), (8, 11, 20))
        draw_card(surface, self.side_panel_rect.inflate(-14, -14), (12, 18, 30), (60, 74, 98), alpha=228)

        viewport = self.side_panel_rect.inflate(-20, -20)
        content_surface = pygame.Surface((viewport.width, 1320), pygame.SRCALPHA)
        inner = content_surface.get_rect()
        self.side_hitboxes = []
        self._side_interaction_origin = (viewport.x, viewport.y - self.side_scroll)
        content_surface.blit(self.title_font.render("Bench Reading", True, (244, 247, 252)), (inner.x, inner.y))
        content_surface.blit(self.caption_font.render("The simulator only asserts products when the rule engine recognizes the chemistry.", True, (188, 202, 222)), (inner.x, inner.y + 34))

        cols = 3
        button_height = 30
        preset_rows = math.ceil(len(REACTION_PRESETS) / cols)
        preset_height = 72 + preset_rows * button_height + max(preset_rows - 1, 0) * 8 + 12
        preset_rect = pygame.Rect(inner.x, inner.y + 64, inner.width, preset_height)
        draw_card(content_surface, preset_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Quick Reagents", True, (244, 247, 252)), (preset_rect.x + 12, preset_rect.y + 10))
        content_surface.blit(self.caption_font.render(f"Loads into active Flask {self.active_flask}", True, (130, 210, 255)), (preset_rect.x + 12, preset_rect.y + 34))

        button_width = (preset_rect.width - 24 - (cols - 1) * 8) // cols
        for index, (label, _) in enumerate(REACTION_PRESETS):
            row = index // cols
            col = index % cols
            rect = pygame.Rect(
                preset_rect.x + 12 + col * (button_width + 8),
                preset_rect.y + 60 + row * (button_height + 8),
                button_width,
                button_height,
            )
            color = (98, 214, 180) if self.active_flask == "A" else (122, 166, 224)
            self.draw_side_button(content_surface, rect, label, f"preset:{index}", color)

        block_height = 220
        first_block = pygame.Rect(inner.x, preset_rect.bottom + 14, inner.width, block_height)
        second_block = pygame.Rect(inner.x, first_block.bottom + 14, inner.width, block_height)
        reaction_block = pygame.Rect(inner.x, second_block.bottom + 14, inner.width, 248)
        guide_block = pygame.Rect(inner.x, reaction_block.bottom + 14, inner.width, 164)

        self.draw_compound_block(content_surface, first_block, "Flask A", "A")
        self.draw_compound_block(content_surface, second_block, "Flask B", "B")

        draw_card(content_surface, reaction_block, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Reaction Output", True, (244, 247, 252)), (reaction_block.x + 12, reaction_block.y + 10))
        content_surface.blit(self.caption_font.render(f"Confidence: {self.reaction.get('confidence', 'n/a')}", True, (130, 210, 255)), (reaction_block.x + 12, reaction_block.y + 34))
        draw_text_block(
            content_surface,
            self.body_font,
            self.reaction.get("equation", ""),
            (220, 227, 238),
            pygame.Rect(reaction_block.x + 12, reaction_block.y + 58, reaction_block.width - 24, 46),
        )
        draw_text_block(
            content_surface,
            self.body_font,
            self.reaction.get("reading", ""),
            (220, 227, 238),
            pygame.Rect(reaction_block.x + 12, reaction_block.y + 108, reaction_block.width - 24, reaction_block.height - 120),
        )

        draw_card(content_surface, guide_block, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Use Tips", True, (244, 247, 252)), (guide_block.x + 12, guide_block.y + 10))
        draw_text_block(
            content_surface,
            self.caption_font,
            "Click a flask label or toolbar tab to choose which reagent you are editing. Left click an element in the periodic table to add it, right click to remove it, and scroll this panel when the reading extends below the visible window.",
            (206, 216, 232),
            pygame.Rect(guide_block.x + 12, guide_block.y + 36, guide_block.width - 24, guide_block.height - 48),
            line_gap=2,
        )

        self.side_content_height = guide_block.bottom + 12
        self.side_scroll = blit_scroll_surface(surface, content_surface, viewport, self.side_scroll)
        del self._side_interaction_origin

    def render(self, surface):
        draw_gradient(surface, self.play_rect, (20, 28, 44), (8, 12, 22))
        self.draw_apparatus(surface)
        self.draw_periodic_table(surface)
        self.draw_side_panel(surface)
