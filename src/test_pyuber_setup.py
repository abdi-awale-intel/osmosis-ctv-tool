#!/usr/bin/env python3
"""
PyUber Connectivity Test Script

This script tests PyUber module availability and database connectivity.
Use this to diagnose PyUber-related issues in the Osmosis CTV Tool.
"""

import sys
import os

def test_pyuber_import():
    """Test if PyUber module can be imported"""
    print("=" * 60)
    print("🧪 PYUBER MODULE IMPORT TEST")
    print("=" * 60)
    
    try:
        # Add parent directory to path (same as main application)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            print(f"📁 Added to Python path: {parent_dir}")
        
        # Try importing PyUber directly
        print("🔄 Attempting to import PyUber...")
        import PyUber
        print("✅ PyUber imported successfully!")
        
        # Get PyUber information
        if hasattr(PyUber, '__version__'):
            print(f"📦 PyUber version: {PyUber.__version__}")
        else:
            print("📦 PyUber version: Unknown")
            
        if hasattr(PyUber, '__file__'):
            print(f"📍 PyUber location: {PyUber.__file__}")
        else:
            print("📍 PyUber location: Unknown")
            
        return True
        
    except ImportError as e:
        print(f"❌ PyUber import failed: {e}")
        print("\n🔍 Searching for PyUber in system paths...")
        
        # Search for PyUber in common locations
        search_paths = [
            os.path.join(sys.prefix, 'Lib', 'site-packages'),
            os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages'),
            'C:\\PyUber',
            'C:\\Program Files\\PyUber',
            os.path.expanduser('~/PyUber'),
        ]
        
        found = False
        for path in search_paths:
            pyuber_path = os.path.join(path, 'PyUber')
            if os.path.exists(pyuber_path):
                print(f"🎯 Found PyUber directory at: {pyuber_path}")
                found = True
        
        if not found:
            print("❌ PyUber not found in standard locations")
            
        return False

def test_pyuber_query_module():
    """Test if pyuber_query module can be imported"""
    print("\n" + "=" * 60)
    print("🧪 PYUBER_QUERY MODULE TEST")
    print("=" * 60)
    
    try:
        print("🔄 Attempting to import pyuber_query...")
        import pyuber_query as py
        print("✅ pyuber_query imported successfully!")
        
        # Test PyUber status
        if hasattr(py, 'get_pyuber_status'):
            status = py.get_pyuber_status()
            print(f"📊 PyUber Status: {status}")
        
        if hasattr(py, 'PYUBER_AVAILABLE'):
            print(f"🔗 PyUber Available: {py.PYUBER_AVAILABLE}")
        
        return True
        
    except ImportError as e:
        print(f"❌ pyuber_query import failed: {e}")
        return False

def test_database_connection():
    """Test database connection if PyUber is available"""
    print("\n" + "=" * 60)
    print("🧪 DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        import pyuber_query as py
        
        if hasattr(py, 'test_pyuber_connection'):
            # Test default databases
            databases = ['D1D_PROD_XEUS', 'F24_PROD_XEUS']
            
            for db in databases:
                print(f"\n🔗 Testing connection to {db}...")
                try:
                    success = py.test_pyuber_connection(db)
                    if success:
                        print(f"✅ {db} connection successful")
                    else:
                        print(f"❌ {db} connection failed")
                except Exception as e:
                    print(f"❌ {db} connection error: {e}")
        else:
            print("⚠️ test_pyuber_connection function not available")
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")

def print_system_info():
    """Print system information for debugging"""
    print("\n" + "=" * 60)
    print("🖥️ SYSTEM INFORMATION")
    print("=" * 60)
    
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Python executable: {sys.executable}")
    print(f"📚 Python path entries:")
    for i, path in enumerate(sys.path[:10], 1):  # Show first 10 paths
        print(f"   {i}. {path}")
    if len(sys.path) > 10:
        print(f"   ... and {len(sys.path) - 10} more paths")

def print_installation_guide():
    """Print PyUber installation guide"""
    print("\n" + "=" * 60)
    print("📋 PYUBER INSTALLATION GUIDE")
    print("=" * 60)
    
    print("""
🔧 If PyUber is not available, try these steps:

1. 📦 Install via pip (if available):
   pip install PyUber

2. 🏢 Contact System Administrator:
   PyUber may require special installation or configuration
   by your IT department or database administrator

3. 🔍 Check Custom Locations:
   PyUber might be installed in a custom directory
   that needs to be added to your Python path

4. 🔌 Alternative Database Drivers:
   If PyUber is not available, consider using:
   - pyodbc (for SQL Server)
   - cx_Oracle (for Oracle)
   - psycopg2 (for PostgreSQL)

5. 🆘 Get Help:
   - Check with your database team
   - Review internal documentation
   - Contact the Osmosis CTV Tool maintainer
""")

def main():
    """Main test function"""
    print("🧪 OSMOSIS CTV TOOL - PYUBER DIAGNOSTIC SCRIPT")
    print("This script will test PyUber connectivity for the Osmosis application")
    
    # System information
    print_system_info()
    
    # Test PyUber import
    pyuber_direct = test_pyuber_import()
    
    # Test pyuber_query module
    pyuber_query_works = test_pyuber_query_module()
    
    # Test database connection if modules work
    if pyuber_direct and pyuber_query_works:
        test_database_connection()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"PyUber Direct Import: {'✅ PASS' if pyuber_direct else '❌ FAIL'}")
    print(f"pyuber_query Module: {'✅ PASS' if pyuber_query_works else '❌ FAIL'}")
    
    if pyuber_direct and pyuber_query_works:
        print("🎉 PyUber setup appears to be working!")
        print("   The Osmosis CTV Tool should be able to connect to databases.")
    else:
        print("⚠️ PyUber setup has issues.")
        print("   Database features in Osmosis CTV Tool may not work.")
        print_installation_guide()

if __name__ == "__main__":
    main()
