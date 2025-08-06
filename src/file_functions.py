import csv
import json
import os
import sys
import re
import winreg
import pandas as pd

def txt_to_list(file_path):
    """Read entries from a text file where each entry is separated by a newline."""
    with open(file_path, 'r') as file:
        entries = file.read().splitlines()
    return entries

def csv_to_list(file_path, column_name):
    """Read entries from a CSV file where each cell in a specified column is an entry."""
    df = pd.read_csv(file_path)
    entries = df[column_name].tolist()
    return entries

def xls_to_list(file_path, sheet_name, column_name):
    """Read entries from an Excel file where each cell in a specified column is an entry."""
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    entries = df[column_name].tolist()
    return entries

def test_input_to_list(file_path, column_name=None, sheet_name=None):
    """Read entries from a file, automatically detecting the file type."""
    _, file_extension = os.path.splitext(file_path)

    if file_extension.lower() == '.txt':
        return txt_to_list(file_path)
    elif file_extension.lower() == '.csv':
        if column_name is None:
            raise ValueError("Column name must be specified for CSV files.")
        return csv_to_list(file_path, column_name)
    elif file_extension.lower() in ['.xls', '.xlsx']:
        if column_name is None or sheet_name is None:
            raise ValueError("Both column name and sheet name must be specified for Excel files.")
        return xls_to_list(file_path, sheet_name, column_name)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def check_write_permission(file_name):
    suffix = 0
    while True:
        try:
            file = open(file_name,'w',newline='')
            file.close()
            return(file_name)
        except PermissionError:
            suffix += 1
            file_name = file_name.replace('_copy','')
            temp_list = file_name.split('.')
            temp_list[-2] = temp_list[-2]+f'_copy{suffix}'
            file_name = '.'.join(temp_list)

def process_file_input(input_string):
    """Process user input to remove quotes and normalize paths while preserving UNC paths."""
    # Remove surrounding quotes
    if input_string.startswith('"') and input_string.endswith('"'):
        input_string = input_string[1:-1]
    elif input_string.startswith("'") and input_string.endswith("'"):
        input_string = input_string[1:-1]
    
    # Check if it's a UNC path before processing
    is_unc = input_string.startswith('\\\\')
    
    # Handle escape sequences but avoid corrupting UNC paths
    if '\\' in input_string and not is_unc:
        # Only encode escape sequences for non-UNC paths
        raw_input = input_string.encode('unicode_escape').decode('utf-8')
    else:
        # For UNC paths, just use the input as-is
        raw_input = input_string
    
    # Normalize path while preserving UNC format
    if is_unc:
        # For UNC paths, manually normalize to avoid os.path.normpath corruption
        # Strip all leading backslashes and add exactly 2
        stripped_path = raw_input.lstrip('\\')
        # Replace multiple consecutive backslashes with single ones (except the leading \\)
        normalized_path = '\\\\' + stripped_path.replace('\\\\', '\\')
        return normalized_path
    else:
        # For regular paths, use standard normalization
        return os.path.normpath(raw_input)

def get_file_extension(file_path):
    """Return the file extension of the given file path."""
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower()

def get_module_name(file_path):
    #Grab first slash index around Module name
    first_bslash_index = file_path.find('Modules\\')
    first_fslash_index = file_path.find('/Modules')
    first_slash_index = 0
    if first_fslash_index != -1:
        first_slash_index = first_fslash_index + len('/Modules')
    else:
        first_slash_index = first_bslash_index + len('Modules\\')
    #Grab second slash index around Module name        
    next_slash_index = 0
    next_bslash_index = file_path.find('\\', first_slash_index+1)
    next_fslash_index = file_path.find('/', first_slash_index+1)
    if next_fslash_index == -1 or next_bslash_index ==-1:
        next_slash_index = max(next_bslash_index,next_fslash_index)
    else:
        next_slash_index = min(next_bslash_index,next_fslash_index)
    #Module name contained in file path
    module_name = file_path[first_slash_index:next_slash_index]
    return(module_name)

def delete_files(file_list):
    for file in file_list:
        try:
            os.remove(file)
            print(f"{file} has been deleted.")
        except FileNotFoundError:
            print(f"File {file} not found, skipping deletion.")
        except Exception as e:
            print(f"An error occurred while deleting {file}: {e}")

def find_latest_jmp_pro_path():
    locations = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
    ]
    
    latest_version = 0
    latest_install_location = None
    
    for location in locations:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, location)
            
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                
                try:
                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    for version in range(14, 20):
                        if f"JMP Pro {version}" in display_name:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            if version > latest_version:
                                latest_version = version
                                latest_install_location = install_location
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(subkey)
            
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass
    
    # Return the full path to the JMP executable, not just the install directory
    if latest_install_location:
        jmp_exe_path = os.path.join(latest_install_location, "jmp.exe")
        if os.path.exists(jmp_exe_path):
            return jmp_exe_path
        # Try alternative paths
        jmp_exe_path = os.path.join(latest_install_location, "bin", "jmp.exe")
        if os.path.exists(jmp_exe_path):
            return jmp_exe_path
    
    # Fallback: try common installation paths
    common_paths = [
        r"C:\Program Files\SAS\JMPPRO\18\jmp.exe",
        r"C:\Program Files\SAS\JMPPRO\17\jmp.exe",
        r"C:\Program Files\SAS\JMPPRO\16\jmp.exe",
        r"C:\Program Files\SAS\JMPPRO\15\jmp.exe",
        r"C:\Program Files (x86)\SAS\JMPPRO\18\jmp.exe",
        r"C:\Program Files (x86)\SAS\JMPPRO\17\jmp.exe",
        r"C:\Program Files (x86)\SAS\JMPPRO\16\jmp.exe",
        r"C:\Program Files (x86)\SAS\JMPPRO\15\jmp.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None