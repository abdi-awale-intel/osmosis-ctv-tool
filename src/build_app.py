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
        self.deployment_dir = Path(__file__).parent.absolute()  # src/ directory
        self.project_root = self.deployment_dir.parent.absolute()  # osmosis-ctv-tool/ directory
        self.build_dir = self.deployment_dir / "build"
        self.dist_dir = self.deployment_dir / "dist"
        self.image_dir = self.deployment_dir / "images"
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
    
    def setup_images_directory(self):
        """Setup and verify the images directory"""
        self.print_status("Setting up images directory...")
        
        # Create images directory if it doesn't exist
        if not self.image_dir.exists():
            try:
                self.image_dir.mkdir(exist_ok=True)
                self.print_status(f"Created images directory: {self.image_dir}")
            except Exception as e:
                self.print_status(f"Could not create images directory: {e}", "WARNING")
                return False
        
        # Check for expected image files
        expected_files = {
            "App Icon": ["icon.png", "icon.jpg", "icon.jpeg", "logo.png", "logo.jpg", "logo.jpeg"],
            "Light Mode Logo": ["lightmode-logo.jpg", "lightmode-logo.png", "light-logo.jpg", "light-logo.png"],
            "Dark Mode Logo": ["darkmode-logo.jpg", "darkmode-logo.png", "dark-logo.jpg", "dark-logo.png"]
        }
        
        found_files = {}
        missing_categories = []
        
        for category, files in expected_files.items():
            found = False
            for filename in files:
                if (self.image_dir / filename).exists():
                    found_files[category] = filename
                    found = True
                    self.print_status(f"Found {category}: {filename}", "SUCCESS")
                    break
            if not found:
                missing_categories.append(category)
                self.print_status(f"Missing {category} (expected: {', '.join(files)})", "WARNING")
        
        if missing_categories:
            self.print_status(f"Missing image categories: {', '.join(missing_categories)}", "WARNING")
            self.print_status("The application will use text-based fallbacks for missing images.", "INFO")
        
        return True
            
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
        """Create PyInstaller spec file with proper images support"""
        self.print_status("Creating PyInstaller spec file...")
        
        spec_file_path = self.deployment_dir / f"{self.app_name.lower()}.spec"
        
        # Check if spec file already exists
        if spec_file_path.exists():
            self.print_status(f"Spec file already exists: {spec_file_path}", "WARNING")
            
            # In interactive mode, ask user what to do
            if sys.stdin.isatty():
                while True:
                    choice = "o"
                    if choice in ['o', 'overwrite']:
                        self.print_status("Overwriting existing spec file...", "INFO")
                        break
                    elif choice in ['u', 'use', 'existing']:
                        self.print_status("Using existing spec file", "SUCCESS")
                        return spec_file_path
                    elif choice in ['b', 'backup']:
                        # Create backup
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_path = self.deployment_dir / f"{self.app_name.lower()}_backup_{timestamp}.spec"
                        shutil.copy2(spec_file_path, backup_path)
                        self.print_status(f"Backed up existing spec to: {backup_path}", "SUCCESS")
                        break
                    else:
                        print("Please enter 'o' for overwrite, 'u' for use existing, or 'b' for backup")
            else:
                # Non-interactive mode (CI/CD) - create backup automatically
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.deployment_dir / f"{self.app_name.lower()}_backup_{timestamp}.spec"
                shutil.copy2(spec_file_path, backup_path)
                self.print_status(f"Automatically backed up existing spec to: {backup_path}", "INFO")
        
        # Find icon file for the executable
        icon_file = None
        possible_icons = ["icon.png", "icon.jpg", "icon.jpeg", "logo.png", "logo.jpg", "logo.jpeg"]
        for icon_name in possible_icons:
            icon_path = self.image_dir / icon_name
            if icon_path.exists():
                icon_file = str(icon_path)
                break
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

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

print(f"Using spec root directory: {{spec_root}}")

# Application details
app_name = '{self.app_name}'
main_script = spec_root / 'osmosis_main.py'
deployment_dir = spec_root

# Verify main script exists
if not main_script.exists():
    print(f"ERROR: Main script not found at: {{main_script}}")
    sys.exit(1)

print(f"Main script: {{main_script}}")
print(f"Deployment directory: {{deployment_dir}}")

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
    print(f"Added images directory: {{images_dir}}")
else:
    print(f"Warning: Images directory not found at: {{images_dir}}")

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
        print(f"Added module: {{module}}")
    else:
        print(f"Warning: Module not found: {{module}}")

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
    print(f"  {{data_item[0]}} -> {{data_item[1]}}")

# Analysis
a = Analysis(
    [str(main_script)],
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

# Find icon file
icon_file = None
possible_icons = ['icon.png', 'icon.jpg', 'icon.jpeg', 'logo.png', 'logo.jpg', 'logo.jpeg']
for icon_name in possible_icons:
    icon_path = deployment_dir / 'images' / icon_name
    if icon_path.exists():
        icon_file = str(icon_path)
        print(f"Using icon: {{icon_file}}")
        break

if not icon_file:
    print("No icon file found")

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
'''
        
        spec_file_path = self.deployment_dir / f"{self.app_name.lower()}.spec"
        with open(spec_file_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
            
        self.print_status(f"Spec file created: {spec_file_path}", "SUCCESS")
        if icon_file:
            self.print_status(f"Using icon: {icon_file}", "SUCCESS")
        else:
            self.print_status("No icon file found", "WARNING")
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
echo   ########  ##### #     # ####### ##### ##### #####
echo  #        #       ##   ## #      #      #     #    
echo  #        #       # # # # #      #      #     #    
echo  #        #       #  #  # #####  #####  #     ##### 
echo  #        #       #     # #      #      #         #
echo  #        #       #     # #      #      #         #
echo   ########  ##### #     # ####### ##### ##### ##### 
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
if exist "images" xcopy "images" "%INSTALL_DIR%\\images\\" /E /I /Q >nul

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
        # These files are in the project root (parent directory)
        files_to_copy = [
            # (source_path, dest_name, description)
            (self.project_root / "config.json", "config.json", "Configuration file"),
            (self.project_root / "resources", "resources", "Resources directory"),
            (self.project_root / "README.md", "README.md", "Documentation"),
            (self.project_root / "PyUber", "PyUber", "PyUber directory"),
            (self.project_root / "Uber", "Uber", "Uber directory"),
            (self.deployment_dir / "images", "images", "Images directory")  # Images are in src/
        ]
        
        for source_path, dest_name, description in files_to_copy:
            dest = self.dist_dir / dest_name
            
            if source_path.exists():
                if source_path.is_file():
                    shutil.copy2(source_path, dest)
                    self.print_status(f"Copied {description}: {source_path.name}")
                else:
                    shutil.copytree(source_path, dest, dirs_exist_ok=True)
                    self.print_status(f"Copied {description}: {source_path.name}/")
            else:
                self.print_status(f"Source not found: {source_path}", "WARNING")
                    
        self.print_status("Distribution packaging completed", "SUCCESS")
        
    def build_app(self):
        """Main build function"""
        self.print_status(f"Starting {self.app_name} application build...")
        
        # Check for command line arguments
        use_existing_spec = '--use-existing-spec' in sys.argv or '--use-spec' in sys.argv
        force_spec_creation = '--force-spec' in sys.argv or '--force' in sys.argv
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        # Setup images directory
        if not self.setup_images_directory():
            self.print_status("Continuing without complete image setup...", "WARNING")
            
        # Clean previous builds
        self.clean_build_dirs()
        
        # Create main script
        main_script_path = self.create_main_script()
        
        # Handle spec file creation
        spec_file_path = self.deployment_dir / f"{self.app_name.lower()}.spec"
        
        if use_existing_spec and spec_file_path.exists():
            self.print_status(f"Using existing spec file: {spec_file_path}", "INFO")
        elif spec_file_path.exists() and not force_spec_creation:
            self.print_status(f"Spec file exists: {spec_file_path}", "WARNING")
            if sys.stdin.isatty():
                choice = 'N'
                if choice in ['y', 'yes']:
                    self.print_status("Using existing spec file", "INFO")
                else:
                    # Create spec file (will handle overwrite prompts internally)
                    spec_file_path = self.create_spec_file(main_script_path)
            else:
                # Non-interactive mode - use existing
                self.print_status("Using existing spec file (non-interactive mode)", "INFO")
        else:
            # Create spec file
            spec_file_path = self.create_spec_file(main_script_path)
            
        if not spec_file_path or not spec_file_path.exists():
            self.print_status("No valid spec file available", "ERROR")
            return False
        
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
    print("🔧 Osmosis Application Builder")
    print("=" * 50)
    
    # Show usage information if help requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python build_app.py [options]")
        print()
        print("Options:")
        print("  --use-existing-spec    Use existing spec file without prompting")
        print("  --force-spec          Force creation of new spec file")
        print("  --force               Same as --force-spec")
        print("  --help, -h            Show this help message")
        print()
        print("Examples:")
        print("  python build_app.py                    # Interactive mode")
        print("  python build_app.py --use-existing-spec  # Use existing spec")
        print("  python build_app.py --force-spec        # Always create new spec")
        sys.exit(0)
    
    builder = OsmosisAppBuilder()
    success = builder.build_app()
    
    if success:
        try:
            print("\\n" + "="*60)
            print("[+] APPLICATION BUILD SUCCESSFUL!")
            print("="*60)
            print("Your Osmosis application is ready for distribution!")
            print()
            print("Distribution files located in: dist/")
            print("- Osmosis.exe          (Main application)")
            print("- Install_Osmosis.bat  (Installer script)")
            print("- README.md            (Documentation)")
            print("- config.json          (Configuration)")
            print("- images/              (Application images and icons)")
            print()
            print("To distribute:")
            print("1. Zip the entire 'dist' folder")
            print("2. Share with end users")
            print("3. Users run 'Install_Osmosis.bat' to install")
        except UnicodeEncodeError:
            print("\\n" + "="*60)
            print("[+] APPLICATION BUILD SUCCESSFUL!")
            print("="*60)
            print("Your Osmosis application is ready for distribution!")
    else:
        try:
            print("\\n" + "="*60)
            print("[!] APPLICATION BUILD FAILED!")
            print("="*60)
            print("Please check the error messages above and try again.")
        except UnicodeEncodeError:
            print("\\n" + "="*60)
            print("[!] APPLICATION BUILD FAILED!")
            print("="*60)
            print("Please check the error messages above and try again.")
        
    # Only prompt for input if running interactively (not in CI/CD)
    if sys.stdin.isatty():
        input("\\nPress Enter to exit...")
    else:
        print("\\nBuild process completed.")