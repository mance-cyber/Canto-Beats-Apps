"""
Nuitka Build Script for Canto-beats
Compiles Python to native C code for protection against reverse engineering.

Usage:
    python build_nuitka.py          # Full build
    python build_nuitka.py --help   # Show help
    python build_nuitka.py --dry-run  # Show command without executing
"""

import subprocess
import sys
import os
from pathlib import Path


def get_nuitka_command():
    """Generate Nuitka compilation command with optimal settings."""
    
    project_dir = Path(__file__).parent
    main_script = project_dir / "main.py"
    output_dir = project_dir / "dist"
    
    # Nuitka compilation arguments
    cmd = [
        sys.executable, "-m", "nuitka",
        
        # === Output Configuration ===
        "--standalone",                    # Create standalone executable
        "--onefile",                       # Package into single file
        f"--output-dir={output_dir}",
        "--output-filename=Canto-beats.exe",
        
        # === Optimization ===
        "--lto=yes",                       # Link-time optimization
        "--jobs=4",                        # Parallel compilation
        
        # === Windows Specific ===
        "--windows-console-mode=disable", # GUI application, no console
        f"--windows-icon-from-ico={project_dir / 'public' / 'app icon_002.png'}",
        "--windows-company-name=Canto-beats",
        "--windows-product-name=Canto-beats",
        "--windows-file-version=1.0.0.0",
        "--windows-product-version=1.0.0.0",
        "--windows-file-description=粵語字幕神器",
        
        # === Code Protection ===
        "--include-data-dir=src=src",
        "--include-data-dir=public=public",
        "--include-data-dir=models=models",
        
        # === PySide6 Plugin ===
        "--enable-plugin=pyside6",
        
        # === Include necessary packages ===
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
    print("Canto-beats Nuitka Build Script")
    print("=" * 60)
    
    # Check for dry-run mode
    dry_run = "--dry-run" in sys.argv
    show_help = "--help" in sys.argv or "-h" in sys.argv
    
    if show_help:
        print(__doc__)
        print("\nOptions:")
        print("  --dry-run    Show the Nuitka command without executing")
        print("  --help, -h   Show this help message")
        return 0
    
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
    
    if dry_run:
        print("[DRY RUN] Command not executed.")
        return 0
    
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
            print(f"Output: dist/Canto-beats.exe")
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
