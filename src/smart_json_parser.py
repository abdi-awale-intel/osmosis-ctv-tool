import json
import csv
import os
import sys
import csv
import re
import pandas as pd
import time
import file_functions as fi
 
#To do, add functionality for customparameter that is simpler than iterator logic
 
 
#Steps to decode SmartCTV:
#1.Obtain base path and JSON path
#2 Grab information from JSON and open CTV csv file
#3 Recursion to generate rows from iterators
#4 Dataframe functions to improve output
 
#def process_SmartCTV(base_path, JSON_path):
def process_SmartCTV(base_path, JSON_path, config_number='',place_in=''):
    """Process SmartCTV configuration with enhanced error handling"""
    #2
    json_obj = {}
    try:
        print(f"Loading JSON from: {JSON_path}")
        with open(JSON_path, 'r') as json_file:
            json_obj  = json.load(json_file)
<<<<<<< HEAD
        print(f"JSON loaded successfully, config_number: '{config_number}'")
    except Exception as e:
        # Print the exception details
        print(f"An error occurred loading JSON: {e}, Possible Trailing Comma Issue")
        return ''
=======
        print(f"✅ Successfully loaded JSON: {JSON_path}")
    except Exception as e:
        # Print the exception details
        print(f"❌ An error occurred loading JSON {JSON_path}: {e}")
        return [], []  # Return empty lists instead of empty string
>>>>>>> a2ad2ab6f5c4fcb2fcf1c73d4edf0d39644d8e55
    #map_params = {get hierarchical lists and the names of the modules}
    #Feed map params into the replace section of the gen rows function under the if area
    # Replace using returned value from JSON based on whatever is the current hierarchical list
    #by making a temporary dictionary
    output_paths = []
    suffixes = []
    print(f"🔍 Processing SmartCTV - config_number: '{config_number}', base_path: {base_path}")
    
    # Check if TestConfigurations exists
    if 'TestConfigurations' not in json_obj:
        print("❌ No TestConfigurations found in JSON")
        return [], []
    
    print(f"📋 Found {len(json_obj['TestConfigurations'])} test configurations")
    #Iterates per test in smart json to create CTV decoders for each test
    for testconfig in json_obj['TestConfigurations']:
<<<<<<< HEAD
        # Ensure both values are strings for comparison
        testconfig_str = str(testconfig) if testconfig is not None else ''
        config_number_str = str(config_number) if config_number is not None else ''
       
        print(f"Processing testconfig: '{testconfig_str}', comparing with config_number: '{config_number_str}'")
       
        if testconfig_str != config_number_str and config_number_str != '':#check for ctvtag mode which always has config number as ''
            print(f"Skipping testconfig '{testconfig_str}' (doesn't match '{config_number_str}')")
=======
        print(f"🔄 Processing test config: {testconfig}")
        if testconfig != config_number and config_number!='':#check for ctvtag mode which always has config number as ''
            print(f"⏩ Skipping config {testconfig} (doesn't match '{config_number}')")
>>>>>>> a2ad2ab6f5c4fcb2fcf1c73d4edf0d39644d8e55
            continue
        CTV_path = ''
        iterator_nest = {}
        map_params = {}
        custom_params = {}
        # Safely get the CTV path and ensure it's a string
        try:
            CTV_path_raw = json_obj['TestConfigurations'][testconfig]['Decoder']['ConfigurationFile']
            CTV_path = str(CTV_path_raw).strip('\"') if CTV_path_raw is not None else ''
        except (KeyError, TypeError) as e:
            print(f'Error accessing ConfigurationFile: {e}')
            continue
           
        if not CTV_path:
            print('Empty ConfigurationFile found.')
            continue
           
        pos = CTV_path.find("Module")
        if pos == -1:
            print('File out of scope found.')
            continue
        else:
            CTV_path = os.path.join(base_path,CTV_path[pos:])
            CTV_path = fi.process_file_input(CTV_path)

            global boolean_queue
            boolean_queue = False

        try:
            map_params = json_obj['TestConfigurations'][testconfig]['Decoder']['MapParameters']
        except KeyError:
            map_params = {}
        try:
            iterator_nest = json_obj['TestConfigurations'][testconfig]['Decoder']['Iterators']
        except KeyError:
            iterator_nest = {}
        try:
            custom_params = json_obj['TestConfigurations'][testconfig]['Decoder']['CustomParameters']
        except KeyError:
            custom_params = {}
        try:
            queue_params = json_obj['TestConfigurations'][testconfig]['Decoder']['QueueParameters']
            if queue_params is not None:
                print('this test has queue parameters')
                boolean_queue = True 
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
            output_file_path = os.path.join(place_in, str(config_number)+'_'+os.path.basename(CTV_path_str))
            out_list = output_file_path.split('.')
            out_list[-2]=out_list[-2]+ "_decoded"
 
        output_file_path = '.'.join(out_list)
        output_file_path = fi.check_write_permission(output_file_path)
        #3
        # Write the completed CSV file
        #os.chmod(output_file_path, 0o666)#Only do this check if file path known to exist
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
            #if len(row_chunks) <= 1: #this splits the rows back into individual rows if there are no queue parameters with no break lines to reduce number of iterators and duplicates
             #   row_chunks = [row for lsit in row_chunks for row in lsit]
            #Necessary section for queue params
 
            #for row in data_rows:#replace this with chunks and revise iterator mapping to happen outside of for row iteration
            for row_chunk in row_chunks:
                iterator_local_nest = iterator_nest.copy()
                pattern = r"<Iterator(.*?)>"
                csv_keys = [key for row in row_chunk for row_element in row for key in re.findall(pattern, row_element)]
                iterator_local_nest = {key: value for key, value in iterator_local_nest.items() if key in csv_keys}
                #queue attempt
                queue_local_nest = queue_params.copy()
                pattern = r"<QueueParameter(.*?)>"
                csv_keys = [key for row in row_chunk for row_element in row for key in re.findall(pattern, row_element)]
                queue_local_nest = {key: value for key, value in queue_local_nest.items() if key in csv_keys}
                filled_rows_from_less_rows,_ = generate_filled_CTV_rows(row_chunk, iterator_local_nest, map_params, custom_params, queue_local_nest, header)

                writer.writerows(filled_rows_from_less_rows)
                counter += len(filled_rows_from_less_rows)
        #4
 
        # get rid of duplicates
 
        df = pd.read_csv(output_file_path, index_col=False,low_memory=False)
        df = df.drop_duplicates()
        #replace fields with actual values (adapt to make for all headers)
        #df.rename(columns={col: 'Pin' for col in df.columns if 'Pin' in col}, inplace=True)
        df['Field'] = df.apply(lambda row: replace_placeholders(row['Field'], row), axis=1)
        df['ItuffToken'] = df.apply(lambda row: replace_placeholders(row['ItuffToken'], row), axis=1)
        df.to_csv(output_file_path, index=False)
        #Remove lines composed of "BREAK"
        clean_up_breaks(output_file_path)
        print(output_file_path+" is decoded!")
<<<<<<< HEAD
        if config_number != '':
            return output_file_path
        output_paths.append(output_file_path)
 
 
=======
        if config_number != '': 
            return [output_file_path], ['']  # Return as lists for consistency
        output_paths.append(output_file_path)


    print(f"📤 SmartCTV processing complete - returning {len(output_paths)} files and {len(suffixes)} suffixes")
>>>>>>> a2ad2ab6f5c4fcb2fcf1c73d4edf0d39644d8e55
    return output_paths, suffixes
 
def generate_filled_CTV_rows(rows, iterator_dict, map_dict, custom_dict, queue_dict, header,counter=0):
    completed_rows = []

    try:
            # Check if all values are not lists
        if all(not isinstance(value, list) for value in iterator_dict.values()):
            if boolean_queue:
                print(iterator_dict)
                print("Counter:", counter)
            if iterator_dict == {'MC': 'M0', 'Nibble': '0', 'SubChannel': 'A', 'MuxDQ': '2', 'Byte': '0'}:
                print("Special case for iterator_dict matched.")
            # Replace placeholders with values
            for row in rows:
                #Get smaller queueparameter list for each row
                small_queue = {}
                for key in queue_dict:
                    small_queue[key] = queue_dict[key][counter]            
                completed_row = replace_iterators_maps_customs_queues(row, iterator_dict, map_dict, custom_dict, small_queue, header)
                completed_rows.append(completed_row)
                counter += 1
        else:
            # Iterate over each key-value pair
            for key, values in iterator_dict.items():
                if isinstance(values, list):
                    for value in values:
                        # Create a new dictionary with the current value replaced
                        new_dict = {**iterator_dict, key: value}
                        # Recursively generate rows
                        filled_rows,counter = generate_filled_CTV_rows(rows, new_dict, map_dict, custom_dict, queue_dict, header, counter)
                        completed_rows.extend(filled_rows)
                    break
        if counter == 1280  :
            print("Counter reached 1280, stopping further processing.")
        if boolean_queue:
            print(pd.DataFrame(completed_rows).shape)
    except Exception as e:
        print(f"An error occurred while generating filled CTV rows: {e}")
        print("Iterator dictionary:", iterator_dict)
        print("Map dictionary:", map_dict)
        print("Custom dictionary:", custom_dict)
        print("Queue dictionary:", queue_dict)
        print("Header:", header)
        print("Counter:", counter)

    return completed_rows,counter
 
# Replace iterators one at a time in a row
def replace_iterators_customs(row_element, iterator_dict, custom_dict,queue_dict):
    for key, value in iterator_dict.items():
        row_element = row_element.replace(f'<Iterator{key}>', value)
    for key, value in custom_dict.items():
        row_element = row_element.replace(f'<CustomParameter{key}>', value)
    for key, value in queue_dict.items():
        row_element = row_element.replace(f'<QueueParameter{key}>', value)      
    return row_element
 
# Replace iterators and maptokens one at a time in a row
def replace_iterators_maps_customs_queues(row, iterator_dict,map_dict, custom_dict, queue_dict, header):
    revised_row = [replace_iterators_customs(row_element, iterator_dict, custom_dict,queue_dict) for row_element in row]
    # Replace map tokens
    for map_name, map_data in map_dict.items():
        hierarchy_columns = map_data.get("HierarchyColumns", [])
        map_values = map_data.get("Map", {})
        # Get indices of hierarchy columns from the header
        hierarchy_indices = [header.index(col) for col in hierarchy_columns if col in header]
        # Construct the key for map lookup based on current iterator values
        map_key = ','.join(revised_row[index] for index in hierarchy_indices)
        # Debugging print statements
        revised_row = [
            element.replace(f'<MapParameter{map_name}>', map_values.get(map_key, element))
            if isinstance(element, str) else element
            for element in revised_row
        ]
    return revised_row
 
def replace_placeholders(field_value, row):
    # Find all placeholders bounded by <>
    # first arg is regex, next is the text we want to search
    # This will create a list of placeholders if there are more than one
    placeholders = re.findall(r'<(.*?)>', str(field_value))
    # iterate through this list and replace each one
    for ph in placeholders:
        # Replace placeholder with whatever is in the column of the same name
        if ph in row:
            replacement = str(row[ph])
            # Replace the placeholder including <>
            field_value = field_value.replace(f'<{ph}>', replacement)
    return field_value
 
def clean_up_breaks(output_file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(output_file_path, encoding='utf-8')
 
    # Define the keyword to filter out
    keyword = 'BREAK'
 
    # Filter out rows that contain the keyword in any column
    df_cleaned = df[~df.apply(lambda row: row.astype(str).str.contains(keyword).any(), axis=1)]
 
    # Write the cleaned DataFrame back to the original file
    df_cleaned.to_csv(output_file_path, index=False, encoding='utf-8')
 
def clean_header(header):
    # Use a regular expression to keep only alphabetic characters
    cleaned_header = [re.sub(r'[^a-zA-Z]', '', col) for col in header]
    return cleaned_header
 
if __name__ == "__main__":
    #1
    # Prompt user to choose path type
    base_path = fi.process_file_input(input("Enter an absolute input TP location that the other csv paths are relative to (base path): "))
    # Get absolute paths from user
    file_path = fi.process_file_input(input("Enter an absolute JSON input file location: "))
    # Process the JSON file and write results to CSV
    process_SmartCTV(base_path, file_path, config_number=0)
 