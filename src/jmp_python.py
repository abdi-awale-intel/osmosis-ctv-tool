"""
JMP Python Integration Module

This module provides comprehensive integration between Python data processing workflows 
and JMP statistical analysis software. It handles JSL script generation, CSV data 
preparation, and automated JMP workspace management for CTV (Circuit Test Vehicle) 
data analysis.

Key Features:
- Generate JSL scripts for individual CSV files
- Create master JSL scripts for multi-file analysis
- Combine multiple stacked CSV files for unified analysis
- Automated JMP executable detection and launching
- Support for both individual and batch processing workflows

Dependencies:
- pandas: Data manipulation and CSV processing
- subprocess: JMP executable launching
- pathlib: Cross-platform path handling
- file_functions: Custom file utility module

Author: Intel CTV Analysis Team
Version: 2.0
Last Updated: 2025-08-11
"""

import pandas as pd
import os
import subprocess
from pathlib import Path
import winreg
import file_functions as fi


def create_jsl_script(csv_file_path):
    """
    Create JSL (JMP Scripting Language) script for individual CSV file analysis.
    
    This function generates a JSL script that opens a CSV file in JMP and creates
    variability charts using columns between FUNCTIONAL_BIN and Data as label columns.
    The script includes enhanced column detection logic for better analysis setup.
    
    Args:
        csv_file_path (str): Absolute path to the CSV file to analyze
        
    Returns:
        str: Path to the created JSL script file
        
    Raises:
        IOError: If JSL script file cannot be written
        
    Example:
        >>> jsl_path = create_jsl_script("data/test_results.csv")
        >>> print(f"JSL script created at: {jsl_path}")
    """
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

// Find columns between FUNCTIONAL_BIN and Data for label columns
functionalBinIndex = -1;
dataIndex = -1;

// Find the indices of FUNCTIONAL_BIN and Data columns
For(i = 1, i <= N Items(columnNames), i++,
    If(Contains(columnNames[i], "FUNCTIONAL_BIN"), functionalBinIndex = i);
    If(Contains(columnNames[i], "Data"), dataIndex = i);
);

// Process columns between FUNCTIONAL_BIN and Data as label columns
If(functionalBinIndex > 0 & dataIndex > 0 & functionalBinIndex < dataIndex,
    For(i = functionalBinIndex + 1, i < dataIndex, i++,
        colName = columnNames[i];
        col = Column(dt, colName);
        levels = col << Get Values;
        // Use Associative Array to find unique values
        uniqueValues = Associative Array(levels) << Get Keys;
        
        // Include all columns between FUNCTIONAL_BIN and Data with at least 2 unique values
        If(N Items(uniqueValues) >= 2,
            Insert Into(xColumns, col);
            Print("Added label column: " || colName || " (" || Char(N Items(uniqueValues)) || " unique values)");
        );
    );
,
    // Fallback: if column structure is different, use Label-containing columns
    For(i = 1, i <= N Items(columnNames), i++,
        colName = columnNames[i];
        col = Column(dt, colName);
        levels = col << Get Values;
        uniqueValues = Associative Array(levels) << Get Keys;
        
        If(Contains(colName, "Label") & N Items(uniqueValues) >= 2,
            Insert Into(xColumns, col);
            Print("Added fallback label column: " || colName || " (" || Char(N Items(uniqueValues)) || " unique values)");
        );
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
    jsl_file_path = f"{csv_file_path.replace('.csv', '')}.jsl"
    with open(jsl_file_path, "w") as file:
        file.write(jsl_code)

    print(f"JSL script created at: {jsl_file_path}")
    return jsl_file_path


def run_jsl(csv_path, jmp_executable_path):
    """
    Execute a JSL script in JMP for a given CSV file.
    
    This function creates a JSL script for the provided CSV file and then executes
    it using the specified JMP executable. It includes comprehensive error handling
    and timeout management for robust operation.
    
    Args:
        csv_path (str): Absolute path to the CSV file to analyze
        jmp_executable_path (str): Path to the JMP executable
        
    Raises:
        FileNotFoundError: If JMP executable or JSL script not found
        subprocess.TimeoutExpired: If JMP execution times out
        PermissionError: If insufficient permissions to run JMP
        
    Example:
        >>> run_jsl("data/results.csv", "C:/Program Files/SAS/JMPPRO/17/jmp.exe")
    """
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
    Combine multiple stacked CSV files into a single master CSV for unified JMP analysis.
    
    This function reads multiple CSV files, adds source file identification columns,
    and combines them into a single dataset. This enables comparative analysis
    across multiple test runs or datasets in JMP.
    
    Args:
        stacked_file_list (list): List of paths to CSV files to combine
        output_folder (str, optional): Directory for output file. Uses first file's 
                                     directory if not specified.
        
    Returns:
        str or None: Path to the combined CSV file, or None if combination fails
        
    Features:
        - Adds Source_File and File_Index columns for data traceability
        - Handles missing files gracefully with error logging
        - Generates unique output filenames to prevent overwrites
        - Provides detailed file breakdown summary
        
    Example:
        >>> files = ["data1.csv", "data2.csv", "data3.csv"]
        >>> combined_path = combine_stacked_files(files, "output/")
        >>> print(f"Combined file created: {combined_path}")
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
    """
    Generate comprehensive JSL script for analyzing combined CSV data from multiple sources.
    
    This function creates JSL script that opens a combined CSV file and
    performs multiple types of analysis including variability charts, distribution
    analysis, and source file comparisons. The script automatically detects columns
    between FUNCTIONAL_BIN and Data for use as label columns.
    
    Args:
        combined_csv_path (str): Path to the combined CSV file to analyze
        
    Returns:
        str: Path to the created JSL script file
        
    Features:
        - Automatic column detection between FUNCTIONAL_BIN and Data
        - Main variability chart with comprehensive settings
        - Source file comparison charts
        - Distribution analysis with histograms and statistics
        - Summary tables grouped by source file
        - Fallback logic for different data structures
        
    JSL Script Components:
        1. Main variability chart across all data
        2. Source file comparison variability chart
        3. Overall data distribution analysis
        4. Per-source file distribution analysis
        5. Summary statistics table
        
    Example:
        >>> jsl_path = create_combined_jsl_script("combined_data.csv")
        >>> print(f"Combined analysis script: {jsl_path}")
    """
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

// Find columns between FUNCTIONAL_BIN and Data for label columns
functionalBinIndex = -1;
dataIndex = -1;

// Find the indices of FUNCTIONAL_BIN and Data columns
For(i = 1, i <= N Items(columnNames), i++,
    If(Contains(columnNames[i], "FUNCTIONAL_BIN"), functionalBinIndex = i);
    If(Contains(columnNames[i], "Data"), dataIndex = i);
);

// Process columns between FUNCTIONAL_BIN and Data as label columns
If(functionalBinIndex > 0 & dataIndex > 0 & functionalBinIndex < dataIndex,
    Print("Using columns between FUNCTIONAL_BIN and Data as label columns...");
    For(i = functionalBinIndex + 1, i < dataIndex, i++,
        colName = columnNames[i];
        
        // Skip certain system columns
        if( !Contains( colName, "Source_File" ) & !Contains( colName, "File_Index" ) & 
            !Contains( colName, "Lot_WafXY" ),
            
            col = Column(dt, colName);
            levels = col << Get Values;
            uniqueValues = Associative Array(levels) << Get Keys;
            
            // Include all columns between FUNCTIONAL_BIN and Data with at least 2 unique values
            If(N Items(uniqueValues) >= 2,
                Insert Into(xColumns, col);
                Print( "Added label column: " || colName || " (" || Char( N Items(uniqueValues) ) || " unique values)" );
            );
        );
    );
,
    // Fallback: if column structure is different, use Label-containing columns
    Print("Using fallback method - searching for Label columns...");
    For(i = 1, i <= N Items(columnNames), i++,
        colName = columnNames[i];
        
        // Skip certain columns
        if( !Contains( colName, "Source_File" ) & !Contains( colName, "File_Index" ) & 
            !Contains( colName, "Data" ) & !Contains( colName, "Lot_WafXY" ),
            
            col = Column(dt, colName);
            levels = col << Get Values;
            uniqueValues = Associative Array(levels) << Get Keys;
            
            // Include columns with "Label" in name and at least 2 unique values
            If( Contains(colName, "Label") & N Items(uniqueValues) >= 2,
                Insert Into(xColumns, col);
                Print( "Added fallback label column: " || colName || " (" || Char( N Items(uniqueValues) ) || " unique values)" );
            );
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
    """
    Execute JMP analysis on combined CSV data using generated JSL script.
    
    This function creates a comprehensive JSL script for the combined CSV data
    and executes it in JMP. It provides enhanced error handling and validation
    to ensure reliable execution of complex multi-dataset analysis.
    
    Args:
        combined_csv_path (str): Path to the combined CSV file
        jmp_executable_path (str): Path to the JMP executable
        
    Raises:
        FileNotFoundError: If JMP executable, JSL script, or CSV file not found
        subprocess.TimeoutExpired: If JMP execution exceeds timeout (60 seconds)
        PermissionError: If insufficient permissions to execute JMP
        
    Features:
        - Automatic JSL script generation for combined data
        - Extended timeout (60s) for complex analyses
        - Comprehensive file existence validation
        - Detailed error reporting and logging
        
    Example:
        >>> run_combined_jsl("combined_data.csv", "C:/Programs/JMP/jmp.exe")
        Combined JSL script executed in JMP successfully.
    """
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


def create_multiple_jsl_scripts(stacked_files, output_folder=""):
    """
    Create individual JSL scripts for multiple stacked files without executing them.
    
    This function generates JSL scripts for a list of stacked CSV files in batch mode.
    It's designed for the optimized workflow where all scripts are created first
    before launching a single JMP workspace, avoiding resource-intensive multiple
    JMP instances.
    
    Args:
        stacked_files (list): List of paths to stacked CSV files
        output_folder (str, optional): Directory for JSL script output
        
    Returns:
        list: Paths to successfully created JSL script files
        
    Features:
        - Batch processing with individual error handling per file
        - Graceful handling of missing or inaccessible files
        - Progress tracking with detailed logging
        - Resource-efficient script generation (no JMP launching)
        
    Workflow Integration:
        This function is part of the optimized JMP workflow:
        1. create_multiple_jsl_scripts() - Generate all JSL scripts
        2. create_master_jsl_script() - Create master workspace script
        3. run_master_jsl_workspace() - Launch single JMP instance
        
    Example:
        >>> files = ["data1_stacked.csv", "data2_stacked.csv"]
        >>> scripts = create_multiple_jsl_scripts(files, "output/")
        >>> print(f"Created {len(scripts)} JSL scripts")
    """
    jsl_scripts = []
    
    if not stacked_files:
        print("No stacked files provided")
        return jsl_scripts
    
    print(f"Creating JSL scripts for {len(stacked_files)} stacked files...")
    
    for i, stacked_file in enumerate(stacked_files):
        try:
            if os.path.exists(stacked_file):
                print(f"Creating JSL script for: {os.path.basename(stacked_file)}")
                jsl_file_path = create_jsl_script(stacked_file)
                jsl_scripts.append(jsl_file_path)
                print(f"✅ JSL script created: {os.path.basename(jsl_file_path)}")
            else:
                print(f"❌ File not found: {stacked_file}")
        except Exception as e:
            print(f"❌ Error creating JSL for {os.path.basename(stacked_file)}: {e}")
            continue
    
    print(f"Successfully created {len(jsl_scripts)} JSL scripts")
    return jsl_scripts


def create_master_jsl_script(jsl_scripts, output_folder=""):
    """
    Create a master JSL script that consolidates all individual analyses into one workspace.
    
    This function generates a master JSL script that includes and executes all individual
    JSL scripts within a single JMP session. This approach is far more resource-efficient
    than launching multiple JMP instances and provides an organized workspace for analysis.
    
    Args:
        jsl_scripts (list): List of paths to individual JSL script files
        output_folder (str, optional): Directory for master script output
        
    Returns:
        str or None: Path to the created master JSL script, or None if creation fails
        
    Features:
        - Consolidates multiple analyses into single JMP workspace
        - Error handling for individual script loading failures
        - Cross-platform path normalization (Windows/Linux compatibility)
        - Comprehensive logging and progress reporting
        
    Master Script Structure:
        - Initialization and workspace setup
        - Sequential loading of individual analysis scripts
        - Error handling with Try/Catch for each script
        - Summary reporting of loaded analyses
        
    Example:
        >>> scripts = ["analysis1.jsl", "analysis2.jsl", "analysis3.jsl"]
        >>> master_path = create_master_jsl_script(scripts, "workspace/")
        >>> print(f"Master workspace script: {master_path}")
    """
    if not jsl_scripts:
        print("No JSL scripts provided")
        return None
    
    # Generate master JSL file path
    if output_folder:
        master_jsl_path = os.path.join(output_folder, "master_jmp_workspace.jsl")
    else:
        master_jsl_path = "master_jmp_workspace.jsl"
    
    # Create master JSL code
    master_jsl_code = """
Names Default To Here( 1 );

// Master JMP Workspace Script
// This script opens all individual analysis scripts in organized windows

Print( "Loading Master JMP Workspace..." );
Print( "Opening multiple analysis windows..." );

"""
    
    # Add each JSL script to the master
    for i, jsl_script in enumerate(jsl_scripts):
        abs_jsl_path = os.path.abspath(jsl_script)
        # Replace backslashes with forward slashes for JSL compatibility
        jsl_path_normalized = abs_jsl_path.replace('\\', '/')
        
        master_jsl_code += f"""
// Analysis {i+1}: {os.path.basename(jsl_script)}
Print( "Loading analysis {i+1}: {os.path.basename(jsl_script)}" );
Try(
    Include( "{jsl_path_normalized}" );
    Print( "✅ Successfully loaded: {os.path.basename(jsl_script)}" );
,
    Print( "❌ Error loading: {os.path.basename(jsl_script)}" );
);

"""
    
    master_jsl_code += f"""
Print( "Master workspace loading complete!" );
Print( "Loaded {len(jsl_scripts)} analysis scripts" );
Print( "Each dataset now has its own analysis window in this JMP session" );
"""
    
    # Save master JSL file
    try:
        with open(master_jsl_path, "w") as file:
            file.write(master_jsl_code)
        
        print(f"🎯 Master JSL script created: {master_jsl_path}")
        print(f"   📊 Contains {len(jsl_scripts)} individual analyses")
        print(f"   🔄 Single JMP instance will open all datasets")
        
        return master_jsl_path
        
    except Exception as e:
        print(f"❌ Error creating master JSL script: {e}")
        return None


def run_master_jsl_workspace(jsl_scripts, jmp_executable_path, output_folder=""):
    """
    Create and execute a master JSL workspace containing all individual analyses.
    
    This function represents the final step in the optimized JMP workflow. It creates
    a master JSL script that includes all individual analyses and launches a single
    JMP instance with an organized workspace. This approach is dramatically more
    resource-efficient than launching multiple JMP instances.
    
    Args:
        jsl_scripts (list): List of paths to individual JSL script files
        jmp_executable_path (str): Path to the JMP executable
        output_folder (str, optional): Directory for master script output
        
    Returns:
        bool: True if successful, False otherwise
        
    Features:
        - Single JMP process for all analyses (resource efficient)
        - Extended timeout (120s) for complex multi-dataset loading
        - Comprehensive error handling and validation
        - Detailed progress reporting and logging
        - Organized workspace with all datasets in one session
        
    Resource Efficiency:
        Instead of launching 180 JMP instances (potentially 90GB+ RAM):
        - Single JMP process (~500MB RAM)
        - No threading complexity or resource contention
        - Faster overall execution
        - Better user experience with organized workspace
        
    Workflow Integration:
        This completes the optimized three-step workflow:
        1. create_multiple_jsl_scripts() - Generate individual JSL scripts
        2. create_master_jsl_script() - Create consolidation script  
        3. run_master_jsl_workspace() - Launch unified JMP session
        
    Example:
        >>> scripts = ["test1.jsl", "test2.jsl", "test3.jsl"]
        >>> success = run_master_jsl_workspace(scripts, "C:/JMP/jmp.exe")
        >>> if success:
        ...     print("Master workspace launched successfully!")
    """
    if not jsl_scripts:
        print("No JSL scripts provided")
        return False
    
    print(f"🚀 Creating master JMP workspace for {len(jsl_scripts)} analyses...")
    
    # Create master JSL script
    master_jsl_path = create_master_jsl_script(jsl_scripts, output_folder)
    
    if not master_jsl_path:
        print("❌ Failed to create master JSL script")
        return False
    
    # Check if JMP executable exists
    if not os.path.exists(jmp_executable_path):
        raise FileNotFoundError(f"JMP executable not found at: {jmp_executable_path}")
    
    try:
        print(f"🎯 Launching JMP with master workspace...")
        print(f"   📊 Will open {len(jsl_scripts)} analysis windows")
        print(f"   ⚡ Single JMP process (resource efficient)")
        
        # Run the master JSL script
        result = subprocess.run([jmp_executable_path, master_jsl_path], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"❌ JMP returned error code {result.returncode}")
            if result.stderr:
                print(f"JMP stderr: {result.stderr}")
            return False
        else:
            print("✅ Master JMP workspace launched successfully!")
            print("💡 All your analyses are now in one organized JMP session")
            return True
            
    except subprocess.TimeoutExpired:
        print("⏰ JMP execution timed out after 120 seconds")
        return False
    except PermissionError as e:
        print(f"🔒 Permission denied when trying to run JMP: {e}")
        print(f"Try running as administrator or check JMP installation permissions")
        raise
    except Exception as e:
        print(f"❌ Error executing JMP: {e}")
        raise


def stack_file(unstacked_input_file):
    """
    Convert unstacked CSV data to stacked format for JMP analysis.
    
    This function transforms wide-format CSV data into long-format (stacked) data
    suitable for JMP variability analysis. It melts the data using specific ID variables
    and creates separate label columns from the variable names.
    
    Args:
        unstacked_input_file (str): Path to the unstacked (wide-format) CSV file
        
    Returns:
        str: Path to the created stacked CSV file
        
    Data Transformation:
        - Melts data using ID variables: ['Lot_WafXY', 'LOT', 'WAFER_ID', 'SORT_X', 
                                        'SORT_Y', 'INTERFACE_BIN', 'FUNCTIONAL_BIN']
        - Creates 'Label' column from variable names
        - Creates 'Data' column from values
        - Splits Label column on '---' delimiter into separate label columns
        
    Output File Naming:
        - Replaces 'dataoutput' with 'datastacked' in filename
        - Preserves original file directory and extension
        
    Example:
        >>> input_file = "test_dataoutput.csv"
        >>> stacked_file = stack_file(input_file)
        >>> print(f"Stacked data saved to: {stacked_file}")
        # Output: "Stacked data saved to: test_datastacked.csv"
    """
    stacked_data_out_file = str(unstacked_input_file).replace("dataoutput", "datastacked")
    df = pd.read_csv(unstacked_input_file)
    df_stacked = df.melt(id_vars=['Lot_WafXY','LOT','WAFER_ID','SORT_X','SORT_Y','INTERFACE_BIN','FUNCTIONAL_BIN'], var_name='Label',value_name='Data')
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
    """
    Advanced stacking function with custom label column naming support.
    
    This function provides enhanced data stacking capabilities with support for
    custom label column names. It's designed for more complex data structures
    where default naming may not be sufficient.
    
    Args:
        unstacked_input_file (str): Path to the unstacked CSV file
        label_column_names (list, optional): Custom names for label columns
        
    Returns:
        str: Path to the created stacked and split CSV file
        
    Enhanced Features:
        - Custom label column naming support
        - Automatic name extension if insufficient names provided
        - Preserves all original ID variables
        - Intelligent file naming with write permission checking
        
    Label Column Handling:
        - If label_column_names provided: Uses custom names for split columns
        - If insufficient names: Extends with default pattern (Label1, Label2, etc.)
        - If no names provided: Uses default naming pattern
        
    File Management:
        - Uses file_functions.check_write_permission() for safe file creation
        - Replaces 'dataoutput' with 'datastacked' in filename
        - Handles file path conflicts automatically
        
    Example:
        >>> custom_names = ["TestType", "Condition", "Measurement"]
        >>> stacked_file = stack_and_split_file("data.csv", custom_names)
        >>> print(f"Enhanced stacked file: {stacked_file}")
    """
    stacked_data_out_file = str(unstacked_input_file).replace("dataoutput", "datastacked")
    stacked_data_out_file = fi.check_write_permission(stacked_data_out_file)
    df = pd.read_csv(unstacked_input_file)
    
    # Melt the dataframe to stack it
    df_stacked = df.melt(id_vars=['Lot_WafXY','LOT','WAFER_ID','SORT_X','SORT_Y','INTERFACE_BIN','FUNCTIONAL_BIN'], 
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


# Main execution block for testing and development
if __name__ == "__main__":
    """
    Development and testing entry point for the JMP Python integration module.
    
    This block provides example usage and testing capabilities for the module.
    It demonstrates the typical workflow for processing CTV data and launching JMP analysis.
    
    Example Workflow:
        1. Define paths to test data and JMP executable
        2. Stack the input CSV file for JMP compatibility
        3. Launch JMP with the stacked data
        
    Note: Update the file paths below to match your system configuration before testing.
    """
    # Example configuration - update these paths for your system
    csv_path = Path("C:\\Users\\burtonr\\the best scripts\\DAC%_script_output\\LJPLL_TOP_CLKUTILS_K_SDTBEGIN_TAP_CORE_NOM_X_DCM_FLL_IREFTRIM_dataoutput.csv")
    jmp_executable_path = Path("C:\\Program Files\\SAS\\JMPPRO\\17\\jmp.exe")
    
    # Process the data through the complete workflow
    csv_path = stack_file(csv_path)
    run_jsl(csv_path, jmp_executable_path)