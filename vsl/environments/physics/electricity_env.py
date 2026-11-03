import pygame
from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.core.circuit_solver import CircuitSolver
from vsl.components.electrical.battery import Battery
from vsl.components.electrical.switch import Switch
from vsl.components.electrical.resistor import Resistor
from vsl.components.electrical.bulb import Bulb
from vsl.components.electrical.meter import Ammeter, Voltmeter
from vsl.components.electrical.wire import Wire


class ElectricityEnvironment(BaseEnvironment):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.background_color = (40, 45, 50)

        electricity_tools = [
            ("Battery", "spawn_battery", (255, 215, 0), "Add Battery"),
            ("Switch", "spawn_switch", (120, 120, 120), "Add Toggle Switch"),
            ("Resistor", "spawn_resistor", (210, 180, 140), "Add Resistor"),
            ("Bulb", "spawn_bulb", (240, 240, 100), "Add Light Bulb"),
            ("Ammeter", "spawn_ammeter", (200, 200, 255), "Measure Current (A)"),
            ("Voltmeter", "spawn_voltmeter", (200, 200, 255), "Measure Voltage (V)"),
            ("Wire", "toggle_wire", (0, 255, 255), "Toggle Wiring Mode"),
            ("Clear", "clear_scene", (255, 100, 100), "Delete All Objects"),
            ("Menu", "exit_to_menu", (50, 50, 50), "Back to Physics Menu"),
        ]

        screen_w, screen_h = self.app.screen.get_size()
        self.toolbar = Toolbar(0, screen_h - 60, screen_w, 60, electricity_tools)
        self.toolbar.set_active_tool(None)

        self.title_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.hud_font = pygame.font.SysFont("Arial", 15, bold=True)
        self.caption_font = pygame.font.SysFont("Arial", 14)
        self.mono_font = pygame.font.SysFont("Consolas", 14, bold=True)

        self.btn_val_down_rect = None
        self.btn_val_up_rect = None

        self.wires = []
        self.active_wire_start = None
        self.wire_mode = False
        self.solver_metrics = dict(CircuitSolver.latest_metrics)

    def selected_object(self):
        return next((obj for obj in reversed(self.objects) if getattr(obj, "selected", False)), None)

    def clear_selection(self):
        for obj in self.objects:
            obj.selected = False

    def wire_under_point(self, point):
        return next((wire for wire in reversed(self.wires) if wire.contains_point(point)), None)

    def update_layout(self, w, h):
        self.toolbar.update_layout(x=0, y=h - 60, width=w, height=60)

    def get_adjustable_property(self, obj):
        if isinstance(obj, Battery):
            return "voltage", getattr(obj, "voltage", 9.0), 1.5, 240.0, 1.5, "V"
        if isinstance(obj, Resistor):
            return "resistance", getattr(obj, "resistance", 100.0), 1.0, 10000.0, 10.0, "Ohm"
        if isinstance(obj, Bulb):
            return "resistance", getattr(obj, "resistance", 50.0), 1.0, 5000.0, 5.0, "Ohm"
        return None, None, None, None, None, None

    def update_object_property(self, obj, delta_steps):
        prop, val, min_val, max_val, step, unit = self.get_adjustable_property(obj)
        if prop:
            new_val = val + (delta_steps * step)
            new_val = max(min_val, min(new_val, max_val))
            setattr(obj, prop, new_val)

    def selected_reading_lines(self, obj):
        if isinstance(obj, Ammeter):
            current = getattr(obj, "value", getattr(obj, "current", 0.0))
            voltage = getattr(obj, "v_drop", 0.0)
            return [
                f"Reading: {current:6.2f} A",
                f"Drop:    {voltage:6.3f} V",
                f"Power:   {voltage * current:6.3f} W",
            ]

        if isinstance(obj, Voltmeter):
            voltage = getattr(obj, "value", getattr(obj, "v_drop", 0.0))
            current = getattr(obj, "current", 0.0)
            return [
                f"Reading: {voltage:6.2f} V",
                f"Current: {current:6.4f} A",
                f"Power:   {voltage * current:6.4f} W",
            ]

        voltage = getattr(obj, "v_drop", getattr(obj, "voltage", 0.0))
        current = getattr(obj, "current", 0.0)
        power = voltage * current
        lines = [
            f"Voltage: {voltage:6.2f} V",
            f"Current: {current:6.2f} A",
            f"Power:   {power:6.2f} W",
        ]
        brightness = getattr(obj, "brightness", 0.0)
        if brightness > 0.0:
            lines.append(f"Lamp:    {brightness * 100:6.1f} %")
        return lines

    def update(self):
        for obj in self.objects:
            obj.update()
        CircuitSolver.solve(self.objects, self.wires)
        self.solver_metrics = dict(CircuitSolver.latest_metrics)

    def draw_background_grid(self, surface):
        width, height = surface.get_size()
        for x in range(0, width, 48):
            pygame.draw.line(surface, (50, 55, 62), (x, 0), (x, height), 1)
        for y in range(0, height, 48):
            pygame.draw.line(surface, (50, 55, 62), (0, y), (width, y), 1)

    def render_hud(self, surface):
        card = pygame.Rect(18, 18, 390, 138)
        overlay = pygame.Surface(card.size, pygame.SRCALPHA)
        pygame.draw.rect(overlay, (13, 18, 25, 220), overlay.get_rect(), border_radius=14)
        pygame.draw.rect(overlay, (70, 82, 98, 255), overlay.get_rect(), 1, border_radius=14)
        surface.blit(overlay, card.topleft)

        surface.blit(self.title_font.render("Electricity Lab", True, (242, 247, 252)), (card.x + 16, card.y + 12))

        mode_label = "Wiring Mode (Click terminals to add/remove)" if self.wire_mode else "Select & Drag Mode"
        surface.blit(self.hud_font.render(f"Mode: {mode_label}", True, (226, 232, 240)), (card.x + 16, card.y + 48))
        surface.blit(self.caption_font.render(
            f"Components: {len(self.objects)}    Wires: {len(self.wires)}    Nodes: {self.solver_metrics.get('node_count', 0)}",
            True,
            (176, 188, 204),
        ), (card.x + 16, card.y + 68))
        surface.blit(self.caption_font.render(
            "Tip: right-click a wire to remove only that connection.",
            True,
            (176, 188, 204),
        ), (card.x + 16, card.y + 108))

        total_current = self.solver_metrics.get("total_current", 0.0)
        total_power = self.solver_metrics.get("total_power", 0.0)
        eq_res = self.solver_metrics.get("equivalent_resistance")
        eq_text = f"{eq_res:6.2f} Ohm" if eq_res is not None else "--"
        surface.blit(self.caption_font.render(
            f"Supply I: {total_current:5.2f} A    Power: {total_power:6.2f} W    EqR: {eq_text}",
            True,
            (176, 188, 204),
        ), (card.x + 16, card.y + 88))

        self.btn_val_down_rect = None
        self.btn_val_up_rect = None

        selected = self.selected_object()
        if selected:
            prop, val, min_val, max_val, step, unit = self.get_adjustable_property(selected)
            height = 148 if prop else 110

            stats_rect = pygame.Rect(18, 150, 300, height)
            stats_surface = pygame.Surface(stats_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(stats_surface, (13, 18, 25, 210), stats_surface.get_rect(), border_radius=14)
            pygame.draw.rect(stats_surface, (70, 82, 98, 255), stats_surface.get_rect(), 1, border_radius=14)
            surface.blit(stats_surface, stats_rect.topleft)

            title_text = selected.__class__.__name__
            surface.blit(self.hud_font.render(title_text, True, (242, 247, 252)), (stats_rect.x + 14, stats_rect.y + 12))

            readings_y = stats_rect.y + 38

            if prop:
                self.btn_val_down_rect = pygame.Rect(stats_rect.x + 14, readings_y, 32, 26)
                self.btn_val_up_rect = pygame.Rect(stats_rect.x + 254, readings_y, 32, 26)

                pygame.draw.rect(surface, (230, 96, 96), self.btn_val_down_rect, border_radius=6)
                surface.blit(self.hud_font.render("-", True, (255, 255, 255)), (self.btn_val_down_rect.x + 12, self.btn_val_down_rect.y + 2))

                pygame.draw.rect(surface, (84, 214, 112), self.btn_val_up_rect, border_radius=6)
                surface.blit(self.hud_font.render("+", True, (255, 255, 255)), (self.btn_val_up_rect.x + 10, self.btn_val_up_rect.y + 2))

                val_text = f"{prop.capitalize()}: {val:>5.1f} {unit}"
                surface.blit(self.mono_font.render(val_text, True, (255, 230, 140)), (stats_rect.x + 60, readings_y + 4))
                readings_y += 38

            for index, line in enumerate(self.selected_reading_lines(selected)):
                surface.blit(self.mono_font.render(line, True, (184, 196, 214)), (stats_rect.x + 14, readings_y + index * 20))

    def render(self, surface: pygame.Surface):
        surface.fill(self.background_color)
        self.draw_background_grid(surface)

        for wire in self.wires:
            wire.render(surface)

        if self.active_wire_start:
            mouse_pos = pygame.mouse.get_pos()
            start_obj, start_offset = self.active_wire_start
            start_pos = (start_obj.rect.x + start_offset[0], start_obj.rect.y + start_offset[1])
            pygame.draw.line(surface, (100, 200, 255), start_pos, mouse_pos, 2)

        for obj in self.objects:
            obj.render(surface)

        self.render_hud(surface)

    def handle_event(self, event: pygame.event.Event):
        action = self.toolbar.handle_event(event)
        if action:
            self.handle_ui(action)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            target_wire = self.wire_under_point(event.pos)
            if target_wire:
                self.wires.remove(target_wire)
                self.active_wire_start = None
                return

        if event.type == pygame.MOUSEWHEEL:
            selected = self.selected_object()
            if selected:
                self.update_object_property(selected, event.y)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            selected = self.selected_object()

            if self.btn_val_down_rect and self.btn_val_down_rect.collidepoint(event.pos):
                if selected:
                    self.update_object_property(selected, -1)
                return

            if self.btn_val_up_rect and self.btn_val_up_rect.collidepoint(event.pos):
                if selected:
                    self.update_object_property(selected, 1)
                return

            self.clear_selection()

            if self.wire_mode:
                for obj in self.objects:
                    if hasattr(obj, "get_hit_terminal"):
                        term = obj.get_hit_terminal(event.pos)
                        if term:
                            if not self.active_wire_start:
                                self.active_wire_start = (obj, term)
                            else:
                                start_obj, start_term = self.active_wire_start
                                if not (start_obj is obj and start_term == term):
                                    existing_wire = next((
                                        wire
                                        for wire in self.wires
                                        if wire.matches_connection(start_obj, start_term, obj, term)
                                    ), None)
                                    if existing_wire:
                                        self.wires.remove(existing_wire)
                                    else:
                                        self.wires.append(Wire(
                                            start_obj=start_obj,
                                            end_obj=obj,
                                            start_offset=start_term,
                                            end_offset=term,
                                        ))
                                self.active_wire_start = None
                            return
                self.active_wire_start = None
                return

        for obj in reversed(self.objects):
            if obj.handle_event(event):
                break

    def handle_ui(self, action):
        cw, ch = self.app.screen.get_size()
        cx, cy = cw // 2, ch // 2

        if action == "spawn_battery":
            self.objects.append(Battery(cx, cy))
        elif action == "spawn_switch":
            self.objects.append(Switch(cx, cy))
        elif action == "spawn_resistor":
            self.objects.append(Resistor(cx, cy))
        elif action == "spawn_bulb":
            self.objects.append(Bulb(cx, cy))
        elif action == "spawn_ammeter":
            self.objects.append(Ammeter(cx, cy))
        elif action == "spawn_voltmeter":
            self.objects.append(Voltmeter(cx, cy))
        elif action == "toggle_wire":
            self.wire_mode = not self.wire_mode
            self.toolbar.set_active_tool("toggle_wire" if self.wire_mode else None)
            self.active_wire_start = None
        elif action == "clear_scene":
            self.objects.clear()
            self.wires.clear()
            self.active_wire_start = None
        elif action == "exit_to_menu":
            self.app.switch_environment("PhysicsMenu")
