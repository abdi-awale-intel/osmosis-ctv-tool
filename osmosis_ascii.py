#!/usr/bin/env python3
"""
Proper OSMOSIS ASCII Art Generator
Creates ASCII art that actually spells OSMOSIS
"""

def create_osmosis_ascii():
    """Create proper OSMOSIS ASCII art"""
    
    styles = {
        "block": [
            "",
            "==================================================",
            "",
            "  ███████  ███████ ███    ███  ███████ ███████ ███████ ███████",
            " ██     ██ ██      ████  ████ ██    ██ ██      ██      ██     ",
            " ██     ██ ███████ ██ ████ ██ ██    ██ ███████ ███████ ███████",
            " ██     ██      ██ ██  ██  ██ ██    ██      ██      ██      ██",
            "  ███████  ███████ ██      ██  ███████ ███████ ███████ ███████",
            "",
            "              INTEL CTV ANALYSIS TOOL v2.0",
            "",
            "=================================================="
        ],
        
        "simple": [
            "",
            "================================================",
            "",
            "  ######   #####  #     #  ######   #####  ##### #####",
            " #      # #       ##   ## #      # #       #     #    ",
            " #      #  #####  # ### # #      #  #####   ###   ### ",
            " #      #       # #  #  # #      #       #     #     #",
            "  ######   #####  #     #  ######   #####  #####  ### ",
            "",
            "            OSMOSIS v2.0 INSTALLER",
            "          Advanced CTV Tool Suite",
            "        Intel Database Analysis Tool",
            "",
            "================================================"
        ],
        
        "clean": [
            "",
            "================================================",
            "",
            " ####   ####  #   #  ####   ####  ####  ####",
            "#    # #      ## ##  #    # #      #    #    ",
            "#    #  ###   # # #  #    #  ###   ###   ### ",
            "#    #     #  #   #  #    #     #     #     #",
            " ####  ####   #   #   ####  ####  ####  #### ",
            "",
            "         OSMOSIS v2.0 INSTALLER",
            "       Advanced CTV Tool Suite",
            "     Intel Database Analysis Tool",
            "",
            "================================================"
        ],
        
        "text": [
            "",
            "=" * 50,
            "",
            "   ___  _____ __  __  ___  _____ _____ _____",
            "  / _ \\/ ___/|  \\/  |/ _ \\/ __/ / __/ / ___/",
            " / // /\\__ \\ | |\\/| / // /\\__ \\ \\__ \\ \\__ \\ ",
            "/____/____/  |_|  |_\\___/____/ ____/ ____/ ",
            "",
            "        OSMOSIS v2.0 INSTALLER",
            "      Advanced CTV Tool Suite",
            "",
            "=" * 50
        ]
    }
    
    return styles

def create_proper_osmosis():
    """Create the most readable OSMOSIS ASCII"""
    return [
        "",
        "================================================",
        "",
        "  ####   ####  #   #  ####   ####  ####  ####",
        " #    # #      ## ##  #    # #      #    #    ",
        " #    #  ###   # # #  #    #  ###   ###   ### ",
        " #    #     #  #   #  #    #     #     #     #",
        "  ####  ####   #   #   ####  ####  ####  #### ",
        "",
        "         OSMOSIS v2.0 INSTALLER",
        "       Advanced CTV Tool Suite",
        "     Intel Database Analysis Tool",
        "",
        "================================================"
    ]

def generate_batch_commands(style="clean"):
    """Generate batch file echo commands"""
    styles = create_osmosis_ascii()
    if style == "proper":
        lines = create_proper_osmosis()
    else:
        lines = styles.get(style, styles["clean"])
    
    batch_commands = []
    for line in lines:
        if line.strip():
            batch_commands.append(f'echo {line}')
        else:
            batch_commands.append('echo.')
    
    return "\n".join(batch_commands)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        style = sys.argv[1]
        print(generate_batch_commands(style))
    else:
        print("Available styles: clean, simple, block, text, proper")
        print("\nUsage: python osmosis_ascii.py [style]")
        print("\nExample output (proper style):")
        print(generate_batch_commands("proper"))
