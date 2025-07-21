#!/bin/bash
# Build script for CTV List GUI - Git CI/CD compatible
# This script ensures consistent builds across different environments

set -e  # Exit on any error

echo "🚀 Starting CTV List GUI Build Process"
echo "======================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"

echo "📍 Script Directory: $SCRIPT_DIR"
echo "📍 Source Directory: $SRC_DIR"

# Validate environment
echo ""
echo "🔍 Validating Build Environment"
echo "==============================="

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found in PATH"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1)
echo "✅ Found: $PYTHON_VERSION"

# Check pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found in PATH"
    exit 1
fi

echo "✅ pip is available"

# Install dependencies
echo ""
echo "📦 Installing Dependencies"
echo "=========================="

# Upgrade pip first
pip install --upgrade pip

# Install requirements
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "📋 Installing from requirements.txt..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "⚠️ requirements.txt not found, installing core packages..."
    pip install pandas>=1.5.0 pillow>=9.0.0 openpyxl>=3.0.0 pyinstaller>=6.0.0
fi

# Validate critical modules
echo ""
echo "🧪 Testing Module Imports"
echo "========================="

cd "$SRC_DIR"

# Run build validator if available
if [ -f "build_validator.py" ]; then
    echo "🔍 Running build validation..."
    python build_validator.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Build validation failed"
        exit 1
    fi
else
    echo "⚠️ Build validator not found, skipping validation"
fi

# Test basic imports
python -c "
import sys
import os
sys.path.insert(0, '.')
print('Testing core imports...')

try:
    import tkinter as tk
    print('✅ tkinter imported successfully')
except ImportError as e:
    print(f'❌ tkinter import failed: {e}')
    sys.exit(1)

try:
    import pandas as pd
    print('✅ pandas imported successfully')
except ImportError as e:
    print(f'❌ pandas import failed: {e}')
    sys.exit(1)

try:
    from PIL import Image, ImageTk
    print('✅ PIL imported successfully')
except ImportError as e:
    print('⚠️ PIL import failed (optional): {e}')

print('✅ Core module test completed')
"

if [ $? -ne 0 ]; then
    echo "❌ Module import test failed"
    exit 1
fi

# Create executable
echo ""
echo "🔨 Building Executable"
echo "======================"

# Check for spec file
SPEC_FILE="$SCRIPT_DIR/ctvlist_gui.spec"
MAIN_SCRIPT="$SRC_DIR/ctvlist_gui.py"

if [ -f "$SPEC_FILE" ]; then
    echo "📋 Using PyInstaller spec file: $SPEC_FILE"
    pyinstaller "$SPEC_FILE" --clean --noconfirm
else
    echo "📋 Using default PyInstaller configuration"
    pyinstaller \
        --onefile \
        --windowed \
        --name="CTVListGUI" \
        --add-data="$SRC_DIR:." \
        --hidden-import="pandas" \
        --hidden-import="PIL" \
        --hidden-import="openpyxl" \
        --hidden-import="tkinter" \
        --clean \
        --noconfirm \
        "$MAIN_SCRIPT"
fi

# Verify build output
echo ""
echo "✅ Build Verification"
echo "===================="

DIST_DIR="$SCRIPT_DIR/dist"
EXE_NAME="CTVListGUI"

# Check for different possible executable names/locations
POSSIBLE_EXES=(
    "$DIST_DIR/$EXE_NAME.exe"
    "$DIST_DIR/$EXE_NAME"
    "$DIST_DIR/ctvlist_gui.exe"
    "$DIST_DIR/ctvlist_gui"
)

FOUND_EXE=""
for exe in "${POSSIBLE_EXES[@]}"; do
    if [ -f "$exe" ]; then
        FOUND_EXE="$exe"
        break
    fi
done

if [ -n "$FOUND_EXE" ]; then
    echo "✅ Executable created successfully: $FOUND_EXE"
    
    # Get file size
    FILE_SIZE=$(ls -lh "$FOUND_EXE" | awk '{print $5}')
    echo "📏 File size: $FILE_SIZE"
    
    # Test executable (quick startup test)
    echo "🧪 Testing executable startup..."
    timeout 10s "$FOUND_EXE" --help > /dev/null 2>&1 || true
    echo "✅ Executable startup test completed"
    
else
    echo "❌ Executable not found in expected locations:"
    for exe in "${POSSIBLE_EXES[@]}"; do
        echo "   - $exe"
    done
    
    echo ""
    echo "📁 Contents of dist directory:"
    ls -la "$DIST_DIR" 2>/dev/null || echo "   (dist directory not found)"
    
    exit 1
fi

# Create build info
echo ""
echo "📝 Creating Build Information"
echo "============================="

BUILD_INFO_FILE="$DIST_DIR/build_info.txt"
cat > "$BUILD_INFO_FILE" << EOF
CTV List GUI Build Information
==============================

Build Date: $(date)
Build Host: $(hostname)
Python Version: $(python --version 2>&1)
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Branch: $(git branch --show-current 2>/dev/null || echo "N/A")

Executable: $(basename "$FOUND_EXE")
File Size: $FILE_SIZE

Dependencies Installed:
$(pip list | grep -E "(pandas|pillow|pyinstaller|openpyxl)" || echo "N/A")

Build completed successfully!
EOF

echo "✅ Build information saved to: $BUILD_INFO_FILE"

echo ""
echo "🎉 Build Process Completed Successfully!"
echo "========================================"
echo "📦 Executable location: $FOUND_EXE"
echo "📋 Build info: $BUILD_INFO_FILE"
echo ""
echo "🚀 Ready for distribution!"
