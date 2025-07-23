# Installation Guide for CTV List Data Processor

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python ctvlist_gui.py
```

## System Requirements
- Python 3.8 or higher
- tkinter (usually included with Python)
- 50MB free disk space

## Installation Instructions

### 1. Python Installation
**Windows:**
- Download Python from [python.org](https://python.org)
- During installation, check "Add Python to PATH"
- tkinter is included automatically

**macOS:**
- Install Python from [python.org](https://python.org) OR
- Use Homebrew: `brew install python-tk`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk
```

**Linux (RHEL/CentOS/Fedora):**
```bash
sudo dnf install python3 python3-pip python3-tkinter
# OR for older systems:
sudo yum install python3 python3-pip tkinter
```

### 2. Install Dependencies
```bash
# Navigate to project directory
cd osmosis-ctv-tool

# Install required packages
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
# Test tkinter
python -c "import tkinter; print('tkinter: OK')"

# Test PIL/Pillow
python -c "import PIL; print('Pillow: OK')"

# Test pandas
python -c "import pandas; print('pandas: OK')"
```

## Troubleshooting

### tkinter Issues
**Error: "No module named 'tkinter'"**
- **Windows/Mac:** Reinstall Python from python.org
- **Linux:** `sudo apt install python3-tk`

### Pillow/PIL Issues  
**Error: "No module named 'PIL'"**
```bash
pip install --upgrade Pillow
```

**Image loading problems:**
- The app includes fallback systems for missing image libraries
- Intel logo will display as text if image loading fails

### pandas/openpyxl Issues
**Excel file reading problems:**
```bash
pip install --upgrade pandas openpyxl xlsxwriter
```

## Development Setup
```bash
# For developers working on the project
pip install -r requirements.txt
pip install pyinstaller  # For creating executables

# Create standalone executable
pyinstaller ctvlist_gui_python3131.spec
```

## GitHub Actions / CI Setup
For automated testing, this project includes dependency verification in the PyInstaller spec file with robust fallback systems for image processing.

## Support
- tkinter is included with standard Python installations
- Pillow enables logo scaling and image processing
- All dependencies are available via pip
- Fallback systems ensure the app works even with missing optional components
