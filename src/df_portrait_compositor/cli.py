"""Command-line interface for df-portrait-compositor."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from df_portrait_compositor import compose_portrait, DwarfAppearanceData, PORTRAIT_RACES


# DF color names used in the portrait graphics
SKIN_COLORS = [
    "DARK_BROWN", "BURNT_UMBER", "BROWN", "CINNAMON", "COPPER", "DARK_TAN",
    "PALE_BROWN", "RAW_UMBER", "SEPIA", "DARK_PEACH", "ECRU",
    "PALE_CHESTNUT", "PEACH", "TAN", "TAUPE_SANDY", "PALE_PINK", "PINK",
    "TAUPE_PALE",
]

HAIR_COLORS = [
    "BLACK", "CHARCOAL", "CHESTNUT", "CINNAMON", "COPPER", "MAHOGANY",
    "PUMPKIN", "RAW_UMBER", "RUSSET", "AMBER", "AUBURN", "BURNT_SIENNA",
    "DARK_CHESTNUT", "LIGHT_BROWN", "OCHRE", "PALE_BROWN", "SEPIA",
    "TAUPE_DARK", "TAUPE_GRAY", "TAUPE_MEDIUM", "BROWN", "BURNT_UMBER",
    "CHOCOLATE", "DARK_BROWN", "BUFF", "DARK_TAN", "ECRU", "FLAX", "GOLD",
    "GOLDEN_YELLOW", "GOLDENROD", "PALE_CHESTNUT", "SAFFRON", "TAN",
    "TAUPE_PALE", "TAUPE_SANDY", "GRAY", "WHITE",
]

SHAPINGS = ["", "NEATLY_COMBED", "BRAIDED", "DOUBLE_BRAIDS", "PONY_TAILS"]


def _find_df_install() -> str | None:
    """Try to auto-detect DF install path."""
    candidates = [
        Path("C:/Program Files (x86)/Steam/steamapps/common/Dwarf Fortress"),
        Path("C:/Program Files/Steam/steamapps/common/Dwarf Fortress"),
        Path("D:/SteamLibrary/steamapps/common/Dwarf Fortress"),
        Path("E:/SteamLibrary/steamapps/common/Dwarf Fortress"),
        Path.home() / ".steam/steam/steamapps/common/Dwarf Fortress",
        Path.home() / ".local/share/Steam/steamapps/common/Dwarf Fortress",
    ]
    for p in candidates:
        if (p / "data/vanilla/vanilla_creatures_graphics/graphics/images/portraits").exists():
            return str(p)
    return None


def _random_appearance(seed: int | None = None) -> DwarfAppearanceData:
    """Generate a random but valid appearance for demo purposes."""
    rng = random.Random(seed)
    sex = rng.choice(["male", "female"])
    hair_color = rng.choice(HAIR_COLORS)
    hair_length = rng.randint(0, 350)
    shaping = rng.choice(SHAPINGS) if hair_length >= 50 else ""

    return DwarfAppearanceData(
        sex=sex,
        skin_color=rng.choice(SKIN_COLORS),
        hair_color=hair_color,
        beard_color=hair_color,
        eyebrow_color=hair_color,
        hair_length=hair_length,
        hair_shaping=shaping,
        hair_curly=rng.randint(0, 200),
        beard_length=rng.randint(0, 300) if sex == "male" else 0,
        beard_shaping=rng.choice(SHAPINGS[:3]) if sex == "male" else "",
        head_broadness=rng.randint(50, 150),
        eye_round_vs_narrow=rng.randint(50, 170),
        eye_deep_set=rng.randint(50, 170),
        eyebrow_density=rng.randint(40, 160),
        nose_upturned=rng.randint(30, 180),
        nose_length=rng.randint(50, 180),
        nose_broadness=rng.randint(50, 170),
        random_seed=seed or rng.randint(0, 100000),
    )


def cmd_demo(args: argparse.Namespace) -> None:
    """Generate random demo portraits."""
    df_install = args.df_path or _find_df_install()
    if not df_install:
        print("Error: Could not find Dwarf Fortress install.")
        print("Specify with: df-portrait demo --df-path \"C:/path/to/Dwarf Fortress\"")
        sys.exit(1)

    count = args.count
    output = Path(args.output)
    race = args.race.upper()

    if count == 1:
        seed = args.seed or random.randint(0, 100000)
        appearance = _random_appearance(seed)
        img = compose_portrait(df_install, appearance, scale=args.scale, race=race)
        img.save(output, "PNG")
        print(f"Saved {race.lower()} portrait to {output} (seed={seed})")
    else:
        output.mkdir(parents=True, exist_ok=True)
        base_seed = args.seed or random.randint(0, 100000)
        for i in range(count):
            seed = base_seed + i
            appearance = _random_appearance(seed)
            path = output / f"portrait_{seed}.png"
            img = compose_portrait(df_install, appearance, scale=args.scale, race=race)
            img.save(path, "PNG")
            print(f"  [{i+1}/{count}] {appearance.sex:6s} seed={seed} -> {path}")
        print(f"Generated {count} {race.lower()} portraits in {output}/")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate a portrait from a JSON appearance dict."""
    df_install = args.df_path or _find_df_install()
    if not df_install:
        print("Error: Could not find Dwarf Fortress install.")
        print("Specify with: df-portrait generate --df-path \"C:/path/to/Dwarf Fortress\" ...")
        sys.exit(1)

    try:
        appearance_data = json.loads(args.appearance)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)

    seed = args.seed or int(hashlib.md5(args.appearance.encode()).hexdigest(), 16) % 100000

    app = DwarfAppearanceData(
        sex=appearance_data.get("sex", "male"),
        skin_color=appearance_data.get("skin_color", "PEACH"),
        hair_color=appearance_data.get("hair_color", "BROWN"),
        beard_color=appearance_data.get("beard_color", appearance_data.get("hair_color", "BROWN")),
        eyebrow_color=appearance_data.get("eyebrow_color", appearance_data.get("hair_color", "BROWN")),
        hair_length=appearance_data.get("hair_length", 100),
        hair_shaping=appearance_data.get("hair_shaping", ""),
        hair_curly=appearance_data.get("hair_curly", 0),
        beard_length=appearance_data.get("beard_length", 0),
        beard_shaping=appearance_data.get("beard_shaping", ""),
        head_broadness=appearance_data.get("head_broadness", 100),
        eye_round_vs_narrow=appearance_data.get("eye_round_vs_narrow", 100),
        eye_deep_set=appearance_data.get("eye_deep_set", 100),
        eyebrow_density=appearance_data.get("eyebrow_density", 100),
        nose_upturned=appearance_data.get("nose_upturned", 100),
        nose_length=appearance_data.get("nose_length", 100),
        nose_broadness=appearance_data.get("nose_broadness", 100),
        is_vampire=appearance_data.get("is_vampire", False),
        random_seed=seed,
        age=appearance_data.get("age", 0),
    )

    race = args.race.upper()
    img = compose_portrait(df_install, app, scale=args.scale, race=race)
    output = Path(args.output)
    img.save(output, "PNG")
    print(f"Saved {race.lower()} portrait to {output}")


def cmd_from_snapshot(args: argparse.Namespace) -> None:
    """Generate portraits from a storyteller snapshot JSON file."""
    df_install = args.df_path or _find_df_install()
    if not df_install:
        print("Error: Could not find Dwarf Fortress install.")
        sys.exit(1)

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"Error: Snapshot file not found: {snapshot_path}")
        sys.exit(1)

    with open(snapshot_path, encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    citizens = data.get("data", {}).get("citizens", [])
    if not citizens:
        print("No citizens found in snapshot.")
        sys.exit(1)

    # Style name mapping (Lua names -> graphics condition names)
    style_map = {
        "combed": "NEATLY_COMBED", "braided": "BRAIDED",
        "double_braids": "DOUBLE_BRAIDS", "pony_tail": "PONY_TAILS",
        "shaved": "", "thinning": "", "unkempt": "",
    }

    output = Path(args.output)
    unit_id = args.unit_id

    if unit_id is not None:
        citizens = [c for c in citizens if c.get("unit_id") == unit_id]
        if not citizens:
            print(f"Error: Unit ID {unit_id} not found in snapshot.")
            sys.exit(1)

    output.mkdir(parents=True, exist_ok=True)

    for citizen in citizens:
        cid = citizen["unit_id"]
        name = citizen.get("name", f"unit_{cid}")
        a = citizen.get("appearance", {})

        if not a.get("skin_color"):
            print(f"  Skipping {name} (no appearance data)")
            continue

        hair_shaping = style_map.get(a.get("hair_style", ""), "")
        beard_shaping = style_map.get(a.get("beard_style", ""), "")

        app = DwarfAppearanceData(
            sex=citizen.get("sex", "male"),
            skin_color=a.get("skin_color", "PEACH"),
            hair_color=a.get("hair_color", "BROWN"),
            beard_color=a.get("beard_color", a.get("hair_color", "BROWN")),
            eyebrow_color=a.get("eyebrow_color", a.get("hair_color", "BROWN")),
            hair_length=a.get("hair_length", 0),
            hair_shaping=hair_shaping,
            hair_curly=a.get("hair_curly", 0),
            beard_length=a.get("beard_length", 0) if citizen.get("sex") == "male" else 0,
            beard_shaping=beard_shaping,
            head_broadness=a.get("body_broadness", 100),
            eye_round_vs_narrow=a.get("eye_round_vs_narrow", 100),
            eye_deep_set=a.get("eye_deep_set", 100),
            eyebrow_density=a.get("eyebrow_density", 100),
            nose_upturned=a.get("nose_upturned", 100),
            nose_length=a.get("nose_length", 100),
            nose_broadness=a.get("nose_broadness", 100),
            is_vampire=citizen.get("is_vampire", False),
            random_seed=cid,
            age=citizen.get("age", 0),
        )

        race = citizen.get("race", args.race).upper()
        img = compose_portrait(df_install, app, scale=args.scale, race=race)
        path = output / f"portrait_{cid}.png"
        img.save(path, "PNG")
        print(f"  {name} -> {path}")

    print(f"Generated {len(citizens)} portrait(s) in {output}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="df-portrait",
        description="Generate dwarf portraits from Dwarf Fortress sprite sheets.",
    )
    parser.add_argument(
        "--df-path",
        help="Path to Dwarf Fortress install (auto-detected if not specified)",
    )
    parser.add_argument(
        "--scale", type=int, default=2,
        help="Upscale factor (1=96px, 2=192px, 4=384px). Default: 2",
    )
    parser.add_argument(
        "--race", default="DWARF",
        help=f"Creature race ({', '.join(sorted(PORTRAIT_RACES))}). Default: DWARF",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # demo
    demo_parser = subparsers.add_parser(
        "demo", help="Generate random demo portraits",
    )
    demo_parser.add_argument(
        "-n", "--count", type=int, default=1,
        help="Number of portraits to generate (default: 1)",
    )
    demo_parser.add_argument(
        "-o", "--output", default="portrait.png",
        help="Output file (single) or directory (multiple). Default: portrait.png",
    )
    demo_parser.add_argument(
        "--seed", type=int, help="Random seed for reproducible results",
    )

    # generate
    gen_parser = subparsers.add_parser(
        "generate", help="Generate a portrait from JSON appearance data",
    )
    gen_parser.add_argument(
        "appearance", help='JSON string with appearance data, e.g. \'{"sex":"female","skin_color":"PEACH","hair_length":200}\'',
    )
    gen_parser.add_argument(
        "-o", "--output", default="portrait.png",
        help="Output file. Default: portrait.png",
    )
    gen_parser.add_argument(
        "--seed", type=int, help="Random seed for deterministic features (mouth, eyebrows)",
    )

    # from-snapshot
    snap_parser = subparsers.add_parser(
        "from-snapshot", help="Generate portraits from a df-storyteller snapshot JSON",
    )
    snap_parser.add_argument(
        "snapshot", help="Path to snapshot JSON file",
    )
    snap_parser.add_argument(
        "--unit-id", type=int, dest="unit_id",
        help="Generate for a specific unit ID only",
    )
    snap_parser.add_argument(
        "-o", "--output", default="portraits",
        help="Output directory. Default: portraits/",
    )

    args = parser.parse_args()

    if args.command == "demo":
        cmd_demo(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "from-snapshot":
        cmd_from_snapshot(args)


if __name__ == "__main__":
    main()
