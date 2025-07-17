# CTV List GUI Application - Deployment Package

## 📋 Overview

This deployment package automatically installs the CTV List Data Processor GUI application with all required dependencies, including a portable Python environment.

## 🚀 Quick Installation

1. **Download** this deployment package
2. **Extract** all files to a folder
3. **Right-click** `install.bat` and select **"Run as Administrator"**
4. **Follow** the on-screen instructions
5. **Launch** the application from the desktop shortcut

## 💻 System Requirements

- **Operating System**: Windows 10 or later (64-bit)
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 500 MB free disk space
- **Network**: Internet connection required for initial setup
- **Permissions**: Administrator rights for installation

## 📦 What Gets Installed

### SQLPathFinder3 Environment
- **Location**: `C:\Users\[Username]\My Programs\SQLPathFinder3\`
- **Python**: Portable Python 3.11 with pip
- **Packages**: pandas, numpy, openpyxl, Pillow

### Application Files
- **Location**: Same directory as deployment package
- **Main App**: `ctvlist_gui.py`
- **Launcher**: `Launch_CTV_List_GUI.bat`
- **Config**: Application configuration files

### Desktop Integration
- **Shortcut**: "CTV List Data Processor" on desktop
- **Context**: Properly configured working directory
- **Icon**: Python executable icon

## 🖥️ Usage Instructions

### Starting the Application

**Option 1: Desktop Shortcut**
- Double-click "CTV List Data Processor" on your desktop

**Option 2: Manual Launch**
- Navigate to the deployment package folder
- Double-click `Launch_CTV_List_GUI.bat`

### Application Workflow

1. **Material Data Tab**
   - Enter material parameters (Lot, Wafer, Program, etc.)
   - Or load from CSV/Excel file
   - Click "Create DataFrame" to proceed

2. **MTPL & Test Selection Tab**
   - Browse and load your MTPL file
   - Search and filter available tests
   - Select tests for processing

3. **Output & Processing Tab**
   - Choose output folder (default: dataOut)
   - Configure processing options
   - Start processing and monitor progress

## 🔧 Troubleshooting

### Common Issues

**❌ "Python not found" Error**
- **Solution**: Reinstall using `install.bat` as Administrator
- **Cause**: Incomplete installation or corrupted Python environment

**❌ Package Import Errors**
- **Solution**: Check internet connection and reinstall
- **Details**: Required packages: pandas, numpy, openpyxl, Pillow

**❌ Permission Denied**
- **Solution**: Run installer as Administrator
- **Cause**: Insufficient permissions to create directories

**❌ Application Won't Start**
- **Solution**: Check if all files are in the correct locations
- **Debug**: Look at the console output in the launcher window

### Advanced Troubleshooting

**Verify Installation**
```bash
# Navigate to: C:\Users\[Username]\My Programs\SQLPathFinder3\python3\
# Run: python.exe --version
# Should show: Python 3.11.0
```

**Test Package Installation**
```bash
# In the same directory, run:
# python.exe -c "import pandas, numpy, tkinter; print('All packages OK')"
```

**Reset Installation**
1. Delete `C:\Users\[Username]\My Programs\SQLPathFinder3\`
2. Delete `C:\Users\[Username]\Downloads\Scripts\_Current\`
3. Run `install.bat` again as Administrator

## 📞 Support

### Self-Help Resources
- Check error messages in the launcher console
- Verify internet connection for package downloads
- Ensure Windows is up to date

### Contact Information
- **System Administrator**: Contact your IT department
- **Application Issues**: Refer to the application documentation
- **Installation Problems**: Check Windows Event Viewer for detailed errors

## ⚙️ Technical Details

### Architecture
- **Python**: 3.11 Embedded Distribution (Portable)
- **GUI Framework**: tkinter (built-in)
- **Data Processing**: pandas, numpy
- **File Formats**: CSV, Excel (.xlsx, .xls)

### File Locations
```
C:\Users\[Username]\
├── My Programs\
│   └── SQLPathFinder3\
│       └── python3\           # Portable Python environment
├── [Deployment Folder]\       # Wherever you extracted the package
│   ├── ctvlist_gui.py        # Main application
│   ├── Launch_CTV_List_GUI.bat # Launcher script
│   └── config files...
└── Desktop\
    └── CTV List Data Processor.lnk # Desktop shortcut
```

### Network Requirements
- **Initial Setup**: ~50 MB download (Python + packages)
- **Runtime**: No network connection required
- **Updates**: Manual reinstallation required

## 📝 Version Information

- **Application**: CTV List Data Processor v1.0
- **Python Version**: 3.11.0
- **Deployment Package**: v1.0
- **Last Updated**: January 2025

## 🔄 Updates and Maintenance

### Updating the Application
1. Download new deployment package
2. Run `install.bat` (will update application files only)
3. Existing Python environment will be preserved

### Uninstalling
1. Delete desktop shortcut
2. Remove `C:\Users\[Username]\My Programs\SQLPathFinder3\`
3. Remove the deployment package folder

---

*For additional technical support, please contact your system administrator.*
