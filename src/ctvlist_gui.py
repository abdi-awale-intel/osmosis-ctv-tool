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
        self.root.title("CTV List Data Processor")
        
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
        
        # Initialize theme components as None for fallback handling
        self.light_logo = None
        self.dark_logo = None
        self.light_mode_btn = None
        self.dark_mode_btn = None
        self.theme_label = None
        
        # Setup window management first
        self.setup_window_management()
        
        self.create_widgets()
        
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
                    title_label = create_label(logo_frame, text="CTV List Data Processor")
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
        
        # Tab 3: Output Settings and Processing
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
        
        title_label = create_label(title_frame, text="CTV List Data Processor")
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
        
        # MTPL file loading
        mtpl_load_frame = ttk.LabelFrame(scrollable_frame, text="Load MTPL File")
        mtpl_load_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(mtpl_load_frame, text="MTPL File Path:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        ttk.Entry(mtpl_load_frame, textvariable=self.mtpl_file_path, width=60).grid(row=0, column=1, padx=10, pady=5)
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
        
        # MTPL data display with proper layout management
        mtpl_display_frame = ttk.LabelFrame(scrollable_frame, text="MTPL Data")
        mtpl_display_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Configure grid weights for proper resizing
        mtpl_display_frame.grid_rowconfigure(1, weight=1)  # Make treeview area expandable
        mtpl_display_frame.grid_columnconfigure(0, weight=1)
        
        # Enhanced Search and Filter Controls
        filter_control_frame = ttk.LabelFrame(mtpl_display_frame, text="🔍 Search & Filter Controls")
        filter_control_frame.pack(fill='x', padx=10, pady=(10, 5))
        
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
        
        # Collapsible Column filters frame
        self.column_filters_frame = ttk.LabelFrame(mtpl_display_frame, text="📋 Advanced Column Filters")
        self.column_filters_visible = False  # Start collapsed
        
        # Initialize column filter variables
        self.column_filters = {}
        self.column_filter_combos = {}
        
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
        
        # Add mouse wheel support for the treeview
        def _on_treeview_mousewheel(event):
            self.mtpl_tree.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.mtpl_tree.bind("<MouseWheel>", _on_treeview_mousewheel)
        
        # Bind click events for test selection
        self.mtpl_tree.bind('<Double-1>', self.toggle_test_selection)
        self.mtpl_tree.bind('<Button-1>', self.on_treeview_click)
        
        # Enhanced Test Selection and Management
        test_management_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Test Selection & Management")
        test_management_frame.pack(fill='x', padx=20, pady=10)
        
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
        
        # Always stack output files for JMP; option removed
        
        self.run_jmp_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Run JMP on stacked files", variable=self.run_jmp_var).pack(anchor='w', padx=10, pady=5)
        
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
            
            # Process the file
            self.mtpl_csv_path = mt.mtpl_to_csv(fi.process_file_input(self.last_mtpl_path))
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
            
        filtered_items = []
        
        # Get current filter values
        text_filter = self.search_var.get().lower().strip()
        
        for item_data in self.all_mtpl_items:
            values = item_data['values']
            # Skip checkbox column for filtering
            row_values = values[1:]  
            
            # Apply text filter
            text_match = True
            if text_filter:
                item_text = ' '.join(str(val).lower() for val in row_values)
                text_match = text_filter in item_text
            
            # Apply column filters
            column_match = True
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
        self.last_mtpl_path = ""  # Clear the last MTPL path
        # Disable reload button
        if hasattr(self, 'reload_mtpl_button'):
            self.reload_mtpl_button.configure(state='disabled')
                
        # Clear column filters
        for col, filter_var in self.column_filters.items():
            filter_var.set("All")
            
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
        self.selected_tests_label.configure(text=str(count))
        
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
            self.active_filters_label.configure(text="Active filters: 0", foreground='gray')
        else:
            self.filter_status_label.configure(text="Filters applied", foreground='green')
            self.active_filters_label.configure(text=f"Active filters: {active_count}", foreground='blue')
    
    def select_all_visible_tests(self):
        """Select all currently visible tests"""
        # Get current filtered items and mark them as selected
        search_text = self.search_var.get().lower()
        
        # Apply current filters to get visible items
        filtered_items = self.all_mtpl_items.copy()
        
        # Apply search filter
        if search_text:
            filtered_items = [
                item for item in filtered_items
                if search_text in ' '.join(str(val).lower() for val in item['values'][1:])
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
        self.update_selected_tests_count()
    
    def invert_selection(self):
        """Invert the current selection"""
        # Get current filtered items
        search_text = self.search_var.get().lower()
        
        # Apply current filters to get visible items
        filtered_items = self.all_mtpl_items.copy()
        
        # Apply search filter
        if search_text:
            filtered_items = [
                item for item in filtered_items
                if search_text in ' '.join(str(val).lower() for val in item['values'][1:])
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
        self.update_selected_tests_count()
    
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
                    print('TEST:',test)
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
                            indexed_file,csv_identifier,tag_header_names = ind.index_CTV(test_file, test,module_name,place_in)
                            tag_header_names_chunks.append(tag_header_names)
                            intermediary_file_list.append(indexed_file)
                            self.log_message(f"Performing data request for test: {test}")
                            # Set need_suffix to False for regular CTV processing
                            need_suffix = False
                            datainput_file,datacombine_file = py.uber_request(indexed_file,test,test_type,need_suffix,place_in,program, csv_identifier,lot_list,wafer_list,prefetch,databases)
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
