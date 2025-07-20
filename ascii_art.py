#!/usr/bin/env python3
"""
ASCII Art Generator for Osmosis Installer
Creates clean, terminal-compatible ASCII art
"""

def generate_osmosis_banner():
    """Generate simple, clean ASCII banner"""
    
    banners = {
        "simple": [
            "",
            "================================================",
            "",
            "   ####    ####  ####  ####    ####   ####  ####",
            "  ##  ##  ##    ##  ## ##  ##  ##  ## ##    ##", 
            "  ##  ##  ##     ####  ##  ##  ##  ##  ###   ###",
            "  ##  ##   ###   ##    ####    ##  ##    ##    ##",
            "   ####     ###  ##    ##       ####  ####  ####",
            "",
            "",
            "          OSMOSIS v2.0 INSTALLER",
            "        Advanced CTV Tool Suite", 
            "      Intel Database Analysis Tool",
            "",
            "================================================"
        ],
        
        "block": [
            "",
            "████████████████████████████████████████████████",
            "",
            " ██████  ███████ ███    ███  ██████  ███████ ██████",
            "██    ██ ██      ████  ████ ██    ██ ██      ██   ██",
            "██    ██ ███████ ██ ████ ██ ██    ██ ███████ ██ ██",
            "██    ██      ██ ██  ██  ██ ██    ██      ██ ██████",
            " ██████  ███████ ██      ██  ██████  ███████ ██",
            "",
            "      Intel Osmosis v2.0 - CTV Analysis Tool",
            "",
            "████████████████████████████████████████████████"
        ],
        
        "text": [
            "",
            "=" * 50,
            "",
            "   ___  ____  __  __  ___  ____  ____  ____",
            "  / _ \\/ __/ |  \\/  |/ _ \\/ __/  __/ __/",
            " / ___/\\__\\  | |\\/| | ___/\\__\\  \\__\\",
            " \\___/|___/  |_|  |_|\\___/ |___/ |___/",
            "",
            "        OSMOSIS v2.0 INSTALLER",
            "      Advanced CTV Tool Suite",
            "",
            "=" * 50
        ]
    }
    
    return banners

def test_banners():
    """Test different banner styles"""
    banners = generate_osmosis_banner()
    
    for style, banner in banners.items():
        print(f"\n{style.upper()} STYLE:")
        print("-" * 40)
        for line in banner:
            print(line)
        print("-" * 40)
        input("Press Enter for next style...")

def create_installer_header(style="simple"):
    """Create installer header for batch file"""
    banners = generate_osmosis_banner()
    banner = banners.get(style, banners["simple"])
    
    batch_lines = []
    for line in banner:
        if line:
            batch_lines.append(f'echo {line}')
        else:
            batch_lines.append('echo.')
    
    return "\n".join(batch_lines)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_banners()
        elif sys.argv[1] == "batch":
            style = sys.argv[2] if len(sys.argv) > 2 else "simple"
            print(create_installer_header(style))
    else:
        print("ASCII Art Generator for Osmosis")
        print("Commands:")
        print("  python ascii_art.py test          # Test all styles")
        print("  python ascii_art.py batch simple  # Generate batch file header")
