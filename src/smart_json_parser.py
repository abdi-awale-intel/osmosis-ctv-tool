"""
Smart JSON Parser for CTV (Circuit Test Vehicle) Configuration Processing

This module processes SmartCTV JSON configuration files and generates decoded CSV files
for circuit test vehicle testing. It handles iterators, map parameters, custom parameters,
and queue parameters to expand test configurations into executable test sequences.

Main Features:
- Parse SmartCTV JSON configuration files
- Process CTV CSV templates with placeholders
- Expand iterators and parameters into complete test sequences
- Handle hierarchical test configurations
- Generate decoded CSV files for test execution

Author: Intel CTV Tool Team
Date: 2025
"""

import json  # JSON file parsing and manipulation
import csv   # CSV file reading and writing operations
import os    # Operating system interface for file path operations
import sys   # System-specific parameters and functions
import csv   # CSV handling (duplicate import - could be removed)
import re    # Regular expression operations for pattern matching
import pandas as pd  # Data manipulation and analysis library

import time     # Time-related functions (not currently used)
import chardet  # Character encoding detection (not currently used)
import file_functions as fi  # Custom file handling utilities

# TODO: Add functionality for CustomParameter that is simpler than iterator logic

# Pre-compile regex patterns for better performance - avoids recompiling patterns repeatedly
ITERATOR_PATTERN = re.compile(r"<Iterator(.*?)>")          # Matches <Iterator...> placeholders
QUEUE_PARAMETER_PATTERN = re.compile(r"<QueueParameter(.*?)>")  # Matches <QueueParameter...> placeholders
PLACEHOLDER_PATTERN = re.compile(r'<(.*?)>')              # Matches any <...> placeholder

def fix_json_trailing_commas(json_string):
    """
    Remove trailing commas from JSON string to fix malformed JSON files.
    
    Many JSON files may have trailing commas which are not valid JSON syntax.
    This function uses regex to remove commas that appear before closing brackets/braces.
    
    Args:
        json_string (str): Raw JSON string that may contain trailing commas
        
    Returns:
        str: Fixed JSON string with trailing commas removed
        
    Example:
        Input:  '{"key": "value",}'
        Output: '{"key": "value"}'
    """
    # Remove trailing commas before closing brackets/braces using regex substitution
    # Pattern matches: comma + optional whitespace + closing bracket/brace
    return re.sub(r',\s*([}\]])', r'\1', json_string)

def load_json_with_comma_fix(file_path):
    """
    Load JSON file with automatic trailing comma removal if standard parsing fails.
    
    Attempts to load JSON normally first, then tries to fix trailing commas
    if a JSONDecodeError occurs. This provides robust JSON loading for files
    that may not be perfectly formatted.
    
    Args:
        file_path (str): Path to the JSON file to load
        
    Returns:
        dict: Parsed JSON object as Python dictionary
        
    Raises:
        json.JSONDecodeError: If JSON cannot be parsed even after comma fixing
        FileNotFoundError: If the specified file doesn't exist
    """
    try:
        # Attempt standard JSON loading with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()  # Read entire file content into memory
        return json.loads(content)  # Parse JSON string into Python object
    except json.JSONDecodeError:
        # If standard parsing fails, try fixing trailing commas
        print("JSON decode error, attempting to fix trailing commas...")
        try:
            # Apply comma fixing function to the content
            fixed_content = fix_json_trailing_commas(content)
            return json.loads(fixed_content)  # Attempt parsing again
        except json.JSONDecodeError as e:
            # If comma fixing doesn't work, raise the original error
            print(f"Could not fix JSON: {e}")
            raise


"""
Steps to decode SmartCTV configuration:
1. Obtain base path and JSON path from user input or parameters
2. Grab configuration information from JSON and open corresponding CTV CSV template file
3. Use recursion to generate expanded rows from iterators and parameters
4. Apply DataFrame functions to improve output formatting and remove duplicates
"""

def process_SmartCTV(base_path, JSON_path, config_number='', place_in=''):
    """
    Process SmartCTV configuration files and generate decoded CSV outputs.
    
    This is the main function that orchestrates the entire SmartCTV processing workflow.
    It reads JSON configuration files, processes CTV templates, expands iterators and
    parameters, and generates decoded CSV files ready for test execution.
    
    Args:
        base_path (str): Base directory path where CTV files are located relative to
        JSON_path (str): Full path to the SmartCTV JSON configuration file
        config_number (str, optional): Specific configuration number to process.
                                     If empty, processes all configurations.
        place_in (str, optional): Output directory for generated files.
                                 If empty, uses same directory as input.
    
    Returns:
        tuple: (output_paths, suffixes, config_numbers) where:
            - output_paths: List of generated CSV file paths
            - suffixes: List of ITUFF test name postfixes for each configuration
            - config_numbers: List of processed configuration numbers
            
    Raises:
        Exception: If JSON loading fails or file processing encounters errors
    """
    # Step 2: Load and parse the JSON configuration file
    json_obj = {}  # Initialize empty dictionary to store parsed JSON
    try:
        print(f"Loading JSON from: {JSON_path}")  # User feedback for loading process
        json_obj = load_json_with_comma_fix(JSON_path)  # Load with error correction
        print(f"JSON loaded successfully, config_number: '{config_number}'")  # Confirm success
    except Exception as e:
        # Handle any errors during JSON loading and provide user feedback
        print(f"An error occurred loading JSON: {e}")
        return ''  # Return empty string to indicate failure
    
    # Initialize lists to collect results from processing multiple configurations
    # These will be used to track outputs for batch processing scenarios
    output_paths = []    # Paths to generated decoded CSV files
    suffixes = []        # ITUFF postfix strings for test naming
    config_numbers = []  # Configuration numbers that were processed
    
    # Validate that the JSON contains the expected TestConfigurations structure
    if 'TestConfigurations' not in json_obj:
        print("❌ No TestConfigurations found in JSON")  # Error indicator with emoji
        return [], [], []  # Return empty lists to indicate no processing occurred
    
    # Get total count for progress tracking and user feedback
    total_configs = len(json_obj['TestConfigurations'])
    print(f"📋 Found {total_configs} test configurations to process")  # Progress indicator
    
    # Main processing loop: Iterate through each test configuration in the JSON
    # Each configuration represents a different test scenario or parameter set
    for config_index, testconfig in enumerate(json_obj['TestConfigurations'], 1):
        # Ensure both values are strings for reliable comparison
        # Handle None values that might exist in malformed JSON files
        testconfig_str = str(testconfig) if testconfig is not None else ''
        config_number_str = str(config_number) if config_number is not None else ''
        
        # Provide progress feedback with current configuration being processed
        print(f"🔄 Processing config {config_index}/{total_configs}: {testconfig_str}")
        
        # Skip configurations that don't match the requested config_number
        # This allows selective processing when only specific configs are needed
        # Check for ctvtag mode which always has config number as empty string
        if testconfig_str != config_number_str and config_number_str != '':
            print(f"⏩ Skipping config {testconfig_str} (doesn't match '{config_number_str}')")
            continue  # Move to next configuration without processing this one

        # Add current configuration to the list of processed configs
        config_numbers.append(testconfig)

        # Initialize variables to store configuration parameters for current test
        CTV_path = ''        # Path to the CTV template CSV file
        iterator_nest = {}   # Dictionary of iterators that define parameter loops
        map_params = {}      # Hierarchical mapping parameters for value substitution
        custom_params = {}   # Custom parameters for specific test requirements
        
        # Safely extract the CTV configuration file path from JSON structure
        # Handle potential KeyError if JSON structure is malformed
        try:
            # Navigate through nested JSON structure to get ConfigurationFile
            CTV_path_raw = json_obj['TestConfigurations'][testconfig]['Decoder']['ConfigurationFile']
            # Convert to string and remove any surrounding quotes from JSON
            CTV_path = str(CTV_path_raw).strip('\"') if CTV_path_raw is not None else ''
        except (KeyError, TypeError) as e:
            # Log error and skip this configuration if path cannot be extracted
            print(f'Error accessing ConfigurationFile: {e}')
            continue  # Move to next configuration
            
        # Validate that a configuration file path was found
        if not CTV_path:
            print('Empty ConfigurationFile found.')  # Log warning about missing path
            continue  # Skip this configuration and move to next one
            
        # Check if the path contains "Module" to ensure it's in expected format
        # CTV files should be located within Module directories in the test program structure
        pos = CTV_path.find("Module")
        if pos == -1:
            print('File out of scope found.')  # Path doesn't contain Module directory
            continue  # Skip configurations that don't follow expected path structure
        else:
            # Construct full path by joining base path with relative Module path
            CTV_path = os.path.join(base_path, CTV_path[pos:])
            # Process the file path through utility function for normalization
            CTV_path = fi.process_file_input(CTV_path)

        # Extract MapParameters from JSON configuration with error handling
        # MapParameters define hierarchical value mappings for test parameter substitution
        try:
            map_params = json_obj['TestConfigurations'][testconfig]['Decoder']['MapParameters']
        except KeyError:
            map_params = {}  # Use empty dict if MapParameters not found
            
        # Extract Iterators from JSON configuration with error handling
        # Iterators define loops and parameter variations for test expansion
        try:
            iterator_nest = json_obj['TestConfigurations'][testconfig]['Decoder']['Iterators']
        except KeyError:
            iterator_nest = {}  # Use empty dict if Iterators not found
            
        # Extract CustomParameters from JSON configuration with error handling
        # CustomParameters allow for specific test customizations
        try:
            custom_params = json_obj['TestConfigurations'][testconfig]['Decoder']['CustomParameters']
        except KeyError:
            custom_params = {}
        try:
            queue_params = json_obj['TestConfigurations'][testconfig]['Decoder']['QueueParameters']
        except KeyError:
            queue_params = {}


        with open(CTV_path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)
            # Get the header and data rows
            header = rows[0]
            header = clean_header(header)
            data_rows = rows[1:]
        if len(header) == 1:
            with open(CTV_path, 'r') as csv_file:
                reader = csv.reader(csv_file,delimiter='\t')
                rows = list(reader)
                # Get the header and data rows
                header = rows[0]
                header = clean_header(header)
                data_rows = rows[1:]
        
        #Record the ITUFF SUFFIX if available and Generate the output CSV file path using string concatenation
        suffix = ''
        try:
            suffix_raw = json_obj['TestConfigurations'][testconfig]['Decoder']['ItuffTestNamePostfix']
            suffix = str(suffix_raw) if suffix_raw is not None else ''
            suffixes.append(suffix)
        except (KeyError, TypeError):
            suffix = ''
            suffixes.append('')
        
        # Ensure CTV_path is a string for basename operations
        CTV_path_str = str(CTV_path) if CTV_path is not None else ''
        
        if suffix != '':
            output_file_path = os.path.join(place_in, suffix+os.path.basename(CTV_path_str))
            out_list = output_file_path.split('.')
            out_list[-2]=out_list[-2]+ suffix+"_decoded"
        else:
            output_file_path = os.path.join(place_in, os.path.basename(CTV_path_str))
            out_list = output_file_path.split('.')
            out_list[-2]=out_list[-2]+ '_' + testconfig + "_decoded"

        output_file_path = '.'.join(out_list)

        #os.chmod(output_file_path, 0o666)#Only do this check if file path known to exist
        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            output_paths.append(output_file_path)
            continue

        print(f"📂 Processing CTV file: {CTV_path_str}" )
        output_file_path = fi.check_write_permission(output_file_path)
        #3
        # Write the completed CSV file
        
        
        with open(output_file_path, 'w', newline='') as csv_file:
            counter = 0
            writer = csv.writer(csv_file)
            writer.writerow(header)

            #Necessary section for queue params
            row_chunks = []
            current_chunk = []
            for row in data_rows:#make chunks based on the word break
                # Check if 'break' is in any element of the row
                if any("break" in element.lower() for element in row):
                    # If current_chunk is not empty, append it to row_chunks
                    if current_chunk:
                        row_chunks.append(current_chunk)
                        current_chunk = []  # Reset current_chunk for the next series
                else:
                    # Append row to current_chunk
                    current_chunk.append(row)
            if current_chunk:
                row_chunks.append(current_chunk)
            
            print(f"📊 Processing {len(row_chunks)} row chunks with {len(data_rows)} total rows")
            
            #if len(row_chunks) <= 1: #this splits the rows back into individual rows if there are no queue parameters with no break lines to reduce number of iterators and duplicates
            #    row_chunks = [row for lsit in row_chunks for row in lsit]#
            #Necessary section for queue params

            #for row in data_rows:#replace this with chunks and revise iterator mapping to happen outside of for row iteration
            for chunk_index, row_chunk in enumerate(row_chunks, 1):
                if chunk_index % 10 == 0 or chunk_index == len(row_chunks):
                    print(f"  Processing chunk {chunk_index}/{len(row_chunks)}...")
                    
                iterator_local_nest = iterator_nest.copy()
                # Use pre-compiled pattern for better performance
                csv_keys = [key for row in row_chunk for row_element in row for key in ITERATOR_PATTERN.findall(row_element)]
                iterator_local_nest = {key: value for key, value in iterator_local_nest.items() if key in csv_keys}
                #queue attempt
                queue_local_nest = queue_params.copy()
                # Use pre-compiled pattern for better performance
                csv_keys = [key for row in row_chunk for row_element in row for key in QUEUE_PARAMETER_PATTERN.findall(row_element)]
                queue_local_nest = {key: value for key, value in queue_local_nest.items() if key in csv_keys}
                filled_rows_from_less_rows,_ = generate_filled_CTV_rows(row_chunk, iterator_local_nest, map_params, custom_params, queue_local_nest, header)

                writer.writerows(filled_rows_from_less_rows)
                counter += len(filled_rows_from_less_rows)
        #4
        # Optimize DataFrame operations for better performance
        print(f"Processing {counter} rows for post-processing...")
        
        df = pd.read_csv(output_file_path, index_col=False, low_memory=False)
        
        # Remove duplicates first to reduce data size for subsequent operations
        initial_rows = len(df)
        df = df.drop_duplicates()
        final_rows = len(df)
        if initial_rows != final_rows:
            print(f"Removed {initial_rows - final_rows} duplicate rows")
        
        # Optimize placeholder replacement by processing all columns at once
        print("Applying placeholder replacements...")
        for col in df.columns:
            # Use vectorized string operations where possible
            df[col] = df[col].astype(str)  # Ensure all values are strings
            
        # Apply replace_placeholders more efficiently
        for idx, row in df.iterrows():
            for col in df.columns:
                df.at[idx, col] = replace_placeholders(df.at[idx, col], row)
        
        df.to_csv(output_file_path, index=False)
        
        # Remove lines composed of "BREAK"
        clean_up_breaks(output_file_path)
        print(f"{output_file_path} is decoded! ({final_rows} rows processed)")
        if config_number != '': 
            return output_file_path
        output_paths.append(output_file_path)

    print(f"📤 SmartCTV processing complete - returning {len(output_paths)} files and {len(suffixes)} suffixes")
    return output_paths, suffixes, config_numbers

def generate_filled_CTV_rows(rows, iterator_dict, map_dict, custom_dict, queue_dict, header, counter=0):
    """
    Recursively generate expanded CTV rows by processing iterators and parameters.
    
    This function handles the core logic of expanding template rows with iterator values.
    It uses recursion to handle nested iterators and generates all possible combinations
    of parameter values to create complete test sequences.
    
    Args:
        rows (list): List of template CSV rows to be expanded
        iterator_dict (dict): Dictionary of iterator parameters and their value lists
        map_dict (dict): Hierarchical mapping parameters for value substitution
        custom_dict (dict): Custom parameters for specific test requirements
        queue_dict (dict): Queue parameters for sequential value assignment
        header (list): CSV header row for column reference
        counter (int, optional): Row counter for queue parameter indexing
    
    Returns:
        tuple: (completed_rows, counter) where:
            - completed_rows: List of fully expanded CSV rows with values substituted
            - counter: Updated counter for queue parameter tracking
            
    Note:
        This function uses recursion to handle nested iterators. When an iterator
        contains a list of values, it processes each value recursively until all
        iterators are resolved to single values.
    """
    completed_rows = []  # Initialize list to collect all expanded rows
    
    # Check if all iterator values are single values (not lists)
    # This is the base case for recursion - when all iterators are resolved
    if all(not isinstance(value, list) for value in iterator_dict.values()):
        # All iterators are resolved to single values, process each template row
        for row in rows:
            # Create queue parameter subset for current row
            # Queue parameters are indexed sequentially across rows
            small_queue = {}
            for key in queue_dict:
                # Extract the value at current counter position for each queue parameter
                small_queue[key] = queue_dict[key][counter]

            # Replace all placeholders in the current row with actual values
            completed_row = replace_iterators_maps_customs_queues(row, iterator_dict, map_dict, custom_dict, small_queue, header)
            completed_rows.append(completed_row)  # Add completed row to results
            counter += 1  # Increment counter for next queue parameter indexing
    else:
        # Recursive case: at least one iterator still contains a list of values
        # Find the first iterator with a list value and expand it
        for key, values in iterator_dict.items():
            if isinstance(values, list):  # Found an iterator with multiple values
                # Process each value in the iterator list
                for value in values:
                    # Create new dictionary with current value substituted for the list
                    # This reduces the problem size by resolving one iterator
                    new_dict = {**iterator_dict, key: value}
                    # Recursively process with the reduced iterator dictionary
                    filled_rows, counter = generate_filled_CTV_rows(rows, new_dict, map_dict, custom_dict, queue_dict, header, counter)
                    completed_rows.extend(filled_rows)  # Add all recursive results
                break  # Process only the first list key, recursion handles the rest
                
    # Return all completed rows and updated counter
    return completed_rows, counter

def replace_iterators_customs_queues(row_element, iterator_dict, custom_dict, queue_dict):
    """
    Replace iterator, custom, and queue parameter placeholders in a single row element.
    
    This function performs string replacement for all types of parameters in a single
    cell or row element. It processes placeholders in the format <IteratorKey>,
    <CustomParameterKey>, and <QueueParameterKey>.
    
    Args:
        row_element (str): Single cell value that may contain placeholders
        iterator_dict (dict): Dictionary of iterator parameters {key: value}
        custom_dict (dict): Dictionary of custom parameters {key: value}
        queue_dict (dict): Dictionary of queue parameters {key: value}
        
    Returns:
        str: Row element with all placeholders replaced by actual values
        
    Example:
        Input:  "<IteratorSample>_<CustomParameterType>_<QueueParameterIndex>"
        Output: "S0_CALIBRATION_001"
    """
    # Replace iterator placeholders with format <IteratorKey>
    for key, value in iterator_dict.items():
        row_element = row_element.replace(f'<Iterator{key}>', value)
        
    # Replace custom parameter placeholders with format <CustomParameterKey>
    for key, value in custom_dict.items():
        row_element = row_element.replace(f'<CustomParameter{key}>', value)
        
    # Replace queue parameter placeholders with format <QueueParameterKey>
    for key, value in queue_dict.items():
        row_element = row_element.replace(f'<QueueParameter{key}>', value)
        
    return row_element

def replace_iterators_maps_customs_queues(row, iterator_dict, map_dict, custom_dict, queue_dict, header):
    """
    Replace all types of placeholders in a complete CSV row including map parameters.
    
    This function processes an entire CSV row and replaces all placeholders including
    iterators, custom parameters, queue parameters, and hierarchical map parameters.
    Map parameters use hierarchical lookups based on multiple column values.
    
    Args:
        row (list): Complete CSV row as list of cell values
        iterator_dict (dict): Dictionary of iterator parameters {key: value}
        map_dict (dict): Dictionary of hierarchical map parameters with structure:
                        {map_name: {"HierarchyColumns": [...], "Map": {...}}}
        custom_dict (dict): Dictionary of custom parameters {key: value}
        queue_dict (dict): Dictionary of queue parameters {key: value}
        header (list): CSV header row for column index lookup
        
    Returns:
        list: Complete CSV row with all placeholders replaced
        
    Note:
        Map parameters use hierarchical keys constructed from multiple column values.
        For example, if HierarchyColumns are ["Register", "Domain"], the map key
        might be "REG1,DOMAIN_A" to lookup the corresponding map value.
    """
    # First pass: replace iterator, custom, and queue parameters in all row elements
    revised_row = [replace_iterators_customs_queues(row_element, iterator_dict, custom_dict, queue_dict) 
                   for row_element in row]
    
    # Second pass: process hierarchical map parameters
    for map_name, map_data in map_dict.items():
        # Extract hierarchy column names and mapping values from map configuration
        hierarchy_columns = map_data.get("HierarchyColumns", [])
        map_values = map_data.get("Map", {})
        
        # Get column indices for hierarchy columns from the CSV header
        hierarchy_indices = [header.index(col) for col in hierarchy_columns if col in header]
        
        # Construct hierarchical lookup key from current row values
        # Key format: "value1,value2,value3" based on hierarchy columns
        map_key = ','.join(revised_row[index] for index in hierarchy_indices)
        
        # Replace map parameter placeholders with looked-up values
        # Use the hierarchical key to find the corresponding value in the map
        revised_row = [
            element.replace(f'<MapParameter{map_name}>', map_values.get(map_key, element))
            if isinstance(element, str) else element
            for element in revised_row
        ]
    return revised_row

def replace_placeholders(field_value, row):
    """
    Replace cross-column placeholders with values from other columns in the same row.
    
    This function handles placeholders that reference other columns within the same row.
    It's used for final cleanup after all other parameter types have been processed.
    
    Args:
        field_value (str): Cell value that may contain placeholders like <ColumnName>
        row (pandas.Series or dict): Current row data with column names as keys
        
    Returns:
        str: Field value with placeholders replaced by corresponding column values
        
    Example:
        If row contains {"Register": "REG1", "TestName": "<Register>_TEST"}
        Then "<Register>_TEST" becomes "REG1_TEST"
    """
    # Find all placeholders bounded by <> using pre-compiled regex pattern
    # This creates a list of placeholder names found within the field value
    placeholders = PLACEHOLDER_PATTERN.findall(str(field_value))
    
    # Iterate through each placeholder found and replace it
    for ph in placeholders:
        # Check if the placeholder name exists as a column in the current row
        if ph in row:
            replacement = str(row[ph])  # Convert column value to string
            # Replace the placeholder including the <> brackets
            field_value = field_value.replace(f'<{ph}>', replacement)
    return field_value

def clean_up_breaks(output_file_path):
    """
    Remove rows containing 'BREAK' keyword from the output CSV file.
    
    BREAK rows are used as delimiters in CTV templates to separate test chunks
    for queue parameter processing. They should be removed from the final output
    as they are not actual test instructions.
    
    Args:
        output_file_path (str): Path to the CSV file to clean up
        
    Side Effects:
        Modifies the CSV file in place, removing rows containing 'BREAK'
        Prints count of removed rows for user feedback
    """
    # Read the entire CSV file into a pandas DataFrame for processing
    df = pd.read_csv(output_file_path, encoding='utf-8')

    # Define the keyword to filter out from all rows
    keyword = 'BREAK'
    
    # Get initial row count for reporting purposes
    initial_rows = len(df)

    # Create boolean mask to identify rows containing 'BREAK' in any column
    # Convert all values to strings to handle mixed data types, then check for keyword
    mask = df.astype(str).apply(lambda x: x.str.contains(keyword, case=False, na=False)).any(axis=1)
    # Keep rows that do NOT contain the keyword (invert mask with ~)
    df_cleaned = df[~mask]
    
    # Calculate final row count and report removal statistics
    final_rows = len(df_cleaned)
    if initial_rows != final_rows:
        print(f"Removed {initial_rows - final_rows} rows containing 'BREAK'")

    # Write the cleaned DataFrame back to the original file location
    df_cleaned.to_csv(output_file_path, index=False, encoding='utf-8')

def clean_header(header):
    """
    Clean CSV header by removing non-alphabetic characters from column names.
    
    This function standardizes column names by keeping only alphabetic characters,
    which helps prevent issues with special characters in column references and
    ensures consistent column naming across different CTV files.
    
    Args:
        header (list): List of original column names from CSV header row
        
    Returns:
        list: List of cleaned column names with only alphabetic characters
        
    Example:
        Input:  ["Test_Name", "Port#", "Value(V)", "Status-Check"]
        Output: ["TestName", "Port", "ValueV", "StatusCheck"]
    """
    # Use regular expression to remove all non-alphabetic characters from each column name
    # This keeps only letters (a-z, A-Z) and removes numbers, symbols, spaces, etc.
    cleaned_header = [re.sub(r'[^a-zA-Z]', '', col) for col in header]
    return cleaned_header

if __name__ == "__main__":
    """
    Main execution block for standalone script usage.
    
    This block runs when the script is executed directly (not imported as a module).
    It prompts the user for input paths and processes a single SmartCTV configuration.
    """
    # Step 1: Get base path from user
    # This is the root directory where all relative CTV file paths are resolved from
    base_path = fi.process_file_input(input("Enter an absolute input TP location that the other csv paths are relative to (base path): "))
    
    # Get JSON configuration file path from user
    # This should be the full path to the SmartCTV JSON configuration file
    file_path = fi.process_file_input(input("Enter an absolute JSON input file location: "))
    
    # Process the JSON file and write results to CSV
    # Using config_number=0 processes the first configuration found
    process_SmartCTV(base_path, file_path, config_number=0)


