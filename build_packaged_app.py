#!/usr/bin/env python3
"""
Canto-Beats macOS Packaging Script
==================================
This script automates the entire packaging workflow for macOS.

Usage:
    python build_packaged_app.py [--sign "Developer ID Application: ..."]

Steps:
1. Checks environment (FFmpeg, Icons, Dependencies)
2. Cleans previous builds
3. Runs PyInstaller
4. Fixes dynamic library paths (if needed)
5. Signs the application (if identity provided)
6. Verifies the bundle
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
import time

# Configuration
PROJECT_ROOT = Path(__file__).parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
APP_NAME = "Canto-beats.app"
APP_PATH = DIST_DIR / APP_NAME
SPEC_FILE = PROJECT_ROOT / "canto-beats.spec"
ENTITLEMENTS_FILE = PROJECT_ROOT / "entitlements.plist"

def log(msg, level="INFO"):
    print(f"[{level}] {msg}")

def check_environment():
    """Verify all necessary tools and files exist."""
    log("Checking environment...")
    
    # 1. Check FFmpeg
    if not (PROJECT_ROOT / "ffmpeg").exists() and not shutil.which("ffmpeg"):
        log("FFmpeg not found! Please install via 'brew install ffmpeg' or place binary in root.", "ERROR")
        return False
        
    # 2. Check Icons
    icon_path = PROJECT_ROOT / "public/icons/app_icon.icns"
    if not icon_path.exists():
        log(f"Icon not found at {icon_path}", "WARNING")
        
    # 3. Check Entitlements
    if not ENTITLEMENTS_FILE.exists():
        log(f"Entitlements file missing at {ENTITLEMENTS_FILE}", "ERROR")
        return False
        
    return True

def clean_build_dirs():
    """Remove build and dist directories."""
    log("Cleaning build directories...")
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            log(f"Removed {d}")

def run_pyinstaller():
    """Execute PyInstaller build."""
    log("Running PyInstaller...")
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]
    
    try:
        subprocess.check_call(cmd)
        log("PyInstaller build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        log(f"PyInstaller failed with exit code {e.returncode}", "ERROR")
        return False

def sign_application(identity):
    """Sign the application bundle with a Developer ID."""
    if not identity:
        log("No code signing identity provided. Skipping signing.", "WARNING")
        return

    log(f"Signing application with identity: '{identity}'")
    
    # 1. Sign internal frameworks and dylibs first (inside-out)
    frameworks_dir = APP_PATH / "Contents/Frameworks"
    if frameworks_dir.exists():
        for item in frameworks_dir.glob("**/*"):
            if item.suffix in ['.dylib', '.so', '.framework']:
                try:
                    subprocess.run([
                        "codesign", "--force", "--verify", "--verbose",
                        "--sign", identity,
                        "--options", "runtime",
                        "--timestamp",
                        "--entitlements", str(ENTITLEMENTS_FILE),
                        str(item)
                    ], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    log(f"Failed to sign inner item: {item.name}", "WARNING")

    # 2. Sign the main bundle
    try:
        subprocess.check_call([
            "codesign", "--force", "--verify", "--verbose",
            "--sign", identity,
            "--options", "runtime",
            "--timestamp",
            "--entitlements", str(ENTITLEMENTS_FILE),
            "--deep", # Resign everything inside just in case
            str(APP_PATH)
        ])
        log("Application signed successfully.")
    except subprocess.CalledProcessError as e:
        log("Failed to sign application bundle!", "ERROR")
        sys.exit(1)

def verify_bundle():
    """Sanity check the generated bundle."""
    log("Verifying .app bundle...")
    
    if not APP_PATH.exists():
        log("App bundle not found!", "ERROR")
        return False
        
    # Check for executable
    exe = APP_PATH / "Contents/MacOS/Canto-beats"
    if not exe.exists():
        log("Executable missing!", "ERROR")
        return False
        
    # Check for resources
    res_src = APP_PATH / "Contents/Resources/src"
    if not res_src.exists():
        log("Resources/src missing! Path handling might fail.", "ERROR")
        return False
        
    log(f"Verification passed: {APP_PATH}")
    log(f"Size: {sum(f.stat().st_size for f in APP_PATH.glob('**/*') if f.is_file()) / (1024*1024):.2f} MB")
    return True

def main():
    parser = argparse.ArgumentParser(description="Build Canto-Beats macOS App")
    parser.add_argument("--sign", help="Developer ID Application certificate name")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build dirs and exit")
    args = parser.parse_args()
    
    if args.clean_only:
        clean_build_dirs()
        return

    start_time = time.time()
    
    if not check_environment():
        sys.exit(1)
        
    clean_build_dirs()
    
    if not run_pyinstaller():
        sys.exit(1)
        
    if args.sign:
        sign_application(args.sign)
    else:
        log("Skipping code signing (pass --sign to enable).", "WARNING")
        log("NOTE: Unsigned apps will require 'Right Click > Open' on other Macs.", "INFO")
        
    if not verify_bundle():
        log("Build verification failed!", "ERROR")
        sys.exit(1)
        
    duration = time.time() - start_time
    log(f"Build process completed in {duration:.1f} seconds.", "SUCCESS")
    log(f"Output: {APP_PATH}")

if __name__ == "__main__":
    main()
