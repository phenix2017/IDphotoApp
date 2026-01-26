# IDphotoApp Copilot Instructions

## Project Purpose
Auto-crop and process identity photos for passport/ID compliance across multiple countries, with background replacement and print sheet layout generation.

## Architecture & Data Flow

### Core Pipeline (in `process_photo.py`)
1. **Face Detection** → Mediapipe extracts bounding box + eye landmarks
2. **Scaling** → Resize to match country's `head_height_ratio` spec
3. **Crop + Center** → Position eyes to match `eye_line_from_bottom_ratio`
4. **Padding** → Fill edges with background color if crop extends beyond image
5. **Background Replace** (optional) → Mediapipe selfie segmentation replaces background
6. **Print Layout** → Grid arrangement on 4x6 or 6x6 sheets at 300 DPI

### Key Data Structures
- **PhotoSpec** (dataclass): `width_in/height_in`, `head_height_ratio`, `eye_line_from_bottom_ratio`, `background_rgb`
  - Loaded from `specs.json` keyed by country code (US, CA, UK)
  - Supports both inches and mm (converted via `/25.4`)
- **LayoutSpec**: Sheet dimensions in inches (e.g., 4x6 or 6x6)

## Critical Functions & Workflows

### `detect_face()` 
- Uses Mediapipe FaceDetection (model_selection=1 for efficiency)
- Returns bounding box `(x_min, y_min, width, height)` and eye center `(x, y)` in pixels
- **Error handling**: Raises if no face or Mediapipe missing
- Eye coordinates are averaged from left/right eye keypoints (indices 0, 1)

### `crop_to_spec()`
- **Algorithm**: Scale face to match spec → position eyes at target y-line → crop canvas
- Coordinates must be recalculated after resize (scale factor applied)
- Target eye Y = `out_h * (1 - eye_line_from_bottom_ratio)` (inverted because image coords start at top)

### `crop_with_padding()`
- Handles partial-image crops gracefully with `cv2.copyMakeBorder`
- Padding added before cropping; crop window adjusted to new coordinates
- Order matters: pad first, then slice adjusted region

### `replace_background()`
- Mediapipe selfie segmentation outputs mask where `mask > 0.5` = foreground
- NumPy vectorized: `np.where(condition, rgb, background)` for efficiency
- Convert BGR ↔ RGB at function boundaries

## Command-Line Interface
```bash
python process_photo.py <input.jpg> --country US [--replace-bg] [--dpi 300] [--layout 4x6] [--copies 6]
```
- `--country` is required; must match key in `specs.json`
- Default layout: 4x6 inches; parsed via `parse_layout()` (lowercase, validates format)
- Output files: `output/{country}_photo.jpg`, `output/{country}_sheet_4x6.jpg`

## Development Patterns

### Module Imports
- **OpenCV** (`cv2`): Lazy error handling if missing (runtime check)
- **Mediapipe** (`mp`): Optional import; raises `SystemExit` if used without package
- Prefer `pathlib.Path` over string paths for file I/O

### DPI Conversions
- Always convert inches to pixels: `int(round(inches * dpi))`
- Used for output size, margins, spacing in print layout
- Default: 300 DPI (photo print standard)

### Error Messages
- Use `SystemExit()` for fatal errors (missing dependencies, no face detected, invalid specs)
- Prefix output with "Unknown country" or "Could not read" for clarity

### Type Hints
- All functions annotated with input/output types
- Use `Tuple[int, int, int, int]` for bounding boxes, `Dict[str, PhotoSpec]` for spec lookups

## Common Extension Points

1. **Add country specs**: Add entry to `specs.json` with required fields
2. **Change background strategy**: Modify `replace_background()` to use different segmentation model or chroma-key
3. **Custom print layouts**: Extend `LayoutSpec` or add sheet template generator
4. **CLI preset profiles**: Add argument group for common workflows (e.g., `--preset passport-set`)

## Testing & Validation
- Face detection reliability depends on photo clarity and frontal pose
- Test with varied lighting, skin tones, and head angles
- Print quality targets: 300 DPI minimum, 95% JPEG quality
- Validate specs against official country requirements (head height, eye placement tolerance)

## Dependencies
- OpenCV 4.8+: Image processing (resize, border, read/write)
- Mediapipe 0.10+: Face detection, selfie segmentation
- Pillow 10.0+: Print layout composition
- NumPy 1.24+: Vectorized array operations
