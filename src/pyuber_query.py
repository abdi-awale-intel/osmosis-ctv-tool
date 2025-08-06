import pandas as pd
import PyUber
import csv
import pandas
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import time
import sys
import os
import file_functions as fi
#for suffixes...
import re
from collections import defaultdict


def execute_pyuber_query(token_chunks, lot_condition, wafer_condition, program_condition, prefetch, databases, intermediary_file,test_name):
    """Execute PyUber query with given parameters and return whether data was found"""
    cursor = ''
    data_found = False
    finish_loops = False
    first_iteration = True

    for database in databases:
        missing_counter = 0 #remove this if data gets too big #yet another flaw with the quick hardcoded route
        for token_chunk in token_chunks:
            # place tokens into SQL query
            print('Running Query')
            query = f"""
            /*BEGIN SQL*/
            SELECT /*+  use_nl (dt) */
                    v0.lot AS lot
                    ,v0.operation AS operation
                    ,v0.program_name AS program_name
                    ,v0.wafer_id AS wafer_id
                    ,dt.sort_x AS sort_x
                    ,dt.sort_y AS sort_y
                    ,dt.interface_bin AS interface_bin
                    ,dt.functional_bin AS functional_bin
                    ,t0.test_name AS test_name
                    ,Replace(Replace(Replace(Replace(Replace(Replace(str.string_result,',',';'),chr(9),' '),chr(10),' '),chr(13),' '),chr(34),''''),chr(7),' ') AS string_result
            FROM 
            A_Testing_Session v0
            INNER JOIN A_Test t0 ON t0.devrevstep = v0.devrevstep AND (t0.program_name = v0.program_name or t0.program_name is null or v0.program_name is null)  AND (t0.temperature = v0.temperature OR (t0.temperature IS NULL AND v0.temperature IS NULL))
            INNER JOIN A_Device_Testing dt ON v0.lao_start_ww + 0 = dt.lao_start_ww AND v0.ts_id + 0 = dt.ts_id
            LEFT JOIN A_String_Result str ON v0.lao_start_ww = str.lao_start_ww AND v0.ts_id = str.ts_id AND dt.dt_id = str.dt_id AND t0.t_id = str.t_id
            WHERE 1=1
            AND      v0.valid_flag = 'Y' 
            AND      {lot_condition}
            AND      {wafer_condition}
            AND      t0.test_name IN ('{token_chunk}')
            
            AND      str.string_result IS NOT NULL  
            AND      v0.test_end_date_time >= TRUNC(SYSDATE) - {str(int(prefetch))}
            AND      {program_condition}
            /*END SQL*/
            """
                    #,dt.functional_bin AS functional_bin
            #AND      t0.test_name LIKE '{test_name}'
            query_out = fi.check_write_permission("query.txt")
            with open(query_out,'w') as queryfile:
                queryfile.write(query)

            start_time = time.time()
            #connect to database and execute query
            conn = PyUber.connect(datasource=database)
            cursor = conn.execute(query)

            # Record the end time and calculate the duration
            end_time = time.time()
            duration = end_time - start_time
            print(f"Query executed in {duration:.2f} seconds.")


            results = cursor.fetchall()
            if results:
                columns = [col[0] for col in cursor.description]
                missing_counter = 0
                # Open the file in write mode if it's the first iteration, otherwise append mode
                mode = 'w' if first_iteration else 'a'
                with open(intermediary_file, mode, newline='') as outfile:
                    writer = csv.writer(outfile)
                    if first_iteration:  # Write headers only once
                        writer.writerow(columns)
                        first_iteration = False  # Set flag to False after first write
                    for row in results:
                        writer.writerow(row)
                    data_found = True
            else:
                print('Problem with query! Likely no data.')
                missing_counter += 1
                if first_iteration:  # Only create empty file on first iteration
                    intermediary_file = fi.check_write_permission(intermediary_file)
                    with open(intermediary_file,'w', newline='') as outfile:
                        writer = csv.writer(outfile)
                        writer.writerow(['LOT','WAFER_ID','SORT_X','SORT_Y','INTERFACE_BIN','FUNCTIONAL_BIN'])
                if missing_counter >= 5:
                    break
            if token_chunk == token_chunks[-1] and data_found:
                finish_loops = True
                break
        if finish_loops:
            break
    
    return data_found

def pivot_data(intermediary_file):
    # Load CSV
    df1 = pd.read_csv(intermediary_file)

    # Concatenate the columns 'LOT', 'WAFER_ID', 'SORT_X', and 'SORT_Y' with underscores
    df1['Lot_WafXY'] = df1['LOT'].astype(str) + "_" + df1['WAFER_ID'].astype(str) + "_" + df1['SORT_X'].astype(str) + "_" + df1['SORT_Y'].astype(str)

    id_cols = ['Lot_WafXY', 'LOT', 'WAFER_ID', 'SORT_X', 'SORT_Y','INTERFACE_BIN','FUNCTIONAL_BIN']
    # Pivot the DataFrame - "split" or unstack in JMP, pivoting string results to their own columns by test name for each unit
    try:
        df_pivot = df1.pivot_table(
            index=id_cols,
            columns='TEST_NAME',
            values='STRING_RESULT',
            aggfunc='first'  # or another aggregation if duplicates exist
        ).reset_index()
    except:
        print("Did not pivot.")
        df_pivot = df1

    # Save the unstacked dataframe back to the same CSV file (overwrites original)
    df_pivot.to_csv(intermediary_file, index=False)###this is the the datainput file
    return df_pivot

#def uber_request(indexed_input, test_name_file,test_type, output_folder,extra_identifier=''):
def uber_request(indexed_input, test_name_file, test_type='', output_folder='', program='DAC%', extra_identifier='', lot = ['Not Null'], wafer_id = ['Not Null'], prefetch = '1', databases = ['D1D_PROD_XEUS','F24_PROD_XEUS'],config_number = '',mode=''):
    decoder_df = pd.read_csv(indexed_input)
    test_name = test_name_file
    #print(output_folder)
    indexed_input = fi.process_file_input(indexed_input)
    if output_folder == '':
        output_folder = os.path.dirname(indexed_input)
        if output_folder != '':
            output_folder = output_folder + '\\'
    #Define datainput from SQL csv and datacombined after SQL file paths
    if '::' in test_name_file:
        test_name_file = test_name_file.split('::')[1]


    # Get the first non-blank or hyphen ItuffToken for file naming
    first_ituff_token = ''
    if 'Name' in decoder_df.columns:
        for token in decoder_df['Name'].tolist():
            if pd.notna(token) and str(token).strip() != '' and str(token).strip() != '-' and str(token).replace(test_name_file,'').split('::')[-1] != '':
                first_ituff_token = str(token).strip().replace(test_name_file,'').split('::')[-1]
                break
    # Include ItuffToken in output file name if available
    if mode == 'CtvTag' or first_ituff_token:
        ituff_suffix = f'{first_ituff_token}' if first_ituff_token else '_' + config_number
    else:
        ituff_suffix = ''

    intermediary_file = f'{output_folder}{test_name_file}{ituff_suffix}_datapulled.csv'
    intermediary_file = fi.check_write_permission(intermediary_file)
    data_out_file=''    
    if extra_identifier != '':
        data_out_file = f'{output_folder}{extra_identifier}_{test_name_file}{ituff_suffix}_dataoutput.csv'
        data_out_file = data_out_file.replace('decoded','')
    else:
        data_out_file = f'{output_folder}{test_name_file}{ituff_suffix}_dataoutput.csv'
        data_out_file = data_out_file.replace('decoded','')
    # load decoder csv to get token names
    #decoder_name = input("Enter name of decoder file:")#input argument or just feed the output file #make index CTV return a file path#remove percent signs
    
    token_names = decoder_df['Name'].tolist()
    #print(token_names)
    token_set = set(token_names)
    token_names = list(token_set)
    token_names_upper= [token_name.upper() for token_name in token_names]
    token_names.extend(token_names_upper)
    token_names = list(set(token_names))

    max_bytes = 63000 #Estimated max number of bytes for a smaller SQL query system
    
    #print(token_names)
    if test_type == 'ClkUtils':
        token_1 = modify_tokens(token_names, "1")
        token_2 = modify_tokens(token_names, "2")
        token_3 = modify_tokens(token_names, "3")
        token_4 = modify_tokens(token_names, "4")
        token_5 = modify_tokens(token_names, "5")
        token_6 = modify_tokens(token_names, "6")
        token_7 = modify_tokens(token_names, "7")
        token_8 = modify_tokens(token_names, "8")
        token_9 = modify_tokens(token_names, "9")
        token_10 = modify_tokens(token_names, "10")
        token_11 = modify_tokens(token_names, "11")
        token_12 = modify_tokens(token_names, "12")
        token_13 = modify_tokens(token_names, "13")
        token_14 = modify_tokens(token_names, "14")
        token_15 = modify_tokens(token_names, "15")
        token_16 = modify_tokens(token_names, "16")
        token_17 = modify_tokens(token_names, "17")
        token_18 = modify_tokens(token_names, "18")
        token_19 = modify_tokens(token_names, "19")
        token_20 = modify_tokens(token_names, "20")      
        token_names_list = token_names + token_1 + token_2 + token_3 + token_4 + token_5 + token_6 + token_7 + token_8 + token_9 + token_10 + token_11 + token_12 + token_13 + token_14 + token_15 + token_16 + token_17 + token_18 + token_19 + token_20
    else:
        token_names_to_modify = [token_name for token_name in token_names if not token_name.upper().endswith('_PASS') and not token_name.upper().endswith('_FAIL')]
        token_names_FAIL = modify_tokens(token_names_to_modify, "FAIL")
        token_names_PASS = modify_tokens(token_names_to_modify, "PASS")
        token_names_pass = modify_tokens(token_names_to_modify, "pass")
        token_names_fail = modify_tokens(token_names_to_modify, "fail")
        token_names_FAIL_1 = modify_tokens(token_names_to_modify, "FAIL_1")
        token_names_PASS_1 = modify_tokens(token_names_to_modify, "PASS_1")
        token_names_pass_1 = modify_tokens(token_names_to_modify, "pass_1")
        token_names_fail_1 = modify_tokens(token_names_to_modify, "fail_1")
        token_names_FAIL_2 = modify_tokens(token_names_to_modify, "FAIL_2")
        token_names_PASS_2 = modify_tokens(token_names_to_modify, "PASS_2")
        token_names_pass_2 = modify_tokens(token_names_to_modify, "pass_2")
        token_names_fail_2 = modify_tokens(token_names_to_modify, "fail_2")
        token_names_FAIL_3 = modify_tokens(token_names_to_modify, "FAIL_3")
        token_names_PASS_3 = modify_tokens(token_names_to_modify, "PASS_3")
        token_names_pass_3 = modify_tokens(token_names_to_modify, "pass_3")
        token_names_fail_3 = modify_tokens(token_names_to_modify, "fail_3")
        token_names_FAIL_4 = modify_tokens(token_names_to_modify, "FAIL_4")
        token_names_PASS_4 = modify_tokens(token_names_to_modify, "PASS_4")
        token_names_pass_4 = modify_tokens(token_names_to_modify, "pass_4")
        token_names_fail_4 = modify_tokens(token_names_to_modify, "fail_4")
        token_names_FAIL_5 = modify_tokens(token_names_to_modify, "FAIL_5")
        token_names_PASS_5 = modify_tokens(token_names_to_modify, "PASS_5")
        token_names_pass_5 = modify_tokens(token_names_to_modify, "pass_5")
        token_names_fail_5 = modify_tokens(token_names_to_modify, "fail_5")
        token_names_FAIL_6 = modify_tokens(token_names_to_modify, "FAIL_6")
        token_names_PASS_6 = modify_tokens(token_names_to_modify, "PASS_6")
        token_names_pass_6 = modify_tokens(token_names_to_modify, "pass_6")
        token_names_fail_6 = modify_tokens(token_names_to_modify, "fail_6")
        token_names_FAIL_7 = modify_tokens(token_names_to_modify, "FAIL_7")
        token_names_PASS_7 = modify_tokens(token_names_to_modify, "PASS_7")
        token_names_pass_7 = modify_tokens(token_names_to_modify, "pass_7")
        token_names_fail_7 = modify_tokens(token_names_to_modify, "fail_7")
        token_names_FAIL_8 = modify_tokens(token_names_to_modify, "FAIL_8")
        token_names_PASS_8 = modify_tokens(token_names_to_modify, "PASS_8")
        token_names_pass_8 = modify_tokens(token_names_to_modify, "pass_8")
        token_names_fail_8 = modify_tokens(token_names_to_modify, "fail_8")
        token_names_FAIL_9 = modify_tokens(token_names_to_modify, "FAIL_9")
        token_names_PASS_9 = modify_tokens(token_names_to_modify, "PASS_9")
        token_names_pass_9 = modify_tokens(token_names_to_modify, "pass_9")
        token_names_fail_9 = modify_tokens(token_names_to_modify, "fail_9")
        token_names_FAIL_10 = modify_tokens(token_names_to_modify, "FAIL_10")
        token_names_PASS_10 = modify_tokens(token_names_to_modify, "PASS_10")
        token_names_pass_10 = modify_tokens(token_names_to_modify, "pass_10")
        token_names_fail_10 = modify_tokens(token_names_to_modify, "fail_10")
        token_names_FAIL_11 = modify_tokens(token_names_to_modify, "FAIL_11")
        token_names_PASS_11 = modify_tokens(token_names_to_modify, "PASS_11")
        token_names_pass_11 = modify_tokens(token_names_to_modify, "pass_11")
        token_names_fail_11 = modify_tokens(token_names_to_modify, "fail_11")
        token_names_FAIL_12 = modify_tokens(token_names_to_modify, "FAIL_12")
        token_names_PASS_12 = modify_tokens(token_names_to_modify, "PASS_12")
        token_names_pass_12 = modify_tokens(token_names_to_modify, "pass_12")
        token_names_fail_12 = modify_tokens(token_names_to_modify, "fail_12")
        token_names_FAIL_13 = modify_tokens(token_names_to_modify, "FAIL_13")
        token_names_PASS_13 = modify_tokens(token_names_to_modify, "PASS_13")
        token_names_pass_13 = modify_tokens(token_names_to_modify, "pass_13")
        token_names_fail_13 = modify_tokens(token_names_to_modify, "fail_13")
        token_names_FAIL_14 = modify_tokens(token_names_to_modify, "FAIL_14")
        token_names_PASS_14 = modify_tokens(token_names_to_modify, "PASS_14")
        token_names_pass_14 = modify_tokens(token_names_to_modify, "pass_14")
        token_names_fail_14 = modify_tokens(token_names_to_modify, "fail_14")
        token_names_FAIL_15 = modify_tokens(token_names_to_modify, "FAIL_15")
        token_names_PASS_15 = modify_tokens(token_names_to_modify, "PASS_15")
        token_names_pass_15 = modify_tokens(token_names_to_modify, "pass_15")
        token_names_fail_15 = modify_tokens(token_names_to_modify, "fail_15")
        token_names_FAIL_16 = modify_tokens(token_names_to_modify, "FAIL_16")
        token_names_PASS_16 = modify_tokens(token_names_to_modify, "PASS_16")
        token_names_pass_16 = modify_tokens(token_names_to_modify, "pass_16")
        token_names_fail_16 = modify_tokens(token_names_to_modify, "fail_16")
        token_names_FAIL_17 = modify_tokens(token_names_to_modify, "FAIL_17")
        token_names_PASS_17 = modify_tokens(token_names_to_modify, "PASS_17")
        token_names_pass_17 = modify_tokens(token_names_to_modify, "pass_17")
        token_names_fail_17 = modify_tokens(token_names_to_modify, "fail_17")
        token_names_FAIL_18 = modify_tokens(token_names_to_modify, "FAIL_18")
        token_names_PASS_18 = modify_tokens(token_names_to_modify, "PASS_18")
        token_names_pass_18 = modify_tokens(token_names_to_modify, "pass_18")
        token_names_fail_18 = modify_tokens(token_names_to_modify, "fail_18")
        token_names_FAIL_19 = modify_tokens(token_names_to_modify, "FAIL_19")
        token_names_PASS_19 = modify_tokens(token_names_to_modify, "PASS_19")
        token_names_pass_19 = modify_tokens(token_names_to_modify, "pass_19")
        token_names_fail_19 = modify_tokens(token_names_to_modify, "fail_19")
        token_names_FAIL_20 = modify_tokens(token_names_to_modify, "FAIL_20")
        token_names_PASS_20 = modify_tokens(token_names_to_modify, "PASS_20")
        token_names_pass_20 = modify_tokens(token_names_to_modify, "pass_20")
        token_names_fail_20 = modify_tokens(token_names_to_modify, "fail_20")
        
        
        token_names_missing = [token_name for token_name in token_names if token_name.upper().endswith('_PASS') or token_name.upper().endswith('_FAIL')]
        token_1 = token_names_FAIL_1 + token_names_PASS_1 + token_names_pass_1 + token_names_fail_1
        token_2 = token_names_FAIL_2 + token_names_PASS_2 + token_names_pass_2 + token_names_fail_2
        token_3 = token_names_FAIL_3 + token_names_PASS_3 + token_names_pass_3 + token_names_fail_3
        token_4 = token_names_FAIL_4 + token_names_PASS_4 + token_names_pass_4 + token_names_fail_4
        token_5 = token_names_FAIL_5 + token_names_PASS_5 + token_names_pass_5 + token_names_fail_5
        token_6 = token_names_FAIL_6 + token_names_PASS_6 + token_names_pass_6 + token_names_fail_6
        token_7 = token_names_FAIL_7 + token_names_PASS_7 + token_names_pass_7 + token_names_fail_7
        token_8 = token_names_FAIL_8 + token_names_PASS_8 + token_names_pass_8 + token_names_fail_8
        token_9 = token_names_FAIL_9 + token_names_PASS_9 + token_names_pass_9 + token_names_fail_9
        token_10 = token_names_FAIL_10 + token_names_PASS_10 + token_names_pass_10 + token_names_fail_10
        token_11 = token_names_FAIL_11 + token_names_PASS_11 + token_names_pass_11 + token_names_fail_11
        token_12 = token_names_FAIL_12 + token_names_PASS_12 + token_names_pass_12 + token_names_fail_12
        token_13 = token_names_FAIL_13 + token_names_PASS_13 + token_names_pass_13 + token_names_fail_13
        token_14 = token_names_FAIL_14 + token_names_PASS_14 + token_names_pass_14 + token_names_fail_14
        token_15 = token_names_FAIL_15 + token_names_PASS_15 + token_names_pass_15 + token_names_fail_15
        token_16 = token_names_FAIL_16 + token_names_PASS_16 + token_names_pass_16 + token_names_fail_16
        token_17 = token_names_FAIL_17 + token_names_PASS_17 + token_names_pass_17 + token_names_fail_17
        token_18 = token_names_FAIL_18 + token_names_PASS_18 + token_names_pass_18 + token_names_fail_18
        token_19 = token_names_FAIL_19 + token_names_PASS_19 + token_names_pass_19 + token_names_fail_19
        token_20 = token_names_FAIL_20 + token_names_PASS_20 + token_names_pass_20 + token_names_fail_20
        token_names_list = token_names_FAIL + token_names_PASS + token_names_pass + token_names_fail + token_names_missing + token_1 + token_2 + token_3 + token_4 + token_5 + token_6 + token_7 + token_8 + token_9 + token_10 + token_11 + token_12 + token_13 + token_14 + token_15 + token_16 + token_17 + token_18 + token_19 + token_20
        #token_names_string = "',\n'".join(token_names)
    token_chunks = list(split_by_byte_size(token_names_list, max_bytes))
    #print(token_names_string) #Useful for testing if indexed_SmartCTV was correct

    #settle for 1-9 and regular

    # Determine the condition for lot
    if lot == ['Not Null'] or not lot or lot == ['']:
        lot_condition = "v0.lot IS NOT NULL"
    else:
        #lot_condition = f"v0.lot IN ({','.join(f"'{l}'" for l in lot)})"
        lot_condition = "v0.lot IN ({})".format(','.join("'{}'".format(l) for l in lot))

    # Determine the condition for wafer_id
    if wafer_id == ['Not Null'] or not wafer_id or wafer_id == ['']:
        wafer_condition = "v0.wafer_id IS NOT NULL"
    else:
        wafer_condition = "v0.wafer_id IN ({})".format(','.join("'{}'".format(w) for w in wafer_id))
    # Determine the condition for program
    if '%' in program:
        program_condition = f"v0.program_name LIKE '{program}'"
    else:
        program_condition = f"v0.program_name = '{program}'"
    if not prefetch or prefetch=='nan':
        prefetch = 3
    if not databases:
        databases = ['D1D_PROD_XEUS','F24_PROD_XEUS']
    
    

    execute_pyuber_query(token_chunks, lot_condition, wafer_condition, program_condition, prefetch, databases, intermediary_file,test_name+'%')
    df_pivot = pivot_data(intermediary_file)
    # Read CSV
    df = pd.read_csv(intermediary_file)###this is the the datainput file

    '''#below is for addressing the mess of possibilities
    data_columns = df.columns.tolist()[5:]
    partially_empty_columns = [col for col in data_columns if (
        df[col].isna() |                                    # NaN values
        (df[col].astype(str).str.strip() == '') |          # Empty strings
        (df[col].astype(str).str.upper() == 'NAN') |       # 'NaN' strings
        (df[col].astype(str).str.upper() == 'NULL') |      # 'NULL' strings
        (df[col].astype(str).str.upper() == 'NONE')        # 'NONE' strings
    ).any()]
    
    suffix_num = 1
    file_temp = intermediary_file.split('.')
    file_temp[-2] = file_temp[-2] + '_pe'
    suffixed_file = '.'.join(file_temp)
    part_data_found = True
    partial_tokens = partially_empty_columns.copy()
    suffixed_tokens = [] # this is a running total that will be used to combine later
    while part_data_found:
        suffixed_part_empty = [col+f'_{str(suffix_num)}' for col in partial_tokens]
        token_chunks = list(split_by_byte_size(suffixed_part_empty, max_bytes))
        part_data_found = execute_pyuber_query(token_chunks, lot_condition, wafer_condition, program_condition, prefetch, databases, suffixed_file)
        pivot_data(suffixed_file)
        dfs = pd.read_csv(suffixed_file)
        #merge columns
        partial_tokens = dfs.columns.tolist()[5:]
        suffixed_tokens.extend(partial_tokens)
        id_cols = dfs.columns[:5]
        df =   df.merge(
                            dfs, 
                            on=id_cols, 
                            how='outer'
                        )
#need way to detect new data columns
#merge them into df
#flag them for future
#replace suffix mod by using split and replace
#



    suffix_num = 1
    missing_columns = list(set(token_names_list) - set(data_columns))    
    file_temp[-2] = file_temp[-2].replace('_pe','') + '_miss'
    missing_file = '.'.join(file_temp)
    miss_data_found = True
    while miss_data_found:
        pass

    #token_names_list
#above is for obtaining the data for all the suffixed columns.'''

    #below is for combining the suffixed data
    '''TRIAL SECTION FOR SUFFIXES'''
    # Below is for combining the suffixed data

    #print(df.columns.tolist())
    '''BEGIN Combined suffix columns'''
    # Get all data columns (excluding first 5 ID columns)
    data_columns = df.columns[7:]

    # Find columns with numeric suffixes using regex
    suffix_pattern = r'^(.+)_(\d+)$'  # Matches base_name_number
    suffix_groups = defaultdict(list)

    for col in data_columns:
        match = re.match(suffix_pattern, col)
        if match:
            base_name = match.group(1)  # Everything before _number
            suffix_num = int(match.group(2))  # The number
            suffix_groups[base_name].append((col, suffix_num))

    # Process each group of suffixed columns
    columns_to_drop = []

    for base_name, suffix_list in suffix_groups.items():
        if len(suffix_list) > 1:  # Only process if there are multiple suffixed columns
            # Sort by suffix number to maintain order
            suffix_list.sort(key=lambda x: x[1])
            
            # Extract just the column names in order
            cols_to_combine = [col_name for col_name, _ in suffix_list]
            
            # Create new column name with underscore after base name
            new_column_name = f"{base_name}_"
            
            # Combine the columns with pipe separator, handling NaN values
            df[new_column_name] = df[cols_to_combine].fillna('').astype(str).apply(
                lambda row: '|'.join([val for val in row if val != '' and val.lower() != 'nan']), 
                axis=1
            )
            
            # Mark original suffixed columns for removal
            columns_to_drop.extend(cols_to_combine)

    # Drop the original suffixed columns
    if columns_to_drop:
        df.drop(columns=columns_to_drop, inplace=True)

    #df.to_csv(intermediary_file, index=False)
    '''BEGIN Combine partially empty columns'''
    # Merge basename_ columns with existing basename columns
    data_columns_updated = df.columns[7:]  # Get updated column list after suffix processing

    merge_pairs = []
    for col in data_columns_updated:
        if col.endswith('_'):
            base_name = col[:-1]  # Remove trailing underscore
            if base_name in data_columns_updated:
                merge_pairs.append((base_name, col))
            else:
                # If base_name is not found, it means it's a new column
                df[base_name] = df[col]
                df.drop(columns=[col], inplace=True)

    # Process each merge pair
    for original_col, suffixed_col in merge_pairs:
        # Simple row-by-row merge: use original_col data if not blank, otherwise use suffixed_col data
        df[original_col] = df.apply(
            lambda row: str(row[original_col]) if (pd.notna(row[original_col]) and str(row[original_col]).strip() != '' and str(row[original_col]).lower() != 'nan') 
                    else str(row[suffixed_col]) if (pd.notna(row[suffixed_col]) and str(row[suffixed_col]).strip() != '' and str(row[suffixed_col]).lower() != 'nan')
                    else '', 
            axis=1
        )
        
        # Drop the suffix column after merging
        df.drop(columns=[suffixed_col], inplace=True)


    #df.to_csv(intermediary_file, index=False)
    #print(df.columns.tolist())
    '''END OF TRIAL SECTION FOR SUFFIXES'''
#below is for depiping the data
    if test_type == 'ClkUtils':
            cols_to_drop = df.columns[7:]
            # Process each column that needs to be split
            new_columns = []
            for col_name in cols_to_drop:
                # Split the column into multiple columns
                split_cols = df[col_name].str.split('|', expand=True)
                # Rename columns with suffixes _0, _1, ...
                split_cols = split_cols.rename(columns=lambda x: f"{col_name}_{x}")
                new_columns.append(split_cols)
            
            # Concatenate all new split columns to original dataframe
            if new_columns:
                df = pd.concat([df] + new_columns, axis=1)
            df.drop(columns=cols_to_drop, inplace=True)
    else:
        cols_to_drop = []
        pass_cols = [col for col in df.columns if col.upper().endswith('_PASS')]#Empty if ClkUtils
    
        for pass_col in pass_cols:
            test_name = pass_col[:-5]  # Remove '_PASS'
            fail_col = test_name + '_fail'
            Fail_col = test_name + '_FAIL'
            combined_col = test_name + '_combined'
            # Check if the fail column exists
            if fail_col in df.columns or Fail_col in df.columns:
                # Generate combined string
                if fail_col in df.columns:
                    df[combined_col] = df.apply(lambda row: combine_pipe_fields(str(row[pass_col]), str(row[fail_col])), axis=1)
                else:
                    df[combined_col] = df.apply(lambda row: combine_pipe_fields(str(row[pass_col]), str(row[Fail_col])), axis=1)
            else:
                # _FAIL column missing, combine _PASS with empty string
                df[combined_col] = df[pass_col].astype(str).apply(lambda x: combine_pipe_fields(x, ''))

            # Split the combined column into multiple columns
            split_cols = df[combined_col].str.split('|', expand=True)

            # Rename columns with suffixes _0, _1, ...
            split_cols = split_cols.rename(columns=lambda x: f"{test_name}_combined_{x}")

            # Concatenate split columns to original dataframe
            df = pd.concat([df, split_cols], axis=1)

            #print(df.columns.tolist())
        # Drop columns that contain 'CTV' but do NOT contain 'combined_'
            cols_to_drop.extend([col for col in df.columns if test_name in col and 'combined_' not in col])#Only affects CTV
        
        cols_to_drop = list(set(cols_to_drop))  # Remove duplicates
        df.drop(columns=cols_to_drop, inplace=True)#####QUESTION THIS LOGIC IF NEW COLUMNS

        # Remove '_combined' substring from any column name that contains it
        df.rename(columns=lambda x: x.replace('_combined', '') if '_combined' in x else x, inplace=True)
  # Regex pattern to match the column patterns
    pattern = rf'^{test_name_file.upper()}(_(?:PASS|FAIL)(?:_\d+)?)?$'


    # Drop if column has data contain "TDO" in the data
    if  "MIO_DDR" in test_name_file.upper():
        for col in df.columns:
            if re.match(pattern, col.upper()):
                # Drop the column if it matches the pattern
                df.drop(columns=col, inplace=True)

    for col in df.columns:
        if col.upper().endswith('_PASS') or col.upper().endswith('_FAIL'):
            if df[col].astype(str).str.contains('TDO', case=False, na=False).any():
                for col_df in df_pivot.columns:
                    if col in col_df:
                        df_pivot.drop(columns=col_df, inplace=True)
                         #print(f"Dropping column {col} due to TDO data.")
                df.drop(columns=col, inplace=True)

    # Exclude the first two columns from sorting
    excluded_columns = df.columns[:7]
    columns_to_sort = df.columns[7:]

    # Sort the remaining columns using the custom sorting key
    sorted_columns = sorted(columns_to_sort, key=sorting_key)

    # Combine the excluded columns with the sorted columns
    new_column_order = list(excluded_columns) + sorted_columns

    # Reindex the DataFrame with the new column order
    df = df.reindex(new_column_order, axis=1)

    # Create a set of original column names from df_pivot
    original_columns_set = set(df_pivot.columns)

    # Create a set of column names with '_PASS' and '_FAIL' removed
    modified_columns_set = set([col.upper().replace('_PASS', '').replace('_FAIL', '').replace('_1', '') for col in df_pivot.columns]
                               +[col.upper().replace('_PASS', '').replace('_FAIL', '') for col in df_pivot.columns]
                               +[col.upper() for col in df_pivot.columns])
    # Combine both sets to create a comprehensive set of column names
    df_columns_set = original_columns_set.union(modified_columns_set)

    # Convert the elements in df_columns_set to lowercase
    df_columns_set_lower = {col.lower() for col in df_columns_set}

    # Filter decoder_df to include only rows where 'Name' is in the comprehensive set of column names
    filtered_df = decoder_df[decoder_df['Name'].str.lower().isin(df_columns_set_lower)]
    #print(filtered_df)
    try:#passes if no data or all data mapped
        df.columns = df.columns[:7].tolist() + filtered_df['combined_string'].tolist()
        print('Mapping!')
        
        # For CLKUTILS tests, fill blank entries with defaults based on output_enable setting
        if 'CLKUTILS' in test_name_file.upper():
            for _, row in filtered_df.iterrows():
                if row['output_enable'] == False:  # If output_enable is False
                    column_name = row['combined_string']
                    default_value = row['default']
                    
                    # Check if the column exists in the dataframe
                    if column_name in df.columns:
                        # Replace blank/empty entries with the default value
                        mask = (df[column_name].isna()) | (df[column_name].astype(str).str.strip() == '') | (df[column_name].astype(str).str.upper() == 'NAN')
                        df.loc[mask, column_name] = default_value
        
        #print(df.columns.tolist())
    except:
        print(set(filtered_df['Name'].tolist()))
        print(df_columns_set)
        print('No mapping!')

    #print(data_out_file)
    data_out_file = fi.check_write_permission(data_out_file)
    df.to_csv(data_out_file, index=False)#originally df.to_csv
    print(data_out_file, "has been completed!")
    return intermediary_file, data_out_file


def modify_tokens(tokens, status):
    modified_tokens = []
    
    for token in tokens:
        # Check if token ends with underscore followed by number(s)
        import re
        parts = token.split('_')
        
        # Check if the last part is purely a number
        if parts and re.match(r'^\d+$', parts[-1]) and parts[-2] != status:
            # Insert status before the underscore and number
            number_part = parts[-1]  # e.g., "1"
            base_parts = parts[:-1]  # everything before the number
            base_part = '_'.join(base_parts)
            modified_token = f"{base_part}_{status}_{number_part}"
        else:
            # Append status at the end
            modified_token = f"{token}_{status}"
        
        # Add the modified token to the list
        modified_tokens.append(modified_token)
    
    return modified_tokens

def split_by_byte_size(lst, max_bytes):
    current_chunk = []
    current_size = 0

    for token in lst:
        # Calculate the size of the token when joined with commas and newlines
        token_size = len(f"'{token}',\n")
        
        # Check if adding this token would exceed the max byte size
        if current_size + token_size > max_bytes:
            current_chunk_joined = "',\n'".join(current_chunk)
            yield current_chunk_joined
            print('chunked')
            current_chunk = [token]
            current_size = token_size
        else:
            current_chunk.append(token)
            current_size += token_size

    # Yield the last chunk if it has any tokens
    if current_chunk:
        current_chunk_joined = "',\n'".join(current_chunk)
        yield current_chunk_joined

def combine_pipe_fields(pass_str, fail_str):
    pass_fields = pass_str.split('|')
    fail_fields = fail_str.split('|')

    max_len = max(len(pass_fields), len(fail_fields))

    # Extend shorter list with empty strings to match length
    pass_fields.extend([''] * (max_len - len(pass_fields)))

    fail_fields.extend([''] * (max_len - len(fail_fields)))

    combined_fields = []
    for p, f in zip(pass_fields, fail_fields):
        if p != '':
            combined_fields.append(p)
        else:
            combined_fields.append(f)

    return '|'.join(combined_fields)

def sorting_key(name):
    # Split the name by underscores
    parts = name.rsplit('_', 1)
    # Extract the last integer part for sorting
    try:
        last_int = int(parts[-1])
    except ValueError:
        last_int = float('inf')  # Use a large number if no integer is found
    # Return the name minus the last integer part and the integer itself
    return (parts[0], last_int)

if __name__ == "__main__":
    #indexed_input = "C:\\Users\\burtonr\\DAC_GIT\\Modules\\CLK_PLL_BASE\\InputFiles\\ConfigFiles\\Pre Offline tester 2\\CLK_PLL_BASE_LJPLL_BASE_CTVDEC_K_SDTBEGIN_TAP_INF_NOM_X_FLL_RELOCK_indexed_ctv_decoder.csv"
    indexed_input = "C:\\Users\\burtonr\\DAC_GIT\\Modules\\CLK_PLL_BASE\\InputFiles\\ConfigFiles\\CLK_PLL_BASE_LJPLL_BASE_CTVDEC_K_SDTBEGIN_TAP_INF_NOM_X_PLL_FREQCRAWL_indexed_ctv_decoder.csv"
    test_name_file = "CLK_PLL_BASE::LJPLL_BASE_CTVDEC_K_SDTBEGIN_TAP_INF_NOM_X_PLL_FREQCRAWL"
    test_type = ''
    output_folder = ''
    program = 'DAC%'
    #print(indexed_input)
    #print(test_type)
    #print(test_name_file)
    uber_request(indexed_input, test_name_file,test_type,output_folder, program)
    #for indexed_input, test_name_file in zip(inputs,tests):
    #    uber_request(indexed_input, test_name_file,output_folder)




