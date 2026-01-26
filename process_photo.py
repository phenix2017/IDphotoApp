#!/usr/bin/env python3
"""Process ID photos with auto-crop, background replacement, and print layout."""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from PIL import Image

try:
    import cv2
except ImportError as exc:  # pragma: no cover - handled by runtime env
    raise SystemExit("OpenCV is required. Install dependencies from requirements.txt") from exc

try:
    import mediapipe as mp
except ImportError:  # pragma: no cover - optional
    mp = None


@dataclass
class PhotoSpec:
    name: str
    width_in: float
    height_in: float
    head_height_ratio: float
    eye_line_from_bottom_ratio: float
    background_rgb: Tuple[int, int, int]


@dataclass
class LayoutSpec:
    width_in: float
    height_in: float


def load_specs(path: Path) -> Dict[str, PhotoSpec]:
    data = json.loads(path.read_text())
    specs: Dict[str, PhotoSpec] = {}
    for key, value in data.items():
        width_in = value.get("photo_width_in")
        height_in = value.get("photo_height_in")
        if width_in is None:
            width_in = value["photo_width_mm"] / 25.4
        if height_in is None:
            height_in = value["photo_height_mm"] / 25.4
        specs[key] = PhotoSpec(
            name=value["name"],
            width_in=width_in,
            height_in=height_in,
            head_height_ratio=value["head_height_ratio"],
            eye_line_from_bottom_ratio=value["eye_line_from_bottom_ratio"],
            background_rgb=tuple(value["background_rgb"]),
        )
    return specs


def detect_face(image_bgr: np.ndarray) -> Tuple[Tuple[int, int, int, int], Tuple[int, int]]:
    """Detect face using OpenCV cascade classifier (no MediaPipe dependency)."""
    
    # Load OpenCV cascade classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    cascade = cv2.CascadeClassifier(cascade_path)
    
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    # Use conservative parameters that work well with both synthetic and real photos
    faces = cascade.detectMultiScale(gray, scaleFactor=1.01, minNeighbors=3, minSize=(30, 30))
    
    if len(faces) == 0:
        # Try more lenient parameters
        faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=2, minSize=(20, 20))
    
    if len(faces) == 0:
        raise RuntimeError("No face detected. Please use a clearer, front-facing photo.")
    
    # Get largest face
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
    
    # Estimate eye position (roughly 1/3 from top of face)
    eye_x = x + w // 2
    eye_y = y + int(h * 0.35)
    
    return (x, y, w, h), (eye_x, eye_y)


def replace_background(image_bgr: np.ndarray, background_rgb: Tuple[int, int, int]) -> np.ndarray:
    """Replace background using simple color-based segmentation (no MediaPipe dependency).
    
    For better results, consider implementing MediaPipe or DeepLab integration.
    This basic version uses edge detection and color clustering.
    """
    # Convert to HSV for better skin detection
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    
    # Skin color range in HSV (very basic)
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Dilate to fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=1)
    
    # Create composite
    background = np.full_like(image_bgr, background_rgb[::-1])  # Convert RGB to BGR
    condition = mask[:, :, None] > 128
    composite = np.where(condition, image_bgr, background)
    return composite


def compute_output_size_px(spec: PhotoSpec, dpi: int) -> Tuple[int, int]:
    return int(round(spec.width_in * dpi)), int(round(spec.height_in * dpi))


def crop_to_spec(
    image_bgr: np.ndarray,
    bbox: Tuple[int, int, int, int],
    eye_point: Tuple[int, int],
    spec: PhotoSpec,
    dpi: int,
) -> np.ndarray:
    out_w, out_h = compute_output_size_px(spec, dpi)
    x_min, y_min, box_w, box_h = bbox

    target_head_height = spec.head_height_ratio * out_h
    scale = target_head_height / max(box_h, 1)

    resized = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    eye_x, eye_y = eye_point
    eye_x = int(round(eye_x * scale))
    eye_y = int(round(eye_y * scale))

    target_eye_y = int(round(out_h * (1 - spec.eye_line_from_bottom_ratio)))

    left = int(round(eye_x - out_w / 2))
    top = int(round(eye_y - target_eye_y))

    return crop_with_padding(resized, left, top, out_w, out_h, spec.background_rgb)


def crop_with_padding(
    image_bgr: np.ndarray,
    left: int,
    top: int,
    width: int,
    height: int,
    background_rgb: Tuple[int, int, int],
) -> np.ndarray:
    img_h, img_w, _ = image_bgr.shape

    right = left + width
    bottom = top + height

    pad_left = max(0, -left)
    pad_top = max(0, -top)
    pad_right = max(0, right - img_w)
    pad_bottom = max(0, bottom - img_h)

    if any((pad_left, pad_top, pad_right, pad_bottom)):
        image_bgr = cv2.copyMakeBorder(
            image_bgr,
            pad_top,
            pad_bottom,
            pad_left,
            pad_right,
            borderType=cv2.BORDER_CONSTANT,
            value=background_rgb,
        )
        left += pad_left
        top += pad_top

    return image_bgr[top : top + height, left : left + width]


def build_print_sheet(
    photo: Image.Image,
    layout: LayoutSpec,
    dpi: int,
    margin_in: float = 0.25,
    spacing_in: float = 0.05,
    copies: int = 6,
) -> Image.Image:
    """Build print sheet maximizing photo usage on paper.
    
    Args:
        photo: Photo to tile
        layout: Sheet dimensions (width_in, height_in)
        dpi: Dots per inch resolution
        margin_in: Margin from edges (default: 0.25" - standard print margin)
        spacing_in: Space between photos (default: 0.05")
        copies: Number of photos to place
    
    Returns:
        PIL Image with tiled photos
    """
    sheet_w = int(round(layout.width_in * dpi))
    sheet_h = int(round(layout.height_in * dpi))
    
    # Use minimal margins and spacing for maximum photo density
    margin = int(round(margin_in * dpi))
    spacing = int(round(spacing_in * dpi))
    
    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    photo_w, photo_h = photo.size

    # Calculate how many photos fit per row and column
    available_width = sheet_w - 2 * margin
    available_height = sheet_h - 2 * margin
    
    # Calculate maximum photos that can fit with original orientation
    max_cols_orig = max(1, (available_width + spacing) // (photo_w + spacing))
    max_rows_orig = max(1, (available_height + spacing) // (photo_h + spacing))
    total_photos_orig = max_cols_orig * max_rows_orig
    
    # Calculate maximum photos that can fit with 90-degree rotation
    photo_w_rot, photo_h_rot = photo_h, photo_w  # Swap dimensions for rotation
    max_cols_rot = max(1, (available_width + spacing) // (photo_w_rot + spacing))
    max_rows_rot = max(1, (available_height + spacing) // (photo_h_rot + spacing))
    total_photos_rot = max_cols_rot * max_rows_rot
    
    # Choose orientation that fits more photos
    if total_photos_rot > total_photos_orig:
        photo = photo.rotate(90, expand=True)
        photo_w, photo_h = photo_w_rot, photo_h_rot
        max_cols = max_cols_rot
        max_rows = max_rows_rot
    else:
        max_cols = max_cols_orig
        max_rows = max_rows_orig
    
    # Center the photos on the sheet for better appearance
    total_photos_width = max_cols * photo_w + (max_cols - 1) * spacing
    total_photos_height = max_rows * photo_h + (max_rows - 1) * spacing
    
    # Calculate centered margins
    left_margin = margin + (available_width - total_photos_width) // 2
    top_margin = margin + (available_height - total_photos_height) // 2
    
    # Create drawing context for guide lines
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    guide_color = (200, 200, 200)  # Light gray guide lines
    guide_width = 2
    
    placed = 0
    for row in range(max_rows):
        for col in range(max_cols):
            if placed >= copies:
                break
            x = left_margin + col * (photo_w + spacing)
            y = top_margin + row * (photo_h + spacing)
            sheet.paste(photo, (x, y))
            
            # Draw frame/border around the photo
            frame_color = (150, 150, 150)  # Dark gray frame
            frame_width = 2
            draw.rectangle(
                [(x, y), (x + photo_w - 1, y + photo_h - 1)],
                outline=frame_color,
                width=frame_width
            )
            
            placed += 1
        if placed >= copies:
            break

    # Draw vertical guide lines between photos (after photos are placed)
    for col in range(1, max_cols):
        x = left_margin + col * (photo_w + spacing) - spacing // 2
        draw.line([(x, top_margin), (x, top_margin + max_rows * photo_h + (max_rows - 1) * spacing)],
                  fill=guide_color, width=guide_width)

    # Draw horizontal guide lines between photos
    for row in range(1, max_rows):
        y = top_margin + row * (photo_h + spacing) - spacing // 2
        draw.line([(left_margin, y), (left_margin + max_cols * photo_w + (max_cols - 1) * spacing, y)],
                  fill=guide_color, width=guide_width)

    return sheet


def parse_layout(value: str) -> LayoutSpec:
    try:
        width_str, height_str = value.lower().split("x")
        return LayoutSpec(width_in=float(width_str), height_in=float(height_str))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("layout must be like 4x6 or 6x6") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Process ID photos for passport specs.")
    parser.add_argument("input", type=Path, help="Input photo path")
    parser.add_argument("--specs", type=Path, default=Path("specs.json"))
    parser.add_argument("--country", required=True, help="Country code from specs.json")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--replace-bg", action="store_true")
    parser.add_argument("--layout", type=parse_layout, default=parse_layout("4x6"))
    parser.add_argument("--copies", type=int, default=6)
    parser.add_argument("--margin", type=float, default=0.1, help="Margin in inches")
    parser.add_argument("--spacing", type=float, default=0.1, help="Spacing in inches")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    specs = load_specs(args.specs)
    if args.country not in specs:
        raise SystemExit(f"Unknown country '{args.country}'. Available: {', '.join(specs)}")
    spec = specs[args.country]

    image_bgr = cv2.imread(str(args.input))
    if image_bgr is None:
        raise SystemExit("Could not read input image.")

    if args.replace_bg:
        image_bgr = replace_background(image_bgr, spec.background_rgb)

    bbox, eye_point = detect_face(image_bgr)
    cropped_bgr = crop_to_spec(image_bgr, bbox, eye_point, spec, args.dpi)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
    photo = Image.fromarray(cropped_rgb)

    photo_path = output_dir / f"{args.country.lower()}_photo.jpg"
    photo.save(photo_path, quality=95)

    sheet = build_print_sheet(
        photo=photo,
        layout=args.layout,
        dpi=args.dpi,
        margin_in=args.margin,
        spacing_in=args.spacing,
        copies=args.copies,
    )
    sheet_path = output_dir / f"{args.country.lower()}_sheet_{int(args.layout.width_in)}x{int(args.layout.height_in)}.jpg"
    sheet.save(sheet_path, quality=95)

    print(f"Saved cropped photo: {photo_path}")
    print(f"Saved print sheet: {sheet_path}")


if __name__ == "__main__":
    main()
