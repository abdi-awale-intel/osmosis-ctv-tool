#!/usr/bin/env python3
"""
Create placeholder Intel logo images for the CTV application
"""
import os

def create_logo_files():
    """Create Intel logo placeholder files"""
    try:
        # Try using PIL to create proper images
        from PIL import Image, ImageDraw
        
        # Create a simple Intel-blue logo (48x32 pixels)
        logo_files = [
            ('logo.png', 'PNG'),
            ('logo.jpg', 'JPEG'), 
            ('logo.jpeg', 'JPEG'),
            ('lightmode-logo.png', 'PNG'),
            ('lightmode-logo.jpg', 'JPEG'),
            ('light-logo.png', 'PNG'),
            ('light-logo.jpg', 'JPEG'),
            ('darkmode-logo.png', 'PNG'),
            ('dark-logo.png', 'PNG'),
            ('dark-logo.jpg', 'JPEG')
        ]
        
        images_dir = os.path.dirname(os.path.abspath(__file__))
        
        for filename, format_type in logo_files:
            filepath = os.path.join(images_dir, filename)
            
            # Create a simple Intel-blue rectangle with "INTEL" text
            if format_type == 'JPEG':
                # Create RGB image for JPEG
                img = Image.new('RGB', (48, 32), color=(0, 113, 197))  # Intel blue
                draw = ImageDraw.Draw(img)
                draw.text((8, 12), "INTEL", fill='white')
            else:
                # Create RGBA image for PNG
                img = Image.new('RGBA', (48, 32), color=(0, 113, 197, 255))  # Intel blue
                draw = ImageDraw.Draw(img)
                draw.text((8, 12), "INTEL", fill='white')
            
            img.save(filepath, format_type, quality=95 if format_type == 'JPEG' else None)
            print(f"Created: {filepath}")
            
        print(f"\n[SUCCESS] Created {len(logo_files)} Intel logo files using PIL")
        
    except ImportError:
        print("[INFO] PIL not available, creating minimal logo files...")
        create_minimal_logos()
        
    except Exception as e:
        print(f"[WARNING] PIL failed ({e}), creating minimal logo files...")
        create_minimal_logos()

def create_minimal_logos():
    """Create minimal PNG files without PIL"""
    # Minimal 1x1 PNG file data (transparent pixel)
    minimal_png = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 size
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # RGBA, CRC
        0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,  # compressed data
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,  # CRC
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
        0x42, 0x60, 0x82
    ])
    
    logo_files = [
        'logo.png', 'logo.jpg', 'logo.jpeg',
        'lightmode-logo.png', 'lightmode-logo.jpg',
        'light-logo.png', 'light-logo.jpg',
        'darkmode-logo.png', 'dark-logo.png', 'dark-logo.jpg'
    ]
    
    images_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename in logo_files:
        filepath = os.path.join(images_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(minimal_png)
        print(f"Created: {filepath}")
        
    print(f"\n[SUCCESS] Created {len(logo_files)} minimal logo files")

if __name__ == "__main__":
    create_logo_files()
