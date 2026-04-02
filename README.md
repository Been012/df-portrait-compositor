# df-portrait-compositor

Generate dwarf portrait images from Dwarf Fortress (Steam/Premium) sprite sheets by parsing the game's graphics definition files, evaluating layer conditions against appearance data, and compositing the matching tiles with palette recoloring.

## Features

- Parses DF's `graphics_creatures_portrait_dwarf.txt` into structured layer rules
- **All three age groups**: BABY (age < 1), CHILD (age 1-11), and PORTRAIT (adult 12+) layer sets
- Evaluates 10+ condition types: caste, tissue color/length/shaping/curliness, body part modifiers (head broadness, nose shape/broadness, eye shape), equipment, syndromes (vampire, zombie, necromancer, ghost), material flags/types, item quality, and randomized part selection
- BP_MISSING condition support for injury-based layer filtering
- Implements DF's "first match wins" layer group logic for mutually exclusive alternatives
- Composites selected tiles onto an RGBA canvas with proper alpha blending
- Palette recoloring for skin and hair colors using DF's palette PNGs
- **HSV clothing tinting**: clothing layers use HSV color space to apply the item's material/dye color with naturally muted saturation, matching DF's subdued portrait aesthetic
- **Creature portraits**: load portrait sprites for 500+ creatures across 6 sprite sheets (domestic, surface, aquatic, animal people, and more)
- Appearance-hash-based caching so portraits only regenerate when the dwarf's look changes
- Deterministic random seed (from unit ID) for consistent clothing/feature variation

## Installation

```bash
pip install df-portrait-compositor
```

Or install from source:

```bash
git clone https://github.com/Been012/df-portrait-compositor.git
cd df-portrait-compositor
pip install -e .
```

## Requirements

- Python 3.11+
- Pillow
- A Dwarf Fortress Premium (Steam) installation (for the sprite sheet PNGs and graphics definition file)

## Quick Start

### CLI

The fastest way to see it in action:

```bash
# Generate a random demo portrait
df-portrait demo

# Generate 10 random portraits in a directory
df-portrait demo -n 10 -o my_portraits/

# Generate with a specific seed for reproducibility
df-portrait demo --seed 42

# Generate from JSON appearance data
df-portrait generate '{"sex":"female","skin_color":"PEACH","hair_color":"BROWN","hair_length":200,"hair_shaping":"BRAIDED"}'

# Generate from a df-storyteller snapshot file
df-portrait from-snapshot path/to/snapshot.json -o portraits/

# Generate for a specific dwarf from a snapshot
df-portrait from-snapshot path/to/snapshot.json --unit-id 7116

# Specify DF install path (auto-detected on common Steam paths)
df-portrait --df-path "C:\path\to\Dwarf Fortress" demo
```

### Python API

```python
from df_portrait_compositor import compose_portrait, DwarfAppearanceData

# Point to your DF install directory
df_install = r"C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress"

# Build appearance data (all fields have sensible defaults)
appearance = DwarfAppearanceData(
    sex="female",
    skin_color="PEACH",
    hair_color="BROWN",
    hair_length=150,
    hair_shaping="BRAIDED",
    beard_length=0,
    head_broadness=120,
    eye_round_vs_narrow=80,
    nose_upturned=130,
    nose_broadness=90,
    random_seed=42,
)

# Compose and save
img = compose_portrait(df_install, appearance, scale=2)
img.save("portrait.png")
```

### Child and Baby Portraits

The compositor automatically selects the correct sprite set based on age:

```python
# Baby portrait (age < 1)
baby = DwarfAppearanceData(age=0.5, skin_color="PEACH", random_seed=1)
img = compose_portrait(df_install, baby)

# Child portrait (age 1-11)
child = DwarfAppearanceData(age=7, sex="female", skin_color="PEACH", hair_color="BROWN", random_seed=2)
img = compose_portrait(df_install, child)
```

### Creature Portraits

Load portrait sprites for any of DF's 500+ creatures:

```python
from df_portrait_compositor import get_creature_portrait, list_available_creatures

# Get a specific creature's portrait
img = get_creature_portrait(df_install, "DOG", scale=2)
if img:
    img.save("dog_portrait.png")

# Caste-specific portraits (e.g. male/female peacock)
img = get_creature_portrait(df_install, "BIRD_PEAFOWL_BLUE", caste="MALE")

# List all available creature IDs
creatures = list_available_creatures(df_install)
print(f"{len(creatures)} creatures with portraits")
```

### Clothing with Material Colors

Equipment items with material colors are tinted using HSV color space:

```python
appearance = DwarfAppearanceData(
    sex="male",
    skin_color="PEACH",
    hair_color="BROWN",
    equipment=[
        {
            "slot": "BODY_UPPER",
            "item_type": "ARMOR",
            "item_subtype": "ITEM_ARMOR_SHIRT",
            "material_flags": ["IS_METAL"],
            "material_color": [180, 180, 200],  # Steel-gray RGB
            "quality": 3,
        },
    ],
    random_seed=42,
)
img = compose_portrait(df_install, appearance, scale=2)
```

### Using generate_portrait for Caching

If you are generating portraits for many dwarves, `generate_portrait` handles caching automatically. It takes a raw appearance dict and a cache directory, and only regenerates when appearance data changes:

```python
from pathlib import Path
from df_portrait_compositor import generate_portrait

appearance_dict = {
    "sex": "male",
    "skin_color": "PEACH",
    "hair_color": "BLACK",
    "beard_color": "BLACK",
    "hair_length": 200,
    "beard_length": 300,
    "beard_shaping": "DOUBLE_BRAIDS",
    "head_broadness": 140,
    "nose_length": 160,
    "eyebrow_density": 130,
    "random_seed": 1001,
}

portrait_path = generate_portrait(
    df_install=r"C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress",
    unit_id=1001,
    appearance=appearance_dict,
    cache_dir=Path("./portrait_cache"),
)
# Returns Path to the PNG, or None on failure
```

## Getting Appearance Data from DFHack

The appearance fields map to data extracted from DF's internal structures via DFHack. You need a Lua script running inside DFHack to read each dwarf's:

- **Sex**: `unit.sex` (0 = female, 1 = male)
- **Skin/hair/beard colors**: Resolved from `unit.appearance.colors` via `caste.color_modifiers` and `descriptor_color` lookups
- **Hair/beard length**: From `unit.appearance.tissue_length` indexed through `caste.bp_appearance.style_part_idx`
- **Hair/beard shaping**: From `unit.appearance.tissue_style` (0=NEATLY_COMBED, 1=BRAIDED, 2=DOUBLE_BRAIDS, 3=PONY_TAIL, 4=CLEAN_SHAVEN)
- **Body part modifiers** (head broadness, nose shape, eye shape): From `unit.appearance.bp_modifiers` indexed through `caste.bp_appearance.modifier_idx/part_idx`
- **Equipment**: From `unit.inventory` items with material color via `dfhack.matinfo.decode(item)`

The `dfhack_scripts/` directory contains debug scripts that demonstrate how to read these values:

| Script | Purpose |
|--------|---------|
| `storyteller-debug-colors.lua` | Dump color modifier values for all citizens |
| `storyteller-debug-hair.lua` | Identify tissue types and lengths for each styled tissue |
| `storyteller-debug-bpmod.lua` | Show body part appearance modifiers (density, broadness, etc.) |

### Tissue Length Index Layout

The indices into `unit.appearance.tissue_length` and `unit.appearance.tissue_style` vary by sex. The mapping is determined by `caste.bp_appearance.style_part_idx` and `style_layer_idx`, but for the default dwarf creature definition:

**Male** (12 tissue entries):
| Index | Tissue |
|-------|--------|
| 0, 1 | SIDEBURNS |
| 2 | CHIN_WHISKERS (beard) |
| 3 | MOUSTACHE |
| 4, 5 | EYEBROW |
| 6, 7 | HAIR (scalp) |
| 8, 9 | CHEEK_WHISKERS (on CHEEK body parts) |
| 10, 11 | N/A |

**Female** (6 tissue entries):
| Index | Tissue |
|-------|--------|
| 0, 1 | EYEBROW |
| 2, 3 | HAIR (scalp) |
| 4, 5 | N/A |

**HEAD body part layer indices** (for `bp_appearance.layer_idx`):
| Layer | Tissue |
|-------|--------|
| 0, 1 | SIDEBURNS |
| 2 | CHIN_WHISKERS |
| 3 | MOUSTACHE |
| 4, 5 | EYEBROW |
| 6, 7 | HAIR |
| 8 | SKIN |

## API Reference

### Core Functions

#### `compose_portrait(df_install, appearance, scale=2)`

Compose a portrait from sprite sheet layers. Automatically selects BABY, CHILD, or PORTRAIT layer set based on `appearance.age`.

- **df_install** (`str`): Path to the Dwarf Fortress installation directory.
- **appearance** (`DwarfAppearanceData`): Dwarf appearance data for condition matching.
- **scale** (`int`): Upscale factor. 1 = 96px native, 2 = 192px (default).
- **Returns**: `PIL.Image.Image` (RGBA).

#### `generate_portrait(df_install, unit_id, appearance, cache_dir=None)`

Generate and cache a portrait PNG for a dwarf.

- **df_install** (`str`): Path to the DF installation directory.
- **unit_id** (`int`): Dwarf unit ID (used for filename and random seed).
- **appearance** (`dict`): Raw appearance dict (keys match `DwarfAppearanceData` fields).
- **cache_dir** (`Path | None`): Directory to store cached PNGs. Required for output.
- **Returns**: `Path` to the generated PNG, or `None` on failure.

#### `get_creature_portrait(df_install, creature_id, caste="", scale=2)`

Get a creature's portrait sprite from DF's creature portrait sprite sheets.

- **df_install** (`str`): Path to the DF installation directory.
- **creature_id** (`str`): DF creature ID (e.g. "DOG", "CAT", "DRAGON").
- **caste** (`str`): Optional caste for dimorphic species (e.g. "MALE", "FEMALE").
- **scale** (`int`): Upscale factor. 1 = 96px, 2 = 192px (default).
- **Returns**: `PIL.Image.Image` (RGBA), or `None` if no portrait found.

#### `list_available_creatures(df_install)`

List all creature IDs that have portrait sprites available.

- **df_install** (`str`): Path to the DF installation directory.
- **Returns**: `list[str]` of sorted creature ID strings.

### Data Classes

#### `DwarfAppearanceData`

Dataclass holding all appearance attributes used for condition evaluation. All fields have defaults, so partial data still produces a portrait (with fewer layers).

Key fields: `sex`, `skin_color`, `hair_color`, `beard_color`, `hair_length`, `hair_shaping`, `hair_curly`, `beard_length`, `beard_shaping`, `head_broadness`, `eye_round_vs_narrow`, `eye_deep_set`, `eyebrow_density`, `nose_upturned`, `nose_length`, `nose_broadness`, `is_vampire`, `is_zombie`, `is_necromancer`, `is_ghost`, `equipment`, `random_seed`, `age`.

#### `SelectedLayer`

Dataclass representing a layer selected for rendering: `tile_page`, `tile_x`, `tile_y`, `palette_name`, `palette_index`, `use_item_palette`, `item_color`.

#### `LayerRule`

Dataclass representing a parsed layer rule from the graphics definition file, including all condition types.

### Parser and Evaluator

#### `parse_portrait_graphics(filepath)`

Parse a DF portrait graphics definition file into a list of `LayerRule` objects. Parses all three age layer sets (BABY, CHILD, PORTRAIT).

#### `evaluate_layers(rules, appearance)`

Evaluate layer rules against appearance data and return matching `SelectedLayer` objects in render order.

### Constants

#### `TILE_SIZE`

The native tile size in pixels (96).

## License

MIT
