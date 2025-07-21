# CTV List GUI - Build Troubleshooting Guide

This guide helps resolve differences between local builds and Git CI/CD builds.

## 🚨 Common Git Build Issues

### Issue 1: Module Import Errors
**Symptoms:** Application crashes on startup with `ImportError` or `ModuleNotFoundError`

**Causes:**
- Custom modules not found in PyInstaller bundle
- Missing Python path configuration
- Different module resolution in CI environment

**Solutions:**
1. Run the build validator: `python src/build_validator.py`
2. Check that all custom modules are in the `src/` directory
3. Ensure PyInstaller spec file includes all custom modules
4. Verify `requirements.txt` contains all dependencies

### Issue 2: Column Access Errors
**Symptoms:** `KeyError` or `IndexError` when processing MTPL data

**Causes:**
- Hardcoded column indices vs. dynamic column names
- Different data file formats between environments

**Solutions:**
- ✅ **FIXED**: Replaced hardcoded column indices with robust column name lookup
- Use the diagnostic button in the GUI to inspect actual column structure
- Check data files have expected column names

### Issue 3: Resource/Image Loading Failures
**Symptoms:** Missing icons, logos, or GUI elements

**Causes:**
- Image files not bundled with executable
- Path resolution differences between dev and bundled environments

**Solutions:**
- ✅ **FIXED**: Added fallback image handling and embedded base64 images
- Images directory automatically included in PyInstaller bundle
- Fallback to text-based UI elements when images unavailable

### Issue 4: PyUber/Database Connection Errors
**Symptoms:** Database connection failures or PyUber module errors

**Causes:**
- PyUber module not available in Git build environment
- Database drivers missing

**Solutions:**
- ✅ **FIXED**: Added comprehensive fallback handling for missing PyUber
- Application shows clear error messages when PyUber unavailable
- Core functionality works without PyUber (limited features)

## 🔧 Build Environment Setup

### For Git CI/CD (Automated Builds)

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Build Validation:**
   ```bash
   python src/build_validator.py
   ```

3. **Build with PyInstaller:**
   ```bash
   # Using spec file (recommended)
   pyinstaller ctvlist_gui.spec --clean --noconfirm
   
   # Or using build script
   ./build.sh  # Linux/Mac
   build.bat   # Windows
   ```

### For Local Development

1. **Ensure all modules are in src/ directory:**
   - `file_functions.py`
   - `mtpl_parser.py`
   - `index_ctv.py`
   - `smart_json_parser.py`
   - `pyuber_query.py` (optional)

2. **Test locally before pushing:**
   ```bash
   cd src/
   python ctvlist_gui.py
   ```

## 🛠️ Troubleshooting Tools

### 1. Build Validator (`src/build_validator.py`)
Checks module availability and environment setup:
```bash
python src/build_validator.py
```

### 2. Diagnostic Button in GUI
- Click "Run Diagnostics" in the Output tab
- Shows actual column structure and module status
- Helps identify runtime issues

### 3. Enhanced Logging
- All imports now show success/failure messages
- Startup diagnostics show environment info
- Error messages include specific failure reasons

## 📋 Build Configuration Files

### 1. `requirements.txt`
- Lists all Python package dependencies
- Ensures consistent package versions
- Updated with all necessary packages

### 2. `ctvlist_gui.spec` (PyInstaller Configuration)
- Defines how to bundle the application
- Includes all custom modules and data files
- Optimized for Git build environments

### 3. Build Scripts
- `build.sh` - Linux/Mac automated build
- `build.bat` - Windows automated build
- Handle dependency installation and validation

## 🏥 Quick Diagnosis Steps

If the Git build fails but local build works:

1. **Check Module Availability:**
   ```bash
   python src/build_validator.py
   ```

2. **Compare Environments:**
   - Local Python version vs. CI Python version
   - Local package versions vs. CI package versions
   - Available custom modules

3. **Test Minimal Import:**
   ```python
   # Test this in both environments
   import sys
   sys.path.append('src')
   import ctvlist_gui  # Should not crash
   ```

4. **Check PyInstaller Bundle:**
   ```bash
   # After build, check bundle contents
   pyinstaller --log-level DEBUG ctvlist_gui.spec
   ```

## 🔄 Key Fixes Applied

### ✅ Column Access (CRITICAL)
- Replaced `row.iloc[0]`, `row.iloc[1]`, etc. with robust column name lookup
- Added fallback to index if column names not found
- Handles missing or reordered columns gracefully

### ✅ Module Import Fallbacks
- All custom modules have try/catch import blocks
- Clear error messages when modules unavailable
- Application continues with limited functionality

### ✅ Resource Loading
- Embedded base64 images as fallback
- Multiple path resolution strategies
- Graceful degradation to text-based UI

### ✅ Error Reporting
- Comprehensive startup diagnostics
- Enhanced logging throughout application
- Build validation tools

### ✅ Path Resolution
- Works in both development and PyInstaller environments
- Proper handling of `sys._MEIPASS`
- Cross-platform compatibility

## 📞 Support

If issues persist:

1. Run `python src/build_validator.py` and share output
2. Check the diagnostic output from the GUI
3. Compare local vs. Git build logs
4. Verify all files are committed to Git repository

The application is now much more robust and should work consistently across different build environments.
