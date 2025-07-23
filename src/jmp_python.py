import pandas as pd
import os
import subprocess
from pathlib import Path
import winreg
import file_functions as fi

#//make menu to pause in between 
def create_jsl_script(csv_file_path):
    # Create JSL code as a string
    jsl_code = f"""
Names Default To Here( 1 );
dt = Open( "{csv_file_path}" );
"""
    jsl_code += """
// Specify the column to be used for the y-axis
yColumn = Column(dt, "Data");
// Initialize a list to store columns for the x-axis
xColumns = {};
columnNames = dt << Get Column Names(string);
For(i = 1, i <= N Items(columnNames), i++,
    colName = columnNames[i];
    col = Column(dt, colName);
    levels =col << Get Values;
    // Use Associative Array to find unique values
    uniqueValues = Associative Array(levels) << Get Keys;
    
    // Check if the column name contains "Label" and has at least two unique items
    If (Contains(colName, "Label") & N Items(uniqueValues) >= 2,
        // Add the column to the list of x-axis columns
        Insert Into(xColumns, col);
    );
);
Show(xColumns);

// Create a variability chart using the specified y-axis and x-axis columns with point jitter
Variability Chart(
    Y(yColumn),
    X(Eval List(xColumns)),
    Data Table(dt),
    Points Jitter(1), // Add point jitter with a specified amount
	Show Averages(),
    Summary Report()
);
"""
    # Save JSL code to a file
    jsl_file_path = "variability_script.jsl"
    with open(jsl_file_path, "w") as file:
        file.write(jsl_code)

    print(f"JSL script created!")
    return jsl_file_path
        

def run_jsl(csv_path,jmp_executable_path):
    jsl_file_path = os.path.abspath(create_jsl_script(csv_path))
    command = f'"{jmp_executable_path}" "{jsl_file_path}"'
    subprocess.run(command, shell=True)
    process = subprocess.Popen([jmp_executable_path, jsl_file_path])
    print("JSL script executed in JMP.")

def stack_file(unstacked_input_file):
    stacked_data_out_file = str(unstacked_input_file).replace("dataoutput", "datastacked")
    df = pd.read_csv(unstacked_input_file)
    df_stacked = df.melt(id_vars=['Lot_WafXY','LOT','WAFER_ID','SORT_X','SORT_Y'], var_name='Label',value_name='Data')
    label_split = df_stacked['Label'].str.split('---', expand=True)
    label_split.columns = ["Label" + str(i + 1) for i in range(label_split.shape[1])]
    #cols_to_keep = [col for col in label_split.columns if label_split[col].nunique() >= 2] 
    #label_split_filtered = label_split[cols_to_keep]
    df_data = df_stacked['Data']
    df_stacked = df_stacked.drop(columns=['Label','Data'])
    #df_stack_filtered = pd.concat([df_stacked, label_split_filtered, df_data], axis=1)
    df_stacked = pd.concat([df_stacked, label_split, df_data], axis=1)
    df_stacked.to_csv(stacked_data_out_file, index=False)#originally df.to_csv
    print(stacked_data_out_file, "has been stacked!")
    return stacked_data_out_file

def stack_and_split_file(unstacked_input_file, label_column_names=None):
    stacked_data_out_file = str(unstacked_input_file).replace("dataoutput", "datastacked")
    stacked_data_out_file = fi.check_write_permission(stacked_data_out_file)
    df = pd.read_csv(unstacked_input_file)
    
    # Melt the dataframe to stack it
    df_stacked = df.melt(id_vars=['Lot_WafXY','LOT','WAFER_ID','SORT_X','SORT_Y'], 
                        var_name='Label', value_name='Data')
    
    # Split the Label column by '---'
    label_split = df_stacked['Label'].str.split('---', expand=True)
    
    # Apply custom column names if provided
    if label_column_names:
        # Ensure we have enough names for all split columns
        num_split_cols = label_split.shape[1]
        if len(label_column_names) < num_split_cols:
            # Extend with default names if not enough provided
            extended_names = label_column_names + [f"Label{i+len(label_column_names)+1}" 
                                                  for i in range(num_split_cols - len(label_column_names))]
            label_split.columns = extended_names
        else:
            # Use only the needed number of names
            label_split.columns = label_column_names[:num_split_cols]
    else:
        # Use default naming
        label_split.columns = ["Label" + str(i + 1) for i in range(label_split.shape[1])]
    
    # Get the data column
    df_data = df_stacked['Data']
    
    # Remove original Label and Data columns
    df_stacked = df_stacked.drop(columns=['Label','Data'])
    
    # Concatenate everything together
    df_stacked = pd.concat([df_stacked, label_split, df_data], axis=1)
    
    # Save to CSV
    df_stacked.to_csv(stacked_data_out_file, index=False)
    print(f"{stacked_data_out_file} has been stacked and split!")
    return stacked_data_out_file

def find_latest_jmp_pro_path():
    locations = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
    ]
    
    latest_version = 0
    latest_install_location = None
    
    for location in locations:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, location)
            
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                
                try:
                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    for version in range(14, 20):
                        if f"JMP Pro {version}" in display_name:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            if version > latest_version:
                                latest_version = version
                                latest_install_location = install_location
                except FileNotFoundError:
                    pass
                finally:
                    winreg.CloseKey(subkey)
            
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass
    
    return latest_install_location

if __name__ == "__main__":
    csv_path = Path("C:\\Users\\burtonr\\the best scripts\\DAC%_script_output\\LJPLL_TOP_CLKUTILS_K_SDTBEGIN_TAP_CORE_NOM_X_DCM_FLL_IREFTRIM_dataoutput.csv")
    jmp_executable_path = Path("C:\\Program Files\\SAS\\JMPPRO\\17\\jmp.exe")
    csv_path = stack_file(csv_path)
    run_jsl(csv_path,jmp_executable_path)