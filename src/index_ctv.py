"""
CTV (Circuit Test Vehicle) Indexing and Processing Module

This module processes CTV decoder CSV files and generates indexed versions for test execution.
It handles token replacement, sorting, indexing, and field concatenation to create structured
test files that can be used in circuit test vehicle workflows.

Main Features:
- Process CTV decoder CSV files with token replacement
- Generate indexed test sequences with unique identifiers
- Handle placeholder substitution in test names and tokens
- Create concatenated field strings for test parameter organization
- Support for multiple test configuration modes (CtvTag, standard)
- Automatic file naming and output management

Key Functions:
- process_CTV(): Core CSV processing with token handling
- index_CTV(): Main orchestration function for CTV indexing workflow
- replace_placeholders(): Cross-column placeholder substitution
- get_columns_btwn_index_name(): Column extraction utility

Author: Intel CTV Tool Team
Date: 2025
"""

import csv                          # CSV file reading and writing operations
import subprocess                   # Process execution (not currently used)
import os                          # Operating system interface for file operations
import sys                         # System-specific parameters and functions
import re                          # Regular expression operations for pattern matching
import xml.etree.ElementTree as ET # XML parsing (not currently used)
import pandas as pd                # Data manipulation and analysis library
import time                        # Time-related functions (not currently used)
import file_functions as fi        # Custom file handling utilities

def process_CTV(csv_input_file, log_file, test_name_prefix, MAX_VALUE_PRINT=1433):
    """
    Process CTV decoder CSV file and generate indexed log file with token replacement.
    
    This function is the core processing engine that reads a CTV decoder CSV file,
    performs token replacement, sorts by tokens, and generates an indexed output
    file suitable for test execution. It handles various token types and creates
    unique test instance names.
    
    Args:
        csv_input_file (str): Path to input CTV decoder CSV file
        log_file (str): Path for output log CSV file
        test_name_prefix (str): Prefix for generated test names
        MAX_VALUE_PRINT (int, optional): Maximum value limit (legacy parameter, defaults to 1433)
        
    Returns:
        None: Function creates output file as side effect
        
    Side Effects:
        - Creates or overwrites log_file with processed data
        - Modifies file numbering if log_file already exists
        
    Note:
        The function automatically detects whether to use 'ItuffToken' or 'StorageToken'
        based on what's available in the CSV columns.
    """
    # Normalize and validate the input file path using utility function
    csv_input_file = fi.process_file_input(csv_input_file)
    
    # Handle log file naming conflicts by adding incremental suffixes
    if not os.path.exists(log_file):
        log_file = log_file  # Use original name if file doesn't exist
    else:
        # Split filename and extension for incremental naming
        base, ext = os.path.splitext(log_file)
        i = 1
        log_file = f"{base}_{i}{ext}"  # Create numbered version
        
    # Continue incrementing until we find an unused filename
    while os.path.exists(log_file):
        i += 1
        log_file = f"{base}_{i}{ext}"
        
    # Read the entire CSV file into memory for processing
    with open(csv_input_file, mode='r') as file:
        reader = csv.DictReader(file)  # Use DictReader for column name access
        rows = list(reader)  # Convert to list for multiple iterations
        
    # Extract CSV headers for dynamic column processing
    available_columns = rows[0].keys()  # Get all column names from first row
    header_names = list(available_columns)  # Convert to list for indexing
    
    # Find tag header names between 'Pin' and 'Size' columns
    # This extracts the relevant test parameter columns for processing
    counter = 0
    for i in range(len(header_names)):
        if header_names[i] == 'Size':  # Stop when we reach 'Size' column
            break
        counter = counter + 1
        
    # Extract columns between index 1 (after Pin) and Size column
    tag_header_names = header_names[1:counter]  # LEAVE THIS IN - critical for functionality

    # Auto-detect which token column is available in the CSV
    # Different CTV files may use different token column names
    token_key = "ItuffToken"  # Default token type
    if 'ItuffToken' in available_columns:
        token_key = 'ItuffToken'  # Preferred token type
    elif 'StorageToken' in available_columns:
        token_key = 'StorageToken'  # Alternative token type
        
    # Apply placeholder replacement to every token in all rows
    # This resolves cross-column references like <ColumnName> with actual values
    for row in rows:
        original_value = row[token_key]  # Get current token value
        new_value = replace_placeholders(original_value, row)  # Replace placeholders
        row[token_key] = new_value  # Update the row with processed value
    
    # Sort all rows by token value for consistent output ordering
    # This ensures that tests with similar tokens are grouped together
    rows = sorted(rows, key=lambda row: row[token_key])

    # Create the output log file with indexed test instances
    with open(log_file, mode='w', newline='') as file:
        # Define output CSV structure with Index column first
        fieldnames = ['Index']  # Start with Index column for test instance numbering
        
        # Add all tag header columns dynamically from input CSV
        for i in range(len(tag_header_names)): 
            fieldnames.append(f"{tag_header_names[i]}")
            
        # Add Name column last for test instance identification
        fieldnames.append('Name')
        
        # Create CSV writer with defined field structure
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write column headers to file

        # Dictionary to track occurrence count for each unique test name
        # This enables multiple instances of the same test with different indices
        token_occurrence_count = {}
        
        # Process each row and create indexed test instances
        for row in rows:
            # Handle special cases for different test types based on test name prefix
            # Skip rows with empty/dash tokens for specific test types
            
            # Special handling for CLK test types - skip rows with dash tokens
            if row[token_key] == '-' and "CLK" in test_name_prefix.upper():
                continue  # Skip this row for CLK tests
                
            # Special handling for MIO_DDR test types - skip empty/dash tokens
            if row[token_key] == '' or row[token_key] == '-' and "MIO_DDR" in test_name_prefix.upper():
                continue  # Skip this row for MIO_DDR tests
                
            # Generate test name based on token availability
            elif row[token_key] == '' or row[token_key] == '-':
                # Use only prefix when no valid token is available
                test_name = f"{test_name_prefix}"  
            else:
                # Combine prefix with token for unique test identification
                test_name = f"{test_name_prefix + '_' + row[token_key]}"                
            
            # Track occurrence count and get current index for this test name
            # This allows multiple instances of the same test configuration
            if test_name not in token_occurrence_count:
                token_occurrence_count[test_name] = 0  # Initialize counter
            current_index = token_occurrence_count[test_name]  # Get current count
            
            # Create output row dictionary with Index and Name
            row_dict = {'Index': current_index, 'Name': test_name}
                
            # Add all tag header values dynamically from input row
            for i in range(len(tag_header_names)):
                row_dict[f"{tag_header_names[i]}"] = row[tag_header_names[i]]
                
            # Write the completed row to output file
            writer.writerow(row_dict)
            
            # Increment the occurrence count for this test name
            token_occurrence_count[test_name] += 1
            
    return  # Function completes by creating log file 
def ingest_input(input_file):
    """
    Read CSV file and separate headers from data rows.
    
    This is a utility function that reads a CSV file and returns the column names
    separately from the data rows. It's used for legacy compatibility but the
    main processing now uses pandas DictReader.
    
    Args:
        input_file (str): Path to CSV file to read
        
    Returns:
        tuple: (names, input_data) where:
            - names: List of column header names
            - input_data: List of data rows (excluding header)
            
    Note:
        This function is marked as legacy - modern processing uses pandas DataFrame operations.
    """
    input_data = []  # Initialize list to store data rows
    
    # Read CSV file line by line
    with open(input_file, "r") as file:
        reader = csv.reader(file)  # Create CSV reader object
        
        # Process each line with line number tracking
        for line_number, row in enumerate(reader):
            if line_number == 0:
                names = row  # First row contains column names
            else:
                input_data.append(row)  # All other rows are data
                
    return names, input_data  # Return separated headers and data

def replace_placeholders(field_value, row):
    """
    Replace placeholders in field values with corresponding values from the same row.
    
    This function finds placeholder patterns like <ColumnName> in a field value
    and replaces them with the actual value from the specified column in the
    current row. This enables dynamic cross-column references in CTV files.
    
    Args:
        field_value (str): Field value that may contain placeholders like <ColumnName>
        row (dict): Dictionary representing current CSV row with column names as keys
        
    Returns:
        str: Field value with all placeholders replaced by actual column values
        
    Example:
        If row = {"Sample": "S0", "TestName": "<Sample>_CALIBRATION"}
        Then replace_placeholders("<Sample>_CALIBRATION", row) returns "S0_CALIBRATION"
        
    Note:
        Placeholders that don't match any column names are left unchanged.
    """
    # Find all placeholder patterns bounded by < > using regex
    # This returns a list of placeholder names found in the field value
    placeholders = re.findall(r'<(.*?)>', str(field_value))
    
    # Process each placeholder found in the field value
    for ph in placeholders:
        # Check if the placeholder name exists as a column in the current row
        if ph in row:
            replacement = str(row[ph])  # Get the column value as string
            # Replace the placeholder including the < > brackets with actual value
            field_value = field_value.replace(f'<{ph}>', replacement)
            
    return field_value  # Return field value with all placeholders resolved

def index_CTV(input_file, test_name, module_name='', place_in='', mode='', config_number=''):
    """
    Main orchestration function for CTV indexing workflow.
    
    This function coordinates the entire CTV processing pipeline, from reading input
    files through generating indexed output with concatenated field strings. It handles
    test name construction, data cleaning, field concatenation, and output file generation
    with appropriate naming conventions for different test modes.
    
    Args:
        input_file (str): Path to input CTV decoder CSV file
        test_name (str): Base test name for generated test instances
        module_name (str, optional): Module prefix for test categorization (e.g. 'CLK_PLL_BASE')
        place_in (str, optional): Output directory path for generated files
        mode (str, optional): Processing mode ('CtvTag' for tag mode, '' for standard)
        config_number (str, optional): Configuration number for file naming differentiation
        
    Returns:
        tuple: (out_file, csv_identifier, tag_header_names) where:
            - out_file: Path to generated indexed CSV file
            - csv_identifier: Extracted identifier from input filename
            - tag_header_names: List of tag header column names between Index and Name
            
    Side Effects:
        - Creates indexed CSV output file in specified directory
        - Creates and removes temporary 'log.csv' file during processing
        - Prints completion message with output file path
        
    Processing Pipeline:
        1. Construct full test name with module prefix if provided
        2. Process input CSV with token replacement and sorting
        3. Load processed data into pandas DataFrame
        4. Clean data by replacing empty/null values with '&' placeholder
        5. Remove completely empty columns
        6. Concatenate remaining columns into combined_string field
        7. Generate appropriate output filename based on mode and configuration
        8. Save final indexed CSV and clean up temporary files
        
    Note:
        The function automatically handles different naming conventions for CtvTag mode
        versus standard mode, and includes ITUFF token information in filenames when available.
    """
    # Construct full test name with module prefix for proper test categorization
    if module_name != '':
        test_name = module_name + "::" + test_name  # Use :: as module separator
        
    # Step 1: Process the input CSV file and create temporary log file
    # This handles token replacement, sorting, and basic indexing
    process_CTV(input_file, 'log.csv', test_name)
    
    # Step 2: Load processed data into pandas DataFrame for advanced manipulation
    combined_df = pd.read_csv('log.csv')  # Read the temporary log file
    
    # Create composite identifier combining test name with index for uniqueness
    combined_df['Name_Index'] = combined_df['Name'] + '_' + combined_df['Index'].astype(str)
    
    # Sort by Name and Index to ensure consistent ordering in output
    combined_df = combined_df.sort_values(by=['Name', 'Index'])
    
    # Initialize empty combined_string column for field concatenation
    combined_df['combined_string'] = ''
    
    # Step 3: Data cleaning - Replace problematic values with standardized placeholder
    # This section addresses the requirement to handle empty, NaN, dash, and blank values
    for col in combined_df.columns:
        # Skip the combined_string column as it's our output field
        if col == 'combined_string':
            continue
            
        # Create boolean mask to identify cells that need replacement
        # Targets: NaN values, empty strings, dashes, and 'NaN' text
        mask = (
            combined_df[col].isna() |                                    # True NaN values
            (combined_df[col].astype(str).str.strip() == '') |          # Empty strings after stripping
            (combined_df[col].astype(str).str.strip() == '-') |         # Just dashes
            (combined_df[col].astype(str).str.upper() == 'NAN')         # 'NaN' as text
        )
   
        # Convert column to object type to allow mixed data types, then replace
        if mask.any():  # Only process if there are values to replace
            combined_df[col] = combined_df[col].astype('object')  # Enable mixed types
            combined_df.loc[mask, col] = '&'  # Replace problematic values with '&' placeholder 

    # Step 4: Column processing and field concatenation
    # Process each column to either include in concatenation or remove if empty
    for col in combined_df.columns:
        # Check if column is completely empty (all NaN, empty strings, dashes, or & placeholders)
        is_all_empty = (combined_df[col].isna().all() or 
                       (combined_df[col].astype(str).str.strip() == '').all() or 
                       (combined_df[col].astype(str).str.strip() == '-').all() or 
                       (combined_df[col].astype(str).str.strip() == '&').all())
        
        # Special handling for 'Field' column - always add to concatenation and stop processing
        if col == "Field":
            combined_df['combined_string'] = combined_df['combined_string'] + '---' + combined_df[f'{col}'].astype(str)
            break  # Field column should be last in concatenation
            
        # Remove completely empty columns to clean up the dataset
        elif is_all_empty:
            combined_df.drop(columns=[col], inplace=True)  # Remove empty column
            continue  # Move to next column
            
        # Include relevant columns in concatenation (skip structural columns)
        elif col != "Index" and col != "Name" and col != "Name_Index":
            combined_df['combined_string'] = combined_df['combined_string'] + '---' + combined_df[f'{col}'].astype(str)
            
    # Clean up the concatenated string by removing leading separator
    # Using '---' instead of '@' to avoid JSL/JMP column parsing errors
    combined_df['combined_string'] = combined_df['combined_string'].str.lstrip('---')

    # Step 5: Output file naming logic based on mode and configuration
    # Handle different naming conventions for various test execution modes
    
    # Find module separator for filename construction
    colon_index = test_name.find('::')
    
    # Add configuration number suffix if provided
    if config_number != '':
        config_number = f'_{config_number}'  # Format with underscore prefix
    else:
        config_number = ''  # No suffix if not provided

    # Extract first valid ITUFF token for filename inclusion
    # This helps identify the specific test variation in the filename
    first_ituff_token = ''
    if 'Name' in combined_df.columns:
        # Search through Name column for first non-empty token
        for token in combined_df['Name'].tolist():
            # Check for valid token (not NaN, empty, dash, and contains content after test name)
            if (pd.notna(token) and 
                str(token).strip() != '' and 
                str(token).strip() != '-' and 
                str(token).strip().replace(test_name, '').split('::')[-1] != ''):
                # Extract token part after test name for filename
                first_ituff_token = str(token).strip().replace(test_name, '').split('::')[-1]
                break  # Use first valid token found

    # Determine ITUFF suffix based on processing mode
    if mode == 'CtvTag':
        # CtvTag mode: include ITUFF token or config number in filename
        ituff_suffix = f'{first_ituff_token}' if first_ituff_token else '_' + config_number
    else:
        # Standard mode: no ITUFF suffix
        ituff_suffix = ''

    # Construct final output filename based on test name structure
    out_file = ''
    if colon_index != -1:
        # Module-prefixed test: use module_name + extracted test portion
        out_file = os.path.join(place_in, f'{module_name}_{test_name[colon_index+len("::"):]}{config_number}{ituff_suffix}_indexed.csv')
    else:
        # Simple test name: use full test name
        out_file = os.path.join(place_in, f'{test_name}{config_number}{ituff_suffix}_indexed.csv')
        
    # Ensure output file has write permissions and handle conflicts
    out_file = fi.check_write_permission(out_file)

    # Step 6: Save final output and cleanup
    # Write the processed DataFrame to the final output file
    combined_df.to_csv(out_file, index=False)  # Save without row indices
    print(out_file, "is indexed!")  # Confirm successful completion
    
    # Clean up temporary log file
    os.remove('log.csv')  # Remove temporary processing file

    # Step 7: Extract CSV identifier from input filename for return value
    # This helps identify the source file in downstream processing
    
    # Find the last path separator (backslash or forward slash)
    last_backslash_index = input_file.rfind('\\')
    last_forwardslash_index = input_file.rfind('/')
    last_slash_index = max(last_backslash_index, last_forwardslash_index)
    
    # Find the .csv extension after the last path separator
    end_index = input_file.find('.csv', last_slash_index)
    csv_identifier = ''  # Initialize identifier
    
    # Extract filename identifier based on mode and filename patterns
    if mode != 'CtvTag':
        if last_slash_index != -1 and end_index != -1 and 'decoded' in input_file:
            # For decoded files: remove 'decoded' and underscores from identifier
            csv_identifier = input_file[last_slash_index+1:end_index].strip('deco').strip('_')
        elif last_slash_index != -1 and end_index != -1:
            # For regular files: use filename without extension
            csv_identifier = input_file[last_slash_index+1:end_index]

    # Extract tag header names for return (columns between Index and Name)
    tag_header_names = get_columns_btwn_index_name(combined_df)

    # Return processing results for downstream use
    return out_file, csv_identifier, tag_header_names

def get_columns_btwn_index_name(df):
    """
    Extract column names that appear between 'Index' and 'Name' columns in DataFrame.
    
    This utility function identifies the tag header columns that contain test parameter
    information. These columns represent the meaningful test data fields that should
    be preserved in the final indexed output.
    
    Args:
        df (pandas.DataFrame): DataFrame containing 'Index' and 'Name' columns
        
    Returns:
        list: List of column names that appear between 'Index' and 'Name' columns.
              Returns empty list if either 'Index' or 'Name' columns don't exist.
              
    Example:
        If DataFrame has columns: ['Index', 'Register', 'Domain', 'Value', 'Name', 'combined_string']
        Returns: ['Register', 'Domain', 'Value']
        
    Note:
        The function returns columns in the order they appear in the DataFrame,
        which preserves the original column ordering from the input CSV.
    """
    # Get list of all column names in their original order
    columns = df.columns.tolist()
    
    try:
        # Find the position of Index and Name columns
        index_pos = columns.index('Index')  # Starting boundary
        name_pos = columns.index('Name')    # Ending boundary
        
        # Extract columns between Index and Name (exclusive of both boundaries)
        # These represent the tag header columns with test parameter data
        tag_header_columns = columns[index_pos + 1:name_pos]

        return tag_header_columns
    except ValueError:
        # Handle case where 'Index' or 'Name' columns don't exist in DataFrame
        # This could happen if CSV structure is unexpected or malformed
        return []  # Return empty list as safe fallback


if __name__ == "__main__":
    """
    Main execution block for standalone script usage.
    
    This block runs when the script is executed directly (not imported as a module).
    It provides an interactive interface for users to process individual CTV files
    with manual input of file paths and test parameters.
    
    Interactive Workflow:
        1. Prompts user for absolute path to CTV decoder CSV file
        2. Prompts user for ITUFF test name (base identifier)
        3. Uses hardcoded module name 'CLK_PLL_BASE' for demonstration
        4. Processes the file and generates indexed output
        
    Example Usage:
        python index_ctv.py
        > Absolute CTV decoder csv file path: C:/path/to/decoder.csv
        > ITUFF test name: TEST_CALIBRATION
        
    Note:
        The module_name is currently hardcoded to 'CLK_PLL_BASE' for demonstration.
        In production usage, this should be made configurable or passed as parameter.
    """
    # Get input file path from user with clear prompt
    input_file = input("Absolute CTV decoder csv file path: ")
    
    # Get test name from user - this becomes the base identifier for generated tests
    test_name = input('ITUFF test name: ')
    
    # Hardcoded module name for demonstration purposes
    # TODO: Make this configurable via command line argument or additional prompt
    module_name = 'CLK_PLL_BASE'
    
    # Process the CTV file with user-provided parameters
    # Uses default values for optional parameters (place_in='', mode='', config_number='')
    index_CTV(input_file, test_name, module_name)

