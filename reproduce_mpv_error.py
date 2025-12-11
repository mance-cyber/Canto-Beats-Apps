import os
import sys
from pathlib import Path
import time

# Add project root to PATH to find libmpv-2.dll if needed
project_root = Path(__file__).parent
dll_path = str(project_root)
if dll_path not in os.environ["PATH"]:
    os.environ["PATH"] = dll_path + os.pathsep + os.environ["PATH"]

try:
    import mpv
    print("MPV imported successfully")
except ImportError:
    print("Failed to import mpv")
    sys.exit(1)
except OSError as e:
    print(f"Failed to load libmpv: {e}")
    sys.exit(1)

def test_subtitle_loading():
    try:
        # Initialize MPV
        player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True)
        player.keep_open = True
        
        # Load dummy video
        print("Loading dummy video...")
        player.play('av://lavfi:color=c=black:s=1280x720:d=10')
        time.sleep(2) # Wait for load
        
        # Create dummy subtitle file
        sub_path = Path("test_sub.srt").absolute()
        with open(sub_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:05,000\nHello World\n")
            
        print(f"Created dummy subtitle at {sub_path}")
        
        # Test sub_remove
        print("Testing sub_remove()...")
        try:
            player.sub_remove()
            print("sub_remove() success")
        except Exception as e:
            print(f"sub_remove() failed: {e}")
            
        # Test sub_add
        print("Testing sub_add()...")
        try:
            player.sub_add(str(sub_path))
            print("sub_add() success")
        except Exception as e:
            print(f"sub_add() failed: {e}")
            
        player.terminate()
        
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    test_subtitle_loading()
