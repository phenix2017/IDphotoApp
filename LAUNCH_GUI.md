# 🎨 IDphotoApp GUI - Launch Instructions

## THE EASIEST WAY 👇

### 🖱️ Double-Click This File:
```
run_gui.bat
```

**That's it!** A browser window opens automatically.

---

## If Double-Click Doesn't Work:

### Option 1: Copy-Paste into PowerShell
```powershell
cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp"; python -m streamlit run streamlit_app.py
```

Then open browser to: **http://localhost:8501**

### Option 2: Windows Run Dialog
Press `Win + R`, then paste:
```
cmd /c cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp" && python -m streamlit run streamlit_app.py
```

---

## What Happens Next:

1. **Terminal shows**:
   ```
   You can now view your Streamlit app in your browser.
   
   Local URL: http://localhost:8501
   ```

2. **Browser opens** (or navigate manually to the URL above)

3. **See the GUI** with:
   - Photo upload area
   - Country/DPI/Layout settings
   - Download buttons

---

## Using the GUI

### 3-Step Process:

**Step 1: Upload Photo**
- Click upload area or drag & drop JPG/PNG
- Must be clear, well-lit, front-facing

**Step 2: Configure Settings (Left Panel)**
- Country: US / CA / UK
- Replace Background: Yes/No
- DPI: 300 (best quality)
- Layout: 4x6" or 6x6"
- Copies: How many photos

**Step 3: Download**
- "📥 Download Photo" - Your cropped photo
- "📥 Download Sheet" - Print sheet with copies

---

## 🆘 Troubleshooting

### "Command not found"
- Make sure you're in the right folder first:
  ```powershell
  cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp"
  ```

### Browser doesn't open
- Manually go to: `http://localhost:8501`
- Or check if another Streamlit app is running

### "Address already in use"
- Another app is using port 8501
- Use different port:
  ```powershell
  python -m streamlit run streamlit_app.py --server.port 8502
  ```

### Files don't download
- Try different browser (Chrome, Firefox, Edge)
- Wait 2-3 seconds after processing

### "Face not detected"
- Photo must be clear and front-facing
- Try a different, better-lit photo

---

## 🎯 Pro Tips

✓ **Best Results**: Clear photo, good lighting, neutral expression  
✓ **Fast Processing**: Click upload and settings appear instantly  
✓ **Batch Workflow**: Process multiple photos, switching between them  
✓ **Print Ready**: Downloaded sheets are ready for standard photo printing  
✓ **Mobile Friendly**: Works on tablets too!  

---

## 📖 For More Help

- [GUI_GUIDE.md](GUI_GUIDE.md) - Detailed guide with all features
- [TEST_GUIDE.md](TEST_GUIDE.md) - Command-line version
- [GUI_VS_CLI.md](GUI_VS_CLI.md) - Compare GUI vs CLI

---

## ✨ Ready?

### 👉 Double-click: `run_gui.bat`

Or copy-paste:
```powershell
cd "C:\Users\robin\Documents\GitHub\IDphoto\IDphotoApp"; python -m streamlit run streamlit_app.py
```

**Happy photo processing!** 📸
