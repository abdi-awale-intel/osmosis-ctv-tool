@echo off
title CTV List GUI Installer
color 0B

echo.
echo  ███████╗████████╗██╗   ██╗    ██╗     ██╗███████╗████████╗
echo  ██╔════╝╚══██╔══╝██║   ██║    ██║     ██║██╔════╝╚══██╔══╝
echo  ██║        ██║   ██║   ██║    ██║     ██║███████╗   ██║   
echo  ██║        ██║   ╚██╗ ██╔╝    ██║     ██║╚════██║   ██║   
echo  ███████╗   ██║    ╚████╔╝     ███████╗██║███████║   ██║   
echo  ╚══════╝   ╚═╝     ╚═══╝      ╚══════╝╚═╝╚══════╝   ╚═╝   
echo.
echo  CTV List Data Processor - Installer
echo  ====================================
echo.
echo  This installer will:
echo  - Install SQLPathFinder3 if not present
echo  - Set up Python environment
echo  - Install required packages
echo  - Create desktop shortcut
echo.

set /p confirm="Continue with installation? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Installation cancelled.
    pause
    exit /b
)

echo.
echo Starting installation...

REM Check if Python is available on the system
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found on system. The installer will download a portable version.
    echo This may take a few minutes depending on your internet connection.
    echo.
)

python deploy_ctvlist.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo Installation completed successfully!
    echo ====================================
    echo.
    echo You can now launch the CTV List GUI using:
    echo 1. Desktop shortcut "CTV List Data Processor"
    echo 2. Launch_CTV_List_GUI.bat in Downloads\Scripts\_Current\
    echo.
) else (
    echo.
    echo ====================================
    echo Installation encountered errors!
    echo ====================================
    echo Please check the error messages above and try again.
    echo.
)

pause
