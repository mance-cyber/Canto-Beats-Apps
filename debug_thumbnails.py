
import ffmpeg
import os
import sys

# Hardcoded path from user logs - hope it's accessible
VIDEO_PATH = "E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/RTC/RTC_v12/RTC_v12_001.mp4"
OUTPUT_DIR = "debug_thumbs"

if not os.path.exists(VIDEO_PATH):
    print(f"Video file not found at: {VIDEO_PATH}")
    # Try to find a local mp4
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".mp4"):
                VIDEO_PATH = os.path.join(root, file)
                print(f"Using local video: {VIDEO_PATH}")
                break
        if os.path.exists(VIDEO_PATH): break

if not os.path.exists(VIDEO_PATH):
    print("No video file found to test.")
    sys.exit(1)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_thumb(name, filters, output_kwargs):
    output_path = os.path.join(OUTPUT_DIR, f"{name}.jpg")
    print(f"Generating {name}...")
    try:
        stream = ffmpeg.input(VIDEO_PATH, ss=10) # Capture at 10s
        
        for f_name, f_args in filters:
            if isinstance(f_args, list):
                stream = stream.filter(f_name, *f_args)
            elif isinstance(f_args, dict):
                stream = stream.filter(f_name, **f_args)
            else:
                stream = stream.filter(f_name, f_args)
        
        stream = stream.output(output_path, vframes=1, **output_kwargs)
        stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
        print(f"  ✅ Saved to {output_path}")
    except ffmpeg.Error as e:
        print(f"  ❌ Failed: {e.stderr.decode() if e.stderr else str(e)}")

# 1. Current CPU implementation (yuv420p)
generate_thumb(
    "1_current_cpu",
    [
        ('scale', [320, 180]), # Assuming max_width/height
        ('format', 'yuv420p')
    ],
    {'format': 'image2', 'vcodec': 'mjpeg', 'qscale': 2}
)

# 2. Force even dimensions (scale=-2)
generate_thumb(
    "2_even_dimensions",
    [
        ('scale', ['-2', 180]), # -2 ensures even width
        ('format', 'yuv420p')
    ],
    {'format': 'image2', 'vcodec': 'mjpeg', 'qscale': 2}
)

# 3. Use yuvj420p (Full range)
generate_thumb(
    "3_yuvj420p",
    [
        ('scale', [320, 180]),
        ('format', 'yuvj420p')
    ],
    {'format': 'image2', 'vcodec': 'mjpeg', 'qscale': 2}
)

# 4. No format filter (Let ffmpeg decide)
generate_thumb(
    "4_no_format_filter",
    [
        ('scale', [320, 180])
    ],
    {'format': 'image2', 'vcodec': 'mjpeg', 'qscale': 2}
)

# 5. PNG (Lossless check)
generate_thumb(
    "5_png_reference",
    [
        ('scale', [320, 180])
    ],
    {'format': 'image2', 'vcodec': 'png'} # Save as .jpg but it will be png content if we don't change ext, wait ffmpeg might complain.
)
# Fix extension for PNG
try:
    ffmpeg.input(VIDEO_PATH, ss=10).filter('scale', 320, 180).output(os.path.join(OUTPUT_DIR, "5_reference.png"), vframes=1).run(quiet=True, overwrite_output=True)
    print("  ✅ Saved reference PNG")
except:
    pass

print("\nDone. Please check the 'debug_thumbs' folder.")
