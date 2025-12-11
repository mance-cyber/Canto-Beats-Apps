"""
PyInstaller Build Script for Canto-beats (Windows)
Creates a standalone executable using PyInstaller.

Usage:
    python build_pyinstaller.py
"""

import PyInstaller.__main__
import sys
from pathlib import Path


def main():
    """Main build function."""
    
    print("=" * 60)
    print("Canto-beats PyInstaller Build Script (Windows)")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    main_script = str(project_dir / "main.py")
    icon_path = str(project_dir / "public" / "app icon_002.png")
    
    # PyInstaller arguments
    args = [
        main_script,
        
        # === Output Configuration ===
        "--onefile",                          # Single executable
        "--windowed",                         # GUI app, no console
        "--name=Canto-beats",
        f"--icon={icon_path}",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        
        # === Add Data Files ===
        "--add-data=src;src",
        "--add-data=public;public",
        
        # === Hidden Imports (explicit) ===
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=torch",
        "--hidden-import=faster_whisper",
        "--hidden-import=transformers",
        "--hidden-import=cryptography",
        
        # === Windows Version Info ===
        "--version-file=version_info.txt" if (project_dir / "version_info.txt").exists() else "",
        
        # === Optimization ===
        "--clean",                            # Clean cache before building
        "--noconfirm",                        # Replace output without asking
        
        # Exclude unnecessary modules
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=PIL.ImageTk",
    ]
    
    # Remove empty strings
    args = [arg for arg in args if arg]
    
    print("\nStarting PyInstaller build...")
    print("This should take 10-20 minutes.\n")
    print("-" * 60)
    
    try:
        PyInstaller.__main__.run(args)
        
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"Output: dist/Canto-beats.exe")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
