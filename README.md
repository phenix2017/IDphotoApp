# ID Photo Desktop Workflow Plan

This document outlines a practical desktop workflow and supporting architecture to: (1) take a compliant photo yourself, (2) auto-crop to head position/size for different countries, (3) replace/standardize background, and (4) lay out multiple copies on 4x6 or 6x6 prints for cheap printing.

## 1) Practical “Do-It-On-Your-Desktop” Plan

### Capture
- **Camera**: Use a phone or webcam in good light (window light or two soft lamps). Avoid shadows on the face or background.
- **Background**: Stand ~1m in front of a plain wall. A light gray or off-white wall is ideal.
- **Pose**: Neutral expression, mouth closed, eyes open, looking straight at the camera, shoulders squared.
- **Distance**: Frame from just above head to mid-chest to provide enough margin for cropping.

### Quick Desktop Workflow
1. **Take multiple shots** (5–10) and pick the sharpest.
2. **Run auto-crop** for the target country/spec (head size and eye-line position).
3. **Replace background** to uniform white/light gray per country requirements.
4. **Generate print sheet** (4x6 or 6x6) with multiple copies.
5. **Print at a photo kiosk** (Staples, Walgreens, etc.) on glossy or matte paper depending on requirements.

## 2) Architecture Overview

### Core Pipeline (per image)
1. **Input**: User photo
2. **Face detection + landmarks**
3. **Auto-crop** to country spec (head height, eye line position)
4. **Background replacement**
5. **Export** final photo + print sheet layout

### Key Components
- **Spec engine**: Country presets (size, head height % of photo, eye-line %). Example: US passport 2x2 in, head height 50–69% of photo height.
- **Face detection**: Detect face bounding box and landmarks (eyes, nose).
- **Cropper**: Adjust crop window to meet head-size and eye-line spec.
- **Background replace**: Semantic segmentation or chroma-based replacement to solid color.
- **Layout engine**: Arrange multiple copies on 4x6 or 6x6 sheet.

## 3) Country Spec Examples
- **US Passport**: 2x2 in (51x51 mm), head height 50–69% of image height, eye line 56–69% from bottom.
- **Canada Passport**: 50x70 mm, head size 31–36 mm (top of head to chin).
- **UK Passport**: 35x45 mm, head height 29–34 mm.

Store these specs in a JSON file for easy extension.

## 4) Auto-Crop Logic
1. Detect landmarks (eyes, chin).
2. Compute scale so head height matches spec.
3. Compute vertical placement so eye line matches spec.
4. Crop and pad to final size.

## 5) Background Replacement
- Use segmentation (e.g., Mediapipe Selfie Segmentation or OpenCV + DeepLab).
- Replace background with uniform RGB (e.g., #FFFFFF or #F5F5F5).

## 6) Print Sheet Layout
- 4x6 in sheet at 300 DPI = 1200x1800 px.
- 6x6 in sheet at 300 DPI = 1800x1800 px.
- Compute grid based on photo dimensions + margins.

## 7) Suggested Desktop Stack
- **Python**: OpenCV, Mediapipe, Pillow.
- **Optional UI**: Streamlit or Electron frontend.
- **Output**: JPEG for final photo, JPEG or PNG for print sheet.

---

## Next Steps
- Add a `specs.json` with country definitions.
- Implement a prototype script: `process_photo.py`.
- Add a CLI or minimal UI for user input and preview.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the processor:
   ```bash
   python process_photo.py path/to/photo.jpg --country US --replace-bg
   ```
3. Outputs are saved in `output/` as a cropped photo and a print sheet.

## GUI

Run the script without arguments to open a simple desktop UI with defaults pre-filled:

```bash
python process_photo.py
```

The GUI defaults to a built-in demo image so you can click **Process** without selecting a file. Uncheck **Use demo image** to choose your own photo.

## CLI Defaults

To test quickly without any input file, run:

```bash
python process_photo.py --demo
```
