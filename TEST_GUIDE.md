# IDphotoApp Manual Testing Guide

## Setup

A test image (`test_sample.jpg`) has been created automatically. You can also use your own photo.

## How to Run the Program

Open PowerShell and navigate to the project directory:

```powershell
cd C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp
```

Then use one of the commands below. Copy and paste directly!

---

## Test Commands (Copy & Paste Ready)

### 1. Basic US Passport Test
```powershell
python process_photo.py test_sample.jpg --country US
```

**Output:** 
- `output/us_photo.jpg` - Cropped 2x2" photo (600x600px at 300 DPI)
- `output/us_sheet_4x6.jpg` - Print sheet with 6 copies

---

### 2. Canada Passport with Custom Layout
```powershell
python process_photo.py test_sample.jpg --country CA --layout 4x6 --copies 4
```

**Output:**
- `output/ca_photo.jpg` - 50x70mm photo
- `output/ca_sheet_4x6.jpg` - Print sheet with 4 copies

---

### 3. UK Passport on 6x6 Sheet
```powershell
python process_photo.py test_sample.jpg --country UK --layout 6x6 --copies 2
```

**Output:**
- `output/uk_photo.jpg` - 35x45mm photo  
- `output/uk_sheet_6x6.jpg` - Square 6x6" layout with 2 copies

---

### 4. With Background Replacement
```powershell
python process_photo.py test_sample.jpg --country US --replace-bg
```

Uses simple color-based segmentation to create a white background.

---

### 5. Custom DPI & Spacing
```powershell
python process_photo.py test_sample.jpg --country US --dpi 200 --margin 0.2 --spacing 0.15 --copies 8
```

- `--dpi 200`: Print at 200 DPI (lower quality, smaller file)
- `--margin 0.2`: 0.2" margin around sheet edges
- `--spacing 0.15`: 0.15" space between photos
- `--copies 8`: Generate 8 copies on sheet

---

### 6. Full Control Example
```powershell
python process_photo.py test_sample.jpg --country CA --replace-bg --dpi 300 --layout 6x6 --copies 6 --margin 0.1 --spacing 0.1
```

---

## Using Your Own Photo

Replace `test_sample.jpg` with your own image:

```powershell
python process_photo.py "C:\Users\YourName\Pictures\my_photo.jpg" --country US
```

**Tips for best results:**
- ✓ Clear, well-lit photo
- ✓ Front-facing pose, neutral expression
- ✓ Full face visible (forehead to chin)
- ✓ Plain or uniform background
- ✓ JPEG or PNG format

---

## View Your Output

All files are saved to `output/` directory. Open them with:
- **Windows Photo Viewer**: Right-click → Open with → Photos
- **Paint**: For quick preview
- **Print preview**: Right-click → Print to check layout

---

## Help & Errors

### See all options:
```powershell
python process_photo.py --help
```

### Face not detected:
- Use a clearer, frontal photo
- Ensure good lighting
- Cascade classifier works better with real photos than synthetic images

### Invalid layout format:
- Must be `WxH` format like `4x6`, `5x7`, `6x6`
- No spaces, lowercase preferred

---

## Testing Checklist

After running each command, verify:
- [ ] No errors in PowerShell
- [ ] Output files created in `output/` directory
- [ ] Photos are the correct size  
- [ ] Print sheets have correct number of copies
- [ ] Layout looks good for printing

---

## Example Output Sizes

| Country | Spec | Photo Size @ 300 DPI |
|---------|------|----------------------|
| US | 2x2" | 600x600 px |
| CA | 50x70mm | 591x827 px |
| UK | 35x45mm | 413x531 px |

| Layout | Sheet Size @ 300 DPI |
|--------|----------------------|
| 4x6" | 1200x1800 px |
| 6x6" | 1800x1800 px |



