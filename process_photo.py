#!/usr/bin/env python3
"""Process ID photos with auto-crop, background replacement, and print layout."""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

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

_selfie_segmenter = None


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


def _foreground_mask_hsv(image_bgr: np.ndarray) -> np.ndarray:
    """Fallback foreground mask using simple color-based segmentation."""
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
    
    return (mask > 128).astype(np.uint8) * 255


def _border_stats(image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    h, w = image_bgr.shape[:2]
    border = np.concatenate(
        [
            image_bgr[0:5, :, :].reshape(-1, 3),
            image_bgr[h - 5 : h, :, :].reshape(-1, 3),
            image_bgr[:, 0:5, :].reshape(-1, 3),
            image_bgr[:, w - 5 : w, :].reshape(-1, 3),
        ],
        axis=0,
    )
    mean = np.mean(border, axis=0)
    std = np.std(border, axis=0)
    return mean, std


def _white_key_mask(image_bgr: np.ndarray, bg_tolerance: float) -> Optional[np.ndarray]:
    mean, std = _border_stats(image_bgr)
    if float(np.mean(mean)) < (180 - max(0.0, bg_tolerance - 25.0)) or float(np.mean(std)) > 40:
        return None
    diff = np.linalg.norm(image_bgr.astype(np.float32) - mean.astype(np.float32), axis=2)
    bg = diff < max(10.0, bg_tolerance)
    fg_mask = (~bg).astype(np.uint8) * 255
    fg_mask = cv2.medianBlur(fg_mask, 5)
    return fg_mask


def _white_bg_heuristic(image_bgr: np.ndarray, bg_tolerance: float) -> np.ndarray:
    """Aggressive white-background keying using HSV thresholds."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # Background if bright and low saturation
    v_thresh = int(max(180, 255 - bg_tolerance * 1.5))
    s_thresh = int(min(60, max(20, bg_tolerance)))
    bg = (v > v_thresh) & (s < s_thresh)
    fg_mask = (~bg).astype(np.uint8) * 255
    fg_mask = cv2.medianBlur(fg_mask, 5)
    return fg_mask


def _border_color_key_mask(image_bgr: np.ndarray, bg_tolerance: float) -> Optional[np.ndarray]:
    """Key out a uniform background color by keeping only border-connected regions."""
    mean, std = _border_stats(image_bgr)
    mean_std = float(np.mean(std))
    # Only use when the border looks reasonably uniform.
    if mean_std > 45:
        return None

    diff = np.linalg.norm(image_bgr.astype(np.float32) - mean.astype(np.float32), axis=2)
    thresh = max(10.0, bg_tolerance) + 1.5 * mean_std
    bg_candidate = (diff < thresh).astype(np.uint8) * 255

    # Keep only background regions connected to the border.
    num_labels, labels = cv2.connectedComponents(bg_candidate)
    if num_labels <= 1:
        return None

    border_labels = set()
    h, w = labels.shape
    border_labels.update(np.unique(labels[0, :]).tolist())
    border_labels.update(np.unique(labels[h - 1, :]).tolist())
    border_labels.update(np.unique(labels[:, 0]).tolist())
    border_labels.update(np.unique(labels[:, w - 1]).tolist())
    border_labels.discard(0)

    if not border_labels:
        return None

    bg_mask = np.isin(labels, list(border_labels))
    fg_mask = (~bg_mask).astype(np.uint8) * 255
    fg_mask = cv2.medianBlur(fg_mask, 5)
    return fg_mask


def _get_selfie_segmenter():
    global _selfie_segmenter
    if _selfie_segmenter is None and mp is not None:
        if not hasattr(mp, "solutions"):
            return None
        _selfie_segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    return _selfie_segmenter


def get_foreground_mask(
    image_bgr: np.ndarray,
    threshold: float = 0.5,
    face_bbox: Optional[Tuple[int, int, int, int]] = None,
    bbox_expand_x: float = 0.4,
    bbox_expand_y: float = 0.6,
    prefer_white_key: bool = False,
    bg_tolerance: float = 25.0,
    face_protect: float = 0.4,
) -> np.ndarray:
    """Return a foreground mask (uint8 0/255) using the most reliable method available."""
    border_key = _border_color_key_mask(image_bgr, bg_tolerance=bg_tolerance)
    if border_key is not None:
        return border_key

    white_key = _white_key_mask(image_bgr, bg_tolerance=bg_tolerance)
    if white_key is not None:
        return white_key
    if prefer_white_key:
        return _white_bg_heuristic(image_bgr, bg_tolerance=bg_tolerance)

    segmenter = _get_selfie_segmenter()
    if segmenter is not None:
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        result = segmenter.process(image_rgb)
        if result.segmentation_mask is not None:
            mask = result.segmentation_mask
            # Smooth edges for cleaner composites
            mask = cv2.GaussianBlur(mask, (7, 7), 0)
            mask = (mask > threshold).astype(np.uint8) * 255
            mask = cv2.medianBlur(mask, 5)

            # If mask is almost all foreground or background, treat as failure.
            fg_ratio = float(np.mean(mask > 0))
            if 0.02 < fg_ratio < 0.98:
                return mask

    if face_bbox is not None:
        try:
            x, y, w, h = face_bbox
            h_img, w_img = image_bgr.shape[:2]
            # Expand bbox to include hair/shoulders
            pad_x = int(w * bbox_expand_x)
            pad_y = int(h * bbox_expand_y)
            x0 = max(0, x - pad_x)
            y0 = max(0, y - pad_y)
            x1 = min(w_img - 1, x + w + pad_x)
            y1 = min(h_img - 1, y + h + pad_y)

            mask = np.full(image_bgr.shape[:2], cv2.GC_BGD, dtype=np.uint8)
            mask[y0:y1, x0:x1] = cv2.GC_PR_FGD
            # Mark central face as sure foreground
            cx0 = max(0, x + int(w * 0.2))
            cy0 = max(0, y + int(h * 0.2))
            cx1 = min(w_img - 1, x + int(w * 0.8))
            cy1 = min(h_img - 1, y + int(h * 0.8))
            mask[cy0:cy1, cx0:cx1] = cv2.GC_FGD

            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            cv2.grabCut(image_bgr, mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)

            fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
            fg_mask = cv2.medianBlur(fg_mask, 5)

            # If the face region isn't mostly foreground, the mask likely inverted.
            face_region = fg_mask[cy0:cy1, cx0:cx1]
            if face_region.size > 0 and (np.mean(face_region) < 128):
                fg_mask = cv2.bitwise_not(fg_mask)

            # Force face + nearby area to foreground to avoid "cutting into" subject.
            fg_mask[y0:y1, x0:x1] = 255
            fg_mask = cv2.dilate(fg_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=1)
            return fg_mask
        except Exception:
            pass

    if face_bbox is not None:
        x, y, w, h = face_bbox
        h_img, w_img = image_bgr.shape[:2]
        pad_x = int(w * max(0.1, bbox_expand_x))
        pad_y = int(h * max(0.2, bbox_expand_y))
        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y)
        x1 = min(w_img - 1, x + w + pad_x)
        y1 = min(h_img - 1, y + h + pad_y)
        fg_mask = np.zeros((h_img, w_img), dtype=np.uint8)
        fg_mask[y0:y1, x0:x1] = 255
        return fg_mask

    return _foreground_mask_hsv(image_bgr)


def replace_background(
    image_bgr: np.ndarray,
    background_rgb: Tuple[int, int, int],
    threshold: float = 0.5,
    face_bbox: Optional[Tuple[int, int, int, int]] = None,
    bbox_expand_x: float = 0.4,
    bbox_expand_y: float = 0.6,
    bg_tolerance: float = 25.0,
    face_protect: float = 0.4,
) -> np.ndarray:
    """Replace background using the best available foreground mask."""
    fg_mask = get_foreground_mask(
        image_bgr,
        threshold=threshold,
        face_bbox=face_bbox,
        bbox_expand_x=bbox_expand_x,
        bbox_expand_y=bbox_expand_y,
        prefer_white_key=True,
        bg_tolerance=bg_tolerance,
        face_protect=face_protect,
    )
    # If the mask is almost all-foreground, fall back to white-key.
    if float(np.mean(fg_mask > 0)) > 0.98:
        white_key = _white_key_mask(image_bgr, bg_tolerance=bg_tolerance)
        if white_key is not None:
            fg_mask = white_key

    # Hard-protect only the core face ellipse to avoid erosion without swallowing background.
    if face_bbox is not None:
        x, y, w, h = face_bbox
        cx = x + w // 2
        cy = y + h // 2
        axes = (int(w * face_protect), int(h * (face_protect + 0.15)))
        face_core = np.zeros_like(fg_mask)
        cv2.ellipse(face_core, (cx, cy), axes, 0, 0, 360, 255, -1)
        fg_mask = cv2.bitwise_or(fg_mask, face_core)
    background = np.full_like(image_bgr, background_rgb[::-1])  # RGB to BGR

    # Feather edges for a more natural composite.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
    alpha = cv2.GaussianBlur(fg_mask, (11, 11), 0).astype(np.float32) / 255.0
    alpha = alpha[:, :, None]
    composite = image_bgr.astype(np.float32) * alpha + background.astype(np.float32) * (1.0 - alpha)
    return composite.astype(np.uint8)


def compute_output_size_px(spec: PhotoSpec, dpi: int) -> Tuple[int, int]:
    return int(round(spec.width_in * dpi)), int(round(spec.height_in * dpi))


def crop_to_spec(
    image_bgr: np.ndarray,
    bbox: Tuple[int, int, int, int],
    eye_point: Tuple[int, int],
    spec: PhotoSpec,
    dpi: int,
    background_rgb: Optional[Tuple[int, int, int]] = None,
) -> np.ndarray:
    """Crop and resize to spec while maintaining aspect ratio (no face distortion)."""
    out_w, out_h = compute_output_size_px(spec, dpi)
    x_min, y_min, box_w, box_h = bbox

    target_head_height = spec.head_height_ratio * out_h
    scale = target_head_height / max(box_h, 1)

    # Scale uniformly to preserve aspect ratio
    resized = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    eye_x, eye_y = eye_point
    eye_x = int(round(eye_x * scale))
    eye_y = int(round(eye_y * scale))

    target_eye_y = int(round(out_h * (1 - spec.eye_line_from_bottom_ratio)))

    left = int(round(eye_x - out_w / 2))
    top = int(round(eye_y - target_eye_y))

    # Crop with padding - maintains aspect ratio
    pad_rgb = background_rgb if background_rgb is not None else spec.background_rgb
    cropped = crop_with_padding(resized, left, top, out_w, out_h, pad_rgb)
    
    # Final resize to exact dimensions if needed (minimal distortion since we've already positioned correctly)
    # Only resize if aspect ratio is significantly different
    h, w = cropped.shape[:2]
    if abs(w/h - out_w/out_h) > 0.05:  # Only if aspect ratio differs by more than 5%
        # Use INTER_AREA for downsampling, INTER_CUBIC for upsampling
        interpolation = cv2.INTER_AREA if (w * h > out_w * out_h) else cv2.INTER_CUBIC
        cropped = cv2.resize(cropped, (out_w, out_h), interpolation=interpolation)
    
    return cropped


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
    draw_guides: bool = True,
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
    
    if draw_guides:
        # Create drawing context for guide lines
        from PIL import ImageDraw
        draw = ImageDraw.Draw(sheet)
        guide_color = (200, 200, 200)  # Light gray cutting guide lines
        guide_width = 1
        outline_color = (210, 210, 210)  # Very light gray photo outline for cutting edges
        outline_width = 1
    
    placed = 0
    for row in range(max_rows):
        for col in range(max_cols):
            if placed >= copies:
                break
            x = left_margin + col * (photo_w + spacing)
            y = top_margin + row * (photo_h + spacing)
            sheet.paste(photo, (x, y))
            
            if draw_guides:
                # Draw subtle outline around each photo for clear cutting edges
                draw.rectangle(
                    [(x, y), (x + photo_w - 1, y + photo_h - 1)],
                    outline=outline_color,
                    width=outline_width
                )
            
            placed += 1
        if placed >= copies:
            break

    if draw_guides:
        # Draw vertical guide lines between photos (for cutting guidance)
        for col in range(1, max_cols):
            x = left_margin + col * (photo_w + spacing) - spacing // 2
            draw.line([(x, top_margin), (x, top_margin + max_rows * photo_h + (max_rows - 1) * spacing)],
                      fill=guide_color, width=guide_width)

        # Draw horizontal guide lines between photos (for cutting guidance)
        for row in range(1, max_rows):
            y = top_margin + row * (photo_h + spacing) - spacing // 2
            draw.line([(left_margin, y), (left_margin + max_cols * photo_w + (max_cols - 1) * spacing, y)],
                      fill=guide_color, width=guide_width)
        
        # Draw corner markers at photo edges for precise cutting (tiny L-shaped corners at each photo's edges)
        corner_marker_color = (180, 180, 180)  # Slightly darker gray for visibility
        corner_size = 5
        
        for row in range(max_rows):
            for col in range(max_cols):
                if row * max_cols + col >= copies:
                    break
                x = left_margin + col * (photo_w + spacing)
                y = top_margin + row * (photo_h + spacing)
                
                # Draw small corner marks at the 4 corners of each photo
                # Top-left corner
                draw.line([(x, y), (x + corner_size, y)], fill=corner_marker_color, width=1)
                draw.line([(x, y), (x, y + corner_size)], fill=corner_marker_color, width=1)
                
                # Top-right corner
                draw.line([(x + photo_w - 1, y), (x + photo_w - 1 - corner_size, y)], fill=corner_marker_color, width=1)
                draw.line([(x + photo_w - 1, y), (x + photo_w - 1, y + corner_size)], fill=corner_marker_color, width=1)
                
                # Bottom-left corner
                draw.line([(x, y + photo_h - 1), (x + corner_size, y + photo_h - 1)], fill=corner_marker_color, width=1)
                draw.line([(x, y + photo_h - 1), (x, y + photo_h - 1 - corner_size)], fill=corner_marker_color, width=1)
                
                # Bottom-right corner
                draw.line([(x + photo_w - 1, y + photo_h - 1), (x + photo_w - 1 - corner_size, y + photo_h - 1)], fill=corner_marker_color, width=1)
                draw.line([(x + photo_w - 1, y + photo_h - 1), (x + photo_w - 1, y + photo_h - 1 - corner_size)], fill=corner_marker_color, width=1)

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

    bbox, eye_point = detect_face(image_bgr)

    if args.replace_bg:
        image_bgr = replace_background(image_bgr, spec.background_rgb, face_bbox=bbox)
    cropped_bgr = crop_to_spec(
        image_bgr,
        bbox,
        eye_point,
        spec,
        args.dpi,
        background_rgb=spec.background_rgb,
    )

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
