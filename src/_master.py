import csv
import json
import os
import sys
import re
import pandas as pd
import time

import file_functions as fi
import mtpl_parser as mt
import smart_json_parser as sm
import index_ctv as ind
import pyuber_query as py
import clkutils_config_json_to_csv as clk
import jmp_python as jmp

# Function to check if a value is considered "undefined"
def is_undefined(value):
    return value is None or value == '' or value == '-'

if __name__ == "__main__":
    start_time = time.time()

    # At the beginning of your script, add this (ensures config_DMR will be found):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_directory)
    print(f"Changed working directory to: {os.getcwd()}")

    #test_list = fi.test_input_to_list(fi.process_file_input(input("Absolute file path to list of test names: ")))
    material_file = fi.process_file_input(input("Absolute file path to csv of material qualifiers (Lot,Wafer,TP,days_back): "))
    mat_file_ext = fi.get_file_extension(material_file)
    #base_dir = fi.process_file_input(input("Absolute file path to TP base directory: "))

    material_df = []
    if mat_file_ext == '.csv':
        material_df = pd.read_csv(material_file)
    elif mat_file_ext in ['.xsl','.xslx']:
        material_df = pd.read_excel(material_file)
    else:
        print("Improper file extension. Try again.")
        sys.exit()
    print(material_df)
    test_list = material_df['Test'].tolist()
    try:
        mtpl_list = material_df['MTPL'].tolist()
    except:
        pass

    # Default values
    default_values = {
    'Lot': ['Not Null'],
    'Wafer': ['Not Null'],
    'Program': ['DAB%','DAC%'],
    'Prefetch': 3,
    'Database': ['D1D_PROD_XEUS','F24_PROD_XEUS']
    }
    # Extract columns as lists, filtering out NaN values and using default values if columns are missing or empty
    lot_list = material_df['Lot'].dropna().tolist() if 'Lot' in material_df.columns else default_values['Lot']
    wafer_list = material_df['Wafer'].dropna().tolist() if 'Wafer' in material_df.columns else default_values['Wafer']
    wafer_list = list(map(int,wafer_list))
    program_list = material_df['Program'].dropna().tolist() if 'Program' in material_df.columns else default_values['Program']
    prefetch = material_df.iat[0, material_df.columns.get_loc('Prefetch')] if 'Prefetch' in material_df.columns else default_values['Prefetch']
    databases = material_df['Database'].dropna().tolist() if 'Database' in material_df.columns else default_values['Database']
    if not databases:
        databases = default_values['Database']
    if not program_list:
        program_list = default_values['Program']
    #Extract the important data if prefetch and database are empty but the columns are present
    if pd.isna(prefetch):
        prefetch = 3
    if not mtpl_list:
        mtpl = fi.process_file_input(input('Input full path to mtpl: '))
        mtpl_list = mtpl*len(program_list)
    if len(program_list)>len(mtpl_list) and program_list == default_values['Program']:
        mtpl_list.extend(mtpl_list)


    # Ask user if they want to make decisions once for all programs or separately for each
    decision_mode = input(f'Make decisions for all {len(program_list)} programs at once or separately for each?\n'
                        f'Programs to process: {", ".join(program_list)}\n'
                        f'Decisions include:\n'
                        f'  - Output folder location (default vs custom)\n'
                        f'  - Delete intermediary files (Y/N)\n'
                        f'  - Stack output files (Y/N)\n'
                        f'Enter "A" for ALL at once or "S" for SEPARATE: ').upper()

    # Initialize variables for "all at once" mode
    use_same_settings = decision_mode == 'A'
    global_place_in_choice = ''
    global_delete_files = ''
    global_stack_files = ''
    global_custom_folder = ''

    if use_same_settings:
        print("\n--- Making decisions for ALL programs ---")
        
        # Get global decisions
        global_place_in_choice = input(f'Place all output data in specialized folders (Y/N)\n'
                                    f'(Y = custom folder, N = default program_script_output folders): ').upper()
        
        if global_place_in_choice == 'Y':
            global_custom_folder = input('Input full path to data output folder (all programs will use subdirectories): ')
        
        global_delete_files = input(f'Delete intermediary files for ALL programs (Y/N)\n'
                                f'(Deletes everything other than mapped and stacked datafiles): ').upper()
        
        global_stack_files = input(f'Stack all mapped output files for ALL programs (Y/N): ').upper()
        
        print(f"\nSettings will be applied to all programs: {', '.join(program_list)}\n")

    #Loop everything below for each mtpl
    for program,mtpl in zip(program_list,mtpl_list):
        intermediary_file_list = []
        output_files = []
        stacked_files = []
        tag_header_names_chunks = []
        #run_jmp = 'N'

        # Use global settings or ask for each program
        if use_same_settings:
            print(f"\n--- Processing {program} with global settings ---")
            
            # Apply global settings
            if global_place_in_choice == 'Y':
                place_in = os.path.join(global_custom_folder, f'{program}_output')
                os.makedirs(place_in, exist_ok=True)
                place_in = place_in + '\\'
            else:
                default_path = os.getcwd() + f'\\{program}_script_output'
                place_in = default_path
                os.makedirs(place_in, exist_ok=True)
                place_in = place_in + '\\'
            
            delete_files = global_delete_files
            stack_files = global_stack_files
            
            print(f"  Output folder: {place_in}")
            print(f"  Delete intermediary files: {delete_files}")
            print(f"  Stack files: {stack_files}")
            
        else:
            print(f"\n--- Making decisions for {program} ---")
            
            # Ask for individual program settings
            default_path = os.getcwd() + f'\\{program}_script_output'
            place_in_choice = input(f'Place all output data for {program} in a specialized folder(Y/N)\n'
                                f'(Defaults to {default_path}): ').upper()
            
            delete_files = input(f'Delete intermediary files for {program} (Y/N)\n'
                            f'(Deletes everything other than mapped and stacked datafiles): ').upper()
            
            stack_files = input(f'Stack all mapped output files for {program} (Y/N): ').upper()
            
            # Handle folder creation
            if place_in_choice == 'Y':
                place_in = input('Input full path to data output folder: ')
                os.makedirs(place_in, exist_ok=True)
                place_in = place_in + '\\'
            else:
                place_in = default_path
                os.makedirs(place_in, exist_ok=True)
                place_in = place_in + '\\'

        try:
            mtpl = os.path.normpath(mtpl)
        except Exception as e:
            print(f"Error processing MTPL path: {e}")
        
        program_start_time = time.time()
        ###special section for clkutils
        for test in test_list:
            if type(test) is not str:
                continue
            if 'CLKUTILS' in test.upper():#ClkUtils do not require mtpl parsing
                print('\n'+str(test), 'is running!')
                indexed_file,tag_header_names = clk.process_json_to_csv('configFile_DMR.json',test,place_in)
                tag_header_names_chunks.append(tag_header_names)
                intermediary_file_list.append(indexed_file)
                datainput_file,datacombine_file=py.uber_request(indexed_file,test,'ClkUtils',False,place_in,program, '', lot_list, wafer_list, prefetch, databases)
                intermediary_file_list.append(datainput_file)
                output_files.append(datacombine_file)
            
        if delete_files == 'Y':
            fi.delete_files(intermediary_file_list)
        if stack_files == 'Y':
            for output_file, tag_header_names in zip(output_files, tag_header_names_chunks):
                stacked_file = jmp.stack_and_split_file(output_file, tag_header_names)
                stacked_files.append(stacked_file)
            if delete_files == 'Y':
                fi.delete_files(output_files)
        if mtpl == '' or str(mtpl).lower() == 'nan' or not mtpl_list: 
            continue
        ###special section for clkutils

        mtpl_csv_path = mt.mtpl_to_csv(fi.process_file_input(mtpl),place_in)
        mtpl_df = pd.read_csv(mtpl_csv_path)

        base_dir = mtpl.split('Modules')[0].strip('\\/')

        for test in test_list:

            if type(test) is not str or 'CLKUTILS' in str(test).upper():
                continue
            if '::' in test:
                test_match = test.split('::')[-1]  # Extract the test name after '::'
            else:
                test_match = test
            for row in mtpl_df.itertuples():
                #check if row matches
                if row[2] != test_match:# and "CLKUTILS" not in test:#add check that doesn't continue if it test contains CLKUTILS(if go configDMR route, this is not needed and can skip right past everything and include CONFIGDMR as a local file that must be downloaded with this file)
                    continue

                print(test, 'is running!')
                test_type = row[1]
                config_path = fi.process_file_input(row[3][row[3].find('Modules'):].strip('\"'))
                module_name = fi.get_module_name(config_path).strip('\\')
                test_file = os.path.join(base_dir, config_path)
                
                #Ensure config file referenced in mtpl csv exists
                try:
                    with open(test_file,'r') as file:
                        pass
                    print(f"{test_file} was found!")
                except FileNotFoundError:
                    print(f"Error: The file '{test_file}' was not found.")
                    continue #Skip the following if config file does not exist

                indexed_file = ''
                csv_identifier = ''
                mode = row[5]
                    
                if test_type == "CtvDecoderSpm":#simple CTV indexing
                    indexed_file,csv_identifier,tag_header_names = ind.index_CTV(test_file, test,module_name,place_in)
                    tag_header_names_chunks.append(tag_header_names)
                    intermediary_file_list.append(indexed_file)
                    datainput_file,datacombine_file = py.uber_request(indexed_file,test_match,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                    intermediary_file_list.append(datainput_file)
                    output_files.append(datacombine_file)
                elif test_type=="SmartCtvDc":#SMART CTV loop/check logic and indexing
                    if "ctvtag" in str(mode).lower():
                        mode = mode.strip('\"\'')
                        config_number = ''
                        ctv_files,ITUFF_suffixes,config_numbers = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                        for ctv_file,ITUFF_suffix,config_number in zip(ctv_files,ITUFF_suffixes,config_numbers):
                            intermediary_file_list.append(ctv_file)
                            test = test + ITUFF_suffix
                            print(test)
                            indexed_file,csv_identifier,tag_header_names = ind.index_CTV(ctv_file, test_match,module_name,place_in,mode,config_number)
                            tag_header_names_chunks.append(tag_header_names)
                            intermediary_file_list.append(indexed_file)
                            datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases,config_number,mode)
                            intermediary_file_list.append(datainput_file)
                            output_files.append(datacombine_file)
                            test = test.replace(ITUFF_suffix,'')
                    else:
                        config_number = str(int(row[4]))                    
                        ctv_file = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                        intermediary_file_list.append(ctv_file)
                        indexed_file,csv_identifier,tag_header_names = ind.index_CTV(ctv_file, test_match,module_name,place_in)
                        intermediary_file_list.append(indexed_file)
                        tag_header_names_chunks.append(tag_header_names)
                        datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                        intermediary_file_list.append(datainput_file)
                        output_files.append(datacombine_file)
                break

        if delete_files == 'Y':
            fi.delete_files(intermediary_file_list)
        if stack_files == 'Y':
            for output_file, tag_header_names in zip(output_files, tag_header_names_chunks):
                stacked_file = jmp.stack_and_split_file(output_file, tag_header_names)
                stacked_files.append(stacked_file)
            if delete_files == 'Y':
                fi.delete_files(output_files)
        '''if run_jmp == 'Y' and jmp_executable_path:
            for stacked_file in stacked_files:
                jmp.run_jsl(stacked_file,jmp_executable_path)
        else:
            print("Did not run JMP on stacked files or JMP executable path not found.")'''

        program_end_time = time.time()
        program_duration = program_end_time - program_start_time
        print(f"\nProgram {program} executed in {program_duration:.2f} seconds.") 
    # Record the end time and calculate the duration
    end_time = time.time()
    duration = end_time - start_time
    print(f"\nMaster Program executed in {duration:.2f} seconds.")


    '''if stack_files == 'Y':
        run_jmp = input('Run JMP on all stacked files (Y/N): ').upper()
        if run_jmp == 'Y':
            jmp_executable_path = fi.find_latest_jmp_pro_path()'''