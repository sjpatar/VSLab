import math

import pygame

from vsl.core.base_env import BaseEnvironment
from vsl.ui.toolbar import Toolbar
from vsl.environments.chemistry.common import blit_scroll_surface, clamp, clamp_scroll, draw_card, draw_gradient, draw_grid, draw_text_block, fit_text
from vsl.environments.chemistry.chemistry_models import hill_formula


ROOT_NAMES = {
    1: "meth",
    2: "eth",
    3: "prop",
    4: "but",
    5: "pent",
    6: "hex",
    7: "hept",
    8: "oct",
    9: "non",
    10: "dec",
    11: "undec",
    12: "dodec",
}

ATTACHMENT_LIBRARY = [
    {"key": "OH", "label": "OH", "counts": {"O": 1, "H": 1}, "bond_order": 1, "color": (98, 214, 180), "reading": "A hydroxy group adds oxygen and raises polarity."},
    {"key": "=O", "label": "O", "counts": {"O": 1}, "bond_order": 2, "color": (248, 146, 146), "reading": "A double-bonded oxygen creates a carbonyl-like feature."},
    {"key": "NH2", "label": "NH2", "counts": {"N": 1, "H": 2}, "bond_order": 1, "color": (126, 188, 255), "reading": "An amino group introduces nitrogen and raises basic character."},
    {"key": "Cl", "label": "Cl", "counts": {"Cl": 1}, "bond_order": 1, "color": (188, 234, 142), "reading": "A halogen substituent replaces a hydrogen on the carbon skeleton."},
    {"key": "Br", "label": "Br", "counts": {"Br": 1}, "bond_order": 1, "color": (202, 176, 96), "reading": "Bromine is a heavier halogen substituent."},
    {"key": "F", "label": "F", "counts": {"F": 1}, "bond_order": 1, "color": (188, 234, 142), "reading": "Fluorine is a strongly electron-withdrawing substituent."},
    {"key": "I", "label": "I", "counts": {"I": 1}, "bond_order": 1, "color": (194, 170, 246), "reading": "Iodine gives a bulky halogen substituent."},
]


class CarbonLabEnvironment(BaseEnvironment):
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

        self.carbons = []
        self.carbon_count = 4
        self.shape_mode = "chain"
        self.bond_mode = "single"
        self.selected_carbon = 0
        self.selected_group_index = 0
        self.status_message = "Click a carbon to edit it. The hydrogens and functional groups update the formula live."
        self.side_hitboxes = []
        self.carbon_hitboxes = []
        self.side_scroll = 0
        self.side_content_height = 0

        self.update_layout(*self.app.screen.get_size())
        self.rebuild_carbons(reset=True)

    def build_tool_defs(self):
        return [
            ("C -", "carbon_down", (122, 166, 224), "Remove one carbon from the skeleton"),
            ("C +", "carbon_up", (92, 214, 162), "Add one carbon to the skeleton"),
            ("Shape", "cycle_shape", (246, 184, 92), "Cycle chain, ring, and branched skeletons"),
            ("Bond", "cycle_bond", (188, 170, 246), "Cycle single, double, triple, and aromatic bonding"),
            ("Auto H", "auto_h", (104, 170, 246), "Refill hydrogens to the maximum valid valence"),
            ("Reset", "reset_model", (236, 116, 116), "Reset the whole carbon builder"),
            ("Menu", "exit_to_menu", (70, 78, 92), "Return to Chemistry Labs"),
        ]

    def current_group(self):
        return ATTACHMENT_LIBRARY[self.selected_group_index]

    def update_layout(self, w, h):
        toolbar_height = 60
        panel_width = min(380, max(320, int(w * 0.31)))
        self.play_rect = pygame.Rect(0, 0, max(w - panel_width, 1), max(h - toolbar_height, 1))
        self.side_panel_rect = pygame.Rect(self.play_rect.right, 0, panel_width, max(h - toolbar_height, 1))
        self.toolbar.update_layout(x=0, y=h - toolbar_height, width=w, height=toolbar_height)

    def rebuild_carbons(self, *, reset=False):
        previous = self.carbons if self.carbons and not reset else []
        new_carbons = []
        for index in range(self.carbon_count):
            if index < len(previous):
                new_carbons.append(
                    {
                        "hydrogens": previous[index]["hydrogens"],
                        "attachments": list(previous[index]["attachments"]),
                    }
                )
            else:
                new_carbons.append({"hydrogens": 0, "attachments": []})
        self.carbons = new_carbons
        self.selected_carbon = int(clamp(self.selected_carbon, 0, max(self.carbon_count - 1, 0)))
        self.normalize_structure()
        self.auto_fill_hydrogens()

    def topology(self):
        edges = []
        if self.shape_mode == "ring":
            for index in range(self.carbon_count):
                next_index = (index + 1) % self.carbon_count
                order = 1
                if self.bond_mode == "double" and index == 0:
                    order = 2
                elif self.bond_mode == "triple" and index == 0:
                    order = 3
                elif self.bond_mode == "aromatic":
                    order = 2 if index % 2 == 0 else 1
                edges.append((index, next_index, order))
            return edges

        if self.shape_mode == "branched" and self.carbon_count >= 4:
            main_chain = self.carbon_count - 1
            for index in range(main_chain - 1):
                order = 1
                if self.bond_mode == "double" and index == 0:
                    order = 2
                elif self.bond_mode == "triple" and index == 0:
                    order = 3
                edges.append((index, index + 1, order))
            branch_anchor = max(1, main_chain // 2)
            edges.append((branch_anchor, self.carbon_count - 1, 1))
            return edges

        for index in range(self.carbon_count - 1):
            order = 1
            if self.bond_mode == "double" and index == 0:
                order = 2
            elif self.bond_mode == "triple" and index == 0:
                order = 3
            edges.append((index, index + 1, order))
        return edges

    def bond_order_sum(self, index):
        total = 0
        for start, end, order in self.topology():
            if start == index or end == index:
                total += order
        return total

    def attachment_load(self, index):
        total = 0
        for group_key in self.carbons[index]["attachments"]:
            group = next(item for item in ATTACHMENT_LIBRARY if item["key"] == group_key)
            total += group["bond_order"]
        return total

    def raw_hydrogen_capacity(self, index):
        return 4 - self.bond_order_sum(index) - self.attachment_load(index)

    def max_hydrogens(self, index):
        return max(0, self.raw_hydrogen_capacity(index))

    def normalize_structure(self):
        if self.shape_mode == "ring" and self.carbon_count < 3:
            self.shape_mode = "chain"
        if self.shape_mode == "branched" and self.carbon_count < 4:
            self.shape_mode = "chain"
        if self.bond_mode == "aromatic" and (self.shape_mode != "ring" or self.carbon_count != 6):
            self.bond_mode = "single"

        for index, carbon in enumerate(self.carbons):
            while carbon["attachments"] and self.raw_hydrogen_capacity(index) < 0:
                carbon["attachments"].pop()
            carbon["hydrogens"] = int(clamp(carbon["hydrogens"], 0, self.max_hydrogens(index)))

    def auto_fill_hydrogens(self):
        self.normalize_structure()
        for index, carbon in enumerate(self.carbons):
            carbon["hydrogens"] = self.max_hydrogens(index)

    def handle_ui(self, action):
        if action == "carbon_down":
            self.carbon_count = int(clamp(self.carbon_count - 1, 1, 12))
            self.rebuild_carbons()
        elif action == "carbon_up":
            self.carbon_count = int(clamp(self.carbon_count + 1, 1, 12))
            self.rebuild_carbons()
        elif action == "cycle_shape":
            shapes = ["chain", "ring", "branched"]
            self.shape_mode = shapes[(shapes.index(self.shape_mode) + 1) % len(shapes)]
            self.normalize_structure()
            self.auto_fill_hydrogens()
        elif action == "cycle_bond":
            bonds = ["single", "double", "triple", "aromatic"]
            self.bond_mode = bonds[(bonds.index(self.bond_mode) + 1) % len(bonds)]
            self.normalize_structure()
            self.auto_fill_hydrogens()
        elif action == "auto_h":
            self.auto_fill_hydrogens()
            self.status_message = "Hydrogens were rebalanced to match the current carbon valence."
        elif action == "reset_model":
            self.carbon_count = 4
            self.shape_mode = "chain"
            self.bond_mode = "single"
            self.selected_carbon = 0
            self.selected_group_index = 0
            self.rebuild_carbons(reset=True)
        elif action == "exit_to_menu":
            self.app.switch_environment("ChemistryMenu")
        elif action == "select_prev_carbon":
            self.selected_carbon = (self.selected_carbon - 1) % self.carbon_count
        elif action == "select_next_carbon":
            self.selected_carbon = (self.selected_carbon + 1) % self.carbon_count
        elif action == "hydrogen_down":
            carbon = self.carbons[self.selected_carbon]
            carbon["hydrogens"] = max(0, carbon["hydrogens"] - 1)
        elif action == "hydrogen_up":
            carbon = self.carbons[self.selected_carbon]
            carbon["hydrogens"] = min(self.max_hydrogens(self.selected_carbon), carbon["hydrogens"] + 1)
        elif action == "group_prev":
            self.selected_group_index = (self.selected_group_index - 1) % len(ATTACHMENT_LIBRARY)
        elif action == "group_next":
            self.selected_group_index = (self.selected_group_index + 1) % len(ATTACHMENT_LIBRARY)
        elif action == "add_group":
            self.add_group_to_selected()
        elif action == "remove_group":
            self.remove_group_from_selected()

    def add_group_to_selected(self):
        carbon = self.carbons[self.selected_carbon]
        group = self.current_group()
        available = self.max_hydrogens(self.selected_carbon)
        if available < group["bond_order"]:
            needed = group["bond_order"] - available
            if carbon["hydrogens"] >= needed:
                carbon["hydrogens"] -= needed
            else:
                self.status_message = "That carbon has no free valence left for the selected group."
                return
        carbon["attachments"].append(group["key"])
        carbon["hydrogens"] = int(clamp(carbon["hydrogens"], 0, self.max_hydrogens(self.selected_carbon)))
        self.status_message = f"{group['label']} attached to carbon {self.selected_carbon + 1}."

    def remove_group_from_selected(self):
        carbon = self.carbons[self.selected_carbon]
        if carbon["attachments"]:
            removed = carbon["attachments"].pop()
            self.status_message = f"{removed} removed from carbon {self.selected_carbon + 1}."
            carbon["hydrogens"] = min(carbon["hydrogens"], self.max_hydrogens(self.selected_carbon))
        else:
            self.status_message = "The selected carbon has no attached group to remove."

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
            for index, rect in self.carbon_hitboxes:
                if rect.collidepoint(event.pos):
                    self.selected_carbon = index
                    self.status_message = f"Carbon {index + 1} selected."
                    return

        if event.type == pygame.MOUSEWHEEL:
            if self.side_panel_rect.collidepoint(pygame.mouse.get_pos()):
                viewport_height = max(self.side_panel_rect.height - 28, 1)
                self.side_scroll = clamp_scroll(self.side_scroll - event.y * 32, viewport_height, self.side_content_height)
            else:
                if event.y > 0:
                    self.handle_ui("hydrogen_up")
                elif event.y < 0:
                    self.handle_ui("hydrogen_down")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.handle_ui("select_prev_carbon")
            elif event.key == pygame.K_RIGHT:
                self.handle_ui("select_next_carbon")
            elif event.key == pygame.K_UP:
                self.handle_ui("hydrogen_up")
            elif event.key == pygame.K_DOWN:
                self.handle_ui("hydrogen_down")
            elif event.key == pygame.K_a:
                self.handle_ui("add_group")
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                self.handle_ui("remove_group")
            elif event.key == pygame.K_r:
                self.handle_ui("reset_model")

    def update(self):
        pass

    def formula_counts(self):
        counts = {"C": self.carbon_count}
        total_h = sum(carbon["hydrogens"] for carbon in self.carbons)
        if total_h:
            counts["H"] = total_h

        for carbon in self.carbons:
            for group_key in carbon["attachments"]:
                group = next(item for item in ATTACHMENT_LIBRARY if item["key"] == group_key)
                for symbol, amount in group["counts"].items():
                    counts[symbol] = counts.get(symbol, 0) + amount
        return counts

    def attachment_summary(self):
        summary = {}
        for carbon in self.carbons:
            for group_key in carbon["attachments"]:
                summary[group_key] = summary.get(group_key, 0) + 1
        return summary

    def dbe(self):
        counts = self.formula_counts()
        carbons = counts.get("C", 0)
        hydrogens = counts.get("H", 0)
        nitrogens = counts.get("N", 0)
        halogens = counts.get("F", 0) + counts.get("Cl", 0) + counts.get("Br", 0) + counts.get("I", 0)
        return max(0.0, carbons - (hydrogens + halogens) / 2.0 + nitrogens / 2.0 + 1.0)

    def open_valence(self):
        return sum(max(0, self.max_hydrogens(index) - carbon["hydrogens"]) for index, carbon in enumerate(self.carbons))

    def common_name(self):
        counts = self.formula_counts()
        formula = hill_formula(counts)
        if self.shape_mode == "ring" and self.bond_mode == "aromatic" and formula == "C6H6":
            return "Benzene"
        if self.shape_mode == "ring" and self.bond_mode == "aromatic" and formula == "C6H6O" and self.attachment_summary().get("OH") == 1:
            return "Phenol"
        if self.shape_mode == "chain" and self.bond_mode == "single" and formula == "CH4":
            return "Methane"
        if self.shape_mode == "chain" and self.bond_mode == "single" and formula == "C2H6":
            return "Ethane"
        if self.shape_mode == "chain" and self.bond_mode == "double" and formula == "C2H4":
            return "Ethene"
        if self.shape_mode == "chain" and self.bond_mode == "triple" and formula == "C2H2":
            return "Ethyne"
        if self.shape_mode == "chain" and self.attachment_summary().get("OH") == 1 and formula == "C2H6O":
            return "Ethanol"
        if self.shape_mode == "chain" and self.attachment_summary().get("=O") == 1 and formula == "C2H4O":
            return "Ethanal"
        if self.shape_mode == "chain" and self.attachment_summary().get("OH") == 1:
            return f"{ROOT_NAMES.get(self.carbon_count, 'carbon')}anol-like molecule"
        if self.shape_mode == "chain" and self.bond_mode == "single":
            return f"{ROOT_NAMES.get(self.carbon_count, 'carbon')}ane-like skeleton"
        if self.shape_mode == "chain" and self.bond_mode == "double":
            return f"{ROOT_NAMES.get(self.carbon_count, 'carbon')}ene-like skeleton"
        if self.shape_mode == "chain" and self.bond_mode == "triple":
            return f"{ROOT_NAMES.get(self.carbon_count, 'carbon')}yne-like skeleton"
        if self.shape_mode == "ring":
            return "Cyclic carbon framework"
        return "Branched carbon framework"

    def reading_text(self):
        summary = self.attachment_summary()
        attachment_text = ", ".join(f"{key} x{count}" for key, count in summary.items()) if summary else "no added functional groups"
        aromatic_note = "The ring uses alternating double bonds in an aromatic sketch." if self.bond_mode == "aromatic" else ""
        radical_note = (
            f"There are {self.open_valence()} open valence position(s), so the current sketch represents an unsaturated or radical-style structure rather than a fully hydrogen-filled stable neutral molecule. "
            if self.open_valence() > 0
            else "All carbon valences are currently satisfied by bonds, hydrogens, or attached groups. "
        )
        return (
            f"This editable model lets you decide the carbon count, the carbon-carbon bonding style, and the hydrogens on each carbon. "
            f"Attached groups right now: {attachment_text}. "
            f"Degrees of unsaturation: {self.dbe():0.1f}. "
            f"{radical_note}"
            f"{aromatic_note} "
            "Use this as a structure-aware playground: the formula updates from the chosen skeleton and substituents rather than from a fixed family preset."
        )

    def carbon_points(self):
        canvas = self.play_rect.inflate(-44, -54)
        draw_area = pygame.Rect(canvas.x + 18, canvas.y + 96, canvas.width - 36, canvas.height - 158)

        if self.shape_mode == "ring":
            radius = min(draw_area.width, draw_area.height) * 0.28
            points = []
            for index in range(self.carbon_count):
                angle = -math.pi / 2 + (2 * math.pi * index / self.carbon_count)
                points.append((draw_area.centerx + math.cos(angle) * radius, draw_area.centery + math.sin(angle) * radius))
            return points

        if self.shape_mode == "branched" and self.carbon_count >= 4:
            main_chain = self.carbon_count - 1
            span = min(draw_area.width * 0.66, 110 + (main_chain - 1) * 84)
            step = span / max(main_chain - 1, 1)
            start_x = draw_area.centerx - span / 2
            base_y = draw_area.centery + 24
            points = []
            for index in range(main_chain):
                y = base_y - 46 if index % 2 else base_y + 46
                points.append((start_x + index * step, y))
            branch_anchor = max(1, main_chain // 2)
            points.append((points[branch_anchor][0], points[branch_anchor][1] - 122))
            return points

        span = min(draw_area.width * 0.74, 110 + (self.carbon_count - 1) * 84)
        step = span / max(self.carbon_count - 1, 1)
        start_x = draw_area.centerx - span / 2
        points = []
        for index in range(self.carbon_count):
            y = draw_area.centery - 44 if index % 2 else draw_area.centery + 44
            if self.carbon_count == 1:
                y = draw_area.centery
            points.append((start_x + index * step, y))
        return points

    def draw_bond(self, surface, start, end, order):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = max(math.hypot(dx, dy), 1.0)
        nx = -dy / length
        ny = dx / length
        offsets = {1: [0], 2: [-5, 5], 3: [-8, 0, 8]}[order]
        for offset in offsets:
            shifted_start = (start[0] + nx * offset, start[1] + ny * offset)
            shifted_end = (end[0] + nx * offset, end[1] + ny * offset)
            pygame.draw.line(surface, (228, 234, 242), shifted_start, shifted_end, 4 if order == 1 else 3)

    def draw_structure(self, surface):
        draw_card(surface, self.play_rect.inflate(-18, -18), (10, 18, 32), (72, 90, 120))
        draw_grid(surface, self.play_rect.inflate(-18, -18), 48, (24, 34, 56))
        points = self.carbon_points()
        center = pygame.Rect(self.play_rect.inflate(-60, -90)).center

        self.carbon_hitboxes = []

        for start, end, order in self.topology():
            self.draw_bond(surface, points[start], points[end], order)

        if self.shape_mode == "ring" and self.bond_mode == "aromatic":
            radius = min(self.play_rect.width, self.play_rect.height) * 0.12
            pygame.draw.circle(surface, (228, 234, 242), center, int(radius), 2)

        for index, point in enumerate(points):
            rect = pygame.Rect(point[0] - 22, point[1] - 22, 44, 44)
            self.carbon_hitboxes.append((index, rect))
            fill = (36, 48, 70) if index != self.selected_carbon else (56, 82, 128)
            outline = (114, 156, 224) if index != self.selected_carbon else (138, 226, 255)
            pygame.draw.circle(surface, fill, point, 22)
            pygame.draw.circle(surface, outline, point, 22, 2)
            label = self.hud_font.render("C", True, (244, 247, 252))
            surface.blit(label, label.get_rect(center=point))
            index_label = self.caption_font.render(str(index + 1), True, (184, 196, 214))
            surface.blit(index_label, (point[0] + 16, point[1] - 24))

            hydrogen_count = self.carbons[index]["hydrogens"]
            if hydrogen_count > 0:
                h_rect = pygame.Rect(point[0] - 18, point[1] + 26, 36, 18)
                pygame.draw.rect(surface, (18, 28, 44), h_rect, border_radius=8)
                pygame.draw.rect(surface, (86, 102, 132), h_rect, 1, border_radius=8)
                draw_text = self.caption_font.render(f"H{hydrogen_count}", True, (214, 226, 240))
                surface.blit(draw_text, draw_text.get_rect(center=h_rect.center))

            attachments = self.carbons[index]["attachments"]
            if attachments:
                base_angle = math.atan2(point[1] - center[1], point[0] - center[0])
                if point == center:
                    base_angle = -math.pi / 2
                for attach_index, group_key in enumerate(attachments):
                    group = next(item for item in ATTACHMENT_LIBRARY if item["key"] == group_key)
                    slot_angle = base_angle + (-0.7 + attach_index * 0.7)
                    anchor = (point[0] + math.cos(slot_angle) * 58, point[1] + math.sin(slot_angle) * 58)
                    self.draw_bond(surface, point, anchor, 1 if group["bond_order"] == 1 else 2)
                    pygame.draw.circle(surface, (30, 40, 58), anchor, 20)
                    pygame.draw.circle(surface, group["color"], anchor, 20, 2)
                    text = self.caption_font.render(group["label"], True, (244, 247, 252))
                    surface.blit(text, text.get_rect(center=anchor))

        title_width = min(max(self.play_rect.width - 180, 320), 560)
        title_rect = pygame.Rect(self.play_rect.x + 28, self.play_rect.y + 28, title_width, 72)
        draw_card(surface, title_rect, (14, 22, 36), (78, 96, 126), alpha=232)
        surface.blit(self.hud_font.render("Carbon Compound Builder", True, (244, 247, 252)), (title_rect.x + 14, title_rect.y + 10))
        name_text = fit_text(self.hud_font, self.common_name(), title_rect.width - 28)
        surface.blit(self.hud_font.render(name_text, True, (134, 224, 178)), (title_rect.x + 14, title_rect.y + 34))
        draw_text_block(
            surface,
            self.caption_font,
            self.status_message,
            (206, 216, 232),
            pygame.Rect(title_rect.x + 14, title_rect.y + 52, title_rect.width - 28, 12),
            line_gap=1,
        )

        formula_rect = pygame.Rect(self.play_rect.right - 168, self.play_rect.y + 28, 140, 48)
        draw_card(surface, formula_rect, (14, 22, 36), (78, 96, 126), alpha=232, radius=12)
        formula_text = self.mono_font.render(hill_formula(self.formula_counts()), True, (206, 216, 232))
        surface.blit(formula_text, formula_text.get_rect(center=formula_rect.center))

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

    def draw_action_button(self, surface, rect, label, action, color):
        if hasattr(self, "_side_interaction_origin"):
            ox, oy = self._side_interaction_origin
            self.side_hitboxes.append({"rect": rect.move(ox, oy), "action": action})
        else:
            self.side_hitboxes.append({"rect": rect, "action": action})
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (64, 76, 94), rect, 1, border_radius=8)
        text = self.caption_font.render(label, True, (18, 22, 28) if sum(color) > 420 else (244, 247, 252))
        surface.blit(text, text.get_rect(center=rect.center))

    def draw_side_panel(self, surface):
        draw_gradient(surface, self.side_panel_rect, (16, 22, 36), (8, 11, 20))
        draw_card(surface, self.side_panel_rect.inflate(-14, -14), (12, 18, 30), (60, 74, 98), alpha=228)

        viewport = self.side_panel_rect.inflate(-20, -20)
        content_surface = pygame.Surface((viewport.width, 980), pygame.SRCALPHA)
        inner = content_surface.get_rect()
        self.side_hitboxes = []
        self._side_interaction_origin = (viewport.x, viewport.y - self.side_scroll)

        selected = self.carbons[self.selected_carbon]
        current_group = self.current_group()
        summary = self.attachment_summary()

        content_surface.blit(self.title_font.render("Structure Reading", True, (244, 247, 252)), (inner.x, inner.y))
        content_surface.blit(self.caption_font.render("Hydrogens and attached groups update the formula from the actual drawn structure.", True, (188, 202, 222)), (inner.x, inner.y + 34))

        y = inner.y + 72
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Selected Carbon", f"C{self.selected_carbon + 1}", "select_prev_carbon", "select_next_carbon")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Hydrogens On Selected Carbon", f"H{selected['hydrogens']}", "hydrogen_down", "hydrogen_up")
        y += 46
        self.draw_stepper(content_surface, pygame.Rect(inner.x, y, inner.width, 24), "Current Group", current_group["label"], "group_prev", "group_next")
        y += 48

        button_row_y = y
        self.draw_action_button(content_surface, pygame.Rect(inner.x, button_row_y, (inner.width - 10) // 2, 30), "Add Group", "add_group", (98, 214, 180))
        self.draw_action_button(content_surface, pygame.Rect(inner.x + (inner.width + 10) // 2, button_row_y, (inner.width - 10) // 2, 30), "Remove Group", "remove_group", (236, 116, 116))
        y += 50

        info_rect = pygame.Rect(inner.x, y, inner.width, 176)
        draw_card(content_surface, info_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Molecule Stats", True, (244, 247, 252)), (info_rect.x + 12, info_rect.y + 10))
        lines = [
            f"Formula: {hill_formula(self.formula_counts())}",
            f"Name: {self.common_name()}",
            f"Shape: {self.shape_mode}",
            f"Bond mode: {self.bond_mode}",
            f"DBE: {self.dbe():0.1f}",
            f"Open valence: {self.open_valence()}",
            f"Groups: {', '.join(f'{key} x{count}' for key, count in summary.items()) if summary else 'none'}",
        ]
        line_y = info_rect.y + 38
        for line in lines:
            content_surface.blit(self.caption_font.render(line, True, (206, 216, 232)), (info_rect.x + 12, line_y))
            line_y += 22

        reading_rect = pygame.Rect(inner.x, info_rect.bottom + 14, inner.width, 290)
        draw_card(content_surface, reading_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Why This Structure Matters", True, (244, 247, 252)), (reading_rect.x + 12, reading_rect.y + 10))
        draw_text_block(
            content_surface,
            self.body_font,
            self.reading_text() + " " + current_group["reading"],
            (220, 227, 238),
            pygame.Rect(reading_rect.x + 12, reading_rect.y + 40, reading_rect.width - 24, reading_rect.height - 52),
        )

        guide_rect = pygame.Rect(inner.x, reading_rect.bottom + 14, inner.width, 126)
        draw_card(content_surface, guide_rect, (14, 20, 34), (76, 90, 118), alpha=228, radius=14)
        content_surface.blit(self.hud_font.render("Use Tips", True, (244, 247, 252)), (guide_rect.x + 12, guide_rect.y + 10))
        draw_text_block(
            content_surface,
            self.caption_font,
            "Use left and right arrow keys to move between carbons, the mouse wheel to tune hydrogens, and this panel's own scroll when the reading extends below the window.",
            (206, 216, 232),
            pygame.Rect(guide_rect.x + 12, guide_rect.y + 38, guide_rect.width - 24, guide_rect.height - 48),
            line_gap=2,
        )

        self.side_content_height = guide_rect.bottom + 12
        self.side_scroll = blit_scroll_surface(surface, content_surface, viewport, self.side_scroll)
        del self._side_interaction_origin

    def render(self, surface):
        draw_gradient(surface, self.play_rect, (22, 30, 46), (8, 12, 22))
        self.draw_structure(surface)
        self.draw_side_panel(surface)
