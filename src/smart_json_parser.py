import json
import csv
import os
import sys
import csv
import re
import pandas as pd

import time
import chardet
import file_functions as fi

#To do, add functionality for customparameter that is simpler than iterator logic


#Steps to decode SmartCTV:
#1.Obtain base path and JSON path
#2 Grab information from JSON and open CTV csv file
#3 Recursion to generate rows from iterators
#4 Dataframe functions to improve output

#def process_SmartCTV(base_path, JSON_path):
def process_SmartCTV(base_path, JSON_path, config_number='',place_in=''):
    #2
    json_obj = {}
    try:
        with open(JSON_path, 'r') as json_file:
            json_obj  = json.load(json_file)
        print(f"✅ Successfully loaded JSON: {JSON_path}")
    except Exception as e:
        # Print the exception details
        print(f"❌ An error occurred loading JSON {JSON_path}: {e}")
        return [], []  # Return empty lists instead of empty string
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
        print(f"🔄 Processing test config: {testconfig}")
        if testconfig != config_number and config_number!='':#check for ctvtag mode which always has config number as ''
            print(f"⏩ Skipping config {testconfig} (doesn't match '{config_number}')")
            continue
        CTV_path = ''
        iterator_nest = {}
        map_params = {}
        custom_params = {}
        CTV_path = json_obj['TestConfigurations'][testconfig]['Decoder']['ConfigurationFile'].strip('\"')
        pos = CTV_path.find("Module")
        if pos == -1:
            print('File out of scope found.')
            continue
        else:
            CTV_path = os.path.join(base_path,CTV_path[pos:])
            CTV_path = fi.process_file_input(CTV_path)
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
            suffix = json_obj['TestConfigurations'][testconfig]['Decoder']['ItuffTestNamePostfix']
            suffixes.append(suffix)
        except:
            suffix = ''
            suffixes.append('')
        
        if suffix != '':
            output_file_path = os.path.join(place_in, suffix+os.path.basename(CTV_path))
            out_list = output_file_path.split('.')
            out_list[-2]=out_list[-2]+ suffix+"_decoded"
        else:
            output_file_path = os.path.join(place_in, config_number+'_'+os.path.basename(CTV_path))
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
            for row in data_rows:
                iterator_local_nest = iterator_nest.copy()

                pattern = r"<Iterator(.*?)>"
                csv_keys = [key for row_element in row for key in re.findall(pattern, row_element)]

                iterator_local_nest = {key: value for key, value in iterator_local_nest.items() if key in csv_keys}
                filled_rows_from_one_row = generate_filled_CTV_rows(row, iterator_local_nest, map_params, custom_params, header)

                writer.writerows(filled_rows_from_one_row)
                counter += len(filled_rows_from_one_row)
        #4

        # get rid of duplicates

        df = pd.read_csv(output_file_path, index_col=False,low_memory=False)
        df = df.drop_duplicates()
        #replace fields with actual values (adapt to make for all headers)
        df.rename(columns={col: 'Pin' for col in df.columns if 'Pin' in col}, inplace=True)
        df['Field'] = df.apply(lambda row: replace_placeholders(row['Field'], row), axis=1)

        df['ItuffToken'] = df.apply(lambda row: replace_placeholders(row['ItuffToken'], row), axis=1) 
        df.to_csv(output_file_path, index=False)
        #Remove lines composed of "BREAK"
        clean_up_breaks(output_file_path)
        print(output_file_path+" is decoded!")
        if config_number != '': 
            return [output_file_path], ['']  # Return as lists for consistency
        output_paths.append(output_file_path)


    print(f"📤 SmartCTV processing complete - returning {len(output_paths)} files and {len(suffixes)} suffixes")
    return output_paths, suffixes

def generate_filled_CTV_rows(row, iterator_dict, map_dict, custom_dict, header):
    completed_rows = []
    # Check if all values are not lists
    if all(not isinstance(value, list) for value in iterator_dict.values()):
        # Replace placeholders with values
        completed_row = replace_iterators_maptokens_customs(row, iterator_dict, map_dict, custom_dict, header)
        completed_rows.append(completed_row)
    else:
        # Iterate over each key-value pair
        for key, values in iterator_dict.items():
            if isinstance(values, list):
                for value in values:
                    # Create a new dictionary with the current value replaced
                    new_dict = {**iterator_dict, key: value}
                    # Recursively generate rows
                    filled_rows = generate_filled_CTV_rows(row, new_dict, map_dict, custom_dict, header)
                    completed_rows.extend(filled_rows)
    return completed_rows

# Replace iterators one at a time in a row
def replace_iterators_customs(row_element, iterator_dict, custom_dict):
    for key, value in iterator_dict.items():
        row_element = row_element.replace(f'<Iterator{key}>', value)
    for key, value in custom_dict.items():
        row_element = row_element.replace(f'<CustomParameter{key}>', value)    
    return row_element

# Replace iterators and maptokens one at a time in a row
def replace_iterators_maptokens_customs(row, iterator_dict,map_dict, custom_dict, header):
    revised_row = [replace_iterators_customs(row_element, iterator_dict, custom_dict) for row_element in row]
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

#def replace_maptoken(row)

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


