@echo off
REM ==========================================================================
REM  GFH/VidaPay Bot — Force Clean EXE Build
REM  Developed by Abad Umair Channa
REM
REM  This script:
REM    1. Cleans previous build artifacts (build/, dist/, *.spec.tmp)
REM    2. Rebuilds every .spec file in the repo with PyInstaller
REM    3. Produces self-contained .exe files with:
REM       - Embedded logo (base64, resized, composited on navy)
REM       - Embedded icon (base64 ICO)
REM       - Embedded theme_manager (light/dark themes, toggle button)
REM       - Embedded logo_handler (theme-safe logo display)
REM       - Windows Explorer .exe icon (from icon= in .spec)
REM       - Taskbar + titlebar icon (from iconbitmap at runtime)
REM       - All button colors (run=red, sched=navy, stop=grey, save=navy)
REM
REM  USAGE:
REM    1. Save this file in the repo root (next to the .spec files)
REM    2. Double-click build_exe.bat, OR run from Command Prompt
REM    3. The .exe files will appear in the dist\ folder
REM
REM  PREREQUISITES:
REM    - Python 3.11+ installed and in PATH
REM    - Run: pip install pyinstaller -r requirements.txt
REM ==========================================================================

setlocal enabledelayedexpansion
title Force Clean EXE Build

echo.
echo  ============================================================
echo   Force Clean EXE Build
echo  ============================================================
echo.

REM ── Step 0: Verify Python + PyInstaller are available ──
echo  Step 0: Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ERROR: Python not found in PATH. Install Python 3.11+ first.
    pause
    exit /b 1
)
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo    PyInstaller not found. Installing...
    python -m pip install --upgrade pyinstaller
)
echo    Python + PyInstaller OK
echo.

REM ── Step 1: Clean previous build artifacts ──
echo  Step 1: Cleaning previous build artifacts...
if exist "build" (
    rmdir /s /q "build"
    echo    removed build\
)
if exist "dist" (
    rmdir /s /q "dist"
    echo    removed dist\
)
REM Clean __pycache__ dirs
for /d %%D in (__pycache__) do (
    if exist "%%D" rmdir /s /q "%%D"
)
REM Clean .pyc files
del /s /q *.pyc 2>nul
echo    cleaned __pycache__ and .pyc files
echo.

REM ── Step 2: Install/upgrade dependencies ──
echo  Step 2: Installing dependencies...
if exist "requirements.txt" (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install --upgrade pyinstaller
    echo    dependencies installed
) else (
    echo    no requirements.txt found — skipping
)
echo.

REM ── Step 3: Build every .spec file ──
echo  Step 3: Building .exe files from .spec files...
set BUILD_COUNT=0
set FAIL_COUNT=0

for %%S in (*.spec) do (
    echo.
    echo    Building: %%S
    python -m PyInstaller "%%S" --noconfirm --clean 2>&1
    if errorlevel 1 (
        echo    FAILED: %%S
        set /a FAIL_COUNT+=1
    ) else (
        echo    SUCCESS: %%S
        set /a BUILD_COUNT+=1
    )
)

echo.
echo  ============================================================
echo   Build Summary
echo  ============================================================
echo    Successful builds: !BUILD_COUNT!
echo    Failed builds:     !FAIL_COUNT!
echo.

REM ── Step 4: List produced .exe files ──
if exist "dist" (
    echo  Produced .exe files in dist\:
    dir /b "dist\*.exe" 2>nul
    echo.
    echo  Full paths:
    for %%E in (dist\*.exe) do (
        echo    %%~fE
    )
) else (
    echo  WARNING: dist\ folder not found — all builds may have failed
)

echo.
echo  ============================================================
echo   Done. Copy the .exe files from dist\ to distribute.
echo  ============================================================
echo.
pause
endlocal
