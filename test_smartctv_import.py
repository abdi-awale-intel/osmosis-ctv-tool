import subprocess
import os

# Test the SmartCTV import status in the executable
print("Testing SmartCTV functionality in Osmosis executable...")

# Create a simple test script to check import status
test_script = '''
import sys
print("Python executable:", sys.executable)
print("Python path:", sys.path[:3])

# Test the import exactly as done in ctvlist_gui.py
SMART_CTV_AVAILABLE = False
sm = None

try:
    # Try relative import first (for packaged executable)
    from . import smart_json_parser as sm
    # Test that the module actually has the required function
    if hasattr(sm, 'process_SmartCTV'):
        SMART_CTV_AVAILABLE = True
        print("✅ SmartCTV module loaded successfully (relative import)")
    else:
        sm = None
        print("⚠️ SmartCTV module found but missing required functions (relative import)")
except ImportError as e:
    print(f"❌ Relative import failed: {e}")
    try:
        # Try direct import (for development environment)
        import smart_json_parser as sm
        if hasattr(sm, 'process_SmartCTV'):
            SMART_CTV_AVAILABLE = True
            print("✅ SmartCTV module loaded successfully (direct import)")
        else:
            sm = None
            print("⚠️ SmartCTV module found but missing required functions (direct import)")
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")
        try:
            # Try importing from src directory
            import src.smart_json_parser as sm
            if hasattr(sm, 'process_SmartCTV'):
                SMART_CTV_AVAILABLE = True
                print("✅ SmartCTV module loaded successfully (src import)")
            else:
                sm = None
                print("⚠️ SmartCTV module found but missing required functions (src import)")
        except ImportError as e:
            print(f"❌ Src import failed: {e}")
            sm = None
            SMART_CTV_AVAILABLE = False
            print("❌ SmartCTV functionality not available - all import methods failed")

# Final validation
if SMART_CTV_AVAILABLE and sm is not None:
    try:
        # Test that we can actually access the function
        func = getattr(sm, 'process_SmartCTV', None)
        if func is None:
            SMART_CTV_AVAILABLE = False
            sm = None
            print("❌ SmartCTV process_SmartCTV function not found, disabling SmartCTV")
        else:
            print(f"✅ SmartCTV fully validated and ready")
    except Exception as e:
        print(f"❌ SmartCTV validation failed: {e}")
        SMART_CTV_AVAILABLE = False
        sm = None
        
print(f"🔧 Final SmartCTV status: Available={SMART_CTV_AVAILABLE}, Module={sm is not None}")
'''

# Write test script to file
with open('smartctv_test.py', 'w') as f:
    f.write(test_script)

print("✅ SmartCTV test script created: smartctv_test.py")
print("Now you can run this with the Osmosis executable to test import status")
