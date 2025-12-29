"""
Convert PNG to ICO for Windows application icon.
"""

from PIL import Image
from pathlib import Path

def main():
    project_dir = Path(__file__).parent
    png_path = project_dir / "public" / "app icon_002.png"
    ico_path = project_dir / "public" / "app_icon.ico"
    
    print(f"Converting {png_path} to {ico_path}...")
    
    # Open PNG image
    img = Image.open(png_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create multiple sizes for ICO (Windows needs various sizes)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # Save as ICO with multiple sizes
    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s, _ in sizes],
        append_images=icons[1:]
    )
    
    print(f"✓ Created {ico_path}")
    print(f"  Sizes included: {sizes}")

if __name__ == "__main__":
    main()
