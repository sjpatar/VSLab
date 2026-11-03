import math

import pygame

from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.environments.chemistry.common import (
    blit_scroll_surface,
    clamp,
    clamp_scroll,
    draw_card,
    draw_gradient,
    draw_grid,
    draw_text_block,
    fit_text,
    lerp_color,
)
from vsl.environments.chemistry.chemistry_models import KNOWN_BY_KEY, TITRATION_SPECIES


KW = 1e-14

INDICATORS = [
    {"name": "Phenolphthalein", "low": 8.2, "high": 10.0, "acid_color": (242, 245, 250), "base_color": (238, 120, 194)},
    {"name": "Methyl Orange", "low": 3.1, "high": 4.4, "acid_color": (242, 102, 76), "base_color": (255, 208, 88)},
    {"name": "Bromothymol Blue", "low": 6.0, "high": 7.6, "acid_color": (245, 205, 92), "base_color": (88, 154, 242)},
    {"name": "Universal Indicator", "low": 4.0, "high": 10.0, "acid_color": (232, 118, 78), "base_color": (94, 174, 248)},
]


def safe_log10(value):
    return math.log10(max(value, 1e-12))


def titration_compound(spec):
    return KNOWN_BY_KEY[spec["compound_key"]]


def species_label(spec):
    compound = titration_compound(spec)
    return f"{spec['label']} ({compound['name']})"


def indicator_color(indicator, pH):
    if pH <= indicator["low"]:
        return indicator["acid_color"]
    if pH >= indicator["high"]:
        return indicator["base_color"]
    blend = (pH - indicator["low"]) / max(indicator["high"] - indicator["low"], 1e-6)
    return lerp_color(indicator["acid_color"], indicator["base_color"], blend)


def analyze_titration(analyte, titrant, analyte_concentration, titrant_concentration, analyte_volume_ml, added_volume_ml):
    if analyte["role"] == titrant["role"]:
        return {
            "valid": False,
            "pH": 7.0,
            "equivalence_ml": 0.0,
            "total_volume_ml": analyte_volume_ml + added_volume_ml,
            "region": "invalid",
            "observation": "Select one acid and one base to create a titration pair.",
            "progress": 0.0,
            "slope": 0.0,
        }

    analyte_volume_l = analyte_volume_ml / 1000.0
    titrant_volume_l = max(added_volume_ml, 0.0) / 1000.0
    total_volume_l = max(analyte_volume_l + titrant_volume_l, 1e-9)
    analyte_moles = analyte_concentration * analyte_volume_l
    titrant_moles = titrant_concentration * titrant_volume_l
    equivalence_ml = (analyte_moles / max(titrant_concentration, 1e-9)) * 1000.0

    if analyte["role"] == "acid":
        acid = analyte
        base = titrant
        acid_moles = analyte_moles
        base_moles = titrant_moles
        acid_in_flask = True
    else:
        acid = titrant
        base = analyte
        acid_moles = titrant_moles
        base_moles = analyte_moles
        acid_in_flask = False

    region = "initial"
    if acid_in_flask:
        if acid["strength"] == "strong":
            if base_moles < acid_moles:
                hydronium = (acid_moles - base_moles) / total_volume_l
                pH = -safe_log10(hydronium)
                region = "acid_excess"
            elif math.isclose(base_moles, acid_moles, rel_tol=0.0, abs_tol=1e-9):
                pH = 7.0
                region = "equivalence"
            else:
                hydroxide = (base_moles - acid_moles) / total_volume_l
                pH = 14.0 + safe_log10(hydroxide)
                region = "base_excess"
        else:
            pKa = acid["pKa"]
            Ka = 10 ** (-pKa)
            if base_moles <= 1e-12:
                hydronium = math.sqrt(Ka * analyte_concentration)
                pH = -safe_log10(hydronium)
                region = "initial"
            elif base_moles < acid_moles:
                weak_left = acid_moles - base_moles
                conjugate = base_moles
                pH = pKa + safe_log10(conjugate / max(weak_left, 1e-12))
                region = "buffer"
            elif math.isclose(base_moles, acid_moles, rel_tol=0.0, abs_tol=1e-9):
                conjugate_base = acid_moles / total_volume_l
                Kb = KW / Ka
                hydroxide = math.sqrt(max(Kb * conjugate_base, 1e-12))
                pH = 14.0 + safe_log10(hydroxide)
                region = "equivalence"
            else:
                hydroxide = (base_moles - acid_moles) / total_volume_l
                pH = 14.0 + safe_log10(hydroxide)
                region = "base_excess"
    else:
        if base["strength"] == "strong":
            if acid_moles < base_moles:
                hydroxide = (base_moles - acid_moles) / total_volume_l
                pH = 14.0 + safe_log10(hydroxide)
                region = "base_excess"
            elif math.isclose(acid_moles, base_moles, rel_tol=0.0, abs_tol=1e-9):
                pH = 7.0
                region = "equivalence"
            else:
                hydronium = (acid_moles - base_moles) / total_volume_l
                pH = -safe_log10(hydronium)
                region = "acid_excess"
        else:
            pKb = base["pKb"]
            Kb = 10 ** (-pKb)
            if acid_moles <= 1e-12:
                hydroxide = math.sqrt(Kb * analyte_concentration)
                pH = 14.0 + safe_log10(hydroxide)
                region = "initial"
            elif acid_moles < base_moles:
                weak_left = base_moles - acid_moles
                conjugate = acid_moles
                pOH = pKb + safe_log10(conjugate / max(weak_left, 1e-12))
                pH = 14.0 - pOH
                region = "buffer"
            elif math.isclose(acid_moles, base_moles, rel_tol=0.0, abs_tol=1e-9):
                conjugate_acid = base_moles / total_volume_l
                Ka = KW / Kb
                hydronium = math.sqrt(max(Ka * conjugate_acid, 1e-12))
                pH = -safe_log10(hydronium)
                region = "equivalence"
            else:
                hydronium = (acid_moles - base_moles) / total_volume_l
                pH = -safe_log10(hydronium)
                region = "acid_excess"

    pH = clamp(pH, 0.0, 14.0)

    if region == "buffer":
        observation = "The solution is in the buffer region, so the conjugate pair resists sharp pH changes."
    elif region == "equivalence":
        observation = "The titration is at the equivalence neighborhood, where tiny additions cause the biggest pH swing."
    elif region == "acid_excess":
        observation = "Acid remains in excess, so the flask is still controlled by hydronium concentration."
    elif region == "base_excess":
        observation = "Base is now in excess, so hydroxide controls the pH."
    else:
        observation = "The initial flask chemistry is setting the starting point of the titration curve."

    return {
        "valid": True,
        "pH": pH,
        "equivalence_ml": equivalence_ml,
        "total_volume_ml": analyte_volume_ml + added_volume_ml,
        "region": region,
        "observation": observation,
        "progress": clamp(added_volume_ml / max(equivalence_ml, 1e-9), 0.0, 2.0),
        "slope": 0.0,
    }


class TitrationEnvironment(BaseEnvironment):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.toolbar = Toolbar(0, 0, 0, 60, self.build_tool_defs())

        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.caption_font = pygame.font.SysFont("Arial", 14)
        self.body_font = pygame.font.SysFont("Arial", 15)
        self.mono_font = pygame.font.SysFont("Consolas", 14, bold=True)

        self.play_rect = pygame.Rect(0, 0, 0, 0)
        self.side_panel_rect = pygame.Rect(0, 0, 0, 0)
        self.apparatus_rect = pygame.Rect(0, 0, 0, 0)
        self.curve_rect = pygame.Rect(0, 0, 0, 0)

        self.analyte_index = 0
        self.titrant_index = 4
        self.indicator_index = 0
        self.analyte_concentration = 0.10
        self.titrant_concentration = 0.10
        self.analyte_volume_ml = 25.0
        self.step_volume_ml = 0.20
        self.max_burette_volume_ml = 60.0
        self.added_volume_ml = 0.0
        self.auto_mode = False
        self.droplet_time = 0.0
        self.last_tick = pygame.time.get_ticks()

        self.curve_points = []
        self.state = None
        self.side_hitboxes = []
        self.side_scroll = 0
        self.side_content_height = 0
        self.status_message = "Configure the analyte and titrant on the right, then add titrant from the burette."

        self.update_layout(*self.app.screen.get_size())
        self.recompute_curve()

    def build_tool_defs(self):
        return [
            ("Dose -", "dose_back", (122, 166, 224), "Remove one configured step from the burette total"),
            ("Dose +", "dose_forward", (92, 214, 162), "Add one configured step of titrant"),
            ("+1.0 mL", "dose_large", (92, 214, 162), "Add a full millilitre"),
            ("Auto", "toggle_auto", (104, 170, 246), "Run a continuous drip"),
            ("Reset", "reset_trial", (236, 116, 116), "Reset the burette and flask"),
            ("Menu", "exit_to_menu", (70, 78, 92), "Return to Chemistry Labs"),
        ]

    def analyte(self):
        return TITRATION_SPECIES[self.analyte_index]

    def titrant(self):
        return TITRATION_SPECIES[self.titrant_index]

    def indicator(self):
        return INDICATORS[self.indicator_index]

    def current_state(self):
        return analyze_titration(
            self.analyte(),
            self.titrant(),
            self.analyte_concentration,
            self.titrant_concentration,
            self.analyte_volume_ml,
            self.added_volume_ml,
        )

    def recompute_curve(self):
        self.state = self.current_state()
        self.curve_points = []
        samples = 180
        for index in range(samples + 1):
            volume = self.max_burette_volume_ml * (index / samples)
            state = analyze_titration(
                self.analyte(),
                self.titrant(),
                self.analyte_concentration,
                self.titrant_concentration,
                self.analyte_volume_ml,
                volume,
            )
            self.curve_points.append((volume, state["pH"]))

        if self.state["valid"]:
            left = analyze_titration(
                self.analyte(),
                self.titrant(),
                self.analyte_concentration,
                self.titrant_concentration,
                self.analyte_volume_ml,
                max(self.added_volume_ml - 0.1, 0.0),
            )
            right = analyze_titration(
                self.analyte(),
                self.titrant(),
                self.analyte_concentration,
                self.titrant_concentration,
                self.analyte_volume_ml,
                min(self.added_volume_ml + 0.1, self.max_burette_volume_ml),
            )
            self.state["slope"] = (right["pH"] - left["pH"]) / max(0.2, abs((self.added_volume_ml + 0.1) - max(self.added_volume_ml - 0.1, 0.0)))

    def update_layout(self, w, h):
        toolbar_height = 60
        panel_width = min(390, max(330, int(w * 0.32)))
        self.play_rect = pygame.Rect(0, 0, max(w - panel_width, 1), max(h - toolbar_height, 1))
        self.side_panel_rect = pygame.Rect(self.play_rect.right, 0, panel_width, max(h - toolbar_height, 1))
        self.toolbar.update_layout(x=0, y=h - toolbar_height, width=w, height=toolbar_height)

        apparatus_height = int(self.play_rect.height * 0.56)
        self.apparatus_rect = pygame.Rect(self.play_rect.x + 18, self.play_rect.y + 18, self.play_rect.width - 36, apparatus_height)
        self.curve_rect = pygame.Rect(
            self.play_rect.x + 18,
            self.apparatus_rect.bottom + 18,
            self.play_rect.width - 36,
            max(self.play_rect.bottom - self.apparatus_rect.bottom - 36, 140),
        )

    def reset_trial(self):
        self.added_volume_ml = 0.0
        self.auto_mode = False
        self.droplet_time = 0.0
        self.toolbar.set_active_tool(None)
        self.recompute_curve()

    def dose(self, volume_ml):
        self.added_volume_ml = clamp(self.added_volume_ml + volume_ml, 0.0, self.max_burette_volume_ml)
        self.droplet_time = 0.35
        self.recompute_curve()

    def modify_setting(self, action):
        if action == "analyte_prev":
            self.analyte_index = (self.analyte_index - 1) % len(TITRATION_SPECIES)
        elif action == "analyte_next":
            self.analyte_index = (self.analyte_index + 1) % len(TITRATION_SPECIES)
        elif action == "titrant_prev":
            self.titrant_index = (self.titrant_index - 1) % len(TITRATION_SPECIES)
        elif action == "titrant_next":
            self.titrant_index = (self.titrant_index + 1) % len(TITRATION_SPECIES)
        elif action == "analyte_conc_down":
            self.analyte_concentration = clamp(self.analyte_concentration - 0.05, 0.05, 2.00)
        elif action == "analyte_conc_up":
            self.analyte_concentration = clamp(self.analyte_concentration + 0.05, 0.05, 2.00)
        elif action == "titrant_conc_down":
            self.titrant_concentration = clamp(self.titrant_concentration - 0.05, 0.05, 2.00)
        elif action == "titrant_conc_up":
            self.titrant_concentration = clamp(self.titrant_concentration + 0.05, 0.05, 2.00)
        elif action == "volume_down":
            self.analyte_volume_ml = clamp(self.analyte_volume_ml - 5.0, 10.0, 100.0)
        elif action == "volume_up":
            self.analyte_volume_ml = clamp(self.analyte_volume_ml + 5.0, 10.0, 100.0)
        elif action == "step_down":
            self.step_volume_ml = clamp(self.step_volume_ml - 0.05, 0.05, 5.0)
        elif action == "step_up":
            self.step_volume_ml = clamp(self.step_volume_ml + 0.05, 0.05, 5.0)
        elif action == "indicator_prev":
            self.indicator_index = (self.indicator_index - 1) % len(INDICATORS)
        elif action == "indicator_next":
            self.indicator_index = (self.indicator_index + 1) % len(INDICATORS)
        else:
            return

        self.reset_trial()

    def handle_ui(self, action):
        if action == "dose_back":
            self.dose(-self.step_volume_ml)
        elif action == "dose_forward":
            self.dose(self.step_volume_ml)
        elif action == "dose_large":
            self.dose(1.0)
        elif action == "toggle_auto":
            self.auto_mode = not self.auto_mode
            self.toolbar.set_active_tool("toggle_auto" if self.auto_mode else None)
        elif action == "reset_trial":
            self.reset_trial()
        elif action == "exit_to_menu":
            self.app.switch_environment("ChemistryMenu")
        else:
            self.modify_setting(action)

    def handle_event(self, event):
        action = self.toolbar.handle_event(event)
        if action:
            self.handle_ui(action)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for hitbox in self.side_hitboxes:
                if hitbox["rect"].collidepoint(event.pos):
                    self.handle_ui(hitbox["action"])
                    return

        if event.type == pygame.MOUSEWHEEL:
            if self.side_panel_rect.collidepoint(pygame.mouse.get_pos()):
                viewport_height = max(self.side_panel_rect.height - 28, 1)
                self.side_scroll = clamp_scroll(self.side_scroll - event.y * 32, viewport_height, self.side_content_height)
            else:
                self.dose(self.step_volume_ml * event.y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.handle_ui("toggle_auto")
            elif event.key == pygame.K_r:
                self.handle_ui("reset_trial")
            elif event.key == pygame.K_LEFT:
                self.handle_ui("dose_back")
            elif event.key == pygame.K_RIGHT:
                self.handle_ui("dose_forward")

    def update(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_tick) / 1000.0
        self.last_tick = now

        if self.auto_mode:
            self.dose(self.step_volume_ml * dt * 2.0)

        self.droplet_time = max(0.0, self.droplet_time - dt)

    def draw_stepper(self, surface, rect, label, value, action_left, action_right):
        left_rect = pygame.Rect(rect.x, rect.y, 26, 24)
        right_rect = pygame.Rect(rect.right - 26, rect.y, 26, 24)
        if hasattr(self, "_side_interaction_origin"):
            ox, oy = self._side_interaction_origin
            self.side_hitboxes.append({"rect": left_rect.move(ox, oy), "action": action_left})
            self.side_hitboxes.append({"rect": right_rect.move(ox, oy), "action": action_right})
        else:
            self.side_hitboxes.append({"rect": left_rect, "action": action_left})
            self.side_hitboxes.append({"rect": right_rect, "action": action_right})

        pygame.draw.rect(surface, (92, 108, 136), left_rect, border_radius=6)
        pygame.draw.rect(surface, (92, 108, 136), right_rect, border_radius=6)
        surface.blit(self.hud_font.render("-", True, (255, 255, 255)), (rect.x + 8, rect.y + 1))
        surface.blit(self.hud_font.render("+", True, (255, 255, 255)), (rect.right - 18, rect.y + 1))
        surface.blit(self.caption_font.render(label, True, (212, 220, 232)), (rect.x, rect.y - 18))
        fitted = fit_text(self.caption_font, value, max(rect.width - 78, 40))
        surface.blit(self.caption_font.render(fitted, True, (244, 247, 252)), (rect.x + 36, rect.y + 4))

    def draw_apparatus(self, surface):
        draw_card(surface, self.apparatus_rect, (10, 18, 34), (72, 92, 126))
        draw_grid(surface, self.apparatus_rect, 44, (26, 38, 60))

        inner = self.apparatus_rect.inflate(-28, -24)
        status_rect = pygame.Rect(inner.x, inner.y, inner.width, 62)
        draw_card(surface, status_rect, (16, 24, 42), (78, 102, 140), alpha=236, radius=14)
        surface.blit(self.hud_font.render("Titration Bench", True, (244, 247, 252)), (status_rect.x + 12, status_rect.y + 10))
        mode_text = "Auto drip running" if self.auto_mode else "Manual dosing"
        mode_color = (120, 224, 170) if self.auto_mode else (206, 216, 232)
        mode_render = self.caption_font.render(mode_text, True, mode_color)
        surface.blit(mode_render, (status_rect.right - mode_render.get_width() - 12, status_rect.y + 12))
        draw_text_block(
            surface,
            self.caption_font,
            "Wheel outside the panel doses titrant. Scroll the right panel for reading.",
            (188, 202, 222),
            pygame.Rect(status_rect.x + 12, status_rect.y + 32, status_rect.width - mode_render.get_width() - 36, 18),
            line_gap=1,
        )
        content_top = status_rect.bottom + 14
        bottom_band_top = inner.bottom - 48

        burette_rect = pygame.Rect(inner.x + 26, content_top + 8, 42, max(bottom_band_top - content_top - 16, 120))
        info_width = min(186, max(142, int(inner.width * 0.25)))
        flask_width = min(256, max(196, inner.width - burette_rect.width - info_width - 110))
        flask_height = min(196, max(152, bottom_band_top - content_top - 28))
        flask_rect = pygame.Rect(
            burette_rect.right + max(34, int(inner.width * 0.08)),
            bottom_band_top - flask_height,
            flask_width,
            flask_height,
        )
        if flask_rect.right > inner.right - info_width - 18:
            flask_rect.right = inner.right - info_width - 18
        meter_rect = pygame.Rect(inner.right - info_width, content_top + 8, info_width, 110)

        pygame.draw.rect(surface, (212, 226, 244), burette_rect, 2, border_radius=12)
        fill_top = int(burette_rect.height * (self.added_volume_ml / self.max_burette_volume_ml))
        if fill_top < burette_rect.height - 8:
            liquid_rect = pygame.Rect(
                burette_rect.x + 5,
                burette_rect.y + 5 + fill_top,
                burette_rect.width - 10,
                burette_rect.height - fill_top - 10,
            )
            pygame.draw.rect(surface, (112, 184, 255), liquid_rect, border_radius=10)

        nozzle_x = burette_rect.centerx
        pygame.draw.line(surface, (212, 226, 244), (nozzle_x, burette_rect.bottom), (nozzle_x, burette_rect.bottom + 40), 3)
        pygame.draw.line(surface, (212, 226, 244), (nozzle_x, burette_rect.bottom + 40), (flask_rect.centerx - 60, burette_rect.bottom + 40), 3)
        pygame.draw.line(surface, (212, 226, 244), (flask_rect.centerx - 60, burette_rect.bottom + 40), (flask_rect.centerx - 60, flask_rect.y + 18), 3)

        flask_outline = [
            (flask_rect.centerx - 26, flask_rect.y),
            (flask_rect.centerx + 26, flask_rect.y),
            (flask_rect.centerx + 16, flask_rect.y + 28),
            (flask_rect.right - 34, flask_rect.bottom - 16),
            (flask_rect.left + 34, flask_rect.bottom - 16),
            (flask_rect.centerx - 16, flask_rect.y + 28),
        ]
        pygame.draw.polygon(surface, (212, 226, 244), flask_outline, 3)
        pygame.draw.line(surface, (212, 226, 244), (flask_rect.left + 40, flask_rect.bottom - 16), (flask_rect.right - 40, flask_rect.bottom - 16), 3)

        fluid_color = indicator_color(self.indicator(), self.state["pH"])
        liquid_surface = pygame.Surface(flask_rect.size, pygame.SRCALPHA)
        level = clamp(0.30 + 0.18 * min(self.state["total_volume_ml"] / 60.0, 1.0), 0.0, 0.78)
        fill_top = int(flask_rect.height * (1.0 - level))
        pygame.draw.rect(
            liquid_surface,
            (*fluid_color, 184),
            pygame.Rect(40, fill_top, flask_rect.width - 80, flask_rect.height - fill_top - 36),
            border_radius=20,
        )
        pygame.draw.ellipse(
            liquid_surface,
            (*fluid_color, 210),
            pygame.Rect(28, fill_top + 26, flask_rect.width - 56, flask_rect.height - fill_top - 46),
        )
        surface.blit(liquid_surface, flask_rect.topleft)

        if self.auto_mode or self.droplet_time > 0.0:
            drop_y = flask_rect.y + 12 + int((math.sin(pygame.time.get_ticks() * 0.012) + 1.0) * 18)
            pygame.draw.circle(surface, (118, 190, 255), (flask_rect.centerx - 60, drop_y), 5)
            pygame.draw.circle(surface, (184, 220, 255), (flask_rect.centerx - 60, drop_y), 2)

        draw_card(surface, meter_rect, (18, 26, 44), (72, 98, 138), alpha=236, radius=14)
        surface.blit(self.hud_font.render("Live Meter", True, (244, 247, 252)), (meter_rect.x + 14, meter_rect.y + 12))
        surface.blit(self.mono_font.render(f"pH  {self.state['pH']:5.2f}", True, (134, 224, 178)), (meter_rect.x + 14, meter_rect.y + 40))
        surface.blit(self.mono_font.render(f"pOH {14.0 - self.state['pH']:5.2f}", True, (206, 216, 232)), (meter_rect.x + 14, meter_rect.y + 62))
        surface.blit(self.caption_font.render(f"Eq. volume: {self.state['equivalence_ml']:5.2f} mL", True, (196, 208, 224)), (meter_rect.x + 14, meter_rect.y + 84))

        scale_rect = pygame.Rect(flask_rect.x + 14, bottom_band_top + 8, flask_rect.width - 28, 18)
        pygame.draw.rect(surface, (32, 42, 60), scale_rect, border_radius=9)
        progress_width = int(scale_rect.width * clamp(self.state["progress"] / 1.5, 0.0, 1.0))
        progress_color = (112, 214, 162) if self.state["progress"] <= 1.0 else (244, 136, 116)
        if progress_width > 0:
            pygame.draw.rect(surface, progress_color, (scale_rect.x, scale_rect.y, progress_width, scale_rect.height), border_radius=9)
        pygame.draw.rect(surface, (74, 92, 122), scale_rect, 1, border_radius=9)
        added_text = self.caption_font.render(f"Added titrant: {self.added_volume_ml:5.2f} mL", True, (206, 216, 232))
        surface.blit(added_text, (scale_rect.x, scale_rect.y - 18))

    def draw_curve(self, surface):
        draw_card(surface, self.curve_rect, (10, 18, 34), (72, 92, 126))
        surface.blit(self.hud_font.render("Titration Curve", True, (244, 247, 252)), (self.curve_rect.x + 16, self.curve_rect.y + 12))

        plot_rect = self.curve_rect.inflate(-28, -34)
        plot_rect.y += 18
        plot_rect.height -= 18

        pygame.draw.rect(surface, (14, 22, 38), plot_rect, border_radius=12)
        pygame.draw.rect(surface, (66, 82, 112), plot_rect, 1, border_radius=12)

        for pH_tick in range(0, 15, 2):
            y = plot_rect.bottom - int((pH_tick / 14.0) * plot_rect.height)
            pygame.draw.line(surface, (30, 44, 70), (plot_rect.x, y), (plot_rect.right, y), 1)
            surface.blit(self.caption_font.render(str(pH_tick), True, (182, 194, 210)), (plot_rect.x + 6, y - 16))

        points = []
        for volume, pH in self.curve_points:
            px = plot_rect.x + int((volume / self.max_burette_volume_ml) * plot_rect.width)
            py = plot_rect.bottom - int((pH / 14.0) * plot_rect.height)
            points.append((px, py))

        if len(points) >= 2:
            pygame.draw.lines(surface, (120, 208, 255), False, points, 3)

        if self.state["valid"]:
            eq_x = plot_rect.x + int((self.state["equivalence_ml"] / self.max_burette_volume_ml) * plot_rect.width)
            pygame.draw.line(surface, (252, 196, 92), (eq_x, plot_rect.y), (eq_x, plot_rect.bottom), 2)

        current_x = plot_rect.x + int((self.added_volume_ml / self.max_burette_volume_ml) * plot_rect.width)
        current_y = plot_rect.bottom - int((self.state["pH"] / 14.0) * plot_rect.height)
        pygame.draw.circle(surface, (255, 255, 255), (current_x, current_y), 7)
        pygame.draw.circle(surface, indicator_color(self.indicator(), self.state["pH"]), (current_x, current_y), 4)

        surface.blit(self.caption_font.render("0 mL", True, (184, 196, 214)), (plot_rect.x, plot_rect.bottom + 6))
        end_label = self.caption_font.render(f"{self.max_burette_volume_ml:.0f} mL titrant", True, (184, 196, 214))
        surface.blit(end_label, (plot_rect.right - end_label.get_width(), plot_rect.bottom + 6))

    def draw_side_panel(self, surface):
        draw_gradient(surface, self.side_panel_rect, (16, 22, 36), (8, 11, 20))
        draw_card(surface, self.side_panel_rect.inflate(-14, -14), (12, 18, 30), (60, 74, 98), alpha=228)

        viewport = self.side_panel_rect.inflate(-20, -20)
        content_height = 860
        content_surface = pygame.Surface((viewport.width, content_height), pygame.SRCALPHA)
        inner = content_surface.get_rect()
        self.side_hitboxes = []
        self._side_interaction_origin = (viewport.x, viewport.y - self.side_scroll)

        analyte = self.analyte()
        titrant = self.titrant()
        indicator = self.indicator()
        analyte_compound = titration_compound(analyte)
        titrant_compound = titration_compound(titrant)
        indicator_fit = "choose acid/base pair"
        if self.state["valid"]:
            eq_state = analyze_titration(
                analyte,
                titrant,
                self.analyte_concentration,
                self.titrant_concentration,
                self.analyte_volume_ml,
                self.state["equivalence_ml"],
            )
            center = (indicator["low"] + indicator["high"]) / 2.0
            indicator_fit = "good" if indicator["low"] <= eq_state["pH"] <= indicator["high"] or abs(eq_state["pH"] - center) < 1.4 else "narrow"

        content_surface.blit(self.title_font.render("Titration Bench", True, (244, 247, 252)), (inner.x, inner.y))
        content_surface.blit(self.caption_font.render("This lab keeps to acid-base systems the model can calculate directly and reliably.", True, (188, 202, 222)), (inner.x, inner.y + 34))

        y = inner.y + 72
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Analyte", species_label(analyte), "analyte_prev", "analyte_next")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Titrant", species_label(titrant), "titrant_prev", "titrant_next")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Analyte M", f"{self.analyte_concentration:0.2f} M", "analyte_conc_down", "analyte_conc_up")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Titrant M", f"{self.titrant_concentration:0.2f} M", "titrant_conc_down", "titrant_conc_up")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Analyte Volume", f"{self.analyte_volume_ml:0.0f} mL", "volume_down", "volume_up")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Dose Step", f"{self.step_volume_ml:0.2f} mL", "step_down", "step_up")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Indicator", indicator["name"], "indicator_prev", "indicator_next")
        y += 52

        reading_rect = pygame.Rect(inner.x, y, inner.width, 180)
        draw_card(content_surface, reading_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Reading", True, (244, 247, 252)), (reading_rect.x + 12, reading_rect.y + 10))
        lines = [
            f"Analyte: {analyte_compound['formula']}  |  {analyte_compound['strength'] or 'modelled'}",
            f"Titrant: {titrant_compound['formula']}  |  {titrant_compound['strength'] or 'modelled'}",
            f"pH: {self.state['pH']:5.2f}    pOH: {14.0 - self.state['pH']:5.2f}",
            f"Eq. volume: {self.state['equivalence_ml']:5.2f} mL",
            f"Current slope: {self.state['slope']:5.2f} pH/mL",
            f"Indicator fit: {indicator_fit}",
        ]
        line_y = reading_rect.y + 38
        for line in lines:
            content_surface.blit(self.caption_font.render(line, True, (206, 216, 232)), (reading_rect.x + 12, line_y))
            line_y += 22

        explanation_rect = pygame.Rect(inner.x, reading_rect.bottom + 14, inner.width, 240)
        draw_card(content_surface, explanation_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Why This Curve Looks Like It Does", True, (244, 247, 252)), (explanation_rect.x + 12, explanation_rect.y + 10))
        explanation = (
            f"{analyte_compound['reading']} "
            f"{titrant_compound['reading']} "
            f"{self.state['observation']} "
            "Use the mouse wheel for fast dosing, or switch to auto drip when you want to watch the curve cross the endpoint continuously."
        )
        draw_text_block(
            content_surface,
            self.body_font,
            explanation,
            (220, 227, 238),
            pygame.Rect(explanation_rect.x + 12, explanation_rect.y + 40, explanation_rect.width - 24, explanation_rect.height - 52),
        )

        footer_rect = pygame.Rect(inner.x, explanation_rect.bottom + 14, inner.width, 110)
        draw_card(content_surface, footer_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Use Tips", True, (244, 247, 252)), (footer_rect.x + 12, footer_rect.y + 10))
        draw_text_block(
            content_surface,
            self.caption_font,
            "Scroll this panel with the mouse wheel when the text is longer than the visible space. The burette keeps dosing when the wheel is used outside this panel.",
            (206, 216, 232),
            pygame.Rect(footer_rect.x + 12, footer_rect.y + 36, footer_rect.width - 24, footer_rect.height - 46),
            line_gap=2,
        )

        self.side_content_height = footer_rect.bottom + 12
        self.side_scroll = blit_scroll_surface(surface, content_surface, viewport, self.side_scroll)
        del self._side_interaction_origin

    def render(self, surface):
        draw_gradient(surface, self.play_rect, (22, 30, 46), (8, 12, 22))
        self.draw_apparatus(surface)
        self.draw_curve(surface)
        self.draw_side_panel(surface)
