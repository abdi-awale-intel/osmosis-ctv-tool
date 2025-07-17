import csv
import json
import os
import sys
import re
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
   #Process user input to remove quotes and encode escape sequences as literal characters.
    if input_string.startswith('"') and input_string.endswith('"'):
        input_string = input_string[1:-1]
    elif input_string.startswith("'") and input_string.endswith("'"):
        input_string = input_string[1:-1]
    # Encode escape sequences as literal characters
    raw_input = input_string.encode('unicode_escape').decode('utf-8')
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

