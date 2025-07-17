# Osmosis Deployment Package

## For Deployers (Distribution Team)

### 1. Package Contents Verification
Before distributing, ensure these files are present:
```
deployment_package/
├── deploy_ctvlist.py          # Main deployment script
├── ctvlist_gui.py             # Osmosis GUI application ✅
├── requirements.txt           # Python package dependencies
├── install.bat               # Windows installer batch file
├── README.md                 # End-user instructions
├── DEPLOYMENT_INSTRUCTIONS.md # This file
└── resources/                # Additional files
    └── config.json           # Configuration file
```

### 2. Testing Before Distribution
1. **Test on Clean Machine**: Use a virtual machine or clean Windows installation
2. **Run Deployment**: Execute `install.bat` as Administrator
3. **Verify Installation**: Check that Osmosis launches successfully
4. **Test Core Functions**: Ensure material data loading and MTPL processing work

### 3. Creating Distribution Package
```bash
# Option 1: ZIP Archive
# Select the entire deployment_package folder
# Right-click → "Send to" → "Compressed (zipped) folder"
# Name it: "Osmosis_v1.0_Installer.zip"

# Option 2: Self-Extracting Archive (Advanced)
# Use 7-Zip or WinRAR to create a self-extracting executable
```

### 4. Distribution Checklist
- [ ] All required files present
- [ ] `ctvlist_gui.py` is the latest version
- [ ] Tested on clean Windows 10/11 machine
- [ ] Installation completes successfully
- [ ] Application launches without errors
- [ ] Desktop shortcut works
- [ ] Core functionality verified

## For End Users

### Quick Installation
1. **Download** the Osmosis installer package
2. **Extract** all files to a folder (e.g., `C:\Osmosis_Installer\`)
3. **Right-click** `install.bat` → **Run as Administrator**
4. **Follow** on-screen prompts
5. **Launch** Osmosis from desktop shortcut

### System Requirements
- Windows 10 or later (64-bit)
- 4 GB RAM minimum
- 500 MB free disk space
- Internet connection (for initial setup)
- Administrator privileges (for installation only)

### Installation Locations
- **Python Environment**: `C:\Users\[Username]\My Programs\SQLPathFinder3\`
- **Application Files**: Same folder as installer
- **Desktop Shortcut**: `Osmosis.lnk`

### Troubleshooting
- **"Python not found"**: Reinstall as Administrator
- **"Permission denied"**: Run installer as Administrator
- **"Package errors"**: Check internet connection
- **Application won't start**: Verify all files are present
- **"PyUber not available" warnings**: Normal behavior - database features disabled but application works
- **"NoneType uber_request" errors**: Fixed in current version - update to latest build

### Known Issues & Solutions
#### PyUber Database Dependency
- **Issue**: Some tests may show "PyUber not available" warnings
- **Impact**: Database queries are skipped, but file processing continues normally
- **Solution**: This is expected behavior when PyUber library is not installed
- **Status**: Application works in "offline mode" with reduced functionality

## Technical Notes

### Architecture
- **Portable Python 3.11**: No system Python installation required
- **Self-contained**: All dependencies included
- **Modular**: Can be deployed to any folder location
- **User-friendly**: Automated dependency management

### Security Considerations
- **Code Signing**: Consider signing the executable for enterprise deployment
- **Antivirus**: Some AV software may flag the installer (false positive)
- **Firewall**: Python.exe may require firewall exception for network features

### Customization Options
- **Python Version**: Modify URL in `deploy_ctvlist.py` line 49
- **Package Requirements**: Edit `requirements.txt`
- **Installation Path**: Modify `self.programs_dir` in deployer class
- **Branding**: Update ASCII art and application names

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Maintainer**: Development Team
