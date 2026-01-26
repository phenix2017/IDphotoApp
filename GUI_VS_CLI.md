# IDphotoApp - GUI Now Available! 🎉

## Two Ways to Use the App

### 1️⃣ Command Line (Original)
```powershell
python process_photo.py your_photo.jpg --country US
```
- Fast, scriptable
- Good for batch processing
- See: [TEST_GUIDE.md](TEST_GUIDE.md)

### 2️⃣ GUI - Graphical Interface (NEW!)
```powershell
python -m streamlit run streamlit_app.py
```
- **Or just double-click:** `run_gui.bat`
- Visual, interactive
- Easy to configure
- See: [GUI_GUIDE.md](GUI_GUIDE.md)

---

## 🖥️ GUI Features

### User Interface
✅ Web-based (opens in browser)  
✅ Point & click configuration  
✅ Live photo preview  
✅ Real-time print sheet display  
✅ One-click download  

### Settings Panel (Left Sidebar)
- **Country Selection** - US, Canada, UK
- **Background Replacement** - Toggle white background
- **DPI** - Print quality (100-600)
- **Layout** - 4x6", 6x6", or custom
- **Copies** - 1 to 20 photos per sheet
- **Spacing & Margin** - Fine-tune layout

### Results Display (Main Area)
- **Cropped Photo** - Your individual photo
- **Print Sheet** - Multi-copy grid
- **Download Buttons** - Save JPEGs directly
- **Specifications** - Show what was used

---

## ⚡ Quick Start

### Option A: Double-Click (Easiest!)
```
C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp\run_gui.bat
```
Browser opens automatically at `http://localhost:8501`

### Option B: PowerShell
```powershell
cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp"
python -m streamlit run streamlit_app.py
```

### Option C: Batch Command
```powershell
cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp"
.\run_gui.bat
```

---

## 📋 Workflow: GUI vs CLI

### Using GUI
1. Double-click `run_gui.bat`
2. Upload photo
3. Adjust settings visually
4. See results instantly
5. Click "Download Photo" or "Download Sheet"

### Using CLI
1. Open PowerShell
2. Run: `python process_photo.py photo.jpg --country US`
3. Results saved to `output/` folder
4. Open files with image viewer

---

## 🎯 Choose Your Approach

| Feature | GUI | CLI |
|---------|-----|-----|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Speed** | Fast | Faster |
| **Batch Processing** | ❌ | ✅ |
| **No Installation** | ✅ | ✅ |
| **Visual Preview** | ✅ | ❌ |
| **Mobile Friendly** | ✅ | ❌ |
| **Automation** | ❌ | ✅ |

---

## 📚 Documentation

- **GUI_GUIDE.md** - Full GUI user guide with tips
- **START_GUI.txt** - Quick start for GUI (read first!)
- **TEST_GUIDE.md** - Command-line examples
- **README.md** - Project architecture
- **.github/copilot-instructions.md** - For AI agents

---

## ✨ Example GUI Workflow

### Scenario: Get passport photo printed

1. **Open GUI**: Double-click `run_gui.bat`
2. **Upload**: Drag-drop your photo
3. **Country**: Select "US - US Passport"
4. **Settings**: 
   - ✓ Replace Background: ON
   - DPI: 300
   - Layout: 4x6"
   - Copies: 6
5. **Download**: Click "Download Sheet"
6. **Print**: Take to Staples/CVS on glossy paper

Done in under 1 minute! 🎉

---

## 🔧 System Requirements

✅ Python 3.8+  
✅ Streamlit 1.28+ (auto-installed)  
✅ OpenCV, PIL (already installed)  
✅ Modern web browser  
✅ 100MB free disk space  

---

## 🚀 Try It Now!

### GUI (Recommended for beginners)
```
Double-click: run_gui.bat
```

### CLI (Recommended for power users)
```
python process_photo.py test_sample.jpg --country US
```

---

**Choose GUI or CLI - both work perfectly!** ✨
