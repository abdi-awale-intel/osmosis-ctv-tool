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

# Import CustomTkinter for modern GUI
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("light")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("CustomTkinter not available - using standard tkinter")

# Import PIL for images (with fallback)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available - images will be disabled")

# Helper functions for widget creation with CustomTkinter fallback
def create_frame(parent, **kwargs):
    """Create a frame using CustomTkinter if available, otherwise use ttk.Frame"""
    if CTK_AVAILABLE:
        return ctk.CTkFrame(parent, **kwargs)
    else:
        return ttk.Frame(parent)

def create_button(parent, text="", command=None, **kwargs):
    """Create a button using CustomTkinter if available, otherwise use ttk.Button"""
    if CTK_AVAILABLE:
        return ctk.CTkButton(parent, text=text, command=command, **kwargs)
    else:
        return ttk.Button(parent, text=text, command=command, **kwargs)

def create_label(parent, text="", **kwargs):
    """Create a label using CustomTkinter if available, otherwise use ttk.Label"""
    if CTK_AVAILABLE:
        return ctk.CTkLabel(parent, text=text, **kwargs)
    else:
        return ttk.Label(parent, text=text, **kwargs)

def create_entry(parent, **kwargs):
    """Create an entry using CustomTkinter if available, otherwise use ttk.Entry"""
    if CTK_AVAILABLE:
        return ctk.CTkEntry(parent, **kwargs)
    else:
        return ttk.Entry(parent, **kwargs)

def create_notebook(parent, **kwargs):
    """Create a notebook - CustomTkinter doesn't have notebook, so use ttk.Notebook"""
    return ttk.Notebook(parent, **kwargs)

# Import your existing modules
import file_functions as fi
import mtpl_parser as mt
import index_ctv as ind
import smart_json_parser as sm
import clkutils_config_json_to_csv as clk

# Import pyuber_query with fallback handling
PYUBER_AVAILABLE = True
try:
    # Add the parent directory to Python path to find PyUber module
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    import pyuber_query as py
    print("PyUber module loaded successfully")
except ImportError as e:
    PYUBER_AVAILABLE = False
    print(f"PyUber not available - some features will be disabled: {e}")
    # Create a dummy module for fallback
    class DummyPyUber:
        def uber_request(self, *args, **kwargs):
            raise ImportError("PyUber module not available")
    py = DummyPyUber()

class CTVListGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Osmosis")
        
        # Initialize scaling and window management variables
        self.current_zoom_level = 1.0
        self.zoom_levels = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0]
        self.default_font_size = 9
        self.compact_mode = False
        self.compact_mode_var = tk.BooleanVar(value=self.compact_mode)
        
        # Detect screen resolution and set appropriate initial size
        self.setup_window_sizing()
        
        # Ensure images directory exists
        self.setup_images_directory()
        
        # Set application icon
        if PIL_AVAILABLE:
            try:
                # Try different possible icon files
                possible_icons = ["logo.jpeg", "logo.jpg", "logo.png", "icon.png", "icon.jpg", "icon.jpeg"]
                icon_loaded = False
                
                for icon_name in possible_icons:
                    try:
                        icon_path = os.path.join(os.path.dirname(__file__), "images", icon_name)
                        if os.path.exists(icon_path):
                            icon_image = Image.open(icon_path)
                            icon_photo = ImageTk.PhotoImage(icon_image)
                            self.root.iconphoto(False, icon_photo)
                            print(f"Successfully loaded app icon: {icon_name}")
                            icon_loaded = True
                            break
                    except Exception as e:
                        print(f"Failed to load icon {icon_name}: {e}")
                        continue
                
                if not icon_loaded:
                    print("No app icon found in images directory")
                    
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
        self.last_mtpl_path = "" # Track last MTPL file path
        self.is_dark_mode = False  # Track current theme
        self.processing = False
        
        # Test instance filtering variables
        self.material_test_instances = []  # Store test instances from loaded material data
        self.auto_filter_enabled = False  # Track if auto-filtering is active
        
        # CLKUtils tab variables
        self.clkutils_tests = []  # Store CLKUtils test names
        self.all_clkutils_items = []  # Store all CLKUtils items for filtering
        self.clkutils_file_path = tk.StringVar()
        self.run_clkutils_var = tk.BooleanVar(value=False)  # Initialize here for early access
        
        # Initialize theme components as None for fallback handling
        self.light_logo = None
        self.dark_logo = None
        self.light_mode_btn = None
        self.dark_mode_btn = None
        self.theme_label = None
        
        # Setup window management first
        self.setup_window_management()
        
        # Ensure proper working directory for config files
        self.setup_working_directory()
        
        self.create_widgets()
        
        # Setup file path normalization callbacks (after widgets are created)
        self.setup_file_path_traces()
        
        # Load user preferences for zoom and window state
        self.load_user_preferences()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Setup window close handler to save preferences
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_window_sizing(self):
        """Setup window sizing based on screen resolution with responsive scaling"""
        try:
            # Get screen dimensions
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            print(f"Screen resolution detected: {screen_width}x{screen_height}")
            
            # Calculate appropriate window size based on screen resolution
            if screen_width <= 1366:  # Small screens
                window_width = int(screen_width * 0.95)
                window_height = int(screen_height * 0.85)
                self.current_zoom_level = 0.8
            elif screen_width <= 1920:  # Standard HD screens
                window_width = min(1400, int(screen_width * 0.85))
                window_height = min(900, int(screen_height * 0.85))
                self.current_zoom_level = 1.0
            else:  # Large/4K screens
                window_width = min(1600, int(screen_width * 0.75))
                window_height = min(1000, int(screen_height * 0.80))
                self.current_zoom_level = 1.1
            
            # Set window geometry
            self.root.geometry(f"{window_width}x{window_height}")
            
            # Center window on screen
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Set minimum size based on screen
            min_width = min(800, int(screen_width * 0.5))
            min_height = min(600, int(screen_height * 0.5))
            self.root.minsize(min_width, min_height)
            
            # Make window resizable
            self.root.resizable(True, True)
            
            print(f"Window sized to: {window_width}x{window_height}, Zoom level: {self.current_zoom_level}")
            
        except Exception as e:
            print(f"Error setting up window sizing: {e}")
            # Fallback to default sizing
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            self.current_zoom_level = 1.0
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for window operations"""
        # Window management shortcuts
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Zoom shortcuts
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())  # For keyboards where + requires shift
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        
        # Focus the root window to ensure shortcuts work
        self.root.focus_set()
        
    def zoom_in(self):
        """Increase zoom level"""
        current_index = self.zoom_levels.index(self.current_zoom_level) if self.current_zoom_level in self.zoom_levels else 5
        if current_index < len(self.zoom_levels) - 1:
            self.current_zoom_level = self.zoom_levels[current_index + 1]
            self.apply_zoom()
            
    def zoom_out(self):
        """Decrease zoom level"""
        current_index = self.zoom_levels.index(self.current_zoom_level) if self.current_zoom_level in self.zoom_levels else 5
        if current_index > 0:
            self.current_zoom_level = self.zoom_levels[current_index - 1]
            self.apply_zoom()
            
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.current_zoom_level = 1.0
        self.apply_zoom()
        
    def clear_all_values(self):
        """Clear all user input values to default/empty state"""
        try:
            # Clear material input fields
            if hasattr(self, 'lot_var'):
                self.lot_var.set("")
            if hasattr(self, 'wafer_var'):
                self.wafer_var.set("")
            if hasattr(self, 'program_var'):
                self.program_var.set("")
            if hasattr(self, 'prefetch_var'):
                self.prefetch_var.set("3")  # Keep default value for prefetch
            if hasattr(self, 'database_var'):
                self.database_var.set("F24_PROD_XEUS")  # Keep default database
            
            # Clear output settings
            if hasattr(self, 'output_path_var'):
                self.output_path_var.set("")
            if hasattr(self, 'delete_files_var'):
                self.delete_files_var.set(True)  # Reset to default
            if hasattr(self, 'run_jmp_var'):
                self.run_jmp_var.set(False)  # Reset to default
            
            # Clear MTPL settings
            if hasattr(self, 'mtpl_file_path'):
                self.mtpl_file_path.set("")
            if hasattr(self, 'search_var'):
                self.search_var.set("")
            
            # Clear data
            self.material_df = None
            self.mtpl_df = None
            self.test_list = []
            self.all_mtpl_items = []
            self.last_mtpl_path = ""
            
            # Clear displays
            if hasattr(self, 'material_tree'):
                for item in self.material_tree.get_children():
                    self.material_tree.delete(item)
            
            if hasattr(self, 'mtpl_tree'):
                for item in self.mtpl_tree.get_children():
                    self.mtpl_tree.delete(item)
            
            # Clear log
            if hasattr(self, 'log_text'):
                self.log_text.delete(1.0, tk.END)
            
            # Reset progress
            if hasattr(self, 'progress_var'):
                self.progress_var.set(0)
            
            # Update status indicators
            if hasattr(self, 'mtpl_info_label'):
                self.mtpl_info_label.configure(text="Select an MTPL file for processing", foreground='gray')
            if hasattr(self, 'selected_tests_label'):
                self.selected_tests_label.configure(text="0")
            if hasattr(self, 'reload_mtpl_button'):
                self.reload_mtpl_button.configure(state='disabled')
            
            self.log_message("All values cleared successfully", "success")
            print("All user input values have been cleared")
            
        except Exception as e:
            print(f"Error clearing values: {e}")
            if hasattr(self, 'log_text'):
                self.log_message(f"Error clearing values: {e}", "error")
        
    def set_zoom(self, level):
        """Set specific zoom level"""
        if level in self.zoom_levels:
            self.current_zoom_level = level
            self.apply_zoom()
            
    def apply_zoom(self):
        """Apply current zoom level to all UI elements"""
        try:
            # Calculate scaled font size
            scaled_font_size = max(6, int(self.default_font_size * self.current_zoom_level))
            
            # Update style configuration for all ttk widgets
            style = ttk.Style()
            
            # Configure fonts for different widget types
            style.configure('TLabel', font=('Segoe UI', scaled_font_size))
            style.configure('TButton', font=('Segoe UI', scaled_font_size))
            style.configure('TEntry', font=('Segoe UI', scaled_font_size))
            style.configure('TCheckbutton', font=('Segoe UI', scaled_font_size))
            style.configure('Treeview', font=('Segoe UI', scaled_font_size), rowheight=int(30 * self.current_zoom_level))
            style.configure('Treeview.Heading', font=('Segoe UI', scaled_font_size, 'bold'))
            style.configure('TCombobox', font=('Segoe UI', scaled_font_size))
            style.configure('TLabelFrame.Label', font=('Segoe UI', scaled_font_size, 'bold'))
            
            # Update specific UI elements that need special scaling
            if hasattr(self, 'log_text'):
                self.log_text.configure(font=('Courier New', scaled_font_size))
            
            # Update zoom status
            if hasattr(self, 'zoom_label'):
                self.zoom_label.configure(text=f"{int(self.current_zoom_level * 100)}%")
            
            # Force refresh of all widgets
            self.root.update_idletasks()
            
            print(f"Applied zoom level: {self.current_zoom_level} (Font size: {scaled_font_size})")
            
        except Exception as e:
            print(f"Error applying zoom: {e}")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        
    def fit_to_screen(self):
        """Fit window to screen size optimally"""
        self.setup_window_sizing()
        self.apply_zoom()
        
    def toggle_compact_mode(self):
        """Toggle compact mode for smaller screens"""
        self.compact_mode = not self.compact_mode
        self.compact_mode_var.set(self.compact_mode)
        self.apply_compact_mode()
        
    def on_compact_mode_toggle(self):
        """Handle compact mode toggle from checkbutton"""
        self.compact_mode = self.compact_mode_var.get()
        self.apply_compact_mode()
        
    def apply_compact_mode(self):
        """Apply or remove compact mode styling"""
        if self.compact_mode:
            # Reduce padding and spacing
            self.root.configure(padx=5, pady=5)
            # Update zoom status
            if hasattr(self, 'compact_mode_label'):
                self.compact_mode_label.configure(text="Compact Mode: ON")
        else:
            # Normal padding and spacing
            self.root.configure(padx=16, pady=16)
            if hasattr(self, 'compact_mode_label'):
                self.compact_mode_label.configure(text="Compact Mode: OFF")
                
    def save_user_preferences(self):
        """Save user preferences like zoom level and window state"""
        try:
            preferences = {
                'zoom_level': self.current_zoom_level,
                'compact_mode': self.compact_mode,
                'window_geometry': self.root.geometry(),
                'theme_mode': 'dark' if self.is_dark_mode else 'light',
                'last_mtpl_path': getattr(self, 'last_mtpl_path', ""),
                # Save all user input fields
                'material_inputs': {
                    'lot': getattr(self, 'lot_var', tk.StringVar()).get(),
                    'wafer': getattr(self, 'wafer_var', tk.StringVar()).get(),
                    'program': getattr(self, 'program_var', tk.StringVar()).get(),
                    'prefetch': getattr(self, 'prefetch_var', tk.StringVar()).get(),
                    'database': getattr(self, 'database_var', tk.StringVar()).get()
                },
                'output_settings': {
                    'output_path': getattr(self, 'output_path_var', tk.StringVar()).get(),
                    'delete_files': getattr(self, 'delete_files_var', tk.BooleanVar()).get(),
                    'run_jmp': getattr(self, 'run_jmp_var', tk.BooleanVar()).get()
                }
            }
            import json
            prefs_file = os.path.join(os.path.dirname(__file__), 'user_preferences.json')
            with open(prefs_file, 'w') as f:
                json.dump(preferences, f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")
            
    def load_user_preferences(self):
        """Load user preferences from previous session"""
        try:
            prefs_file = os.path.join(os.path.dirname(__file__), 'user_preferences.json')
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    preferences = json.load(f)
                # Apply saved preferences
                self.current_zoom_level = preferences.get('zoom_level', 1.0)
                self.compact_mode = preferences.get('compact_mode', False)
                self.compact_mode_var.set(self.compact_mode)
                
                # Restore material input fields
                material_inputs = preferences.get('material_inputs', {})
                if hasattr(self, 'lot_var'):
                    self.lot_var.set(material_inputs.get('lot', 'G5088651'))
                if hasattr(self, 'wafer_var'):
                    self.wafer_var.set(material_inputs.get('wafer', '533'))
                if hasattr(self, 'program_var'):
                    self.program_var.set(material_inputs.get('program', 'DABHOPCA0H20C022528'))
                if hasattr(self, 'prefetch_var'):
                    self.prefetch_var.set(material_inputs.get('prefetch', '3'))
                if hasattr(self, 'database_var'):
                    self.database_var.set(material_inputs.get('database', 'F24_PROD_XEUS'))
                
                # Restore output settings
                output_settings = preferences.get('output_settings', {})
                if hasattr(self, 'output_path_var'):
                    self.output_path_var.set(output_settings.get('output_path', ''))
                if hasattr(self, 'delete_files_var'):
                    self.delete_files_var.set(output_settings.get('delete_files', True))
                if hasattr(self, 'run_jmp_var'):
                    self.run_jmp_var.set(output_settings.get('run_jmp', False))
                
                # Restore last MTPL file path if available
                last_mtpl_path = preferences.get('last_mtpl_path', "")
                if last_mtpl_path and os.path.exists(last_mtpl_path):
                    self.last_mtpl_path = last_mtpl_path
                    self.mtpl_file_path.set(last_mtpl_path)
                    # Enable reload button if widget exists
                    if hasattr(self, 'reload_mtpl_button'):
                        self.reload_mtpl_button.configure(state='normal')
                    # Optionally, update info label
                    if hasattr(self, 'mtpl_info_label'):
                        file_name = os.path.basename(last_mtpl_path)
                        self.update_status_indicator(self.mtpl_info_label, f"🔄 Reload available: {file_name}", "info")
                else:
                    self.last_mtpl_path = ""
                    if hasattr(self, 'reload_mtpl_button'):
                        self.reload_mtpl_button.configure(state='disabled')
                self.root.after(100, self.apply_zoom)
                self.root.after(100, self.apply_compact_mode)
                print(f"Loaded user preferences: Zoom {self.current_zoom_level}, Compact: {self.compact_mode}, Last MTPL: {self.last_mtpl_path}")
        except Exception as e:
            print(f"Error loading preferences: {e}")
        self.root.after(200, self.update_zoom_display)
    
    def update_zoom_display(self):
        """Update the zoom display label"""
        if hasattr(self, 'zoom_label'):
            self.zoom_label.configure(text=f"{int(self.current_zoom_level * 100)}%")
    
    def on_closing(self):
        """Handle application closing - save preferences and cleanup"""
        try:
            self.save_user_preferences()
            print("User preferences saved successfully")
        except Exception as e:
            print(f"Error saving preferences on close: {e}")
        
        # Clean up .mtpl.csv files from src directory
        try:
            src_dir = os.path.dirname(__file__)
            mtpl_csv_files = []
            
            # Find all .mtpl.csv files in the src directory
            for file in os.listdir(src_dir):
                if file.endswith('.mtpl.csv'):
                    mtpl_csv_files.append(file)
            
            # Remove the files
            for file in mtpl_csv_files:
                file_path = os.path.join(src_dir, file)
                try:
                    os.remove(file_path)
                    print(f"Cleaned up temporary file: {file}")
                except OSError as e:
                    print(f"Could not remove {file}: {e}")
            
            if mtpl_csv_files:
                print(f"Cleanup completed: removed {len(mtpl_csv_files)} .mtpl.csv file(s)")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        finally:
            self.root.destroy()
    
    def setup_images_directory(self):
        """Setup the images directory and provide guidance if images are missing"""
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        
        # Create images directory if it doesn't exist
        if not os.path.exists(images_dir):
            try:
                os.makedirs(images_dir)
                print(f"Created images directory: {images_dir}")
            except Exception as e:
                print(f"Could not create images directory: {e}")
                return
        
        # Check for expected image files and provide guidance
        expected_files = {
            "App Icon": ["logo.jpeg", "logo.jpg", "logo.png", "icon.png", "icon.jpg", "icon.jpeg"],
            "Light Mode Logo": ["lightmode-logo.jpg", "lightmode-logo.png", "light-logo.jpg", "light-logo.png"],
            "Dark Mode Logo": ["darkmode-logo.jpg", "darkmode-logo.png", "dark-logo.jpg", "dark-logo.png"]
        }
        
        missing_categories = []
        for category, files in expected_files.items():
            found = False
            for filename in files:
                if os.path.exists(os.path.join(images_dir, filename)):
                    found = True
                    break
            if not found:
                missing_categories.append(category)
        
        if missing_categories:
            print(f"Images directory: {images_dir}")
            print("Missing image files for:", ", ".join(missing_categories))
            print("Expected files:")
            for category in missing_categories:
                print(f"  {category}: {' or '.join(expected_files[category])}")
            print("The application will use text-based fallbacks for missing images.")
        
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
        
    def setup_working_directory(self):
        """Setup proper working directory for config files"""
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            current_dir = os.getcwd()
            
            # Check if configFile_DMR.json exists in current directory
            config_file = 'configFile_DMR.json'
            
            # Log current working directory
            print(f"Current working directory: {current_dir}")
            print(f"Script directory: {script_dir}")
            
            if os.path.exists(config_file):
                print(f"Found {config_file} in current working directory")
            elif os.path.exists(os.path.join(script_dir, config_file)):
                print(f"Found {config_file} in script directory, changing working directory")
                os.chdir(script_dir)
                print(f"Changed working directory to: {os.getcwd()}")
            else:
                print(f"Warning: {config_file} not found in current directory ({current_dir}) or script directory ({script_dir})")
                print(f"Please ensure {config_file} is available for CLKUtils processing")
                
        except Exception as e:
            print(f"Error setting up working directory: {e}")
    
    def setup_file_path_traces(self):
        """Setup trace callbacks for file path StringVars to auto-normalize paths"""
        try:
            # Add trace callbacks for file path normalization
            self._mtpl_path_trace_id = self.mtpl_file_path.trace_add('write', self.on_file_path_change)
            self._clkutils_path_trace_id = self.clkutils_file_path.trace_add('write', self.on_file_path_change)
            self._output_path_trace_id = self.output_path_var.trace_add('write', self.on_output_path_change)
        except Exception as e:
            print(f"Error setting up file path traces: {e}")

    def on_file_path_change(self, var_name, index, mode):
        """Handle file path changes to auto-normalize paths"""
        try:
            # Get the StringVar that triggered this callback
            if var_name == str(self.mtpl_file_path):
                path_var = self.mtpl_file_path
            elif var_name == str(self.clkutils_file_path):
                path_var = self.clkutils_file_path
            else:
                return
            
            current_path = path_var.get()
            if current_path:
                normalized = self.normalize_unc_path(current_path)
                if normalized != current_path:
                    # Temporarily remove trace to avoid recursion
                    if var_name == str(self.mtpl_file_path):
                        self.mtpl_file_path.trace_remove('write', self._mtpl_path_trace_id)
                        self.mtpl_file_path.set(normalized)
                        self._mtpl_path_trace_id = self.mtpl_file_path.trace_add('write', self.on_file_path_change)
                    elif var_name == str(self.clkutils_file_path):
                        self.clkutils_file_path.trace_remove('write', self._clkutils_path_trace_id)
                        self.clkutils_file_path.set(normalized)
                        self._clkutils_path_trace_id = self.clkutils_file_path.trace_add('write', self.on_file_path_change)
        except Exception as e:
            print(f"Error in on_file_path_change: {e}")

    def on_output_path_change(self, var_name, index, mode):
        """Handle output path changes to auto-normalize paths and strip quotes"""
        try:
            current_path = self.output_path_var.get()
            if current_path:
                normalized = self.normalize_unc_path(current_path)
                if normalized != current_path:
                    # Temporarily remove trace to avoid recursion
                    self.output_path_var.trace_remove('write', self._output_path_trace_id)
                    self.output_path_var.set(normalized)
                    self._output_path_trace_id = self.output_path_var.trace_add('write', self.on_output_path_change)
        except Exception as e:
            print(f"Error in on_output_path_change: {e}")
    
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
    
    def create_resizable_data_frame(self, parent, title, min_height=200, default_height=400, min_width=400, default_width=800):
        """Create a 2D resizable frame for data display with drag-to-resize functionality in both dimensions"""
        # Main container frame - stretch with consistent margins
        container = ttk.LabelFrame(parent, text=title)
        container.pack(fill='both', expand=True, padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Configure container for 2D resizing
        container.grid_rowconfigure(2, weight=1)  # Data area expandable
        container.grid_columnconfigure(1, weight=1)  # Data area expandable
        
        # Instructions frame at the top
        instructions_frame = ttk.Frame(container)
        instructions_frame.grid(row=0, column=0, columnspan=3, sticky='ew', padx=5, pady=(5, 0))
        
        instructions = ttk.Label(instructions_frame, 
                               text="💡 Drag edges/corner to resize • Double-click handles to auto-fit", 
                               font=('Arial', 8), foreground='gray')
        instructions.pack(side='left')
        
        # Size controls - only utility buttons
        size_controls = ttk.Frame(instructions_frame)
        size_controls.pack(side='right')
        
        # Utility controls only
        utility_frame = ttk.Frame(size_controls)
        utility_frame.pack(side='left')
        
        ttk.Button(utility_frame, text="🔄 Auto-fit", 
                  command=lambda: self.auto_fit_frame_2d(container, data_frame),
                  width=10).pack(side='left', padx=2)
        ttk.Button(utility_frame, text="↩️ Reset", 
                  command=lambda: self.reset_frame_size_2d(container, default_height, default_width),
                  width=8).pack(side='left', padx=2)
        
        # Left edge handle (for width resizing from left side - optional)
        left_handle = ttk.Frame(container, width=8)
        left_handle.grid(row=2, column=0, sticky='ns', padx=(5, 2))
        left_handle.grid_propagate(False)
        left_handle.configure(cursor='sb_h_double_arrow', relief='raised', borderwidth=1)
        
        # Data display frame
        data_frame = ttk.Frame(container)
        data_frame.grid(row=2, column=1, sticky='nsew', padx=2, pady=2)
        data_frame.grid_rowconfigure(0, weight=1)
        data_frame.grid_columnconfigure(0, weight=1)
        
        # Right edge handle (for width resizing)
        right_handle = ttk.Frame(container, width=8)
        right_handle.grid(row=2, column=2, sticky='ns', padx=(2, 5))
        right_handle.grid_propagate(False)
        right_handle.configure(cursor='sb_h_double_arrow', relief='raised', borderwidth=1)
        
        # Visual indicator for right handle
        right_label = ttk.Label(right_handle, text="║", 
                              font=('Arial', 10), foreground='blue', anchor='center')
        right_label.pack(fill='both', expand=True)
        
        # Bottom edge handle (for height resizing)
        bottom_handle = ttk.Frame(container, height=8)
        bottom_handle.grid(row=3, column=0, columnspan=3, sticky='ew', padx=5, pady=(2, 5))
        bottom_handle.grid_propagate(False)
        bottom_handle.configure(cursor='sb_v_double_arrow', relief='raised', borderwidth=1)
        
        # Visual indicator for bottom handle
        bottom_label = ttk.Label(bottom_handle, text="═══ Drag to Resize Height ═══", 
                               font=('Arial', 7), foreground='blue', anchor='center')
        bottom_label.pack(fill='both', expand=True)
        
        # Corner handle (for both width and height resizing)
        corner_handle = ttk.Frame(container, width=8, height=8)
        corner_handle.grid(row=3, column=2, sticky='se', padx=(2, 5), pady=(2, 5))
        corner_handle.grid_propagate(False)
        corner_handle.configure(cursor='sizing', relief='raised', borderwidth=1)
        
        # Visual indicator for corner handle
        corner_label = ttk.Label(corner_handle, text="◢", 
                               font=('Arial', 8), foreground='purple', anchor='center')
        corner_label.pack(fill='both', expand=True)
        
        # Store initial dimensions and limits
        setattr(container, '_initial_height', default_height)
        setattr(container, '_min_height', min_height)
        setattr(container, '_max_height', min_height * 4)
        setattr(container, '_initial_width', default_width)
        setattr(container, '_min_width', min_width)
        setattr(container, '_max_width', min_width * 3)
        
        # Set initial size
        container.configure(height=default_height, width=default_width)
        container.grid_propagate(False)
        
        # Bind 2D drag events to resize handles
        self.make_frame_resizable_2d(bottom_handle, right_handle, corner_handle, container)
        
        # Add double-click to auto-fit for each handle
        bottom_handle.bind('<Double-Button-1>', 
                          lambda e: self.auto_fit_frame_2d(container, data_frame))
        bottom_label.bind('<Double-Button-1>', 
                         lambda e: self.auto_fit_frame_2d(container, data_frame))
        right_handle.bind('<Double-Button-1>', 
                         lambda e: self.auto_fit_frame_2d(container, data_frame))
        right_label.bind('<Double-Button-1>', 
                        lambda e: self.auto_fit_frame_2d(container, data_frame))
        corner_handle.bind('<Double-Button-1>', 
                          lambda e: self.auto_fit_frame_2d(container, data_frame))
        corner_label.bind('<Double-Button-1>', 
                         lambda e: self.auto_fit_frame_2d(container, data_frame))
        
        return data_frame
    
    def make_frame_resizable_2d(self, bottom_handle, right_handle, corner_handle, target_frame):
        """Make a frame resizable in both dimensions with multiple drag handles"""
        
        # Shared state variables
        resize_state = {
            'start_x': None,
            'start_y': None,
            'start_width': None,
            'start_height': None,
            'resize_mode': None  # 'horizontal', 'vertical', or 'both'
        }
        
        def start_drag(event, mode):
            resize_state['start_x'] = event.x_root
            resize_state['start_y'] = event.y_root
            resize_state['start_width'] = target_frame.winfo_width()
            resize_state['start_height'] = target_frame.winfo_height()
            resize_state['resize_mode'] = mode
            
            # Visual feedback
            if mode == 'horizontal':
                right_handle.configure(relief='sunken')
                self.root.configure(cursor='sb_h_double_arrow')
            elif mode == 'vertical':
                bottom_handle.configure(relief='sunken')
                self.root.configure(cursor='sb_v_double_arrow')
            elif mode == 'both':
                corner_handle.configure(relief='sunken')
                self.root.configure(cursor='sizing')
        
        def drag_resize(event):
            if resize_state['resize_mode'] is None:
                return
                
            delta_x = event.x_root - resize_state['start_x']
            delta_y = event.y_root - resize_state['start_y']
            
            # Get constraints
            min_width = getattr(target_frame, '_min_width', 400)
            max_width = getattr(target_frame, '_max_width', 1200)
            min_height = getattr(target_frame, '_min_height', 200)
            max_height = getattr(target_frame, '_max_height', 800)
            
            # Calculate new dimensions
            new_width = resize_state['start_width']
            new_height = resize_state['start_height']
            
            if resize_state['resize_mode'] in ['horizontal', 'both']:
                new_width = max(min_width, min(max_width, resize_state['start_width'] + delta_x))
                
            if resize_state['resize_mode'] in ['vertical', 'both']:
                new_height = max(min_height, min(max_height, resize_state['start_height'] + delta_y))
            
            # Apply new size
            if resize_state['resize_mode'] in ['horizontal', 'both']:
                target_frame.configure(width=new_width)
            if resize_state['resize_mode'] in ['vertical', 'both']:
                target_frame.configure(height=new_height)
                
            target_frame.grid_propagate(False)
            
            # Update visual feedback
            self.update_resize_feedback_2d(resize_state['resize_mode'], bottom_handle, right_handle, 
                                         corner_handle, new_width, new_height, min_width, max_width, 
                                         min_height, max_height)
        
        def end_drag(event):
            resize_state['resize_mode'] = None
            
            # Reset visual feedback
            bottom_handle.configure(relief='raised')
            right_handle.configure(relief='raised')
            corner_handle.configure(relief='raised')
            self.root.configure(cursor='')
            
            # Reset handle text
            self.reset_resize_feedback_2d(bottom_handle, right_handle, corner_handle)
        
        # Bind events for bottom handle (vertical resize)
        bottom_handle.bind('<Button-1>', lambda e: start_drag(e, 'vertical'))
        bottom_handle.bind('<B1-Motion>', drag_resize)
        bottom_handle.bind('<ButtonRelease-1>', end_drag)
        
        # Bind events for right handle (horizontal resize)
        right_handle.bind('<Button-1>', lambda e: start_drag(e, 'horizontal'))
        right_handle.bind('<B1-Motion>', drag_resize)
        right_handle.bind('<ButtonRelease-1>', end_drag)
        
        # Bind events for corner handle (both dimensions)
        corner_handle.bind('<Button-1>', lambda e: start_drag(e, 'both'))
        corner_handle.bind('<B1-Motion>', drag_resize)
        corner_handle.bind('<ButtonRelease-1>', end_drag)
        
        # Also bind to labels for better UX
        for handle in [bottom_handle, right_handle, corner_handle]:
            if handle.winfo_children():
                label = handle.winfo_children()[0]
                if handle == bottom_handle:
                    label.bind('<Button-1>', lambda e: start_drag(e, 'vertical'))
                elif handle == right_handle:
                    label.bind('<Button-1>', lambda e: start_drag(e, 'horizontal'))
                elif handle == corner_handle:
                    label.bind('<Button-1>', lambda e: start_drag(e, 'both'))
                label.bind('<B1-Motion>', drag_resize)
                label.bind('<ButtonRelease-1>', end_drag)
        
        # Add hover effects
        self.add_hover_effects_2d(bottom_handle, right_handle, corner_handle)
    
    def update_resize_feedback_2d(self, mode, bottom_handle, right_handle, corner_handle, 
                                 width, height, min_w, max_w, min_h, max_h):
        """Update visual feedback during 2D resize"""
        try:
            if mode in ['vertical', 'both']:
                bottom_label = bottom_handle.winfo_children()[0] if bottom_handle.winfo_children() else None
                if bottom_label:
                    if height <= min_h:
                        color = 'red'
                        status = "MIN HEIGHT"
                    elif height >= max_h:
                        color = 'orange'
                        status = "MAX HEIGHT"
                    else:
                        color = 'green'
                        status = "HEIGHT"
                    bottom_label.configure(text=f"═══ {status}: {height}px ═══", foreground=color)
            
            if mode in ['horizontal', 'both']:
                right_label = right_handle.winfo_children()[0] if right_handle.winfo_children() else None
                if right_label:
                    if width <= min_w:
                        color = 'red'
                        status = "MIN"
                    elif width >= max_w:
                        color = 'orange'
                        status = "MAX"
                    else:
                        color = 'green'
                        status = "W"
                    right_label.configure(text=f"║\n{status}\n{width}px\n║", foreground=color)
            
            if mode == 'both':
                corner_label = corner_handle.winfo_children()[0] if corner_handle.winfo_children() else None
                if corner_label:
                    w_status = "MIN" if width <= min_w else "MAX" if width >= max_w else "OK"
                    h_status = "MIN" if height <= min_h else "MAX" if height >= max_h else "OK"
                    color = 'red' if 'MIN' in [w_status, h_status] else 'orange' if 'MAX' in [w_status, h_status] else 'green'
                    corner_label.configure(text=f"◢\n{width}×{height}", foreground=color)
        except:
            pass
    
    def reset_resize_feedback_2d(self, bottom_handle, right_handle, corner_handle):
        """Reset visual feedback after resize"""
        try:
            bottom_label = bottom_handle.winfo_children()[0] if bottom_handle.winfo_children() else None
            if bottom_label:
                bottom_label.configure(text="═══ Drag to Resize Height ═══", foreground='blue')
                
            right_label = right_handle.winfo_children()[0] if right_handle.winfo_children() else None
            if right_label:
                right_label.configure(text="║", foreground='blue')
                
            corner_label = corner_handle.winfo_children()[0] if corner_handle.winfo_children() else None
            if corner_label:
                corner_label.configure(text="◢", foreground='purple')
        except:
            pass
    
    def add_hover_effects_2d(self, bottom_handle, right_handle, corner_handle):
        """Add hover effects for 2D resize handles"""
        def create_hover_handlers(handle, hover_color, normal_color):
            def on_enter(event):
                handle.configure(relief='ridge')
                if handle.winfo_children():
                    label = handle.winfo_children()[0]
                    label.configure(foreground=hover_color)
            
            def on_leave(event):
                handle.configure(relief='raised')
                if handle.winfo_children():
                    label = handle.winfo_children()[0]
                    label.configure(foreground=normal_color)
            
            return on_enter, on_leave
        
        # Add hover effects for each handle
        enter_bottom, leave_bottom = create_hover_handlers(bottom_handle, 'darkblue', 'blue')
        bottom_handle.bind('<Enter>', enter_bottom)
        bottom_handle.bind('<Leave>', leave_bottom)
        
        enter_right, leave_right = create_hover_handlers(right_handle, 'darkblue', 'blue')
        right_handle.bind('<Enter>', enter_right)
        right_handle.bind('<Leave>', leave_right)
        
        enter_corner, leave_corner = create_hover_handlers(corner_handle, 'darkmagenta', 'purple')
        corner_handle.bind('<Enter>', enter_corner)
        corner_handle.bind('<Leave>', leave_corner)
    
    def resize_frame_by_delta_2d(self, frame, height_delta=0, width_delta=0):
        """Resize frame by specific amounts in both dimensions"""
        current_height = frame.winfo_height()
        current_width = frame.winfo_width()
        
        min_height = getattr(frame, '_min_height', 200)
        max_height = getattr(frame, '_max_height', 800)
        min_width = getattr(frame, '_min_width', 400)
        max_width = getattr(frame, '_max_width', 1200)
        
        new_height = max(min_height, min(max_height, current_height + height_delta))
        new_width = max(min_width, min(max_width, current_width + width_delta))
        
        frame.configure(height=new_height, width=new_width)
        frame.grid_propagate(False)
    
    def auto_fit_frame_2d(self, container, data_frame):
        """Auto-fit frame to content in both dimensions"""
        try:
            data_frame.update_idletasks()
            
            # Find content widget
            content_widget = None
            for child in data_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, (ttk.Treeview, tk.Text)):
                            content_widget = grandchild
                            break
                elif isinstance(child, (ttk.Treeview, tk.Text)):
                    content_widget = child
                    break
            
            if content_widget:
                min_height = getattr(container, '_min_height', 200)
                max_height = getattr(container, '_max_height', 800)
                min_width = getattr(container, '_min_width', 400)
                max_width = getattr(container, '_max_width', 1200)
                
                if isinstance(content_widget, ttk.Treeview):
                    # Calculate optimal dimensions for treeview
                    row_count = len(content_widget.get_children())
                    row_height = 25
                    header_height = 30
                    optimal_height = min(max_height, max(min_height, row_count * row_height + header_height + 80))
                    
                    # Calculate width based on column content
                    total_width = 0
                    for col in content_widget['columns']:
                        total_width += content_widget.column(col, 'width')
                    optimal_width = min(max_width, max(min_width, total_width + 50))
                else:
                    # For text widget, use reasonable defaults
                    optimal_height = min(max_height, max(min_height, 300))
                    optimal_width = min(max_width, max(min_width, 600))
                
                container.configure(height=optimal_height, width=optimal_width)
                container.grid_propagate(False)
                
        except Exception as e:
            print(f"Error auto-fitting frame: {e}")
            # Fallback to default sizes
            default_height = getattr(container, '_initial_height', 400)
            default_width = getattr(container, '_initial_width', 800)
            container.configure(height=default_height, width=default_width)
            container.grid_propagate(False)
    
    def reset_frame_size_2d(self, frame, default_height, default_width):
        """Reset frame to default size in both dimensions"""
        frame.configure(height=default_height, width=default_width)
        frame.grid_propagate(False)
    
    def resize_frame_by_delta(self, frame, delta):
        """Resize frame by a specific amount"""
        current_height = frame.winfo_height()
        min_height = getattr(frame, '_min_height', 200)
        max_height = getattr(frame, '_max_height', 800)
        
        new_height = max(min_height, min(max_height, current_height + delta))
        frame.configure(height=new_height)
        frame.grid_propagate(False)
    
    def auto_fit_frame(self, container, data_frame):
        """Auto-fit frame to content"""
        try:
            # Update to get current content size
            data_frame.update_idletasks()
            
            # Find treeview or text widget in data_frame
            content_widget = None
            for child in data_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, (ttk.Treeview, tk.Text)):
                            content_widget = grandchild
                            break
                elif isinstance(child, (ttk.Treeview, tk.Text)):
                    content_widget = child
                    break
            
            if content_widget:
                min_height = getattr(container, '_min_height', 200)
                max_height = getattr(container, '_max_height', 800)
                
                if isinstance(content_widget, ttk.Treeview):
                    # For treeview, calculate based on visible items
                    row_count = len(content_widget.get_children())
                    row_height = 25  # Approximate row height
                    header_height = 30
                    optimal_height = min(max_height, max(min_height, row_count * row_height + header_height + 60))
                else:
                    # For text widget, use a reasonable size
                    optimal_height = min(max_height, max(min_height, 300))
                
                container.configure(height=optimal_height)
                container.grid_propagate(False)
                
        except Exception as e:
            print(f"Error auto-fitting frame: {e}")
            # Fallback to default size
            default_height = getattr(container, '_initial_height', 400)
            container.configure(height=default_height)
            container.grid_propagate(False)
    
    def make_frame_resizable(self, handle, target_frame, min_height):
        """Make a frame resizable by dragging a handle"""
        start_y = None
        start_height = None
        
        def start_drag(event):
            nonlocal start_y, start_height
            start_y = event.y_root
            start_height = target_frame.winfo_height()
            handle.configure(relief='sunken')
            # Change cursor for visual feedback
            self.root.configure(cursor='sb_v_double_arrow')
        
        def drag_resize(event):
            nonlocal start_y, start_height
            if start_y is not None:
                delta_y = event.y_root - start_y
                max_height = getattr(target_frame, '_max_height', min_height * 4)
                new_height = max(min_height, min(max_height, start_height + delta_y))
                
                # Update frame size
                target_frame.configure(height=new_height)
                target_frame.grid_propagate(False)  # Prevent automatic resizing
                
                # Visual feedback with color coding
                handle_label = handle.winfo_children()[0] if handle.winfo_children() else None
                if handle_label:
                    if new_height <= min_height:
                        color = 'red'
                        status = "MIN"
                    elif new_height >= max_height:
                        color = 'orange'
                        status = "MAX"
                    else:
                        color = 'green'
                        status = "SIZE"
                    
                    handle_label.configure(
                        text=f"═══ {status}: {new_height}px ═══",
                        foreground=color
                    )
        
        def end_drag(event):
            nonlocal start_y, start_height
            start_y = None
            start_height = None
            handle.configure(relief='raised')
            # Reset cursor
            self.root.configure(cursor='')
            
            # Reset handle text and color
            handle_label = handle.winfo_children()[0] if handle.winfo_children() else None
            if handle_label:
                handle_label.configure(text="═══ Drag to Resize ═══", foreground='blue')
            
            # Update the UI
            self.root.update_idletasks()
        
        # Bind drag events
        handle.bind('<Button-1>', start_drag)
        handle.bind('<B1-Motion>', drag_resize)
        handle.bind('<ButtonRelease-1>', end_drag)
        
        # Also bind to the label for better UX
        if handle.winfo_children():
            label = handle.winfo_children()[0]
            label.bind('<Button-1>', start_drag)
            label.bind('<B1-Motion>', drag_resize)
            label.bind('<ButtonRelease-1>', end_drag)
        
        # Add hover effects
        def on_enter(event):
            handle.configure(relief='ridge')
            if handle.winfo_children():
                label = handle.winfo_children()[0]
                label.configure(foreground='darkblue')
        
        def on_leave(event):
            if start_y is None:  # Only if not dragging
                handle.configure(relief='raised')
                if handle.winfo_children():
                    label = handle.winfo_children()[0]
                    label.configure(foreground='blue')
        
        handle.bind('<Enter>', on_enter)
        handle.bind('<Leave>', on_leave)
        if handle.winfo_children():
            label = handle.winfo_children()[0]
            label.bind('<Enter>', on_enter)
            label.bind('<Leave>', on_leave)
    
    def reset_frame_size(self, frame, default_height):
        """Reset frame to default size"""
        frame.configure(height=default_height)
        frame.grid_propagate(False)
    
    def create_widgets(self):
        # Add theme toggle logos at the top center
        if PIL_AVAILABLE:
            try:
                # Try different possible image paths and extensions
                possible_paths = [
                    # Try different extensions for light mode logo
                    ("lightmode-logo.jpg", "darkmode-logo.jpg"),
                    ("lightmode-logo.png", "darkmode-logo.png"),
                    ("light-logo.jpg", "dark-logo.jpg"),
                    ("light-logo.png", "dark-logo.png")
                ]
                
                light_image = None
                dark_image = None
                
                # Try to find existing image files
                for light_name, dark_name in possible_paths:
                    try:
                        lightmode_logo_path = os.path.join(os.path.dirname(__file__), "images", light_name)
                        darkmode_logo_path = os.path.join(os.path.dirname(__file__), "images", dark_name)
                        
                        if os.path.exists(lightmode_logo_path) and os.path.exists(darkmode_logo_path):
                            light_image = Image.open(lightmode_logo_path)
                            dark_image = Image.open(darkmode_logo_path)
                            print(f"Successfully loaded theme logos: {light_name}, {dark_name}")
                            break
                    except Exception as e:
                        print(f"Failed to load {light_name}/{dark_name}: {e}")
                        continue
                
                if light_image and dark_image:
                    # Resize logos to fit nicely (adjust size as needed)
                    light_image = light_image.resize((80, 60), Image.Resampling.LANCZOS)
                    dark_image = dark_image.resize((80, 60), Image.Resampling.LANCZOS)
                    
                    self.light_logo = ImageTk.PhotoImage(light_image)
                    self.dark_logo = ImageTk.PhotoImage(dark_image)
                    
                    # Create logo frame at the top
                    logo_frame = create_frame(self.root)
                    logo_frame.pack(pady=10)
                    
                    # Create frame for the two logos side by side
                    logos_container = create_frame(logo_frame)
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
                    title_label = create_label(logo_frame, text="Osmosis Data Processor")
                    if CTK_AVAILABLE:
                        title_label.configure(font=ctk.CTkFont(size=16, weight="bold"))
                    else:
                        title_label.configure(font=('Arial', 16, 'bold'), foreground='#0071c5')
                    title_label.pack(pady=(10, 5))
                    
                    # Add zoom controls
                    zoom_frame = create_frame(logo_frame)
                    zoom_frame.pack(pady=5)
                    
                    zoom_label_widget = create_label(zoom_frame, text="Zoom:")
                    if not CTK_AVAILABLE:
                        zoom_label_widget.configure(font=('Arial', 9))
                    zoom_label_widget.pack(side='left', padx=(0, 5))
                    
                    zoom_out_btn = create_button(zoom_frame, text="🔍−", command=self.zoom_out)
                    if not CTK_AVAILABLE:
                        zoom_out_btn.configure(width=4)
                    zoom_out_btn.pack(side='left', padx=2)
                    
                    self.zoom_label = create_label(zoom_frame, text=f"{int(self.current_zoom_level * 100)}%")
                    if CTK_AVAILABLE:
                        self.zoom_label.configure(font=ctk.CTkFont(weight="bold"))
                    else:
                        self.zoom_label.configure(font=('Arial', 9, 'bold'), foreground='blue', width=5)
                    self.zoom_label.pack(side='left', padx=5)
                    
                    zoom_in_btn = create_button(zoom_frame, text="🔍+", command=self.zoom_in)
                    if not CTK_AVAILABLE:
                        zoom_in_btn.configure(width=4)
                    zoom_in_btn.pack(side='left', padx=2)
                    
                    clear_btn = create_button(zoom_frame, text="Clear", command=self.clear_all_values)
                    if not CTK_AVAILABLE:
                        clear_btn.configure(width=6)
                    clear_btn.pack(side='left', padx=(10, 0))
                    
                    # Add theme indicator
                    self.theme_label = create_label(logo_frame, text="Light Mode")
                    if not CTK_AVAILABLE:
                        self.theme_label.configure(font=('Arial', 10), foreground='gray')
                    self.theme_label.pack()
                else:
                    print("Could not find theme logo images, using fallback")
                    self.create_fallback_title()
                
            except Exception as e:
                print(f"Could not load theme logos: {e}")
                # Fallback to text-only title
                self.create_fallback_title()
        else:
            # Fallback to text-only title when PIL is not available
            self.create_fallback_title()
        
        # Create notebook for tabs (this should always be created)
        notebook = create_notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=16, pady=16)  # Increased padding
        
        # Tab 1: Material Data Input
        self.material_frame = create_frame(notebook)
        notebook.add(self.material_frame, text="📊 Material Data")  # Added icon
        self.create_material_tab()
        
        # Tab 2: MTPL and Test Selection
        self.mtpl_frame = create_frame(notebook)
        notebook.add(self.mtpl_frame, text="🧪 MTPL & Test Selection")  # Added icon
        self.create_mtpl_tab()
        
        # Tab 3: CLKUtils Test Input
        self.clkutils_frame = create_frame(notebook)
        notebook.add(self.clkutils_frame, text="⏰ CLKUtils Tests")  # Added icon
        self.create_clkutils_tab()
        
        # Tab 4: Output Settings and Processing
        self.output_frame = create_frame(notebook)
        notebook.add(self.output_frame, text="⚙️ Output & Processing")  # Added icon
        self.create_output_tab()
        
        # Apply enhancements
        self.enhance_visual_feedback()
        self.apply_enhanced_spacing()
        
        # Configure initial treeview colors
        self.configure_treeview_alternating_colors()
        
    def create_fallback_title(self):
        """Create a simple text-only title when images are not available"""
        title_frame = create_frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = create_label(title_frame, text="Osmosis Data Processor")
        if CTK_AVAILABLE:
            title_label.configure(font=ctk.CTkFont(size=16, weight="bold"))
        else:
            title_label.configure(font=('Arial', 16, 'bold'))
        title_label.pack()
        
        # Create simple theme toggle buttons
        theme_frame = create_frame(title_frame)
        theme_frame.pack(pady=5)
        
        create_button(theme_frame, text="Light Mode", command=self.switch_to_light_mode).pack(side='left', padx=5)
        create_button(theme_frame, text="Dark Mode", command=self.switch_to_dark_mode).pack(side='left', padx=5)
        
        # Add zoom controls
        zoom_frame = create_frame(title_frame)
        zoom_frame.pack(pady=5)
        
        zoom_label_widget = create_label(zoom_frame, text="Zoom:")
        if not CTK_AVAILABLE:
            zoom_label_widget.configure(font=('Arial', 9))
        zoom_label_widget.pack(side='left', padx=(0, 5))
        
        zoom_out_btn = create_button(zoom_frame, text="🔍−", command=self.zoom_out)
        if not CTK_AVAILABLE:
            zoom_out_btn.configure(width=4)
        zoom_out_btn.pack(side='left', padx=2)
        
        self.zoom_label = create_label(zoom_frame, text=f"{int(self.current_zoom_level * 100)}%")
        if CTK_AVAILABLE:
            self.zoom_label.configure(font=ctk.CTkFont(weight="bold"))
        else:
            self.zoom_label.configure(font=('Arial', 9, 'bold'), foreground='blue', width=5)
        self.zoom_label.pack(side='left', padx=5)
        
        zoom_in_btn = create_button(zoom_frame, text="🔍+", command=self.zoom_in)
        if not CTK_AVAILABLE:
            zoom_in_btn.configure(width=4)
        zoom_in_btn.pack(side='left', padx=2)
        
        clear_btn = create_button(zoom_frame, text="Clear", command=self.clear_all_values)
        if not CTK_AVAILABLE:
            clear_btn.configure(width=6)
        clear_btn.pack(side='left', padx=(10, 0))
        
        # Add theme indicator
        self.theme_label = create_label(title_frame, text="Light Mode")
        if not CTK_AVAILABLE:
            self.theme_label.configure(font=('Arial', 10), foreground='gray')
        self.theme_label.pack()
        
    def create_material_tab(self):
        # Create a canvas and scrollbar for scrollable content
        material_canvas = tk.Canvas(self.material_frame, highlightthickness=0)
        material_scrollbar = ttk.Scrollbar(self.material_frame, orient="vertical", command=material_canvas.yview)
        self.material_scrollable_frame = ttk.Frame(material_canvas)
        
        # Configure scrolling
        self.material_scrollable_frame.bind(
            "<Configure>",
            lambda e: material_canvas.configure(scrollregion=material_canvas.bbox("all"))
        )
        
        material_canvas.create_window((0, 0), window=self.material_scrollable_frame, anchor="nw")
        material_canvas.configure(yscrollcommand=material_scrollbar.set)
        
        # Pack the canvas and scrollbar
        material_canvas.pack(side="left", fill="both", expand=True)
        material_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas for smooth scrolling
        def _on_material_mousewheel(event):
            material_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_material_mousewheel(event):
            material_canvas.bind_all("<MouseWheel>", _on_material_mousewheel)
        
        def _unbind_from_material_mousewheel(event):
            material_canvas.unbind_all("<MouseWheel>")
        
        material_canvas.bind('<Enter>', _bind_to_material_mousewheel)
        material_canvas.bind('<Leave>', _unbind_from_material_mousewheel)
        
        # Now create all the content in the scrollable_frame instead of self.material_frame
        # Material Data Input Section
        ttk.Label(self.material_scrollable_frame, text="Material Data Input", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Input fields frame - stretch with consistent margins
        input_frame = ttk.LabelFrame(self.material_scrollable_frame, text="Enter Material Parameters")
        input_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Configure input_frame to expand with window
        input_frame.grid_columnconfigure(1, weight=1)
        
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
            ttk.Entry(input_frame, textvariable=var).grid(row=i, column=1, padx=10, pady=5, sticky='ew')  # Remove fixed width, use sticky='ew'
        
        # Buttons frame
        button_frame = ttk.Frame(self.material_scrollable_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Load from CSV/Excel", command=self.load_material_file).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Create DataFrame", command=self.create_material_dataframe).pack(side='left', padx=10)
        
        # Display frame for material data using resizable frame - stretch with consistent margins
        data_frame = self.create_resizable_data_frame(
            self.material_scrollable_frame, 
            "Current Material Data", 
            min_height=150, 
            default_height=300
        )
        
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(data_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)  # Add padding inside the data frame
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for displaying material data
        self.material_tree = ttk.Treeview(tree_frame, height=10)
        self.material_tree.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbars with proper grid placement
        material_v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.material_tree.yview)
        material_v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.material_tree.configure(yscrollcommand=material_v_scrollbar.set)
        
        material_h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.material_tree.xview)
        material_h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.material_tree.configure(xscrollcommand=material_h_scrollbar.set)
        
    def create_mtpl_tab(self):
        # Create a canvas and scrollbar for scrollable content
        canvas = tk.Canvas(self.mtpl_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.mtpl_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas for smooth scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Now create all the content in the scrollable_frame instead of self.mtpl_frame
        ttk.Label(scrollable_frame, text="MTPL File and Test Selection", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # MTPL file loading - stretch with consistent margins
        mtpl_load_frame = ttk.LabelFrame(scrollable_frame, text="Load MTPL File")
        mtpl_load_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Configure grid weights for responsive design
        mtpl_load_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(mtpl_load_frame, text="MTPL File Path:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(mtpl_load_frame, textvariable=self.mtpl_file_path).grid(row=0, column=1, padx=10, pady=5, sticky='ew')  # Remove fixed width, use sticky='ew'
        ttk.Button(mtpl_load_frame, text="Browse", command=self.browse_mtpl_file).grid(row=0, column=2, padx=10, pady=5)
        # Place both Load and Reload buttons inside button_frame, and grid button_frame properly
        button_frame = ttk.Frame(mtpl_load_frame)
        button_frame.grid(row=1, column=1, columnspan=2, pady=10, sticky='w')
        load_btn = ttk.Button(button_frame, text="Load MTPL", command=self.load_mtpl_file)
        load_btn.pack(side='left', padx=(0, 5))
        self.reload_mtpl_button = ttk.Button(button_frame, text="🔄 Reload Last", command=self.reload_mtpl_file, state='disabled')
        self.reload_mtpl_button.pack(side='left')

        
        # MTPL file info label
        self.mtpl_info_label = ttk.Label(mtpl_load_frame, text="Select an MTPL file for processing", 
                                        foreground='gray')
        self.mtpl_info_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Enhanced Search and Filter Controls (separate from data display) - stretch with consistent margins
        filter_control_frame = ttk.LabelFrame(scrollable_frame, text="🔍 Search & Filter Controls")
        filter_control_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Top row: Search and main controls
        top_filter_row = ttk.Frame(filter_control_frame)
        top_filter_row.pack(fill='x', padx=10, pady=5)
        
        # Search section with icon
        search_section = ttk.Frame(top_filter_row)
        search_section.pack(side='left', fill='x', expand=True)
        
        ttk.Label(search_section, text="🔍 Quick Search:", font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_section, textvariable=self.search_var, width=35, font=('Arial', 9))
        search_entry.pack(side='left', padx=(0, 10))
        search_entry.bind('<Return>', lambda e: self.apply_all_filters())
        
        # Control buttons
        control_section = ttk.Frame(top_filter_row)
        control_section.pack(side='right')
        
        ttk.Button(control_section, text="🗑️ Clear All", command=self.clear_all_filters, width=12).pack(side='left', padx=(0, 5))
        ttk.Button(control_section, text="🔄 Refresh", command=self.refresh_filters, width=12).pack(side='left', padx=(0, 5))
        ttk.Button(control_section, text="🎯 Clear Auto-Filter", command=self.clear_automatic_filter, width=15).pack(side='left', padx=(0, 5))
        self.toggle_filters_btn = ttk.Button(control_section, text="▼ Show Filters", command=self.toggle_column_filters, width=15)
        self.toggle_filters_btn.pack(side='left')
        
        # Filter status row
        status_row = ttk.Frame(filter_control_frame)
        status_row.pack(fill='x', padx=10, pady=(0, 5))
        
        self.filter_status_label = ttk.Label(status_row, text="", font=('Arial', 9), foreground='blue')
        self.filter_status_label.pack(side='left')
        
        # Active filters display
        self.active_filters_label = ttk.Label(status_row, text="", font=('Arial', 8), foreground='orange')
        self.active_filters_label.pack(side='right')
        
        # Collapsible Column filters frame (part of controls)
        self.column_filters_frame = ttk.LabelFrame(scrollable_frame, text="📋 Advanced Column Filters")
        self.column_filters_visible = False  # Start collapsed
        
        # Initialize column filter variables
        self.column_filters = {}
        self.column_filter_combos = {}
        
        # MTPL data display using resizable frame
        mtpl_data_frame = self.create_resizable_data_frame(
            scrollable_frame, 
            "MTPL Data", 
            min_height=200, 
            default_height=450
        )
        
        # Create frame for treeview and scrollbars
        mtpl_tree_frame = ttk.Frame(mtpl_data_frame)
        mtpl_tree_frame.pack(fill='both', expand=True)
        mtpl_tree_frame.grid_rowconfigure(0, weight=1)
        mtpl_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for MTPL data
        self.mtpl_tree = ttk.Treeview(mtpl_tree_frame, height=15)
        self.mtpl_tree.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbars with proper grid placement
        mtpl_v_scrollbar = ttk.Scrollbar(mtpl_tree_frame, orient='vertical', command=self.mtpl_tree.yview)
        mtpl_v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.mtpl_tree.configure(yscrollcommand=mtpl_v_scrollbar.set)
        
        mtpl_h_scrollbar = ttk.Scrollbar(mtpl_tree_frame, orient='horizontal', command=self.mtpl_tree.xview)
        mtpl_h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.mtpl_tree.configure(xscrollcommand=mtpl_h_scrollbar.set)
        
        # Add mouse wheel support for the treeview
        def _on_treeview_mousewheel(event):
            self.mtpl_tree.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.mtpl_tree.bind("<MouseWheel>", _on_treeview_mousewheel)
        
        # Bind click events for test selection
        self.mtpl_tree.bind('<Double-1>', self.toggle_test_selection)
        self.mtpl_tree.bind('<Button-1>', self.on_treeview_click)
        
        # Enhanced Test Selection and Management - stretch with consistent margins
        test_management_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Test Selection & Management")
        test_management_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Selection controls row
        selection_row = ttk.Frame(test_management_frame)
        selection_row.pack(fill='x', padx=10, pady=5)
        
        # Left side: Basic selection controls
        basic_controls = ttk.Frame(selection_row)
        basic_controls.pack(side='left')
        
        ttk.Button(basic_controls, text="☑️ Select All Visible", command=self.select_all_visible_tests, width=18).pack(side='left', padx=(0, 5))
        ttk.Button(basic_controls, text="☐ Clear All", command=self.clear_test_selection, width=12).pack(side='left', padx=(0, 10))
        
        # Selection info
        info_frame = ttk.Frame(basic_controls)
        info_frame.pack(side='left', padx=(10, 0))
        ttk.Label(info_frame, text="Selected:", font=('Arial', 9, 'bold')).pack(side='left')
        self.selected_tests_label = ttk.Label(info_frame, text="0", font=('Arial', 10, 'bold'), foreground='blue')
        self.selected_tests_label.pack(side='left', padx=(5, 0))
        
        # Right side: Advanced controls
        advanced_controls = ttk.Frame(selection_row)
        advanced_controls.pack(side='right')
        
        ttk.Button(advanced_controls, text="↕️ Reorder Tests", command=self.open_reorder_window, width=15).pack(side='left', padx=(0, 5))
        ttk.Button(advanced_controls, text="🔄 Invert Selection", command=self.invert_selection, width=15).pack(side='left')
        
        # Export controls row
        export_row = ttk.Frame(test_management_frame)
        export_row.pack(fill='x', padx=10, pady=(5, 10))
        
        ttk.Label(export_row, text="📤 Export Options:", font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 10))
        ttk.Button(export_row, text="📋 Selected Tests", command=self.export_selected_tests, width=15).pack(side='left', padx=(0, 5))
        ttk.Button(export_row, text="📊 Visible Tests", command=self.export_visible_tests, width=15).pack(side='left', padx=(0, 5))
        ttk.Button(export_row, text="📄 All Tests", command=self.export_all_tests, width=12).pack(side='left', padx=(0, 5))
        
        # Test order display (when reordering is active)
        self.order_info_frame = ttk.Frame(test_management_frame)
        self.order_info_label = ttk.Label(self.order_info_frame, text="", font=('Arial', 8), foreground='green')
        self.order_info_label.pack()
        
    def create_clkutils_tab(self):
        """Create the CLKUtils test input tab with scrollable functionality"""
        # Create a canvas and scrollbar for scrollable content
        clkutils_canvas = tk.Canvas(self.clkutils_frame, highlightthickness=0)
        clkutils_scrollbar = ttk.Scrollbar(self.clkutils_frame, orient="vertical", command=clkutils_canvas.yview)
        self.clkutils_scrollable_frame = ttk.Frame(clkutils_canvas)
        
        # Configure scrolling
        self.clkutils_scrollable_frame.bind(
            "<Configure>",
            lambda e: clkutils_canvas.configure(scrollregion=clkutils_canvas.bbox("all"))
        )
        
        clkutils_canvas.create_window((0, 0), window=self.clkutils_scrollable_frame, anchor="nw")
        clkutils_canvas.configure(yscrollcommand=clkutils_scrollbar.set)
        
        # Pack the canvas and scrollbar
        clkutils_canvas.pack(side="left", fill="both", expand=True)
        clkutils_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas for smooth scrolling
        def _on_clkutils_mousewheel(event):
            clkutils_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_clkutils_mousewheel(event):
            clkutils_canvas.bind_all("<MouseWheel>", _on_clkutils_mousewheel)
        
        def _unbind_from_clkutils_mousewheel(event):
            clkutils_canvas.unbind_all("<MouseWheel>")
        
        clkutils_canvas.bind('<Enter>', _bind_to_clkutils_mousewheel)
        clkutils_canvas.bind('<Leave>', _unbind_from_clkutils_mousewheel)
        
        # Now create all the content in the scrollable_frame
        ttk.Label(self.clkutils_scrollable_frame, text="CLKUtils Test Input", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Instructions - stretch with consistent margins
        instruction_frame = ttk.LabelFrame(self.clkutils_scrollable_frame, text="Instructions")
        instruction_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        instruction_text = ("CLKUtils tests do not require MTPL files. You can input test names from:\n"
                          "• CSV file (select a column containing test names)\n"
                          "• Text file (comma, whitespace, or newline-separated test names)\n"
                          "• Manual text input (comma, whitespace, or newline-separated)")
        ttk.Label(instruction_frame, text=instruction_text, wraplength=600, justify='left').pack(padx=10, pady=10)
        
        # Input method selection - stretch with consistent margins
        method_frame = ttk.LabelFrame(self.clkutils_scrollable_frame, text="Test Input Method")
        method_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        self.clkutils_input_method = tk.StringVar(value="csv")
        ttk.Radiobutton(method_frame, text="📊 From CSV file (select column)", 
                       variable=self.clkutils_input_method, value="csv").pack(anchor='w', padx=10, pady=5)
        ttk.Radiobutton(method_frame, text="📄 From text file (comma, whitespace, or newline separated)", 
                       variable=self.clkutils_input_method, value="txt").pack(anchor='w', padx=10, pady=5)
        ttk.Radiobutton(method_frame, text="✏️ Manual text input", 
                       variable=self.clkutils_input_method, value="manual").pack(anchor='w', padx=10, pady=5)
        
        # File input section - stretch with consistent margins
        file_input_frame = ttk.LabelFrame(self.clkutils_scrollable_frame, text="File Input")
        file_input_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Configure grid weights for responsive design
        file_input_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(file_input_frame, text="File Path:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(file_input_frame, textvariable=self.clkutils_file_path).grid(row=0, column=1, padx=10, pady=5, sticky='ew')  # Remove fixed width, use sticky='ew'
        ttk.Button(file_input_frame, text="Browse", command=self.browse_clkutils_file).grid(row=0, column=2, padx=10, pady=5)
        
        # CSV column selection (only shown when CSV is selected)
        self.csv_column_frame = ttk.Frame(file_input_frame)
        # Don't grid it initially - let the method change handler manage it
        
        ttk.Label(self.csv_column_frame, text="Select Column:").grid(row=0, column=0, sticky='w', padx=(0, 5), pady=5)
        self.clkutils_column_var = tk.StringVar()
        self.clkutils_column_combo = ttk.Combobox(self.csv_column_frame, textvariable=self.clkutils_column_var, 
                                                  state="readonly", width=20)
        self.clkutils_column_combo.grid(row=0, column=1, padx=(0, 10), pady=5)
        
        ttk.Button(file_input_frame, text="Load Tests from File", command=self.load_clkutils_from_file).grid(row=2, column=1, pady=10)
        
        # Manual input section - stretch with consistent margins
        manual_input_frame = ttk.LabelFrame(self.clkutils_scrollable_frame, text="Manual Test Input")
        manual_input_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        ttk.Label(manual_input_frame, text="Enter test names (comma, whitespace, or newline separated):").pack(anchor='w', padx=10, pady=(10, 5))
        
        # Text area for manual input
        text_frame = ttk.Frame(manual_input_frame)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.clkutils_text_input = tk.Text(text_frame, height=6)  # Remove fixed width
        self.clkutils_text_input.pack(side='left', fill='both', expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.clkutils_text_input.yview)
        text_scrollbar.pack(side='right', fill='y')
        self.clkutils_text_input.configure(yscrollcommand=text_scrollbar.set)
        
        # Buttons for manual input
        manual_buttons_frame = ttk.Frame(manual_input_frame)
        manual_buttons_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(manual_buttons_frame, text="Load Tests from Text", command=self.load_clkutils_from_text).pack(side='left', padx=(0, 10))
        ttk.Button(manual_buttons_frame, text="Clear Text", command=lambda: self.clkutils_text_input.delete('1.0', tk.END)).pack(side='left')
        
        # CLKUtils test controls (separate from data display) - stretch with consistent margins
        control_frame = ttk.LabelFrame(self.clkutils_scrollable_frame, text="🔍 Search & Controls")
        control_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Search and filter controls
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="🔍 Search:").pack(side='left', padx=(0, 5))
        self.clkutils_search_var = tk.StringVar()
        self.clkutils_search_var.trace('w', self.on_clkutils_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.clkutils_search_var, width=30)
        search_entry.pack(side='left', padx=(0, 10))
        
        # Control buttons
        control_buttons_frame = ttk.Frame(search_frame)
        control_buttons_frame.pack(side='right')
        
        ttk.Button(control_buttons_frame, text="☑️ Select All", command=self.select_all_clkutils_tests).pack(side='left', padx=(0, 5))
        ttk.Button(control_buttons_frame, text="☐ Clear All", command=self.clear_all_clkutils_tests).pack(side='left', padx=(0, 5))
        ttk.Button(control_buttons_frame, text="🗑️ Remove Selected", command=self.remove_selected_clkutils_tests).pack(side='left')
        
        # CLKUtils test display using resizable frame
        clkutils_data_frame = self.create_resizable_data_frame(
            self.clkutils_scrollable_frame, 
            "CLKUtils Tests", 
            min_height=180, 
            default_height=350
        )
        
        # Test list display
        list_frame = ttk.Frame(clkutils_data_frame)
        list_frame.pack(fill='both', expand=True)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Treeview for CLKUtils tests
        self.clkutils_tree = ttk.Treeview(list_frame, columns=('Test Name',), show='tree headings', height=12)
        self.clkutils_tree.grid(row=0, column=0, sticky='nsew')
        
        # Configure columns
        self.clkutils_tree.heading('#0', text='☐', anchor='w')
        self.clkutils_tree.heading('Test Name', text='Test Name', anchor='w')
        self.clkutils_tree.column('#0', width=50, minwidth=50)
        self.clkutils_tree.column('Test Name', width=400, minwidth=200)
        
        # Scrollbars
        clkutils_v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.clkutils_tree.yview)
        clkutils_v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.clkutils_tree.configure(yscrollcommand=clkutils_v_scrollbar.set)
        
        clkutils_h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.clkutils_tree.xview)
        clkutils_h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.clkutils_tree.configure(xscrollcommand=clkutils_h_scrollbar.set)
        
        # Add mouse wheel support for the treeview
        def _on_clkutils_mousewheel(event):
            self.clkutils_tree.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.clkutils_tree.bind("<MouseWheel>", _on_clkutils_mousewheel)
        
        # Bind events
        self.clkutils_tree.bind('<Button-1>', self.on_clkutils_tree_click)
        self.clkutils_tree.bind('<Double-1>', self.toggle_clkutils_selection)
        
        # Selection status (separate frame) - stretch with consistent margins
        status_frame = ttk.Frame(self.clkutils_scrollable_frame)
        status_frame.pack(fill='x', padx=(20, 40), pady=(5, 10))  # Right margin accounts for scrollbar
        
        ttk.Label(status_frame, text="Selected CLKUtils Tests:", font=('Arial', 9, 'bold')).pack(side='left')
        self.clkutils_selected_label = ttk.Label(status_frame, text="0", font=('Arial', 10, 'bold'), foreground='blue')
        self.clkutils_selected_label.pack(side='left', padx=(5, 0))
        
        # Update input method visibility
        self.clkutils_input_method.trace('w', self.on_clkutils_method_change)
        self.on_clkutils_method_change()  # Initial setup
    
    def browse_clkutils_file(self):
        """Browse for CLKUtils input file (CSV or TXT)"""
        filetypes = [
            ("CSV files", "*.csv"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Select CLKUtils Test File", filetypes=filetypes)
        if file_path:
            # Normalize the file path to handle UNC paths and strip quotes
            normalized_path = self.normalize_unc_path(file_path)
            self.clkutils_file_path.set(normalized_path)
            # If CSV file, load column options
            if normalized_path.lower().endswith('.csv'):
                self.load_csv_columns()
    
    def load_csv_columns(self):
        """Load column names from CSV file for selection"""
        try:
            csv_path = self.clkutils_file_path.get()
            if csv_path and csv_path.lower().endswith('.csv'):
                df = pd.read_csv(csv_path)
                columns = list(df.columns)
                self.clkutils_column_combo['values'] = columns
                if columns:
                    self.clkutils_column_combo.set(columns[0])  # Select first column by default
                self.log_message(f"Loaded {len(columns)} columns from CSV file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV columns: {str(e)}")
            self.log_message(f"Error loading CSV columns: {str(e)}")
    
    def on_clkutils_method_change(self, *args):
        """Handle input method change"""
        method = self.clkutils_input_method.get()
        # Show/hide CSV column selection based on method
        if method == "csv":
            self.csv_column_frame.grid(row=1, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        else:
            self.csv_column_frame.grid_remove()
    
    def load_clkutils_from_file(self):
        """Load CLKUtils tests from selected file"""
        file_path = self.clkutils_file_path.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file first")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
        
        try:
            method = self.clkutils_input_method.get()
            tests = []
            
            if method == "csv":
                # Load from CSV column
                df = pd.read_csv(file_path)
                column_name = self.clkutils_column_var.get()
                if not column_name:
                    messagebox.showwarning("Warning", "Please select a column")
                    return
                if column_name not in df.columns:
                    messagebox.showerror("Error", f"Column '{column_name}' not found in CSV")
                    return
                
                # Get tests from selected column, filter out NaN/empty values
                test_series = df[column_name].dropna()
                tests = [str(test).strip() for test in test_series if str(test).strip() and str(test).lower() != 'nan']
                
            elif method == "txt":
                # Load from text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Split by comma, whitespace, or newline
                import re
                # Split on any combination of commas, spaces, tabs, newlines
                test_tokens = re.split(r'[,\s]+', content)
                tests = [test.strip() for test in test_tokens if test.strip() and test.lower() != 'nan']
            
            if tests:
                self.add_clkutils_tests(tests)
                self.log_message(f"Loaded {len(tests)} CLKUtils tests from {os.path.basename(file_path)}")
            else:
                messagebox.showwarning("Warning", "No valid tests found in the selected file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tests from file: {str(e)}")
            self.log_message(f"Error loading CLKUtils tests: {str(e)}")
    
    def load_clkutils_from_text(self):
        """Load CLKUtils tests from manual text input"""
        content = self.clkutils_text_input.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "Please enter some test names")
            return
        
        # Split by comma, whitespace, or newline
        import re
        # Split on any combination of commas, spaces, tabs, newlines
        test_tokens = re.split(r'[,\s]+', content)
        tests = [test.strip() for test in test_tokens if test.strip() and test.lower() != 'nan']
        
        if tests:
            self.add_clkutils_tests(tests)
            self.log_message(f"Loaded {len(tests)} CLKUtils tests from manual input")
        else:
            messagebox.showwarning("Warning", "No valid tests found in the text input")
    
    def add_clkutils_tests(self, test_names):
        """Add CLKUtils tests to the list"""
        added_count = 0
        duplicate_count = 0
        
        for test_name in test_names:
            test_name = test_name.strip()
            if not test_name:
                continue
                
            # Check for duplicates
            if test_name in self.clkutils_tests:
                duplicate_count += 1
                continue
            
            self.clkutils_tests.append(test_name)
            added_count += 1
        
        # Update display
        self.update_clkutils_display()
        
        if duplicate_count > 0:
            messagebox.showinfo("Info", f"Added {added_count} new tests. {duplicate_count} duplicates were skipped.")
        else:
            messagebox.showinfo("Success", f"Added {added_count} CLKUtils tests")
    
    def update_clkutils_display(self):
        """Update the CLKUtils tests display"""
        # Clear existing items
        for item in self.clkutils_tree.get_children():
            self.clkutils_tree.delete(item)
        
        # Store all items for filtering
        self.all_clkutils_items = []
        
        for i, test_name in enumerate(self.clkutils_tests):
            item_data = {
                'tree_text': '☐',  # This goes in the tree column (#0)
                'values': (test_name,),  # This goes in the 'Test Name' column
                'tags': ('unchecked',),
                'test_name': test_name
            }
            self.all_clkutils_items.append(item_data)
        
        # Apply current search filter
        self.apply_clkutils_filter()
        
        # Update selection count
        self.update_clkutils_selection_count()
        
        # Configure alternating row colors
        self.configure_clkutils_tree_colors()
    
    def apply_clkutils_filter(self):
        """Apply search filter to CLKUtils tests"""
        search_text = self.clkutils_search_var.get().lower().strip()
        
        # Clear current display
        for item in self.clkutils_tree.get_children():
            self.clkutils_tree.delete(item)
        
        # Add filtered items
        for i, item_data in enumerate(self.all_clkutils_items):
            test_name = item_data['test_name']
            
            # Apply search filter
            if search_text and search_text not in test_name.lower():
                continue
            
            # Determine checkbox state
            checkbox = '☑' if 'checked' in item_data['tags'] else '☐'
            tree_text = checkbox
            values = (test_name,)  # Test name goes in the column
            
            # Insert item
            item_id = self.clkutils_tree.insert('', 'end', text=tree_text, values=values, tags=item_data['tags'])
            
            # Apply alternating row colors
            if i % 2 == 0:
                current_tags = list(item_data['tags']) + ['evenrow']
            else:
                current_tags = list(item_data['tags']) + ['oddrow']
            self.clkutils_tree.item(item_id, tags=current_tags)
    
    def on_clkutils_search_change(self, *args):
        """Handle search text change"""
        self.apply_clkutils_filter()
    
    def on_clkutils_tree_click(self, event):
        """Handle single click on CLKUtils tree"""
        item = self.clkutils_tree.identify('item', event.x, event.y)
        column = self.clkutils_tree.identify('column', event.x, event.y)
        
        # If clicked on the checkbox column (first column)
        if item and column == '#0':
            self.toggle_clkutils_selection_for_item(item)
    
    def toggle_clkutils_selection(self, event):
        """Toggle CLKUtils test selection when double-clicked"""
        if self.clkutils_tree.selection():
            item = self.clkutils_tree.selection()[0]
            self.toggle_clkutils_selection_for_item(item)
    
    def toggle_clkutils_selection_for_item(self, item):
        """Toggle selection for a specific CLKUtils item"""
        current_text = self.clkutils_tree.item(item, 'text')
        values = list(self.clkutils_tree.item(item, 'values'))
        current_tags = self.clkutils_tree.item(item, 'tags')
        test_name = values[0]  # Test name is in the first (and only) column
        
        # Determine current row type for alternating colors
        item_index = self.clkutils_tree.index(item)
        row_tag = 'evenrow' if item_index % 2 == 0 else 'oddrow'
        
        if 'checked' in current_tags:
            # Uncheck
            new_text = '☐'
            new_tags = ('unchecked', row_tag)
        else:
            # Check
            new_text = '☑'
            new_tags = ('checked', row_tag)
        
        self.clkutils_tree.item(item, text=new_text, tags=new_tags)
        
        # Update stored data
        for item_data in self.all_clkutils_items:
            if item_data['test_name'] == test_name:
                item_data['tree_text'] = new_text
                item_data['tags'] = (new_tags[0],)
                break
        
        self.update_clkutils_selection_count()
    
    def select_all_clkutils_tests(self):
        """Select all CLKUtils tests"""
        for item_data in self.all_clkutils_items:
            item_data['tree_text'] = '☑'
            item_data['tags'] = ('checked',)
        
        self.apply_clkutils_filter()
        self.update_clkutils_selection_count()
    
    def clear_all_clkutils_tests(self):
        """Clear all CLKUtils test selections"""
        for item_data in self.all_clkutils_items:
            item_data['tree_text'] = '☐'
            item_data['tags'] = ('unchecked',)
        
        self.apply_clkutils_filter()
        self.update_clkutils_selection_count()
    
    def remove_selected_clkutils_tests(self):
        """Remove selected CLKUtils tests from the list"""
        selected_tests = self.get_selected_clkutils_tests()
        if not selected_tests:
            messagebox.showwarning("Warning", "No tests selected for removal")
            return
        
        # Confirm removal
        result = messagebox.askyesno("Confirm Removal", 
                                   f"Remove {len(selected_tests)} selected tests from the list?")
        if not result:
            return
        
        # Remove tests
        for test_name in selected_tests:
            if test_name in self.clkutils_tests:
                self.clkutils_tests.remove(test_name)
        
        # Update display
        self.update_clkutils_display()
        self.log_message(f"Removed {len(selected_tests)} CLKUtils tests")
    
    def get_selected_clkutils_tests(self):
        """Get list of selected CLKUtils test names"""
        selected_tests = []
        for item_data in self.all_clkutils_items:
            if 'checked' in item_data['tags']:
                selected_tests.append(item_data['test_name'])
        return selected_tests
    
    def update_clkutils_selection_count(self):
        """Update the count of selected CLKUtils tests"""
        count = len(self.get_selected_clkutils_tests())
        self.clkutils_selected_label.configure(text=str(count))
    
    def configure_clkutils_tree_colors(self):
        """Configure alternating row colors for CLKUtils tree"""
        try:
            if self.is_dark_mode:
                self.clkutils_tree.tag_configure('oddrow', background='#2d2d48', foreground='#e8e9f0')
                self.clkutils_tree.tag_configure('evenrow', background='#353553', foreground='#e8e9f0')
                self.clkutils_tree.tag_configure('checked', background='#4a6fa5', foreground='white')
                self.clkutils_tree.tag_configure('unchecked', background='#2d2d48', foreground='#e8e9f0')
            else:
                self.clkutils_tree.tag_configure('oddrow', background='#ffffff', foreground='#24292e')
                self.clkutils_tree.tag_configure('evenrow', background='#f6f8fa', foreground='#24292e')
                self.clkutils_tree.tag_configure('checked', background='#e6f3ff', foreground='#24292e')
                self.clkutils_tree.tag_configure('unchecked', background='#ffffff', foreground='#24292e')
        except Exception as e:
            print(f"Error configuring CLKUtils tree colors: {e}")

    def create_mode_toggle(self, parent):
        """Create a visual toggle switch for MTPL/CLKUtils mode selection"""
        # Main container for the toggle
        toggle_container = ttk.Frame(parent)
        toggle_container.pack(fill='x', pady=5)
        
        # Left side - MTPL mode info
        mtpl_frame = ttk.Frame(toggle_container)
        mtpl_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(mtpl_frame, text="🧪 MTPL Mode", font=('Arial', 10, 'bold')).pack(anchor='w')
        ttk.Label(mtpl_frame, text="Use tests from MTPL tab\nRequires MTPL file loading", 
                 font=('Arial', 8), foreground='gray').pack(anchor='w')
        
        # Center - Toggle switch
        toggle_frame = ttk.Frame(toggle_container)
        toggle_frame.pack(side='left', padx=20)
        
        # Create toggle button that looks like a switch
        self.mode_toggle_button = ttk.Button(toggle_frame, text="MTPL", 
                                           command=self.toggle_processing_mode, width=15)
        self.mode_toggle_button.pack(pady=10)
        
        # Mode indicator label
        self.mode_indicator_label = ttk.Label(toggle_frame, text="📊 Current: MTPL Mode", 
                                            font=('Arial', 9, 'bold'), foreground='blue')
        self.mode_indicator_label.pack()
        
        # Right side - CLKUtils mode info
        clkutils_frame = ttk.Frame(toggle_container)
        clkutils_frame.pack(side='right', fill='x', expand=True)
        
        ttk.Label(clkutils_frame, text="⏰ CLKUtils Mode", font=('Arial', 10, 'bold')).pack(anchor='e')
        ttk.Label(clkutils_frame, text="Use tests from CLKUtils tab\nNo MTPL file required", 
                 font=('Arial', 8), foreground='gray').pack(anchor='e')
        
        # Update initial appearance
        self.update_mode_toggle_appearance()
    
    def toggle_processing_mode(self):
        """Toggle between MTPL and CLKUtils processing modes"""
        current_mode = self.run_clkutils_var.get()
        new_mode = not current_mode
        self.run_clkutils_var.set(new_mode)
        self.update_mode_toggle_appearance()
        
        # Log the mode change
        mode_name = "CLKUtils" if new_mode else "MTPL"
        self.log_message(f"Switched to {mode_name} processing mode")
    
    def update_mode_toggle_appearance(self):
        """Update the toggle button appearance based on current mode"""
        is_clkutils = self.run_clkutils_var.get()
        
        if is_clkutils:
            # CLKUtils mode
            self.mode_toggle_button.configure(text="CLKUtils ⏰")
            self.mode_indicator_label.configure(text="⏰ Current: CLKUtils Mode", foreground='green')
            if hasattr(self, 'log_message'):
                pass  # Don't log during initialization
        else:
            # MTPL mode
            self.mode_toggle_button.configure(text="🧪 MTPL")
            self.mode_indicator_label.configure(text="🧪 Current: MTPL Mode", foreground='blue')
            if hasattr(self, 'log_message'):
                pass  # Don't log during initialization

    def create_output_tab(self):
        # Create a canvas and scrollbar for scrollable content
        output_canvas = tk.Canvas(self.output_frame, highlightthickness=0)
        output_scrollbar = ttk.Scrollbar(self.output_frame, orient="vertical", command=output_canvas.yview)
        self.output_scrollable_frame = ttk.Frame(output_canvas)
        
        # Configure scrolling
        self.output_scrollable_frame.bind(
            "<Configure>",
            lambda e: output_canvas.configure(scrollregion=output_canvas.bbox("all"))
        )
        
        output_canvas.create_window((0, 0), window=self.output_scrollable_frame, anchor="nw")
        output_canvas.configure(yscrollcommand=output_scrollbar.set)
        
        # Pack the canvas and scrollbar
        output_canvas.pack(side="left", fill="both", expand=True)
        output_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas for smooth scrolling
        def _on_output_mousewheel(event):
            output_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_output_mousewheel(event):
            output_canvas.bind_all("<MouseWheel>", _on_output_mousewheel)
        
        def _unbind_from_output_mousewheel(event):
            output_canvas.unbind_all("<MouseWheel>")
        
        output_canvas.bind('<Enter>', _bind_to_output_mousewheel)
        output_canvas.bind('<Leave>', _unbind_from_output_mousewheel)
        
        # Now create all the content in the scrollable_frame
        ttk.Label(self.output_scrollable_frame, text="Output Settings and Processing", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Output folder selection - stretch with consistent margins
        output_folder_frame = ttk.LabelFrame(self.output_scrollable_frame, text="Output Folder Selection")
        output_folder_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        # Configure grid weights for responsive design
        output_folder_frame.grid_columnconfigure(1, weight=1)
        
        self.output_path_var = tk.StringVar()
        ttk.Label(output_folder_frame, text="Output Folder:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(output_folder_frame, textvariable=self.output_path_var).grid(row=0, column=1, padx=10, pady=5, sticky='ew')  # Remove fixed width, use sticky='ew'
        ttk.Button(output_folder_frame, text="Browse", command=self.browse_output_folder).grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(output_folder_frame, text="Use Default", command=self.use_default_output).grid(row=1, column=1, pady=10)
        
        # Processing options - stretch with consistent margins
        options_frame = ttk.LabelFrame(self.output_scrollable_frame, text="Processing Options")
        options_frame.pack(fill='x', padx=(20, 40), pady=10)  # Right margin accounts for scrollbar
        
        self.delete_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Delete intermediary files", variable=self.delete_files_var).pack(anchor='w', padx=10, pady=5)
        
        # Always stack output files for JMP; option removed
        
        self.run_jmp_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Run JMP on stacked files", variable=self.run_jmp_var).pack(anchor='w', padx=10, pady=5)
        
        # Processing mode selection (MTPL vs CLKUtils)
        mode_frame = ttk.LabelFrame(options_frame, text="Processing Mode")
        mode_frame.pack(fill='x', padx=10, pady=10)
        
        # Create mode selection frame
        mode_selector_frame = ttk.Frame(mode_frame)
        mode_selector_frame.pack(fill='x', padx=10, pady=10)
        
        # Initialize the mode variable (False = MTPL, True = CLKUtils)
        self.run_clkutils_var = tk.BooleanVar(value=False)
        
        # Create custom toggle switch appearance
        self.create_mode_toggle(mode_selector_frame)
        
        # Processing controls
        process_frame = ttk.Frame(self.output_scrollable_frame)
        process_frame.pack(pady=20)
        
        ttk.Button(process_frame, text="Start Processing", command=self.start_processing, style='Accent.TButton').pack(side='left', padx=10)
        self.stop_button = ttk.Button(process_frame, text="Stop", command=self.stop_processing, state='disabled')
        self.stop_button.pack(side='left', padx=10)
        ttk.Button(process_frame, text="Get Testtimes", command=self.get_testtimes, style='Accent.TButton').pack(side='left', padx=10)
        ttk.Button(process_frame, text="Clear All", command=self.clear_all).pack(side='left', padx=10)
        
        # Progress bar (separate from log) - stretch with consistent margins
        progress_info_frame = ttk.LabelFrame(self.output_scrollable_frame, text="Processing Progress")
        progress_info_frame.pack(fill='x', padx=(20, 40), pady=(10, 5))  # Right margin accounts for scrollbar
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_info_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=10)
        
        # Log display using resizable frame
        log_data_frame = self.create_resizable_data_frame(
            self.output_scrollable_frame, 
            "Processing Log & Output", 
            min_height=150, 
            default_height=300
        )
        
        # Log text area with scrollbars
        log_container = ttk.Frame(log_data_frame)
        log_container.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(log_container, height=10, width=80)
        self.log_text.pack(side='left', fill='both', expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_container, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Add mouse wheel support for the log text area
        def _on_log_mousewheel(event):
            self.log_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.log_text.bind("<MouseWheel>", _on_log_mousewheel)
        
    def load_csv_filtered(self, file_path):
        """Load CSV file with robust column filtering to handle empty wafer sections and preserve data structure"""
        try:
            # Read the CSV first
            df = pd.read_csv(file_path, dtype=str, na_filter=False)  # Read as strings to preserve empty values
            
            # Define required columns in expected order
            required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
            
            self.log_message(f"Original columns: {list(df.columns)}")
            self.log_message(f"Original dataframe shape: {df.shape}")
            
            # Clean column names (remove whitespace, handle unnamed)
            cleaned_columns = []
            for col in df.columns:
                col_str = str(col).strip()
                if col_str.startswith('Unnamed:') or col_str == '' or col_str == 'nan':
                    cleaned_columns.append(None)  # Mark for removal
                else:
                    cleaned_columns.append(col_str)
            
            # Remove unnamed/empty columns while preserving order
            valid_df = df.copy()
            valid_columns = []
            cols_to_drop = []
            
            for i, col_name in enumerate(cleaned_columns):
                if col_name is None:
                    cols_to_drop.append(df.columns[i])
                else:
                    valid_columns.append(col_name)
            
            if cols_to_drop:
                valid_df = valid_df.drop(columns=cols_to_drop)
                valid_df.columns = valid_columns
                self.log_message(f"Dropped unnamed/empty columns: {cols_to_drop}")
            
            self.log_message(f"Valid columns after cleanup: {valid_columns}")
            
            # Try to map columns to required structure
            column_mapping = {}
            final_columns = []
            
            # First pass: exact matches
            used_columns = set()
            for req_col in required_columns:
                if req_col in valid_columns and req_col not in used_columns:
                    final_columns.append(req_col)
                    used_columns.add(req_col)
                else:
                    final_columns.append(None)  # Placeholder
            
            # Second pass: case-insensitive matches
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is None:  # Not found yet
                    for valid_col in valid_columns:
                        if (valid_col not in used_columns and 
                            valid_col.lower() == req_col.lower()):
                            final_columns[i] = valid_col
                            column_mapping[valid_col] = req_col
                            used_columns.add(valid_col)
                            break
            
            # Third pass: positional mapping for remaining columns
            remaining_valid = [col for col in valid_columns if col not in used_columns]
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is None and i < len(remaining_valid):
                    final_columns[i] = remaining_valid[i]
                    column_mapping[remaining_valid[i]] = req_col
                    self.log_message(f"Positional mapping: '{remaining_valid[i]}' -> '{req_col}'")
            
            # Build the final dataframe with required structure
            result_df = pd.DataFrame()
            
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is not None:
                    # Column exists, copy it
                    col_data = valid_df[final_columns[i]].copy()
                    # Only fill Prefetch column with defaults, preserve Wafer empty values
                    if req_col == 'Prefetch' and col_data.eq('').all():
                        self.log_message(f"Prefetch column is empty, filling with default value '3'")
                        col_data = col_data.fillna('3').replace('', '3')
                    elif req_col == 'Wafer':
                        # Preserve Wafer column as-is (keep empty values empty)
                        self.log_message(f"Preserving Wafer column values (including empty values)")
                        col_data = col_data.fillna('')
                    else:
                        # For other columns, preserve empty values as empty strings
                        col_data = col_data.fillna('')
                    
                    result_df[req_col] = col_data
                else:
                    # Column missing, create with default values
                    if req_col == 'Wafer':
                        default_val = ''
                    elif req_col == 'Prefetch':
                        default_val = '3'
                    else:
                        default_val = ''
                    
                    result_df[req_col] = [default_val] * len(valid_df)
                    self.log_message(f"Created missing column '{req_col}' with default value '{default_val}'")
            
            self.log_message(f"Final columns: {list(result_df.columns)}")
            self.log_message(f"Final dataframe shape: {result_df.shape}")
            
            if column_mapping:
                self.log_message(f"Applied column mappings: {column_mapping}")
            
            # Post-processing validation: only fix Prefetch, keep Wafer empty
            if not result_df.empty:
                # Keep Wafer column as-is (preserve empty values)
                self.log_message("Keeping Wafer column values as-is (preserving empty values)")
                
                # Check if Prefetch column is completely empty and fix it
                if 'Prefetch' in result_df.columns and result_df['Prefetch'].eq('').all():
                    result_df['Prefetch'] = '3'
                    self.log_message("Fixed completely empty Prefetch column with default value '3'")
                
                # Only ensure Prefetch column is properly formatted
                if 'Prefetch' in result_df.columns:
                    # Replace any remaining empty/NaN values in Prefetch only
                    result_df['Prefetch'] = result_df['Prefetch'].replace(['nan', 'NaN'], '3')
                    result_df['Prefetch'] = result_df['Prefetch'].fillna('3')
            
            return result_df
            
        except Exception as e:
            self.log_message(f"Error filtering CSV: {str(e)}", "error")
            raise e
    
    def load_excel_filtered(self, file_path):
        """Load Excel file with robust column filtering to handle empty wafer sections and preserve data structure"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, dtype=str, na_filter=False)  # Read as strings to preserve empty values
            
            # Define required columns in expected order
            required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
            
            self.log_message(f"Original columns: {list(df.columns)}")
            self.log_message(f"Original dataframe shape: {df.shape}")
            
            # Clean column names (remove whitespace, handle unnamed)
            cleaned_columns = []
            for col in df.columns:
                col_str = str(col).strip()
                if col_str.startswith('Unnamed:') or col_str == '' or col_str == 'nan':
                    cleaned_columns.append(None)  # Mark for removal
                else:
                    cleaned_columns.append(col_str)
            
            # Remove unnamed/empty columns while preserving order
            valid_df = df.copy()
            valid_columns = []
            cols_to_drop = []
            
            for i, col_name in enumerate(cleaned_columns):
                if col_name is None:
                    cols_to_drop.append(df.columns[i])
                else:
                    valid_columns.append(col_name)
            
            if cols_to_drop:
                valid_df = valid_df.drop(columns=cols_to_drop)
                valid_df.columns = valid_columns
                self.log_message(f"Dropped unnamed/empty columns: {cols_to_drop}")
            
            self.log_message(f"Valid columns after cleanup: {valid_columns}")
            
            # Try to map columns to required structure
            column_mapping = {}
            final_columns = []
            
            # First pass: exact matches
            used_columns = set()
            for req_col in required_columns:
                if req_col in valid_columns and req_col not in used_columns:
                    final_columns.append(req_col)
                    used_columns.add(req_col)
                else:
                    final_columns.append(None)  # Placeholder
            
            # Second pass: case-insensitive matches
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is None:  # Not found yet
                    for valid_col in valid_columns:
                        if (valid_col not in used_columns and 
                            valid_col.lower() == req_col.lower()):
                            final_columns[i] = valid_col
                            column_mapping[valid_col] = req_col
                            used_columns.add(valid_col)
                            break
            
            # Third pass: positional mapping for remaining columns
            remaining_valid = [col for col in valid_columns if col not in used_columns]
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is None and i < len(remaining_valid):
                    final_columns[i] = remaining_valid[i]
                    column_mapping[remaining_valid[i]] = req_col
                    self.log_message(f"Positional mapping: '{remaining_valid[i]}' -> '{req_col}'")
            
            # Build the final dataframe with required structure
            result_df = pd.DataFrame()
            
            for i, req_col in enumerate(required_columns):
                if final_columns[i] is not None:
                    # Column exists, copy it
                    col_data = valid_df[final_columns[i]].copy()
                    # Only fill Prefetch column with defaults, preserve Wafer empty values
                    if req_col == 'Prefetch' and col_data.eq('').all():
                        self.log_message(f"Prefetch column is empty, filling with default value '3'")
                        col_data = col_data.fillna('3').replace('', '3')
                    elif req_col == 'Wafer':
                        # Preserve Wafer column as-is (keep empty values empty)
                        self.log_message(f"Preserving Wafer column values (including empty values)")
                        col_data = col_data.fillna('')
                    else:
                        # For other columns, preserve empty values as empty strings
                        col_data = col_data.fillna('')
                    
                    result_df[req_col] = col_data
                else:
                    # Column missing, create with default values
                    if req_col == 'Wafer':
                        default_val = ''
                    elif req_col == 'Prefetch':
                        default_val = '3'
                    else:
                        default_val = ''
                    
                    result_df[req_col] = [default_val] * len(valid_df)
                    self.log_message(f"Created missing column '{req_col}' with default value '{default_val}'")
            
            self.log_message(f"Final columns: {list(result_df.columns)}")
            self.log_message(f"Final dataframe shape: {result_df.shape}")
            
            if column_mapping:
                self.log_message(f"Applied column mappings: {column_mapping}")
            
            # Post-processing validation: only fix Prefetch, keep Wafer empty
            if not result_df.empty:
                # Keep Wafer column as-is (preserve empty values)
                self.log_message("Keeping Wafer column values as-is (preserving empty values)")
                
                # Check if Prefetch column is completely empty and fix it
                if 'Prefetch' in result_df.columns and result_df['Prefetch'].eq('').all():
                    result_df['Prefetch'] = '3'
                    self.log_message("Fixed completely empty Prefetch column with default value '3'")
                
                # Only ensure Prefetch column is properly formatted
                if 'Prefetch' in result_df.columns:
                    # Replace any remaining empty/NaN values in Prefetch only
                    result_df['Prefetch'] = result_df['Prefetch'].replace(['nan', 'NaN'], '3')
                    result_df['Prefetch'] = result_df['Prefetch'].fillna('3')
            
            return result_df
            
        except Exception as e:
            self.log_message(f"Error filtering Excel: {str(e)}", "error")
            raise e
    
    def extract_test_instances_from_material_data(self):
        """
        Extract test instances from loaded material data for automatic filtering
        
        This method:
        1. Searches for columns containing test instance data (looking for 'test', 'testname', etc.)
        2. Extracts unique test instances from those columns (handles comma-separated values)
        3. Stores them in self.material_test_instances for later filtering
        4. Enables automatic filtering if test instances are found
        """
        self.material_test_instances = []
        
        if self.material_df is None or self.material_df.empty:
            return
        
        # Look for test instance columns in material data
        test_columns = []
        self.log_message(f"Material data columns: {list(self.material_df.columns)}", "info")
        
        for col in self.material_df.columns:
            col_lower = col.lower()
            # Expanded keywords to catch more column naming variations
            test_keywords = ['test', 'testname', 'test_name', 'testinstance', 'test_instance', 'tests', 'test_list']
            self.log_message(f"Checking material column: '{col}' (lowercase: '{col_lower}')", "info")
            
            if any(test_keyword in col_lower for test_keyword in test_keywords):
                test_columns.append(col)
                self.log_message(f"✅ Found test column: '{col}'", "success")
                
        if not test_columns:
            self.log_message("No test instance columns found in material data", "warning")
            self.log_message("Looking for columns containing: test, testname, test_name, testinstance, test_instance, tests, test_list", "info")
            return
            
        # Extract unique test instances from all test columns
        test_instances = set()
        for col in test_columns:
            self.log_message(f"Extracting test instances from column: '{col}'", "info")
            col_values = []
            for value in self.material_df[col].dropna():
                if pd.notna(value) and str(value).strip():
                    # Handle comma-separated values
                    test_values = [test.strip() for test in str(value).split(',') if test.strip()]
                    col_values.extend(test_values)
                    test_instances.update(test_values)
            self.log_message(f"Found {len(col_values)} test instances in column '{col}': {col_values[:5]}{'...' if len(col_values) > 5 else ''}", "info")
        
        self.material_test_instances = sorted(list(test_instances))
        
        if self.material_test_instances:
            self.log_message(f"✅ Extracted {len(self.material_test_instances)} total unique test instances from material data: {self.material_test_instances[:5]}{'...' if len(self.material_test_instances) > 5 else ''}", "success")
            self.auto_filter_enabled = True
        else:
            self.log_message("❌ No valid test instances found in material data", "error")
            self.auto_filter_enabled = False
    
    def validate_material_columns(self, df):
        """Validate that the material data contains expected columns and has proper structure"""
        required_columns = ['Database', 'Program', 'Test', 'Lot', 'Wafer', 'Prefetch']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            self.log_message(f"Warning: Missing columns: {missing_columns}", "warning")
        else:
            self.log_message("All required columns found", "success")
        
        # Additional validation: check for data integrity
        if not df.empty:
            # Validate Wafer column has reasonable values
            if 'Wafer' in df.columns:
                wafer_col = df['Wafer']
                empty_wafers = wafer_col.eq('').sum()
                if empty_wafers > 0:
                    self.log_message(f"Found {empty_wafers} empty wafer values, will use defaults", "info")
            
            # Validate Prefetch column has reasonable values
            if 'Prefetch' in df.columns:
                prefetch_col = df['Prefetch']
                empty_prefetch = prefetch_col.eq('').sum()
                if empty_prefetch > 0:
                    self.log_message(f"Found {empty_prefetch} empty prefetch values, will use defaults", "info")
        
        return len(missing_columns) == 0, missing_columns
    
    def apply_automatic_test_instance_filter(self):
        """
        Apply automatic filtering based on test instances from material data
        
        This method:
        1. Uses test instances extracted from material data to filter MTPL tests
        2. Shows only MTPL tests that match the test instances from the Excel/CSV material data
        3. Updates the UI to indicate filtering is active
        4. Provides feedback on matched tests
        """
        if not self.auto_filter_enabled or not self.material_test_instances:
            self.log_message("Auto-filter not enabled or no test instances available", "info")
            return
            
        if not hasattr(self, 'all_mtpl_items') or not self.all_mtpl_items:
            self.log_message("No MTPL items available for filtering", "warning")
            return
            
        self.log_message(f"Applying auto-filter with {len(self.material_test_instances)} test instances", "info")
        self.log_message(f"Material test instances: {self.material_test_instances}", "info")
            
        # Debug: Show MTPL DataFrame structure
        if self.mtpl_df is not None:
            self.log_message(f"MTPL DataFrame columns: {list(self.mtpl_df.columns)}", "info")
            self.log_message(f"MTPL DataFrame shape: {self.mtpl_df.shape}", "info")
            if not self.mtpl_df.empty:
                # Show first few test names for debugging
                if len(self.mtpl_df.columns) > 1:
                    test_col = self.mtpl_df.columns[1]  # Typically the second column
                    sample_tests = self.mtpl_df[test_col].head(3).tolist()
                    self.log_message(f"Sample MTPL test names from column '{test_col}': {sample_tests}", "info")
            
        # Find the test name column in MTPL data (usually column 1 or 2)
        test_name_column_index = None
        if self.mtpl_df is not None:
            # Try to find test name column by checking common patterns
            # Look for columns that contain 'testname' or exact 'name' (but not just 'test' to avoid 'testtype')
            for i, col in enumerate(self.mtpl_df.columns):
                col_lower = col.lower()
                self.log_message(f"Checking column {i}: '{col}' (lowercase: '{col_lower}')", "info")
                
                # More specific matching to avoid 'TestType' being selected over 'TestName'
                if ('testname' in col_lower or 
                    col_lower == 'name' or 
                    col_lower == 'test_name' or
                    col_lower.endswith('name')):
                    test_name_column_index = i + 1  # +1 because of checkbox column
                    self.log_message(f"✅ Found test name column: '{col}' at index {test_name_column_index} (with checkbox offset)", "success")
                    break
            
            # If not found by specific name patterns, try broader search but prioritize columns with 'name'
            if test_name_column_index is None:
                for i, col in enumerate(self.mtpl_df.columns):
                    col_lower = col.lower()
                    if 'name' in col_lower and 'type' not in col_lower:  # Avoid TestType, prefer TestName
                        test_name_column_index = i + 1  # +1 because of checkbox column
                        self.log_message(f"✅ Found test name column (broader search): '{col}' at index {test_name_column_index} (with checkbox offset)", "success")
                        break
            
            # If still not found, assume it's the second column (index 1, or 2 with checkbox)
            if test_name_column_index is None:
                test_name_column_index = 2  # Default to second data column
                default_col_name = self.mtpl_df.columns[1] if len(self.mtpl_df.columns) > 1 else "Unknown"
                self.log_message(f"⚠️ Using default test name column index: {test_name_column_index} (column: '{default_col_name}')", "warning")
        
        if test_name_column_index is None:
            self.log_message("❌ Could not determine test name column for filtering", "error")
            return
            
        # Debug: Show what column we're using
        display_columns = ['Selected'] + list(self.mtpl_df.columns)
        target_column = display_columns[test_name_column_index] if test_name_column_index < len(display_columns) else "Index out of range"
        self.log_message(f"Using column index {test_name_column_index} ('{target_column}') for test name matching", "info")
            
        # Filter items based on test instances
        filtered_items = []
        matched_tests = set()
        unmatched_tests = []
        
        self.log_message(f"Filtering {len(self.all_mtpl_items)} MTPL items...", "info")
        
        for i, item_data in enumerate(self.all_mtpl_items):
            values = item_data['values']
            if len(values) > test_name_column_index:
                test_name = str(values[test_name_column_index]).strip()
                
                # Debug: Show first few items being processed
                if i < 5:
                    self.log_message(f"Item {i}: values={values}, test_name='{test_name}'", "info")
                
                # Use search-like filtering: check if any material test instance is contained in the test name
                # or if the test name is contained in any material test instance
                match_found = False
                matched_instance = None
                
                for mat_test in self.material_test_instances:
                    # Case-insensitive substring matching (like search function)
                    test_name_lower = test_name.lower()
                    mat_test_lower = mat_test.lower()
                    
                    # Check both directions: material test in MTPL test name, or MTPL test name in material test
                    if (mat_test_lower in test_name_lower or 
                        test_name_lower in mat_test_lower):
                        match_found = True
                        matched_instance = mat_test
                        break
                
                if match_found:
                    filtered_items.append(item_data)
                    matched_tests.add(f"{test_name} (matched: {matched_instance})")
                    if i < 5:  # Log first few matches
                        self.log_message(f"✅ Match found: '{test_name}' <-> '{matched_instance}'", "success")
                else:
                    unmatched_tests.append(test_name)
        
        # Show debugging results
        self.log_message(f"Filtering complete: {len(filtered_items)} matched, {len(unmatched_tests)} unmatched", "info")
        
        if matched_tests:
            self.log_message(f"✅ Matched tests: {sorted(matched_tests)}", "success")
        else:
            self.log_message("❌ No tests matched!", "warning")
            
        # Show some unmatched tests for comparison
        if unmatched_tests:
            sample_unmatched = unmatched_tests[:5]  # Show first 5 unmatched
            self.log_message(f"Sample unmatched MTPL tests: {sample_unmatched}", "info")
            
            # Try to find potential matches with case-insensitive comparison
            case_insensitive_matches = []
            material_lower = [t.lower() for t in self.material_test_instances]
            for test in sample_unmatched:
                if test.lower() in material_lower:
                    case_insensitive_matches.append(test)
            
            if case_insensitive_matches:
                self.log_message(f"⚠️ Found case-insensitive matches: {case_insensitive_matches}", "warning")
                self.log_message("Consider checking for case sensitivity issues in test names", "warning")
        
        if filtered_items:
            self.log_message(f"✅ Auto-filtered MTPL using substring matching: {len(filtered_items)} tests found", "success")
            self.log_message(f"Matched pairs: {', '.join(sorted(matched_tests)[:3])}{'...' if len(matched_tests) > 3 else ''}", "info")
            
            # Update search field to show filter is active
            if hasattr(self, 'search_var'):
                self.search_var.set("AUTO-FILTERED BY MATERIAL DATA")
            
            # Display filtered items
            self.display_filtered_items(filtered_items)
            
            # Show prominent info message to user - THIS IS THE KEY VISUAL FEEDBACK
            if hasattr(self, 'filter_status_label'):
                self.filter_status_label.configure(
                    text=f"🎯 AUTO-FILTERED: {len(filtered_items)} tests match material data (substring matching) | Click 'Clear Auto-Filter' to see all tests",
                    foreground='green'
                )
            
            # Update active filters label
            if hasattr(self, 'active_filters_label'):
                self.active_filters_label.configure(
                    text=f"Auto-filter: {len(filtered_items)}/{len(self.all_mtpl_items)} tests shown",
                    foreground='green'
                )
                
        else:
            self.log_message("❌ No MTPL tests match the test instances from material data using substring matching", "error")
            self.log_message("This means no material test names contain MTPL test names, and no MTPL test names contain material test names", "warning")
            # Show warning message
            if hasattr(self, 'filter_status_label'):
                self.filter_status_label.configure(
                    text="⚠️ AUTO-FILTER: No MTPL tests match material data test instances (substring matching tried)",
                    foreground='orange'
                )
    
    def clear_automatic_filter(self):
        """
        Clear the automatic test instance filter
        
        This method clears the automatic filtering and shows all MTPL tests again.
        Users can click this button to see all tests instead of just the filtered ones.
        """
        if hasattr(self, 'search_var'):
            self.search_var.set("")
        
        # Clear all filters
        self.clear_all_filters()
        
        # Update filter status to show no filters are active
        if hasattr(self, 'filter_status_label'):
            self.filter_status_label.configure(text="Auto-filter cleared - showing all tests", foreground='blue')
        
        # Log the action
        self.log_message("Automatic filter cleared - showing all MTPL tests", "info")

    def load_material_file(self):
        """Load material data from CSV or Excel file with enhanced column filtering"""
        file_path = filedialog.askopenfilename(
            title="Select Material Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Normalize the file path to handle UNC paths and strip quotes
                normalized_path = self.normalize_unc_path(file_path)
                self.log_message(f"Loading material data from: {normalized_path}")
                
                # Load and filter the file based on type
                if normalized_path.endswith('.csv'):
                    self.material_df = self.load_csv_filtered(normalized_path)
                elif normalized_path.endswith(('.xlsx', '.xls')):
                    self.material_df = self.load_excel_filtered(normalized_path)
                else:
                    # Try CSV as fallback
                    self.material_df = self.load_csv_filtered(normalized_path)
                
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
                
                # Extract test instances from material data for automatic filtering
                self.extract_test_instances_from_material_data()
                
                # Show column preview to user
                self.show_column_preview()
                
                # Update entry fields with first row data if available
                if not self.material_df.empty:
                    self.update_entry_fields_from_dataframe()
                    
                # If MTPL is already loaded, apply automatic filtering
                if hasattr(self, 'mtpl_df') and self.mtpl_df is not None and self.auto_filter_enabled:
                    self.log_message("Applying automatic filter to loaded MTPL data based on material test instances", "info")
                    self.apply_automatic_test_instance_filter()
                        
            except Exception as e:
                error_msg = f"Failed to load file: {str(e)}"
                self.log_message(error_msg, "error")
                messagebox.showerror("Error", error_msg)
    
    def test_empty_wafer_handling(self):
        """Test method to validate empty wafer handling works correctly"""
        try:
            # Create a test dataframe with empty wafer column to simulate the issue
            test_data = {
                'Database': ['D1D_PROD_XEUS'],
                'Program': ['DABHOPCA0H20C022528'],
                'Test': ['TestInstance1'],
                'Lot': ['841'],
                'Wafer': [''],  # Empty wafer - this should be fixed
                'Prefetch': ['']  # Empty prefetch - this should be fixed
            }
            
            test_df = pd.DataFrame(test_data)
            self.log_message("Testing empty wafer/prefetch handling...", "info")
            self.log_message(f"Before fix - Wafer: '{test_df['Wafer'].iloc[0]}', Prefetch: '{test_df['Prefetch'].iloc[0]}'", "info")
            
            # Simulate the fix
            if 'Wafer' in test_df.columns and test_df['Wafer'].eq('').all():
                test_df['Wafer'] = '1'
                self.log_message("Fixed empty Wafer column with default value '1'")
            
            if 'Prefetch' in test_df.columns and test_df['Prefetch'].eq('').all():
                test_df['Prefetch'] = '3'
                self.log_message("Fixed empty Prefetch column with default value '3'")
            
            self.log_message(f"After fix - Wafer: '{test_df['Wafer'].iloc[0]}', Prefetch: '{test_df['Prefetch'].iloc[0]}'", "success")
            self.log_message("Empty wafer/prefetch handling test completed successfully!", "success")
            
            return test_df
            
        except Exception as e:
            self.log_message(f"Test failed: {str(e)}", "error")
            return None
    
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
            
            # Add information about automatic filtering
            if self.auto_filter_enabled and self.material_test_instances:
                preview_msg += f"\n🎯 Automatic Filtering Enabled:\n"
                preview_msg += f"Found {len(self.material_test_instances)} test instances that will be used to automatically filter MTPL tests.\n"
                preview_msg += f"Test instances: {', '.join(self.material_test_instances[:3])}{'...' if len(self.material_test_instances) > 3 else ''}\n"
                preview_msg += f"\nWhen you load an MTPL file, it will be automatically filtered to show only these test instances."
            
            messagebox.showinfo("Import Preview", preview_msg)
    
    def update_entry_fields_from_dataframe(self):
        """Update the entry fields with data from the loaded dataframe"""
        if self.material_df is not None and not self.material_df.empty:
            first_row = self.material_df.iloc[0]
            
            # Update entry fields only if the column exists
            if 'Lot' in self.material_df.columns:
                self.lot_var.set(str(first_row['Lot']))
            if 'Wafer' in self.material_df.columns:
                # Convert to integer if it's a float
                wafer_value = first_row['Wafer']
                if isinstance(wafer_value, float) and wafer_value.is_integer():
                    wafer_value = int(wafer_value)
                self.wafer_var.set(str(wafer_value))
            if 'Program' in self.material_df.columns:
                self.program_var.set(str(first_row['Program']))
            if 'Prefetch' in self.material_df.columns:
                # Convert to integer if it's a float
                prefetch_value = first_row['Prefetch']
                if isinstance(prefetch_value, float) and prefetch_value.is_integer():
                    prefetch_value = int(prefetch_value)
                self.prefetch_var.set(str(prefetch_value))
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
            wafer_raw_list = parse_input(wafer_input, default_values['Wafer'])
            program_list = parse_input(program_input, default_values['Program'])
            database_list = parse_input(database_input, default_values['Database'])
            
            # Convert wafer values to integers where possible
            wafer_list = []
            for w in wafer_raw_list:
                try:
                    # Try to convert to float first, then to int if it's a whole number
                    if str(w).strip() and str(w).strip().replace('.', '').isdigit():
                        float_val = float(w)
                        if float_val.is_integer():
                            wafer_list.append(int(float_val))
                        else:
                            wafer_list.append(str(w))  # Keep as string if not a whole number
                    else:
                        wafer_list.append(str(w))  # Keep as string if not numeric
                except:
                    wafer_list.append(str(w))
            
            # Handle prefetch specially as it should be an integer
            if prefetch_input.strip():
                try:
                    # Handle both string digits and float values
                    prefetch_float = float(prefetch_input.strip())
                    if prefetch_float.is_integer():
                        prefetch_value = int(prefetch_float)
                    else:
                        prefetch_value = int(prefetch_float)  # Round down if not integer
                except:
                    prefetch_value = default_values['Prefetch'][0]
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
            def format_list_for_display(item_list):
                """Convert list items to strings, handling integers and floats properly"""
                formatted_items = []
                for item in item_list:
                    if isinstance(item, float) and item.is_integer():
                        formatted_items.append(str(int(item)))  # Convert 841.0 to "841"
                    elif isinstance(item, int):
                        formatted_items.append(str(item))  # Convert 841 to "841"
                    else:
                        formatted_items.append(str(item))  # Convert everything else to string
                return formatted_items
            
            display_data = {
                'Lot': [', '.join(format_list_for_display(lot_list))],
                'Wafer': [', '.join(format_list_for_display(wafer_list))],
                'Program': [', '.join(format_list_for_display(program_list))],
                'Prefetch': [str(prefetch_value)],
                'Database': [', '.join(format_list_for_display(database_list))]
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
            # Normalize the file path to handle UNC paths and strip quotes
            normalized_path = self.normalize_unc_path(file_path)
            self.mtpl_file_path.set(normalized_path)
            self.update_mtpl_info(normalized_path)
            
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
            
            # Normalize path for UNC paths before processing
            normalized_mtpl_path = self.normalize_unc_path(mtpl_path)
            self.log_message(f"Original path: {mtpl_path}")
            self.log_message(f"Normalized path: {normalized_mtpl_path}")
            
            # Apply normalization again to the result of fi.process_file_input
            processed_path = fi.process_file_input(normalized_mtpl_path)
            final_path = self.normalize_unc_path(processed_path)
            self.log_message(f"Processed path: {processed_path}")
            self.log_message(f"Final path: {final_path}")
            
            self.mtpl_csv_path = mt.mtpl_to_csv(final_path)
            self.mtpl_df = pd.read_csv(self.mtpl_csv_path)
            
            # Debug: Print MTPL dataframe info
            print(f"Debug - MTPL columns: {self.mtpl_df.columns.tolist()}")
            print(f"Debug - MTPL shape: {self.mtpl_df.shape}")
            if not self.mtpl_df.empty:
                print(f"Debug - First few rows of MTPL:")
                print(self.mtpl_df.head())
            
            self.update_mtpl_display()
            self.log_message(f"MTPL file processed: {self.mtpl_csv_path}", "success")
            
            # Store the successfully loaded path for reload functionality
            self.last_mtpl_path = mtpl_path
            self.reload_mtpl_button.configure(state='normal')  # Enable reload button

            # Update the info label with last loaded info
            file_name = os.path.basename(mtpl_path)
            self.update_status_indicator(self.mtpl_info_label, 
                           f"✅ Loaded: {file_name} (Reload available)", "success")
            # Set default output folder
            self.set_default_output_folder()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process MTPL file: {str(e)}")
            self.log_message(f"Error processing MTPL: {str(e)}", "error")
    def reload_mtpl_file(self):
        """Reload the last successfully loaded MTPL file"""
        if not self.last_mtpl_path:
            messagebox.showwarning("Warning", "No previous MTPL file to reload")
            return
            
        if not os.path.exists(self.last_mtpl_path):
            messagebox.showerror("Error", f"Last MTPL file no longer exists:\n{self.last_mtpl_path}")
            # Disable reload button since file is gone
            self.reload_mtpl_button.configure(state='disabled')
            self.last_mtpl_path = ""
            return
            
        try:
            # Set the path and load
            self.mtpl_file_path.set(self.last_mtpl_path)
            self.log_message(f"Reloading MTPL file: {os.path.basename(self.last_mtpl_path)}")
            
            # Normalize path for UNC paths before processing
            normalized_mtpl_path = self.normalize_unc_path(self.last_mtpl_path)
            
            # Apply normalization again to the result of fi.process_file_input
            processed_path = fi.process_file_input(normalized_mtpl_path)
            final_path = self.normalize_unc_path(processed_path)
            
            # Process the file
            self.mtpl_csv_path = mt.mtpl_to_csv(final_path)
            self.mtpl_df = pd.read_csv(self.mtpl_csv_path)
            
            self.update_mtpl_display()
            self.log_message(f"MTPL file reloaded successfully: {self.mtpl_csv_path}", "success")
            
            # Update the info label
            file_name = os.path.basename(self.last_mtpl_path)
            self.update_status_indicator(self.mtpl_info_label, 
                                    f"🔄 Reloaded: {file_name}", "success")
            
            # Set default output folder
            self.set_default_output_folder()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload MTPL file: {str(e)}")
            self.log_message(f"Error reloading MTPL: {str(e)}", "error")
            
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
                
            # Create column filters
            self.create_column_filters()
                
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
            
            # Clear search
            self.search_var.set("")
            self.update_filter_status()
            
            # Enhance visual feedback
            self.enhance_visual_feedback()
            
            # Apply automatic filtering if material test instances are available
            if self.auto_filter_enabled and self.material_test_instances:
                self.log_message("Applying automatic filter based on material data test instances", "info")
                self.apply_automatic_test_instance_filter()
            
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
                                
    def create_column_filters(self):
        """Create dropdown filters for each column"""
        # Clear existing filters
        for widget in self.column_filters_frame.winfo_children():
            widget.destroy()
        
        self.column_filters = {}
        self.column_filter_combos = {}
        
        if self.mtpl_df is None:
            return
            
        # Create filters for each column (skip the checkbox column)
        columns = list(self.mtpl_df.columns)
        
        # Create a scrollable frame for filters if needed
        filters_container = ttk.Frame(self.column_filters_frame)
        filters_container.pack(fill='x', padx=5, pady=5)
        
        # Arrange filters in rows (3 per row to fit better)
        filters_per_row = 3
        current_row = 0
        current_col = 0
        
        for i, col in enumerate(columns):
            # Get unique values for this column
            unique_values = sorted(self.mtpl_df[col].astype(str).unique())
            # Add "All" option at the beginning
            filter_options = ["All"] + unique_values
            
            # Create filter frame
            filter_frame = ttk.Frame(filters_container)
            filter_frame.grid(row=current_row, column=current_col, padx=5, pady=2, sticky='w')
            
            # Create label
            ttk.Label(filter_frame, text=f"{col}:", font=('Arial', 8)).pack(side='left', padx=(0, 5))
            
            # Create combobox
            filter_var = tk.StringVar(value="All")
            combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=filter_options, 
                               state="readonly", width=15, font=('Arial', 8))
            combo.pack(side='left')
            
            # Bind change event
            combo.bind('<<ComboboxSelected>>', lambda e, col=col: self.on_column_filter_change(col))
            
            # Store references
            self.column_filters[col] = filter_var
            self.column_filter_combos[col] = combo
            
            # Update grid position
            current_col += 1
            if current_col >= filters_per_row:
                current_col = 0
                current_row += 1
                
    def on_column_filter_change(self, column):
        """Handle column filter changes"""
        self.apply_all_filters()
        
    def apply_all_filters(self):
        """Apply both text search and column filters"""
        if not hasattr(self, 'all_mtpl_items') or not self.all_mtpl_items:
            return
            
        # Check if auto-filter is active
        text_filter = self.search_var.get().strip()
        is_auto_filtered = (text_filter.upper() == "AUTO-FILTERED BY MATERIAL DATA")
        
        if is_auto_filtered:
            # When auto-filter is active, we should re-apply the automatic filtering
            # instead of the normal text/column filtering
            self.apply_automatic_test_instance_filter()
            return
            
        filtered_items = []
        text_filter_lower = text_filter.lower()
        
        for item_data in self.all_mtpl_items:
            values = item_data['values']
            # Skip checkbox column for filtering
            row_values = values[1:]  
            
            # Apply text filter
            text_match = True
            if text_filter_lower:
                item_text = ' '.join(str(val).lower() for val in row_values)
                text_match = text_filter_lower in item_text
            
            # Apply column filters
            column_match = True
            if hasattr(self, 'column_filters'):
                for i, col in enumerate(self.mtpl_df.columns):
                    if col in self.column_filters:
                        filter_value = self.column_filters[col].get()
                        if filter_value != "All":
                            # Compare with the actual value in this column
                            if i < len(row_values) and str(row_values[i]) != filter_value:
                                column_match = False
                                break
            
            # Include item if it passes both filters
            if text_match and column_match:
                filtered_items.append(item_data)
        
        self.display_filtered_items(filtered_items)
        self.update_filter_status()
        self.update_selected_tests_count()
        
    def clear_all_filters(self):
        """Clear all filters including text search and column filters"""
        # Clear text search
        self.search_var.set("")
        
        # Clear column filters
        for col, filter_var in self.column_filters.items():
            filter_var.set("All")
            
        # Apply filters to show all items
        self.apply_all_filters()
        
        # Update status
        self.filter_status_label.configure(text="All filters cleared - showing all tests", foreground='blue')
            
    def on_search_change(self, *args):
        """Handle text search changes"""
        self.apply_all_filters()
        
    def export_selected_tests(self):
        """Export only the selected tests to CSV"""
        try:
            if not hasattr(self, 'all_mtpl_items') or not self.all_mtpl_items:
                messagebox.showwarning("Warning", "No MTPL data available to export")
                return
                
            # Get selected tests
            selected_items = []
            selected_count = 0
            
            print("Debug - Starting export of selected tests...")
            print(f"Debug - Total items to check: {len(self.all_mtpl_items)}")
            
            for i, item_data in enumerate(self.all_mtpl_items):
                print(f"Debug - Item {i}: tags={item_data.get('tags', 'No tags')}, values={item_data.get('values', 'No values')}")
                
                # Check if item is selected
                tags = item_data.get('tags', ())
                if 'checked' in tags:
                    selected_count += 1
                    values = item_data.get('values', [])
                    if len(values) > 1:
                        # Remove checkbox column (first column) and convert to list
                        row_data = list(values[1:])  # Skip checkbox column
                        selected_items.append(row_data)
                        print(f"Debug - Added selected item: {row_data}")
                    else:
                        print(f"Debug - Warning: Selected item has insufficient values: {values}")
            
            print(f"Debug - Found {selected_count} selected items, {len(selected_items)} valid for export")
            
            if not selected_items:
                messagebox.showwarning("Warning", "No tests selected for export")
                return
                
            self._export_to_csv(selected_items, "selected_tests.csv", f"Export {len(selected_items)} Selected Tests")
            
        except Exception as e:
            error_msg = f"Error in export_selected_tests: {str(e)}"
            print(f"Debug - {error_msg}")
            messagebox.showerror("Export Error", error_msg)
            if hasattr(self, 'log_message'):
                self.log_message(error_msg, "error")
        
    def export_visible_tests(self):
        """Export currently visible (filtered) tests to CSV"""
        if not hasattr(self, 'mtpl_tree') or not self.mtpl_tree.get_children():
            messagebox.showwarning("Warning", "No visible tests to export")
            return
            
        # Get all visible items from treeview
        visible_items = []
        for item_id in self.mtpl_tree.get_children():
            values = self.mtpl_tree.item(item_id, 'values')
            # Remove checkbox column
            row_data = values[1:]  # Skip checkbox column
            visible_items.append(row_data)
            
        if not visible_items:
            messagebox.showwarning("Warning", "No visible tests to export")
            return
            
        self._export_to_csv(visible_items, "visible_tests.csv", f"Export {len(visible_items)} Visible Tests")
        
    def export_all_tests(self):
        """Export all tests from MTPL to CSV"""
        if self.mtpl_df is None or self.mtpl_df.empty:
            messagebox.showwarning("Warning", "No MTPL data available to export")
            return
            
        # Convert dataframe to list of lists
        all_items = []
        for index, row in self.mtpl_df.iterrows():
            all_items.append(list(row))
            
        self._export_to_csv(all_items, "all_tests.csv", f"Export {len(all_items)} All Tests")
        
    def _export_to_csv(self, data_items, default_filename, dialog_title):
        """Helper method to export data to CSV file"""
        try:
            print(f"Debug - Starting CSV export with {len(data_items)} items")
            print(f"Debug - Sample data item: {data_items[0] if data_items else 'No data'}")
            
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title=dialog_title,
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not file_path:
                print("Debug - User cancelled file save dialog")
                return  # User cancelled
                
            print(f"Debug - Saving to: {file_path}")
                
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                if hasattr(self, 'mtpl_df') and self.mtpl_df is not None:
                    header = list(self.mtpl_df.columns)
                    writer.writerow(header)
                    print(f"Debug - Wrote header: {header}")
                else:
                    print("Debug - No MTPL dataframe available for header")
                    
                # Write data
                rows_written = 0
                for i, row_data in enumerate(data_items):
                    try:
                        writer.writerow(row_data)
                        rows_written += 1
                        if i < 3:  # Log first few rows for debugging
                            print(f"Debug - Wrote row {i}: {row_data}")
                    except Exception as row_error:
                        print(f"Debug - Error writing row {i}: {row_error}")
                        continue
                
                print(f"Debug - Successfully wrote {rows_written} rows")
                
            # Success message
            success_msg = f"✅ Exported {len(data_items)} tests to: {os.path.basename(file_path)}"
            if hasattr(self, 'log_message'):
                self.log_message(success_msg, "success")
            messagebox.showinfo("Export Successful", f"Successfully exported {len(data_items)} tests to:\n{file_path}")
            
        except Exception as e:
            error_msg = f"Failed to export tests: {str(e)}"
            print(f"Debug - Export error: {error_msg}")
            import traceback
            print(f"Debug - Full traceback: {traceback.format_exc()}")
            
            if hasattr(self, 'log_message'):
                self.log_message(f"❌ {error_msg}", "error")
            messagebox.showerror("Export Error", error_msg)
            
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
        try:
            print(f"Debug - select_all_tests called, total items: {len(self.all_mtpl_items)}")
            
            # Update all stored items
            for item_data in self.all_mtpl_items:
                values = list(item_data['values'])
                values[0] = '☑'  # Set checkbox to checked
                item_data['values'] = values
                item_data['tags'] = ('checked',)
                print(f"Debug - Updated item to checked: {values}")
                
            # Refresh the current display - handle auto-filter case properly
            search_text = self.search_var.get().strip()
            is_auto_filtered = (search_text.upper() == "AUTO-FILTERED BY MATERIAL DATA")
            
            if is_auto_filtered:
                # If auto-filter is active, we need to re-apply the automatic filtering
                # to show the same filtered set but with all selections
                self.apply_automatic_test_instance_filter()
                self.log_message("Selected all tests (including auto-filtered ones)", "success")
            else:
                # Normal filtering logic for manual filters
                search_text_lower = search_text.lower()
                if not search_text_lower:
                    filtered_items = self.all_mtpl_items
                else:
                    filtered_items = []
                    for item_data in self.all_mtpl_items:
                        item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                        if search_text_lower in item_text:
                            filtered_items.append(item_data)
                            
                self.display_filtered_items(filtered_items)
                self.log_message("Selected all tests", "success")
                
            self.update_selected_tests_count()
            
        except Exception as e:
            self.log_message(f"Error selecting all tests: {e}", "error")
            print(f"Error in select_all_tests: {e}")
        
    def clear_test_selection(self):
        """Clear all test selections (including filtered ones)"""
        try:
            # Update all stored items
            for item_data in self.all_mtpl_items:
                values = list(item_data['values'])
                values[0] = '☐'  # Set checkbox to unchecked
                item_data['values'] = values
                item_data['tags'] = ('unchecked',)
                
            # Refresh the current display - handle auto-filter case properly
            search_text = self.search_var.get().strip()
            is_auto_filtered = (search_text.upper() == "AUTO-FILTERED BY MATERIAL DATA")
            
            if is_auto_filtered:
                # If auto-filter is active, we need to re-apply the automatic filtering
                # to show the same filtered set but with cleared selections
                self.apply_automatic_test_instance_filter()
                self.log_message("Cleared selections for auto-filtered tests", "success")
            else:
                # Normal filtering logic for manual filters
                search_text_lower = search_text.lower()
                if not search_text_lower:
                    filtered_items = self.all_mtpl_items
                else:
                    filtered_items = []
                    for item_data in self.all_mtpl_items:
                        item_text = ' '.join(str(val).lower() for val in item_data['values'][1:])
                        if search_text_lower in item_text:
                            filtered_items.append(item_data)
                            
                self.display_filtered_items(filtered_items)
                self.log_message("Cleared all test selections", "success")
                
            self.update_selected_tests_count()
            
        except Exception as e:
            self.log_message(f"Error clearing test selection: {e}", "error")
            print(f"Error in clear_test_selection: {e}")
        
    def update_selected_tests_count(self):
        """Update the count of selected tests"""
        count = 0
        checked_items = []
        # Count from stored data, not just visible items
        for i, item_data in enumerate(self.all_mtpl_items):
            if 'checked' in item_data['tags']:
                count += 1
                checked_items.append(f"Item {i}: {item_data['values'][1] if len(item_data['values']) > 1 else 'Unknown'}")
                print(f"Debug - Checked item {i}: {item_data['values']}")
        
        print(f"Debug - Total checked count: {count}")
        if count > 0:
            print(f"Debug - First few checked items: {checked_items[:3]}")
        
        self.selected_tests_label.configure(text=str(count))
        
    def get_selected_tests(self):
        """Get list of selected test names from both MTPL and CLKUtils tabs"""
        selected_tests = []
        
        # Check if CLKUtils mode is enabled
        if hasattr(self, 'run_clkutils_var') and self.run_clkutils_var.get():
            # Only get CLKUtils tests
            if hasattr(self, 'all_clkutils_items'):
                for item_data in self.all_clkutils_items:
                    if 'checked' in item_data['tags']:
                        test_name = item_data['test_name']
                        selected_tests.append(test_name)
                        print(f"Debug - Added CLKUtils test: {test_name}")
            print(f"Debug - CLKUtils mode: {len(selected_tests)} tests selected")
        else:
            # Only get MTPL tests (original behavior)
            for item_data in self.all_mtpl_items:
                if 'checked' in item_data['tags']:
                    values = item_data['values']
                    # Debug: Print the values to understand the structure
                    print(f"Debug - Selected MTPL item values: {values}")
                    # The first column is checkbox, so test name should be in index 2 (third column)
                    # Based on the processing logic where row[2] is the test name
                    if len(values) > 2:  
                        test_name = values[2]  # This should be the test name column
                        selected_tests.append(test_name)
                        print(f"Debug - Added MTPL test: {test_name}")
            print(f"Debug - MTPL mode: {len(selected_tests)} tests selected")
        
        print(f"Debug - Total selected tests: {selected_tests}")
        return selected_tests
    
    def toggle_column_filters(self):
        """Toggle visibility of column filters"""
        if hasattr(self, 'column_filters_frame'):
            if self.column_filters_frame.winfo_viewable():
                self.column_filters_frame.pack_forget()
                self.toggle_filters_btn.configure(text="▼ Show Column Filters")
                self.filter_status_label.configure(text="Column filters hidden")
            else:
                self.column_filters_frame.pack(fill='x', padx=10, pady=5, after=self.search_controls_frame)
                self.toggle_filters_btn.configure(text="▲ Hide Column Filters")
                self.update_filter_status()
    
    def refresh_filters(self):
        """Refresh all filters and update display"""
        # Clear search box
        self.search_var.set("")
        
        # Reset all column filters
        if hasattr(self, 'column_filters'):
            for filter_var in self.column_filters.values():
                filter_var.set("")
        
        # Update status
        self.filter_status_label.configure(text="All filters cleared")
        self.active_filters_label.configure(text="Active filters: 0")
        
        # Refresh the display
        self.apply_all_filters()
    
    def update_filter_status(self):
        """Update the filter status display"""
        # Check if auto-filter is active - if so, don't override the specific message
        if (hasattr(self, 'search_var') and 
            self.search_var.get().strip().upper() == "AUTO-FILTERED BY MATERIAL DATA"):
            # Auto-filter is active, don't override the specific status message
            # The filter_status_label should already have the detailed auto-filter message
            if hasattr(self, 'active_filters_label'):
                self.active_filters_label.configure(text="Auto-filter active", foreground='green')
            return
        
        # Normal filter status logic for manual filters
        active_count = 0
        
        # Check search filter
        if self.search_var.get().strip():
            active_count += 1
        
        # Check column filters
        if hasattr(self, 'column_filters'):
            for filter_var in self.column_filters.values():
                if filter_var.get() and filter_var.get() != "All":
                    active_count += 1
        
        if active_count == 0:
            self.filter_status_label.configure(text="No active filters", foreground='gray')
            if hasattr(self, 'active_filters_label'):
                self.active_filters_label.configure(text="Active filters: 0", foreground='gray')
        else:
            self.filter_status_label.configure(text="Filters applied", foreground='green')
            if hasattr(self, 'active_filters_label'):
                self.active_filters_label.configure(text=f"Active filters: {active_count}", foreground='blue')
    
    def select_all_visible_tests(self):
        """Select all currently visible tests"""
        try:
            # Check if auto-filter is active
            search_text = self.search_var.get().strip()
            is_auto_filtered = (search_text.upper() == "AUTO-FILTERED BY MATERIAL DATA")
            
            if is_auto_filtered:
                # When auto-filter is active, get currently displayed items from treeview
                # This ensures we work with the actual filtered results
                self.log_message("Auto-filter detected - selecting all currently displayed tests", "info")
                
                # Get all currently displayed items from the treeview
                visible_items = []
                updates_made = 0
                
                for item_id in self.mtpl_tree.get_children():
                    item_values = list(self.mtpl_tree.item(item_id, 'values'))
                    # Mark as selected
                    item_values[0] = '☑'
                    
                    # Find corresponding item in all_mtpl_items to update the source data
                    # Use more robust matching with type conversion
                    match_found = False
                    for item_data in self.all_mtpl_items:
                        # Compare all values except the checkbox column with type conversion
                        stored_values = [str(v) for v in item_data['values'][1:]]
                        current_values = [str(v) for v in item_values[1:]]
                        
                        if stored_values == current_values:
                            item_data['values'][0] = '☑'
                            item_data['tags'] = ('checked',)
                            updates_made += 1
                            match_found = True
                            print(f"Debug - Updated stored item: {item_data['values']}")
                            break
                    
                    if not match_found:
                        print(f"Debug - No match found for treeview item: {item_values}")
                    
                    # Update the treeview item immediately
                    row_tag = 'evenrow' if len(visible_items) % 2 == 0 else 'oddrow'
                    self.mtpl_tree.item(item_id, values=item_values, tags=('checked', row_tag))
                    visible_items.append(item_values)
                
                self.log_message(f"Selected {len(visible_items)} auto-filtered tests (updated {updates_made} stored items)", "success")
                print(f"Debug - Auto-filter mode: visible items={len(visible_items)}, stored updates={updates_made}")
                
            else:
                # Normal filtering logic for manual filters
                search_text_lower = search_text.lower()
                
                # Apply current filters to get visible items
                filtered_items = self.all_mtpl_items.copy()
                
                # Apply search filter
                if search_text_lower:
                    filtered_items = [
                        item for item in filtered_items
                        if search_text_lower in ' '.join(str(val).lower() for val in item['values'][1:])
                    ]
                
                # Apply column filters
                if hasattr(self, 'column_filters'):
                    for col_name, filter_var in self.column_filters.items():
                        filter_value = filter_var.get()
                        if filter_value and filter_value != "All":
                            col_index = self.get_column_index(col_name)
                            if col_index is not None:
                                filtered_items = [
                                    item for item in filtered_items
                                    if str(item['values'][col_index]).strip() == filter_value.strip()
                                ]
                
                # Mark filtered items as selected
                for item_data in filtered_items:
                    values = list(item_data['values'])
                    values[0] = '☑'  # Set checkbox to checked
                    item_data['values'] = values
                    item_data['tags'] = ('checked',)
                
                # Refresh display
                self.display_filtered_items(filtered_items)
                self.log_message(f"Selected {len(filtered_items)} manually filtered tests", "success")
                print(f"Debug - Manual filter mode: selected {len(filtered_items)} items")
            
            # Update the selected tests count
            self.update_selected_tests_count()
            
        except Exception as e:
            self.log_message(f"Error selecting all visible tests: {e}", "error")
            print(f"Error in select_all_visible_tests: {e}")
    
    def invert_selection(self):
        """Invert the current selection"""
        try:
            # Check if auto-filter is active
            search_text = self.search_var.get().strip()
            is_auto_filtered = (search_text.upper() == "AUTO-FILTERED BY MATERIAL DATA")
            
            if is_auto_filtered:
                # When auto-filter is active, work with currently displayed items from treeview
                self.log_message("Auto-filter detected - inverting selection for currently displayed tests", "info")
                
                # Get all currently displayed items from the treeview and invert their selection
                visible_items = []
                updates_made = 0
                
                for item_id in self.mtpl_tree.get_children():
                    item_values = list(self.mtpl_tree.item(item_id, 'values'))
                    current_state = item_values[0]
                    
                    # Invert selection
                    item_values[0] = '☐' if current_state == '☑' else '☑'
                    new_tag = 'unchecked' if current_state == '☑' else 'checked'
                    
                    # Find corresponding item in all_mtpl_items to update the source data
                    # Use more robust matching with type conversion
                    match_found = False
                    for item_data in self.all_mtpl_items:
                        # Compare all values except the checkbox column with type conversion
                        stored_values = [str(v) for v in item_data['values'][1:]]
                        current_values = [str(v) for v in item_values[1:]]
                        
                        if stored_values == current_values:
                            item_data['values'][0] = item_values[0]
                            item_data['tags'] = (new_tag,)
                            updates_made += 1
                            match_found = True
                            print(f"Debug - Updated stored item during invert: {item_data['values']}")
                            break
                    
                    if not match_found:
                        print(f"Debug - No match found during invert for treeview item: {item_values}")
                    
                    # Update the treeview item immediately
                    row_tag = 'evenrow' if len(visible_items) % 2 == 0 else 'oddrow'
                    self.mtpl_tree.item(item_id, values=item_values, tags=(new_tag, row_tag))
                    visible_items.append(item_values)
                
                self.log_message(f"Inverted selection for {len(visible_items)} auto-filtered tests (updated {updates_made} stored items)", "success")
                print(f"Debug - Auto-filter invert: visible items={len(visible_items)}, stored updates={updates_made}")
                
            else:
                # Normal filtering logic for manual filters
                search_text_lower = search_text.lower()
                
                # Apply current filters to get visible items
                filtered_items = self.all_mtpl_items.copy()
                
                # Apply search filter
                if search_text_lower:
                    filtered_items = [
                        item for item in filtered_items
                        if search_text_lower in ' '.join(str(val).lower() for val in item['values'][1:])
                    ]
                
                # Apply column filters
                if hasattr(self, 'column_filters'):
                    for col_name, filter_var in self.column_filters.items():
                        filter_value = filter_var.get()
                        if filter_value and filter_value != "All":
                            col_index = self.get_column_index(col_name)
                            if col_index is not None:
                                filtered_items = [
                                    item for item in filtered_items
                                    if str(item['values'][col_index]).strip() == filter_value.strip()
                                ]
                
                # Invert selection for visible items
                for item_data in filtered_items:
                    values = list(item_data['values'])
                    current_state = values[0]
                    values[0] = '☐' if current_state == '☑' else '☑'
                    item_data['values'] = values
                    item_data['tags'] = ('unchecked' if current_state == '☑' else 'checked',)
                
                # Refresh display
                self.display_filtered_items(filtered_items)
                self.log_message(f"Inverted selection for {len(filtered_items)} manually filtered tests", "success")
                print(f"Debug - Manual filter invert: inverted {len(filtered_items)} items")
            
            # Update the selected tests count
            self.update_selected_tests_count()
            
        except Exception as e:
            self.log_message(f"Error inverting selection: {e}", "error")
            print(f"Error in invert_selection: {e}")
    
    def open_reorder_window(self):
        """Open a window to reorder selected tests"""
        selected_tests = self.get_selected_tests()
        if not selected_tests:
            messagebox.showwarning("No Selection", "Please select tests to reorder first.")
            return
        
        # Create reorder window
        reorder_window = tk.Toplevel(self.root)
        reorder_window.title("Reorder Selected Tests")
        reorder_window.geometry("600x500")
        reorder_window.transient(self.root)
        reorder_window.grab_set()
        
        # Instructions
        ttk.Label(reorder_window, text="🔄 Drag and drop tests to reorder them", 
                 font=('Arial', 11, 'bold')).pack(pady=10)
        
        # Create listbox with scrollbar
        list_frame = ttk.Frame(reorder_window)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        reorder_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                    selectmode=tk.SINGLE, height=15)
        reorder_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.configure(command=reorder_listbox.yview)
        
        # Populate listbox with selected tests
        test_data = selected_tests.copy()
        for test_name in test_data:
            reorder_listbox.insert(tk.END, f"📝 {test_name}")
        
        # Mouse drag functionality
        def on_drag_start(event):
            reorder_listbox.selection_clear(0, tk.END)
            reorder_listbox.selection_set(reorder_listbox.nearest(event.y))
            reorder_listbox.drag_start_index = reorder_listbox.nearest(event.y)
        
        def on_drag_motion(event):
            current_index = reorder_listbox.nearest(event.y)
            if hasattr(reorder_listbox, 'drag_start_index') and current_index != reorder_listbox.drag_start_index:
                reorder_listbox.selection_clear(0, tk.END)
                reorder_listbox.selection_set(current_index)
        
        def on_drag_release(event):
            if hasattr(reorder_listbox, 'drag_start_index'):
                start_index = reorder_listbox.drag_start_index
                end_index = reorder_listbox.nearest(event.y)
                
                if start_index != end_index and 0 <= end_index < len(test_data):
                    # Move the item
                    item_to_move = test_data.pop(start_index)
                    test_data.insert(end_index, item_to_move)
                    
                    # Update listbox
                    reorder_listbox.delete(0, tk.END)
                    for test_name in test_data:
                        reorder_listbox.insert(tk.END, f"📝 {test_name}")
        
        reorder_listbox.bind('<Button-1>', on_drag_start)
        reorder_listbox.bind('<B1-Motion>', on_drag_motion)
        reorder_listbox.bind('<ButtonRelease-1>', on_drag_release)
        
        # Control buttons
        button_frame = ttk.Frame(reorder_window)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        def move_up():
            selection = reorder_listbox.curselection()
            if selection and selection[0] > 0:
                idx = selection[0]
                # Swap in data
                test_data[idx], test_data[idx-1] = test_data[idx-1], test_data[idx]
                # Update display
                reorder_listbox.delete(0, tk.END)
                for test_name in test_data:
                    reorder_listbox.insert(tk.END, f"📝 {test_name}")
                reorder_listbox.selection_set(idx-1)
        
        def move_down():
            selection = reorder_listbox.curselection()
            if selection and selection[0] < len(test_data) - 1:
                idx = selection[0]
                # Swap in data
                test_data[idx], test_data[idx+1] = test_data[idx+1], test_data[idx]
                # Update display
                reorder_listbox.delete(0, tk.END)
                for test_name in test_data:
                    reorder_listbox.insert(tk.END, f"📝 {test_name}")
                reorder_listbox.selection_set(idx+1)
        
        def apply_order():
            # Update the order in the main data
            self.reorder_selected_tests(test_data)
            self.show_reorder_status(f"Order applied! {len(test_data)} tests reordered.")
            reorder_window.destroy()
        
        ttk.Button(button_frame, text="⬆️ Move Up", command=move_up).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="⬇️ Move Down", command=move_down).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="✅ Apply Order", command=apply_order).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="❌ Cancel", command=reorder_window.destroy).pack(side='right')
    
    def reorder_selected_tests(self, new_order):
        """Reorder the selected tests in the main data according to new_order"""
        # Create a mapping of test names to their data
        selected_items = {}
        unselected_items = []
        
        for item_data in self.all_mtpl_items:
            if 'checked' in item_data['tags']:
                test_name = item_data['values'][2] if len(item_data['values']) > 2 else ""
                selected_items[test_name] = item_data
            else:
                unselected_items.append(item_data)
        
        # Rebuild the list with new order
        reordered_items = []
        
        # Add selected items in the new order
        for test_name in new_order:
            if test_name in selected_items:
                reordered_items.append(selected_items[test_name])
        
        # Add unselected items at the end
        reordered_items.extend(unselected_items)
        
        # Update the main data
        self.all_mtpl_items = reordered_items
        
        # Refresh the display
        self.apply_all_filters()
    
    def show_reorder_status(self, message):
        """Show reorder status message"""
        if hasattr(self, 'order_info_frame'):
            self.order_info_frame.pack(fill='x', padx=10, pady=5)
            self.order_info_label.configure(text=message)
            # Hide message after 3 seconds
            self.root.after(3000, lambda: self.order_info_frame.pack_forget())
    
    def get_column_index(self, column_name):
        """Get the index of a column by name"""
        if hasattr(self, 'mtpl_tree') and self.mtpl_tree:
            columns = self.mtpl_tree['columns']
            try:
                return columns.index(column_name) + 1  # +1 because first column is checkbox
            except ValueError:
                return None
        return None
        
    def browse_output_folder(self):
        """Browse for output folder"""
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            # Normalize the folder path to handle UNC paths and strip quotes
            normalized_path = self.normalize_unc_path(folder_path)
            self.output_path_var.set(normalized_path)
            
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
            csv_path = self.normalize_unc_path(self.mtpl_csv_path)
            if 'Modules' in csv_path:
                base_path = csv_path.split('Modules')[0].rstrip(os.sep)
                default_path = os.path.join(base_path, 'dataOut')
            else:
                default_path = os.path.join(os.path.dirname(csv_path), 'dataOut')
            self.output_path_var.set(self.normalize_unc_path(default_path))
            
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
        
        # Check if CLKUtils mode is enabled
        clkutils_mode = hasattr(self, 'run_clkutils_var') and self.run_clkutils_var.get()
        
        if clkutils_mode:
            # In CLKUtils mode, we don't need MTPL file
            if not hasattr(self, 'all_clkutils_items') or not self.all_clkutils_items:
                messagebox.showerror("Error", "Please load CLKUtils tests first")
                return
        else:
            # In MTPL mode, we need MTPL file
            if self.mtpl_df is None:
                messagebox.showerror("Error", "Please load MTPL file first")
                return
            
        selected_tests = self.get_selected_tests()
        print(f"Debug - Selected tests from start_processing: {selected_tests}")
        self.log_message(f"Selected tests: {selected_tests}")
        self.log_message(f"Processing mode: {'CLKUtils' if clkutils_mode else 'MTPL'}")
        
        if not selected_tests:
            test_source = "CLKUtils tests" if clkutils_mode else "MTPL tests"
            messagebox.showerror("Error", f"Please select at least one test from {test_source}")
            return
            
        output_folder = self.output_path_var.get()
        # Normalize the output folder path to handle UNC paths and strip quotes
        if output_folder:
            output_folder = self.normalize_unc_path(output_folder)
            
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
        
    def get_testtimes(self):
        """Get test times using the pyuber_query get_testtimes function"""
        try:
            # Check if PyUber is available
            if not PYUBER_AVAILABLE:
                messagebox.showerror("Error", "PyUber module is not available. Please ensure PyUber is properly installed.")
                return
            
            # Validate that we have material data loaded
            if not hasattr(self, 'material_data') or not self.material_data:
                messagebox.showerror("Error", "Please create or load material data first")
                return
            
            # Get selected tests
            selected_tests = self.get_selected_tests()
            if not selected_tests:
                messagebox.showerror("Error", "Please select at least one test")
                return
            
            # Get material data parameters
            lot_str = self.lot_var.get() if hasattr(self, 'lot_var') and self.lot_var.get() else 'Not Null'
            lot = [item.strip() for item in lot_str.split(',')] if lot_str else ['Not Null']
            
            wafer_str = self.wafer_var.get() if hasattr(self, 'wafer_var') and self.wafer_var.get() else 'Not Null'
            wafer = [item.strip() for item in wafer_str.split(',')] if wafer_str else ['Not Null']
            
            programs_str = self.program_var.get() if hasattr(self, 'program_var') and self.program_var.get() else ''
            programs = [item.strip() for item in programs_str.split(',') if item.strip()] if programs_str else []
            
            prefetch = self.prefetch_var.get() if hasattr(self, 'prefetch_var') and self.prefetch_var.get() else '3'
            
            databases_str = self.database_var.get() if hasattr(self, 'database_var') and self.database_var.get() else 'D1D_PROD_XEUS'
            databases = [item.strip() for item in databases_str.split(',')] if databases_str else ['D1D_PROD_XEUS']
            
            # Get output folder
            output_folder = self.output_path_var.get() if hasattr(self, 'output_path_var') else ''
            if output_folder:
                output_folder = self.normalize_unc_path(output_folder)
                if not os.path.exists(output_folder):
                    try:
                        os.makedirs(output_folder, exist_ok=True)
                        self.log_message(f"Created output directory: {output_folder}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to create output directory: {str(e)}")
                        return
                place_in = output_folder + os.sep if output_folder else ''
            else:
                place_in = ''
            
            # Extract module name intelligently based on mode
            clkutils_mode = hasattr(self, 'run_clkutils_var') and self.run_clkutils_var.get()
            
            if clkutils_mode:
                # In CLKUtils mode, try to extract common prefix from test names
                if selected_tests:
                    # Try to find a common pattern in test names
                    # Look for common prefixes or patterns that could indicate module name
                    first_test = selected_tests[0]
                    
                    if '::' in first_test:
                        module_name = first_test.split('::')[0]  # Use everything before '::'
                    else:
                        module_name = "CLK_PLL_"+ first_test.split('_')[1]
            else:
                # In MTPL mode, extract from MTPL file path
                mtpl_path = self.mtpl_file_path.get() if hasattr(self, 'mtpl_file_path') else ""
                if mtpl_path:
                    # Extract filename from path
                    filename = os.path.basename(mtpl_path)
                    if filename.endswith('.mtpl'):
                        # Remove .mtpl extension to get module name
                        module_name = filename[:-5]  # Remove last 5 characters (.mtpl)
                    else:
                        # Fallback to removing any extension
                        module_name = os.path.splitext(filename)[0]
                    
                    # Clean up module name (remove invalid characters for file names)
                    module_name = ''.join(c for c in module_name if c.isalnum() or c in '_-')
                    
                    if not module_name:  # If cleaning resulted in empty string
                        module_name = "MTPL_Module"
                else:
                    # Fallback to program name if available
                    module_name = programs[0] if programs else "default_module"
            
            # Start processing in a separate thread to avoid UI blocking
            import threading
            
            def run_testtimes():
                try:
                    # Call the get_testtimes function from pyuber_query
                    self.log_message("Calling get_testtimes function...")
                    
                    '''py.get_testtimes(
                        tests=selected_tests,
                        module_name=module_name,
                        lot=lot,
                        wafer_id=wafer,
                        programs=programs,
                        prefetch=prefetch,
                        databases=databases,
                        place_in=place_in
                    )'''
                    py.get_testtimes(
                        module_name=module_name,
                        lot=lot,
                        wafer_id=wafer,
                        programs=programs,
                        prefetch=prefetch,
                        databases=databases,
                        place_in=place_in
                    )
                    # Log success
                    self.log_message("✅ Test times retrieval completed successfully!")
                    if place_in:
                        expected_file = f'{place_in}testtime_output_{module_name}.csv'
                        if os.path.exists(expected_file):
                            self.log_message(f"📁 Output file created: {expected_file}")
                        else:
                            self.log_message("⚠️ Output file not found at expected location")
                    
                    # Show success message
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Test times retrieved successfully!"))
                    
                except Exception as e:
                    error_msg = f"Error getting test times: {str(e)}"
                    self.log_message(f"❌ {error_msg}")
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
            # Start the thread
            thread = threading.Thread(target=run_testtimes, daemon=True)
            thread.start()
            
        except Exception as e:
            error_msg = f"Error initiating test times retrieval: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
        
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
            
            # Normalize path separators for Windows, but preserve UNC paths (from master.py)
            mtpl_path = self.normalize_unc_path(mtpl_path)
            
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
            place_temp = place_in
            for program in program_list:
                if not self.processing:
                    break
                    
                self.log_message(f"Processing program: {program}")
                
                # Create output folder if specified (from master.py)
                place_in = place_temp
                if place_in:
                    place_in = os.path.normpath(place_in)
                    os.makedirs(place_in, exist_ok=True)
                    place_in = place_in + os.sep
                    if len(program_list) >1:
                        place_in = os.path.normpath(place_in + f'{program}_output')
                        os.makedirs(place_in, exist_ok=True)
                        place_in = place_in + os.sep
                else:
                    place_in = os.path.normpath(os.getcwd() + os.sep + f'{program}_output')
                    os.makedirs(place_in, exist_ok=True)
                    place_in = place_in + os.sep
                    
                self.log_message(f"Output directory: {place_in}")
                intermediary_file_list = []
                output_files = []
                tag_header_names = []  # Initialize for stacking functionality
                tag_header_names_chunks = []
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

                    # Check if CLKUtils processing is enabled and test contains CLKUTILS
                    if (hasattr(self, 'run_clkutils_var') and self.run_clkutils_var.get()):
                        if 'CLKUTILS' in test.upper():
                            # ClkUtils do not require mtpl parsing
                            self.log_message(f"Processing ClkUtils for test: {test}")
                            
                            # Ensure configFile_DMR.json exists in current working directory
                            config_file = 'configFile_DMR.json'
                            if not os.path.exists(config_file):
                                # Try looking in the script directory as backup
                                script_dir_config = os.path.join(os.path.dirname(__file__), config_file)
                                if os.path.exists(script_dir_config):
                                    config_file = script_dir_config
                                    self.log_message(f"Using config file from script directory: {script_dir_config}")
                                else:
                                    error_msg = (f"Error: {config_file} not found!\n"
                                               f"Current working directory: {os.getcwd()}\n"
                                               f"Please ensure {config_file} is in the current working directory.")
                                    self.log_message(error_msg, "error")
                                    continue
                            else:
                                self.log_message(f"Using config file from current directory: {os.path.abspath(config_file)}")
                            
                            indexed_file,tag_header_names = clk.process_json_to_csv(config_file,test,place_in,True)
                            tag_header_names_chunks.append(tag_header_names)
                            intermediary_file_list.append(indexed_file)
                            self.log_message(f"Performing data request for test: {test}")
                            datainput_file,datacombine_file=py.uber_request(indexed_file,test,'ClkUtils',place_in,program, '', lot_list, wafer_list, prefetch, databases)
                            intermediary_file_list.append(datainput_file)
                            output_files.append(datacombine_file)
                            current_iteration += 1
                            self.update_progress(current_iteration, total_iterations, f"Completed test: {test}")
                        continue
                 
                    # Find matching row in MTPL dataframe (enhanced from master.py)
                    matching_rows = self.mtpl_df[self.mtpl_df.iloc[:, 1] == test]  # Assuming test name is in column 1
                    
                    if matching_rows.empty:
                        self.log_message(f"No matching MTPL entry found for test: {test}")
                        current_iteration += 1
                        self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (no MTPL entry)")
                        continue
                        
                    row = matching_rows.iloc[0]

                    # Check for SIO and process user variables
                    if 'sio' in row.iloc[2].lower():
                        self.log_message(f"Processing SIO for test: {test}")
                        
                        # Extract the module name from the MTPL path to find the .usrv file
                        mtpl_dir = os.path.dirname(mtpl_path)
                        module_name_from_path = os.path.basename(mtpl_dir)
                        usrv_file_path = os.path.join(mtpl_dir, f"{module_name_from_path}.usrv")
                        
                        if os.path.exists(usrv_file_path):
                            self.log_message(f"Found .usrv file: {usrv_file_path}")
                            
                            # Parse the .usrv file and resolve the configuration file path
                            try:
                                resolved_config_path = self.resolve_sio_config_path(row.iloc[2], usrv_file_path, base_dir)
                                if resolved_config_path:
                                    self.log_message(f"Resolved SIO config path: {resolved_config_path}")
                                    # Override the config_path for SIO processing
                                    config_path = resolved_config_path.replace(base_dir, "").lstrip(os.sep)
                                    config_path = config_path.replace("\\", "/")  # Normalize path separators
                                else:
                                    self.log_message(f"Failed to resolve SIO config path for: {row.iloc[2]}")
                                    current_iteration += 1
                                    self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (SIO config resolution failed)")
                                    continue
                            except Exception as e:
                                self.log_message(f"Error processing SIO config: {str(e)}")
                                current_iteration += 1
                                self.update_progress(current_iteration, total_iterations, f"Skipped test: {test} (SIO processing error)")
                                continue
                        else:
                            self.log_message(f"Warning: .usrv file not found: {usrv_file_path}")
                            # Fall back to original processing
                            config_path = fi.process_file_input(row.iloc[2][row.iloc[2].find('Modules'):].strip('\"'))
                    else:
                        # Original processing for non-SIO tests
                        config_path = fi.process_file_input(row.iloc[2][row.iloc[2].find('Modules'):].strip('\"'))
                     
                    test_type = row.iloc[0]  # Assuming test type is in column 0
                    mode = row.iloc[4]  # Assuming mode is in column 4
                    mode=str(mode)
                    module_name = fi.get_module_name(config_path).strip('\\').strip('//')
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
                            indexed_file,csv_identifier,tag_header_names = ind.index_CTV(test_file, test,module_name,place_in)
                            tag_header_names_chunks.append(tag_header_names)
                            intermediary_file_list.append(indexed_file)
                            self.log_message(f"Performing data request for test: {test}")
                            datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                            intermediary_file_list.append(datainput_file)
                            output_files.append(datacombine_file)

                        elif "smartctv" in test_type.lower():  # SMART CTV loop/check logic and indexing
                            if "ctvtag" in str(mode).lower():
                                mode = mode.strip('\"\'')
                                config_number = ''
                                self.log_message(f"Processing CTV Tag SmartCtvDc for test: {test}")
                                self.log_message(f"Config number: {config_number}")
                                self.update_progress(current_iteration + 0.3, total_iterations, f"Processing SmartCTV for: {test}")
                                try:
                                    ctv_files, ITUFF_suffixes, config_numbers = sm.process_SmartCTV(base_dir, test_file, config_number, place_in)
                                    for ctv_file, ITUFF_suffix in zip(ctv_files, ITUFF_suffixes):
                                        intermediary_file_list.append(ctv_file)
                                        test = test + ITUFF_suffix
                                        self.update_progress(current_iteration + 0.6, total_iterations, f"Indexing SmartCTV for: {test}")
                                        indexed_file,csv_identifier,tag_header_names = ind.index_CTV(ctv_file, test,module_name,place_in,mode,config_number)
                                        tag_header_names_chunks.append(tag_header_names)
                                        intermediary_file_list.append(indexed_file)
                                        self.log_message(f"Performing data request for test: {test}")
                                        # Set need_suffix to True for SmartCTV processing
                                        need_suffix = True
                                        datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases,config_number,mode)
                                        intermediary_file_list.append(datainput_file)
                                        output_files.append(datacombine_file)
                                        test = test.replace(ITUFF_suffix, '')

                                except Exception as e:
                                    self.log_message(f"❌ Error in SmartCTV processing for test {test}: {str(e)}")
                                    current_iteration += 1
                                    self.update_progress(current_iteration, total_iterations, f"Failed test: {test} (SmartCTV error)")
                                    continue
                            else:
                                config_number = str(int(row.iloc[3]))                    
                                try:
                                    ctv_file, ITUFF_suffixes, config_numbers = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                                    if isinstance(ctv_file,list):
                                        ctv_file = ctv_file[0]  # Use the first file if multiple are returned
                                        ITUFF_suffix = ITUFF_suffixes[0] 
                                        test = test + ITUFF_suffix
                                        config_numbers = config_numbers[0]
                                except:
                                    ctv_file = sm.process_SmartCTV(base_dir, test_file,config_number,place_in)
                                    if isinstance(ctv_file,tuple):
                                        ctv_file = ctv_file[0][0]
                                # When config_number is provided, process_SmartCTV returns only the ctv_file path
                                intermediary_file_list.append(ctv_file)
                                self.update_progress(current_iteration + 0.6, total_iterations, f"Indexing SmartCTV for: {test}")
                                indexed_file,csv_identifier,tag_header_names = ind.index_CTV(ctv_file, test,module_name,place_in)
                                tag_header_names_chunks.append(tag_header_names)
                                intermediary_file_list.append(indexed_file)
                                self.log_message(f"Performing data request for test: {test}")
                                # Set need_suffix to True for SmartCTV processing
                                need_suffix = True
                                datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
                                intermediary_file_list.append(datainput_file)
                                output_files.append(datacombine_file)
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
                
                # Stack output files if requested (from master.py)
                stacked_files = []
                if output_files:
                    self.log_message("Stacking output files for JMP...")
                    try:
                        import jmp_python as jmp
                        for output_file, tag_header_names in zip(output_files, tag_header_names_chunks):
                            if os.path.exists(output_file):
                                self.log_message(f"Stacking file: {os.path.basename(output_file)}")
                                stacked_file = jmp.stack_and_split_file(output_file, tag_header_names)
                                stacked_files.append(stacked_file)
                                self.log_message(f"Created stacked file: {os.path.basename(stacked_file)}")
                        self.log_message(f"Successfully stacked {len(stacked_files)} files")
                    except ImportError:
                        self.log_message("Warning: jmp_python module not found - cannot stack files", "warning")
                    except Exception as e:
                        self.log_message(f"Error stacking files: {str(e)}", "error")
                
                # Run JMP on stacked files if requested (from master.py)
                if self.run_jmp_var.get() and stacked_files:
                    self.log_message("Running JMP on combined stacked files...")
                    try:
                        import jmp_python as jmp
                        jmp_executable_path = fi.find_latest_jmp_pro_path()
                        
                        if jmp_executable_path:
                            self.log_message(f"Found JMP executable: {jmp_executable_path}")
                            
                            # Verify JMP executable exists and is accessible
                            if not os.path.exists(jmp_executable_path):
                                self.log_message(f"Error: JMP executable not found at {jmp_executable_path}", "error")
                                return
                            
                            # Test JMP executable access
                            try:
                                import subprocess
                                test_result = subprocess.run([jmp_executable_path, "-h"], 
                                                           capture_output=True, timeout=10)
                                self.log_message("JMP executable access test passed")
                            except subprocess.TimeoutExpired:
                                self.log_message("JMP executable test timed out (this may be normal)")
                            except PermissionError as pe:
                                self.log_message(f"Permission error accessing JMP: {pe}", "error")
                                self.log_message("Try running as administrator or check JMP permissions", "warning")
                                return
                            except Exception as test_e:
                                self.log_message(f"JMP access test warning: {test_e}", "warning")
                            
                            # Combine all stacked files into one master CSV for JMP
                            self.log_message(f"Combining {len(stacked_files)} stacked files for comprehensive JMP analysis...")
                            try:
                                combined_csv_path = jmp.combine_stacked_files(stacked_files, self.output_folder)
                                
                                if combined_csv_path and os.path.exists(combined_csv_path):
                                    self.log_message(f"Successfully created combined dataset: {os.path.basename(combined_csv_path)}")
                                    self.log_message("Opening combined data in JMP for comprehensive analysis...")
                                    
                                    # Run JMP on the combined file (single window with all data)
                                    jmp.run_combined_jsl(combined_csv_path, jmp_executable_path)
                                    self.log_message("JMP analysis launched successfully!")
                                    self.log_message("JMP will display multiple analysis views of your combined data in organized windows.")
                                    self.log_message("All your stacked data is now in one comprehensive JMP analysis.")
                                else:
                                    self.log_message("Failed to create combined CSV file", "error")
                                    
                            except Exception as combine_e:
                                self.log_message(f"Error combining stacked files: {combine_e}", "error")
                                # Fallback to individual file processing if combining fails
                                self.log_message("Falling back to individual file processing...", "warning")
                                for stacked_file in stacked_files:
                                    if os.path.exists(stacked_file):
                                        self.log_message(f"Running JMP on: {os.path.basename(stacked_file)}")
                                        try:
                                            jmp.run_jsl(stacked_file, jmp_executable_path)
                                            self.log_message(f"Successfully ran JMP on {os.path.basename(stacked_file)}")
                                        except Exception as file_e:
                                            self.log_message(f"Error running JMP on {os.path.basename(stacked_file)}: {file_e}", "error")
                            
                            self.log_message("JMP execution completed")
                        else:
                            self.log_message("JMP executable path not found - cannot run JMP", "warning")
                            self.log_message("Please ensure JMP Pro is installed and accessible", "warning")
                    except ImportError:
                        self.log_message("Warning: Required modules not found - cannot run JMP", "warning")
                    except Exception as e:
                        self.log_message(f"Error running JMP: {str(e)}", "error")
                        self.log_message(f"Error type: {type(e).__name__}", "error")
                elif self.run_jmp_var.get() and not stacked_files:
                    self.log_message("No stacked files available - cannot run JMP", "warning")
                
                # Clean up intermediary files if requested (from master.py)
                if self.delete_files_var.get():
                    self.log_message("Cleaning up intermediary files...")
                    for intermediary in intermediary_file_list:
                        try:
                            if os.path.exists(intermediary) and not ( 'decoded.csv' in intermediary or "datastack" in intermediary ):
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
        self.mtpl_file_path = tk.StringVar()
        self.last_mtpl_path = ""  # 🔄 ADD THIS LINE
        self.test_list = []
        
        # Clear CLKUtils data
        self.clkutils_tests = []
        self.all_clkutils_items = []
        self.clkutils_file_path = tk.StringVar()

        
        # Clear displays
        for item in self.material_tree.get_children():
            self.material_tree.delete(item)
        for item in self.mtpl_tree.get_children():
            self.mtpl_tree.delete(item)
        
        # Clear CLKUtils display
        if hasattr(self, 'clkutils_tree'):
            for item in self.clkutils_tree.get_children():
                self.clkutils_tree.delete(item)
            
        # Clear entry fields
        self.mtpl_file_path.set("")
        self.output_path_var.set("")
        self.search_var.set("")
        
        # Clear CLKUtils fields
        if hasattr(self, 'clkutils_search_var'):
            self.clkutils_search_var.set("")
        if hasattr(self, 'clkutils_text_input'):
            self.clkutils_text_input.delete('1.0', tk.END)
        
        # Reset progress
        self.progress_var.set(0)
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        self.log_message("Application reset - all data cleared")
        
    def normalize_unc_path(self, path):
        """
        Properly normalize Windows UNC paths to ensure only 2 backslashes at start,
        and strip any quotation marks from the path.
        
        Args:
            path: The file path to normalize
            
        Returns:
            str: Normalized path with proper UNC format and no quotation marks
        """
        if not path:
            return path
        
        print(f"Debug - normalize_unc_path input: '{path}'")
        
        # Strip quotation marks (single and double) from the beginning and end
        path = path.strip().strip('"\'')
        print(f"Debug - after stripping quotes: '{path}'")
        
        if path.startswith('\\\\'):
            # UNC path - strip all leading backslashes and add exactly 2
            stripped_path = path.lstrip('\\')
            print(f"Debug - stripped all backslashes: '{stripped_path}'")
            # Add exactly 2 backslashes to the front
            normalized_path = '\\\\' + stripped_path
            # Manual normalization to avoid os.path.normpath issues with UNC paths
            # Replace multiple consecutive backslashes with single ones (except the leading \\)
            normalized_path = '\\\\' + stripped_path.replace('\\\\', '\\')
            print(f"Debug - final normalized path: '{normalized_path}'")
            return normalized_path
        else:
            # Regular path - use standard normalization
            normalized = os.path.normpath(path)
            print(f"Debug - regular path normalized: '{normalized}'")
            return normalized
        
    def is_undefined(self, value):
        """Check if a value is considered undefined (from master.py)"""
        return value is None or value == '' or value == '-'
        
    def resolve_sio_config_path(self, config_expression, usrv_file_path, base_dir):
        """
        Parse the .usrv file and resolve the SIO configuration file path.
        
        Args:
            config_expression: String like 'GetEnvironmentVariable("~HDMT_TP_BASE_DIR") + SIO_PCIE.inputFilePath + UCC.DNELB'
            usrv_file_path: Path to the .usrv file
            base_dir: Base directory for the project
            
        Returns:
            Resolved absolute path to the configuration file
        """
        try:
            # Parse the .usrv file to extract variable definitions
            user_vars = self.parse_usrv_file(usrv_file_path)
            
            # Clean the config expression
            config_expr = config_expression.strip().strip('"\'')
            
            self.log_message(f"Resolving SIO config: {config_expr}")
            self.log_message(f"Base directory: {base_dir}")
            
            # Handle GetEnvironmentVariable("~HDMT_TP_BASE_DIR") - replace with base_dir
            if 'GetEnvironmentVariable("~HDMT_TP_BASE_DIR")' in config_expr:
                # Normalize the base_dir for UNC paths
                normalized_base_dir = self.normalize_unc_path(base_dir)
                config_expr = config_expr.replace('GetEnvironmentVariable("~HDMT_TP_BASE_DIR")', f'"{normalized_base_dir}"')
                self.log_message(f"After base_dir replacement: {config_expr}")
            
            # Split the expression by '+' and process each part
            parts = [part.strip() for part in config_expr.split('+')]
            resolved_parts = []
            
            self.log_message(f"Processing parts: {parts}")
            
            for part in parts:
                part = part.strip(' "\'')
                self.log_message(f"Processing part: '{part}'")
                
                if part.startswith('"') and part.endswith('"'):
                    # It's a literal string
                    literal_value = part.strip('"')
                    resolved_parts.append(literal_value)
                    self.log_message(f"  -> Literal string: '{literal_value}'")
                elif '.' in part and not part.startswith('\\\\'):
                    # It's a variable reference like SIO_PCIE.inputFilePath or UCC.DNELB
                    # But not a UNC path (which starts with \\)
                    namespace, var_name = part.split('.', 1)
                    if namespace in user_vars and var_name in user_vars[namespace]:
                        var_value = user_vars[namespace][var_name].strip(' "\'')
                        resolved_parts.append(var_value)
                        self.log_message(f"  -> Variable {namespace}.{var_name}: '{var_value}'")
                    else:
                        self.log_message(f"Warning: Variable {part} not found in .usrv file")
                        return None
                else:
                    # Direct reference or literal (including UNC paths that might have been substituted)
                    resolved_parts.append(part)
                    self.log_message(f"  -> Direct reference: '{part}'")
            
            # Join all parts to form the final path
            resolved_path = ''.join(resolved_parts)
            self.log_message(f"Joined path: '{resolved_path}'")
            
            # Normalize path separators and make it absolute
            resolved_path = resolved_path.replace('/', os.sep)
            
            if not os.path.isabs(resolved_path):
                resolved_path = os.path.join(base_dir, resolved_path)
            
            # Final normalization for UNC paths
            resolved_path = self.normalize_unc_path(resolved_path)
            
            self.log_message(f"SIO config resolution: {config_expression} -> {resolved_path}")
            
            return resolved_path
            
        except Exception as e:
            self.log_message(f"Error resolving SIO config path: {str(e)}")
            return None
    
    def parse_usrv_file(self, usrv_file_path):
        """
        Parse a .usrv file and extract user variable definitions.
        
        Args:
            usrv_file_path: Path to the .usrv file
            
        Returns:
            Dictionary with namespace -> {variable_name: value}
        """
        user_vars = {}
        current_namespace = None
        
        try:
            with open(usrv_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split into lines and process
            lines = content.split('\n')
            in_namespace = False
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('//') or line.startswith('#'):
                    continue
                
                # Check for namespace declaration like "UserVars SIO_PCIE"
                if line.startswith('UserVars ') and '{' in line:
                    namespace_line = line.replace('UserVars ', '').replace('{', '').strip()
                    current_namespace = namespace_line
                    user_vars[current_namespace] = {}
                    in_namespace = True
                    brace_count = 1
                    continue
                elif line.startswith('UserVars '):
                    namespace_line = line.replace('UserVars ', '').strip()
                    current_namespace = namespace_line
                    user_vars[current_namespace] = {}
                    in_namespace = False
                    continue
                
                # Handle opening braces
                if '{' in line and not in_namespace:
                    in_namespace = True
                    brace_count = line.count('{')
                    continue
                
                # Handle closing braces
                if '}' in line:
                    brace_count -= line.count('}')
                    if brace_count <= 0:
                        in_namespace = False
                        current_namespace = None
                    continue
                
                # Parse variable definitions inside namespace
                if in_namespace and current_namespace and '=' in line:
                    # Remove semicolon and split by =
                    line = line.rstrip(';')
                    
                    # Handle different variable declaration formats
                    if 'String ' in line:
                        var_part = line.replace('String ', '').strip()
                    elif 'Const String ' in line:
                        var_part = line.replace('Const String ', '').strip()
                    else:
                        var_part = line.strip()
                    
                    if '=' in var_part:
                        var_name, var_value = var_part.split('=', 1)
                        var_name = var_name.strip()
                        var_value = var_value.strip(' "\'')  # Remove quotes and spaces
                        user_vars[current_namespace][var_name] = var_value
            
            self.log_message(f"Parsed .usrv file: {len(user_vars)} namespaces found")
            for ns, vars_dict in user_vars.items():
                self.log_message(f"  Namespace {ns}: {len(vars_dict)} variables")
            
            return user_vars
            
        except Exception as e:
            self.log_message(f"Error parsing .usrv file {usrv_file_path}: {str(e)}")
            return {}
        
    def switch_to_light_mode(self, event=None):
        """Switch application to light mode with enhanced design consistency"""
        if not self.is_dark_mode:
            return  # Already in light mode
            
        self.is_dark_mode = False
        self.theme_label.configure(text="Light Mode")
        
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
        
        # Update mode toggle appearance if it exists
        if hasattr(self, 'update_mode_toggle_appearance'):
            self.update_mode_toggle_appearance()
        
        # Refresh material display if data exists
        if hasattr(self, 'material_df') and self.material_df is not None:
            self.update_material_display()
            
        self.log_message("☀️ Switched to Enhanced Light Mode with improved design consistency", "success")
        
    def switch_to_dark_mode(self, event=None):
        """Switch application to dark mode with purple/navy theme and proper contrast"""
        if self.is_dark_mode:
            return  # Already in dark mode
            
        self.is_dark_mode = True
        self.theme_label.configure(text="Dark Mode")
        
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
        
        # Update mode toggle appearance if it exists
        if hasattr(self, 'update_mode_toggle_appearance'):
            self.update_mode_toggle_appearance()
        
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
                
                if hasattr(self, 'clkutils_tree') and self.clkutils_tree.winfo_exists():
                    self.clkutils_tree.tag_configure('oddrow', background='#2d2d48', foreground='#e8e9f0')
                    self.clkutils_tree.tag_configure('evenrow', background='#353553', foreground='#e8e9f0')
                    self.clkutils_tree.tag_configure('checked', background='#4a6fa5', foreground='white')
                    self.clkutils_tree.tag_configure('unchecked', background='#2d2d48', foreground='#e8e9f0')
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
                
                if hasattr(self, 'clkutils_tree') and self.clkutils_tree.winfo_exists():
                    self.clkutils_tree.tag_configure('oddrow', background='#ffffff', foreground='#24292e')
                    self.clkutils_tree.tag_configure('evenrow', background='#f6f8fa', foreground='#24292e')
                    self.clkutils_tree.tag_configure('checked', background='#e6f3ff', foreground='#24292e')
                    self.clkutils_tree.tag_configure('unchecked', background='#ffffff', foreground='#24292e')
                    
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
    if CTK_AVAILABLE:
        # Use CustomTkinter for modern appearance
        root = ctk.CTk()
        # Configure window appearance
        root.configure(fg_color=("#f0f0f0", "#212121"))  # Light/Dark mode colors
    else:
        # Fallback to regular Tkinter
        root = tk.Tk()
    
    app = CTVListGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
