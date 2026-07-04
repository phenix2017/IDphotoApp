"""Photo specification loading boundary."""

from __future__ import annotations

from pathlib import Path

from process_photo import PhotoSpec, load_specs


def load_photo_specs(path: Path) -> dict[str, PhotoSpec]:
    specs = load_specs(path)
    if not specs:
        raise ValueError(f"No photo specs found in {path}")
    return specs


__all__ = ["PhotoSpec", "load_photo_specs"]
