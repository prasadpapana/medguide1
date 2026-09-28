@echo off
title MedGuide - Medical Report Simplifier
echo.
echo  ========================================
echo   MedGuide - Starting Application...
echo  ========================================
echo.
cd /d "%~dp0"
echo  Starting Flask server...
echo  Open your browser and go to:
echo.
echo     http://127.0.0.1:5000
echo.
echo  Press CTRL+C to stop the server.
echo.
python app.py
pause
