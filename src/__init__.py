"""
Osmosis CTV Tool - Source Package
Advanced CTV data processing and analysis tool with complete PyUber database integration
"""

__version__ = "2.0.0"
__author__ = "Intel Corporation"
__email__ = "abdi.awale@intel.com"
__description__ = "Advanced CTV data processing and analysis tool"

# Import main modules for easier access
try:
    from .osmosis_main import main as osmosis_main
    from .ctvlist_gui import main as gui_main
    from .deploy_ctvlist import main as deploy_main
except ImportError:
    # Handle imports when not in package mode
    pass

__all__ = [
    "osmosis_main",
    "gui_main", 
    "deploy_main",
]
