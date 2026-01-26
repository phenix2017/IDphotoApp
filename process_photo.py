#!/usr/bin/env python3
"""Process ID photos with auto-crop, background replacement, and print layout."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

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


def create_demo_image() -> Tuple[np.ndarray, Tuple[int, int, int, int], Tuple[int, int]]:
    width, height = 1200, 1600
    image = Image.new("RGB", (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(image)

    face_left = width // 2 - 220
    face_top = height // 2 - 320
    face_right = width // 2 + 220
    face_bottom = height // 2 + 260
    draw.ellipse([face_left, face_top, face_right, face_bottom], fill=(220, 190, 170))

    eye_y = face_top + 200
    draw.ellipse([face_left + 110, eye_y, face_left + 160, eye_y + 50], fill=(50, 50, 50))
    draw.ellipse([face_right - 160, eye_y, face_right - 110, eye_y + 50], fill=(50, 50, 50))

    bbox = (face_left, face_top, face_right - face_left, face_bottom - face_top)
    eye_point = (width // 2, eye_y + 25)

    image_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    return image_bgr, bbox, eye_point


def detect_face(image_bgr: np.ndarray) -> Tuple[Tuple[int, int, int, int], Tuple[int, int]]:
    if mp is None:
        raise SystemExit("mediapipe is required for face detection.")

    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.6) as detector:
        result = detector.process(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))

    if not result.detections:
        raise RuntimeError("No face detected. Please use a clearer, front-facing photo.")

    detection = result.detections[0]
    bbox = detection.location_data.relative_bounding_box
    height, width, _ = image_bgr.shape

    x_min = int(bbox.xmin * width)
    y_min = int(bbox.ymin * height)
    box_w = int(bbox.width * width)
    box_h = int(bbox.height * height)

    keypoints = detection.location_data.relative_keypoints
    left_eye = keypoints[0]
    right_eye = keypoints[1]
    eye_x = int(((left_eye.x + right_eye.x) / 2) * width)
    eye_y = int(((left_eye.y + right_eye.y) / 2) * height)

    return (x_min, y_min, box_w, box_h), (eye_x, eye_y)


def replace_background(image_bgr: np.ndarray, background_rgb: Tuple[int, int, int]) -> np.ndarray:
    if mp is None:
        raise SystemExit("mediapipe is required for background replacement.")

    mp_selfie = mp.solutions.selfie_segmentation
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    with mp_selfie.SelfieSegmentation(model_selection=1) as segmenter:
        result = segmenter.process(rgb)

    mask = result.segmentation_mask
    background = np.full_like(rgb, background_rgb, dtype=np.uint8)
    condition = mask[:, :, None] > 0.5
    composite = np.where(condition, rgb, background)
    return cv2.cvtColor(composite, cv2.COLOR_RGB2BGR)


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
    _, _, _, box_h = bbox

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
    margin_in: float,
    spacing_in: float,
    copies: int,
) -> Image.Image:
    sheet_w = int(round(layout.width_in * dpi))
    sheet_h = int(round(layout.height_in * dpi))
    margin = int(round(margin_in * dpi))
    spacing = int(round(spacing_in * dpi))

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    photo_w, photo_h = photo.size

    max_cols = max(1, (sheet_w - 2 * margin + spacing) // (photo_w + spacing))
    max_rows = max(1, (sheet_h - 2 * margin + spacing) // (photo_h + spacing))

    placed = 0
    for row in range(max_rows):
        for col in range(max_cols):
            if placed >= copies:
                return sheet
            x = margin + col * (photo_w + spacing)
            y = margin + row * (photo_h + spacing)
            sheet.paste(photo, (x, y))
            placed += 1

    return sheet


def parse_layout(value: str) -> LayoutSpec:
    try:
        width_str, height_str = value.lower().split("x")
        return LayoutSpec(width_in=float(width_str), height_in=float(height_str))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("layout must be like 4x6 or 6x6") from exc


def process_photo(
    image_bgr: np.ndarray,
    spec: PhotoSpec,
    dpi: int,
    layout: LayoutSpec,
    copies: int,
    margin: float,
    spacing: float,
    output_dir: Path,
    replace_bg: bool,
    demo_bbox: Optional[Tuple[int, int, int, int]] = None,
    demo_eye_point: Optional[Tuple[int, int]] = None,
    prefix: str = "photo",
) -> Tuple[Path, Path]:
    if replace_bg:
        image_bgr = replace_background(image_bgr, spec.background_rgb)

    if demo_bbox is None or demo_eye_point is None:
        bbox, eye_point = detect_face(image_bgr)
    else:
        bbox, eye_point = demo_bbox, demo_eye_point

    cropped_bgr = crop_to_spec(image_bgr, bbox, eye_point, spec, dpi)

    output_dir.mkdir(parents=True, exist_ok=True)

    cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
    photo = Image.fromarray(cropped_rgb)

    photo_path = output_dir / f"{prefix}_cropped.jpg"
    photo.save(photo_path, quality=95)

    sheet = build_print_sheet(
        photo=photo,
        layout=layout,
        dpi=dpi,
        margin_in=margin,
        spacing_in=spacing,
        copies=copies,
    )
    sheet_path = output_dir / f"{prefix}_sheet_{int(layout.width_in)}x{int(layout.height_in)}.jpg"
    sheet.save(sheet_path, quality=95)

    return photo_path, sheet_path


def run_gui() -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:
        raise SystemExit("tkinter is required for the GUI.") from exc

    specs = load_specs(Path("specs.json"))
    country_codes = list(specs.keys())

    root = tk.Tk()
    root.title("ID Photo Processor")

    input_path = tk.StringVar(value="")
    country = tk.StringVar(value=country_codes[0] if country_codes else "US")
    dpi_var = tk.IntVar(value=300)
    replace_bg = tk.BooleanVar(value=True)
    layout_var = tk.StringVar(value="4x6")
    copies_var = tk.IntVar(value=6)
    margin_var = tk.DoubleVar(value=0.1)
    spacing_var = tk.DoubleVar(value=0.1)
    use_demo = tk.BooleanVar(value=True)

    def browse_file() -> None:
        path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png")],
        )
        if path:
            input_path.set(path)
            use_demo.set(False)

    def handle_process() -> None:
        spec = specs.get(country.get())
        if spec is None:
            messagebox.showerror("Error", "Unknown country spec.")
            return

        if use_demo.get():
            image_bgr, bbox, eye_point = create_demo_image()
            prefix = "demo"
        else:
            path = input_path.get().strip()
            if not path:
                messagebox.showerror("Error", "Please select an input photo or use demo mode.")
                return
            image_bgr = cv2.imread(path)
            if image_bgr is None:
                messagebox.showerror("Error", "Could not read input image.")
                return
            bbox, eye_point = None, None
            prefix = Path(path).stem

        try:
            photo_path, sheet_path = process_photo(
                image_bgr=image_bgr,
                spec=spec,
                dpi=dpi_var.get(),
                layout=parse_layout(layout_var.get()),
                copies=copies_var.get(),
                margin=margin_var.get(),
                spacing=spacing_var.get(),
                output_dir=Path("output"),
                replace_bg=replace_bg.get(),
                demo_bbox=bbox,
                demo_eye_point=eye_point,
                prefix=prefix,
            )
        except Exception as exc:  # noqa: BLE001 - show message to user
            messagebox.showerror("Processing Error", str(exc))
            return

        messagebox.showinfo(
            "Done",
            f"Saved cropped photo:\n{photo_path}\n\nSaved print sheet:\n{sheet_path}",
        )

    frame = ttk.Frame(root, padding=12)
    frame.grid(row=0, column=0, sticky="nsew")

    ttk.Label(frame, text="Input Photo").grid(row=0, column=0, sticky="w")
    ttk.Entry(frame, textvariable=input_path, width=45).grid(row=0, column=1, sticky="ew")
    ttk.Button(frame, text="Browse", command=browse_file).grid(row=0, column=2, padx=4)

    ttk.Checkbutton(frame, text="Use demo image", variable=use_demo).grid(row=1, column=1, sticky="w")

    ttk.Label(frame, text="Country").grid(row=2, column=0, sticky="w")
    ttk.OptionMenu(frame, country, country.get(), *country_codes).grid(row=2, column=1, sticky="w")

    ttk.Label(frame, text="DPI").grid(row=3, column=0, sticky="w")
    ttk.Entry(frame, textvariable=dpi_var, width=10).grid(row=3, column=1, sticky="w")

    ttk.Checkbutton(frame, text="Replace background", variable=replace_bg).grid(row=4, column=1, sticky="w")

    ttk.Label(frame, text="Layout").grid(row=5, column=0, sticky="w")
    ttk.Entry(frame, textvariable=layout_var, width=10).grid(row=5, column=1, sticky="w")

    ttk.Label(frame, text="Copies").grid(row=6, column=0, sticky="w")
    ttk.Entry(frame, textvariable=copies_var, width=10).grid(row=6, column=1, sticky="w")

    ttk.Label(frame, text="Margin (in)").grid(row=7, column=0, sticky="w")
    ttk.Entry(frame, textvariable=margin_var, width=10).grid(row=7, column=1, sticky="w")

    ttk.Label(frame, text="Spacing (in)").grid(row=8, column=0, sticky="w")
    ttk.Entry(frame, textvariable=spacing_var, width=10).grid(row=8, column=1, sticky="w")

    ttk.Button(frame, text="Process", command=handle_process).grid(row=9, column=1, pady=8)

    frame.columnconfigure(1, weight=1)
    root.mainloop()


def main() -> None:
    if len(sys.argv) == 1:
        run_gui()
        return

    parser = argparse.ArgumentParser(description="Process ID photos for passport specs.")
    parser.add_argument("input", nargs="?", type=Path, help="Input photo path")
    parser.add_argument("--specs", type=Path, default=Path("specs.json"))
    parser.add_argument("--country", default="US", help="Country code from specs.json")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--replace-bg", action="store_true")
    parser.add_argument("--layout", type=parse_layout, default=parse_layout("4x6"))
    parser.add_argument("--copies", type=int, default=6)
    parser.add_argument("--margin", type=float, default=0.1, help="Margin in inches")
    parser.add_argument("--spacing", type=float, default=0.1, help="Spacing in inches")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--demo", action="store_true", help="Use a demo image instead of an input photo")
    args = parser.parse_args()

    specs = load_specs(args.specs)
    if args.country not in specs:
        raise SystemExit(f"Unknown country '{args.country}'. Available: {', '.join(specs)}")
    spec = specs[args.country]

    if args.demo or args.input is None:
        image_bgr, bbox, eye_point = create_demo_image()
        prefix = "demo"
    else:
        image_bgr = cv2.imread(str(args.input))
        if image_bgr is None:
            raise SystemExit("Could not read input image.")
        bbox, eye_point = None, None
        prefix = args.input.stem

    photo_path, sheet_path = process_photo(
        image_bgr=image_bgr,
        spec=spec,
        dpi=args.dpi,
        layout=args.layout,
        copies=args.copies,
        margin=args.margin,
        spacing=args.spacing,
        output_dir=args.output_dir,
        replace_bg=args.replace_bg,
        demo_bbox=bbox,
        demo_eye_point=eye_point,
        prefix=prefix,
    )

    print(f"Saved cropped photo: {photo_path}")
    print(f"Saved print sheet: {sheet_path}")


if __name__ == "__main__":
    main()
