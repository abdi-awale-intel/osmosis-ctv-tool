# Python 3.13.1 Build Configuration Guide

This document explains how to ensure your Git builds use Python 3.13.1 specifically.

## Files Created for Python 3.13.1 Builds

### 1. GitHub Actions Workflow (`.github/workflows/build.yml`)
- **Purpose**: Configures GitHub Actions to use Python 3.13.1
- **Key Features**:
  - Explicitly sets `python-version: '3.13.1'`
  - Tests on multiple Windows runners
  - Validates Python version before building
  - Creates artifacts with Python version in name

### 2. Runtime Specification (`runtime.txt`)
- **Purpose**: Specifies Python 3.13.1 for deployment platforms
- **Content**: Simply contains `python-3.13.1`

### 3. Project Configuration (`pyproject.toml`)
- **Purpose**: Modern Python project configuration
- **Key Features**:
  - Sets `requires-python = ">=3.13.1"`
  - Defines dependencies compatible with Python 3.13.1
  - Configures build system and tools

### 4. Docker Configuration (`Dockerfile`)
- **Purpose**: Containerized builds with Python 3.13.1
- **Base Image**: `python:3.13.1-windowsservercore`

### 5. Build Scripts
#### Batch Script (`build_python3131.bat`)
- Windows batch script with Python 3.13.1 verification
- Creates virtual environment with correct Python version
- Validates Python version at each step

#### PowerShell Script (`build_python3131.ps1`)
- Advanced PowerShell script with better error handling
- Colored output and detailed logging
- Parameter support for clean builds

### 6. Enhanced Requirements (`requirements_python3131.txt`)
- **Purpose**: Python 3.13.1 compatible package versions
- **Key Features**:
  - Updated package versions for Python 3.13.1
  - Performance improvements specific to Python 3.13.1
  - Windows-specific packages

### 7. PyInstaller Specification (`ctvlist_gui_python3131.spec`)
- **Purpose**: Enhanced PyInstaller configuration
- **Key Features**:
  - Python 3.13.1 optimized settings
  - Better module detection
  - Improved hidden imports

### 8. Build Validator (`build_validator_python3131.py`)
- **Purpose**: Comprehensive build environment validation
- **Checks**:
  - Verifies Python 3.13.1 is active
  - Tests all required modules
  - Validates custom modules
  - Checks build tools
  - Tests GUI import

## Usage Instructions

### For GitHub Actions (Recommended)
1. Copy `.github/workflows/build.yml` to your repository
2. Commit and push - GitHub will automatically use Python 3.13.1

### For Local Builds

#### Option 1: Use the Batch Script
```cmd
# Navigate to your project directory
cd C:\Users\abdiawal\Downloads\Scripts\osmosis-ctv-tool

# Run the Python 3.13.1 build script
build_python3131.bat
```

#### Option 2: Use the PowerShell Script
```powershell
# Navigate to your project directory
cd C:\Users\abdiawal\Downloads\Scripts\osmosis-ctv-tool

# Run with clean build
.\build_python3131.ps1 -Clean -Verbose

# Or simple build
.\build_python3131.ps1
```

#### Option 3: Manual Build with Python 3.13.1
```cmd
# Verify Python version
python --version
# Should show: Python 3.13.1

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements_python3131.txt

# Validate environment
python build_validator_python3131.py

# Build with PyInstaller
pyinstaller ctvlist_gui_python3131.spec --clean --noconfirm
```

### For Docker Builds
```cmd
# Build Docker image with Python 3.13.1
docker build -t ctvlist-gui:python3131 .

# Run container
docker run -it ctvlist-gui:python3131
```

## Verification Steps

### 1. Check Python Version in Build
Every build script includes verification:
```cmd
python --version | findstr "3.13.1"
```

### 2. Run Build Validator
```cmd
python build_validator_python3131.py
```

### 3. Check GitHub Actions Logs
In GitHub Actions, look for:
```
Set up Python 3.13.1
Python version: Python 3.13.1
```

## Troubleshooting

### Problem: Git builds still use wrong Python version
**Solution**: 
1. Check if `.github/workflows/build.yml` is committed
2. Verify the workflow file has `python-version: '3.13.1'`
3. Clear GitHub Actions cache

### Problem: Local builds fail with Python version error
**Solution**:
1. Install Python 3.13.1 from [python.org](https://www.python.org/downloads/release/python-3131/)
2. Update your PATH environment variable
3. Use virtual environment: `python -m venv venv`

### Problem: PyInstaller fails with module errors
**Solution**:
1. Use the updated spec file: `ctvlist_gui_python3131.spec`
2. Run build validator: `python build_validator_python3131.py`
3. Install missing modules: `pip install -r requirements_python3131.txt`

### Problem: Custom modules not found in compiled executable
**Solution**:
1. Check that custom modules are in the hiddenimports list in the .spec file
2. Verify modules are in the correct directory structure
3. Use the enhanced spec file which auto-detects custom modules

## Best Practices

1. **Always use virtual environments** - prevents version conflicts
2. **Run build validator first** - catches issues early
3. **Use the enhanced .spec file** - better module detection
4. **Test builds locally** - before pushing to Git
5. **Check GitHub Actions logs** - verify Python version is correct

## Integration with Existing Code

Your existing `ctvlist_gui.py` already has good error handling for missing modules. The Python 3.13.1 build configurations will work with your current code structure.

The build process will:
1. Verify Python 3.13.1 is active
2. Install all required dependencies
3. Validate that custom modules can be imported
4. Build the executable with proper module bundling
5. Test the resulting executable

## File Placement

Place these files in your repository root:
```
osmosis-ctv-tool/
├── .github/workflows/build.yml          # GitHub Actions
├── runtime.txt                          # Runtime specification  
├── pyproject.toml                       # Project configuration
├── Dockerfile                           # Docker configuration
├── build_python3131.bat                 # Windows batch script
├── build_python3131.ps1                 # PowerShell script
├── requirements_python3131.txt          # Enhanced requirements
├── ctvlist_gui_python3131.spec          # PyInstaller spec
├── build_validator_python3131.py        # Build validator
└── src/ctvlist_gui.py                   # Your main application
```

## Next Steps

1. **Commit all configuration files** to your Git repository
2. **Push to trigger GitHub Actions** with Python 3.13.1
3. **Test local builds** using the provided scripts
4. **Run build validator** to ensure everything is working
5. **Monitor build logs** to confirm Python 3.13.1 is being used

The configuration ensures that both local development and Git CI/CD builds use exactly Python 3.13.1, eliminating the version mismatch issues you were experiencing.
