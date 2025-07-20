#!/usr/bin/env python3
"""
Test script to verify that the image paths are working correctly
"""
import os
import sys

def test_image_paths():
    """Test that all required image files exist with correct relative paths"""
    print("Testing image file paths...")
    
    # Get the script directory
    script_dir = os.path.dirname(__file__)
    images_dir = os.path.join(script_dir, "images")
    
    # List of required images
    required_images = [
        "logo.jpeg",
        "lightmode-logo.jpg", 
        "darkmode-logo.png"
    ]
    
    success = True
    
    for image_name in required_images:
        image_path = os.path.join(images_dir, image_name)
        if os.path.exists(image_path):
            print(f"✅ {image_name} found at: {image_path}")
        else:
            print(f"❌ {image_name} NOT FOUND at: {image_path}")
            success = False
    
    return success

def test_image_loading():
    """Test that images can be loaded with PIL"""
    try:
        from PIL import Image
        print("\n✅ PIL/Pillow is available")
        
        script_dir = os.path.dirname(__file__)
        images_dir = os.path.join(script_dir, "images")
        
        # Test loading each image
        images = [
            ("logo.jpeg", "Application icon"),
            ("lightmode-logo.jpg", "Light mode theme"),
            ("darkmode-logo.png", "Dark mode theme")
        ]
        
        for img_file, description in images:
            img_path = os.path.join(images_dir, img_file)
            try:
                img = Image.open(img_path)
                print(f"✅ {description} loaded successfully - Size: {img.size}")
            except Exception as e:
                print(f"❌ Failed to load {description}: {e}")
                return False
        
        return True
        
    except ImportError:
        print("❌ PIL/Pillow not available")
        return False

if __name__ == "__main__":
    print("Image Path Validation Test")
    print("=" * 50)
    
    path_success = test_image_paths()
    loading_success = test_image_loading()
    
    print("\n" + "=" * 50)
    if path_success and loading_success:
        print("✅ All tests passed! Images should work correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if path_success and loading_success else 1)
