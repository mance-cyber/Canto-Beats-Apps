"""
Test script to verify MPV loading works correctly.
This simulates what happens on a fresh Windows installation.
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("MPV Installation Test")
print("=" * 60)

# Test 1: Check if VC++ Runtime DLLs are present
print("\n[1] Checking VC++ Runtime DLLs...")
vc_dlls = [
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140.dll"
]
system32 = Path("C:/Windows/System32")
for dll in vc_dlls:
    dll_path = system32 / dll
    status = "[OK]" if dll_path.exists() else "[FAIL]"
    print(f"    {status} {dll}: {'Found' if dll_path.exists() else 'NOT FOUND'}")

# Test 2: Check if D3DCompiler is present in standalone dir
print("\n[2] Checking D3DCompiler...")
standalone_dir = Path(__file__).parent / "dist" / "Canto-beats-Standalone"
d3d_standalone = standalone_dir / "d3dcompiler_47.dll"
print(f"    In standalone dir: {'[OK] Found' if d3d_standalone.exists() else '[FAIL] NOT FOUND'}")

# Test 3: Check libmpv-2.dll
print("\n[3] Checking libmpv-2.dll...")
libmpv_path = standalone_dir / "libmpv-2.dll"
print(f"    Path: {libmpv_path}")
print(f"    Exists: {'[OK]' if libmpv_path.exists() else '[FAIL]'}")
if libmpv_path.exists():
    size_mb = libmpv_path.stat().st_size / (1024 * 1024)
    print(f"    Size: {size_mb:.1f} MB")

# Test 4: Check installer redist files
print("\n[4] Checking installer redist files...")
redist_dir = Path(__file__).parent / "installer" / "redist"
for item in ["vc_redist.x64.exe", "d3dcompiler_47.dll"]:
    item_path = redist_dir / item
    status = "[OK]" if item_path.exists() else "[FAIL]"
    if item_path.exists():
        size_mb = item_path.stat().st_size / (1024 * 1024)
        print(f"    {status} {item}: {size_mb:.1f} MB")
    else:
        print(f"    {status} {item}: NOT FOUND")

# Test 5: Try to load MPV
print("\n[5] Testing MPV loading...")
# Add the standalone dir to PATH
if str(standalone_dir) not in os.environ["PATH"]:
    os.environ["PATH"] = str(standalone_dir) + os.pathsep + os.environ["PATH"]
    print(f"    Added to PATH: {standalone_dir}")

try:
    import mpv
    print("    [OK] mpv module imported successfully!")
    
    # Try to create an instance (without video output)
    player = mpv.MPV(vo='null', ao='null')
    print("    [OK] MPV instance created successfully!")
    player.terminate()
    print("    [OK] MPV instance terminated")
    
except ImportError as e:
    print(f"    [FAIL] ImportError: {e}")
except OSError as e:
    print(f"    [FAIL] OSError (DLL loading failed): {e}")
except Exception as e:
    print(f"    [FAIL] Unexpected error: {type(e).__name__}: {e}")

# Test 6: Check final installer
print("\n[6] Checking final installer...")
installer_path = Path(__file__).parent / "dist" / "Canto-beats-Full-Setup.exe"
if installer_path.exists():
    size_mb = installer_path.stat().st_size / (1024 * 1024)
    print(f"    [OK] Installer found: {size_mb:.1f} MB")
else:
    print(f"    [FAIL] Installer NOT FOUND at {installer_path}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

