#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify CTV List Data Processor dependencies
Run this script to check if all required modules are properly installed
"""

import sys
import traceback
import os

# Ensure UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    # Set UTF-8 encoding for Windows console output
    import codecs
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    # Fallback for older Python versions
    elif hasattr(sys.stdout, 'encoding'):
        if sys.stdout.encoding.lower() != 'utf-8':
            os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_module(module_name, import_statement=None):
    """Test if a module can be imported successfully"""
    try:
        if import_statement:
            exec(import_statement)
        else:
            __import__(module_name)
        print(f"[OK] {module_name}: Available")
        return True
    except ImportError as e:
        print(f"[MISSING] {module_name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {module_name}: {e}")
        return False

def main():
    """Test all required dependencies"""
    print("CTV List Data Processor - Dependency Check")
    print("=" * 50)
    
    # Core Python modules (should always be available)
    core_modules = [
        ("sys", None),
        ("os", None),
        ("pathlib", None),
        ("traceback", None),
        ("base64", None),
        ("io", None),
    ]
    
    # GUI modules
    gui_modules = [
        ("tkinter", None),
        ("tkinter.ttk", "import tkinter.ttk"),
        ("tkinter.filedialog", "import tkinter.filedialog"),
        ("tkinter.messagebox", "import tkinter.messagebox"),
    ]
    
    # Data processing modules
    data_modules = [
        ("pandas", None),
        ("numpy", None),
        ("openpyxl", None),
        ("xlsxwriter", None),
    ]
    
    # Image processing modules (critical for logo display)
    image_modules = [
        ("PIL", None),
        ("PIL.Image", "from PIL import Image"),
        ("PIL.ImageTk", "from PIL import ImageTk"),
    ]
    
    # Optional modules
    optional_modules = [
        ("pyinstaller", None),
    ]
    
    success_count = 0
    total_count = 0
    
    print("\n[CORE] Core Python modules:")
    for module, import_stmt in core_modules:
        if test_module(module, import_stmt):
            success_count += 1
        total_count += 1
    
    print("\n[GUI] GUI modules:")
    for module, import_stmt in gui_modules:
        if test_module(module, import_stmt):
            success_count += 1
        total_count += 1
    
    print("\n[DATA] Data processing modules:")
    for module, import_stmt in data_modules:
        if test_module(module, import_stmt):
            success_count += 1
        total_count += 1
    
    print("\n[IMAGE] Image processing modules:")
    for module, import_stmt in image_modules:
        if test_module(module, import_stmt):
            success_count += 1
        total_count += 1
    
    print("\n[OPTIONAL] Optional modules:")
    for module, import_stmt in optional_modules:
        test_module(module, import_stmt)
    
    print("\n" + "=" * 50)
    print(f"[SUMMARY] {success_count}/{total_count} required modules available")
    
    # Test specific functionality
    print("\n[TESTS] Functionality Tests:")
    
    # Test tkinter window creation
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("[OK] tkinter GUI: Working")
    except Exception as e:
        print(f"[ERROR] tkinter GUI: {e}")
    
    # Test PIL image processing
    try:
        from PIL import Image
        # Create a small test image
        img = Image.new('RGB', (10, 10), color='red')
        print("[OK] PIL Image processing: Working")
    except Exception as e:
        print(f"[ERROR] PIL Image processing: {e}")
    
    # Test pandas DataFrame
    try:
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        print("[OK] pandas DataFrame: Working")
    except Exception as e:
        print(f"[ERROR] pandas DataFrame: {e}")
    
    print("\n[INSTALL] Installation Instructions:")
    if success_count < total_count:
        print("Some required modules are missing. To install:")
        print("pip install -r requirements.txt")
        print("\nFor tkinter issues:")
        print("Windows/Mac: Reinstall Python from python.org")
        print("Linux: sudo apt install python3-tk")
    else:
        print("[SUCCESS] All required dependencies are installed!")
        print("You can run the CTV List Data Processor with:")
        print("python ctvlist_gui.py")

if __name__ == "__main__":
    main()
