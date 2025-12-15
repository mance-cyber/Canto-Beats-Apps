"""
Test script to verify libmpv-2.dll loading in the installed environment.
This simulates running from C:\Program Files\Canto-beats\
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("MPV Loading Test - Simulating Installed Environment")
print("=" * 60)

# Get the standalone directory (simulates install directory)
standalone_dir = Path(__file__).parent / "dist" / "Canto-beats-Standalone"
app_dir = standalone_dir / "app"
src_dir = app_dir / "src"

print(f"\n[1] Checking directory structure...")
print(f"    Standalone dir: {standalone_dir}")
print(f"    - exists: {standalone_dir.exists()}")

print(f"\n[2] Checking libmpv-2.dll...")
libmpv_path = standalone_dir / "libmpv-2.dll"
print(f"    Path: {libmpv_path}")
print(f"    - exists: {libmpv_path.exists()}")
if libmpv_path.exists():
    print(f"    - size: {libmpv_path.stat().st_size / 1024 / 1024:.2f} MB")

print(f"\n[3] Checking video_player.py path calculation...")
video_player_py = src_dir / "ui" / "video_player.py"
print(f"    video_player.py: {video_player_py}")
print(f"    - exists: {video_player_py.exists()}")

if video_player_py.exists():
    # Simulate the path calculation from video_player.py
    # __file__ = src/ui/video_player.py
    simulated_file = video_player_py
    
    # Calculate paths as video_player.py would
    install_dir = simulated_file.parent.parent.parent.parent  # ui -> src -> app -> install
    project_root = simulated_file.parent.parent.parent  # ui -> src -> app (wrong for installed)
    
    print(f"\n[4] Path calculations from video_player.py:")
    print(f"    install_dir (parent x4): {install_dir}")
    print(f"    - libmpv exists here: {(install_dir / 'libmpv-2.dll').exists()}")
    
    print(f"    project_root (parent x3): {project_root}")
    print(f"    - libmpv exists here: {(project_root / 'libmpv-2.dll').exists()}")

print(f"\n[5] Testing actual MPV loading...")

# Add the standalone dir to PATH (simulating the fix)
os.environ["PATH"] = str(standalone_dir) + os.pathsep + os.environ["PATH"]
print(f"    Added to PATH: {standalone_dir}")

# Also add the app dir sources to Python path
sys.path.insert(0, str(src_dir))

try:
    import mpv
    print(f"    ✓ MPV loaded successfully!")
    print(f"    MPV version info available: {hasattr(mpv, 'MPV')}")
except ImportError as e:
    print(f"    ✗ ImportError: {e}")
except OSError as e:
    print(f"    ✗ OSError (DLL not found): {e}")
except Exception as e:
    print(f"    ✗ Unexpected error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
