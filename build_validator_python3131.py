#!/usr/bin/env python3
"""
Python 3.13.1 Build Environment Validator
Validates that the build environment is properly configured for Python 3.13.1
"""

import sys
import os
import platform
import subprocess
import importlib.util
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_status(message, status="INFO"):
    """Print a status message with formatting"""
    symbols = {
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def check_python_version():
    """Check if Python 3.13.1 is being used"""
    print_header("Python Version Check")
    
    version_info = sys.version_info
    version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    print_status(f"Python executable: {sys.executable}")
    print_status(f"Python version: {sys.version}")
    print_status(f"Version tuple: {version_string}")
    
    if version_info[:3] == (3, 13, 1):
        print_status("Python 3.13.1 confirmed!", "SUCCESS")
        return True
    else:
        expected = "3.13.1"
        print_status(f"Expected Python {expected}, found {version_string}", "ERROR")
        return False

def check_required_modules():
    """Check if all required modules are available"""
    print_header("Required Modules Check")
    
    required_modules = [
        'tkinter',
        'pandas',
        'PIL',
        'openpyxl',
        'PyInstaller',
    ]
    
    optional_modules = [
        'numpy',
        'matplotlib',
        'seaborn'
    ]
    
    all_good = True
    
    print("Checking required modules:")
    for module in required_modules:
        try:
            spec = importlib.util.find_spec(module)
            if spec is not None:
                print_status(f"{module}: Available", "SUCCESS")
            else:
                print_status(f"{module}: Not found", "ERROR")
                all_good = False
        except ImportError:
            print_status(f"{module}: Import error", "ERROR")
            all_good = False
    
    print("\nChecking optional modules:")
    for module in optional_modules:
        try:
            spec = importlib.util.find_spec(module)
            if spec is not None:
                print_status(f"{module}: Available", "SUCCESS")
            else:
                print_status(f"{module}: Not available (optional)", "WARNING")
        except ImportError:
            print_status(f"{module}: Not available (optional)", "WARNING")
    
    return all_good

def check_custom_modules():
    """Check if custom project modules are available"""
    print_header("Custom Modules Check")
    
    custom_modules = [
        'file_functions',
        'mtpl_parser',
        'index_ctv',
        'smart_json_parser',
        'pyuber_query'
    ]
    
    # Add src directory to path for module discovery
    src_dir = Path(__file__).parent / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    available_count = 0
    for module in custom_modules:
        try:
            spec = importlib.util.find_spec(module)
            if spec is not None:
                print_status(f"{module}: Available", "SUCCESS")
                available_count += 1
            else:
                print_status(f"{module}: Not found", "WARNING")
        except ImportError:
            print_status(f"{module}: Import error", "WARNING")
    
    print_status(f"Custom modules available: {available_count}/{len(custom_modules)}")
    return available_count > 0

def check_build_tools():
    """Check if build tools are available"""
    print_header("Build Tools Check")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print_status(f"PyInstaller: {PyInstaller.__version__}", "SUCCESS")
    except ImportError:
        print_status("PyInstaller: Not available", "ERROR")
        return False
    
    # Check if PyInstaller command works
    try:
        result = subprocess.run(['pyinstaller', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_status(f"PyInstaller command: {result.stdout.strip()}", "SUCCESS")
        else:
            print_status("PyInstaller command: Failed", "ERROR")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_status("PyInstaller command: Not available in PATH", "ERROR")
        return False
    
    return True

def check_file_structure():
    """Check if required files are present"""
    print_header("File Structure Check")
    
    required_files = [
        'src/ctvlist_gui.py',
        'requirements.txt',
    ]
    
    optional_files = [
        'ctvlist_gui.spec',
        'images/',
        'build_validator.py',
        'README.md'
    ]
    
    base_path = Path(__file__).parent
    
    print("Required files:")
    all_required_present = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print_status(f"{file_path}: Present", "SUCCESS")
        else:
            print_status(f"{file_path}: Missing", "ERROR")
            all_required_present = False
    
    print("\nOptional files:")
    for file_path in optional_files:
        full_path = base_path / file_path
        if full_path.exists():
            print_status(f"{file_path}: Present", "SUCCESS")
        else:
            print_status(f"{file_path}: Not found", "WARNING")
    
    return all_required_present

def check_environment():
    """Check environment variables and settings"""
    print_header("Environment Check")
    
    print_status(f"Platform: {platform.platform()}")
    print_status(f"Architecture: {platform.architecture()}")
    print_status(f"Current working directory: {os.getcwd()}")
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual environment: Active", "SUCCESS")
        print_status(f"Virtual env path: {sys.prefix}")
    else:
        print_status("Virtual environment: Not detected", "WARNING")
    
    # Check PATH
    python_in_path = any(Path(p) / "python.exe" for p in os.environ.get('PATH', '').split(os.pathsep))
    if python_in_path:
        print_status("Python in PATH: Yes", "SUCCESS")
    else:
        print_status("Python in PATH: No", "WARNING")

def test_gui_import():
    """Test if GUI can be imported"""
    print_header("GUI Import Test")
    
    try:
        # Add src to path
        src_dir = Path(__file__).parent / "src"
        if src_dir.exists() and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        
        # Try to import the GUI module
        import ctvlist_gui
        print_status("GUI module import: Success", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"GUI module import failed: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"GUI module import error: {e}", "ERROR")
        return False

def main():
    """Main validation function"""
    print_header("Python 3.13.1 Build Environment Validator")
    print_status(f"Validation started at: {platform.node()}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Modules", check_required_modules),
        ("Custom Modules", check_custom_modules),
        ("Build Tools", check_build_tools),
        ("File Structure", check_file_structure),
        ("Environment", check_environment),
        ("GUI Import", test_gui_import),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_status(f"{check_name} check failed: {e}", "ERROR")
            results[check_name] = False
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "SUCCESS" if result else "ERROR"
        print_status(f"{check_name}: {'PASS' if result else 'FAIL'}", status)
    
    print_status(f"Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("Build environment is ready for Python 3.13.1!", "SUCCESS")
        return 0
    else:
        print_status("Build environment has issues that need to be addressed", "ERROR")
        return 1

if __name__ == "__main__":
    exit(main())
