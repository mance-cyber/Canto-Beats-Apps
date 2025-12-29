"""
Deep diagnosis script for MPV DLL loading issues.
This script attempts to identify ALL missing dependencies.
"""

import os
import sys
import ctypes
from pathlib import Path

print("=" * 70)
print("MPV Deep Diagnosis")
print("=" * 70)

# Determine the installation directory structure
print("\n[1] Environment Analysis")
print("-" * 50)
print(f"Python executable: {sys.executable}")
print(f"Script location: {__file__}")
print(f"Current working directory: {os.getcwd()}")
print(f"sys.frozen: {getattr(sys, 'frozen', False)}")

# Calculate all possible libmpv locations
print("\n[2] Searching for libmpv-2.dll")
print("-" * 50)

script_path = Path(__file__)
possible_locations = []

# From video_player.py logic:
# Case 1: install_dir = parent.parent.parent.parent from video_player.py
# But from THIS script location, we need different logic

# If this script is in the project root
project_root = script_path.parent
possible_locations.append(("Project root", project_root))

# If this is in dist/Canto-beats-Standalone/app/
if "dist" in str(script_path):
    install_dir = script_path.parent.parent  # app -> install dir
    possible_locations.append(("Install dir (from dist)", install_dir))

# Check standalone dist
standalone_dir = project_root / "dist" / "Canto-beats-Standalone"
possible_locations.append(("Standalone dist", standalone_dir))

# Check cwd
possible_locations.append(("CWD", Path.cwd()))

print("Checking locations:")
libmpv_found = None
for name, loc in possible_locations:
    dll_path = loc / "libmpv-2.dll"
    exists = dll_path.exists()
    print(f"  {name}:")
    print(f"    Path: {loc}")
    print(f"    libmpv-2.dll: {'[FOUND]' if exists else '[NOT FOUND]'}")
    if exists:
        size_mb = dll_path.stat().st_size / (1024**2)
        print(f"    Size: {size_mb:.1f} MB")
        libmpv_found = dll_path

# Test 3: Try to load the DLL directly with ctypes
print("\n[3] Direct DLL Loading Test")
print("-" * 50)

if libmpv_found:
    # Add the directory to PATH
    dll_dir = str(libmpv_found.parent)
    if dll_dir not in os.environ["PATH"]:
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ["PATH"]
        print(f"Added to PATH: {dll_dir}")
    
    # Also try os.add_dll_directory (Python 3.8+)
    try:
        os.add_dll_directory(dll_dir)
        print(f"Added DLL directory: {dll_dir}")
    except Exception as e:
        print(f"os.add_dll_directory failed: {e}")
    
    # Try loading with ctypes
    print(f"\nAttempting to load: {libmpv_found}")
    try:
        lib = ctypes.CDLL(str(libmpv_found))
        print("[SUCCESS] libmpv-2.dll loaded successfully with ctypes!")
    except OSError as e:
        print(f"[FAILED] OSError: {e}")
        print("\nThis usually means a DEPENDENCY of libmpv-2.dll is missing.")
        print("The error message above should indicate which DLL is missing.")
else:
    print("[SKIP] libmpv-2.dll not found, cannot test loading")

# Test 4: Try importing mpv module
print("\n[4] Python MPV Module Test")
print("-" * 50)

try:
    import mpv
    print("[SUCCESS] mpv module imported!")
    
    # Try creating player with null output
    try:
        player = mpv.MPV(vo='null', ao='null')
        print("[SUCCESS] MPV instance created!")
        player.terminate()
        print("[SUCCESS] MPV instance terminated!")
    except Exception as e:
        print(f"[FAILED] MPV instantiation: {type(e).__name__}: {e}")
        
except ImportError as e:
    print(f"[FAILED] ImportError: {e}")
except OSError as e:
    print(f"[FAILED] OSError: {e}")
except Exception as e:
    print(f"[FAILED] {type(e).__name__}: {e}")

# Test 5: Check PATH environment
print("\n[5] PATH Analysis (first 5 entries)")
print("-" * 50)
path_entries = os.environ["PATH"].split(os.pathsep)[:5]
for i, p in enumerate(path_entries):
    print(f"  {i+1}. {p}")

print("\n" + "=" * 70)
print("Diagnosis Complete")
print("=" * 70)
