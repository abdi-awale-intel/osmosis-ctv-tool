import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path
import json

class CTVListDeployer:
    def __init__(self):
        self.user_home = Path.home()
        self.programs_dir = self.user_home / "My Programs"
        self.sqlpathfinder_dir = self.programs_dir / "SQLPathFinder3"
        self.python_dir = self.sqlpathfinder_dir / "python3"
        self.python_exe = self.python_dir / "python.exe"
        
        # Use deployment package directory as the target for application files
        self.deployment_dir = Path(__file__).parent.absolute()
        self.scripts_dir = self.deployment_dir
        
    def print_status(self, message, status="INFO"):
        """Print formatted status messages"""
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{icons.get(status, '📋')} [{status}] {message}")
        
    def check_sqlpathfinder_exists(self):
        """Check if SQLPathFinder3 is already installed"""
        if self.sqlpathfinder_dir.exists() and self.python_exe.exists():
            self.print_status("SQLPathFinder3 found - skipping installation", "SUCCESS")
            return True
        return False
        
    def create_directories(self):
        """Create necessary directories"""
        self.print_status("Creating directory structure...")
        try:
            self.programs_dir.mkdir(parents=True, exist_ok=True)
            self.scripts_dir.mkdir(parents=True, exist_ok=True)
            self.sqlpathfinder_dir.mkdir(parents=True, exist_ok=True)
            self.print_status("Directories created successfully", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Failed to create directories: {e}", "ERROR")
            return False
            
    def download_python_portable(self):
        """Download and setup portable Python"""
        self.print_status("Downloading Python 3.11 portable...")
        python_url = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip"
        python_zip = self.programs_dir / "python.zip"
        
        try:
            # Download with progress
            def show_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded * 100) // total_size)
                    print(f"\rDownloading... {percent}%", end="", flush=True)
                    
            urllib.request.urlretrieve(python_url, python_zip, show_progress)
            print()  # New line after progress
            self.print_status("Python downloaded successfully", "SUCCESS")
            
            # Extract Python
            self.print_status("Extracting Python...")
            with zipfile.ZipFile(python_zip, 'r') as zip_ref:
                zip_ref.extractall(self.python_dir)
            
            python_zip.unlink()  # Remove zip file
            self.print_status("Python extracted successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_status(f"Failed to download Python: {e}", "ERROR")
            return False
            
    def setup_pip(self):
        """Setup pip for the portable Python"""
        self.print_status("Setting up pip...")
        
        # Create pth file to enable site-packages
        pth_content = """import site; site.addsitedir(r'Lib\\site-packages')"""
        pth_file = self.python_dir / "python311._pth"
        
        try:
            with open(pth_file, 'w') as f:
                f.write("python311.zip\n")
                f.write(".\n")
                f.write("Lib\\site-packages\n")
                f.write("import site\n")
                
            # Create site-packages directory
            site_packages = self.python_dir / "Lib" / "site-packages"
            site_packages.mkdir(parents=True, exist_ok=True)
            
            # Download get-pip.py
            get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
            get_pip_path = self.python_dir / "get-pip.py"
            
            urllib.request.urlretrieve(get_pip_url, get_pip_path)
            
            # Install pip
            result = subprocess.run([
                str(self.python_exe), str(get_pip_path), "--no-warn-script-location"
            ], capture_output=True, text=True, cwd=str(self.python_dir))
            
            if result.returncode == 0:
                self.print_status("Pip installed successfully", "SUCCESS")
                get_pip_path.unlink()  # Remove get-pip.py
                return True
            else:
                self.print_status(f"Pip installation failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.print_status(f"Failed to setup pip: {e}", "ERROR")
            return False
            
    def install_required_packages(self):
        """Install only necessary packages for Osmosis"""
        self.print_status("Installing required packages...")
        
        # Read requirements from file
        requirements_file = Path(__file__).parent / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            # Default packages based on your GUI requirements
            packages = [
                "pandas>=1.5.0", 
                "numpy>=1.21.0", 
                "openpyxl>=3.0.0",
                "Pillow>=9.0.0"  # For PIL/Image support in Osmosis
            ]
        
        for package in packages:
            self.print_status(f"Installing {package}...")
            result = subprocess.run([
                str(self.python_exe), "-m", "pip", "install", package, "--no-warn-script-location"
            ], capture_output=True, text=True, cwd=str(self.python_dir))
            
            if result.returncode == 0:
                self.print_status(f"{package} installed successfully", "SUCCESS")
            else:
                self.print_status(f"Failed to install {package}: {result.stderr}", "ERROR")
                return False
                
        return True
        
    def copy_application_files(self):
        """Copy Osmosis and related files"""
        self.print_status("Copying application files...")
        
        # Copy main application file to the same directory as deployment script
        source_gui = self.deployment_dir / "ctvlist_gui.py"
        
        if source_gui.exists():
            self.print_status(f"Application files will run from: {self.deployment_dir}")
        else:
            self.print_status("ctvlist_gui.py not found in deployment package", "ERROR")
            return False
        
        # Copy optional resource files within the deployment directory
        optional_files = [
            ("resources/config.json", "config.json"),
        ]
        
        for source_name, dest_name in optional_files:
            source = self.deployment_dir / source_name
            destination = self.deployment_dir / dest_name
            
            if source.exists():
                if source.is_file():
                    shutil.copy2(source, destination)
                    self.print_status(f"Copied {source_name} to {destination}")
                else:
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                    self.print_status(f"Copied {source_name} directory to {destination}")
            else:
                self.print_status(f"Optional file not found: {source_name}", "WARNING")
                
        return True
        
    def create_launcher_script(self):
        """Create a launcher script for easy execution"""
        self.print_status("Creating launcher script...")
        
        launcher_content = f'''@echo off
title Osmosis
color 0A
echo.
echo   ██████╗ ███████╗███╗   ███╗ ██████╗ ███████╗██╗███████╗
echo  ██╔═══██╗██╔════╝████╗ ████║██╔═══██╗██╔════╝██║██╔════╝
echo  ██║   ██║███████╗██╔████╔██║██║   ██║███████╗██║███████╗
echo  ██║   ██║╚════██║██║╚██╔╝██║██║   ██║╚════██║██║╚════██║
echo  ╚██████╔╝███████║██║ ╚═╝ ██║╚██████╔╝███████║██║███████║
echo   ╚═════╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝╚══════╝
echo.
echo  Starting OSMOSIS...
echo  Please wait while the application loads...
echo.

cd /d "{self.deployment_dir}"
"{self.python_exe}" "{self.deployment_dir / "ctvlist_gui.py"}"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Osmosis failed to start
    echo Please check the installation and try again
    echo.
)

pause
'''
        
        launcher_path = self.deployment_dir / "Launch_Osmosis.bat"
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
            
        self.print_status(f"Launcher created: {launcher_path}", "SUCCESS")
        
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        self.print_status("Creating desktop shortcut...")
        
        try:
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "Osmosis.lnk"
            
            # Create VBS script to create shortcut
            vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{self.deployment_dir / "Launch_Osmosis.bat"}"
oLink.WorkingDirectory = "{self.deployment_dir}"
oLink.Description = "Osmosis Data Processor"
oLink.IconLocation = "{self.python_exe},0"
oLink.Save
'''
            
            vbs_file = self.deployment_dir / "create_shortcut.vbs"
            with open(vbs_file, 'w', encoding='utf-8') as f:
                f.write(vbs_content)
                
            # Execute VBS script
            subprocess.run(["cscript", "//nologo", str(vbs_file)], 
                         capture_output=True, cwd=str(self.deployment_dir))
            
            vbs_file.unlink()  # Remove VBS file
            self.print_status("Desktop shortcut created", "SUCCESS")
            
        except Exception as e:
            self.print_status(f"Could not create desktop shortcut: {e}", "WARNING")
            
    def verify_installation(self):
        """Verify the installation is working"""
        self.print_status("Verifying installation...")
        
        try:
            # Test Python executable
            result = subprocess.run([str(self.python_exe), "--version"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                self.print_status(f"Python version: {result.stdout.strip()}", "SUCCESS")
            else:
                self.print_status("Python verification failed", "ERROR")
                return False
                
            # Test required packages
            test_imports = [
                "import pandas",
                "import numpy", 
                "import tkinter",
                "import sqlite3",
                "import json",
                "import csv",
                "from PIL import Image, ImageTk"
            ]
            
            for test_import in test_imports:
                result = subprocess.run([str(self.python_exe), "-c", test_import], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    if "PIL" in test_import:
                        self.print_status(f"Optional package test failed: {test_import}", "WARNING")
                    else:
                        self.print_status(f"Package test failed: {test_import}", "ERROR")
                        return False
                    
            self.print_status("All required packages verified successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_status(f"Verification failed: {e}", "ERROR")
            return False
            
    def deploy(self):
        """Main deployment function"""
        self.print_status("Starting Osmosis deployment...")
        
        # Check if already installed
        if self.check_sqlpathfinder_exists():
            self.print_status("Existing installation found - updating application only...")
            if not self.copy_application_files():
                return False
        else:
            # Full installation
            steps = [
                ("Creating directories", self.create_directories),
                ("Downloading Python", self.download_python_portable),
                ("Setting up pip", self.setup_pip),
                ("Installing packages", self.install_required_packages),
                ("Copying application files", self.copy_application_files),
            ]
            
            for step_name, step_func in steps:
                self.print_status(f"Step: {step_name}")
                if not step_func():
                    self.print_status(f"Deployment failed at step: {step_name}", "ERROR")
                    return False
                    
        # Always create launcher and shortcuts
        self.create_launcher_script()
        self.create_desktop_shortcut()
        
        # Verify installation
        if not self.verify_installation():
            self.print_status("Installation verification failed", "ERROR")
            return False
            
        self.print_status("Deployment completed successfully!", "SUCCESS")
        self.print_status(f"Application installed to: {self.deployment_dir}", "INFO")
        self.print_status(f"Use launcher: {self.deployment_dir / 'Launch_Osmosis.bat'}", "INFO")
        
        return True

if __name__ == "__main__":
    deployer = CTVListDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n" + "="*50)
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("="*50)
        print("You can now run Osmosis using:")
        print("1. Desktop shortcut: 'Osmosis'")
        print("2. Launcher script in the deployment folder")
        print("3. Double-click: Launch_Osmosis.bat")
    else:
        print("\n" + "="*50)
        print("❌ DEPLOYMENT FAILED!")
        print("="*50)
        print("Please check the error messages above and try again.")
        
    input("\nPress Enter to exit...")
