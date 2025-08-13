#NEEDS user to run MTPLBULKPORTEDITOR and MTPL TO CSV on an mtpl
#Ctrl Shft C the outputs and the tp directory
#also change the script to hard code an output csv for the mismatches

import os
import pandas as pd
import json
import re
import mtpl_parser as mtpl #Make code to process mtpl
import file_functions as fi

def fix_json_trailing_commas(json_string):
    """
    Remove trailing commas from JSON string.
    """
    # Remove trailing commas before closing brackets/braces
    return re.sub(r',\s*([}\]])', r'\1', json_string)

def load_json_with_comma_fix(file_path):
    """
    Load JSON file with automatic trailing comma removal if needed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return json.loads(content)
    except json.JSONDecodeError:
        # Try fixing trailing commas
        print("JSON decode error, attempting to fix trailing commas...")
        try:
            fixed_content = fix_json_trailing_commas(content)
            return json.loads(fixed_content)
        except json.JSONDecodeError as e:
            print(f"Could not fix JSON: {e}")
            raise

def find_port_mismatches(mtpl_csv, port_csv,base_dir):
    base_dir = base_dir + '\\'
    #base_dir = r"\\alpfile4.al.intel.com\hop\program\1276\eng\hdmtprogs\dmr_dab_hop\savirine\WW32\WW32.4_EIO_TP8/"
    mtpl_df = pd.read_csv(mtpl_csv,index_col=False,dtype={'BasicTestConfiguration': 'str'})
    port_df = pd.read_csv(port_csv,index_col=False)
    
    mismatches = []
    
    # Iterate through each row of mtpl_df
    for index, row in mtpl_df.iterrows():
        test_name = str(row['TestName'])
        config_file_path = str(row['ConfigurationFile'])
        basic_test_config = row['BasicTestConfiguration']
        mode = str(row.get('Mode', '')).strip('\"\'')  # Get mode, default to empty string if not present
        bypass = str(row.get('BypassPort', '')).strip('\"\'')  # Get bypass, default to empty string if not present
        # Get list of exit ports from configuration files
        exit_ports = []
        if 'ctv' not in row["TestType"].lower():
            continue
        # Handle path construction based on config_file_path format
        #print(f"DEBUG: config_file_path = {config_file_path}")
        if ' + ' in config_file_path:
            # Format: "base_path" + "relative_path"
            relative_path = config_file_path.split(' + ')[1].strip(' \"').replace('./', '').replace('\"+\"', '').replace('\\\\', '\\')
            #print(f"DEBUG: Found '+', relative_path = {relative_path}")
        elif '+' in config_file_path:
            # Format: GetEnvironmentVariable("~HDMT_TP_BASE_DIR")+"\\\\path\\\\file"
            # Extract the path after the environment variable part
            env_part, path_part = config_file_path.split('+"', 1)
            relative_path = path_part.strip('\"').replace('\"+\"', '').replace('\\\\', '\\')
            #print(f"DEBUG: GetEnvironmentVariable format, relative_path = {relative_path}")
        else:
            # Direct path
            relative_path = config_file_path.strip(' \"').replace('./', '').replace('\\\\', '\\')
            #print(f"DEBUG: Direct path format, relative_path = {relative_path}")
        missing_config_flag = False
        missing_decoder_flag = False
        config_missing = ''
        decoder_missing = []
        if '.csv' in config_file_path:
            #if csv
            #print(base_dir)
            #open csv and makes list of all non nan, blank, or noninteger values
            csv_path = base_dir + relative_path
            csv_path = csv_path.replace('\\\\\\', '\\')
            if os.path.exists(os.path.normpath(csv_path)):
                try:
                    # Try multiple CSV parsing approaches for malformed files
                    try:
                        config_df = pd.read_csv(csv_path)
                    except pd.errors.ParserError:
                        #print(f"Parser error with {csv_path}, trying tab-separated parsing...")
                        try:
                            config_df = pd.read_csv(csv_path, sep='\t')
                        except pd.errors.ParserError:
                            #print(f"Tab-separated parsing failed, trying with error skipping...")
                            # Try with error_bad_lines=False (pandas <1.3) or on_bad_lines='skip' (pandas >=1.3)
                            try:
                                config_df = pd.read_csv(csv_path, on_bad_lines='skip')
                            except TypeError:
                                # Fallback for older pandas versions
                                config_df = pd.read_csv(csv_path, error_bad_lines=False, warn_bad_lines=True)
                    
                    if 'ExitPort' in config_df.columns:
                        # Convert ExitPort to numeric, coercing errors (like "-") to NaN
                        config_df['ExitPort'] = pd.to_numeric(config_df['ExitPort'], errors='coerce')
                        
                        # Get all non-NaN values and convert to integers
                        exit_port_values = config_df['ExitPort'].dropna().astype(int)
                        exit_port_values = set(exit_port_values.tolist())
                        
                        # Filter out integer values
                        for value in exit_port_values:
                            exit_ports.append(str(value).strip())
                    else:
                        print('No ExitPort column found!')
                except Exception as e:
                    print(f"Error reading CSV {csv_path}: {e}")
            else:
                print(f"\nCSV file not found: {csv_path}")
                missing_config_flag = True
                config_missing = csv_path

        elif '.json' in config_file_path:
            #if smart.json
            #open smart.json
            json_path = base_dir + relative_path
            json_path = json_path.replace('\\\\\\', '\\')
            if os.path.exists(os.path.normpath(json_path)):
                try:
                    smart_config = load_json_with_comma_fix(json_path)

                    if mode == 'CtvTag':
                        #If row[Mode] == "CtvTag": use all configurations and open the csv in each configuration to get list of exit ports
                        test_configs = smart_config.get('TestConfigurations', {})
                        for config_num, config_data in test_configs.items():
                            decoder_config = config_data.get('Decoder', {})
                            decoder_csv = decoder_config.get('ConfigurationFile', '')
                            if decoder_config.get('ExitPortOffset',''):
                                    exit_ports.append(str(decoder_config.get('ExitPortOffset','')))
                                    #exit_ports = [str(int(x)+int(port_offset for x in exit_ports]
                            elif decoder_csv.endswith('.csv'):
                                decoder_csv_path = base_dir + decoder_csv.strip('\"').replace('./', '').replace('\\\\\\', '\\') 
                                if os.path.exists(os.path.normpath(decoder_csv_path)):
                                    try:
                                        # Try multiple CSV parsing approaches for malformed files
                                        try:
                                            decoder_df = pd.read_csv(decoder_csv_path)
                                        except pd.errors.ParserError:
                                            #print(f"Parser error with {decoder_csv_path}, trying tab-separated parsing...")
                                            # Try parsing as tab-separated file instead of comma-separated
                                            try:
                                                decoder_df = pd.read_csv(decoder_csv_path, sep='\t')
                                            except pd.errors.ParserError:
                                                pass
                                        if 'ExitPort' in decoder_df.columns:
                                            # Convert ExitPort to numeric, coercing errors to NaN
                                            decoder_df['ExitPort'] = pd.to_numeric(decoder_df['ExitPort'], errors='coerce')
                                            exit_port_values = decoder_df['ExitPort'].dropna().astype(int)
                                            exit_port_values = set(exit_port_values.tolist())
                            
                                            for value in exit_port_values:
                                                exit_ports.append(str(value).strip())
                                            #if(exit_port_values):
                                                #print(decoder_df['ExitPort'])
                                        else:
                                            print(f"No ExitPort column found in {decoder_csv_path}\n")
                                    except Exception as e:
                                        print(f"Error reading decoder CSV {decoder_csv_path}: {e}")
                                else:
                                    print("Decoder not found")
                                    missing_decoder_flag = True
                                    decoder_missing.append(decoder_csv_path)
                        exit_ports = list(set(exit_ports))  # Remove duplicates
                    else:
                        #else: use one configuration and open the csv for that configuration to get list of exit ports
                        test_configs = smart_config.get('TestConfigurations', {})
                        if basic_test_config in test_configs:
                            config_data = test_configs[basic_test_config]
                            decoder_config = config_data.get('Decoder', {})
                            decoder_csv = decoder_config.get('ConfigurationFile', '')
                            decoder_csv = decoder_csv.replace('~HDMT_TPL_DIR', '')
                            if decoder_config.get('ExitPortOffset',''):
                                    exit_ports.append(decoder_config.get('ExitPortOffset',''))
                                    #exit_ports = [str(int(x)+int(port_offset for x in exit_ports]
                            elif decoder_csv.endswith('.csv'):
                                decoder_csv_path = base_dir + decoder_csv.strip('\"').replace('./', '').replace('\\\\\\', '\\') 
                                if os.path.exists(os.path.normpath(decoder_csv_path)):
                                    try:
                                        # Try multiple CSV parsing approaches for malformed files
                                        try:
                                            decoder_df = pd.read_csv(decoder_csv_path)
                                        except pd.errors.ParserError:
                                            try:
                                                decoder_df = pd.read_csv(decoder_csv_path, sep='\t')
                                            except pd.errors.ParserError:
                                                pass
                                        
                                        if 'ExitPort' in decoder_df.columns:
                                            # Convert ExitPort to numeric, coercing errors to NaN
                                            decoder_df['ExitPort'] = pd.to_numeric(decoder_df['ExitPort'], errors='coerce')
                                            exit_port_values = decoder_df['ExitPort'].dropna().astype(int)
                                            exit_port_values = set(exit_port_values.tolist())

                                            for value in exit_port_values:
                                                exit_ports.append(str(value).strip())
                                    except Exception as e:
                                        print(f"Error reading decoder CSV {decoder_csv_path}: {e}")
                                else:
                                    print("Decoder not found")
                                    missing_decoder_flag = True
                                    decoder_missing.append(decoder_csv_path)
                except Exception as e:
                    print(f"Error reading JSON {json_path}: {e}")
            else:
                print(f"\nJSON file not found: {json_path}")
                missing_config_flag = True
                config_missing = json_path
        # Make a filtered_df out of port_df that is only rows that match the current mtpl_df row's Test Name
        filtered_df = port_df[port_df['Instance'] == test_name].copy()
        
        if not filtered_df.empty and exit_ports:
            # Compare the filtered_df Port column to the list of exit ports from the configuration files
            if 'Port' in filtered_df.columns:
                port_values = filtered_df['Port'].dropna().astype(str).str.strip().tolist()
                
                # Find mismatches - ports in filtered_df that are not in exit_ports
                missing_ports = [port for port in exit_ports if port not in port_values]
                #extra_ports = [port for port in exit_ports if port not in port_values]

                if missing_ports or missing_config_flag or missing_decoder_flag:# or extra_ports:
                    mismatch_info = {
                        'test_name': test_name,
                        'config_path': config_file_path,
                        'config_miss': config_missing,
                        'decoder_miss': decoder_missing,
                        'basic_test_config': basic_test_config,
                        'mode': mode,
                        'bypass': bypass,
                        'ports_in_data_not_in_config': missing_ports,
                        #'ports_in_config_not_in_data': extra_ports,
                        'expected_ports': exit_ports,
                        'actual_ports': port_values
                    }
                    mismatches.append(mismatch_info)
                    print(f"  Mismatch found for {test_name}        Ports:{missing_ports}")
                    #print(f"    Missing from config: {missing_ports}")
                    #print(f"    Extra in config: {extra_ports}")
                else:
                    print(f"  No mismatches found for {test_name}")
            else:
                print(f"  'Port' column not found in port_df for {test_name}")
        else:
            if missing_config_flag or missing_decoder_flag:
                mismatch_info = {
                    'test_name': test_name,
                    'config_path': config_file_path,
                    'config_miss': config_missing,
                    'decoder_miss': decoder_missing,
                    'basic_test_config': basic_test_config,
                    'mode': mode,
                    'bypass': bypass,
                    'ports_in_data_not_in_config': [],
                    #'ports_in_config_not_in_data': extra_ports,
                    'expected_ports': [],
                    'actual_ports': []
                }
                mismatches.append(mismatch_info)
                print(f"  Missing configuration or decoder for {test_name}\n")
            elif filtered_df.empty:
                print(f"  No matching rows found in port_df for {test_name}")
            elif not exit_ports:
                print(f"\n  No exit ports found in configuration for {test_name}")
    
    return mismatches


def mtpl_verification(mtpl_file,place_in=''):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(mtpl_file)))
    test_csv = mtpl.mtpl_test_to_csv(mtpl_file,place_in)
    port_csv = mtpl.mtpl_port_to_csv(mtpl_file,place_in)
    mismatches = find_port_mismatches(test_csv, port_csv,base_dir)
    output_csv = f"{place_in}{os.path.basename(mtpl_file)}.mismatches.csv"
    output_csv = fi.check_write_permission(output_csv)
    if mismatches:
        results_df = pd.DataFrame([
            {
                'Test Instance': mismatch['test_name'],
                'Missing Ports': ', '.join(mismatch['ports_in_data_not_in_config']),
                'Missing Config': mismatch['config_miss'],
                'Missing Decoder': ', '.join(mismatch['decoder_miss']),
                'Bypass Port': mismatch['bypass']
            }
            for mismatch in mismatches
        ])

        results_df.to_csv(output_csv, index=False)

        print(f"Results saved to {output_csv}")
        print(f"Found {len(mismatches)} test instances with missing ports")
        return output_csv
    else:
        print("\n  NO MISMATCHES FOUND\n")


if __name__ == "__main__":
    mtpl_file = r"H:\program\1276\eng\hdmtprogs\dmr_dai_sds\savirine\WW33\WW33.2_EIO_TP4\Modules\EIO_UCIE\EIO_UCIE.mtpl"
    place_in = r"C:\Users\burtonr\OneDrive - Intel Corporation\Desktop\mismatches\\"
    mtpl_verification(mtpl_file, place_in)