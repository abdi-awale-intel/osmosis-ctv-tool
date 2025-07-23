# Updated PyInstaller spec file for Python 3.13.1
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the directory containing this spec file
spec_dir = Path(__file__).parent

# Determine if we're running from src directory
if spec_dir.name == 'src':
    project_root = spec_dir.parent
    src_dir = spec_dir
else:
    project_root = spec_dir
    src_dir = spec_dir / "src"

block_cipher = None

# Custom module detection for Python 3.13.1
def find_custom_modules():
    """Find all custom modules in the project"""
    custom_modules = []
    
    # Look for Python files in src directory
    if src_dir.exists():
        for py_file in src_dir.glob("*.py"):
            if py_file.name not in ["__init__.py", "ctvlist_gui.py"]:
                module_name = py_file.stem
                custom_modules.append(module_name)
    
    # Look for Python files in root directory
    for py_file in project_root.glob("*.py"):
        if py_file.name not in ["setup.py", "build_validator.py", "build_validator_python3131.py"]:
            module_name = py_file.stem
            custom_modules.append(module_name)
    
    return custom_modules

# Find data files
def find_data_files():
    """Find all data files to include"""
    data_files = []
    
    # Include images directory if it exists - EXPLICIT INCLUSION
    images_dir = src_dir / "images"
    if images_dir.exists():
        print(f"Found images directory: {images_dir}")
        for img_file in images_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                rel_path = img_file.relative_to(src_dir)
                data_files.append((str(img_file), str(rel_path.parent)))
                print(f"Adding image: {img_file} -> {rel_path.parent}")
    
    # Also add explicit image files (backup)
    image_files = [
        'logo.png', 'logo.jpg', 'logo.jpeg',
        'lightmode-logo.png', 'lightmode-logo.jpg',
        'light-logo.png', 'light-logo.jpg',
        'darkmode-logo.png', 'dark-logo.png', 'dark-logo.jpg'
    ]
    
    for img_name in image_files:
        img_path = images_dir / img_name
        if img_path.exists():
            data_files.append((str(img_path), 'images'))
            print(f"Explicitly adding: {img_name}")
    
    # Include any config files
    for config_file in ["config.json", "settings.ini", "*.cfg"]:
        config_path = project_root / config_file
        if config_path.exists():
            data_files.append((str(config_path), "."))
    
    return data_files

# Get custom modules and data files
custom_modules = find_custom_modules()
data_files = find_data_files()

print(f"Found custom modules: {custom_modules}")
print(f"Found data files: {data_files}")

# Hidden imports for Python 3.13.1 compatibility
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'pandas',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'openpyxl',
    'numpy',
    'sys',
    'os',
    'pathlib',
    'base64',
    'io',
    'traceback',
] + custom_modules

# Main analysis
a = Analysis(
    [str(src_dir / 'ctvlist_gui.py')],
    pathex=[str(project_root), str(src_dir)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicates and unnecessary files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ctvlist_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/logo.ico' if (spec_dir / 'images' / 'logo.ico').exists() else None,
    version_file=None,
)

# Optional: Create distribution directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ctvlist_gui_dist',
)
