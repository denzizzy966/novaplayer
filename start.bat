@echo off
title NovaPlayer Launcher
cd /d "%~dp0"

echo ====================================================
echo        NovaPlayer - Android 14 Gaming Suite
echo ====================================================
echo Starting NovaPlayer...

if exist "NovaPlayer.exe" (
    start "" "NovaPlayer.exe"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python app.py
    pause
    exit /b 0
)

if exist "D:\laragon\bin\python\python-3.10\python.exe" (
    "D:\laragon\bin\python\python-3.10\python.exe" app.py
    pause
    exit /b 0
)

echo [!] Error: Python or NovaPlayer.exe not found!
echo Please run setup_dependencies.bat or launch NovaPlayer.exe.
pause
