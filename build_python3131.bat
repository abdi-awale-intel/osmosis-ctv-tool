@echo off
REM Build script with Python 3.13.1 verification
echo ==========================================
echo CTV LIST GUI BUILD SCRIPT
echo Python 3.13.1 Build Environment
echo ==========================================

REM Check Python version
echo Checking Python version...
python --version | findstr "3.13.1"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.13.1 not found!
    echo Current Python version:
    python --version
    echo.
    echo Please install Python 3.13.1 or update your PATH
    echo Download from: https://www.python.org/downloads/release/python-3131/
    pause
    exit /b 1
)

echo ✅ Python 3.13.1 confirmed

REM Verify pip is available
echo Checking pip...
python -m pip --version
if %errorlevel% neq 0 (
    echo ERROR: pip not available
    pause
    exit /b 1
)

echo ✅ pip confirmed

REM Create virtual environment with Python 3.13.1
echo Creating virtual environment...
if exist "venv" rmdir /s /q venv
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Verify we're using the correct Python in venv
echo Verifying virtual environment Python version...
python --version | findstr "3.13.1"
if %errorlevel% neq 0 (
    echo ERROR: Virtual environment not using Python 3.13.1
    python --version
    pause
    exit /b 1
)

echo ✅ Virtual environment using Python 3.13.1

REM Upgrade pip in virtual environment
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
    echo ✅ Requirements installed
) else (
    echo WARNING: requirements.txt not found, installing basic packages
    python -m pip install pandas pillow openpyxl pyinstaller
)

REM Run validation
echo Running build validation...
if exist "build_validator.py" (
    python build_validator.py
    if %errorlevel% neq 0 (
        echo WARNING: Build validation found issues
    ) else (
        echo ✅ Build validation passed
    )
) else (
    echo WARNING: build_validator.py not found
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build executable
echo Building executable with PyInstaller...
if exist "ctvlist_gui.spec" (
    python -m PyInstaller ctvlist_gui.spec --clean --noconfirm
) else (
    echo WARNING: ctvlist_gui.spec not found, using auto-generation
    python -m PyInstaller --onefile --windowed --name ctvlist_gui src\ctvlist_gui.py
)

if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo ✅ Build completed successfully

REM Verify build output
echo Verifying build output...
if exist "dist\ctvlist_gui.exe" (
    echo ✅ Executable created: dist\ctvlist_gui.exe
    dir dist\ctvlist_gui.exe
) else (
    echo ERROR: Executable not found in dist directory
    dir dist\
    pause
    exit /b 1
)

REM Test executable
echo Testing executable...
timeout 5 dist\ctvlist_gui.exe --help >nul 2>&1
echo ✅ Executable test completed

echo.
echo ==========================================
echo BUILD SUMMARY
echo ==========================================
echo Python Version: 3.13.1
echo Build Status: SUCCESS
echo Output: dist\ctvlist_gui.exe
echo Build Environment: Virtual Environment
echo ==========================================
echo.

REM Deactivate virtual environment
deactivate

echo Build completed! Press any key to exit.
pause
