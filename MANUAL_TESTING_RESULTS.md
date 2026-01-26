# IDphotoApp - Manual Testing Complete ✓

## Summary

The IDphotoApp is fully functional and ready for manual testing! You can now run the program directly with real images.

## What Works

✅ **Face Detection** - OpenCV cascade classifier (no Mediapipe required)  
✅ **Photo Cropping** - Scales and positions faces to country specs  
✅ **Background Replacement** - Simple HSV-based color segmentation  
✅ **Print Layout** - Multi-copy grid arrangement on standard paper sizes  
✅ **CLI Interface** - Full argument parsing and validation  
✅ **Error Handling** - Clear error messages for debugging  

## Test Results

| Test | Status | Output |
|------|--------|--------|
| US Passport 2x2" | ✓ PASS | `output/us_photo.jpg` (600x600px) + print sheet |
| Canada 50x70mm | ✓ PASS | `output/ca_photo.jpg` + print sheet |
| UK 35x45mm | ✓ PASS | `output/uk_photo.jpg` + print sheet |
| 6x6" Layout | ✓ PASS | `output/uk_sheet_6x6.jpg` (1800x1800px) |
| Face Detection | ✓ PASS | Detects test face with OpenCV cascade |

## Quick Start Commands

Copy & paste these into PowerShell:

```powershell
# Navigate to project
cd C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp

# Test US passport (simplest)
python process_photo.py test_sample.jpg --country US

# Test with custom layout
python process_photo.py test_sample.jpg --country UK --layout 6x6 --copies 2

# Use your own photo
python process_photo.py "C:\Path\To\Your\Photo.jpg" --country US
```

## Generated Files

All output is saved in `output/` directory:

- `{country}_photo.jpg` - Cropped individual photo
- `{country}_sheet_{W}x{H}.jpg` - Print sheet with multiple copies

## Testing Tips

1. **Use real photos** for best face detection accuracy
2. **Good lighting** helps cascade classifier
3. **Front-facing** pose works best
4. **View output JPEGs** with Windows Photo Viewer or Paint
5. **Print sheets** are ready for standard photo printing

## Documentation

- [TEST_GUIDE.md](TEST_GUIDE.md) - Detailed commands and examples
- [README.md](README.md) - Project architecture overview
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - AI agent guidance

## Next Steps

1. Try with your own photos
2. Test `--replace-bg` flag for background replacement
3. Experiment with `--layout 6x6` for square sheets
4. Print a test sheet to verify output quality
5. Consider adding custom country specs to `specs.json`

## Technical Notes

- **Face Detection**: OpenCV Haar Cascade (fast, no ML models)
- **Background Replacement**: HSV color-space skin detection
- **DPI**: Default 300 DPI (photo print standard)
- **Padding**: Automatically handles crops extending beyond image edges
- **Error Handling**: Clear messages guide users on issues

---

**Ready to test! Start with:** `python process_photo.py test_sample.jpg --country US`
