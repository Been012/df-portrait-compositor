"""Generate dwarf portraits from Dwarf Fortress sprite sheets.

This package parses DF's portrait graphics definition files, evaluates
layer conditions against dwarf appearance data, and composites the
matching sprite tiles into a final portrait image with palette recoloring.
"""

from df_portrait_compositor.compositor import compose_portrait, generate_portrait
from df_portrait_compositor.evaluator import DwarfAppearanceData, SelectedLayer, evaluate_layers
from df_portrait_compositor.graphics_parser import LayerRule, parse_portrait_graphics
from df_portrait_compositor.tile_loader import TILE_SIZE

__all__ = [
    "compose_portrait",
    "generate_portrait",
    "DwarfAppearanceData",
    "SelectedLayer",
    "evaluate_layers",
    "LayerRule",
    "parse_portrait_graphics",
    "TILE_SIZE",
]
