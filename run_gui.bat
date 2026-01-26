@echo off
REM Launch IDphotoApp GUI with Streamlit

echo Starting IDphotoApp GUI...
echo.
echo Opening browser at http://localhost:8501
echo.
echo Press Ctrl+C in this window to stop the server
echo.

cd /d "%~dp0"
.venv\Scripts\python.exe -m streamlit run streamlit_app.py

pause
