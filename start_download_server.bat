@echo off
title Osmosis Download Server Launcher
color 0A

echo.
echo  ███████████████████████████████████████████
echo  ██                                       ██
echo  ██           OSMOSIS v2.0                ██
echo  ██        Download Server Setup          ██
echo  ██                                       ██
echo  ███████████████████████████████████████████
echo.

echo [1/3] Checking prerequisites...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)
echo ✅ Python found

REM Check if package exists
if not exist "package_output\Osmosis_v2.0_Complete.zip" (
    echo ⚠️  Package not found. Creating package first...
    call create_package.bat
    if %errorlevel% neq 0 (
        echo ❌ Failed to create package!
        pause
        exit /b 1
    )
)
echo ✅ Package ready

echo.
echo [2/3] Starting download server...
echo.

REM Start the Python download server
python download_server.py

echo.
echo [3/3] Server stopped.
echo.
echo Thank you for using Osmosis Download Server!
pause
