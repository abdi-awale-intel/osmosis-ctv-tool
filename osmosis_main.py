#!/usr/bin/env python3
"""
Osmosis - Data Processing Application
Main entry point for the standalone application
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(app_dir))

# Import and run the GUI
try:
    # Check if running as a bundled executable
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        os.chdir(bundle_dir)
        sys.path.insert(0, str(bundle_dir))
    else:
        # Running as a script
        os.chdir(app_dir)
        sys.path.insert(0, str(app_dir))
    
    # Import the main GUI module
    import ctvlist_gui
    
    # Create and run the GUI
    import tkinter as tk
    
    if __name__ == "__main__":
        root = tk.Tk()
        # Update title to reflect Osmosis branding
        root.title("Osmosis - Data Processing Application")
        app = ctvlist_gui.CTVListGUI(root)
        root.mainloop()
        
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    messagebox.showerror("Import Error", 
                        f"Failed to import required modules:\n{str(e)}\n\n"
                        "Please ensure all dependencies are installed.\n\n"
                        f"Python path: {sys.path}\n"
                        f"Working directory: {os.getcwd()}")
    sys.exit(1)
    
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    messagebox.showerror("Application Error", 
                        f"An error occurred while starting Osmosis:\n{str(e)}\n\n"
                        f"Working directory: {os.getcwd()}")
    sys.exit(1)
