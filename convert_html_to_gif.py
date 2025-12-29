"""
Convert HTML Animation to GIF
Uses Playwright to render and capture the animation from python-widget-example.py
"""

import asyncio
from pathlib import Path
import sys

# Read the HTML from python-widget-example.py
def extract_html_from_py():
    """Extract HTML content from python-widget-example.py"""
    py_file = Path("public/python-widget-example.py")
    
    if not py_file.exists():
        print(f"Error: {py_file} not found")
        return None
    
    content = py_file.read_text(encoding='utf-8')
    
    # Extract HTML between triple quotes in _get_embedded_html
    start_marker = "return '''"
    end_marker = "'''"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Error: Could not find HTML start marker")
        return None
    
    start_idx += len(start_marker)
    end_idx = content.find(end_marker, start_idx)
    
    if end_idx == -1:
        print("Error: Could not find HTML end marker")
        return None
    
    html = content[start_idx:end_idx].strip()
    return html

async def record_animation_to_gif():
    """Record HTML animation and convert to GIF"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Error: Playwright not installed")
        print("Install with: pip install playwright")
        print("Then run: playwright install chromium")
        return False
    
    # Extract HTML
    html = extract_html_from_py()
    if not html:
        return False
    
    # Create temp HTML file
    temp_html = Path("temp_animation.html")
    temp_html.write_text(html, encoding='utf-8')
    
    print("Starting browser recording...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 600, 'height': 300},
            record_video_dir=".",
            record_video_size={'width': 600, 'height': 300}
        )
        page = await context.new_page()
        
        # Load HTML
        await page.goto(f"file://{temp_html.absolute()}")
        
        # Wait for animation to loop (4 seconds per cycle, record 2 cycles)
        print("Recording 8 seconds of animation...")
        await asyncio.sleep(8)
        
        # Close
        await context.close()
        await browser.close()
        
        # Get video file
        video_path = None
        for f in Path(".").glob("*.webm"):
            video_path = f
            break
        
        if not video_path:
            print("Error: Video not recorded")
            return False
        
        print(f"Video recorded: {video_path}")
        
        # Convert to GIF using ffmpeg
        output_gif = "src/resources/animations/processing.gif"
        Path(output_gif).parent.mkdir(parents=True, exist_ok=True)
        
        import subprocess
        
        # High quality GIF conversion
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", "fps=15,scale=400:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            output_gif
        ]
        
        print("Converting to GIF...")
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"Success! GIF created: {output_gif}")
            # Cleanup
            video_path.unlink()
            temp_html.unlink()
            return True
        else:
            print(f"Error converting to GIF: {result.stderr.decode()}")
            return False
    
    return False

if __name__ == "__main__":
    success = asyncio.run(record_animation_to_gif())
    sys.exit(0 if success else 1)
