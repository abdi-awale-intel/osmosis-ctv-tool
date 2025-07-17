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
#def uber_request(indexed_input, test_name_file,test_type, output_folder,extra_identifier=''):
def uber_request(indexed_input, test_name_file, test_type='',needed_suffix=False, output_folder='', program='DAC%', extra_identifier='', lot = ['Not Null'], wafer_id = ['Not Null'], prefetch = '1', databases = ['D1D_PROD_XEUS','F24_PROD_XEUS']):
    #print(output_folder)
    indexed_input = fi.process_file_input(indexed_input)
    if output_folder == '':
        output_folder = os.path.dirname(indexed_input)
        if output_folder != '':
            output_folder = output_folder + '\\'
    #Define datainput from SQL csv and datacombined after SQL file paths
    if '::' in test_name_file:
        test_name_file = test_name_file.split('::')[1]

    intermediary_file = f'{output_folder}{test_name_file}_datapulled.csv'
    intermediary_file = fi.check_write_permission(intermediary_file)
    data_out_file=''
    if extra_identifier != '':
        data_out_file = f'{output_folder}{extra_identifier}_{test_name_file}_dataoutput.csv'
        data_out_file = data_out_file.replace('decoded','')
    else:
        data_out_file = f'{output_folder}{test_name_file}_dataoutput.csv'
        data_out_file = data_out_file.replace('decoded','')
    # load decoder csv to get token names
    #decoder_name = input("Enter name of decoder file:")#input argument or just feed the output file #make index CTV return a file path#remove percent signs
    decoder_df = pd.read_csv(indexed_input)
    token_names = decoder_df['Name'].tolist()
    #print(token_names)
    token_set = set(token_names)
    token_names = list(token_set)
    max_bytes = 31000 #Estimated max number of bytes for a smaller SQL query system
    
    #print(token_names)
    if needed_suffix and test_type != "SmartCtvDc":
        token_names_list = token_names
        #token_names_string = "',\n'".join(token_names)
    elif needed_suffix:
        token_names_to_modify = [token_name for token_name in token_names if not token_name.upper().endswith('_PASS') and not token_name.upper().endswith('_FAIL')]
        token_names_fail = modify_tokens(token_names_to_modify, "FAIL")
        token_names_pass = modify_tokens(token_names_to_modify, "PASS")
        token_names_missing = [token_name for token_name in token_names if token_name.upper().endswith('_PASS') or token_name.upper().endswith('_FAIL')]
        token_names_list = token_names_fail + token_names_pass + token_names_missing
    else:
        token_names_fail = [token_name + "_FAIL" for token_name in token_names if not token_name.upper().endswith('_PASS') and not token_name.upper().endswith('_FAIL')]
        token_names_pass = [token_name + "_PASS" for token_name in token_names if not token_name.upper().endswith('_PASS') and not token_name.upper().endswith('_FAIL')]
        token_names_missing = [token_name for token_name in token_names if token_name.upper().endswith('_PASS') or token_name.upper().endswith('_FAIL')]
        token_names_list = token_names_fail + token_names_pass + token_names_missing
        #token_names_string = "',\n'".join(token_names)
    token_chunks = list(split_by_byte_size(token_names_list, max_bytes))
    #print(token_names_string) #Useful for testing if indexed_SmartCTV was correct


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
    #print(token_chunks)
    cursor = ''
    data_found = False
    for database in databases:
        first_iteration = True
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
            AND      t0.test_name IN ('{token_chunk.upper()}')
            AND      str.string_result IS NOT NULL  
            AND      v0.test_end_date_time >= TRUNC(SYSDATE) - {str(int(prefetch))}
            AND      {program_condition}
            /*END SQL*/
            """

            #AND      t0.test_name IN ('{token_names_string.upper()}')
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

            #print(cursor)
            results = cursor.fetchall()
            #print(results)
            if results:
                columns = [col[0] for col in cursor.description]

                # Open the file in write mode if it's the first iteration, otherwise append mode
                mode = 'w' if first_iteration else 'a'
                with open(intermediary_file, mode, newline='') as outfile:
                    writer = csv.writer(outfile)
                    if first_iteration:  # Write headers only once
                        writer.writerow(columns)
                        first_iteration = False  # Set flag to False after first write
                    for row in results:
                        #print(row)
                        writer.writerow(row)
                    data_found = True
            else:
                print('Problem with query! Likely no data.')
                intermediary_file = fi.check_write_permission(intermediary_file)
                with open(intermediary_file,'w', newline='') as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(['LOT','WAFER_ID','SORT_X','SORT_Y'])
                break
        if token_chunk == token_chunks[-1] and data_found:
            break

    print('Full SQL done!')
    # Load CSV
    df1 = pd.read_csv(intermediary_file)

    # Concatenate the columns 'LOT', 'WAFER_ID', 'SORT_X', and 'SORT_Y' with underscores
    df1['Lot_WafXY'] = df1['LOT'].astype(str) + "_" + df1['WAFER_ID'].astype(str) + "_" + df1['SORT_X'].astype(str) + "_" + df1['SORT_Y'].astype(str)

    id_cols = ['Lot_WafXY', 'LOT', 'WAFER_ID', 'SORT_X', 'SORT_Y']
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

    # Read CSV
    df = pd.read_csv(intermediary_file)###this is the the datainput file

    pass_cols = [col for col in df.columns if col.endswith('_PASS')]#Empty if ClkUtils
    for pass_col in pass_cols:
        test_name = pass_col[:-5]  # Remove '_PASS'
        fail_col = test_name + '_FAIL'
        combined_col = test_name + '_combined'
        if fail_col in df.columns:
            # Generate combined string
            df[combined_col] = df.apply(lambda row: combine_pipe_fields(str(row[pass_col]), str(row[fail_col])), axis=1)
        else:
            # _FAIL column missing, combine _PASS with empty string
            df[combined_col] = df[pass_col].astype(str).apply(lambda x: combine_pipe_fields(x, ''))

        # Split the combined column into multiple columns
        split_cols = df[combined_col].str.split('|', expand=True)

        # Rename columns with suffixes _0, _1, ...
        split_cols = split_cols.rename(columns=lambda x: f"{test_name}_combined_{x}")

        # Concatenate split columns to original dataframe
        df = pd.concat([df, split_cols], axis=1)

    # Drop columns that contain 'CTV' but do NOT contain 'combined_'
    cols_to_drop = [col for col in df.columns if 'CTV' in col and 'combined_' not in col]#Only affects CTV
    df.drop(columns=cols_to_drop, inplace=True)#####QUESTION THIS LOGIC IF NEW COLUMNS

    # Remove '_combined' substring from any column name that contains it
    df.rename(columns=lambda x: x.replace('_combined', '') if '_combined' in x else x, inplace=True)

    # Exclude the first two columns from sorting
    excluded_columns = df.columns[:5]
    columns_to_sort = df.columns[5:]

    # Sort the remaining columns using the custom sorting key
    sorted_columns = sorted(columns_to_sort, key=sorting_key)

    # Combine the excluded columns with the sorted columns
    new_column_order = list(excluded_columns) + sorted_columns

    # Reindex the DataFrame with the new column order
    df = df.reindex(new_column_order, axis=1)

    #print(len(decoder_df['combined_string'].tolist()))

    # Create a set of original column names from df_pivot
    original_columns_set = set(df_pivot.columns)

    # Create a set of column names with '_PASS' and '_FAIL' removed
    modified_columns_set = set(col.replace('_PASS', '').replace('_FAIL', '') for col in df_pivot.columns)

    # Combine both sets to create a comprehensive set of column names
    df_columns_set = original_columns_set.union(modified_columns_set)

    # Convert the elements in df_columns_set to lowercase
    df_columns_set_lower = {col.lower() for col in df_columns_set}

    # Filter decoder_df to include only rows where 'Name' is in the comprehensive set of column names
    filtered_df = decoder_df[decoder_df['Name'].str.lower().isin(df_columns_set_lower)]

    try:#passes if no data or all data mapped
        df.columns = df.columns[:5].tolist() + filtered_df['combined_string'].tolist()
        print('Mapping!')
    except:
        #print(set(filtered_df['Name'].tolist()))
        #print(df_columns_set)
        print('No mapping!')

    #print(data_out_file)
    data_out_file = fi.check_write_permission(data_out_file)
    df.to_csv(data_out_file, index=False)#originally df.to_csv
    print(data_out_file, "has been completed!")
    return intermediary_file, data_out_file


def modify_tokens(tokens, status):
    modified_tokens = []
    
    for token in tokens:
        # Split the token by '_'
        parts = token.split('_')
        
        # Insert 'Pass' or 'Fail' as the second-to-last entry
        parts.insert(-1, status)
        
        # Rejoin the parts using '_'
        modified_token = '_'.join(parts)
        
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




