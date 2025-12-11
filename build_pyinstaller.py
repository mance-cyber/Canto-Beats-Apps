"""
PyInstaller Build Script for Canto-beats (Windows)
Creates a standalone executable using PyInstaller.

Usage:
    python build_pyinstaller.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Main build function."""
    
    print("=" * 60)
    print("Canto-beats PyInstaller Build Script (Windows)")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    main_script = str(project_dir / "main.py")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        main_script,
        
        # === Output Configuration ===
        "--onefile",
        "--windowed",
        "--name=Canto-beats",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        
        # === Add Data Files (Windows uses ;) ===
        "--add-data=src;src",
        "--add-data=public;public",
        
        # === Hidden Imports ===
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=torch",
        "--hidden-import=faster_whisper",
        "--hidden-import=transformers",
        "--hidden-import=cryptography",
        "--hidden-import=sentencepiece",
        "--hidden-import=accelerate",
        
        # === Optimization ===
        "--clean",
        "--noconfirm",
        
        # Exclude unnecessary modules
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
    ]
    
    print("\nBuild command:")
    print(" ".join(cmd))
    print("\n" + "-" * 60)
    print("Starting PyInstaller build (10-20 minutes)...")
    print("-" * 60 + "\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("Output: dist/Canto-beats.exe")
        print("=" * 60)
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\nBUILD FAILED with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
