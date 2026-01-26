# Manual Cropping Feature Guide

## Overview

The Manual Cropping feature allows you to precisely adjust the crop area around your photo to ensure perfect head-to-shoulder framing according to ID photo standards. This is useful when automatic face detection doesn't capture the exact framing you need.

## Key Features

### 1. **Visual Profile Requirements** (Expandable Section at Top)
- Displays the required head-to-shoulder profile
- Shows country-specific standards (US, CA, UK)
- Includes best practices for lighting, background, and pose

### 2. **Processing Mode Selection**
Choose between two modes:
- **Automatic**: AI detects face and crops automatically
- **Manual Adjustment**: You control the crop boundaries with sliders

### 3. **Instruction Tabs**
- **Instructions Tab**: Shows correct framing guidelines and common mistakes
- **Visual Guide Tab**: Visual examples of good and bad profiles

### 4. **Crop Boundary Sliders**
Four independent sliders control the crop area:
- **Top %**: Where the crop starts from the top of the image (0-50%)
- **Bottom %**: Where the crop ends from the top (depends on Top %)
- **Left %**: Where the crop starts from the left (0-40%)
- **Right %**: Where the crop ends from the left (depends on Left %)

### 5. **Live Preview**
Two-column preview showing:
- **Left**: Original image with green crop box overlay (shows what will be cropped)
- **Right**: Final ID photo result at target dimensions and DPI

## How to Use Manual Cropping

### Step 1: Upload Photo
1. Open the app at `http://localhost:8501`
2. Upload a clear, front-facing photo using the file uploader

### Step 2: Select Manual Adjustment Mode
1. In the "Processing Mode" section, choose **Manual Adjustment**
2. The manual cropping interface will appear

### Step 3: Review Requirements
1. Click on the **Instructions** tab to see guidelines
2. Review the **Visual Guide** tab for examples of correct vs incorrect framing

### Step 4: Adjust Crop Boundaries
1. **Top % slider**: Start with ~20-25%
   - Move left to include more forehead
   - Move right to crop closer to head top
   
2. **Bottom % slider**: Start with ~75-85%
   - Should be at least 30% above the Top % slider
   - Move right to include more shoulders/body
   - Move left to crop tighter

3. **Left % slider**: Start with ~15%
   - Move left to include more of left ear/side
   - Move right to crop tighter on left

4. **Right % slider**: Start with ~85%
   - Should be at least 40% above the Left % slider
   - Move right to include more of right ear/side
   - Move left to crop tighter

### Step 5: Fine-Tune Using Live Preview
1. Watch the **Left panel** (original with green box) to see the crop area
2. Watch the **Right panel** (final photo) to see the result
3. Adjust sliders until:
   - Green box shows head properly centered
   - Eyes are roughly in middle of frame
   - Shoulders visible at bottom
   - Ears visible on sides
   - Equal spacing on all sides

### Step 6: Download Results
1. Once satisfied with the crop:
   - **Download Photo**: The cropped and resized ID photo
   - **Download Sheet**: Print layout with multiple copies

## Visual Guides Included in App

### Good Profile (✓)
- Top: ~10-15% space above head
- Eyes: Center of frame horizontally and vertically
- Shoulders: Visible at bottom, natural width
- Expression: Neutral, looking at camera

### Common Mistakes (✗)
- ❌ Too much forehead (top % too low)
- ❌ Head cut off (top % too high)
- ❌ Tilted head (would need rotation - not in scope)
- ❌ Shoulders cut off (bottom % too low)
- ❌ Too much upper body (bottom % too high)
- ❌ Uneven side framing (left/right % don't match properly)

## Understanding the Percentages

The sliders use **percentage-based positioning** relative to image dimensions:

```
0% ─────────────────────────── 100%
│   Image Width or Height        │
```

### Top & Bottom Example
- **Top 20%**: Crop starts at 20% down from the image top
- **Bottom 80%**: Crop ends at 80% down from the image top
- **Actual crop height**: 80% - 20% = 60% of image height

### Left & Right Example
- **Left 15%**: Crop starts at 15% from the left
- **Right 85%**: Crop ends at 85% from the left
- **Actual crop width**: 85% - 15% = 70% of image width

## Tips for Best Results

### Image Quality
- Use high-resolution photos (1920×1080 minimum recommended)
- Clear, sharp focus on face
- Even, bright lighting

### Framing
1. Start with default values (~20-85% vertical, 15-85% horizontal)
2. Make small adjustments (1-2% at a time)
3. Focus on keeping the face centered in the crop box

### Common Adjustments
- **Face too high**: Increase Top % slightly
- **Face too low**: Decrease Top % slightly
- **Face too far left**: Increase Left % slightly
- **Face too far right**: Decrease Right % slightly
- **Too much forehead**: Increase Top %
- **Shoulders cut off**: Decrease Bottom %

## Automatic vs Manual Mode

### Use Automatic When:
- Photo is clear and well-lit
- Face is frontal and properly positioned
- You trust AI detection
- Quick processing is needed

### Use Manual When:
- Automatic detection isn't quite right
- You need pixel-perfect control
- Photo has unusual framing
- Background is complex
- You want to emphasize certain features

## Download Options

After cropping, you get:

1. **Cropped Photo**
   - Size: Country-specific (e.g., 2"×2" for US)
   - Resolution: Your chosen DPI (default 300 DPI)
   - Format: JPEG, 95% quality
   - Use for: Printing or digital submissions

2. **Print Sheet**
   - Layout: 4×6" or 6×6" (configurable)
   - Copies: 1-20 photos per sheet
   - Resolution: Your chosen DPI
   - Format: JPEG, ready to print
   - Use for: Bulk printing multiple ID photos

## Keyboard Shortcuts

While using sliders:
- **Arrow keys**: Fine-tune by 1%
- **Shift + Arrow keys**: Adjust by 5%
- **Enter**: Update preview

## Troubleshooting

### Preview Not Updating
- Ensure all sliders are moved (may need to adjust slightly)
- Check that Top % < Bottom % and Left % < Right %

### Crop Area Not Visible in Original
- Sliders may be at default. Try adjusting Bottom % slider

### Downloaded Photo Looks Different
- Different monitor/screen sizes may display differently
- Print at 300 DPI for accurate representation
- Check print settings before printing

### Face Still Not Right
- Try automatic mode first to see AI suggestions
- Then switch to manual mode to fine-tune
- Consider re-photographing if face is severely tilted

## Specifications by Country

The app uses these specifications:

**United States (US)**
- Size: 2" × 2"
- Head height: 50% of photo height
- Eyes: 56% from bottom

**Canada (CA)**
- Size: 50mm × 70mm (1.97" × 2.76")
- Head height: 55% of photo height
- Eyes: 60% from bottom

**United Kingdom (UK)**
- Size: 35mm × 45mm (1.38" × 1.77")
- Head height: 54% of photo height
- Eyes: 58% from bottom

## Advanced Tips

### For Professional Results
1. Use consistent lighting across all photos
2. Set background color in settings for consistency
3. Batch process multiple photos using same settings
4. Export print sheets for bulk printing

### For Different Photo Styles
- **Headshots**: Use tighter framing (increase Left/Right %)
- **Full Face**: Use looser framing (decrease Left/Right %)
- **Formal**: Include shoulders prominently (decrease Bottom %)
- **Casual**: Emphasize face (increase Bottom % for less shoulders)

### Multi-Country Processing
1. Upload photo once
2. Process with automatic mode for each country
3. Compare results
4. Switch to manual mode if needed for refinement
5. Download sheets for each country

## Keyboard Controls in Streamlit

- **R key**: Rerun app
- **C key**: Clear cache
- **S key**: Open settings

## Support & Feedback

For issues or suggestions:
1. Check the app's built-in Help section (lower sidebar)
2. Review common mistakes in the Visual Guide
3. Try different preset countries first
4. Test with photos of known good quality

---

**Last Updated**: 2025-01-20
**App Version**: 1.1 (with Manual Cropping)
**Supported Countries**: US, CA, UK
