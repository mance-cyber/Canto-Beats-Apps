"""
Simple Build Script for Canto-beats Distribution
Creates a portable package without compiling an exe.

Usage:
    python build_simple.py
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess


def main():
    """Main build function."""
    print("=" * 60)
    print("Canto-beats Simple Distribution Builder")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist" / "Canto-beats-Portable"
    
    # Clean previous build
    if dist_dir.exists():
        print("\nCleaning previous build...")
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Copy application files
    print("\n[1/4] Copying application files...")
    app_dir = dist_dir / "app"
    app_dir.mkdir(exist_ok=True)
    
    # Copy main.py
    shutil.copy(project_dir / "main.py", app_dir / "main.py")
    print("   ✓ main.py copied")
    
    # Copy src directory
    if (project_dir / "src").exists():
        shutil.copytree(project_dir / "src", app_dir / "src")
        print("   ✓ src/ copied")
    
    # Copy public directory
    if (project_dir / "public").exists():
        shutil.copytree(project_dir / "public", app_dir / "public")
        print("   ✓ public/ copied")
    
    # Step 2: Copy launcher script
    print("\n[2/4] Creating launcher...")
    launcher_bat = project_dir / "installer" / "Canto-beats.bat"
    if launcher_bat.exists():
        shutil.copy(launcher_bat, dist_dir / "Canto-beats.bat")
        print("   ✓ Launcher created")
    else:
        # Create inline
        (dist_dir / "Canto-beats.bat").write_text("""@echo off
cd /d "%~dp0"
start "" pythonw "app\\main.py"
""", encoding="utf-8")
        print("   ✓ Launcher created (inline)")
    
    # Step 3: Export requirements
    print("\n[3/4] Exporting requirements...")
    requirements_file = dist_dir / "requirements.txt"
    with open(requirements_file, "w") as f:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f)
    print("   ✓ Requirements exported")
    
    # Step 4: Create installation script
    print("\n[4/4] Creating install script...")
    install_script = dist_dir / "install.bat"
    install_script.write_text("""@echo off
title Canto-beats Installer
echo ============================================================
echo Canto-beats Dependency Installer
echo ============================================================
echo.
echo This will install all required Python packages.
echo Make sure you have Python 3.11 installed.
echo.
pause

pip install -r requirements.txt

echo.
echo ============================================================
echo Installation complete!
echo You can now run Canto-beats.bat to start the application.
echo ============================================================
pause
""", encoding="utf-8")
    print("   ✓ Install script created")
    
    # Create README
    readme = dist_dir / "README.txt"
    readme.write_text("""
Canto-beats Portable Distribution
==================================

Quick Start:
1. Make sure Python 3.11+ is installed
2. Run install.bat to install dependencies (first time only)
3. Run Canto-beats.bat to start the application

Requirements:
- Python 3.11 or higher
- Windows 10/11 (64-bit)

For support, please visit our GitHub repository.
""", encoding="utf-8")
    
    # Summary
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"\nOutput: {dist_dir}")
    
    # Count files
    total_files = sum(1 for _ in dist_dir.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
    
    print(f"\nTotal files: {total_files}")
    print(f"Total size: {total_size / 1024 / 1024:.1f} MB")
    
    print("\nContents:")
    for item in sorted(dist_dir.iterdir()):
        if item.is_dir():
            count = sum(1 for _ in item.rglob("*") if _.is_file())
            print(f"  📁 {item.name}/ ({count} files)")
        else:
            size = item.stat().st_size / 1024
            print(f"  📄 {item.name} ({size:.1f} KB)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
