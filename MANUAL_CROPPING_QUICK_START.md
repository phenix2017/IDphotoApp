# Manual Cropping Feature - Quick Start

## What's New?

Your ID Photo Processor now includes an advanced **Manual Cropping** feature that lets you precisely adjust the crop area around your photo to ensure perfect head-to-shoulder framing.

## Key Features Added

✅ **Two Processing Modes**
- Automatic: AI detects and crops automatically
- Manual Adjustment: You control the crop boundaries with sliders

✅ **Visual Profile Guide**
- Shows required head-to-shoulder framing
- Country-specific standards (US, CA, UK)
- Best practices for lighting and pose

✅ **Interactive Crop Adjustment**
- 4 independent sliders (Top, Bottom, Left, Right %)
- Live preview with green crop box overlay
- Crosshair and corner markers for precision

✅ **Detailed Instructions**
- Visual examples of correct vs incorrect profiles
- Common mistakes to avoid
- Real-time feedback on crop dimensions

## How to Use

### Step 1: Launch the App
```bash
cd c:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp
streamlit run streamlit_app.py
```
Or double-click `run_gui.bat`

### Step 2: Upload a Photo
- Click the upload box and select your image
- Or drag and drop a JPEG/PNG file

### Step 3: Choose Manual Adjustment Mode
- In "Processing Mode", select **Manual Adjustment**
- The manual cropping interface will appear

### Step 4: Adjust the Crop Area
Use the four sliders to position the green box around the head and shoulders:

**Top %** (0-50%)
- Lower value = include more forehead
- Higher value = crop closer to head top
- Start: ~20-25%

**Bottom %** (50-100%)
- Lower value = less shoulders/body
- Higher value = more shoulders/body
- Start: ~75-85%
- Must be at least 30% above Top %

**Left %** (0-40%)
- Lower value = include more of left side
- Higher value = crop tighter on left
- Start: ~15%

**Right %** (60-100%)
- Lower value = crop tighter on right
- Higher value = include more of right side
- Start: ~85%
- Must be at least 40% above Left %

### Step 5: Review Live Preview
- **Left panel**: Original image with green crop box
- **Right panel**: Final ID photo that will be downloaded
- Adjust sliders until satisfied with framing

### Step 6: Download Results
- **📥 Download Photo**: The cropped and resized ID photo
- **📥 Download Sheet**: Print layout with multiple copies

## Visual Guide Included

Click on the tabs to see:

**Instructions Tab**
- ✓ Correct framing guidelines
- ✗ Common mistakes to avoid
- Country-specific requirements

**Visual Guide Tab**
- Example of good head-to-shoulder profile
- Examples of common issues and how they look

## Example Adjustments

### Face Too High?
→ Increase Top % slider

### Face Too Low?
→ Decrease Top % slider

### Too Much Forehead?
→ Increase Top %

### Shoulders Cut Off?
→ Decrease Bottom %

### Uneven Sides?
→ Adjust Left % and Right % to match

## Tips for Best Results

1. **Start with defaults** (~20-85% vertical, 15-85% horizontal)
2. **Make small adjustments** (1-2% at a time)
3. **Keep face centered** in the crop box
4. **Watch both preview panels** to see the final result
5. **Remember**: The sliders work with percentages of the image dimensions

## When to Use Manual Mode

- Automatic mode didn't frame it quite right
- You want pixel-perfect control
- Photo has unusual framing
- You want to emphasize certain features
- Testing different crop positions

## When to Use Automatic Mode

- Photo is clear and well-lit
- Face is frontal and properly positioned
- You trust AI detection
- Quick processing is needed
- You're not sure where to start

## Download Formats

### Cropped Photo
- Country-specific size (e.g., 2"×2" for US)
- 300 DPI (or your chosen DPI)
- JPEG format, 95% quality
- Ready for printing or digital submission

### Print Sheet
- 4×6" or 6×6" layout (configurable)
- Multiple copies (1-20 photos per sheet)
- Ready to print directly
- Perfect for bulk printing

## Visual Example

```
Original Image with Crop Box (Green):
┌──────────────────────────────────┐
│    ┌──────────────────┐           │
│    │ ┌─ HEAD START ─┐ │           │
│    │ │               │ │           │
│    │ │  [FACE HERE]  │ │           │
│    │ │               │ │           │
│    │ │ SHOULDERS ─┐  │ │           │
│    └─┴───────────── ┴─┘           │
│       Crop region shown in green  │
└──────────────────────────────────┘

                ↓

Final ID Photo (Cropped & Resized):
┌─────────────┐
│  ┌───────┐  │
│  │  HEAD │  │
│  │       │  │
│  │ FACE  │  │
│  │       │  │
│  │SHOULD.│  │
│  └───────┘  │
└─────────────┘
```

## Specifications Reference

**United States (US)**
- Photo Size: 2" × 2"
- Head Height: 50% of photo
- Eyes Position: 56% from bottom

**Canada (CA)**
- Photo Size: 50mm × 70mm (1.97" × 2.76")
- Head Height: 55% of photo
- Eyes Position: 60% from bottom

**United Kingdom (UK)**
- Photo Size: 35mm × 45mm (1.38" × 1.77")
- Head Height: 54% of photo
- Eyes Position: 58% from bottom

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Green crop box not visible | Try adjusting Bottom % slider |
| Preview not updating | Check that Top % < Bottom % and Left % < Right % |
| Crop area seems wrong | Review instructions tab for correct framing |
| Photo doesn't download | Ensure you have space on disk, check browser settings |
| Sliders feel unresponsive | Make sure all slider values are in valid range |

## Files Updated

- **streamlit_app.py** - Main app with manual cropping feature
- **MANUAL_CROPPING_GUIDE.md** - Comprehensive documentation
- **QUICK_START.txt** - This file

## Further Reading

For detailed documentation, see [MANUAL_CROPPING_GUIDE.md](MANUAL_CROPPING_GUIDE.md)

For general app information, see [README_GUI.md](README_GUI.md)

## Next Steps

1. **Try it out**: Launch the app and test with a photo
2. **Compare modes**: Try both Automatic and Manual Adjustment
3. **Refine your workflow**: Find the best crop settings for your photos
4. **Batch process**: Process multiple photos with consistent settings
5. **Print**: Download sheets and print your ID photos

---

**Version**: 1.1 with Manual Cropping Feature
**Last Updated**: January 2025
**Status**: Production Ready ✅

Need help? Check the app's built-in Help section or review the MANUAL_CROPPING_GUIDE.md file.
