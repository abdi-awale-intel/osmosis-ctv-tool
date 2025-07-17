#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Osmosis Application Builder
Creates a standalone executable from the deployment package
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

# Fix encoding issues for GitHub Actions Windows runner
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for stdout
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # Fallback for older Python versions or restricted environments
        pass

class OsmosisAppBuilder:
    def __init__(self):
        self.deployment_dir = Path(__file__).parent.absolute()
        self.build_dir = self.deployment_dir / "build"
        self.dist_dir = self.deployment_dir / "dist"
        self.app_name = "Osmosis"
        
    def print_status(self, message, status="INFO"):
        """Print formatted status messages with ASCII fallback for GitHub Actions"""
        # Use ASCII characters for better compatibility with Windows cp1252 encoding
        icons = {
            "INFO": "[i]", 
            "SUCCESS": "[+]", 
            "ERROR": "[!]", 
            "WARNING": "[?]"
        }
        try:
            print(f"{icons.get(status, '[*]')} [{status}] {message}")
        except UnicodeEncodeError:
            # Fallback to ASCII-only output
            print(f"[{status}] {message}")
        
    def check_requirements(self):
        """Check if PyInstaller is available"""
        self.print_status("Checking build requirements...")
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.print_status("PyInstaller not found. Installing...", "WARNING")
                return self.install_pyinstaller()
            else:
                self.print_status("PyInstaller found", "SUCCESS")
                return True
        except Exception as e:
            self.print_status(f"Error checking PyInstaller: {e}", "ERROR")
            return False
            
    def install_pyinstaller(self):
        """Install PyInstaller"""
        try:
            self.print_status("Installing PyInstaller...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.print_status("PyInstaller installed successfully", "SUCCESS")
                return True
            else:
                self.print_status(f"Failed to install PyInstaller: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.print_status(f"Error installing PyInstaller: {e}", "ERROR")
            return False
            
    def create_main_script(self):
        """Create the main application script"""
        self.print_status("Creating main application script...")
        
        main_script_content = '''#!/usr/bin/env python3
"""
Osmosis - Data Processing Application
Main entry point for the standalone application
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(app_dir))

# Import and run the GUI
try:
    # Check if running as a bundled executable
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        os.chdir(bundle_dir)
        sys.path.insert(0, str(bundle_dir))
    else:
        # Running as a script
        os.chdir(app_dir)
        sys.path.insert(0, str(app_dir))
    
    # Import the main GUI module
    import ctvlist_gui
    
    # Create and run the GUI
    import tkinter as tk
    
    if __name__ == "__main__":
        root = tk.Tk()
        # Update title to reflect Osmosis branding
        root.title("Osmosis - Data Processing Application")
        app = ctvlist_gui.CTVListGUI(root)
        root.mainloop()
        
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    messagebox.showerror("Import Error", 
                        f"Failed to import required modules:\\n{str(e)}\\n\\n"
                        "Please ensure all dependencies are installed.\\n\\n"
                        f"Python path: {sys.path}\\n"
                        f"Working directory: {os.getcwd()}")
    sys.exit(1)
    
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    messagebox.showerror("Application Error", 
                        f"An error occurred while starting Osmosis:\\n{str(e)}\\n\\n"
                        f"Working directory: {os.getcwd()}")
    sys.exit(1)
'''
        
        main_script_path = self.deployment_dir / "osmosis_main.py"
        with open(main_script_path, 'w', encoding='utf-8') as f:
            f.write(main_script_content)
            
        self.print_status(f"Main script created: {main_script_path}", "SUCCESS")
        return main_script_path
        
    def create_spec_file(self, main_script_path):
        """Create PyInstaller spec file"""
        self.print_status("Creating PyInstaller spec file...")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Application details
app_name = '{self.app_name}'
main_script = r'{main_script_path}'
deployment_dir = Path(r'{self.deployment_dir}')

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
    hooksconfig={{}},
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
'''
        
        spec_file_path = self.deployment_dir / f"{self.app_name.lower()}.spec"
        with open(spec_file_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        self.print_status(f"Spec file created: {spec_file_path}", "SUCCESS")
        return spec_file_path
        
    def clean_build_dirs(self):
        """Clean previous build directories"""
        self.print_status("Cleaning previous build files...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.print_status(f"Removed {dir_path}")
                
    def build_executable(self, spec_file_path):
        """Build the executable using PyInstaller"""
        self.print_status("Building executable with PyInstaller...")
        
        try:
            # Build command
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                str(spec_file_path)
            ]
            
            self.print_status(f"Running: {' '.join(cmd)}")
            
            # Run PyInstaller
            result = subprocess.run(cmd, cwd=str(self.deployment_dir), 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_status("Executable built successfully", "SUCCESS")
                return True
            else:
                self.print_status(f"Build failed: {result.stderr}", "ERROR")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            self.print_status(f"Error during build: {e}", "ERROR")
            return False
            
    def create_installer_script(self):
        """Create a simple installer script"""
        self.print_status("Creating installer script...")
        
        installer_content = f'''@echo off
title {self.app_name} Installer
color 0B

echo.
echo   ██████╗ ███████╗███╗   ███╗ ██████╗ ███████╗██╗███████╗
echo  ██╔═══██╗██╔════╝████╗ ████║██╔═══██╗██╔════╝██║██╔════╝
echo  ██║   ██║███████╗██╔████╔██║██║   ██║███████╗██║███████╗
echo  ██║   ██║╚════██║██║╚██╔╝██║██║   ██║╚════██║██║╚════██║
echo  ╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝███████║██║███████║
echo   ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝╚══════╝
echo.
echo  {self.app_name} Installer
echo  ========================
echo.

set "INSTALL_DIR=%USERPROFILE%\\Desktop\\{self.app_name}"

echo This will install {self.app_name} to: %INSTALL_DIR%
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Installation cancelled.
    pause
    exit /b
)

echo.
echo Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying application files...
copy "{self.app_name}.exe" "%INSTALL_DIR%\\" >nul
if exist "config.json" copy "config.json" "%INSTALL_DIR%\\" >nul
if exist "resources" xcopy "resources" "%INSTALL_DIR%\\resources\\" /E /I /Q >nul

echo Creating desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{self.app_name}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{self.app_name}.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '{self.app_name} Data Processor'; $Shortcut.Save()"

echo.
echo ================================
echo Installation completed successfully!
echo ================================
echo.
echo {self.app_name} has been installed to: %INSTALL_DIR%
echo Desktop shortcut created: {self.app_name}.lnk
echo.
echo You can now launch {self.app_name} from:
echo 1. Desktop shortcut
echo 2. Installation folder: %INSTALL_DIR%\\{self.app_name}.exe
echo.

pause
'''
        
        installer_path = self.dist_dir / "Install_Osmosis.bat"
        with open(installer_path, 'w', encoding='utf-8') as f:
            f.write(installer_content)
            
        self.print_status(f"Installer script created: {installer_path}", "SUCCESS")
        
    def package_distribution(self):
        """Package the distribution files"""
        self.print_status("Packaging distribution...")
        
        # Copy additional files to dist directory
        files_to_copy = [
            ("config.json", "config.json"),
            ("resources", "resources"),
            ("README.md", "README.md"),
            ("PyUber", "PyUber"),
            ("Uber", "Uber")
        ]
        
        for source_name, dest_name in files_to_copy:
            source = self.deployment_dir / source_name
            dest = self.dist_dir / dest_name
            
            if source.exists():
                if source.is_file():
                    shutil.copy2(source, dest)
                    self.print_status(f"Copied {source_name}")
                else:
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    self.print_status(f"Copied {source_name} directory")
                    
        self.print_status("Distribution packaging completed", "SUCCESS")
        
    def build_app(self):
        """Main build function"""
        self.print_status(f"Starting {self.app_name} application build...")
        
        # Check requirements
        if not self.check_requirements():
            return False
            
        # Clean previous builds
        self.clean_build_dirs()
        
        # Create main script
        main_script_path = self.create_main_script()
        
        # Create spec file
        spec_file_path = self.create_spec_file(main_script_path)
        
        # Build executable
        if not self.build_executable(spec_file_path):
            return False
            
        # Create installer
        self.create_installer_script()
        
        # Package distribution
        self.package_distribution()
        
        # Final status
        exe_path = self.dist_dir / f"{self.app_name}.exe"
        if exe_path.exists():
            self.print_status("Build completed successfully!", "SUCCESS")
            self.print_status(f"Executable: {exe_path}", "INFO")
            self.print_status(f"Distribution: {self.dist_dir}", "INFO")
            return True
        else:
            self.print_status("Build completed but executable not found", "ERROR")
            return False

if __name__ == "__main__":
    builder = OsmosisAppBuilder()
    success = builder.build_app()
    
    if success:
        print("\\n" + "="*60)
        print("🎉 APPLICATION BUILD SUCCESSFUL!")
        print("="*60)
        print("Your Osmosis application is ready for distribution!")
        print()
        print("Distribution files located in: dist/")
        print("- Osmosis.exe          (Main application)")
        print("- Install_Osmosis.bat  (Installer script)")
        print("- README.md            (Documentation)")
        print("- config.json          (Configuration)")
        print()
        print("To distribute:")
        print("1. Zip the entire 'dist' folder")
        print("2. Share with end users")
        print("3. Users run 'Install_Osmosis.bat' to install")
    else:
        print("\\n" + "="*60)
        print("❌ APPLICATION BUILD FAILED!")
        print("="*60)
        print("Please check the error messages above and try again.")
        
    input("\\nPress Enter to exit...")
