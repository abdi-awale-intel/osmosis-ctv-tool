import csv
import json
import os
import sys
import re
import pprint
import file_functions as fi

def process_json_to_csv(json_file_path,filter_name=r"(.*)",place_in='',ITUFF_limit=1433,filter_choice='NOM'):
    json_file_path = fi.process_file_input(json_file_path)
    with open(json_file_path, 'r') as json_file:
        # load() converts json to nested dictionary
        config = json.load(json_file)
        #Tests config nested navigation
    if filter_name != r"(.*)":
        if filter_name.find('::') != -1:
            filter_tb = '_'+'_'.join(filter_name.split('::'))
        else:
            filter_tb= '_'+filter_name
    else:
        filter_tb=''


    if place_in == '':
        place_in = os.path.dirname(json_file_path)

    die_type = ["top",'base']
    if "SDTBEGIN" in filter_name and 'TOP' in filter_name:
        die_type = ['cbb']
    elif 'BEGIN' in filter_name and 'TOP' in filter_name:
        die_type = ['top']
    elif 'BASE' in filter_name:
        die_type = ['base']
    else:
        die_type = ['top', 'base', 'cbb']

    cbb_values = extract_setups(config["setups"]["setup"]["cbb"])
    top_values = extract_setups(config["setups"]["setup"]["top"])

    indexed_files = []
    for word_tb in die_type:#this will need to change to include cbb at somepoint along with the unique setup mapping of cbb in configDMR file
        indexed_file = f'{place_in}\\clkutils_{word_tb}{filter_tb}_indexed.csv'
        indexed_file = fi.check_write_permission(indexed_file)
        with open(indexed_file, mode='w', newline='') as file:
            fieldnames = ['Index','DCM','Ratio','Test','Stage','Field','Name','Name_Index','combined_string']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()  


            # deal with regex test names in Marco's json  
            #for i in [i for i, item in enumerate(config['ClkUtils_test_case_config']) if word_tb in item["regular_expression"][0].lower() and re.match(config["ClkUtils_test_case_config"][i]["regular_expression"],filter_name)]:
            for i in [i for i, item in enumerate(config['ClkUtils_test_case_config']) if re.match(config["ClkUtils_test_case_config"][i]["regular_expression"][0],filter_name)]:
                test_config = config['ClkUtils_test_case_config'][i]['test_config_name']

                # ITUFF should just be the name of the test
                if filter_name != r"(.*)":
                    ITUFF = filter_name
                else:

                    ITUFF = re.sub(r'\(MIN\|MAX\|NOM\)',filter_choice, config["ClkUtils_test_case_config"][i]["regular_expression"][0])
                    ITUFF = re.sub(r"\(?!_\((corerecovery|Profile)\)\)", "", ITUFF)

                
                #setup the setup name and ratio list before so that ITUFF_MOD can be setup early
                setup_list=[]
                test_modifier_list = []
                if config['ClkUtils_test_case_config'][i]['setup'] == '$setup':
                    if word_tb == 'cbb':
                        # Process each CBB key group separately
                        for cbb_key, setup_nums in cbb_values.items():
                            for setup_num in setup_nums:
                                setup_list.append(config['setups']['setup_map'][setup_num])
                                test_modifier_list.append(cbb_key)
                    elif word_tb == 'top':
                        # For top, there's typically only one key group
                        for top_key, setup_nums in top_values.items():
                            for setup_num in setup_nums:
                                setup_list.append(config['setups']['setup_map'][setup_num])
                                test_modifier_list.append('')                        
                else:
                    setup_list = config["ClkUtils_test_case_config"][i]["setup"]
                    test_modifier_list = [''] * len(setup_list)

                ratio_list = config["ClkUtils_test_case_config"][i]['ratios'].split(', ')
                
                # For CBB, calculate big_num and reset counters for each key group
                if word_tb == 'cbb' and config['ClkUtils_test_case_config'][i]['setup'] == '$setup':
                    
                    
                    for cbb_key, setup_nums in cbb_values.items():
                        # Calculate big_num for this specific CBB key group
                        current_setup_count = len(setup_nums)
                        big_num = 0
                        for k in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'])):
                            if config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                                big_num += len(ratio_list) * current_setup_count * len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])
                        
                        # Reset counters for each CBB key
                        if big_num > ITUFF_limit:
                            mod = 1
                            ITUFF_MOD = f"_{mod}"
                        else:
                            mod = 0
                            ITUFF_MOD = ''
                        
                        counter = 0
                        
                        # Process only setups for this CBB key
                        for setup_num in setup_nums:
                            setup_name = config['setups']['setup_map'][setup_num]
                            test_modifier = cbb_key
                            
                            for ratio_num in ratio_list:
                                ratio = f'r_{ratio_num}'
                                for k in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'])):
                                    stage_name = config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["stage"]
                                    if config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                                        for l in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])):
                                            field_name = config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"][l]["name"]
                                            NAME = ITUFF + '_'+test_modifier + ITUFF_MOD
                                            combined_string = setup_name+'---'+ratio+'---'+test_config+'---'+stage_name+'---'+field_name
                                            row_dict = {'Index': counter, 'DCM': setup_name ,'Ratio': ratio, 'Test': test_config, 'Stage': stage_name ,'Field': field_name,'Name': NAME, 'Name_Index': NAME+"_"+str(counter), 'combined_string':combined_string}
                                            writer.writerow(row_dict) 
                                            counter += 1
                                            if counter > ITUFF_limit-1:
                                                counter = 0
                                                mod += 1
                                                ITUFF_MOD = f"_{mod}"
                else:
                    # Original logic for non-CBB or non-$setup cases
                    #establish ITUFF limit and calculate if ITUFF_limit exceeded
                    big_num = 0
                    for k in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'])):
                        if config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                            big_num += len(ratio_list)*len(setup_list)*len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])
                    if big_num > ITUFF_limit:
                        mod = 1
                        ITUFF_MOD = f"_{mod}"
                    else:
                        mod = 0
                        ITUFF_MOD = ''
                    
                    
                    counter = 0
                    for setup_name, test_modifier in zip(setup_list, test_modifier_list):
                        for ratio_num in ratio_list:
                            ratio = f'r_{ratio_num}'
                            for k in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'])):
                                stage_name = config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["stage"]
                                """if stage_name.upper()=='DFF'  and config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                                    counter+=len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])
                                    continue"""
                                if config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                                    for l in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])):
                                        field_name = config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"][l]["name"]
                                        #IP = setup_name+'_'+ratio
                                        NAME = ITUFF + test_modifier+ITUFF_MOD
                                        combined_string = setup_name+'---'+ratio+'---'+test_config+'---'+stage_name+'---'+field_name
                                        row_dict = {'Index': counter, 'DCM': setup_name ,'Ratio': ratio, 'Test': test_config, 'Stage': stage_name ,'Field': field_name,'Name': NAME, 'Name_Index': NAME+"_"+str(counter), 'combined_string':combined_string}
                                        writer.writerow(row_dict) 
                                        counter += 1
                                        if counter > ITUFF_limit-1:
                                            counter = 0
                                            mod += 1
                                            ITUFF_MOD = f"_{mod}"         
        indexed_files.append(indexed_file)
        print(f"{indexed_file} is indexed!")
        if len(die_type) == 1:
            tag_header_names = ['DCM','Ratio','Test','Stage','Field']
            return indexed_file,tag_header_names
    return indexed_files

# Function to extract and join values from a given section
def extract_setups(section):
    grouped_data = {}
    for key, value in section.items():
        key_suffix = key.split(".")[-1]
        values = value.split(", ")
        if key_suffix not in grouped_data:
            grouped_data[key_suffix] = []
        for val in values:
            grouped_data[key_suffix].append(val)
    return grouped_data

if __name__ == "__main__":
    ## MAIN
    # Define json file and use to generate csv
    json_file_path = input("Enter full path to config file (Remove quotes if copying path): ")
    test_type = input("MIN|NOM|MAX\n").upper()
    filter_choice = input('Test filter (Y or N)? ').upper()
    if filter_choice == 'Y':
        filter =  input('Enter filter: ').upper()
        # Fill xml with information from the json
        #process_json_to_xml(json_file_path, test_type,filter)
        process_json_to_csv(json_file_path, test_type,filter)
    else:
        #process_json_to_xml(json_file_path, test_type)
        process_json_to_csv(json_file_path, test_type)       


'''From line 34                # Regular expression pattern to match the desired split point
                step1 = []
                if '^' in config["ClkUtils_test_case_config"][i]["regular_expression"][0]:
                    step1 = re.split(r'[()]', config["ClkUtils_test_case_config"][i]["regular_expression"][0].split('^')[1])
                elif '\\' in config["ClkUtils_test_case_config"][i]["regular_expression"][0]:
                    step0 = config["ClkUtils_test_case_config"][i]["regular_expression"][0].split('\\w+_V?')
                    step1 = re.split(r'[()]', step0[0]+step0[1])
                else: 
                    step1 = re.split(r'[()]', config["ClkUtils_test_case_config"][i]["regular_expression"][0])
                ITUFF = step1[0]+test_type+step1[2]'''


'''Consider moving this stuff out of more loops to encompass every single test                big_num = 0
                for k in range(len(config["ClkUtils_test_case_config"][i]['ctv_sequence'])):
                    if config["ClkUtils_test_case_config"][i]['ctv_sequence'][k].get('fields') is not None:
                        big_num += len(ratio_list)*len(setup_list)*len(config["ClkUtils_test_case_config"][i]['ctv_sequence']) *len(config["ClkUtils_test_case_config"][i]['ctv_sequence'][k]["fields"])
                if big_num > ITUFF_limit:
                    mod = 0
                    ITUFF_MOD = f"_{mod}"
                else:
                    mod = 0
                    ITUFF_MOD = ''
                    '''