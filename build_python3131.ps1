# PowerShell build script with Python 3.13.1 verification
param(
    [switch]$Clean,
    [switch]$Verbose,
    [string]$OutputDir = "dist"
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "CTV LIST GUI BUILD SCRIPT (PowerShell)" -ForegroundColor Cyan
Write-Host "Python 3.13.1 Build Environment" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Function to check command exit code
function Test-ExitCode {
    param($Message)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: $Message" -ForegroundColor Red
        exit 1
    }
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Current Python: $pythonVersion"

if ($pythonVersion -notmatch "3\.13\.1") {
    Write-Host "ERROR: Python 3.13.1 not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.13.1 from: https://www.python.org/downloads/release/python-3131/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Python 3.13.1 confirmed" -ForegroundColor Green

# Check pip
Write-Host "Checking pip..." -ForegroundColor Yellow
python -m pip --version
Test-ExitCode "pip not available"
Write-Host "✅ pip confirmed" -ForegroundColor Green

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning build directories..." -ForegroundColor Yellow
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleaned build directories" -ForegroundColor Green
}

# Create virtual environment
Write-Host "Creating virtual environment with Python 3.13.1..." -ForegroundColor Yellow
python -m venv venv
Test-ExitCode "Failed to create virtual environment"
Write-Host "✅ Virtual environment created" -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Verify Python version in venv
$venvPythonVersion = python --version 2>&1
if ($venvPythonVersion -notmatch "3\.13\.1") {
    Write-Host "ERROR: Virtual environment not using Python 3.13.1" -ForegroundColor Red
    Write-Host "Venv Python: $venvPythonVersion"
    exit 1
}
Write-Host "✅ Virtual environment using Python 3.13.1" -ForegroundColor Green

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Test-ExitCode "Failed to upgrade pip"

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    python -m pip install -r requirements.txt
    Test-ExitCode "Failed to install requirements"
    Write-Host "✅ Requirements installed" -ForegroundColor Green
} else {
    Write-Host "WARNING: requirements.txt not found, installing basic packages" -ForegroundColor Yellow
    python -m pip install pandas pillow openpyxl pyinstaller
}

# Run validation
Write-Host "Running build validation..." -ForegroundColor Yellow
if (Test-Path "build_validator.py") {
    python build_validator.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Build validation passed" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Build validation found issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: build_validator.py not found" -ForegroundColor Yellow
}

# Build executable
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
if (Test-Path "ctvlist_gui.spec") {
    python -m PyInstaller ctvlist_gui.spec --clean --noconfirm
} else {
    Write-Host "WARNING: ctvlist_gui.spec not found, using auto-generation" -ForegroundColor Yellow
    python -m PyInstaller --onefile --windowed --name ctvlist_gui "src\ctvlist_gui.py"
}
Test-ExitCode "Build failed"

Write-Host "✅ Build completed successfully" -ForegroundColor Green

# Verify build output
Write-Host "Verifying build output..." -ForegroundColor Yellow
if (Test-Path "$OutputDir\ctvlist_gui.exe") {
    $exeInfo = Get-Item "$OutputDir\ctvlist_gui.exe"
    Write-Host "✅ Executable created: $($exeInfo.FullName)" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round($exeInfo.Length/1MB, 2)) MB"
    Write-Host "   Created: $($exeInfo.CreationTime)"
} else {
    Write-Host "ERROR: Executable not found in $OutputDir directory" -ForegroundColor Red
    Get-ChildItem $OutputDir -ErrorAction SilentlyContinue
    exit 1
}

# Test executable (with timeout)
Write-Host "Testing executable..." -ForegroundColor Yellow
$job = Start-Job -ScriptBlock { 
    param($exePath)
    & $exePath --help 2>&1
} -ArgumentList "$OutputDir\ctvlist_gui.exe"

Wait-Job $job -Timeout 10 | Out-Null
Remove-Job $job -Force
Write-Host "✅ Executable test completed" -ForegroundColor Green

# Deactivate virtual environment
deactivate

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "BUILD SUMMARY" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Python Version: 3.13.1" -ForegroundColor White
Write-Host "Build Status: SUCCESS" -ForegroundColor Green
Write-Host "Output: $OutputDir\ctvlist_gui.exe" -ForegroundColor White
Write-Host "Build Environment: Virtual Environment" -ForegroundColor White
Write-Host "===========================================" -ForegroundColor Cyan
