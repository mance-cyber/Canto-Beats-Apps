"""
Nuitka Build Script for Canto-beats (macOS)
Compiles Python to native code for macOS.

Usage:
    python build_nuitka_macos.py
"""

import subprocess
import sys
import os
from pathlib import Path


def get_nuitka_command():
    """Generate Nuitka compilation command for macOS."""
    
    project_dir = Path(__file__).parent
    main_script = project_dir / "main.py"
    output_dir = project_dir / "dist"
    
    cmd = [
        sys.executable, "-m", "nuitka",
        
        # === Output Configuration ===
        "--standalone",
        "--macos-create-app-bundle",  # Create .app bundle
        f"--output-dir={output_dir}",
        "--macos-app-name=Canto-beats",
        
        # === App Icon (macOS uses .icns) ===
        # Note: Nuitka can convert PNG to ICNS with imageio
        f"--macos-app-icon={project_dir / 'public' / 'app icon_002.png'}",
        
        # === Optimization ===
        # "--lto=yes",  # Removed: Too slow
        "--jobs=4",
        
        # === macOS Specific ===
        "--macos-app-version=1.0.0",
        "--macos-signed-app-name=com.cantobeats.app",
        
        # === Data includes ===
        "--include-data-dir=src=src",
        "--include-data-dir=public=public",
        
        # === PySide6 Plugin ===
        "--enable-plugin=pyside6",
        
        # === Include packages ===
        "--include-package=torch",
        "--include-package=faster_whisper",
        "--include-package=PySide6",
        "--include-package=requests",
        "--include-package=cryptography",
        
        # === Follow imports ===
        "--follow-imports",
        
        # Main script
        str(main_script),
    ]
    
    return cmd


def main():
    """Main build function."""
    
    print("=" * 60)
    print("Canto-beats macOS Build Script")
    print("=" * 60)
    
    # Check if Nuitka is installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True, text=True
        )
        print(f"Nuitka version: {result.stdout.strip()}")
    except Exception as e:
        print("ERROR: Nuitka not installed!")
        print("Install with: pip install nuitka")
        return 1
    
    cmd = get_nuitka_command()
    
    print("\nBuild command:")
    print(" ".join(cmd))
    print()
    
    print("Starting compilation (this may take 10-30 minutes)...")
    print("-" * 60)
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end="")
        
        process.wait()
        
        if process.returncode == 0:
            print("\n" + "=" * 60)
            print("BUILD SUCCESSFUL!")
            print(f"Output: dist/Canto-beats.app")
            print("=" * 60)
        else:
            print(f"\nBUILD FAILED with code {process.returncode}")
            return process.returncode
            
    except KeyboardInterrupt:
        print("\nBuild cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nBuild error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
