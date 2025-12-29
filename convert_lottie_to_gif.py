"""
Convert Lottie JSON to GIF using lottie library.

Usage: python convert_lottie_to_gif.py
"""

try:
    from lottie import objects
    from lottie.parsers.tgs import parse_tgs
    from lottie.exporters.gif import export_gif
    from pathlib import Path
    
    # Paths
    lottie_file = Path(__file__).parent / "public" / "Dnlooping.json"
    output_file = Path(__file__).parent / "public" / "loading.gif"
    
    if not lottie_file.exists():
        print(f"Error: {lottie_file} not found!")
        exit(1)
    
    # Load Lottie
    print(f"Loading {lottie_file}...")
    with open(lottie_file, 'r') as f:
        animation = parse_tgs(f.read())
    
    # Export to GIF (120x120, 30fps)
    print(f"Converting to GIF (120x120)...")
    export_gif(animation, str(output_file), size=(120, 120), fps=30)
    
    print(f"✓ GIF created: {output_file}")
    
except ImportError as e:
    print(f"Error: {e}")
    print("Install with: pip install lottie[all]")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)
