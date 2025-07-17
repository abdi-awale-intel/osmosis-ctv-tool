import re
import csv
import os
import file_functions as fi

file_path = "C:/Users/burtonr/applications.manufacturing.ate-test.torch.server.dmr.sort.dab/Modules/PTH_FIVROPS/PTH_FIVROPS.mtpl"
output_csv = 'C:/Users/burtonr/Downloads/parsed_mtpl_output.csv'

def read_mtpl_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_mtpl_content(text):
    # Step 1: Extract all CSharpTest blocks
    block_pattern = re.compile(
        r'CSharpTest\s+(\w+)\s+(\w+)\s*\{(.*?)\}',
        re.DOTALL
    )
    blocks = block_pattern.findall(text)

    extracted_data = []

    for decoder_type, test_name, body in blocks:
        # Step 2: Extract fields within the body (order doesn't matter)
        config_file_match = re.search(r'ConfigurationFile\s*=\s*(.+?);', body)
        config_file_list = re.findall(r'ConfigurationFile_\w+\s*=\s*(.+?);', body) # for CLKUTILSLoader (make multiple lines)
        basic_test_config_match = re.search(r'BasicTestConfiguration\s*=\s*(.+?);', body)
        mode_match = re.search(r'\sMode\s*=\s*(.+?);', body)

        config_cleaned = config_file_match.group(1).strip().replace('\n', ' ') if config_file_match else None
        basic_test_config = basic_test_config_match.group(1).strip() if basic_test_config_match else None
        mode = mode_match.group(1).strip() if mode_match else None
        if config_cleaned or config_file_list:
            if config_file_list:
                for config_file in config_file_list:
                    config_cleaned = config_file.strip().replace('\n', ' ')
                    extracted_data.append([
                        decoder_type.strip(),
                        test_name.strip(),
                        config_cleaned,
                        basic_test_config,
                        mode
                    ])
            else:
                extracted_data.append([
                    decoder_type.strip(),
                    test_name.strip(),
                    config_cleaned,
                    basic_test_config,
                    mode
                ])

    return extracted_data

def save_to_csv(data, csv_path):
    headers = ['TestType', 'TestName', 'ConfigurationFile', 'BasicTestConfiguration','Mode']
    with open(csv_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)


# Main execution
def mtpl_to_csv(file_path,place_in=''):
    text = read_mtpl_file(file_path)
    parsed_data = parse_mtpl_content(text)
    output_csv = f"{place_in}{os.path.basename(file_path)}.csv"
    output_csv = fi.check_write_permission(output_csv)
    save_to_csv(parsed_data,output_csv)

    print(f"Extracted {len(parsed_data)} entries and saved to '{output_csv}'.")
    return output_csv

if __name__ == "__main__":
    file_path = input("Enter full path to mtpl file: ").strip('\"')
    #Example: "C:\\Users\\burtonr\\applications.manufacturing.ate-test.torch.server.dmr.sort.dab\\Modules\\CLK_PLL_BASE\\CLK_PLL_BASE.mtpl"
    mtpl_to_csv(file_path)
