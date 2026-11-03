import itertools
import math


CATEGORY_COLORS = {
    "alkali": (244, 144, 144),
    "alkaline": (252, 176, 112),
    "transition": (120, 188, 240),
    "post": (136, 212, 194),
    "metalloid": (166, 210, 134),
    "nonmetal": (244, 232, 140),
    "halogen": (188, 234, 142),
    "noble": (184, 168, 246),
}


PERIODIC_TABLE = [
    {"symbol": "H", "name": "Hydrogen", "row": 1, "col": 1, "category": "nonmetal"},
    {"symbol": "He", "name": "Helium", "row": 1, "col": 18, "category": "noble"},
    {"symbol": "Li", "name": "Lithium", "row": 2, "col": 1, "category": "alkali"},
    {"symbol": "Be", "name": "Beryllium", "row": 2, "col": 2, "category": "alkaline"},
    {"symbol": "B", "name": "Boron", "row": 2, "col": 13, "category": "metalloid"},
    {"symbol": "C", "name": "Carbon", "row": 2, "col": 14, "category": "nonmetal"},
    {"symbol": "N", "name": "Nitrogen", "row": 2, "col": 15, "category": "nonmetal"},
    {"symbol": "O", "name": "Oxygen", "row": 2, "col": 16, "category": "nonmetal"},
    {"symbol": "F", "name": "Fluorine", "row": 2, "col": 17, "category": "halogen"},
    {"symbol": "Ne", "name": "Neon", "row": 2, "col": 18, "category": "noble"},
    {"symbol": "Na", "name": "Sodium", "row": 3, "col": 1, "category": "alkali"},
    {"symbol": "Mg", "name": "Magnesium", "row": 3, "col": 2, "category": "alkaline"},
    {"symbol": "Al", "name": "Aluminium", "row": 3, "col": 13, "category": "post"},
    {"symbol": "Si", "name": "Silicon", "row": 3, "col": 14, "category": "metalloid"},
    {"symbol": "P", "name": "Phosphorus", "row": 3, "col": 15, "category": "nonmetal"},
    {"symbol": "S", "name": "Sulfur", "row": 3, "col": 16, "category": "nonmetal"},
    {"symbol": "Cl", "name": "Chlorine", "row": 3, "col": 17, "category": "halogen"},
    {"symbol": "Ar", "name": "Argon", "row": 3, "col": 18, "category": "noble"},
    {"symbol": "K", "name": "Potassium", "row": 4, "col": 1, "category": "alkali"},
    {"symbol": "Ca", "name": "Calcium", "row": 4, "col": 2, "category": "alkaline"},
    {"symbol": "Sc", "name": "Scandium", "row": 4, "col": 3, "category": "transition"},
    {"symbol": "Ti", "name": "Titanium", "row": 4, "col": 4, "category": "transition"},
    {"symbol": "V", "name": "Vanadium", "row": 4, "col": 5, "category": "transition"},
    {"symbol": "Cr", "name": "Chromium", "row": 4, "col": 6, "category": "transition"},
    {"symbol": "Mn", "name": "Manganese", "row": 4, "col": 7, "category": "transition"},
    {"symbol": "Fe", "name": "Iron", "row": 4, "col": 8, "category": "transition"},
    {"symbol": "Co", "name": "Cobalt", "row": 4, "col": 9, "category": "transition"},
    {"symbol": "Ni", "name": "Nickel", "row": 4, "col": 10, "category": "transition"},
    {"symbol": "Cu", "name": "Copper", "row": 4, "col": 11, "category": "transition"},
    {"symbol": "Zn", "name": "Zinc", "row": 4, "col": 12, "category": "transition"},
    {"symbol": "Ga", "name": "Gallium", "row": 4, "col": 13, "category": "post"},
    {"symbol": "Ge", "name": "Germanium", "row": 4, "col": 14, "category": "metalloid"},
    {"symbol": "As", "name": "Arsenic", "row": 4, "col": 15, "category": "metalloid"},
    {"symbol": "Se", "name": "Selenium", "row": 4, "col": 16, "category": "nonmetal"},
    {"symbol": "Br", "name": "Bromine", "row": 4, "col": 17, "category": "halogen"},
    {"symbol": "Kr", "name": "Krypton", "row": 4, "col": 18, "category": "noble"},
    {"symbol": "Rb", "name": "Rubidium", "row": 5, "col": 1, "category": "alkali"},
    {"symbol": "Sr", "name": "Strontium", "row": 5, "col": 2, "category": "alkaline"},
    {"symbol": "Y", "name": "Yttrium", "row": 5, "col": 3, "category": "transition"},
    {"symbol": "Zr", "name": "Zirconium", "row": 5, "col": 4, "category": "transition"},
    {"symbol": "Nb", "name": "Niobium", "row": 5, "col": 5, "category": "transition"},
    {"symbol": "Mo", "name": "Molybdenum", "row": 5, "col": 6, "category": "transition"},
    {"symbol": "Tc", "name": "Technetium", "row": 5, "col": 7, "category": "transition"},
    {"symbol": "Ru", "name": "Ruthenium", "row": 5, "col": 8, "category": "transition"},
    {"symbol": "Rh", "name": "Rhodium", "row": 5, "col": 9, "category": "transition"},
    {"symbol": "Pd", "name": "Palladium", "row": 5, "col": 10, "category": "transition"},
    {"symbol": "Ag", "name": "Silver", "row": 5, "col": 11, "category": "transition"},
    {"symbol": "Cd", "name": "Cadmium", "row": 5, "col": 12, "category": "transition"},
    {"symbol": "In", "name": "Indium", "row": 5, "col": 13, "category": "post"},
    {"symbol": "Sn", "name": "Tin", "row": 5, "col": 14, "category": "post"},
    {"symbol": "Sb", "name": "Antimony", "row": 5, "col": 15, "category": "metalloid"},
    {"symbol": "Te", "name": "Tellurium", "row": 5, "col": 16, "category": "metalloid"},
    {"symbol": "I", "name": "Iodine", "row": 5, "col": 17, "category": "halogen"},
    {"symbol": "Xe", "name": "Xenon", "row": 5, "col": 18, "category": "noble"},
    {"symbol": "Cs", "name": "Cesium", "row": 6, "col": 1, "category": "alkali"},
    {"symbol": "Ba", "name": "Barium", "row": 6, "col": 2, "category": "alkaline"},
    {"symbol": "Hf", "name": "Hafnium", "row": 6, "col": 4, "category": "transition"},
    {"symbol": "Ta", "name": "Tantalum", "row": 6, "col": 5, "category": "transition"},
    {"symbol": "W", "name": "Tungsten", "row": 6, "col": 6, "category": "transition"},
    {"symbol": "Re", "name": "Rhenium", "row": 6, "col": 7, "category": "transition"},
    {"symbol": "Os", "name": "Osmium", "row": 6, "col": 8, "category": "transition"},
    {"symbol": "Ir", "name": "Iridium", "row": 6, "col": 9, "category": "transition"},
    {"symbol": "Pt", "name": "Platinum", "row": 6, "col": 10, "category": "transition"},
    {"symbol": "Au", "name": "Gold", "row": 6, "col": 11, "category": "transition"},
    {"symbol": "Hg", "name": "Mercury", "row": 6, "col": 12, "category": "transition"},
    {"symbol": "Tl", "name": "Thallium", "row": 6, "col": 13, "category": "post"},
    {"symbol": "Pb", "name": "Lead", "row": 6, "col": 14, "category": "post"},
    {"symbol": "Bi", "name": "Bismuth", "row": 6, "col": 15, "category": "post"},
    {"symbol": "Po", "name": "Polonium", "row": 6, "col": 16, "category": "metalloid"},
    {"symbol": "At", "name": "Astatine", "row": 6, "col": 17, "category": "halogen"},
    {"symbol": "Rn", "name": "Radon", "row": 6, "col": 18, "category": "noble"},
]

ELEMENTS_BY_SYMBOL = {
    entry["symbol"]: {
        **entry,
        "color": CATEGORY_COLORS.get(entry["category"], (180, 190, 210)),
    }
    for entry in PERIODIC_TABLE
}

METAL_SYMBOLS = {
    symbol
    for symbol, entry in ELEMENTS_BY_SYMBOL.items()
    if entry["category"] in {"alkali", "alkaline", "transition", "post"}
}

ION_LIBRARY = {
    "H": {"formula": "H", "counts": {"H": 1}, "charge": 1, "name": "hydrogen", "polyatomic": False},
    "NH4": {"formula": "NH4", "counts": {"N": 1, "H": 4}, "charge": 1, "name": "ammonium", "polyatomic": True},
    "Na": {"formula": "Na", "counts": {"Na": 1}, "charge": 1, "name": "sodium", "polyatomic": False},
    "K": {"formula": "K", "counts": {"K": 1}, "charge": 1, "name": "potassium", "polyatomic": False},
    "Ag": {"formula": "Ag", "counts": {"Ag": 1}, "charge": 1, "name": "silver", "polyatomic": False},
    "Cu": {"formula": "Cu", "counts": {"Cu": 1}, "charge": 2, "name": "copper(II)", "polyatomic": False},
    "Fe": {"formula": "Fe", "counts": {"Fe": 1}, "charge": 2, "name": "iron(II)", "polyatomic": False},
    "Zn": {"formula": "Zn", "counts": {"Zn": 1}, "charge": 2, "name": "zinc", "polyatomic": False},
    "Mg": {"formula": "Mg", "counts": {"Mg": 1}, "charge": 2, "name": "magnesium", "polyatomic": False},
    "Ca": {"formula": "Ca", "counts": {"Ca": 1}, "charge": 2, "name": "calcium", "polyatomic": False},
    "Ba": {"formula": "Ba", "counts": {"Ba": 1}, "charge": 2, "name": "barium", "polyatomic": False},
    "Pb": {"formula": "Pb", "counts": {"Pb": 1}, "charge": 2, "name": "lead(II)", "polyatomic": False},
    "Cl": {"formula": "Cl", "counts": {"Cl": 1}, "charge": 1, "name": "chloride", "polyatomic": False},
    "Br": {"formula": "Br", "counts": {"Br": 1}, "charge": 1, "name": "bromide", "polyatomic": False},
    "I": {"formula": "I", "counts": {"I": 1}, "charge": 1, "name": "iodide", "polyatomic": False},
    "NO3": {"formula": "NO3", "counts": {"N": 1, "O": 3}, "charge": 1, "name": "nitrate", "polyatomic": True},
    "OH": {"formula": "OH", "counts": {"O": 1, "H": 1}, "charge": 1, "name": "hydroxide", "polyatomic": True},
    "CO3": {"formula": "CO3", "counts": {"C": 1, "O": 3}, "charge": 2, "name": "carbonate", "polyatomic": True},
    "HCO3": {"formula": "HCO3", "counts": {"H": 1, "C": 1, "O": 3}, "charge": 1, "name": "hydrogen carbonate", "polyatomic": True},
    "HCO2": {"formula": "HCO2", "counts": {"H": 1, "C": 1, "O": 2}, "charge": 1, "name": "formate", "polyatomic": True},
    "SO4": {"formula": "SO4", "counts": {"S": 1, "O": 4}, "charge": 2, "name": "sulfate", "polyatomic": True},
    "PO4": {"formula": "PO4", "counts": {"P": 1, "O": 4}, "charge": 3, "name": "phosphate", "polyatomic": True},
    "C2H3O2": {"formula": "C2H3O2", "counts": {"C": 2, "H": 3, "O": 2}, "charge": 1, "name": "acetate", "polyatomic": True},
}

ALKALI_CATIONS = {"Li", "Na", "K", "Rb", "Cs", "NH4"}
ACTIVITY_SERIES = ["K", "Ba", "Ca", "Na", "Mg", "Al", "Zn", "Fe", "Pb", "H", "Cu", "Ag", "Au"]
CATION_KEYS = ["H", "NH4", "Na", "K", "Ag", "Cu", "Fe", "Zn", "Mg", "Ca", "Ba", "Pb"]
ANION_KEYS = ["Cl", "Br", "I", "NO3", "OH", "CO3", "HCO3", "HCO2", "SO4", "PO4", "C2H3O2"]


def counts_key(counts):
    normalized = []
    for symbol, count in counts.items():
        if count:
            normalized.append((symbol, int(count)))
    normalized.sort()
    return tuple(normalized)


def normalize_counts(counts):
    return {symbol: int(count) for symbol, count in counts.items() if int(count) > 0}


def multiply_counts(counts, factor):
    return {symbol: count * factor for symbol, count in counts.items()}


def merge_counts(*groups):
    merged = {}
    for group in groups:
        for symbol, count in group.items():
            merged[symbol] = merged.get(symbol, 0) + count
    return normalize_counts(merged)


def hill_formula(counts):
    counts = normalize_counts(counts)
    if not counts:
        return "-"

    ordered = []
    if "C" in counts:
        ordered.append("C")
    if "H" in counts:
        ordered.append("H")
    ordered.extend(symbol for symbol in sorted(counts) if symbol not in ordered)
    return "".join(symbol if counts[symbol] == 1 else f"{symbol}{counts[symbol]}" for symbol in ordered)


def average_element_color(counts):
    counts = normalize_counts(counts)
    if not counts:
        return (190, 204, 222)

    weighted = [0.0, 0.0, 0.0]
    total = 0.0
    for symbol, count in counts.items():
        color = ELEMENTS_BY_SYMBOL.get(symbol, {}).get("color", (190, 204, 222))
        weighted[0] += color[0] * count
        weighted[1] += color[1] * count
        weighted[2] += color[2] * count
        total += count
    return tuple(int(channel / max(total, 1.0)) for channel in weighted)


def ion_fragment(ion_key, multiplier):
    ion = ION_LIBRARY[ion_key]
    if multiplier == 1:
        return ion["formula"]
    if ion["polyatomic"]:
        return f"({ion['formula']}){multiplier}"
    return f"{ion['formula']}{multiplier}"


def combine_ions(cation_key, anion_key):
    cation = ION_LIBRARY[cation_key]
    anion = ION_LIBRARY[anion_key]
    positive = cation["charge"]
    negative = anion["charge"]
    common = math.lcm(positive, negative)
    cation_multiplier = common // positive
    anion_multiplier = common // negative
    counts = merge_counts(
        multiply_counts(cation["counts"], cation_multiplier),
        multiply_counts(anion["counts"], anion_multiplier),
    )
    formula = f"{ion_fragment(cation_key, cation_multiplier)}{ion_fragment(anion_key, anion_multiplier)}"
    return counts, formula, cation_multiplier, anion_multiplier


def make_compound(
    *,
    name,
    counts,
    formula=None,
    kind="custom",
    state="aq",
    color=None,
    cation=None,
    anion=None,
    strength=None,
    pKa=None,
    pKb=None,
    role=None,
    reading="",
):
    counts = normalize_counts(counts)
    return {
        "name": name,
        "counts": counts,
        "key": counts_key(counts),
        "formula": formula or hill_formula(counts),
        "kind": kind,
        "state": state,
        "color": color or average_element_color(counts),
        "cation": cation,
        "anion": anion,
        "strength": strength,
        "pKa": pKa,
        "pKb": pKb,
        "role": role,
        "reading": reading,
    }


def ionic_compound(name, cation_key, anion_key, *, kind="salt", state="aq", color=None, strength=None, pKa=None, role=None, reading=""):
    counts, formula, _, _ = combine_ions(cation_key, anion_key)
    return make_compound(
        name=name,
        counts=counts,
        formula=formula,
        kind=kind,
        state=state,
        color=color,
        cation=cation_key,
        anion=anion_key,
        strength=strength,
        pKa=pKa,
        role=role,
        reading=reading,
    )


KNOWN_COMPOUNDS = []


def register_compound(compound):
    KNOWN_COMPOUNDS.append(compound)
    return compound


register_compound(
    ionic_compound(
        "Hydrochloric Acid",
        "H",
        "Cl",
        kind="acid",
        state="aq",
        color=(188, 220, 244),
        strength="strong",
        role="acid",
        reading="A strong acid that dissociates almost completely in water.",
    )
)
register_compound(
    ionic_compound(
        "Hydrobromic Acid",
        "H",
        "Br",
        kind="acid",
        state="aq",
        color=(204, 230, 250),
        strength="strong",
        role="acid",
        reading="A strong halogen acid with near-complete dissociation.",
    )
)
register_compound(
    ionic_compound(
        "Hydroiodic Acid",
        "H",
        "I",
        kind="acid",
        state="aq",
        color=(214, 222, 250),
        strength="strong",
        role="acid",
        reading="A strong acid and strong reducing agent in solution.",
    )
)
register_compound(
    ionic_compound(
        "Nitric Acid",
        "H",
        "NO3",
        kind="acid",
        state="aq",
        color=(202, 228, 244),
        strength="strong",
        role="acid",
        reading="A strong acid whose nitrate salts are generally soluble.",
    )
)
register_compound(
    ionic_compound(
        "Sulfuric Acid",
        "H",
        "SO4",
        kind="acid",
        state="aq",
        color=(206, 228, 240),
        strength="strong",
        role="acid",
        reading="A strong acid for the first proton and a source of sulfate ions.",
    )
)
register_compound(
    make_compound(
        name="Acetic Acid",
        counts={"C": 2, "H": 4, "O": 2},
        formula="CH3COOH",
        kind="acid",
        state="aq",
        color=(236, 214, 196),
        strength="weak",
        pKa=4.76,
        role="acid",
        anion="C2H3O2",
        reading="A weak acid that only partially ionizes, so buffer regions appear during titration.",
    )
)
register_compound(
    make_compound(
        name="Formic Acid",
        counts={"C": 1, "H": 2, "O": 2},
        formula="HCOOH",
        kind="acid",
        state="aq",
        color=(232, 220, 198),
        strength="weak",
        pKa=3.75,
        role="acid",
        anion="HCO2",
        reading="A simple weak carboxylic acid with stronger acidity than acetic acid.",
    )
)
register_compound(
    ionic_compound(
        "Sodium Hydroxide",
        "Na",
        "OH",
        kind="base",
        state="aq",
        color=(216, 240, 255),
        strength="strong",
        role="base",
        reading="A strong base with a high hydroxide ion concentration.",
    )
)
register_compound(
    ionic_compound(
        "Potassium Hydroxide",
        "K",
        "OH",
        kind="base",
        state="aq",
        color=(214, 236, 252),
        strength="strong",
        role="base",
        reading="A strong hydroxide base that behaves like NaOH in dilute titrations.",
    )
)
register_compound(
    ionic_compound(
        "Calcium Hydroxide",
        "Ca",
        "OH",
        kind="base",
        state="aq",
        color=(220, 234, 244),
        strength="strong",
        role="base",
        reading="A strong base when dissolved, though its solubility is limited.",
    )
)
register_compound(
    ionic_compound(
        "Barium Hydroxide",
        "Ba",
        "OH",
        kind="base",
        state="aq",
        color=(216, 232, 246),
        strength="strong",
        role="base",
        reading="A strong hydroxide base with fully dissociated OH groups in solution.",
    )
)
register_compound(
    make_compound(
        name="Ammonia",
        counts={"N": 1, "H": 3},
        formula="NH3",
        kind="base",
        state="aq",
        color=(228, 236, 244),
        strength="weak",
        pKb=4.75,
        role="base",
        cation="NH4",
        reading="A weak base that accepts protons to form ammonium ions.",
    )
)
register_compound(ionic_compound("Sodium Chloride", "Na", "Cl", kind="salt", state="aq", color=(232, 236, 242), reading="A highly soluble neutral salt."))
register_compound(ionic_compound("Potassium Chloride", "K", "Cl", kind="salt", state="aq", color=(230, 236, 244), reading="A soluble alkali metal salt."))
register_compound(ionic_compound("Silver Nitrate", "Ag", "NO3", kind="salt", state="aq", color=(234, 236, 246), reading="A source of silver ions used in precipitation reactions."))
register_compound(ionic_compound("Sodium Nitrate", "Na", "NO3", kind="salt", state="aq", color=(236, 238, 246), reading="A highly soluble nitrate salt."))
register_compound(ionic_compound("Potassium Iodide", "K", "I", kind="salt", state="aq", color=(250, 244, 214), reading="A soluble iodide salt used in yellow precipitate reactions."))
register_compound(ionic_compound("Lead Nitrate", "Pb", "NO3", kind="salt", state="aq", color=(242, 242, 246), reading="A soluble lead salt often used to demonstrate precipitation."))
register_compound(ionic_compound("Copper(II) Sulfate", "Cu", "SO4", kind="salt", state="aq", color=(74, 146, 228), reading="A blue solution containing Cu2+ ions."))
register_compound(ionic_compound("Iron(II) Sulfate", "Fe", "SO4", kind="salt", state="aq", color=(156, 188, 126), reading="A pale green iron salt solution."))
register_compound(ionic_compound("Zinc Chloride", "Zn", "Cl", kind="salt", state="aq", color=(204, 220, 236), reading="A soluble zinc salt commonly formed after acid-metal reactions."))
register_compound(ionic_compound("Copper(II) Chloride", "Cu", "Cl", kind="salt", state="aq", color=(118, 182, 120), reading="A green-blue copper salt solution."))
register_compound(ionic_compound("Sodium Sulfate", "Na", "SO4", kind="salt", state="aq", color=(232, 236, 242), reading="A soluble sulfate salt."))
register_compound(ionic_compound("Barium Chloride", "Ba", "Cl", kind="salt", state="aq", color=(232, 236, 242), reading="A soluble source of barium ions."))
register_compound(ionic_compound("Calcium Carbonate", "Ca", "CO3", kind="salt", state="solid", color=(244, 244, 240), reading="A sparingly soluble carbonate that releases CO2 with acids."))
register_compound(ionic_compound("Sodium Carbonate", "Na", "CO3", kind="salt", state="aq", color=(238, 240, 244), reading="A soluble carbonate salt that effervesces with acids."))
register_compound(ionic_compound("Sodium Hydrogen Carbonate", "Na", "HCO3", kind="salt", state="aq", color=(240, 242, 246), reading="A bicarbonate salt that reacts with acids to release carbon dioxide."))
register_compound(ionic_compound("Silver Chloride", "Ag", "Cl", kind="precipitate", state="solid", color=(248, 248, 248), reading="An insoluble white silver halide precipitate."))
register_compound(ionic_compound("Lead(II) Iodide", "Pb", "I", kind="precipitate", state="solid", color=(244, 212, 72), reading="A bright yellow lead iodide precipitate."))
register_compound(ionic_compound("Copper(II) Hydroxide", "Cu", "OH", kind="precipitate", state="solid", color=(94, 172, 240), reading="A blue insoluble hydroxide precipitate."))
register_compound(ionic_compound("Barium Sulfate", "Ba", "SO4", kind="precipitate", state="solid", color=(246, 246, 246), reading="A dense white sulfate precipitate."))
register_compound(
    make_compound(
        name="Water",
        counts={"H": 2, "O": 1},
        formula="H2O",
        kind="molecule",
        state="liquid",
        color=(188, 218, 244),
        reading="The solvent and the product of neutralization.",
    )
)
register_compound(
    make_compound(
        name="Hydrogen",
        counts={"H": 2},
        formula="H2",
        kind="gas",
        state="gas",
        color=(232, 242, 255),
        reading="A flammable gas produced when active metals reduce hydrogen ions.",
    )
)
register_compound(
    make_compound(
        name="Carbon Dioxide",
        counts={"C": 1, "O": 2},
        formula="CO2",
        kind="gas",
        state="gas",
        color=(232, 244, 248),
        reading="A gas released when acids react with carbonates or bicarbonates.",
    )
)
register_compound(
    make_compound(
        name="Zinc",
        counts={"Zn": 1},
        formula="Zn",
        kind="metal",
        state="solid",
        color=(190, 196, 210),
        cation="Zn",
        reading="A reactive metal that can displace hydrogen from acids.",
    )
)
register_compound(
    make_compound(
        name="Iron",
        counts={"Fe": 1},
        formula="Fe",
        kind="metal",
        state="solid",
        color=(126, 136, 150),
        cation="Fe",
        reading="A moderately reactive metal that can displace copper from solution.",
    )
)
register_compound(
    make_compound(
        name="Copper",
        counts={"Cu": 1},
        formula="Cu",
        kind="metal",
        state="solid",
        color=(212, 126, 72),
        cation="Cu",
        reading="A less reactive metal than iron and zinc.",
    )
)
register_compound(
    make_compound(
        name="Magnesium",
        counts={"Mg": 1},
        formula="Mg",
        kind="metal",
        state="solid",
        color=(210, 214, 220),
        cation="Mg",
        reading="A reactive alkaline earth metal that reacts readily with acids.",
    )
)

KNOWN_BY_KEY = {compound["key"]: compound for compound in KNOWN_COMPOUNDS}

TITRATION_SPECIES = [
    {"compound_key": counts_key({"H": 1, "Cl": 1}), "label": "HCl", "role": "acid", "strength": "strong", "pKa": None},
    {"compound_key": counts_key({"H": 1, "N": 1, "O": 3}), "label": "HNO3", "role": "acid", "strength": "strong", "pKa": None},
    {"compound_key": counts_key({"C": 2, "H": 4, "O": 2}), "label": "CH3COOH", "role": "acid", "strength": "weak", "pKa": 4.76},
    {"compound_key": counts_key({"C": 1, "H": 2, "O": 2}), "label": "HCOOH", "role": "acid", "strength": "weak", "pKa": 3.75},
    {"compound_key": counts_key({"Na": 1, "O": 1, "H": 1}), "label": "NaOH", "role": "base", "strength": "strong", "pKb": None},
    {"compound_key": counts_key({"K": 1, "O": 1, "H": 1}), "label": "KOH", "role": "base", "strength": "strong", "pKb": None},
    {"compound_key": counts_key({"N": 1, "H": 3}), "label": "NH3", "role": "base", "strength": "weak", "pKb": 4.75},
]


def lookup_known_compound(counts):
    return KNOWN_BY_KEY.get(counts_key(counts))


def compound_formula(compound):
    return compound.get("formula") or hill_formula(compound.get("counts", {}))


def describe_formula_counts(counts):
    formula = hill_formula(counts)
    if not counts:
        return "Empty flask"
    symbols = ", ".join(f"{symbol}{count}" for symbol, count in sorted(normalize_counts(counts).items()))
    return f"{formula} ({symbols})"


def infer_ionic_compound(counts):
    normalized = normalize_counts(counts)
    for cation_key in CATION_KEYS:
        for anion_key in ANION_KEYS:
            inferred_counts, formula, _, _ = combine_ions(cation_key, anion_key)
            if normalize_counts(inferred_counts) != normalized:
                continue

            cation_name = ION_LIBRARY[cation_key]["name"]
            anion_name = ION_LIBRARY[anion_key]["name"]
            if cation_key == "H":
                strength = "strong" if anion_key in {"Cl", "Br", "I", "NO3", "SO4"} else None
                acid_names = {
                    "Cl": "Hydrochloric Acid",
                    "Br": "Hydrobromic Acid",
                    "I": "Hydroiodic Acid",
                    "NO3": "Nitric Acid",
                    "SO4": "Sulfuric Acid",
                }
                return make_compound(
                    name=acid_names.get(anion_key, f"{anion_name.title()} Acid"),
                    counts=normalized,
                    formula=formula,
                    kind="acid",
                    state="aq",
                    strength=strength,
                    role="acid",
                    anion=anion_key,
                    reading="An inferred inorganic acid based on a hydrogen cation paired with an anion.",
                )

            if anion_key == "OH":
                return make_compound(
                    name=f"{cation_name.title()} Hydroxide",
                    counts=normalized,
                    formula=formula,
                    kind="base",
                    state="aq",
                    strength="strong",
                    role="base",
                    cation=cation_key,
                    anion=anion_key,
                    reading="An inferred hydroxide base built from a metal or ammonium cation paired with hydroxide.",
                )

            precipitating = insoluble_salt(cation_key, anion_key)
            return make_compound(
                name=f"{cation_name.title()} {anion_name}",
                counts=normalized,
                formula=formula,
                kind="precipitate" if precipitating else "salt",
                state="solid" if precipitating else "aq",
                cation=cation_key,
                anion=anion_key,
                reading="An inferred ionic compound recognized from a charge-balanced cation and anion pair.",
            )
    return None


def classify_compound(counts):
    counts = normalize_counts(counts)
    if not counts:
        return make_compound(
            name="Empty Flask",
            counts={},
            formula="-",
            kind="empty",
            state="aq",
            color=(60, 70, 88),
            reading="Add elements from the periodic table to build a reagent.",
        )

    known = lookup_known_compound(counts)
    if known:
        return dict(known)

    inferred = infer_ionic_compound(counts)
    if inferred:
        return inferred

    if len(counts) == 1:
        symbol = next(iter(counts))
        entry = ELEMENTS_BY_SYMBOL.get(symbol)
        if symbol in METAL_SYMBOLS:
            return make_compound(
                name=entry["name"] if entry else symbol,
                counts=counts,
                formula=symbol,
                kind="metal",
                state="solid",
                color=entry["color"] if entry else average_element_color(counts),
                cation=symbol if symbol in ION_LIBRARY else None,
                reading="A single element sample. Metallic elements can enter displacement or acid-metal reactions.",
            )
        return make_compound(
            name=entry["name"] if entry else symbol,
            counts=counts,
            formula=symbol,
            kind="element",
            state="gas" if symbol in {"H", "N", "O", "F", "Cl"} else "solid",
            color=entry["color"] if entry else average_element_color(counts),
            reading="A single element sample. Reactions depend strongly on state and bonding, which are simplified here.",
        )

    formula = hill_formula(counts)
    metals = [symbol for symbol in counts if symbol in METAL_SYMBOLS]
    has_h = "H" in counts
    has_o = "O" in counts
    has_c = "C" in counts

    if has_h and not metals and len(counts) <= 4:
        return make_compound(
            name="Custom Acid-Like Formula",
            counts=counts,
            formula=formula,
            kind="acid_guess",
            state="aq",
            color=average_element_color(counts),
            reading="The formula looks acid-like, but the simulator only treats recognized acids with full reaction confidence.",
        )

    if metals and has_o and has_h:
        return make_compound(
            name="Custom Hydroxide-Like Formula",
            counts=counts,
            formula=formula,
            kind="base_guess",
            state="aq",
            color=average_element_color(counts),
            reading="The formula resembles a hydroxide base. Exact stoichiometry is only guaranteed for recognized compounds.",
        )

    if metals and has_c and has_o:
        return make_compound(
            name="Custom Ionic Formula",
            counts=counts,
            formula=formula,
            kind="salt_guess",
            state="aq",
            color=average_element_color(counts),
            reading="This looks like an ionic compound. The reaction engine will stay conservative unless the ion pattern is recognized.",
        )

    return make_compound(
        name="Custom Compound",
        counts=counts,
        formula=formula,
        kind="custom",
        state="aq",
        color=average_element_color(counts),
        reading="A formula-only custom compound. When the simulator cannot infer a trustworthy model, it reports that directly instead of guessing.",
    )


def is_acid(compound):
    return compound.get("kind") == "acid"


def is_base(compound):
    return compound.get("kind") == "base"


def activity_rank(symbol):
    return ACTIVITY_SERIES.index(symbol) if symbol in ACTIVITY_SERIES else len(ACTIVITY_SERIES)


def insoluble_salt(cation_key, anion_key):
    if cation_key in ALKALI_CATIONS:
        return False
    if anion_key in {"NO3", "C2H3O2"}:
        return False
    # FIX: Ca(OH)2 Limewater exception
    if cation_key == "Ca" and anion_key == "OH":
        return False
    if anion_key in {"Cl", "Br", "I"}:
        return cation_key in {"Ag", "Pb"}
    if anion_key == "SO4":
        return cation_key in {"Ba", "Pb", "Ca", "Ag"}
    if anion_key == "OH":
        return cation_key not in {"Na", "K", "Ba"}
    if anion_key in {"CO3", "PO4"}:
        return cation_key not in {"Na", "K", "NH4"}
    return False


def product_style(compound):
    formula = compound_formula(compound)
    if formula == "AgCl":
        return {"color": (248, 248, 248), "type": "precipitation", "accent": (250, 250, 250)}
    if formula == "PbI2":
        return {"color": (244, 212, 72), "type": "precipitation", "accent": (244, 212, 72)}
    if formula == "Cu(OH)2":
        return {"color": (94, 172, 240), "type": "precipitation", "accent": (94, 172, 240)}
    if formula == "BaSO4":
        return {"color": (246, 246, 246), "type": "precipitation", "accent": (246, 246, 246)}
    if compound.get("kind") == "gas":
        return {"color": compound["color"], "type": "gas", "accent": compound["color"]}
    if compound.get("kind") == "precipitate":
        return {"color": compound["color"], "type": "precipitation", "accent": compound["color"]}
    return {"color": compound["color"], "type": "solution", "accent": compound["color"]}


def balance_reaction(left_parts, right_parts, limit=6):
    symbols = sorted({symbol for part in left_parts + right_parts for symbol in part.get("counts", {})})
    left_ranges = [range(1, limit + 1) for _ in left_parts]
    right_ranges = [range(1, limit + 1) for _ in right_parts]

    best = None
    for left_coeffs in itertools.product(*left_ranges):
        for right_coeffs in itertools.product(*right_ranges):
            balanced = True
            for symbol in symbols:
                left_total = sum(coeff * part["counts"].get(symbol, 0) for coeff, part in zip(left_coeffs, left_parts))
                right_total = sum(coeff * part["counts"].get(symbol, 0) for coeff, part in zip(right_coeffs, right_parts))
                if left_total != right_total:
                    balanced = False
                    break
            if balanced:
                score = sum(left_coeffs) + sum(right_coeffs)
                if best is None or score < best[0]:
                    best = (score, left_coeffs, right_coeffs)
        if best is not None:
            break
    if best is None:
        return [1] * len(left_parts), [1] * len(right_parts)
    return list(best[1]), list(best[2])


def equation_text(left_parts, right_parts):
    left_coeffs, right_coeffs = balance_reaction(left_parts, right_parts)

    def render(coeff, part):
        prefix = "" if coeff == 1 else str(coeff)
        return f"{prefix}{part['formula']}"

    left = " + ".join(render(coeff, part) for coeff, part in zip(left_coeffs, left_parts))
    right = " + ".join(render(coeff, part) for coeff, part in zip(right_coeffs, right_parts))
    return f"{left} -> {right}"


def reaction_result(kind, left_parts, right_parts, *, observation, reading, color, accent, confidence="high"):
    return {
        "type": kind,
        "equation": equation_text(left_parts, right_parts),
        "observation": observation,
        "reading": reading,
        "product_color": color,
        "accent": accent,
        "confidence": confidence,
    }


def acid_base_reaction(acid, base):
    if acid.get("anion") and base.get("anion") == "OH" and base.get("cation"):
        salt = ionic_compound(f"{ION_LIBRARY[base['cation']]['name']} {ION_LIBRARY[acid['anion']]['name']}", base["cation"], acid["anion"], state="aq")
        return reaction_result(
            "neutralization",
            [acid, base],
            [salt, lookup_known_compound({"H": 2, "O": 1})],
            observation="The mixture stays mostly clear while acid and base neutralize into water and a salt.",
            reading="Hydrogen ions from the acid combine with hydroxide ions from the base to make water. Because the salt stays dissolved, the strongest clues are the pH shift and released heat.",
            color=salt["color"],
            accent=(250, 168, 94),
        )

    if acid.get("anion") and compound_formula(base) == "NH3":
        salt = ionic_compound("Ammonium Salt", "NH4", acid["anion"], state="aq")
        return reaction_result(
            "neutralization",
            [acid, base],
            [salt],
            observation="The solution remains clear while ammonia accepts protons and becomes ammonium.",
            reading="Ammonia behaves as a weak base by accepting protons from the acid. The resulting ammonium salt stays dissolved, so the major visible change is the pH shift rather than a precipitate.",
            color=salt["color"],
            accent=(250, 168, 94),
        )
    return None


def acid_metal_reaction(acid, metal):
    cation = metal.get("cation")
    anion = acid.get("anion")
    if not cation or not anion:
        return None
    if activity_rank(cation) >= activity_rank("H"):
        return None
        
    salt = ionic_compound("Metal Salt", cation, anion, state="aq")
    
    # FIX: Nitric Acid Exception (Strong Oxidizer produces NO2 instead of H2)
    if anion == "NO3":
        no2 = make_compound(name="Nitrogen Dioxide", counts={"N":1, "O":2}, formula="NO2", kind="gas", state="gas", color=(180, 100, 50))
        water = lookup_known_compound({"H": 2, "O": 1})
        return reaction_result(
            "gas",
            [acid, metal],
            [salt, no2, water],
            observation="A toxic, brown NO2 gas is rapidly produced.",
            reading="Because Nitric Acid is a strong oxidizing agent, it oxidizes the metal but reduces itself into Nitrogen Dioxide gas instead of releasing Hydrogen gas.",
            color=salt["color"],
            accent=no2["color"],
        )

    # Standard Acid + Metal reaction
    hydrogen = lookup_known_compound({"H": 2})
    return reaction_result(
        "gas",
        [acid, metal],
        [salt, hydrogen],
        observation="Bubbles of hydrogen rise from the metal surface.",
        reading="The metal is above hydrogen in the activity series, so it donates electrons to hydrogen ions. The acid is reduced to H2 gas while the metal forms a salt in solution.",
        color=salt["color"],
        accent=hydrogen["color"],
    )


def acid_carbonate_reaction(acid, carbonate):
    cation = carbonate.get("cation")
    anion = acid.get("anion")
    if not cation or not anion:
        return None
    if carbonate.get("anion") not in {"CO3", "HCO3"}:
        return None
    salt = ionic_compound("Salt", cation, anion, state="aq")
    return reaction_result(
        "gas",
        [acid, carbonate],
        [salt, lookup_known_compound({"H": 2, "O": 1}), lookup_known_compound({"C": 1, "O": 2})],
        observation="Effervescence appears as carbon dioxide escapes from the liquid.",
        reading="Acid reacts with carbonate or hydrogen carbonate ions to form carbonic acid, which quickly decomposes into carbon dioxide and water. The bubbles are the clearest visual sign.",
        color=salt["color"],
        accent=(230, 244, 248),
    )


def displacement_reaction(metal, salt):
    if metal.get("kind") != "metal" or not salt.get("cation") or not salt.get("anion"):
        return None
    active_metal = metal.get("cation")
    displaced_metal = salt.get("cation")
    if active_metal not in ACTIVITY_SERIES or displaced_metal not in ACTIVITY_SERIES:
        return None
    if activity_rank(active_metal) >= activity_rank(displaced_metal):
        return None
    new_salt = ionic_compound("Displacement Salt", active_metal, salt["anion"], state="aq")
    displaced = classify_compound(ION_LIBRARY[displaced_metal]["counts"])
    return reaction_result(
        "displacement",
        [metal, salt],
        [new_salt, displaced],
        observation="A metal coating forms while the solution color shifts toward the new dissolved cation.",
        reading="The more reactive metal gives electrons to the dissolved metal ions, forcing them out of solution. That electron transfer is why the solid deposit forms on the metal surface.",
        color=new_salt["color"],
        accent=displaced["color"],
    )


def double_displacement(compound_a, compound_b):
    if not compound_a.get("cation") or not compound_a.get("anion"):
        return None
    if not compound_b.get("cation") or not compound_b.get("anion"):
        return None

    product_1 = ionic_compound("Product A", compound_a["cation"], compound_b["anion"], state="aq")
    product_2 = ionic_compound("Product B", compound_b["cation"], compound_a["anion"], state="aq")

    precipitates = []
    for product in (product_1, product_2):
        if insoluble_salt(product["cation"], product["anion"]):
            product["kind"] = "precipitate"
            product["state"] = "solid"
            style = product_style(product)
            product["color"] = style["color"]
            precipitates.append(product)

    if not precipitates:
        return None

    solid = precipitates[0]
    return reaction_result(
        "precipitation",
        [compound_a, compound_b],
        [product_1, product_2],
        observation=f"A visible solid appears as {solid['formula']} leaves solution.",
        reading="The ion pairs swap partners, and one of the new combinations is insoluble in water. Once that solid starts forming, the mixture turns cloudy or deposits crystals.",
        color=solid["color"],
        accent=solid["color"],
    )


def no_reaction(compound_a, compound_b):
    mixed_color = average_element_color(merge_counts(compound_a.get("counts", {}), compound_b.get("counts", {})))
    return {
        "type": "no_reaction",
        "equation": f"{compound_formula(compound_a)} + {compound_formula(compound_b)} -> no confident modelled change",
        "observation": "The simulator does not have enough trusted evidence to claim a specific visible reaction.",
        "reading": "This bench stays conservative on purpose. When a pair is not recognized by the reaction rules, it reports that limit instead of inventing products or pretending the chemistry is certain.",
        "product_color": mixed_color,
        "accent": (146, 176, 222),
        "confidence": "low",
    }


def analyze_reaction(counts_a, counts_b, heat_level=0):
    compound_a = classify_compound(counts_a)
    compound_b = classify_compound(counts_b)

    if compound_a["kind"] == "empty" or compound_b["kind"] == "empty":
        return {
            "type": "idle",
            "equation": "Build two reagents to start the reaction bench.",
            "observation": "No reaction can start until both flasks contain a reagent.",
            "reading": "Use the periodic table to add element counts into Flask A and Flask B. Recognized formulas unlock stronger chemistry readings and more specific reaction products.",
            "product_color": (150, 176, 214),
            "accent": (150, 176, 214),
            "confidence": "n/a",
        }

    acid = compound_a if is_acid(compound_a) else compound_b if is_acid(compound_b) else None
    base = compound_a if is_base(compound_a) else compound_b if is_base(compound_b) else None
    metal = compound_a if compound_a.get("kind") == "metal" else compound_b if compound_b.get("kind") == "metal" else None
    salt = compound_a if compound_a.get("kind") in {"salt", "precipitate"} else compound_b if compound_b.get("kind") in {"salt", "precipitate"} else None
    carbonate = None
    for candidate in (compound_a, compound_b):
        if candidate.get("anion") in {"CO3", "HCO3"}:
            carbonate = candidate
            break

    if acid and base:
        result = acid_base_reaction(acid, base)
        if result:
            return result

    if acid and carbonate:
        result = acid_carbonate_reaction(acid, carbonate)
        if result:
            return result

    if acid and metal:
        result = acid_metal_reaction(acid, metal)
        if result:
            return result

    if metal and salt:
        result = displacement_reaction(metal, salt)
        if result:
            return result

    result = double_displacement(compound_a, compound_b)
    if result:
        return result

    fallback = no_reaction(compound_a, compound_b)
    if heat_level >= 3:
        fallback["observation"] = "Heating is present, but the simulator still does not have a confident reaction rule for this pair."
        fallback["reading"] += " The burner can speed the animation, but it does not override the evidence threshold for claiming products."
    return fallback
