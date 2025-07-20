#!/usr/bin/env python3
"""
Test script to validate all imports work correctly
"""

def test_imports():
    """Test all critical imports"""
    results = []
    
    # Test basic imports
    try:
        import tkinter as tk
        results.append("✅ tkinter imported successfully")
    except Exception as e:
        results.append(f"❌ tkinter import failed: {e}")
    
    try:
        import pandas as pd
        results.append("✅ pandas imported successfully")
    except Exception as e:
        results.append(f"❌ pandas import failed: {e}")
    
    # Test PyUber module
    try:
        import pyuber_query
        results.append("✅ pyuber_query imported successfully")
    except Exception as e:
        results.append(f"❌ pyuber_query import failed: {e}")
    
    # Test main GUI module
    try:
        import ctvlist_gui
        results.append("✅ ctvlist_gui imported successfully")
    except Exception as e:
        results.append(f"❌ ctvlist_gui import failed: {e}")
    
    # Test other modules
    try:
        import file_functions
        results.append("✅ file_functions imported successfully")
    except Exception as e:
        results.append(f"❌ file_functions import failed: {e}")
    
    try:
        import mtpl_parser
        results.append("✅ mtpl_parser imported successfully")
    except Exception as e:
        results.append(f"❌ mtpl_parser import failed: {e}")
    
    try:
        import smart_json_parser
        results.append("✅ smart_json_parser imported successfully")
    except Exception as e:
        results.append(f"❌ smart_json_parser import failed: {e}")
    
    return results

if __name__ == "__main__":
    print("Starting import validation tests...")
    print("=" * 50)
    
    test_results = test_imports()
    
    for result in test_results:
        print(result)
    
    print("=" * 50)
    
    # Count successes and failures
    successes = sum(1 for r in test_results if r.startswith("✅"))
    failures = sum(1 for r in test_results if r.startswith("❌"))
    
    print(f"Summary: {successes} successful imports, {failures} failed imports")
    
    if failures == 0:
        print("🎉 All imports successful! Ready to build.")
    else:
        print("⚠️ Some imports failed. Please fix before building.")
