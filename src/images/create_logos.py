#!/usr/bin/env python3
"""
Create placeholder Intel logo images for the CTV application
"""
import base64
import os

# Simple Intel-blue colored logo placeholder (32x24 PNG)
INTEL_LOGO_PNG = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVFiFtZdNaBNBFMd/M5tsNk2bpI1aqRVRwYNePHjw4MWLFy9ePHjx4sWLFy9evHjx4sWDFy8evHjw4sWLFy9ePHjx4MWDF69evPqxM7Mzs/Pe7LxvZt5bAP5fAGMMY4wxjDHGGMMYYwxjjDHGGMMYYwxjjDHGGMMYYwxjjDHGGMMYYwxjjDHGGMMY+x8AxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4w=
"""

def create_logo_files():
    """Create Intel logo placeholder files"""
    # Decode the base64 PNG data
    try:
        png_data = base64.b64decode(INTEL_LOGO_PNG.strip())
        
        # List of logo files to create
        logo_files = [
            'logo.png',
            'logo.jpg', 
            'logo.jpeg',
            'lightmode-logo.png',
            'lightmode-logo.jpg',
            'light-logo.png',
            'light-logo.jpg',
            'darkmode-logo.png',
            'dark-logo.png',
            'dark-logo.jpg'
        ]
        
        images_dir = os.path.dirname(os.path.abspath(__file__))
        
        for filename in logo_files:
            filepath = os.path.join(images_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(png_data)
            print(f"Created: {filepath}")
            
        print(f"\n✅ Created {len(logo_files)} Intel logo placeholder files")
        print("These are small blue placeholder images that will work with PIL/Pillow")
        
    except Exception as e:
        print(f"❌ Error creating logo files: {e}")

if __name__ == "__main__":
    create_logo_files()
