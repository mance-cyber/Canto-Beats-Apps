"""
Simple script to create a processing.gif animation using PIL
Creates a smooth wave/pulse effect for the progress dialog
"""

from PIL import Image, ImageDraw
import math

def create_processing_gif():
    """Create a simple animated GIF for processing indicator"""
    
    # Settings
    width, height = 100, 60
    frames = 20
    duration = 80  # ms per frame
    
    images = []
    
    for frame in range(frames):
        # Create image with transparent background
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw 5 bars with wave animation
        bar_width = 8
        spacing = 6
        total_width = 5 * bar_width + 4 * spacing
        start_x = (width - total_width) // 2
        
        for i in range(5):
            # Calculate bar height with sine wave
            phase = (frame / frames) * 2 * math.pi
            offset = i * 0.8
            height_factor = 0.3 + 0.5 * abs(math.sin(phase + offset))
            bar_height = int(height * height_factor)
            
            # Position
            x = start_x + i * (bar_width + spacing)
            y = (height - bar_height) // 2
            
            # Color gradient from cyan to blue
            color_factor = i / 4
            r = int(6 + (59 - 6) * color_factor)
            g = int(182 + (130 - 182) * color_factor)
            b = int(212 + (246 - 212) * color_factor)
            
            # Draw rounded rectangle
            draw.rounded_rectangle(
                [(x, y), (x + bar_width, y + bar_height)],
                radius=4,
                fill=(r, g, b, 255)
            )
        
        images.append(img)
    
    # Save as GIF
    output_path = 'src/resources/animations/processing.gif'
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True
    )
    
    print(f"✅ Created processing.gif at {output_path}")
    print(f"   Frames: {frames}, Duration: {duration}ms, Size: {width}x{height}")

if __name__ == "__main__":
    try:
        create_processing_gif()
    except ImportError:
        print("❌ PIL/Pillow not installed. Install with: pip install Pillow")
    except Exception as e:
        print(f"❌ Error creating GIF: {e}")
