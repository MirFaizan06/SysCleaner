@echo off
setlocal EnableDelayedExpansion
title SysCleaner Build Pipeline — Tech Bytes Design
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   SysCleaner  —  Build Pipeline  v1.0.0     ║
echo  ║   Tech Bytes Design                          ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ── Step 1: Dependencies ──────────────────────────────────────────────────────
echo [1/4]  Installing dependencies...
python -m pip install rich psutil pillow pyinstaller --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    goto :error
)
echo        Done.
echo.

:: ── Step 2: Icon ──────────────────────────────────────────────────────────────
echo [2/4]  Generating icon...
python create_icon.py
if %errorlevel% neq 0 (
    echo [ERROR] Icon generation failed. Is Pillow installed?
    goto :error
)
echo.

:: ── Step 3: PyInstaller ───────────────────────────────────────────────────────
echo [3/4]  Building EXE (PyInstaller)...
python -m PyInstaller syscleaner.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed. Check output above.
    goto :error
)
echo        EXE ready: dist\SysCleaner.exe
echo.

:: ── Step 4: Inno Setup installer ─────────────────────────────────────────────
echo [4/4]  Creating installer (Inno Setup)...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo [WARN]  Inno Setup not found at expected path. Skipping installer step.
    echo         Install from https://jrsoftware.org/isinfo.php then re-run this script.
    goto :done
)

:: Create output folder
if not exist "dist\installer" mkdir "dist\installer"

%ISCC% syscleaner.iss
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed. Check syscleaner.iss.
    goto :error
)
echo        Installer ready: dist\installer\SysCleaner_Setup_v1.0.0.exe

:done
echo.
echo  ════════════════════════════════════════════════
echo  BUILD COMPLETE
echo.
echo  EXE:        dist\SysCleaner.exe
echo  Installer:  dist\installer\SysCleaner_Setup_v1.0.0.exe  (if Inno Setup ran)
echo  ════════════════════════════════════════════════
echo.
pause
exit /b 0

:error
echo.
echo  [BUILD FAILED] See errors above.
pause
exit /b 1
