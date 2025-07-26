import csv
import subprocess
import os 
import sys
import re
import xml.etree.ElementTree as ET
import pandas as pd
import time
import file_functions as fi

#Modified from indexed_ctvdecoder_gen
## Use this script to take a ctv decoder input file, and generate a new ctv decoder which is indexed, and delimited by field
def process_CTV(csv_input_file, log_file, test_name_prefix, MAX_VALUE_PRINT=1433):
    # Read the CSV file
    csv_input_file = fi.process_file_input(csv_input_file)
    if not os.path.exists(log_file):
        log_file=log_file
    else:
        base, ext = os.path.splitext(log_file)
        i = 1
        log_file = f"{base}_{i}{ext}"
    while os.path.exists(log_file):
        i += 1
        log_file = f"{base}_{i}{ext}"
    with open(csv_input_file, mode='r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
# # Extract headers of csv
    # Ask the user for the columns and values to filter by
    available_columns = rows[0].keys()
    header_names = list(available_columns)
    # get headers from between Pin and Size
    counter = 0
    for i in range(len(header_names)):
        if header_names[i] == 'Size':
            break
        counter = counter + 1
    tag_header_names = header_names[1:counter]#LEAVE THIS IN

    # Detect which token key is available (storageToken or ItuffToken)
    token_key = "ItuffToken"
    if 'ItuffToken' in available_columns:
        token_key = 'ItuffToken'
    elif 'StorageToken' in available_columns:
        token_key = 'StorageToken'
    # Apply the function to every token in rows
    for row in rows:
        original_value = row[token_key]
        new_value = replace_placeholders(original_value, row)
        row[token_key] = new_value  #Update the row with the new value
    
    # Sort rows by token_key
    rows = sorted(rows, key=lambda row: row[token_key])

# # Write the processed data to a new CSV file
    with open(log_file, mode='w', newline='') as file:
        fieldnames = ['Index'] 
        #fieldnames = []
        for i in range(len(tag_header_names)): fieldnames.append(f"{tag_header_names[i]}")
        fieldnames.append('Name')
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        # Dictionary to track occurrences of each unique token_key
        token_occurrence_count = {}
        
        for row in rows:
            #Skips if no Ituff Token modifiers
            if row[token_key] == '-' and "CLK" in test_name_prefix.upper():#solution for clkutils (maybe add an extra qualifier about test type)
                continue
            if row[token_key] == '' or row[token_key]=='-' and "MIO_DDR" in test_name_prefix.upper():#solution for mio
                continue
            elif row[token_key] == '' or row[token_key]=='-':
                test_name= f"{test_name_prefix}"  
            else:
                test_name = f"{test_name_prefix +'_' + row[token_key]}"                
            
            # Track occurrences and get current index for this test_name
            if test_name not in token_occurrence_count:
                token_occurrence_count[test_name] = 0
            current_index = token_occurrence_count[test_name]
            
            # Create row dict with Index and Name
            row_dict = {'Index': current_index, 'Name': test_name}
                
            # Add the tag header values dynamically
            for i in range(len(tag_header_names)):
                row_dict[f"{tag_header_names[i]}"] = row[tag_header_names[i]]
                
            writer.writerow(row_dict)
            
            # Increment the count for this test_name
            token_occurrence_count[test_name] += 1
    return 
#Repeat from indexed_ctvdecoder_gen
def ingest_input(input_file):
    input_data = []
    with open(input_file, "r") as file:
        reader = csv.reader(file)
        for line_number, row in enumerate(reader):
            if line_number == 0:
                names = row
            else:
                input_data.append(row)
    return names,input_data

def replace_placeholders(field_value, row):
    placeholders = re.findall(r'<(.*?)>', str(field_value))
    for ph in placeholders:
        if ph in row:
            replacement = str(row[ph])
            field_value = field_value.replace(f'<{ph}>', replacement)
    return field_value

#Modified from indexed_ctvdecoder_gen
def index_CTV(input_file,test_name,module_name='',place_in='',mode='',config_number=''):
    #module_name = input("Name of test module prefix (e.g. CLK_PLL_BASE):")#removed as input is provided into function
    if module_name != '':
        test_name = module_name + "::" + test_name

    #aDD LOGIC back to separate module name

    #print(f"Processing {test_name}")
    # process each original input csv, get important information from it, and create a new "log" csv which is easier to use
    process_CTV(input_file, 'log.csv', test_name)
    # Apply the function to each element in 'Column1'
    combined_df = pd.read_csv('log.csv')
    #combined_df['Name'] = combined_df.apply(lambda row: replace_placeholders(row['Name'], row), axis=1) 
    combined_df['Name_Index'] = combined_df['Name']+'_'+combined_df['Index'].astype(str)
    combined_df = combined_df.sort_values(by=['Name','Index'])
    combined_df['combined_string'] = ''
    
    #RIGHT HERE ABDI PLEASE ADD THE FOLLOWING
    # Replace cells that have only -, nan, or blanks with &
    for col in combined_df.columns:
        # Create a mask for cells that are -, nan, or blank
        if col == 'combined_string':
            continue
        mask = (
            combined_df[col].isna() |                                    # NaN values
            (combined_df[col].astype(str).str.strip() == '') |          # Empty strings
            (combined_df[col].astype(str).str.strip() == '-') |         # Just dashes
            (combined_df[col].astype(str).str.upper() == 'NAN')         # 'NaN' strings
        )
   
        # Replace matching cells with &
        combined_df.loc[mask, col] = '&'    
  
    #Instead, loop through columns
    #print(combined_df)
    for col in combined_df.columns:
        is_all_empty = combined_df[col].isna().all() or (combined_df[col].astype(str).str.strip() == '').all() or (combined_df[col].astype(str).str.strip() == '-').all() or (combined_df[col].astype(str).str.strip() == '&').all()
        if col == "Field":
            combined_df['combined_string'] = combined_df['combined_string'] + '---' + combined_df[f'{col}'].astype(str)
            #print(col)
            break
        elif is_all_empty:
            combined_df.drop(columns=[col], inplace=True)
            continue
        elif col != "Index" and col != "Name" and col != "Name_Index":
            combined_df['combined_string'] = combined_df['combined_string'] + '---' + combined_df[f'{col}'].astype(str)
            #print(col)
    # Strip leading '---' if present. Using --- instead of @ to avoid jsl jmp column error
    combined_df['combined_string'] = combined_df['combined_string'].str.lstrip('---')


    colon_index=test_name.find('::')
    if config_number != '':
        config_number = f'_{config_number}'
    else:
        config_number = ''


    # data_out_file = f'{test_name}{config_number}{ituff_suffix}indexed.csv'
        # Get the first non-blank or hyphen ItuffToken for file naming
    first_ituff_token = ''
    if 'Name' in combined_df.columns:
        for token in combined_df['Name'].tolist():
            if pd.notna(token) and str(token).strip() != '' and str(token).strip() != '-' and str(token).strip().replace(test_name,'').split('::')[-1] != '':
                first_ituff_token = str(token).strip().replace(test_name,'').split('::')[-1]
                break

     # Include ItuffToken in output file name if available
    if mode == 'CtvTag':
        ituff_suffix = f'{first_ituff_token}' if first_ituff_token else '_' + config_number
    else:
        ituff_suffix = ''


    out_file = ''
    if colon_index != -1:
        out_file = os.path.join(place_in,f'{module_name}_{test_name[colon_index+len("::"):]}{config_number}{ituff_suffix}_indexed.csv')
    else:
        out_file = os.path.join(place_in,f'{test_name}{config_number}{ituff_suffix}_indexed.csv')
    out_file = fi.check_write_permission(out_file)

    combined_df.to_csv(out_file,index = False)
    print(out_file, "is indexed!")
    #remove log
    os.remove('log.csv')


    # Find the position of the last backslash and '.csv'
    last_backslash_index = input_file.rfind('\\')
    last_forwardslash_index = input_file.rfind('/')
    last_slash_index = max(last_backslash_index,last_forwardslash_index)
    end_index = input_file.find('.csv', last_slash_index)
    csv_identifier = ''    
    # Extract the substring
    if mode != 'CtvTag':
        if last_slash_index != -1 and end_index != -1 and 'decoded' in input_file:
            csv_identifier = input_file[last_slash_index+1:end_index].strip('deco').strip('_')
        elif last_slash_index != -1 and end_index != -1:
            csv_identifier = input_file[last_slash_index+1:end_index]

    tag_header_names = get_columns_btwn_index_name(combined_df)

    return out_file, csv_identifier, tag_header_names

def get_columns_btwn_index_name(df):
    columns = df.columns.tolist()
    
    try:
        index_pos = columns.index('Index')
        name_pos = columns.index('Name')
        
        # Return columns between Index and Name (exclusive)
        tag_header_columns = columns[index_pos + 1:name_pos]

        return tag_header_columns
    except ValueError:
        # If 'Index' or 'Name' columns don't exist, return empty list
        return []


if __name__ == "__main__":
    input_file = input("Absolute CTV decoder csv file path: ")
    test_name = input('ITUFF test name: ')
    #test_name = 'LJPLL_BASE_CTVDEC_K_SDTBEGIN_TAP_INF_NOM_X_FLL_RELOCK'
    module_name = 'CLK_PLL_BASE'
    #index_CTV(input_file,test_name)
    index_CTV(input_file,test_name,module_name)

