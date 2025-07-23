# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CTV List GUI
This ensures proper bundling of all dependencies for Git builds
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = spec_dir if os.path.basename(spec_dir) == 'src' else os.path.join(spec_dir, 'src')

# Define the main script
main_script = os.path.join(src_dir, 'ctvlist_gui.py')

# Collect all custom modules
custom_modules = ['file_functions', 'mtpl_parser', 'index_ctv', 'smart_json_parser']
hidden_imports = []
datas = []

# Add custom modules to hidden imports
for module in custom_modules:
    module_path = os.path.join(src_dir, f'{module}.py')
    if os.path.exists(module_path):
        hidden_imports.append(module)
        print(f"✅ Found custom module: {module}")
    else:
        print(f"⚠️ Custom module not found: {module}")

# Collect PyUber if available
pyuber_path = os.path.join(os.path.dirname(src_dir), 'pyuber_query.py')
if os.path.exists(pyuber_path):
    hidden_imports.append('pyuber_query')
    print(f"✅ Found PyUber module: {pyuber_path}")

# Collect data files (images, etc.)
images_dir = os.path.join(src_dir, 'images')
if os.path.exists(images_dir):
    datas.append((images_dir, 'images'))
    print(f"✅ Including images directory: {images_dir}")

# Collect pandas and other package data
pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all('pandas')
datas.extend(pandas_datas)
hidden_imports.extend(pandas_hiddenimports)

# Tkinter data
try:
    tkinter_datas, tkinter_binaries, tkinter_hiddenimports = collect_all('tkinter')
    datas.extend(tkinter_datas)
    hidden_imports.extend(tkinter_hiddenimports)
except:
    print("⚠️ Could not collect tkinter data")

# Pillow data
try:
    pillow_datas, pillow_binaries, pillow_hiddenimports = collect_all('PIL')
    datas.extend(pillow_datas)
    hidden_imports.extend(pillow_hiddenimports)
except:
    print("⚠️ Could not collect PIL data")

# Additional hidden imports for common modules
additional_hidden_imports = [
    'numpy',
    'openpyxl',
    'xlsxwriter',
    'dateutil',
    'chardet',
    'csv',
    'json',
    'base64',
    'io',
    'threading',
    'traceback',
    'datetime',
    'time',
    're',
    'os',
    'sys'
]

hidden_imports.extend(additional_hidden_imports)

# Remove duplicates
hidden_imports = list(set(hidden_imports))

print(f"📦 Hidden imports: {hidden_imports}")
print(f"📁 Data files: {[d[1] for d in datas]}")

block_cipher = None

a = Analysis(
    [main_script],
    pathex=[src_dir, os.path.dirname(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CTVListGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for debugging, False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(src_dir, 'images', 'logo.ico') if os.path.exists(os.path.join(src_dir, 'images', 'logo.ico')) else None
)
