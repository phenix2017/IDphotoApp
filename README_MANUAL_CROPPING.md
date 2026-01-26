# 🎬 Manual Cropping Feature - Complete Overview

## What You Now Have

A complete **ID Photo Processor with Manual Cropping** that allows pixel-perfect control over photo framing with visual guidance.

---

## 🚀 Getting Started (30 seconds)

### Start the App
```bash
cd c:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp
streamlit run streamlit_app.py
```

Or simply **double-click** `run_gui.bat`

### Then
1. Go to `http://localhost:8501` (opens automatically)
2. Upload a photo
3. Select "Manual Adjustment" mode
4. Adjust 4 sliders to frame head and shoulders
5. Download your results

---

## 🎯 Core Features

### 📐 Visual Profile Requirements
- **Expandable section** at the top of the app
- Shows what good ID photos look like
- Country-specific standards (US, CA, UK)
- Best practices for lighting and posing

### 🎛️ Four Adjustment Sliders
- **Top %**: Where to start the crop from the top (0-50%)
- **Bottom %**: Where to end the crop (must be 30%+ below Top)
- **Left %**: Where to start from the left (0-40%)
- **Right %**: Where to end the crop (must be 40%+ above Left)

### 👁️ Live Preview
- **Left side**: Original image with green crop box overlay
  - Shows exactly what will be cropped
  - Crosshair marks center
  - Corner markers for precision
- **Right side**: Final photo result
  - Shows exactly what you'll download
  - Country-specific dimensions
  - At selected DPI

### 📚 Instruction Tabs
- **Instructions Tab**: Correct framing guidelines & common mistakes
- **Visual Guide Tab**: Examples of good profiles & issues

### 🔄 Both Processing Modes
- **Automatic**: AI detects and crops (quick, no effort)
- **Manual Adjustment**: You control the crop (precise control)
- Switch between them anytime

---

## 📊 The Slider System Explained

### Understanding Percentages

Sliders use **percentage-based positioning** relative to your image:

```
Left Edge                          Right Edge
0%  ─────────────────────────────── 100%
    Image Width (for Left/Right sliders)

Top Edge
0%  
    ─────────────────────────────── 
    Image Height
                                    
Bottom Edge                        100%
```

### Default Starting Values

Based on your selected country:

| Setting | Value | What It Means |
|---------|-------|--------------|
| Top | ~20% | Crop starts 20% down from top |
| Bottom | ~80-85% | Crop ends 80-85% down from top |
| Left | ~15% | Crop starts 15% from left |
| Right | ~85% | Crop ends 85% from left |

### Examples

**Standard Portrait** (Most common)
- Top: 20%, Bottom: 80%, Left: 15%, Right: 85%
- Result: Head and shoulders in natural proportion

**Wide Framing** (Show more shoulders)
- Top: 10%, Bottom: 90%, Left: 10%, Right: 90%
- Result: More context around subject

**Tight Framing** (Emphasize face)
- Top: 25%, Bottom: 75%, Left: 20%, Right: 80%
- Result: Face fills more of the frame

---

## ✅ Step-by-Step Usage

### 1️⃣ Upload Your Photo
```
Click "Choose an image file" or drag & drop
Supported: JPG, JPEG, PNG
Recommended: 1920×1080+ resolution for best results
```

### 2️⃣ Select Country & Settings
```
Sidebar:
- Country: US, CA, or UK
- Replace Background: Optional
- DPI: 100-600 (default 300)
- Layout: 4×6" or 6×6"
- Copies: 1-20 per sheet
```

### 3️⃣ Choose Manual Adjustment Mode
```
Processing Mode:
[ ] Automatic
[●] Manual Adjustment
```

### 4️⃣ Review Instructions
```
Click "Instructions" tab to see:
- ✓ Correct framing guidelines
- ✗ Common mistakes to avoid
- Guidelines for your country

Click "Visual Guide" tab to see:
- Example of good profile
- Examples of bad framing
```

### 5️⃣ Adjust Crop Sliders
```
Move four sliders to position crop box:

Top % → Start point from top
    ← Adjust by 1-2% at a time
    
Bottom % → End point from top
    ← Must be 30%+ below Top
    
Left % → Start point from left
    ← Adjust by 1-2% at a time
    
Right % → End point from left
    ← Must be 40%+ right of Left
```

### 6️⃣ Watch Live Preview
```
Left Panel: Shows original image
    - Green box = crop region
    - Crosshair = center point
    - Size = dimensions in pixels & %

Right Panel: Shows final result
    - Your actual ID photo
    - At country spec size
    - At selected DPI
    - Ready to use
```

### 7️⃣ Fine-Tune As Needed
```
Adjust sliders until:
✓ Head fills frame naturally
✓ Eyes in middle of frame
✓ Shoulders visible at bottom
✓ Ears visible on sides
✓ Equal padding around subject
```

### 8️⃣ Download Results
```
Two options:

📥 Download Photo
   - The cropped ID photo
   - Country-specific size
   - 300 DPI (or your choice)
   - JPEG format, 95% quality
   - Single photo

📥 Download Sheet
   - Print layout
   - Multiple copies
   - Ready to print
   - Paper-sized (4×6" or 6×6")
   - 1-20 copies
```

---

## 🎓 Understanding the Visual Feedback

### Green Crop Box
```
┌─────────────────────────────────────┐
│  Original Photo                       │
│                                       │
│     ┌────────────────────┐            │ ← Green border
│     │  ╳  CROP REGION   │            │   shows what
│     │                    │            │   will be
│     │      (HEAD)        │            │   cropped
│     │                    │            │
│     │      (FACE)        │            │
│     │                    │            │
│     │    (SHOULDERS)     │            │
│     └────────────────────┘            │
│                                       │
└─────────────────────────────────────┘
```

### Crosshair & Corner Markers
```
             ╳ ← Crosshair at center
        ╭────X────╮
        │  (FACE) │
        ╰────X────╯
           └─┘ ← Corner markers for precision
```

### Crop Dimensions Display
```
📐 Crop region: 640×640 px | 20-80% height, 15-85% width
   └─ Shows pixel size and percentage position
```

---

## 🔧 Common Adjustments

### Problem: Face is too high in frame
```
Current: Top: 15%, Bottom: 85%
Solution: INCREASE Top slider
Adjust to: Top: 25%, Bottom: 85%
Result: Move crop down, center face better
```

### Problem: Face is too low in frame
```
Current: Top: 25%, Bottom: 85%
Solution: DECREASE Top slider
Adjust to: Top: 15%, Bottom: 85%
Result: Move crop up, position face higher
```

### Problem: Too much forehead visible
```
Current: Top: 10%, Bottom: 80%
Solution: INCREASE Top slider
Adjust to: Top: 20%, Bottom: 80%
Result: Crop closer to actual head top
```

### Problem: Shoulders cut off
```
Current: Top: 20%, Bottom: 75%
Solution: DECREASE Bottom slider
Adjust to: Top: 20%, Bottom: 85%
Result: Include more shoulders
```

### Problem: Too much chest/body visible
```
Current: Top: 15%, Bottom: 90%
Solution: INCREASE Bottom slider
Adjust to: Top: 15%, Bottom: 80%
Result: Crop tighter at bottom
```

### Problem: Left/right framing uneven
```
Current: Left: 10%, Right: 90%
Solution: Adjust BOTH to match
Adjust to: Left: 20%, Right: 80%
Result: Symmetric framing
```

---

## 📋 Country Specifications

### United States (US)
```
Size: 2" × 2" (square)
Head Height: 50% of photo
Eyes: 56% from bottom
Standard for: Passport, driver's license, visa
```

### Canada (CA)
```
Size: 50mm × 70mm (1.97" × 2.76")
Head Height: 55% of photo
Eyes: 60% from bottom
Standard for: Passport, permanent resident card
```

### United Kingdom (UK)
```
Size: 35mm × 45mm (1.38" × 1.77")
Head Height: 54% of photo
Eyes: 58% from bottom
Standard for: Passport, driving license, visa
```

---

## 💡 Tips & Tricks

### ⚡ Speed Tips
- Start with default values (usually pretty close)
- Make 1-2% adjustments at a time
- Watch preview to see changes instantly
- Small tweaks often produce best results

### 🎯 Precision Tips
- Use crosshair as alignment reference
- Check corner markers for symmetry
- Watch dimension display to see exact size
- Take multiple attempts if needed

### 🎨 Quality Tips
- Use good lighting photos for best results
- Higher resolution source = better quality
- 300 DPI is professional printing standard
- JPEG quality at 95% balances size and quality

### 📱 Workflow Tips
- Process test photo first to learn interface
- Once you find good values, reuse them
- Take screenshots of sliders for consistent results
- Batch process similar photos with same settings

---

## 🆚 Automatic vs Manual Mode

### Choose AUTOMATIC When:
✅ Photo is clear and well-lit  
✅ Face is frontal and centered  
✅ You trust AI detection  
✅ Quick processing needed  
✅ Just getting started  

**Time to process**: ~2-3 seconds

### Choose MANUAL When:
✅ Auto detection isn't quite right  
✅ You want pixel-perfect control  
✅ Photo has unusual angle/framing  
✅ You're being particular about composition  
✅ You need to fix AI mistakes  

**Time to process**: ~30-60 seconds

### Pro Tip
Try AUTOMATIC first to see what the AI suggests, then switch to MANUAL to refine if needed!

---

## 📥 Download Options

### Photo Download
```
File: [country]_photo.jpg
Size: Country-specific (e.g., 2"×2" for US)
Resolution: Your chosen DPI (default 300)
Quality: JPEG 95%
Use for:
- Print and submit to agencies
- Digital document upload
- ID card applications
```

### Print Sheet Download
```
File: [country]_sheet_4x6.jpg (or 6x6)
Layout: Multiple copies arranged
Size: Paper dimensions (4×6" or 6×6")
Resolution: Your chosen DPI
Copies: Your selected number (1-20)
Quality: JPEG 95%
Use for:
- Direct printing on photo paper
- Bulk ID photo production
- Keep-on-file copies
```

---

## 🐛 Troubleshooting

### Problem: Sliders aren't moving
**Solution**: 
- Ensure valid range (Top < Bottom, Left < Right)
- Try moving slider all the way to one side first
- Refresh browser page

### Problem: Preview not updating
**Solution**:
- Check that slider values are changing
- Try moving Bottom slider first, then others
- Close and reopen the manual adjustment section

### Problem: Green crop box not visible
**Solution**:
- Adjust Bottom % slider to ensure crop area exists
- Check that values meet minimum requirements
- Try default values first

### Problem: Downloaded photo looks different
**Solution**:
- Photos display differently on different screens
- Print at 300 DPI for accurate representation
- Check print scale in printer settings

### Problem: App won't launch
**Solution**:
- Ensure Python and Streamlit installed
- Check file path has no special characters
- Try: `pip install -r requirements.txt`
- Restart terminal and try again

### Problem: Photo is too small/too large
**Solution**:
- Check country selection (affects final size)
- Verify crop area is large enough
- For larger crops: decrease Top %, increase Bottom %

---

## 📚 Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| MANUAL_CROPPING_QUICK_START.md | Quick reference | Getting started |
| MANUAL_CROPPING_GUIDE.md | Comprehensive guide | Learning details |
| README_GUI.md | General GUI info | App overview |
| IMPLEMENTATION_SUMMARY.md | Technical details | Understanding features |
| This file | Complete overview | You are here! 👈 |

---

## 🎯 Workflow Examples

### Example 1: Quick Processing
```
1. Upload photo (10 sec)
2. Select Automatic mode (5 sec)
3. Click download (5 sec)
Total: ~20 seconds
```

### Example 2: Careful Framing
```
1. Upload photo (10 sec)
2. Select Manual Adjustment (5 sec)
3. Review instructions (30 sec)
4. Adjust sliders 3-5 times (60 sec)
5. Download (10 sec)
Total: ~2 minutes
```

### Example 3: Learning
```
1. Upload photo (10 sec)
2. Try Automatic (5 sec)
3. Switch to Manual (5 sec)
4. Study visual guides (60 sec)
5. Experiment with sliders (90 sec)
6. Download result (10 sec)
Total: ~3 minutes
```

---

## ✨ Feature Highlights

✅ **Two Modes**: Automatic (fast) + Manual (precise)  
✅ **Visual Guides**: Learn proper framing while adjusting  
✅ **Live Preview**: See results in real-time  
✅ **Precise Control**: 4 independent sliders  
✅ **Smart Defaults**: Based on country specs  
✅ **Multiple Countries**: US, CA, UK specs  
✅ **Print Ready**: Download individual or bulk sheets  
✅ **Professional Quality**: 300 DPI default, 95% quality  
✅ **Easy Learning**: Instructions and visual examples included  

---

## 🚀 Next Steps

### Immediate (Now)
- [ ] Launch the app
- [ ] Upload a test photo
- [ ] Try both Automatic and Manual modes
- [ ] Adjust sliders and watch preview

### Short Term (Today)
- [ ] Process your actual photos
- [ ] Download and review results
- [ ] Print test sheet
- [ ] Adjust settings if needed

### Medium Term (This Week)
- [ ] Batch process multiple photos
- [ ] Standardize settings for consistency
- [ ] Build library of print sheets
- [ ] Get feedback from recipients

### Long Term (Ongoing)
- [ ] Refine your preferred settings
- [ ] Share app with friends/family
- [ ] Use for professional applications
- [ ] Explore advanced features

---

## 📞 Quick Reference

### Slider Ranges
- Top: 0-50%
- Bottom: (Top+30%)-100%
- Left: 0-40%
- Right: (Left+40%)-100%

### Default Values
- Top: ~20%
- Bottom: ~80%
- Left: ~15%
- Right: ~85%

### Download Formats
- Photo: Single JPEG at country spec size
- Sheet: Multiple photos on paper-sized JPEG

### DPI Settings
- 100-200 DPI: Draft quality
- 300 DPI: Professional printing (default)
- 400-600 DPI: High-quality printing

### Print Layouts
- 4×6": Smaller, more copies per sheet
- 6×6": Larger, fewer copies per sheet

---

## 🎉 You're Ready!

The manual cropping feature is ready to use. You now have complete control over:

✓ Photo framing and composition  
✓ Crop positioning with pixel precision  
✓ Country-specific requirements  
✓ Print sheet generation  
✓ Professional ID photo production  

**Status**: ✅ PRODUCTION READY
**Version**: 1.1 with Manual Cropping
**Last Updated**: January 2025

Enjoy your new manual cropping capabilities! 📸✨
