# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get paths dynamically - PyInstaller provides SPECPATH variable
try:
    # SPECPATH is provided by PyInstaller and points to the directory containing the spec file
    spec_root = Path(SPECPATH).absolute()
except NameError:
    # Fallback to current working directory if SPECPATH is not available
    spec_root = Path(os.getcwd()).absolute()

print(f"Using spec root directory: {spec_root}")

# Application details
app_name = 'Osmosis'
main_script = spec_root / 'osmosis_main.py'
deployment_dir = spec_root

# Verify main script exists
if not main_script.exists():
    print(f"ERROR: Main script not found at: {main_script}")
    sys.exit(1)

print(f"Main script: {main_script}")
print(f"Deployment directory: {deployment_dir}")

# Data files to include
datas = []

# Add resource files if they exist
config_file = deployment_dir / 'config.json'
if config_file.exists():
    datas.append((str(config_file), '.'))

resources_dir = deployment_dir / 'resources'
if resources_dir.exists():
    datas.append((str(resources_dir), 'resources'))

# *** IMPORTANT: Add images directory ***
images_dir = deployment_dir / 'images'
if images_dir.exists():
    datas.append((str(images_dir), 'images'))
    print(f"Added images directory: {images_dir}")
else:
    print(f"Warning: Images directory not found at: {images_dir}")

# Add PyUber and Uber directories
pyuber_dir = deployment_dir / 'PyUber'
if pyuber_dir.exists():
    datas.append((str(pyuber_dir), 'PyUber'))

uber_dir = deployment_dir / 'Uber'
if uber_dir.exists():
    datas.append((str(uber_dir), 'Uber'))

# Add all Python modules in deployment directory
python_modules = [
    'file_functions.py',
    'mtpl_parser.py',
    'index_ctv.py',
    'pyuber_query.py',
    'smart_json_parser.py',
    'ctvlist_gui.py'
]

for module in python_modules:
    module_path = deployment_dir / module
    if module_path.exists():
        datas.append((str(module_path), '.'))
        print(f"Added module: {module}")
    else:
        print(f"Warning: Module not found: {module}")

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'pandas',
    'numpy',
    'openpyxl',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'csv',
    'json',
    'sqlite3',
    'threading',
    'datetime',
    'time',
    're',
    'os',
    'sys',
    'pathlib',
    'subprocess',
    'dateutil',
    'dateutil.relativedelta',
    # CustomTkinter support
    'customtkinter',
    # PyUber database modules
    'PyUber',
    'PyUber.core',
    'PyUber.client',
    'PyUber.backend',
    'PyUber.exceptions',
    'PyUber.types',
    'PyUber.rows_factory',
    'PyUber._compat',
    'PyUber._uCLR',
    'PyUber._win32com',
    # Custom modules for Osmosis
    'file_functions',
    'mtpl_parser',
    'index_ctv',
    'pyuber_query',
    'smart_json_parser',
    'ctvlist_gui'
]

# Print debugging info
print("Data files being included:")
for data_item in datas:
    print(f"  {data_item[0]} -> {data_item[1]}")

# Analysis
a = Analysis(
    [str(main_script)],
    pathex=[str(deployment_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Find icon file - prioritize ICO files for Windows compatibility
icon_file = None
possible_icons = ['icon.ico', 'logo.ico', 'icon.png', 'icon.jpg', 'icon.jpeg', 'logo.png', 'logo.jpg', 'logo.jpeg']
for icon_name in possible_icons:
    icon_path = deployment_dir / 'images' / icon_name
    if icon_path.exists():
        # Only use ICO files on Windows, skip other formats if PIL not available
        if icon_name.endswith('.ico'):
            icon_file = str(icon_path)
            print(f"Using ICO icon: {icon_file}")
            break
        elif icon_name.endswith(('.png', '.jpg', '.jpeg')):
            # Try to use non-ICO files only if they exist and we can process them
            try:
                # Test if PIL is available for conversion
                from PIL import Image as PILImage
                icon_file = str(icon_path)
                print(f"Using icon with PIL conversion: {icon_file}")
                break
            except ImportError:
                print(f"Skipping {icon_name} - PIL not available for conversion")
                continue

if not icon_file:
    print("No suitable icon file found - building without icon")

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
