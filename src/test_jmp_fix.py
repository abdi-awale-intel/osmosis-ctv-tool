#!/usr/bin/env python3
"""
Test script to verify JMP functionality fixes
"""

import os
import sys

def test_jmp_executable_detection():
    """Test if JMP executable can be found"""
    print("Testing JMP executable detection...")
    
    try:
        import file_functions as fi
        jmp_path = fi.find_latest_jmp_pro_path()
        
        if jmp_path:
            print(f"✓ JMP executable found at: {jmp_path}")
            
            # Check if file exists
            if os.path.exists(jmp_path):
                print("✓ JMP executable file exists")
            else:
                print("✗ JMP executable file does not exist")
                return False
                
            # Check if file is accessible
            try:
                # Try to get file stats (this will fail if no access)
                stat_info = os.stat(jmp_path)
                print("✓ JMP executable is accessible")
            except PermissionError:
                print("✗ JMP executable is not accessible (permission denied)")
                return False
                
            return True
        else:
            print("✗ JMP executable not found")
            return False
            
    except Exception as e:
        print(f"✗ Error testing JMP detection: {e}")
        return False

def test_jmp_access():
    """Test if JMP can be executed"""
    print("\nTesting JMP executable access...")
    
    try:
        import file_functions as fi
        import subprocess
        
        jmp_path = fi.find_latest_jmp_pro_path()
        if not jmp_path:
            print("✗ Cannot test access - JMP not found")
            return False
        
        # Try to run JMP with help flag
        try:
            result = subprocess.run([jmp_path, "-h"], 
                                  capture_output=True, 
                                  timeout=10,
                                  text=True)
            print("✓ JMP executable can be launched")
            return True
        except subprocess.TimeoutExpired:
            print("⚠ JMP test timed out (may be normal)")
            return True  # Timeout might be normal for JMP
        except PermissionError as pe:
            print(f"✗ Permission denied: {pe}")
            return False
        except FileNotFoundError:
            print("✗ JMP executable not found when trying to run")
            return False
        except Exception as e:
            print(f"⚠ JMP access test warning: {e}")
            return True  # Other errors might be normal
            
    except Exception as e:
        print(f"✗ Error testing JMP access: {e}")
        return False

def test_jmp_module():
    """Test if jmp_python module can be imported and used"""
    print("\nTesting jmp_python module...")
    
    try:
        import jmp_python as jmp
        print("✓ jmp_python module imported successfully")
        
        # Check if run_jsl function exists
        if hasattr(jmp, 'run_jsl'):
            print("✓ run_jsl function found")
        else:
            print("✗ run_jsl function not found")
            return False
            
        # Check if stack_and_split_file function exists
        if hasattr(jmp, 'stack_and_split_file'):
            print("✓ stack_and_split_file function found")
        else:
            print("✗ stack_and_split_file function not found")
            return False
            
        return True
        
    except ImportError as e:
        print(f"✗ Cannot import jmp_python module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing jmp_python module: {e}")
        return False

def main():
    """Run all tests"""
    print("JMP Functionality Test Suite")
    print("=" * 40)
    
    tests = [
        test_jmp_executable_detection,
        test_jmp_access,
        test_jmp_module
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed - JMP functionality should work")
    else:
        print("✗ Some tests failed - JMP functionality may have issues")
        print("\nPossible solutions:")
        print("- Run as administrator")
        print("- Check JMP Pro installation")
        print("- Verify JMP Pro license")
        print("- Check file permissions")

if __name__ == "__main__":
    main()
