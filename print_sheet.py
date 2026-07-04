"""Print sheet layout boundary."""

from __future__ import annotations

from process_photo import LayoutSpec, build_front_back_sheet, build_print_sheet, parse_layout


VERY_LIGHT_GUIDE_COLORS = {
    "corner": (232, 232, 232),
    "line": (238, 238, 238),
    "outline": (242, 242, 242),
}


__all__ = [
    "LayoutSpec",
    "VERY_LIGHT_GUIDE_COLORS",
    "build_front_back_sheet",
    "build_print_sheet",
    "parse_layout",
]
