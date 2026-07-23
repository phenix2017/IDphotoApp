"""Application workflow orchestration for ID photo processing."""

from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageFile

from background_engine import selected_background_engine
from crop_engine import crop_to_spec
from process_photo import PhotoSpec, clean_card_photo, detect_face, get_foreground_alpha, replace_background
from print_sheet import LayoutSpec, build_front_back_sheet, build_print_sheet


@dataclass(frozen=True)
class PhotoProcessOptions:
    spec: PhotoSpec
    dpi: int
    replace_background_enabled: bool
    background_rgb: tuple[int, int, int]
    background_engine: str
    bg_tolerance: float
    face_protect: float
    enforce_target: bool = True


@dataclass(frozen=True)
class PhotoProcessResult:
    cropped_bgr: np.ndarray
    face_bbox: tuple[int, int, int, int]
    eye_point: tuple[int, int]
    cropped_face_bbox: tuple[int, int, int, int] | None


def encode_png_bytes(image_bgr: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image_bgr)
    if not ok:
        raise RuntimeError("Could not encode image.")
    return encoded.tobytes()


def _decode_with_pillow_fallback(file_bytes: bytes) -> np.ndarray | None:
    """Recover images OpenCV rejects but are otherwise readable, e.g. JPEGs missing
    their end-of-image marker from an interrupted save/transfer on the source device.
    """
    previous = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_image:
            pil_image.load()
            rgb = np.array(pil_image.convert("RGB"))
    except Exception:
        return None
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = previous
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def decode_image_bytes(file_bytes: bytes) -> np.ndarray:
    image_bgr = cv2.imdecode(np.frombuffer(file_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image_bgr is None:
        image_bgr = _decode_with_pillow_fallback(file_bytes)
    if image_bgr is None:
        raise ValueError(
            "We couldn't open that photo — it may have been saved incompletely or in an "
            f"unsupported format. Try re-saving or re-exporting it, then upload again. "
            f"({len(file_bytes):,} bytes received)"
        )
    return image_bgr


def process_id_photo(image_bgr: np.ndarray, options: PhotoProcessOptions) -> PhotoProcessResult:
    face_bbox, eye_point = detect_face(image_bgr)
    cropped_bgr = crop_to_spec(
        image_bgr,
        face_bbox,
        eye_point,
        options.spec,
        options.dpi,
        background_rgb=options.background_rgb,
        enforce_target=options.enforce_target,
    )

    cropped_face_bbox = None
    if options.replace_background_enabled:
        try:
            cropped_face_bbox, _ = detect_face(cropped_bgr)
        except Exception:
            cropped_face_bbox = None
        with selected_background_engine(options.background_engine):
            cropped_bgr = replace_background(
                cropped_bgr,
                options.background_rgb,
                face_bbox=cropped_face_bbox,
                bbox_expand_x=0.2,
                bbox_expand_y=0.3,
                bg_tolerance=options.bg_tolerance,
                face_protect=options.face_protect,
            )

    return PhotoProcessResult(
        cropped_bgr=cropped_bgr,
        face_bbox=face_bbox,
        eye_point=eye_point,
        cropped_face_bbox=cropped_face_bbox,
    )


def build_print_sheet_for_photo(
    photo: Image.Image,
    layout: LayoutSpec,
    dpi: int,
    margin_in: float,
    spacing_in: float,
    copies: int,
    draw_guides: bool,
) -> Image.Image:
    return build_print_sheet(
        photo,
        layout,
        dpi,
        margin_in=margin_in,
        spacing_in=spacing_in,
        copies=copies,
        draw_guides=draw_guides,
    )


def clean_id_card_photo(
    image_bgr: np.ndarray,
    background_rgb: tuple[int, int, int],
    background_engine: str,
    bg_tolerance: float,
) -> np.ndarray:
    with selected_background_engine(background_engine):
        return clean_card_photo(image_bgr, background_rgb, bg_tolerance=bg_tolerance)


def build_front_back_sheet_for_cards(
    front: Image.Image,
    back: Image.Image,
    layout: LayoutSpec,
    dpi: int,
    margin_in: float,
    spacing_in: float,
    draw_guides: bool,
) -> Image.Image:
    return build_front_back_sheet(
        front,
        back,
        layout,
        dpi,
        margin_in=margin_in,
        spacing_in=spacing_in,
        draw_guides=draw_guides,
    )


def foreground_alpha(
    image_bgr: np.ndarray,
    face_bbox: tuple[int, int, int, int] | None,
    background_engine: str,
    bg_tolerance: float,
    face_protect: float,
    prefer_white_key: bool = True,
) -> np.ndarray:
    with selected_background_engine(background_engine):
        return get_foreground_alpha(
            image_bgr,
            face_bbox=face_bbox,
            bbox_expand_x=0.2,
            bbox_expand_y=0.3,
            prefer_white_key=prefer_white_key,
            bg_tolerance=bg_tolerance,
            face_protect=face_protect,
        )
