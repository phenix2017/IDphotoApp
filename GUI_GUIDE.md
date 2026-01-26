# IDphotoApp GUI - Quick Start Guide

## 🚀 Launch the GUI

### Option 1: Double-Click (Easiest!)
Simply double-click: `run_gui.bat`

A browser window will open automatically at `http://localhost:8501`

### Option 2: Command Line
```powershell
cd C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp
streamlit run streamlit_app.py
```

### Option 3: With Python directly
```powershell
cd C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp
python -m streamlit run streamlit_app.py
```

---

## 📸 How to Use the GUI

### Step 1: Configure Settings (Left Sidebar)
- **Select Country**: Choose US, CA, or UK
- **Replace Background**: Toggle for white background
- **DPI**: Choose print quality (300 DPI = best)
- **Layout**: Pick 4x6", 6x6", or custom
- **Copies**: How many photos on print sheet (1-20)
- **Margin & Spacing**: Fine-tune layout

### Step 2: Upload Photo
- Click "Browse files" or drag & drop
- Supports JPG, JPEG, PNG
- Should be clear, well-lit, front-facing

### Step 3: View Results
- **Left**: Your cropped photo
- **Right**: Print sheet with multiple copies
- Specifications displayed below

### Step 4: Download
- **Download Photo**: Individual cropped photo
- **Download Sheet**: Multi-copy print sheet ready for printing

---

## ⚙️ System Requirements

✓ Python 3.8+  
✓ All dependencies installed (opencv, pillow, streamlit, etc.)  
✓ Modern web browser (Chrome, Firefox, Edge, Safari)  
✓ 500MB free disk space  

---

## 🎨 GUI Features

| Feature | Description |
|---------|-------------|
| **Live Preview** | See cropped photo immediately |
| **Country Selection** | US, Canada, UK with official specs |
| **Background Replace** | One-click background removal |
| **Custom Layouts** | 4x6", 6x6", or custom dimensions |
| **DPI Control** | Adjust print quality (100-600 DPI) |
| **Multi-Copy Grid** | Arrange 1-20 copies on sheet |
| **Direct Download** | Save results instantly |
| **Mobile Responsive** | Works on tablets too |

---

## 💡 Tips for Best Results

### Photo Quality
- ✓ Bright, even lighting (natural window light ideal)
- ✓ Front-facing pose, neutral expression
- ✓ Mouth closed, eyes open, looking at camera
- ✓ Plain background (white, gray, or light colored)
- ✓ Head fills ~60% of frame vertically

### File Format
- ✓ JPEG or PNG
- ✓ Minimum 640×480 pixels
- ✓ Under 10 MB

### Printing
- ✓ Use glossy photo paper for best results
- ✓ Print at 300 DPI for official quality
- ✓ 4x6" is standard photo paper size
- ✓ Use color printer for best colors

---

## 🛑 Troubleshooting

### "Face not detected"
- **Problem**: Camera can't find face in photo
- **Solution**: 
  - Use a clearer, better-lit photo
  - Ensure face is front-facing
  - Make sure entire face is visible

### Browser doesn't open automatically
- **Solution**: Open manually at `http://localhost:8501`

### Slow processing
- **Solution**: This is normal for face detection - takes 1-3 seconds

### Downloaded file is corrupted
- **Solution**: Try a different browser or wait for full generation

### "Port already in use"
- **Solution**: 
  - Close any other Streamlit apps
  - Or use: `streamlit run streamlit_app.py --server.port 8502`

---

## 🎯 Example Workflows

### Quick Test
1. Open `run_gui.bat`
2. Use "test_sample.jpg" or upload a photo
3. Keep default settings
4. Click "Download Photo"

### Professional Printing
1. Select country
2. Toggle "Replace Background" ON
3. Set DPI to 300
4. Set Copies to 6
5. Download sheet and print on glossy paper

### Custom Size
1. Select "Custom" layout
2. Enter width and height in inches
3. Adjust copies and spacing
4. Download and print

---

## 📞 Support

If the GUI won't start:

1. Check Python installation:
   ```powershell
   python --version
   ```

2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt streamlit
   ```

3. Try command-line version:
   ```powershell
   python process_photo.py your_photo.jpg --country US
   ```

---

## 🎓 Learn More

- [Command-Line Guide](TEST_GUIDE.md) - Use without GUI
- [Specifications](specs.json) - Country photo specs
- [Project Architecture](README.md) - Technical details

---

**Enjoy your ID photos! 📸**
