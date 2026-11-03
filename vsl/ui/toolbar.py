# VSLab/vsl/ui/toolbar.py
from vsl.ui.button_panel import ButtonPanel


DEFAULT_TOOL_DEFS = [
    ("Battery", "spawn_battery", (255, 215, 0), "Add 9V Battery"),
    ("Switch", "spawn_switch", (120, 120, 120), "Add Toggle Switch"),
    ("Resistor", "spawn_resistor", (210, 180, 140), "Add 100 Ohm Resistor"),
    ("Bulb", "spawn_bulb", (240, 240, 100), "Add Light Bulb"),
    ("Ammeter", "spawn_ammeter", (200, 200, 255), "Measure Current (A)"),
    ("Voltmeter", "spawn_voltmeter", (200, 200, 255), "Measure Voltage (V)"),
    ("Wire", "toggle_wire", (0, 255, 255), "Toggle Wiring Mode"),
    ("Clear", "clear_scene", (255, 100, 100), "Delete All Objects"),
]


class Toolbar(ButtonPanel):
    def __init__(self, x, y, width, height, btn_defs=None):
        super().__init__(
            (x, y, width, height),
            btn_defs or DEFAULT_TOOL_DEFS,
            layout="horizontal",
            button_height=40,
            padding=12,
            gap=10,
            min_button_width=60,
            max_button_width=112,
            show_panel=True,
            show_tooltips=True,
            panel_color=(22, 27, 34),
            border_color=(60, 72, 84),
            outline_color=(90, 200, 255),
            font_size=13,
            border_radius=12,
        )

    def set_active_tool(self, tool):
        self.set_active_action(tool)
