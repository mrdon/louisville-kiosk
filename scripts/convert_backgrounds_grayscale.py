#!/usr/bin/env python3
"""
Convert all background images to grayscale
"""
from PIL import Image
import os
from pathlib import Path

def convert_to_grayscale(image_path):
    """Convert an image to grayscale and save it"""
    try:
        # Open the image
        img = Image.open(image_path)

        # Convert to grayscale
        grayscale_img = img.convert('L')

        # Convert back to RGB mode so it's still a "color" image (but gray)
        # This preserves compatibility with systems expecting RGB
        rgb_grayscale = grayscale_img.convert('RGB')

        # Save back to the same file
        rgb_grayscale.save(image_path, quality=95)

        print(f"✓ Converted: {image_path.name}")

    except Exception as e:
        print(f"✗ Error converting {image_path.name}: {e}")

def main():
    # Get the backgrounds directory (parent of scripts dir)
    backgrounds_dir = Path(__file__).parent.parent / "images" / "backgrounds"

    if not backgrounds_dir.exists():
        print(f"Error: Directory not found: {backgrounds_dir}")
        return

    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    image_files = [
        f for f in backgrounds_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if not image_files:
        print("No image files found in backgrounds directory")
        return

    print(f"Found {len(image_files)} images to convert...")
    print()

    # Convert each image
    for image_file in sorted(image_files):
        convert_to_grayscale(image_file)

    print()
    print("Done!")

if __name__ == "__main__":
    main()
