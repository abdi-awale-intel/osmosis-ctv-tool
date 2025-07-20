import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import sys
import csv
import json
import re
import time
import datetime
import threading

# Import PIL for images (with fallback)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available - images will be disabled")

# Import your existing modules
import file_functions as fi
import mtpl_parser as mt
import index_ctv as ind

# Import pyuber_query with fallback handling
import pyuber_query as py
PYUBER_AVAILABLE = True

# Import smart_json_parser if available
SMART_CTV_AVAILABLE = False
sm = None

try:
    # Try relative import first (for packaged executable)
    from . import smart_json_parser as sm
    # Test that the module actually has the required function
    if hasattr(sm, 'process_SmartCTV'):
        SMART_CTV_AVAILABLE = True
        print("✅ SmartCTV module loaded successfully (relative import)")
    else:
        sm = None
        print("⚠️ SmartCTV module found but missing required functions (relative import)")
except ImportError as e:
    print(f"❌ Relative import failed: {e}")
    try:
        # Try direct import (for development environment)
        import smart_json_parser as sm
        if hasattr(sm, 'process_SmartCTV'):
            SMART_CTV_AVAILABLE = True
            print("✅ SmartCTV module loaded successfully (direct import)")
        else:
            sm = None
            print("⚠️ SmartCTV module found but missing required functions (direct import)")
    except ImportError as e:
        print(f"❌ Direct import failed: {e}")
        try:
            # Try importing from src directory
            import src.smart_json_parser as sm
            if hasattr(sm, 'process_SmartCTV'):
                SMART_CTV_AVAILABLE = True
                print("✅ SmartCTV module loaded successfully (src import)")
            else:
                sm = None
                print("⚠️ SmartCTV module found but missing required functions (src import)")
        except ImportError as e:
            print(f"❌ Src import failed: {e}")
            sm = None
            SMART_CTV_AVAILABLE = False
            print("❌ SmartCTV functionality not available - all import methods failed")

# Final validation
if SMART_CTV_AVAILABLE and sm is not None:
    try:
        # Test that we can actually access the function
        func = getattr(sm, 'process_SmartCTV', None)
        if func is None:
            SMART_CTV_AVAILABLE = False
            sm = None
            print("❌ SmartCTV process_SmartCTV function not found, disabling SmartCTV")
        else:
            print(f"✅ SmartCTV fully validated and ready")
    except Exception as e:
        print(f"❌ SmartCTV validation failed: {e}")
        SMART_CTV_AVAILABLE = False
        sm = None
        
print(f"🔧 Final SmartCTV status: Available={SMART_CTV_AVAILABLE}, Module={sm is not None}")
class CTVListGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CTV List Data Processor")
        self.root.geometry("1400x800")  # Set better initial size
        self.root.minsize(800, 600)     # Set minimum window size
        
        # Set application icon
        if PIL_AVAILABLE:
            try:
                icon_image = Image.open(r"C:\Users\abdiawal\Downloads\logo.jpeg")
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(False, icon_photo)
            except Exception as e:
                print(f"Could not load app icon: {e}")
        
        # Variables
        self.material_df = None
        self.mtpl_df = None
        self.mtpl_csv_path = ""
        self.mtpl_file_path = tk.StringVar()
        self.test_list = []
        self.output_folder = ""
        self.all_mtpl_items = []  # Store all items for filtering
        self.is_dark_mode = False  # Track current theme
        self.processing = False
        
        # Initialize theme components as None for fallback handling
        self.light_logo = None
        self.dark_logo = None
        self.light_mode_btn = None
        self.dark_mode_btn = None
        self.theme_label = None
        
        # Setup window management first
        self.setup_window_management()
        
        self.create_widgets()
        
    def setup_window_management(self):
        """Setup proper window state handling and resize management"""
        # Configure root window grid weights for proper resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Bind window events for proper handling of resize/minimize/maximize
        self.root.bind('<Configure>', self.on_window_configure)
        self.root.bind('<Map>', self.on_window_state_change)      # Window restored
        self.root.bind('<Unmap>', self.on_window_state_change)    # Window minimized
        
        # Track window state
        self.window_state = "normal"
        self.last_geometry = None
        
    def on_window_configure(self, event):
        """Handle window resize events"""
        if event.widget == self.root:
            # Only refresh if the window size actually changed
            current_geometry = self.root.geometry()
            if current_geometry != self.last_geometry:
                self.last_geometry = current_geometry
                # Small delay to allow window to settle
                self.root.after(100, self.safe_refresh_displays)# Only refresh if the window size actually changed
            current_geometry = self.root.geometry()
            if current_geometry != self.last_geometry:
                self.last_geometry = current_geometry
                # Small delay to allow window to settle
                self.root.after(100, self.safe_refresh_displays)
                
    def on_window_state_change(self, event):
        """Handle window minimize/maximize events"""
        if event.widget == self.root:
            current_state = self.root.state()
            if current_state != self.window_state:
                self.window_state = current_state
                # Force refresh of all widgets after state change
                self.root.after(150, self.safe_refresh_displays)
            if current_state != self.window_state:
                self.window_state = current_state
                # Force refresh of all widgets after state change
                self.root.after(150, self.safe_refresh_displays)
                
    def safe_refresh_displays(self):
        """Safely refresh all data displays with error handling"""
        try:
            # Force update of all widgets
            self.root.update_idletasks()
            
            # Refresh material data display if data exists
            if hasattr(self, 'material_df') and self.material_df is not None:
                self.refresh_material_data_display()
                
            # Refresh MTPL display if data exists
            if hasattr(self, 'all_mtpl_items') and self.all_mtpl_items:
                self.refresh_mtpl_display()
                
        except tk.TclError as e:
            print(f"Tkinter error during refresh: {e}")
            # Retry after a longer delay if widget was destroyed
            self.root.after(200, self.safe_refresh_displays)
        except Exception as e:
            print(f"Unexpected error during refresh: {e}")
            
    def refresh_material_data_display(self):
        """Refresh the material data table display after window operations"""
        try:
            if not hasattr(self, 'material_tree') or not self.material_tree.winfo_exists():
                return
                
            # Clear existing items
            for item in self.material_tree.get_children():
                self.material_tree.delete(item)
            
            # Re-populate with current data if available
            if self.material_df is not None and not self.material_df.empty:
                # Reconfigure columns
                self.material_tree['columns'] = list(self.material_df.columns)
                self.material_tree['show'] = 'headings'
                
                # Configure column headings with better settings for resize
                for col in self.material_df.columns:
                    self.material_tree.heading(col, text=col)
                    self.material_tree.column(col, width=150, minwidth=100, anchor='center')
                    
                # Insert data with alternating row colors
                for index, row in self.material_df.iterrows():
                    tag = 'evenrow' if index % 2 == 0 else 'oddrow'
                    values = list(row)
                    self.material_tree.insert('', 'end', values=values, tags=(tag,))
                
                # Configure alternating colors
                self.configure_treeview_alternating_colors()
                
            # Force update
            self.material_tree.update_idletasks()
            
        except Exception as e:
            print(f"Error refreshing material data: {e}")
            
    def refresh_mtpl_display(self):
        """Refresh the MTPL data table display after window operations"""
        try:
            if not hasattr(self, 'mtpl_tree') or not self.mtpl_tree.winfo_exists():
                return
                
            # Re-display current filtered items
            if hasattr(self, 'all_mtpl_items') and self.all_mtpl_items:
                # Get current search text to maintain filter state
                search_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
                
                if not search_text:
                    filtered_items = self.all_mtpl_items
                else:
                    filtered_items = []
                    for item_data in self.all_mtpl_items:
                        item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                        if search_text in item_text:
                            filtered_items.append(item_data)
                
                self.display_filtered_items(filtered_items)
                
        except Exception as e:
            print(f"Error refreshing MTPL data: {e}")
    
    def create_widgets(self):
        # Add theme toggle logos at the top center
        if PIL_AVAILABLE:
            try:
                # Load light mode and dark mode logos
                lightmode_logo_path = r"C:\Users\abdiawal\Downloads\lightmode-logo.jpg"
                darkmode_logo_path = r"C:\Users\abdiawal\Downloads\darkmode-logo.png"
                
                # Load and resize logos
                light_image = Image.open(lightmode_logo_path)
                dark_image = Image.open(darkmode_logo_path)
                
                # Resize logos to fit nicely (adjust size as needed)
                light_image = light_image.resize((80, 60), Image.Resampling.LANCZOS)
                dark_image = dark_image.resize((80, 60), Image.Resampling.LANCZOS)
                
                self.light_logo = ImageTk.PhotoImage(light_image)
                self.dark_logo = ImageTk.PhotoImage(dark_image)
                
                # Create logo frame at the top
                logo_frame = ttk.Frame(self.root)
                logo_frame.pack(pady=10)
                
                # Create frame for the two logos side by side
                logos_container = ttk.Frame(logo_frame)
                logos_container.pack()
                
                # Add light mode logo button (left)
                self.light_mode_btn = tk.Label(logos_container, image=self.light_logo, cursor="hand2")
                self.light_mode_btn.pack(side='left', padx=(0, 2))
                self.light_mode_btn.bind('<Button-1>', self.switch_to_light_mode)
                
                # Add dark mode logo button (right)
                self.dark_mode_btn = tk.Label(logos_container, image=self.dark_logo, cursor="hand2")
                self.dark_mode_btn.pack(side='left', padx=(2, 0))
                self.dark_mode_btn.bind('<Button-1>', self.switch_to_dark_mode)
                
                # Add application title below logos
                title_label = ttk.Label(logo_frame, text="CTV List Data Processor", 
                                      font=('Arial', 16, 'bold'), foreground='#0071c5')
                title_label.pack(pady=(10, 10))
                
                # Add theme indicator
                self.theme_label = ttk.Label(logo_frame, text="Light Mode", 
                                           font=('Arial', 10), foreground='gray')
                title_label.pack()
                
            except Exception as e:
                print(f"Could not load theme logos: {e}")
                # Fallback to text-only title
                self.create_fallback_title()
        else:
            # Fallback to text-only title when PIL is not available
            self.create_fallback_title()
        
        # Create notebook for tabs (this should always be created)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=16, pady=16)  # Increased padding
        
        # Tab 1: Material Data Input
        self.material_frame = ttk.Frame(notebook)
        notebook.add(self.material_frame, text="📊 Material Data")  # Added icon
        self.create_material_tab()
        
        # Tab 2: MTPL and Test Selection
        self.mtpl_frame = ttk.Frame(notebook)
        notebook.add(self.mtpl_frame, text="🧪 MTPL & Test Selection")  # Added icon
        self.create_mtpl_tab()
        
        # Tab 3: Output Settings and Processing
        self.output_frame = ttk.Frame(notebook)
        notebook.add(self.output_frame, text="⚙️ Output & Processing")  # Added icon
        self.create_output_tab()
        
        # Apply enhancements
        self.enhance_visual_feedback()
        self.apply_enhanced_spacing()
        
        # Configure initial treeview colors
        self.configure_treeview_alternating_colors()
        
    def create_fallback_title(self):
        """Create a simple text-only title when images are not available"""
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        title_label = ttk.Label(title_frame, text="CTV List Data Processor", 
                              font=('Arial', 16, 'bold'))
        title_label.pack()
        
        # Create simple theme toggle buttons
        theme_frame = ttk.Frame(title_frame)
        theme_frame.pack(pady=5)
        
        ttk.Button(theme_frame, text="Light Mode", command=self.switch_to_light_mode).pack(side='left', padx=5)
        ttk.Button(theme_frame, text="Dark Mode", command=self.switch_to_dark_mode).pack(side='left', padx=5)
        
        # Add theme indicator
        self.theme_label = ttk.Label(title_frame, text="Light Mode", 
                                   font=('Arial', 10), foreground='gray')
        self.theme_label.pack()
        
    def create_material_tab(self):
        # Material Data Input Section
        ttk.Label(self.material_frame, text="Material Data Input", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Input fields frame
        input_frame = ttk.LabelFrame(self.material_frame, text="Enter Material Parameters")
        input_frame.pack(fill='x', padx=20, pady=10)
        
        # Entry variables
        self.lot_var = tk.StringVar(value="G5088651")
        self.wafer_var = tk.StringVar(value="533")
        self.program_var = tk.StringVar(value="DABHOPCA0H20C022528")
        self.prefetch_var = tk.StringVar(value="3")
        self.database_var = tk.StringVar(value="F24_PROD_XEUS")
        
        # Create input fields
        fields = [
            ("Lot:", self.lot_var),
            ("Wafer:", self.wafer_var),
            ("Program:", self.program_var),
            ("Prefetch:", self.prefetch_var),
            ("Database:", self.database_var)
        ]
        
        for i, (label, var) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky='w', padx=10, pady=5)
            ttk.Entry(input_frame, textvariable=var, width=40).grid(row=i, column=1, padx=10, pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(self.material_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Load from CSV/Excel", command=self.load_material_file).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Create DataFrame", command=self.create_material_dataframe).pack(side='left', padx=10)
        
        # Display frame for material data with proper layout management
        self.material_display_frame = ttk.LabelFrame(self.material_frame, text="Current Material Data")
        self.material_display_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Configure grid weights for proper resizing
        self.material_display_frame.grid_rowconfigure(0, weight=1)
        self.material_display_frame.grid_columnconfigure(0, weight=1)
        
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(self.material_display_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for displaying material data with proper grid placement
        self.material_tree = ttk.Treeview(tree_frame)
        self.material_tree.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbars with proper grid placement
        material_v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.material_tree.yview)
        material_v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.material_tree.configure(yscrollcommand=material_v_scrollbar.set)
        
        material_h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.material_tree.xview)
        material_h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.material_tree.configure(xscrollcommand=material_h_scrollbar.set)
        
    def create_mtpl_tab(self):
        ttk.Label(self.mtpl_frame, text="MTPL File and Test Selection", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # MTPL file loading
        mtpl_load_frame = ttk.LabelFrame(self.mtpl_frame, text="Load MTPL File")
        mtpl_load_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(mtpl_load_frame, text="MTPL File Path:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(mtpl_load_frame, textvariable=self.mtpl_file_path, width=60).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(mtpl_load_frame, text="Browse", command=self.browse_mtpl_file).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(mtpl_load_frame, text="Load MTPL", command=self.load_mtpl_file).grid(row=1, column=1, pady=10)
        
        # MTPL file info label
        self.mtpl_info_label = ttk.Label(mtpl_load_frame, text="Select an MTPL file for processing", 
                                        foreground='gray')
        self.mtpl_info_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # MTPL data display with proper layout management
        mtpl_display_frame = ttk.LabelFrame(self.mtpl_frame, text="MTPL Data")
        mtpl_display_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Configure grid weights for proper resizing
        mtpl_display_frame.grid_rowconfigure(1, weight=1)  # Make treeview area expandable
        mtpl_display_frame.grid_columnconfigure(0, weight=1)
        
        # Search/Filter frame
        search_frame = ttk.Frame(mtpl_display_frame)
        search_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        ttk.Label(search_frame, text="Search/Filter Tests:").pack(side='left', padx=(0, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side='left', padx=(0, 10))
        ttk.Button(search_frame, text="Clear Filter", command=self.clear_filter).pack(side='left', padx=(0, 10))
        
        # Filter status label
        self.filter_status_label = ttk.Label(search_frame, text="", foreground='blue')
        self.filter_status_label.pack(side='left', padx=(10, 0))
        
        # Create frame for treeview and scrollbars
        mtpl_tree_frame = ttk.Frame(mtpl_display_frame)
        mtpl_tree_frame.pack(fill='both', expand=True, padx=10, pady=(5, 10))
        mtpl_tree_frame.grid_rowconfigure(0, weight=1)
        mtpl_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for MTPL data with proper grid placement
        self.mtpl_tree = ttk.Treeview(mtpl_tree_frame)
        self.mtpl_tree.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbars with proper grid placement
        mtpl_v_scrollbar = ttk.Scrollbar(mtpl_tree_frame, orient='vertical', command=self.mtpl_tree.yview)
        mtpl_v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.mtpl_tree.configure(yscrollcommand=mtpl_v_scrollbar.set)
        
        mtpl_h_scrollbar = ttk.Scrollbar(mtpl_tree_frame, orient='horizontal', command=self.mtpl_tree.xview)
        mtpl_h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.mtpl_tree.configure(xscrollcommand=mtpl_h_scrollbar.set)
        
        # Test selection
        test_selection_frame = ttk.LabelFrame(self.mtpl_frame, text="Test Selection")
        test_selection_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(test_selection_frame, text="Select All Tests", command=self.select_all_tests).pack(side='left', padx=10, pady=10)
        ttk.Button(test_selection_frame, text="Clear Selection", command=self.clear_test_selection).pack(side='left', padx=10, pady=10)
        ttk.Label(test_selection_frame, text="Selected Tests:").pack(side='left', padx=10)
        self.selected_tests_label = ttk.Label(test_selection_frame, text="0")
        self.selected_tests_label.pack(side='left', padx=5)
        
    def create_output_tab(self):
        ttk.Label(self.output_frame, text="Output Settings and Processing", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Output folder selection
        output_folder_frame = ttk.LabelFrame(self.output_frame, text="Output Folder Selection")
        output_folder_frame.pack(fill='x', padx=20, pady=10)
        
        self.output_path_var = tk.StringVar()
        ttk.Label(output_folder_frame, text="Output Folder:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(output_folder_frame, textvariable=self.output_path_var, width=60).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(output_folder_frame, text="Browse", command=self.browse_output_folder).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(output_folder_frame, text="Use Default", command=self.use_default_output).grid(row=1, column=1, pady=10)
        
        # Processing options
        options_frame = ttk.LabelFrame(self.output_frame, text="Processing Options")
        options_frame.pack(fill='x', padx=20, pady=10)
        
        self.delete_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Delete intermediary files", variable=self.delete_files_var).pack(anchor='w', padx=10, pady=5)
        
        # Processing controls
        process_frame = ttk.Frame(self.output_frame)
        process_frame.pack(pady=20)
        
        ttk.Button(process_frame, text="Start Processing", command=self.start_processing, style='Accent.TButton').pack(side='left', padx=10)
        self.stop_button = ttk.Button(process_frame, text="Stop", command=self.stop_processing, state='disabled')
        self.stop_button.pack(side='left', padx=10)
        ttk.Button(process_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=10)
        
        # Progress and log
        progress_frame = ttk.LabelFrame(self.output_frame, text="Progress")
        progress_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=10)
        
        # Log text area
        self.log_text = tk.Text(progress_frame, height=10, width=80)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        log_scrollbar = ttk.Scrollbar(progress_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
    def load_csv_filtered(self, file_path):
        """Load CSV file with column filtering to remove unnamed and empty columns"""
        try:
            # Read the CSV first
            df = pd.read_csv(file_path)
            
            # Define required columns
            required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
            
            # Filter out unnamed columns and empty columns
            valid_columns = []
            for col in df.columns:
                # Skip unnamed columns and completely empty columns
                if (not str(col).startswith('Unnamed:') and 
                    not df[col].isna().all() and 
                    str(col).strip() != ''):
                    valid_columns.append(col)
            
            self.log_message(f"Original columns: {list(df.columns)}")
            self.log_message(f"Valid columns found: {valid_columns}")
            
            # Keep only valid columns that exist in the dataframe
            columns_to_keep = []
            for col in required_columns:
                if col in valid_columns:
                    columns_to_keep.append(col)
                else:
                    # Try case-insensitive matching
                    for valid_col in valid_columns:
                        if col.lower() == valid_col.lower():
                            columns_to_keep.append(valid_col)
                            break
            
            if not columns_to_keep:
                # If no required columns found, keep all valid columns
                columns_to_keep = valid_columns[:6]  # Limit to first 6 valid columns
                self.log_message("No required columns found, using first valid columns", "warning")
            
            self.log_message(f"Columns to keep: {columns_to_keep}")
            
            # Return filtered dataframe
            filtered_df = df[columns_to_keep].copy()
            
            # Rename columns to match expected names if needed
            column_mapping = {}
            for i, col in enumerate(filtered_df.columns):
                if i < len(required_columns):
                    expected_col = required_columns[i]
                    if col.lower() != expected_col.lower():
                        column_mapping[col] = expected_col
                        
            if column_mapping:
                filtered_df = filtered_df.rename(columns=column_mapping)
                self.log_message(f"Renamed columns: {column_mapping}")
            
            return filtered_df
            
        except Exception as e:
            self.log_message(f"Error filtering CSV: {str(e)}", "error")
            raise e
    
    def load_excel_filtered(self, file_path):
        """Load Excel file with column filtering to remove unnamed and empty columns"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Define required columns
            required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
            
            # Remove unnamed and empty columns
            valid_columns = []
            for col in df.columns:
                # Skip unnamed columns and completely empty columns
                if (not str(col).startswith('Unnamed:') and 
                    not df[col].isna().all() and 
                    str(col).strip() != ''):
                    valid_columns.append(col)
            
            self.log_message(f"Original columns: {list(df.columns)}")
            self.log_message(f"Valid columns found: {valid_columns}")
            
            # Keep intersection of required and valid columns
            columns_to_keep = []
            for col in required_columns:
                if col in valid_columns:
                    columns_to_keep.append(col)
                else:
                    # Try case-insensitive matching
                    for valid_col in valid_columns:
                        if col.lower() == valid_col.lower():
                            columns_to_keep.append(valid_col)
                            break
            
            if not columns_to_keep:
                # If no required columns found, keep all valid columns
                columns_to_keep = valid_columns[:6]  # Limit to first 6 valid columns
                self.log_message("No required columns found, using first valid columns", "warning")
            
            self.log_message(f"Columns to keep: {columns_to_keep}")
            
            # Return filtered dataframe
            filtered_df = df[columns_to_keep].copy()
            
            # Rename columns to match expected names if needed
            column_mapping = {}
            for i, col in enumerate(filtered_df.columns):
                if i < len(required_columns):
                    expected_col = required_columns[i]
                    if col.lower() != expected_col.lower():
                        column_mapping[col] = expected_col
                        
            if column_mapping:
                filtered_df = filtered_df.rename(columns=column_mapping)
                self.log_message(f"Renamed columns: {column_mapping}")
            
            return filtered_df
            
        except Exception as e:
            self.log_message(f"Error filtering Excel: {str(e)}", "error")
            raise e
    
    def validate_material_columns(self, df):
        """Validate that the material data contains expected columns"""
        required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            self.log_message(f"Warning: Missing columns: {missing_columns}", "warning")
            return False, missing_columns
        else:
            self.log_message("All required columns found", "success")
            return True, []

    def load_material_file(self):
        """Load material data from CSV or Excel file with enhanced column filtering"""
        file_path = filedialog.askopenfilename(
            title="Select Material Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.log_message(f"Loading material data from: {file_path}")
                
                # Load and filter the file based on type
                if file_path.endswith('.csv'):
                    self.material_df = self.load_csv_filtered(file_path)
                elif file_path.endswith(('.xlsx', '.xls')):
                    self.material_df = self.load_excel_filtered(file_path)
                else:
                    # Try CSV as fallback
                    self.material_df = self.load_csv_filtered(file_path)
                
                # Validate columns
                is_valid, missing_cols = self.validate_material_columns(self.material_df)
                
                if not is_valid:
                    self.log_message(f"File loaded but missing required columns: {missing_cols}", "warning")
                    # Show user a message about missing columns
                    missing_str = ", ".join(missing_cols)
                    response = messagebox.askyesno(
                        "Missing Columns", 
                        f"The file is missing these required columns: {missing_str}\n\n"
                        "Would you like to continue with the available columns?"
                    )
                    if not response:
                        return
                
                # Extract data into raw format for processing
                if not self.material_df.empty:
                    # Helper function to parse comma-separated values from loaded data
                    def parse_loaded_value(value):
                        if pd.isna(value) or not str(value).strip():
                            return []
                        return [item.strip() for item in str(value).split(',') if item.strip()]
                    
                    # Extract first row data and parse into lists
                    first_row = self.material_df.iloc[0]
                    
                    # Use default values for missing columns
                    default_values = {
                        'Lot': ['Not Null'],
                        'Wafer': ['Not Null'], 
                        'Program': ['DAB%', 'DAC%'],
                        'Prefetch': 3,
                        'Database': ['D1D_PROD_XEUS', 'F24_PROD_XEUS']
                    }
                    
                    self.material_data = {}
                    for col, default in default_values.items():
                        if col in first_row:
                            if col == 'Prefetch':
                                # Handle Prefetch as integer
                                value = first_row.get(col, default)
                                if str(value).strip().isdigit():
                                    self.material_data[col] = int(value)
                                else:
                                    self.material_data[col] = default
                            else:
                                # Handle other columns as lists
                                parsed_value = parse_loaded_value(first_row.get(col, ''))
                                self.material_data[col] = parsed_value if parsed_value else default
                        else:
                            # Use default if column not found
                            self.material_data[col] = default
                    
                    self.log_message(f"Parsed material data: {self.material_data}")
                
                self.update_material_display()
                self.log_message(f"Material data loaded successfully from: {os.path.basename(file_path)}", "success")
                
                # Show column preview to user
                self.show_column_preview()
                
                # Update entry fields with first row data if available
                if not self.material_df.empty:
                    self.update_entry_fields_from_dataframe()
                        
            except Exception as e:
                error_msg = f"Failed to load file: {str(e)}"
                self.log_message(error_msg, "error")
                messagebox.showerror("Error", error_msg)
    
    def show_column_preview(self):
        """Show user a preview of the columns that were imported"""
        if hasattr(self, 'material_df') and self.material_df is not None:
            columns = list(self.material_df.columns)
            rows = len(self.material_df)
            
            preview_msg = f"Successfully imported {rows} rows with columns:\n\n"
            for i, col in enumerate(columns, 1):
                preview_msg += f"{i}. {col}\n"
            
            # Show sample data if available
            if not self.material_df.empty:
                preview_msg += f"\nSample data (first row):\n"
                first_row = self.material_df.iloc[0]
                for col in columns:
                    value = str(first_row[col])[:50] + "..." if len(str(first_row[col])) > 50 else str(first_row[col])
                    preview_msg += f"• {col}: {value}\n"
            
            messagebox.showinfo("Import Preview", preview_msg)
    
    def update_entry_fields_from_dataframe(self):
        """Update the entry fields with data from the loaded dataframe"""
        if self.material_df is not None and not self.material_df.empty:
            first_row = self.material_df.iloc[0]
            
            # Update entry fields only if the column exists
            if 'Lot' in self.material_df.columns:
                self.lot_var.set(str(first_row['Lot']))
            if 'Wafer' in self.material_df.columns:
                self.wafer_var.set(str(first_row['Wafer']))
            if 'Program' in self.material_df.columns:
                self.program_var.set(str(first_row['Program']))
            if 'Prefetch' in self.material_df.columns:
                self.prefetch_var.set(str(first_row['Prefetch']))
            if 'Database' in self.material_df.columns:
                self.database_var.set(str(first_row['Database']))
                
    def create_material_dataframe(self):
        """Create material data from manual input"""
        try:
            # Default values
            default_values = {
                'Lot': ['Not Null'],
                'Wafer': ['Not Null'], 
                'Program': ['DAB%', 'DAC%'],
                'Prefetch': [3],
                'Database': ['D1D_PROD_XEUS', 'F24_PROD_XEUS']
            }
            
            # Helper function to parse comma-separated values
            def parse_input(value, default_list):
                """Parse comma-separated input into a list, or return default"""
                if not value.strip():
                    return default_list
                # Split by comma and strip whitespace from each item
                return [item.strip() for item in value.split(',') if item.strip()]
            
            # Get input values and parse them into lists
            lot_input = self.lot_var.get().strip()
            wafer_input = self.wafer_var.get().strip()
            program_input = self.program_var.get().strip()
            prefetch_input = self.prefetch_var.get().strip()
            database_input = self.database_var.get().strip()
            
            # Parse inputs into lists
            lot_list = parse_input(lot_input, default_values['Lot'])
            wafer_list = parse_input(wafer_input, default_values['Wafer'])
            program_list = parse_input(program_input, default_values['Program'])
            database_list = parse_input(database_input, default_values['Database'])
            
            # Handle prefetch specially as it should be an integer
            if prefetch_input.strip() and prefetch_input.strip().isdigit():
                prefetch_value = int(prefetch_input.strip())
            else:
                prefetch_value = default_values['Prefetch'][0]
            
            # Store the raw data dictionary (no DataFrame needed)
            self.material_data = {
                'Lot': lot_list,
                'Wafer': wafer_list,
                'Program': program_list,
                'Prefetch': prefetch_value,
                'Database': database_list
            }
            
            # For backward compatibility, create a simple DataFrame for display
            # Convert lists to comma-separated strings for display
            display_data = {
                'Lot': [', '.join(lot_list)],
                'Wafer': [', '.join(wafer_list)],
                'Program': [', '.join(program_list)],
                'Prefetch': [str(prefetch_value)],
                'Database': [', '.join(database_list)]
            }
            
            self.material_df = pd.DataFrame(display_data)
            self.update_material_display()
            self.log_message("Material data created from manual input", "success")
            self.log_message(f"Parsed data - Lot: {lot_list}, Wafer: {wafer_list}, Program: {program_list}, Prefetch: {prefetch_value}, Database: {database_list}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create material data: {str(e)}")
            
    def update_material_display(self):
        """Update the material data display with enhanced window resize handling"""
        try:
            # Ensure the treeview widget exists and is valid
            if not hasattr(self, 'material_tree') or not self.material_tree.winfo_exists():
                print("Debug - Material tree widget does not exist, skipping update")
                return
            
            # Clear existing data
            for item in self.material_tree.get_children():
                self.material_tree.delete(item)
                
            print(f"Debug - Material data available: {self.material_df is not None}")
            
            if self.material_df is not None and not self.material_df.empty:
                # Configure columns
                columns = list(self.material_df.columns)
                self.material_tree['columns'] = columns
                self.material_tree['show'] = 'headings'
                
                print(f"Debug - Material columns: {columns}")
                print(f"Debug - Material data shape: {self.material_df.shape}")
                
                # Configure column headings with improved settings for resize
                for col in columns:
                    self.material_tree.heading(col, text=col, anchor='center')
                    self.material_tree.column(col, width=150, minwidth=100, anchor='center', stretch=True)
                
                # Insert material data with alternating row colors and debugging
                for index, row in self.material_df.iterrows():
                    try:
                        values = list(row)
                        
                        # Determine row tag for alternating colors
                        row_tag = 'evenrow' if index % 2 == 0 else 'oddrow'
                        
                        # Insert data with proper tagging
                        item_id = self.material_tree.insert('', 'end', values=values, tags=(row_tag,))
                        
                        print(f"Debug - Inserted material row {index}: {values} with tag: {row_tag}")
                        
                    except Exception as row_error:
                        print(f"Debug - Error inserting material row {index}: {row_error}")
                        continue
                
                # Ensure proper tag configuration after insertion
                self.configure_treeview_alternating_colors()
                
                # Force widget update to reflect changes
                self.material_tree.update_idletasks()
                
                print(f"Debug - Material display updated with {len(self.material_df)} rows")
                
            else:
                print("Debug - No material data to display")
                # Show empty state message
                self.material_tree['columns'] = ['Message']
                self.material_tree['show'] = 'headings'
                self.material_tree.heading('Message', text='Material Data Status')
                self.material_tree.column('Message', width=400, anchor='center')
                self.material_tree.insert('', 'end', values=('No material data loaded. Please create or load material data.',))
                
        except Exception as e:
            print(f"Debug - Error in update_material_display: {e}")
            # Try to show error in the treeview if possible
            try:
                if hasattr(self, 'material_tree') and self.material_tree.winfo_exists():
                    # Clear and show error
                    for item in self.material_tree.get_children():
                        self.material_tree.delete(item)
                    self.material_tree['columns'] = ['Error']
                    self.material_tree['show'] = 'headings'
                    self.material_tree.heading('Error', text='Error')
                    self.material_tree.column('Error', width=400, anchor='center')
                    self.material_tree.insert('', 'end', values=(f'Error displaying material data: {str(e)}',))
            except:
                pass
                
    def browse_mtpl_file(self):
        """Browse for MTPL file"""
        file_path = filedialog.askopenfilename(
            title="Select MTPL File",
            filetypes=[("MTPL files", "*.mtpl"), ("All files", "*.*")]
        )
        
        if file_path:
            self.mtpl_file_path.set(file_path)
            self.update_mtpl_info(file_path)
            
    def update_status_indicator(self, label_widget, message, status_type="info"):
        """Update status indicator with color-coded messages and smooth transitions"""
        status_colors = {
            "success": "#28a745" if not self.is_dark_mode else "#6bcf7f",    # Bright green for dark mode
            "warning": "#ffc107" if not self.is_dark_mode else "#ffd93d",    # Bright yellow for dark mode  
            "error": "#dc3545" if not self.is_dark_mode else "#ff6b6b",      # Bright red for dark mode
            "info": "#17a2b8" if not self.is_dark_mode else "#5a9fd4",       # Light blue for dark mode
            "muted": "#6c757d" if not self.is_dark_mode else "#b8bac8"       # Muted text for dark mode
        }
        
        color = status_colors.get(status_type, status_colors["info"])
        
        try:
            label_widget.configure(text=message, foreground=color)
            # Add a subtle animation effect by briefly changing the font weight
            self.root.after(100, lambda: label_widget.configure(font=('Segoe UI', 9, 'bold')))
            self.root.after(1000, lambda: label_widget.configure(font=('Segoe UI', 9)))
        except:
            pass
    
    def update_mtpl_info(self, filename):
        """Update MTPL file info display with enhanced status indicators"""
        try:
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                size_mb = file_size / (1024 * 1024)
                if size_mb >= 1:
                    size_text = f"{size_mb:.1f} MB"
                else:
                    size_text = f"{file_size / 1024:.1f} KB"
                
                message = f"✅ MTPL file loaded: {os.path.basename(filename)} ({size_text})"
                self.update_status_indicator(self.mtpl_info_label, message, "success")
            else:
                self.update_status_indicator(self.mtpl_info_label, "❌ MTPL file not found", "error")
        except Exception as e:
            self.update_status_indicator(self.mtpl_info_label, f"⚠️ Error reading MTPL file: {str(e)}", "error")
    
    def load_mtpl_file(self):
        """Load and process MTPL file"""
        mtpl_path = self.mtpl_file_path.get()
        if not mtpl_path:
            messagebox.showwarning("Warning", "Please select an MTPL file first")
            return
            
        try:
            self.log_message("Processing MTPL file...")
            self.mtpl_csv_path = mt.mtpl_to_csv(fi.process_file_input(mtpl_path))
            self.mtpl_df = pd.read_csv(self.mtpl_csv_path)
            
            # Debug: Print MTPL dataframe info
            print(f"Debug - MTPL columns: {self.mtpl_df.columns.tolist()}")
            print(f"Debug - MTPL shape: {self.mtpl_df.shape}")
            if not self.mtpl_df.empty:
                print(f"Debug - First few rows of MTPL:")
                print(self.mtpl_df.head())
            
            self.update_mtpl_display()
            self.log_message(f"MTPL file processed: {self.mtpl_csv_path}", "success")
            
            # Set default output folder
            self.set_default_output_folder()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process MTPL file: {str(e)}")
            self.log_message(f"Error processing MTPL: {str(e)}", "error")
            
    def update_mtpl_display(self):
        """Update the MTPL data display"""
        # Clear existing data
        for item in self.mtpl_tree.get_children():
            self.mtpl_tree.delete(item)
            
        if self.mtpl_df is not None:
            # Add checkbox column to the original columns
            columns = ['Selected'] + list(self.mtpl_df.columns)
            self.mtpl_tree['columns'] = columns
            self.mtpl_tree['show'] = 'headings'
            
            print(f"Debug - Treeview columns: {columns}")
            
            # Configure column headings
            self.mtpl_tree.heading('Selected', text='✓', anchor='center')
            self.mtpl_tree.column('Selected', width=50, anchor='center')
            
            for col in self.mtpl_df.columns:
                self.mtpl_tree.heading(col, text=col)
                self.mtpl_tree.column(col, width=150, anchor='center')
                
            # Store all items for filtering
            self.all_mtpl_items = []
            for index, row in self.mtpl_df.iterrows():
                # Start with unchecked (empty checkbox)
                values = ['☐'] + list(row)
                item_data = {
                    'values': values,
                    'tags': ('unchecked',),
                    'original_index': index
                }
                self.all_mtpl_items.append(item_data)
                print(f"Debug - Stored item {index}: {values}")
                
            print(f"Debug - Total items stored: {len(self.all_mtpl_items)}")
                
            # Display all items initially
            self.display_filtered_items(self.all_mtpl_items)
            
            # Bind selection events
            self.mtpl_tree.bind('<Double-1>', self.toggle_test_selection)
            self.mtpl_tree.bind('<Button-1>', self.on_treeview_click)
            
            # Clear search
            self.search_var.set("")
            self.update_filter_status(len(self.all_mtpl_items), len(self.all_mtpl_items))
            
            # Enhance visual feedback
            self.enhance_visual_feedback()
            
    def display_filtered_items(self, items):
        """Display the filtered items in the treeview with enhanced resize handling"""
        try:
            # Ensure the treeview widget exists and is valid
            if not hasattr(self, 'mtpl_tree') or not self.mtpl_tree.winfo_exists():
                print("Debug - MTPL tree widget does not exist, skipping display")
                return
                
            # Clear current display
            for item in self.mtpl_tree.get_children():
                self.mtpl_tree.delete(item)
                
            # Insert filtered items with proper tag combinations
            for i, item_data in enumerate(items):
                try:
                    row_tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    
                    # Preserve checked state and combine with row coloring
                    existing_tags = item_data['tags']
                    if 'checked' in existing_tags:
                        combined_tags = ('checked', row_tag)
                    else:
                        combined_tags = ('unchecked', row_tag)
                        
                    self.mtpl_tree.insert('', 'end', 
                                        values=item_data['values'], 
                                        tags=combined_tags)
                except Exception as item_error:
                    print(f"Debug - Error inserting MTPL item {i}: {item_error}")
                    continue
            
            # Configure alternating colors
            self.configure_treeview_alternating_colors()
            
            # Force widget update to reflect changes
            self.mtpl_tree.update_idletasks()
            
        except Exception as e:
            print(f"Debug - Error in display_filtered_items: {e}")
                                
    def on_search_change(self, *args):
        """Handle search text changes"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            # Show all items if search is empty
            filtered_items = self.all_mtpl_items
        else:
            # Filter items based on search text
            filtered_items = []
            for item_data in self.all_mtpl_items:
                # Search in all columns (skip the checkbox column)
                item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                if search_text in item_text:
                    filtered_items.append(item_data)
                    
        self.display_filtered_items(filtered_items)
        self.update_filter_status(len(filtered_items), len(self.all_mtpl_items))
        self.update_selected_tests_count()
        
    def clear_filter(self):
        """Clear the search filter"""
        self.search_var.set("")
        
    def update_filter_status(self, shown_count, total_count):
        """Update the filter status label"""
        if shown_count == total_count:
            self.filter_status_label.config(text=f"Showing all {total_count} tests")
        else:
            self.filter_status_label.config(text=f"Showing {shown_count} of {total_count} tests")
            
    def on_treeview_click(self, event):
        """Handle single click on treeview to toggle selection when clicking checkbox column"""
        item = self.mtpl_tree.identify('item', event.x, event.y)
        column = self.mtpl_tree.identify('column', event.x, event.y)
        
        # If clicked on the checkbox column (first column)
        if item and column == '#1':
            self.toggle_test_selection_for_item(item)
            
    def toggle_test_selection(self, event):
        """Toggle test selection when double-clicked"""
        if self.mtpl_tree.selection():
            item = self.mtpl_tree.selection()[0]
            self.toggle_test_selection_for_item(item)
            
    def toggle_test_selection_for_item(self, item):
        """Toggle selection for a specific item"""
        current_tags = self.mtpl_tree.item(item, 'tags')
        values = list(self.mtpl_tree.item(item, 'values'))
        
        print(f"Debug - Toggling item with current tags: {current_tags}")
        print(f"Debug - Current values: {values}")
        
        # Determine current row type (odd/even) for alternating colors
        item_index = self.mtpl_tree.index(item)
        row_tag = 'evenrow' if item_index % 2 == 0 else 'oddrow'
        
        if 'checked' in current_tags:
            # Uncheck: change to empty checkbox
            values[0] = '☐'
            new_tags = ('unchecked', row_tag)
            self.mtpl_tree.item(item, values=values, tags=new_tags)
            print("Debug - Unchecked item")
        else:
            # Check: change to filled checkbox
            values[0] = '☑'
            new_tags = ('checked', row_tag)
            self.mtpl_tree.item(item, values=values, tags=new_tags)
            print("Debug - Checked item")
            
        # Update the stored item data to maintain state during filtering
        self.update_stored_item_state(values, new_tags)
        self.update_selected_tests_count()
        
    def update_stored_item_state(self, updated_values, new_tags):
        """Update the stored item state for filtering consistency"""
        # Find the matching item in stored data by comparing the non-checkbox values
        test_identifier = updated_values[1:]  # Skip checkbox column
        
        print(f"Debug - Looking for item with identifier: {test_identifier}")
        
        for i, item_data in enumerate(self.all_mtpl_items):
            stored_values = item_data['values'][1:]  # Skip checkbox column
            
            # Compare with type conversion for robust matching
            if len(stored_values) == len(test_identifier):
                match = True
                for j, (stored_val, search_val) in enumerate(zip(stored_values, test_identifier)):
                    # Convert both to strings for comparison to handle type differences
                    if str(stored_val) != str(search_val):
                        match = False
                        break
                
                if match:
                    print(f"Debug - Found matching item at index {i}, updating from {item_data['tags']} to {new_tags}")
                    item_data['values'] = updated_values
                    item_data['tags'] = new_tags
                    return
        
        print("Debug - No matching item found!")
        
    def select_all_tests(self):
        """Select all tests in the MTPL (including filtered ones)"""
        print(f"Debug - select_all_tests called, total items: {len(self.all_mtpl_items)}")
        
        # Update all stored items
        for item_data in self.all_mtpl_items:
            values = list(item_data['values'])
            values[0] = '☑'  # Set checkbox to checked
            item_data['values'] = values
            item_data['tags'] = ('checked',)
            print(f"Debug - Updated item to checked: {values}")
            
        # Refresh the current display
        search_text = self.search_var.get().lower()
        if not search_text:
            filtered_items = self.all_mtpl_items
        else:
            filtered_items = []
            for item_data in self.all_mtpl_items:
                item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                if search_text in item_text:
                    filtered_items.append(item_data)
                    
        self.display_filtered_items(filtered_items)
        self.update_selected_tests_count()
        
    def clear_test_selection(self):
        """Clear all test selections (including filtered ones)"""
        # Update all stored items
        for item_data in self.all_mtpl_items:
            values = list(item_data['values'])
            values[0] = '☐'  # Set checkbox to unchecked
            item_data['values'] = values
            item_data['tags'] = ('unchecked',)
            
        # Refresh the current display
        search_text = self.search_var.get().lower()
        if not search_text:
            filtered_items = self.all_mtpl_items
        else:
            filtered_items = []
            for item_data in self.all_mtpl_items:
                item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                if search_text in item_text:
                    filtered_items.append(item_data)
                    
        self.display_filtered_items(filtered_items)
        self.update_selected_tests_count()
        
    def update_selected_tests_count(self):
        """Update the count of selected tests"""
        count = 0
        # Count from stored data, not just visible items
        for item_data in self.all_mtpl_items:
            if 'checked' in item_data['tags']:
                count += 1
                print(f"Debug - Checked item: {item_data['values']}")
        print(f"Debug - Total checked count: {count}")
        self.selected_tests_label.config(text=str(count))
        
    def get_selected_tests(self):
        """Get list of selected test names"""
        selected_tests = []
        # Get from stored data, not just visible items
        for item_data in self.all_mtpl_items:
            if 'checked' in item_data['tags']:
                values = item_data['values']
                # Debug: Print the values to understand the structure
                print(f"Debug - Selected item values: {values}")
                # The first column is checkbox, so test name should be in index 2 (third column)
                # Based on the processing logic where row[2] is the test name
                if len(values) > 2:  
                    test_name = values[2]  # This should be the test name column
                    selected_tests.append(test_name)
                    print(f"Debug - Added test: {test_name}")
        print(f"Debug - Total selected tests: {selected_tests}")
        return selected_tests
        
    def browse_output_folder(self):
        """Browse for output folder"""
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_path_var.set(folder_path)
            
    def use_default_output(self):
        """Use default output folder based on MTPL path"""
        if self.mtpl_csv_path:
            self.set_default_output_folder()
        else:
            messagebox.showwarning("Warning", "Please load MTPL file first")
            
    def set_default_output_folder(self):
        """Set default output folder"""
        if self.mtpl_csv_path:
            # Normalize the path and use proper path operations
            csv_path = os.path.normpath(self.mtpl_csv_path)
            if 'Modules' in csv_path:
                base_path = csv_path.split('Modules')[0].rstrip(os.sep)
                default_path = os.path.join(base_path, 'dataOut')
            else:
                default_path = os.path.join(os.path.dirname(csv_path), 'dataOut')
            self.output_path_var.set(os.path.normpath(default_path))
            
    def stop_processing(self):
        """Stop the processing"""
        self.processing = False
        self.stop_button.configure(state='disabled')
        self.log_message("Processing stopped by user")
        
    def start_processing(self):
        """Start the data processing"""
        # Validate inputs
        if not hasattr(self, 'material_data') or not self.material_data:
            messagebox.showerror("Error", "Please create or load material data first")
            return
            
        if self.mtpl_df is None:
            messagebox.showerror("Error", "Please load MTPL file first")
            return
            
        selected_tests = self.get_selected_tests()
        print(f"Debug - Selected tests from start_processing: {selected_tests}")
        self.log_message(f"Selected tests: {selected_tests}")
        
        if not selected_tests:
            messagebox.showerror("Error", "Please select at least one test")
            return
            
        output_folder = self.output_path_var.get()
        if output_folder and not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder, exist_ok=True)
                self.log_message(f"Created output directory: {output_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
                return
        
        # Set processing flag and update UI
        self.processing = True
        self.stop_button.configure(state='normal')
        
        # Start processing in a separate thread
        import threading
        thread = threading.Thread(target=self.process_data, args=(selected_tests, output_folder), daemon=True)
        thread.start()
        
    def update_progress(self, current_test, total_tests, step_description=""):
        """Update progress bar with detailed information and smooth animation"""
        target_progress = (current_test / total_tests) * 100
        current_progress = self.progress_var.get()
        
        # Smooth animation - gradually increase progress
        def animate_progress():
            nonlocal current_progress
            if current_progress < target_progress:
                current_progress = min(current_progress + 2, target_progress)
                self.progress_var.set(current_progress)
                self.root.after(50, animate_progress)  # 50ms intervals for smooth animation
            else:
                self.progress_var.set(target_progress)
        
        # Start animation
        animate_progress()
        
        # Calculate proper test number display (handle fractional progress)
        if isinstance(current_test, float):
            # For fractional progress (e.g., 0.2), show the next whole test number
            display_test_num = int(current_test) + 1
            # Calculate sub-progress percentage within the current test
            sub_progress = (current_test - int(current_test)) * 100
            sub_progress_text = f" ({sub_progress:.0f}% of test)" if sub_progress > 0 else ""
        else:
            display_test_num = current_test
            sub_progress_text = ""
        
        # Enhanced status message with emojis and formatting
        status_emoji = "🔄" if current_test < total_tests else "✅"
        
        # Format progress message with proper test number and percentage
        formatted_message = f"{status_emoji} Progress: {display_test_num}/{total_tests} tests ({target_progress:.1f}%){sub_progress_text}"
        
        if step_description:
            formatted_message += f" - {step_description}"
            
        self.log_message(formatted_message)
        self.root.update_idletasks()
        
    def process_data(self, test_list, place_in):
        """Process the data (adapted from master.py with enhanced SmartCTV and CTV processing)"""
        try:
            self.log_message("Starting data processing...")
            self.progress_var.set(0)
            
            # Default values
            default_values = {
                'Lot': ['Not Null'],
                'Wafer': ['Not Null'],
                'Program': ['DAB%', 'DAC%'],
                'Prefetch': 3,
                'Database': ['D1D_PROD_XEUS', 'F24_PROD_XEUS']
            }
            
            # Use the raw material data if available, otherwise use defaults
            if hasattr(self, 'material_data') and self.material_data:
                lot_list = self.material_data.get('Lot', default_values['Lot'])
                wafer_list = self.material_data.get('Wafer', default_values['Wafer'])
                program_list = self.material_data.get('Program', default_values['Program'])
                prefetch = self.material_data.get('Prefetch', default_values['Prefetch'])
                databases = self.material_data.get('Database', default_values['Database'])
            else:
                # Fallback to defaults if no material data
                lot_list = default_values['Lot']
                wafer_list = default_values['Wafer']
                program_list = default_values['Program']
                prefetch = default_values['Prefetch']
                databases = default_values['Database']
            
            # Convert wafer list items to integers where possible
            processed_wafer_list = []
            for w in wafer_list:
                try:
                    if str(w).strip() and str(w).strip().isdigit():
                        processed_wafer_list.append(int(w))
                    else:
                        processed_wafer_list.append(str(w))  # Keep as string if not numeric
                except:
                    processed_wafer_list.append(str(w))
            wafer_list = processed_wafer_list
            
            # Log the extracted values for debugging
            self.log_message(f"Using material data - Lot: {lot_list}, Wafer: {wafer_list}, Program: {program_list}, Prefetch: {prefetch}, Database: {databases}")
            
            # Use the single loaded MTPL file
            mtpl_path = self.mtpl_file_path.get()
            
            # Normalize path separators for Windows (from master.py)
            mtpl_path = os.path.normpath(mtpl_path)
            
            # Get base directory from the loaded MTPL path (enhanced from master.py)
            if 'Modules' in mtpl_path:
                base_dir = mtpl_path.split('Modules')[0].rstrip(os.sep)
                # Ensure we have a valid directory path
                if not base_dir or base_dir == '.' or len(base_dir) < 3:
                    # Fallback to parent directory of MTPL file
                    base_dir = os.path.dirname(os.path.dirname(mtpl_path))
            else:
                base_dir = os.path.dirname(mtpl_path)
            
            # Normalize the base directory path
            base_dir = os.path.normpath(base_dir)
            self.log_message(f"Base directory: {base_dir}")
            
            # Validate base directory exists
            if not os.path.exists(base_dir):
                raise ValueError(f"Base directory does not exist: {base_dir}")
            if not os.path.isdir(base_dir):
                raise ValueError(f"Base path is not a directory: {base_dir}")
            
            total_iterations = len(test_list)  # Progress based on tests, not programs × tests
            current_iteration = 0
            
            # Process for each program with the single loaded MTPL (enhanced logic from master.py)
            for program in program_list:
                if not self.processing:
                    break
                    
                self.log_message(f"Processing program: {program}")
                
                # Create output folder if specified (from master.py)
                if place_in:
                    place_in = os.path.normpath(place_in)
                    os.makedirs(place_in, exist_ok=True)
                    place_in = place_in + os.sep
                else:
                    place_in = os.path.normpath(os.getcwd() + os.sep + f'{program}_script_output')
                    os.makedirs(place_in, exist_ok=True)
                    place_in = place_in + os.sep
                
                self.log_message(f"Output directory: {place_in}")
                intermediary_file_list = []
                
                # Reset iteration counter for each program
                current_iteration = 0
                
                for test in test_list:
                    if not self.processing:
                        break
                        
                    if str(test).lower() == 'nan':
                        current_iteration += 1
                        self.update_progress(current_iteration, total_iterations, f"Skipped invalid test entry")
                        continue
                        
                    self.log_message(f"Processing test: {test} ({current_iteration + 1}/{total_iterations})")
                    self.update_progress(current_iteration, total_iterations, f"Starting test: {test}")
                    
                    # Find matching row in MTPL dataframe (enhanced from master.py)
                    matching_rows = self.mtpl_df[self.mtpl_df.iloc[:, 1] == test]  # Assuming test name is in column 1
                    
                    if matching_rows.empty:
                        self.log_message(f"No matching MTPL entry found for test: {test}")
                        current_iteration += 1
                        self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (no MTPL entry)")
                        continue
                        
                    row = matching_rows.iloc[0]
                    test_type = row.iloc[0]  # Assuming test type is in column 0
                    mode = row.iloc[4]  # Assuming mode is in column 4
                    mode=str(mode)
                    config_path = fi.process_file_input(row.iloc[2][row.iloc[2].find('Modules'):].strip('\"'))  # Assuming config path is in column 2
                    module_name = fi.get_module_name(config_path).strip('\\')
                    test_file = os.path.join(base_dir, config_path)
                    
                    # Check if config file exists (from master.py)
                    if not os.path.exists(test_file):
                        self.log_message(f"Config file not found: {test_file}")
                        current_iteration += 1
                        self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (config file not found)")
                        continue
                        
                    self.log_message(f"Found config file: {test_file}")
                    self.update_progress(current_iteration + 0.2, total_iterations, f"Processing config for: {test}")
                    
                    # Enhanced processing based on test type (from master.py)
                    indexed_file = ''
                    csv_identifier = ''
                    
                    try:
                        if "ctvdecoder" in test_type.lower():  # simple CTV indexing
                            self.log_message(f"Processing CtvDecoderSpm for test: {test}")
                            self.update_progress(current_iteration + 0.4, total_iterations, f"Indexing CTV for: {test}")
                            indexed_file, csv_identifier,need_suffix = ind.index_CTV(test_file, test, module_name, place_in)
                            intermediary_file_list.append(indexed_file)
                            self.log_message(f"Performing data request for test: {test}")
                            datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,need_suffix,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                            intermediary_file_list.append(datainput_file)

                        elif  "smartctv" in test_type.lower(): # SMART CTV loop/check logic and indexing
                            if SMART_CTV_AVAILABLE and sm is not None and "CtvTag" in mode:
                                mode = mode.strip('\"\'')  # Assuming mode is in column 4
                                config_number = ''
                                self.log_message(f"Processing CTV Tag SmartCtvDc for test: {test}")
                                self.log_message(f"Config number: {config_number}")
                                self.update_progress(current_iteration + 0.3, total_iterations, f"Processing SmartCTV for: {test}")
                                try:
                                    ctv_files,ITUFF_suffixes = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                                    for ctv_file,ITUFF_suffix in zip(ctv_files,ITUFF_suffixes):
                                        intermediary_file_list.append(ctv_file)
                                        test = test + ITUFF_suffix
                                        self.update_progress(current_iteration + 0.6, total_iterations, f"Indexing SmartCTV for: {test}")
                                        indexed_file, csv_identifier,need_suffix  = ind.index_CTV(ctv_file, test, module_name, place_in,mode)
                                        intermediary_file_list.append(indexed_file)
                                        self.log_message(f"Performing data request for test: {test}")
                                        datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,need_suffix,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                                        intermediary_file_list.append(datainput_file)
                                        test = test.replace(ITUFF_suffix,'')
                                except Exception as e:
                                    self.log_message(f"❌ Error in SmartCTV processing for test {test}: {str(e)}")
                                    current_iteration += 1
                                    self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (SmartCTV error)")
                                    continue
                            elif SMART_CTV_AVAILABLE and sm is not None:
                                try:
                                    config_number = str(int(row[3]))                    
                                    ctv_file = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                                    intermediary_file_list.append(ctv_file)
                                    indexed_file,csv_identifier,need_suffix = ind.index_CTV(ctv_file, test,module_name,place_in)
                                    self.log_message(f"Processing SmartCtvDc for test: {test}")
                                    current_iteration += 1
                                    intermediary_file_list.append(indexed_file)
                                except Exception as e:
                                    self.log_message(f"❌ Error in SmartCTV processing for test {test}: {str(e)}")
                                    current_iteration += 1
                                    self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (SmartCTV error)")
                                    continue
                            else:
                                self.log_message(f"❌ Error processing test {test}: SmartCTV functionality not available (smart_json_parser module not found)")
                                self.log_message("ℹ️ Skipping SmartCTV processing for this test")
                                current_iteration += 1
                                self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (SmartCTV unavailable)")
                                continue
                        else:
                            self.log_message(f"Unknown test type: {test_type}")
                            current_iteration += 1
                            self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (unknown type)")
                            continue
                            
                        if indexed_file:
                         
                            self.log_message(f"Completed processing for test: {test}")
                        
                    except Exception as test_error:
                        self.log_message(f"Error processing test {test}: {str(test_error)}")
                        
                    # Update progress after each test
                    current_iteration += 1
                    self.update_progress(current_iteration, total_iterations, f"Completed test: {test}")
                    
                    # Add a small delay to make progress visible
                    import time
                    time.sleep(0.2)  # Slightly longer delay for visibility
                
                # Clean up intermediary files if requested (from master.py)
                if self.delete_files_var.get():
                    self.log_message("Cleaning up intermediary files...")
                    for intermediary in intermediary_file_list:
                        try:
                            if os.path.exists(intermediary):
                                os.remove(intermediary)
                                self.log_message(f"Deleted: {os.path.basename(intermediary)}")
                        except Exception as e:
                            self.log_message(f"Could not delete {intermediary}: {str(e)}")
            
            if self.processing:
                self.progress_var.set(100)
                self.log_message("Processing completed successfully!")
                messagebox.showinfo("Success", "Data processing completed successfully!")
            
        except Exception as e:
            self.log_message(f"Error during processing: {str(e)}")
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            
        finally:
            self.processing = False
            self.root.after(0, lambda: self.stop_button.configure(state='disabled'))
            
    def update_treeview_row_colors(self, treeview):
        """Update the row colors of the treeview to alternate between two colors"""
        try:
            for index, item in enumerate(treeview.get_children()):
                if index % 2 == 0:
                    treeview.item(item, tags=('evenrow',))
                else:
                    treeview.item(item, tags=('oddrow',))
        except Exception as e:
            print(f"Could not update treeview row colors: {e}")
    
    def log_message(self, message, level="info"):
        """Add message to log with timestamp, formatting, and color coding"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Add level-specific formatting
        level_emojis = {
            "info": "ℹ️",
            "success": "✅", 
            "warning": "⚠️",
            "error": "❌",
            "progress": "🔄",
            "debug": "🐛"
        }
        
        emoji = level_emojis.get(level, "ℹ️")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"
        
        try:
            # Insert message with color coding based on level
            start_index = self.log_text.index(tk.END + "-1c")
            self.log_text.insert(tk.END, formatted_message)
            
            # Configure text tags for different log levels
            if not hasattr(self, '_tags_configured'):
                self.configure_log_tags()
                self._tags_configured = True
            
            # Apply tag based on level
            end_index = self.log_text.index(tk.END + "-1c")
            if level in ["error"]:
                self.log_text.tag_add("error", start_index, end_index)
            elif level in ["warning"]:
                self.log_text.tag_add("warning", start_index, end_index)
            elif level in ["success"]:
                self.log_text.tag_add("success", start_index, end_index)
            elif level in ["progress"]:
                self.log_text.tag_add("progress", start_index, end_index)
                
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        except:
            # Fallback to simple insertion
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
    
    def configure_log_tags(self):
        """Configure text tags for log message coloring with proper contrast"""
        try:
            if self.is_dark_mode:
                # Purple/Navy dark mode colors with high contrast
                self.log_text.tag_configure("error", foreground="#ff6b6b")      # Bright red for errors
                self.log_text.tag_configure("warning", foreground="#ffd93d")    # Bright yellow for warnings  
                self.log_text.tag_configure("success", foreground="#6bcf7f")    # Bright green for success
                self.log_text.tag_configure("progress", foreground="#5a9fd4")   # Light blue for progress
            else:
                # Light mode colors
                self.log_text.tag_configure("error", foreground="#dc3545")
                self.log_text.tag_configure("warning", foreground="#ffc107")
                self.log_text.tag_configure("success", foreground="#28a745")
                self.log_text.tag_configure("progress", foreground="#17a2b8")
        except:
            pass
            pass
        
    def clear_all(self):
        """Clear all data and reset the application"""
        self.material_df = None
        self.mtpl_df = None
        self.mtpl_csv_path = ""
        self.test_list = []
        self.output_folder = ""
        self.all_mtpl_items = []
        
        # Clear displays
        for item in self.material_tree.get_children():
            self.material_tree.delete(item)
        for item in self.mtpl_tree.get_children():
            self.mtpl_tree.delete(item)
            
        # Clear entry fields
        self.mtpl_file_path.set("")
        self.output_path_var.set("")
        self.search_var.set("")
        
        # Reset progress
        self.progress_var.set(0)
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        self.log_message("Application reset - all data cleared")
        
    def is_undefined(self, value):
        """Check if a value is considered undefined (from master.py)"""
        return value is None or value == '' or value == '-'
        
    def switch_to_light_mode(self, event=None):
        """Switch application to light mode with enhanced design consistency"""
        if not self.is_dark_mode:
            return  # Already in light mode
            
        self.is_dark_mode = False
        self.theme_label.config(text="Light Mode")
        
        # Enhanced light mode color palette
        style = ttk.Style()
        style.theme_use('default')
        
        bg_primary = '#ffffff'      # Clean white background
        bg_secondary = '#f6f8fa'    # Light gray for panels
        bg_tertiary = '#f0f0f0'     # Input field backgrounds
        bg_cards = '#fafbfc'        # Card backgrounds
        bg_headers = '#e1e4e8'      # Section headers
        
        text_primary = '#24292e'    # Dark text
        text_secondary = '#586069'  # Secondary text
        text_headers = '#1b1f23'    # Header text
        text_muted = '#6a737d'      # Muted text
        
        accent_blue = '#0071c5'     # Intel blue
        accent_blue_dark = '#005a9e' # Darker blue
        accent_blue_light = '#e6f3ff' # Light blue for selection
        
        border_color = '#e1e4e8'    # Light borders
        focus_ring = '#0071c5'      # Blue focus rings
        
        # Reset root background
        self.root.configure(bg=bg_primary)
        
        # Enhanced Notebook styling
        style.configure('TNotebook', 
                       background=bg_primary, 
                       borderwidth=0,
                       tabmargins=[8, 8, 8, 0])
        
        style.configure('TNotebook.Tab', 
                       background=bg_secondary, 
                       foreground=text_primary,
                       lightcolor=bg_secondary, 
                       borderwidth=1,
                       focuscolor='none',
                       padding=[16, 12])
        
        style.map('TNotebook.Tab', 
                 background=[('selected', bg_primary), ('active', bg_tertiary)],
                 foreground=[('selected', text_headers), ('active', text_primary)])
        
        # Enhanced Frame styling
        style.configure('TFrame', 
                       background=bg_primary,
                       relief='flat',
                       borderwidth=0)
        
        # Enhanced LabelFrame styling
        style.configure('TLabelFrame', 
                       background=bg_primary, 
                       foreground=text_headers,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=border_color,
                       lightcolor=bg_headers,
                       darkcolor=bg_headers)
        
        style.configure('TLabelFrame.Label', 
                       background=bg_headers, 
                       foreground=text_headers,
                       font=('Segoe UI', 10, 'bold'),
                       padding=[8, 4])
        
        # Enhanced Label styling
        style.configure('TLabel', 
                       background=bg_primary, 
                       foreground=text_primary,
                       font=('Segoe UI', 9))
        
        # Enhanced Button styling
        style.configure('TButton', 
                       background=accent_blue, 
                       foreground='white',
                       borderwidth=0, 
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       padding=[12, 8],
                       relief='flat')
        
        style.map('TButton', 
                 background=[('active', accent_blue_dark), 
                           ('pressed', '#004080'),
                           ('focus', accent_blue)])
        
        # Enhanced Entry styling
        style.configure('TEntry', 
                       fieldbackground=bg_cards, 
                       foreground=text_primary,
                       borderwidth=2, 
                       insertcolor=text_primary,
                       relief='flat',
                       padding=[8, 6])
        
        style.map('TEntry',
                 bordercolor=[('focus', focus_ring), ('!focus', border_color)],
                 lightcolor=[('focus', focus_ring), ('!focus', border_color)],
                 darkcolor=[('focus', focus_ring), ('!focus', border_color)])
        
        # Enhanced Checkbutton styling
        style.configure('TCheckbutton', 
                       background=bg_primary, 
                       foreground=text_primary,
                       focuscolor='none',
                       font=('Segoe UI', 9))
        
        # Enhanced Progress bar styling
        style.configure('Horizontal.TProgressbar', 
                       background=accent_blue,
                       troughcolor=bg_tertiary, 
                       borderwidth=0,
                       lightcolor=accent_blue,
                       darkcolor=accent_blue)
        
        # Enhanced Treeview styling
        style.configure('Treeview', 
                       background=bg_cards, 
                       foreground=text_primary,
                       fieldbackground=bg_cards, 
                       borderwidth=1,
                       relief='solid',
                       bordercolor=border_color,
                       rowheight=36)
        
        style.configure('Treeview.Heading', 
                       background=bg_headers, 
                       foreground=text_headers,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color,
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('Treeview', 
                 background=[('selected', accent_blue_light),
                           ('focus', accent_blue_light)],
                 foreground=[('selected', text_primary)])
        
        style.map('Treeview.Heading', 
                 background=[('active', bg_tertiary)])
        
        # Enhanced Scrollbar styling
        style.configure('Vertical.TScrollbar',
                       background=bg_secondary,
                       troughcolor=bg_primary,
                       borderwidth=0,
                       arrowcolor=text_secondary)
        
        style.configure('Horizontal.TScrollbar',
                       background=bg_secondary,
                       troughcolor=bg_primary,
                       borderwidth=0,
                       arrowcolor=text_secondary)
        
        # Update theme label colors
        try:
            self.theme_label.configure(foreground=text_secondary,
                                     font=('Segoe UI', 9))
        except:
            pass
            
        # Enhanced Text widget styling
        try:
            self.log_text.configure(bg=bg_cards, 
                                  fg=text_primary, 
                                  insertbackground=text_primary,
                                  selectbackground=accent_blue_light,
                                  selectforeground=text_primary,
                                  borderwidth=1,
                                  relief='solid',
                                  highlightbackground=border_color,
                                  highlightcolor=focus_ring,
                                  highlightthickness=1,
                                  font=('Consolas', 9),
                                  spacing1=2,
                                  spacing3=2)
        except:
            pass
            
        # Update MTPL info label styling
        try:
            self.mtpl_info_label.configure(foreground=text_secondary,
                                         font=('Segoe UI', 9))
        except:
            pass
            
        # Update filter status label styling
        try:
            self.filter_status_label.configure(foreground=accent_blue,
                                             font=('Segoe UI', 9))
        except:
            pass
        
        # Reconfigure log tags for light mode
        if hasattr(self, '_tags_configured'):
            self.configure_log_tags()
        
        # Configure alternating row colors
        self.configure_treeview_alternating_colors()
        
        # Refresh material display if data exists
        if hasattr(self, 'material_df') and self.material_df is not None:
            self.update_material_display()
            
        self.log_message("☀️ Switched to Enhanced Light Mode with improved design consistency", "success")
        
    def switch_to_dark_mode(self, event=None):
        """Switch application to dark mode with purple/navy theme and proper contrast"""
        if self.is_dark_mode:
            return  # Already in dark mode
            
        self.is_dark_mode = True
        self.theme_label.config(text="Dark Mode")
        
        # Configure purple/navy dark mode colors
        style = ttk.Style()
        
        # Purple/Navy color palette with proper contrast
        bg_primary = '#2d2d48'      # Deep purple-navy background
        bg_secondary = '#353553'    # Secondary panels and cards  
        bg_tertiary = '#3d3d5c'     # Headers and navigation
        bg_input = '#2d2d48'        # Input field backgrounds
        bg_hover = '#3d3d5c'        # Hover states
        
        text_primary = '#e8e9f0'    # Primary text - high contrast
        text_secondary = '#b8bac8'  # Secondary text - good contrast
        text_headers = '#f5f5f7'    # Header text - highest contrast
        text_muted = '#b8bac8'      # Muted text for less important info
        
        accent_blue = '#0071c5'     # Intel blue
        accent_light = '#5a9fd4'    # Light blue accent
        accent_selected = '#4a6fa5' # Selected item background
        
        border_color = '#4a4a68'    # Subtle borders
        focus_ring = '#5a9fd4'      # Blue focus rings
        success_bg = '#2d4a2d'      # Success message background
        success_text = '#90ee90'    # Success message text
        
        # Main application background with gradient effect
        self.root.configure(bg=bg_primary)
        
        # Enhanced Notebook styling with purple/navy theme
        style.configure('TNotebook', 
                       background=bg_primary, 
                       borderwidth=0,
                       tabmargins=[8, 8, 8, 0])
        
        style.configure('TNotebook.Tab', 
                       background=bg_secondary,
                       foreground=text_primary,
                       lightcolor=bg_secondary,
                       borderwidth=1,
                       focuscolor='none',
                       padding=[16, 12],
                       font=('Segoe UI', 9))
        
        style.map('TNotebook.Tab', 
                 background=[('selected', bg_tertiary), ('active', bg_hover)],
                 foreground=[('selected', text_headers), ('active', text_primary)])
        
        # Enhanced Frame styling
        style.configure('TFrame', 
                       background=bg_primary,
                       relief='flat',
                       borderwidth=0)
        
        # Enhanced LabelFrame for section headers
        style.configure('TLabelFrame', 
                       background=bg_primary,
                       foreground=text_headers,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=border_color,
                       lightcolor=bg_tertiary,
                       darkcolor=bg_tertiary)
        
        style.configure('TLabelFrame.Label', 
                       background=bg_tertiary,
                       foreground=text_headers,
                       font=('Segoe UI', 10, 'bold'),
                       padding=[8, 4])
        
        # Enhanced Label styling with proper contrast
        style.configure('TLabel', 
                       background=bg_primary,
                       foreground=text_primary,
                       font=('Segoe UI', 9))
        
        # Enhanced Button styling with gradient effect
        style.configure('TButton', 
                       background=accent_selected,
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9),
                       padding=[12, 8],
                       relief='flat')
        
        style.map('TButton', 
                 background=[('active', accent_light), 
                           ('pressed', accent_blue),
                           ('focus', accent_selected)],
                 relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        # Enhanced Entry styling with proper background contrast
        style.configure('TEntry', 
                       fieldbackground=bg_input,
                       foreground=text_primary,
                       borderwidth=2,
                       insertcolor=text_primary,
                       relief='flat',
                       padding=[8, 6])
        
        style.map('TEntry',
                 bordercolor=[('focus', focus_ring), ('!focus', border_color)],
                 lightcolor=[('focus', focus_ring), ('!focus', border_color)],
                 darkcolor=[('focus', focus_ring), ('!focus', border_color)])
        
        # Enhanced Checkbutton styling
        style.configure('TCheckbutton', 
                       background=bg_primary,
                       foreground=text_primary,
                       focuscolor='none',
                       font=('Segoe UI', 9))
        
        # Enhanced Progress bar
        style.configure('Horizontal.TProgressbar', 
                       background=accent_blue,
                       troughcolor=bg_secondary,
                       borderwidth=0,
                       lightcolor=accent_blue,
                       darkcolor=accent_blue)
        
        # Enhanced Treeview with proper contrast and zebra striping
        style.configure('Treeview', 
                       background=bg_primary,
                       foreground=text_primary,
                       fieldbackground=bg_primary,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=border_color,
                       rowheight=40)  # Increased for comfortable clicking
        
        style.configure('Treeview.Heading', 
                       background=bg_tertiary,
                       foreground=text_headers,
                       borderwidth=1,
                       relief='flat',
                       bordercolor=border_color,
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('Treeview', 
                 background=[('selected', accent_selected),
                           ('focus', accent_selected)],
                 foreground=[('selected', 'white')])
        
        style.map('Treeview.Heading', 
                 background=[('active', bg_hover)],
                 relief=[('pressed', 'flat')])
        
        # Enhanced Scrollbar styling
        style.configure('Vertical.TScrollbar',
                       background=bg_secondary,
                       troughcolor=bg_primary,
                       borderwidth=0,
                       arrowcolor=text_secondary,
                       darkcolor=border_color,
                       lightcolor=border_color)
        
        style.configure('Horizontal.TScrollbar',
                       background=bg_secondary,
                       troughcolor=bg_primary,
                       borderwidth=0,
                       arrowcolor=text_secondary,
                       darkcolor=border_color,
                       lightcolor=border_color)
        
        # Update theme label with enhanced styling
        try:
            self.theme_label.configure(foreground=text_secondary,
                                     font=('Segoe UI', 9))
        except:
            pass
            
        # Enhanced Text widget with proper contrast
        try:
            self.log_text.configure(bg=bg_secondary,
                                  fg=text_primary,
                                  insertbackground=text_primary,
                                  selectbackground=accent_selected,
                                  selectforeground='white',
                                  borderwidth=1,
                                  relief='solid',
                                  highlightbackground=border_color,
                                  highlightcolor=focus_ring,
                                  highlightthickness=1,
                                  font=('Consolas', 9),
                                  spacing1=2,
                                  spacing3=2)
        except:
            pass
            
        # Update MTPL info label styling
        try:
            self.mtpl_info_label.configure(foreground=text_secondary,
                                         font=('Segoe UI', 9))
        except:
            pass
            
        # Update filter status label styling
        try:
            self.filter_status_label.configure(foreground=accent_light,
                                             font=('Segoe UI', 9))
        except:
            pass
        
        # Reconfigure log tags for dark mode with proper colors
        if hasattr(self, '_tags_configured'):
            self.configure_log_tags()
        
        # Configure alternating row colors
        self.configure_treeview_alternating_colors()
        
        # Refresh material display if data exists
        if hasattr(self, 'material_df') and self.material_df is not None:
            self.update_material_display()
            
        self.log_message("🌙 Switched to Purple/Navy Dark Mode with enhanced visibility", "success")
    
    def enhance_visual_feedback(self):
        """Add visual enhancements like hover effects and focus indicators"""
        try:
            # Add hover effects to treeview
            def on_treeview_motion(event):
                item = self.mtpl_tree.identify('item', event.x, event.y)
                if item:
                    # Subtle hover effect
                    self.mtpl_tree.selection_set(item)
                    
            def on_treeview_leave(event):
                # Clear hover selection when mouse leaves
                if not self.mtpl_tree.focus():
                    self.mtpl_tree.selection_clear()
            
            # Bind hover events
            self.mtpl_tree.bind('<Motion>', on_treeview_motion)
            self.mtpl_tree.bind('<Leave>', on_treeview_leave)
            
        except Exception as e:
            print(f"Could not add visual feedback enhancements: {e}")
    
    def apply_enhanced_spacing(self):
        """Apply enhanced spacing and layout improvements"""
        try:
            # Add consistent padding to main frames
            for widget in [self.material_frame, self.mtpl_frame, self.output_frame]:
                widget.configure(padding=[16, 16, 16, 16])
        except:
            pass
    
    def configure_treeview_alternating_colors(self):
        """Configure alternating row colors for better visibility in dark mode with enhanced error handling"""
        try:
            if self.is_dark_mode:
                # Purple/Navy theme alternating colors with high contrast
                if hasattr(self, 'mtpl_tree') and self.mtpl_tree.winfo_exists():
                    self.mtpl_tree.tag_configure('oddrow', background='#2d2d48', foreground='#e8e9f0')
                    self.mtpl_tree.tag_configure('evenrow', background='#353553', foreground='#e8e9f0')
                    # Configure checked/unchecked states with proper visibility
                    self.mtpl_tree.tag_configure('checked', background='#4a6fa5', foreground='white')
                    self.mtpl_tree.tag_configure('unchecked', background='#2d2d48', foreground='#e8e9f0')
                
                if hasattr(self, 'material_tree') and self.material_tree.winfo_exists():
                    self.material_tree.tag_configure('oddrow', background='#2d2d48', foreground='#e8e9f0')
                    self.material_tree.tag_configure('evenrow', background='#353553', foreground='#e8e9f0')
            else:
                # Light mode alternating colors
                if hasattr(self, 'mtpl_tree') and self.mtpl_tree.winfo_exists():
                    self.mtpl_tree.tag_configure('oddrow', background='#ffffff', foreground='#24292e')
                    self.mtpl_tree.tag_configure('evenrow', background='#f6f8fa', foreground='#24292e')
                    # Configure checked/unchecked states for light mode
                    self.mtpl_tree.tag_configure('checked', background='#e6f3ff', foreground='#24292e')
                    self.mtpl_tree.tag_configure('unchecked', background='#ffffff', foreground='#24292e')
                
                if hasattr(self, 'material_tree') and self.material_tree.winfo_exists():
                    self.material_tree.tag_configure('oddrow', background='#ffffff', foreground='#24292e')
                    self.material_tree.tag_configure('evenrow', background='#f6f8fa', foreground='#24292e')
                    
        except Exception as e:
            print(f"Error configuring treeview colors: {e}")
            
    def debug_window_state(self):
        """Debug function to check window and widget state"""
        try:
            print(f"Window state: {self.root.state()}")
            print(f"Window geometry: {self.root.geometry()}")
            
            if hasattr(self, 'material_tree'):
                print(f"Material tree exists: {self.material_tree.winfo_exists()}")
                print(f"Material tree children: {len(self.material_tree.get_children())}")
                
            if hasattr(self, 'mtpl_tree'):
                print(f"MTPL tree exists: {self.mtpl_tree.winfo_exists()}")
                print(f"MTPL tree children: {len(self.mtpl_tree.get_children())}")
                
            if hasattr(self, 'material_df'):
                print(f"Material data available: {self.material_df is not None}")
                if self.material_df is not None:
                    print(f"Material data shape: {self.material_df.shape}")
                    
        except Exception as e:
            print(f"Error in debug_window_state: {e}")
            
    def force_widget_refresh(self):
        """Force refresh of all widgets to handle resize issues"""
        try:
            # Update all widgets
            self.root.update_idletasks()
            
            # Refresh material display if data exists
            if hasattr(self, 'material_df') and self.material_df is not None:
                self.update_material_display()
                
            # Refresh MTPL display if data exists  
            if hasattr(self, 'all_mtpl_items') and self.all_mtpl_items:
                # Get current search text
                search_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
                
                if not search_text:
                    filtered_items = self.all_mtpl_items
                else:
                    filtered_items = []
                    for item_data in self.all_mtpl_items:
                        item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                        if search_text in item_text:
                            filtered_items.append(item_data)
                            
                self.display_filtered_items(filtered_items)
                
            print("Debug - Force widget refresh completed")
            
        except Exception as e:
            print(f"Error in force_widget_refresh: {e}")
    
def main():
    root = tk.Tk()
    app = CTVListGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
