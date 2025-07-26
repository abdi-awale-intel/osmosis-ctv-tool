# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Application details
app_name = 'Osmosis'
main_script = r'c:\Users\abdiawal\Downloads\Scripts\osmosis-ctv-tool\src\osmosis_main.py'
deployment_dir = Path(r'c:\Users\abdiawal\Downloads\Scripts\osmosis-ctv-tool\src')

# Data files to include
datas = []

# Add resource files if they exist
config_file = deployment_dir / 'config.json'
if config_file.exists():
    datas.append((str(config_file), '.'))

resources_dir = deployment_dir / 'resources'
if resources_dir.exists():
    datas.append((str(resources_dir), 'resources'))

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
    'smart_json_parser.py'
]

for module in python_modules:
    module_path = deployment_dir / module
    if module_path.exists():
        datas.append((str(module_path), '.'))

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
    'dateutil',
    'dateutil.relativedelta',
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
    'smart_json_parser'
]

# Analysis
a = Analysis(
    [main_script],
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
    icon=None,  # Add icon path here if you have one
)
