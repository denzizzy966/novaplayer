@echo off
title NovaPlayer - Environment & Dependency Setup
cd /d "%~dp0"

echo =========================================================
echo       NovaPlayer Dependency & Environment Setup
echo =========================================================
echo.

echo [1/3] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is NOT detected in your system PATH.
    echo     If you are using NovaPlayer.exe, you DO NOT need Python.
    echo     If you want to run from source code, please install Python 3.10+ from python.org.
) else (
    echo [*] Python found! Installing/verifying required packages...
    python -m pip install --upgrade pip >nul 2>nul
    python -m pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo [*] All Python packages are installed and up to date!
    ) else (
        echo [!] Warning: Some packages failed to install.
    )
)
echo.

echo [2/3] Checking Microsoft Edge WebView2 Runtime...
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv >nul 2>nul
if %errorlevel% neq 0 (
    reg query "HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv >nul 2>nul
    if %errorlevel% neq 0 (
        echo [!] WebView2 is NOT installed on this PC.
        echo [*] Modern UI requires WebView2 to prevent freezing and layout distortion.
        echo [*] Downloading official Microsoft WebView2 installer...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile 'MicrosoftEdgeWebview2Setup.exe'"
        if exist "MicrosoftEdgeWebview2Setup.exe" (
            echo [*] Installing WebView2 silently...
            start /wait MicrosoftEdgeWebview2Setup.exe /silent /install
            del MicrosoftEdgeWebview2Setup.exe 2>nul
            echo [*] WebView2 Runtime successfully installed!
        ) else (
            echo [!] Failed to download automatically. Opening official page...
            start https://go.microsoft.com/fwlink/p/?LinkId=2124703
        )
    ) else (
        echo [*] WebView2 Runtime is active and ready!
    )
) else (
    echo [*] WebView2 Runtime is active and ready!
)
echo.

echo [3/3] Checking Android SDK & ADB...
where adb >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] ADB detected in system PATH!
) else if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" (
    echo [*] Android SDK detected at %LOCALAPPDATA%\Android\Sdk!
) else if exist "D:\Android\Sdk\platform-tools\adb.exe" (
    echo [*] Android SDK detected at D:\Android\Sdk!
) else if exist "C:\Android\Sdk\platform-tools\adb.exe" (
    echo [*] Android SDK detected at C:\Android\Sdk!
) else (
    echo [!] Notice: Android SDK not found in standard paths.
    echo     Make sure Android Studio or command-line tools are installed.
    echo     You can also set custom SDK location in NovaPlayer Settings.
)
echo.

echo =========================================================
echo Setup check complete. You can now launch NovaPlayer!
echo =========================================================
echo.
pause
