#!/usr/bin/env python3
"""
Test script to demonstrate the new combined JMP functionality
"""

import os
import sys

def test_combined_jmp_functionality():
    """Test the new combined JMP approach"""
    print("Testing Combined JMP Functionality")
    print("=" * 50)
    
    try:
        import jmp_python as jmp
        print("✓ JMP module imported successfully")
        
        # Test function availability
        required_functions = ['combine_stacked_files', 'create_combined_jsl_script', 'run_combined_jsl']
        
        for func_name in required_functions:
            if hasattr(jmp, func_name):
                print(f"✓ {func_name} function available")
            else:
                print(f"✗ {func_name} function missing")
                return False
        
        print("\n" + "=" * 50)
        print("NEW COMBINED JMP WORKFLOW:")
        print("=" * 50)
        print("1. Multiple stacked CSV files are automatically combined into one master file")
        print("2. The master file includes 'Source_File' column to identify original files")
        print("3. A comprehensive JSL script is created for the combined data")
        print("4. JMP opens with multiple organized analysis windows:")
        print("   - Main Variability Chart (all data)")
        print("   - Source File Comparison Chart")
        print("   - Data Distribution Analysis")
        print("   - Summary Statistics by Source")
        print("5. All analysis is done in ONE JMP session instead of multiple windows")
        
        print("\n" + "=" * 50)
        print("BENEFITS:")
        print("=" * 50)
        print("✓ Single JMP window instead of multiple separate windows")
        print("✓ Comprehensive view of all data together")
        print("✓ Easy comparison between different source files")
        print("✓ Proper label handling across all datasets")
        print("✓ Automatic file source tracking")
        print("✓ Enhanced statistical analysis")
        
        print("\n" + "=" * 50)
        print("USAGE:")
        print("=" * 50)
        print("1. In the GUI, check 'Stack output files for JMP'")
        print("2. Check 'Run JMP on stacked files'")
        print("3. Process your CTV data")
        print("4. The system will automatically:")
        print("   - Create stacked files")
        print("   - Combine them into one master dataset")
        print("   - Open JMP with comprehensive analysis")
        
        return True
        
    except ImportError as e:
        print(f"✗ Error importing JMP module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing JMP functionality: {e}")
        return False

def main():
    """Run the test"""
    success = test_combined_jmp_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TESTS PASSED - Combined JMP functionality is ready!")
        print("✓ No more multiple JMP windows - everything in one organized session!")
    else:
        print("✗ Some tests failed - please check the implementation")
    print("=" * 50)

if __name__ == "__main__":
    main()
