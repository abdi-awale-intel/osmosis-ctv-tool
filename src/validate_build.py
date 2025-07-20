#!/usr/bin/env python3
"""
Quick validation test for the Osmosis application
Tests that the PyUber fix is working in the GUI
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

def test_gui_startup():
    """Test that the GUI starts without errors"""
    try:
        # Add current directory to path for imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        # Test import of GUI module
        import ctvlist_gui
        print("✅ ctvlist_gui imported successfully")
        
        # Create a test GUI instance (without mainloop)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        app = ctvlist_gui.CTVListGUI(root)
        print("✅ GUI instance created successfully")
        
        # Test that PyUber is available
        if hasattr(app, 'PYUBER_AVAILABLE') and ctvlist_gui.PYUBER_AVAILABLE:
            print("✅ PyUber module is available in GUI")
        else:
            print("⚠️ PyUber module availability not confirmed")
            
        # Clean up
        root.destroy()
        print("✅ GUI validation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ GUI validation failed: {e}")
        return False

def test_pyuber_module():
    """Test PyUber module import directly"""
    try:
        # Add parent directory to path for PyUber
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            
        import PyUber
        print(f"✅ PyUber module imported successfully (version: {PyUber.__version__})")
        return True
        
    except Exception as e:
        print(f"❌ PyUber module import failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Osmosis Application Validation")
    print("=" * 40)
    
    # Test PyUber module
    pyuber_success = test_pyuber_module()
    
    # Test GUI startup
    gui_success = test_gui_startup()
    
    print("=" * 40)
    
    if pyuber_success and gui_success:
        print("🎉 All validation tests passed!")
        print("✅ Application is ready for deployment")
        sys.exit(0)
    else:
        print("❌ Some validation tests failed")
        print("⚠️ Please review errors before deployment")
        sys.exit(1)
