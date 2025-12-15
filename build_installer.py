"""
Build script for Canto-beats Installer (Windows)
Creates a portable installation package.

Usage:
    python build_installer.py

This script:
1. Builds a minimal launcher.exe
2. Exports the current Python environment
3. Packages everything for distribution
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    """Main build function."""
    print("=" * 60)
    print("Canto-beats Installer Build Script")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist" / "Canto-beats"
    
    # Clean previous build
    if dist_dir.exists():
        print("\nCleaning previous build...")
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Build launcher.exe
    print("\n[1/4] Building launcher.exe...")
    launcher_script = project_dir / "installer" / "launcher.py"
    
    if launcher_script.exists():
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            str(launcher_script),
            "--onefile",
            "--windowed",
            "--name=Canto-beats",
            f"--distpath={dist_dir}",
            "--workpath=build/launcher",
            "--specpath=build",
            "--clean",
            "--noconfirm",
        ], check=True)
        print("   ✓ Launcher built successfully")
    else:
        print("   ✗ launcher.py not found, skipping...")
    
    # Step 2: Copy application files
    print("\n[2/4] Copying application files...")
    app_dir = dist_dir / "app"
    app_dir.mkdir(exist_ok=True)
    
    # Copy main.py
    shutil.copy(project_dir / "main.py", app_dir / "main.py")
    
    # Copy src directory
    src_dest = app_dir / "src"
    if (project_dir / "src").exists():
        shutil.copytree(project_dir / "src", src_dest)
    
    # Copy public directory
    public_dest = app_dir / "public"
    if (project_dir / "public").exists():
        shutil.copytree(project_dir / "public", public_dest)
    
    print("   ✓ Application files copied")
    
    # Step 3: Export Python environment info
    print("\n[3/4] Exporting environment info...")
    requirements_file = dist_dir / "requirements.txt"
    subprocess.run([
        sys.executable, "-m", "pip", "freeze"
    ], stdout=open(requirements_file, "w"), check=True)
    print("   ✓ Requirements exported")
    
    # Step 4: Create installation instructions
    print("\n[4/4] Creating installation instructions...")
    install_readme = dist_dir / "INSTALL.txt"
    install_readme.write_text("""
Canto-beats Installation Instructions
=====================================

For Users:
----------
1. Install Python 3.11 from https://www.python.org/
2. Open Command Prompt in this folder
3. Run: pip install -r requirements.txt
4. Run: python app/main.py

Or wait for the full installer version with embedded Python.

For Developers:
---------------
This is a portable distribution of Canto-beats.
You can run it directly with your existing Python environment.
""", encoding="utf-8")
    print("   ✓ Installation instructions created")
    
    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"\nOutput: {dist_dir}")
    print("\nContents:")
    for item in dist_dir.iterdir():
        if item.is_dir():
            count = sum(1 for _ in item.rglob("*"))
            print(f"  📁 {item.name}/ ({count} files)")
        else:
            size = item.stat().st_size / 1024
            print(f"  📄 {item.name} ({size:.1f} KB)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
