#!/usr/bin/env python3
"""
Build Validation Script for CTV List GUI
This script helps identify differences between local and Git builds
"""

import sys
import os
import importlib
import traceback

def validate_build_environment():
    """Validate the build environment and identify potential issues"""
    print("=" * 80)
    print("🔍 CTV LIST GUI BUILD VALIDATION")
    print("=" * 80)
    
    # Basic environment info
    print(f"📍 Python Version: {sys.version}")
    print(f"📍 Python Executable: {sys.executable}")
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"📍 Script Location: {os.path.abspath(__file__)}")
    
    # Check if we're in PyInstaller
    if hasattr(sys, '_MEIPASS'):
        print(f"📦 PyInstaller Bundle: {sys._MEIPASS}")
        bundle_contents = os.listdir(sys._MEIPASS)
        print(f"📂 Bundle Contents: {bundle_contents[:10]}..." if len(bundle_contents) > 10 else bundle_contents)
    else:
        print("🐍 Development Mode")
    
    print("\n" + "=" * 80)
    print("📚 REQUIRED MODULES CHECK")
    print("=" * 80)
    
    # List of required modules for the application
    required_modules = [
        'tkinter',
        'pandas', 
        'PIL',
        'file_functions',
        'mtpl_parser',
        'index_ctv',
        'smart_json_parser',
        'pyuber_query'
    ]
    
    module_status = {}
    
    for module_name in required_modules:
        try:
            if module_name == 'tkinter':
                import tkinter
                print(f"✅ {module_name}: Available")
                module_status[module_name] = True
            elif module_name == 'pandas':
                import pandas
                print(f"✅ {module_name}: Available (version: {pandas.__version__})")
                module_status[module_name] = True
            elif module_name == 'PIL':
                from PIL import Image, ImageTk
                print(f"✅ {module_name}: Available")
                module_status[module_name] = True
            else:
                # Try to import custom modules
                spec = importlib.util.find_spec(module_name)
                if spec is not None:
                    module = importlib.import_module(module_name)
                    print(f"✅ {module_name}: Available")
                    module_status[module_name] = True
                else:
                    print(f"❌ {module_name}: Not found")
                    module_status[module_name] = False
        except ImportError as e:
            print(f"❌ {module_name}: Import error - {e}")
            module_status[module_name] = False
        except Exception as e:
            print(f"⚠️ {module_name}: Unexpected error - {e}")
            module_status[module_name] = False
    
    print("\n" + "=" * 80)
    print("📁 FILE SYSTEM CHECK")
    print("=" * 80)
    
    # Check for required files and directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    important_paths = [
        ("Current Directory", current_dir),
        ("Parent Directory", parent_dir),
        ("Images Directory", os.path.join(current_dir, "images")),
        ("PyUber Directory", os.path.join(parent_dir, "pyuber_query.py")),
    ]
    
    for name, path in important_paths:
        if os.path.exists(path):
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: {path} (NOT FOUND)")
    
    print("\n" + "=" * 80)
    print("🎯 BUILD VALIDATION SUMMARY")
    print("=" * 80)
    
    critical_missing = []
    optional_missing = []
    
    critical_modules = ['tkinter', 'pandas']
    
    for module, available in module_status.items():
        if not available:
            if module in critical_modules:
                critical_missing.append(module)
            else:
                optional_missing.append(module)
    
    if critical_missing:
        print(f"🚨 CRITICAL ISSUES: {critical_missing}")
        print("   → These modules are required for basic functionality")
        return False
    
    if optional_missing:
        print(f"⚠️ OPTIONAL ISSUES: {optional_missing}")
        print("   → These modules provide enhanced functionality but app can run without them")
    
    if not critical_missing and not optional_missing:
        print("✅ ALL MODULES AVAILABLE - Build should work correctly")
        return True
    
    print("✅ CORE MODULES AVAILABLE - App should start but with limited functionality")
    return True

def test_gui_startup():
    """Test if the GUI can start properly"""
    print("\n" + "=" * 80)
    print("🚀 GUI STARTUP TEST")
    print("=" * 80)
    
    try:
        # Test basic tkinter functionality
        import tkinter as tk
        test_root = tk.Tk()
        test_root.withdraw()  # Hide the window
        test_root.title("Build Test")
        
        # Test if we can create basic widgets
        test_frame = tk.Frame(test_root)
        test_label = tk.Label(test_frame, text="Test")
        test_button = tk.Button(test_frame, text="Test")
        
        print("✅ Basic Tkinter widgets created successfully")
        
        # Clean up
        test_root.destroy()
        print("✅ GUI startup test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ GUI startup test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting build validation...")
    
    # Run validation
    env_ok = validate_build_environment()
    gui_ok = test_gui_startup()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL RESULT")
    print("=" * 80)
    
    if env_ok and gui_ok:
        print("✅ BUILD VALIDATION PASSED")
        print("   → Application should run correctly")
        sys.exit(0)
    elif env_ok:
        print("⚠️ BUILD VALIDATION PARTIAL")
        print("   → Application should start but may have limited functionality")
        sys.exit(0)
    else:
        print("❌ BUILD VALIDATION FAILED")
        print("   → Application may not start correctly")
        sys.exit(1)
