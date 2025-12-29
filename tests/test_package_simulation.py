"""
COMPREHENSIVE PACKAGE SIMULATION TEST
=====================================
This script simulates what happens in the packaged app by:
1. Testing all import chains
2. Checking for missing packages
3. Detecting metadata issues (like torchcodec)
4. Simulating main.py startup sequence
"""
import sys
import os
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add src to path (like main.py does)
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("=" * 70)
print("COMPREHENSIVE PACKAGE SIMULATION TEST")
print("=" * 70)

errors = []
warnings_list = []
success_count = 0

def log_success(msg):
    global success_count
    success_count += 1
    print(f"  [OK] {msg}")

def log_error(msg, exception=None):
    full_msg = f"{msg}: {exception}" if exception else msg
    errors.append(full_msg)
    print(f"  [FAIL] {full_msg}")

def log_warning(msg):
    warnings_list.append(msg)
    print(f"  [WARN] {msg}")

# ========================================
# TEST 1: Check for problematic top-level imports
# ========================================
print("\n[TEST 1] Checking for problematic top-level imports...")

# These patterns cause issues in PyInstaller - only check for actual imports
problematic_patterns = [
    ('models/__init__.py', 'from .translation_model import TranslationModel', 'Should use lazy import'),
    ('subtitle/style_processor.py', 'from models.translation_model import TranslationModel', 'Should use lazy import (at top level)'),
]

for file_path, pattern, reason in problematic_patterns:
    full_path = os.path.join(src_dir, file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Only check imports at top of file (first 30 lines, outside functions)
            lines = content.split('\n')[:30]
            # Filter out comment lines and docstrings
            import_lines = [l for l in lines if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('"') and not l.strip().startswith("'")]
            top_content = '\n'.join(import_lines)
            if pattern in top_content:
                log_error(f"{file_path} has problematic import: '{pattern}' - {reason}")
            else:
                log_success(f"{file_path} - No problematic import at top level")
    else:
        log_warning(f"{file_path} not found")

# ========================================
# TEST 2: Core module imports
# ========================================
print("\n[TEST 2] Testing core module imports...")

core_modules = [
    ('core.config', 'Configuration'),
    ('core.path_setup', 'Path setup'),
    ('utils.logger', 'Logger'),
]

for module, desc in core_modules:
    try:
        __import__(module)
        log_success(f"{module} ({desc})")
    except Exception as e:
        log_error(f"{module} ({desc})", e)

# ========================================
# TEST 3: UI module imports (critical chain)
# ========================================
print("\n[TEST 3] Testing UI module imports...")

# Test splash screen first (should be lightweight)
try:
    from ui.splash_screen import SplashScreen
    log_success("ui.splash_screen (SplashScreen)")
except Exception as e:
    log_error("ui.splash_screen", e)

# Test style processor (was causing issues)
try:
    from subtitle.style_processor import StyleProcessor
    # Verify TranslationModel is NOT in namespace
    import subtitle.style_processor as sp
    if hasattr(sp, 'TranslationModel'):
        log_error("style_processor has TranslationModel in namespace (should be lazy)")
    else:
        log_success("subtitle.style_processor (lazy import verified)")
except Exception as e:
    log_error("subtitle.style_processor", e)

# ========================================
# TEST 4: Check models package
# ========================================
print("\n[TEST 4] Testing models package...")

try:
    import models
    # Check what's exported
    exported = [name for name in dir(models) if not name.startswith('_')]
    log_success(f"models package loads (exports: {exported})")
    
    # Verify TranslationModel NOT exported
    if 'TranslationModel' in exported:
        log_error("models exports TranslationModel (should be lazy)")
except Exception as e:
    log_error("models package", e)

# ========================================
# TEST 5: Check for metadata issues
# ========================================
print("\n[TEST 5] Checking for package metadata issues...")

metadata_packages = [
    'torch',
    'transformers',
    'PySide6',
    'faster_whisper',
]

import importlib.metadata as metadata

for pkg in metadata_packages:
    try:
        version = metadata.version(pkg)
        log_success(f"{pkg} metadata found (version: {version})")
    except metadata.PackageNotFoundError:
        log_warning(f"{pkg} metadata not found (may cause issues in PyInstaller)")

# Check specifically for torchcodec (the problematic one)
try:
    version = metadata.version('torchcodec')
    log_success(f"torchcodec metadata found (version: {version})")
except metadata.PackageNotFoundError:
    log_warning("torchcodec metadata not found - but this is OK if we use lazy imports!")

# ========================================
# TEST 6: Simulate main.py startup sequence
# ========================================
print("\n[TEST 6] Simulating main.py startup sequence...")

try:
    # Step 1: Path setup
    from core.path_setup import setup_all_paths
    setup_all_paths()
    log_success("Path setup completed")
except Exception as e:
    log_error("Path setup", e)

try:
    # Step 2: Config
    from core.config import Config
    config = Config()
    log_success("Config loaded")
except Exception as e:
    log_error("Config loading", e)

try:
    # Step 3: Import main_window (this is the big one)
    print("\n  [CRITICAL] Testing main_window import...")
    from ui.main_window import MainWindow
    log_success("main_window imported successfully!")
except Exception as e:
    log_error("main_window import", e)

# ========================================
# RESULTS SUMMARY
# ========================================
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)

print(f"\nSuccesses: {success_count}")
print(f"Warnings: {len(warnings_list)}")
print(f"Errors: {len(errors)}")

if warnings_list:
    print("\n--- Warnings ---")
    for w in warnings_list:
        print(f"  - {w}")

if errors:
    print("\n--- ERRORS (will cause failures in packaged app) ---")
    for e in errors:
        print(f"  - {e}")
    print("\n[!] FIX THESE ERRORS before building the installer!")
else:
    print("\n[SUCCESS] All tests passed! The packaged app should start correctly.")
