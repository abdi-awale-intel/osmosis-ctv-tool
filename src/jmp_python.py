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
    
    # Check if JMP executable exists
    if not os.path.exists(jmp_executable_path):
        raise FileNotFoundError(f"JMP executable not found at: {jmp_executable_path}")
    
    # Check if JSL file was created
    if not os.path.exists(jsl_file_path):
        raise FileNotFoundError(f"JSL script file not found at: {jsl_file_path}")
    
    try:
        # Use subprocess.run with proper shell handling for Windows
        result = subprocess.run([jmp_executable_path, jsl_file_path], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"JMP returned error code {result.returncode}")
            if result.stderr:
                print(f"JMP stderr: {result.stderr}")
        else:
            print("JSL script executed in JMP successfully.")
            
    except subprocess.TimeoutExpired:
        print("JMP execution timed out after 30 seconds")
    except PermissionError as e:
        print(f"Permission denied when trying to run JMP: {e}")
        print(f"Try running as administrator or check JMP installation permissions")
        raise
    except Exception as e:
        print(f"Error executing JMP: {e}")
        raise

def combine_stacked_files(stacked_file_list, output_folder=""):
    """
    Combine multiple stacked CSV files into one master CSV file for JMP analysis
    """
    if not stacked_file_list:
        print("No stacked files to combine")
        return None
    
    combined_data = []
    file_source_mapping = []
    
    for i, file_path in enumerate(stacked_file_list):
        try:
            if os.path.exists(file_path):
                print(f"Reading {os.path.basename(file_path)}...")
                df = pd.read_csv(file_path)
                
                # Add a source file identifier column
                df['Source_File'] = os.path.splitext(os.path.basename(file_path))[0]
                df['File_Index'] = i + 1
                
                combined_data.append(df)
                file_source_mapping.append({
                    'file_index': i + 1,
                    'filename': os.path.basename(file_path),
                    'full_path': file_path,
                    'rows': len(df)
                })
                print(f"  Added {len(df)} rows from {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    if not combined_data:
        print("No valid data found in stacked files")
        return None
    
    # Combine all dataframes
    master_df = pd.concat(combined_data, ignore_index=True, sort=False)
    
    # Generate output filename
    if output_folder:
        output_file = os.path.join(output_folder, "Combined_JMP_Data.csv")
    else:
        # Use the directory of the first file
        first_file_dir = os.path.dirname(stacked_file_list[0])
        output_file = os.path.join(first_file_dir, "Combined_JMP_Data.csv")
    
    # Ensure unique filename
    output_file = fi.check_write_permission(output_file)
    
    # Save combined data
    master_df.to_csv(output_file, index=False)
    
    # Print summary
    total_rows = len(master_df)
    total_files = len(file_source_mapping)
    print(f"\nCombined {total_files} files into {os.path.basename(output_file)}")
    print(f"Total rows: {total_rows}")
    print("File breakdown:")
    for mapping in file_source_mapping:
        print(f"  {mapping['file_index']}: {mapping['filename']} ({mapping['rows']} rows)")
    
    return output_file

def create_combined_jsl_script(combined_csv_path):
    """Create JSL code for analyzing combined CSV data from multiple sources"""
    # Create enhanced JSL code for combined data analysis
    jsl_code = f"""
Names Default To Here( 1 );

// Open the combined dataset
dt = Open( "{combined_csv_path}" );

// Set the window title
dt << Set Name( "Combined CTV Data Analysis" );

// Get basic info about the dataset
n_rows = N Rows( dt );
n_cols = N Cols( dt );
Print( "Dataset loaded with " || Char( n_rows ) || " rows and " || Char( n_cols ) || " columns" );

// Identify the Data column for Y-axis
yColumn = Column(dt, "Data");

// Initialize lists for analysis
xColumns = {{}};
sourceFiles = {{}};
columnNames = dt << Get Column Names(string);

// Get unique source files
if( Contains( columnNames, "Source_File" ),
    sourceCol = Column(dt, "Source_File");
    sourceFiles = Associative Array( sourceCol << Get Values ) << Get Keys;
    Print( "Found " || Char( N Items( sourceFiles ) ) || " source files: " );
    For( i = 1, i <= N Items( sourceFiles ), i++,
        Print( "  " || Char( i ) || ": " || sourceFiles[i] );
    );
);

// Find columns suitable for X-axis (Label columns with multiple unique values)
For(i = 1, i <= N Items(columnNames), i++,
    colName = columnNames[i];
    
    // Skip certain columns
    if( !Contains( colName, "Source_File" ) & !Contains( colName, "File_Index" ) & 
        !Contains( colName, "Data" ) & !Contains( colName, "Lot_WafXY" ),
        
        col = Column(dt, colName);
        levels = col << Get Values;
        uniqueValues = Associative Array(levels) << Get Keys;
        
        // Include columns with at least 2 unique values
        If( Contains(colName, "Label") & N Items(uniqueValues) >= 2,
            Insert Into(xColumns, col);
            Print( "Added X-axis column: " || colName || " (" || Char( N Items(uniqueValues) ) || " unique values)" );
        );
    );
);

// Create the main variability chart
Print( "Creating variability chart..." );
variChart = Variability Chart(
    Y(yColumn),
    X(Eval List(xColumns)),
    Data Table(dt),
    Points Jitter(1),
    Show Averages(1),
    Show Grand Mean(1),
    Show Grand Median(1),
    Connect Means(1),
    Summary Report(1)
);

// Add source file grouping if available
if( Contains( columnNames, "Source_File" ),
    Print( "Adding source file analysis..." );
    
    // Create a separate chart grouped by source file
    variChart2 = Variability Chart(
        Y(yColumn),
        X(Column(dt, "Source_File"), Eval List(xColumns)),
        Data Table(dt),
        Points Jitter(1),
        Show Averages(1),
        Connect Means(1),
        Summary Report(1)
    );
    
    // Create a summary table by source file
    summaryDT = dt << Summary(
        Group( :Source_File ),
        Mean( :Data ),
        Std Dev( :Data ),
        Min( :Data ),
        Max( :Data ),
        N( :Data )
    );
    summaryDT << Set Name( "Summary by Source File" );
);

// Create distribution analysis
Print( "Creating data distribution analysis..." );
distChart = Distribution(
    Column( :Data ),
    Data Table(dt),
    Histogram( 1 ),
    Normal Quantile Plot( 1 ),
    Summary Statistics( 1 ),
    Outlier Box Plot( 1 )
);

// If we have multiple source files, create by-group distribution
if( Contains( columnNames, "Source_File" ),
    distBySource = Distribution(
        Column( :Data ),
        By( :Source_File ),
        Data Table(dt),
        Histogram( 1 ),
        Summary Statistics( 1 )
    );
);

Print( "Analysis complete! Multiple windows created for comprehensive data review." );
Print( "Windows created:" );
Print( "  1. Main Variability Chart - Overall data trends" );
Print( "  2. Source File Variability Chart - Comparison between files" );
Print( "  3. Data Distribution - Statistical analysis" );
Print( "  4. Distribution by Source - Per-file statistics" );
Print( "  5. Summary Table - Numerical summary by source file" );
"""
    
    # Save JSL code to a file
    jsl_file_path = "combined_variability_script.jsl"
    with open(jsl_file_path, "w") as file:
        file.write(jsl_code)

    print(f"Enhanced JSL script created for combined data analysis!")
    return jsl_file_path

def run_combined_jsl(combined_csv_path, jmp_executable_path):
    """Run JMP analysis on combined CSV data"""
    jsl_file_path = os.path.abspath(create_combined_jsl_script(combined_csv_path))
    
    # Check if JMP executable exists
    if not os.path.exists(jmp_executable_path):
        raise FileNotFoundError(f"JMP executable not found at: {jmp_executable_path}")
    
    # Check if JSL file was created
    if not os.path.exists(jsl_file_path):
        raise FileNotFoundError(f"JSL script file not found at: {jsl_file_path}")
    
    # Check if combined CSV exists
    if not os.path.exists(combined_csv_path):
        raise FileNotFoundError(f"Combined CSV file not found at: {combined_csv_path}")
    
    try:
        print(f"Opening combined data analysis in JMP...")
        print(f"Data file: {os.path.basename(combined_csv_path)}")
        
        # Use subprocess.run with proper shell handling for Windows
        result = subprocess.run([jmp_executable_path, jsl_file_path], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"JMP returned error code {result.returncode}")
            if result.stderr:
                print(f"JMP stderr: {result.stderr}")
        else:
            print("Combined JSL script executed in JMP successfully.")
            print("JMP will open with comprehensive analysis of all your stacked data.")
            
    except subprocess.TimeoutExpired:
        print("JMP execution timed out after 60 seconds")
    except PermissionError as e:
        print(f"Permission denied when trying to run JMP: {e}")
        print(f"Try running as administrator or check JMP installation permissions")
        raise
    except Exception as e:
        print(f"Error executing JMP: {e}")
        raise

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

if __name__ == "__main__":
    csv_path = Path("C:\\Users\\burtonr\\the best scripts\\DAC%_script_output\\LJPLL_TOP_CLKUTILS_K_SDTBEGIN_TAP_CORE_NOM_X_DCM_FLL_IREFTRIM_dataoutput.csv")
    jmp_executable_path = Path("C:\\Program Files\\SAS\\JMPPRO\\17\\jmp.exe")
    csv_path = stack_file(csv_path)
    run_jsl(csv_path,jmp_executable_path)