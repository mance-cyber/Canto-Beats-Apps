"""
Import Chain Test - Simulates what happens at application startup.
This helps catch import issues before deployment.
"""
import sys
import os

# Add src to path (like main.py does)
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print("=" * 60)
print("IMPORT CHAIN TEST - Simulating Application Startup")
print("=" * 60)

# Track what gets imported
import_errors = []
import_success = []

def test_import(module_path, description):
    """Test importing a module and track result."""
    global import_errors, import_success
    try:
        print(f"\n[TEST] Importing: {module_path}")
        __import__(module_path)
        print(f"  [OK] {description}")
        import_success.append(module_path)
        return True
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        print(f"  [FAIL] {description}")
        print(f"  ERROR: {error_msg}")
        import_errors.append((module_path, error_msg))
        return False

# ========================================
# Stage 1: Core imports (should be safe)
# ========================================
print("\n--- Stage 1: Core Imports ---")
test_import("core.config", "Config module")
test_import("core.path_setup", "Path setup module")
test_import("utils.logger", "Logger module")

# ========================================
# Stage 2: UI imports (main_window dependencies)
# ========================================
print("\n--- Stage 2: UI Imports ---")
test_import("ui.splash_screen", "Splash screen")

# This is the critical one - main_window imports many things
print("\n[CRITICAL] Testing main_window import chain...")

# Test the specific import that was causing issues
print("\n  Testing: subtitle.style_processor (should NOT import TranslationModel at top level)")
try:
    # Import style_processor - this should NOT trigger transformers loading
    from subtitle import style_processor
    
    # Check if TranslationModel was imported at module level
    if 'TranslationModel' in dir(style_processor):
        print("  [WARN] TranslationModel is in style_processor namespace!")
    else:
        print("  [OK] TranslationModel is NOT in style_processor namespace (lazy import works!)")
    
    import_success.append("subtitle.style_processor")
except Exception as e:
    import_errors.append(("subtitle.style_processor", f"{type(e).__name__}: {e}"))
    print(f"  [FAIL] {type(e).__name__}: {e}")

# ========================================
# Stage 3: Models imports (heavy packages)
# ========================================
print("\n--- Stage 3: Models Imports (should be lazy) ---")

# Check models/__init__.py does NOT import TranslationModel
print("\n[CHECKING] models/__init__.py should NOT import TranslationModel...")
try:
    import models
    if hasattr(models, 'TranslationModel'):
        print("  [FAIL] TranslationModel is exported from models.__init__.py!")
        import_errors.append(("models", "TranslationModel should not be in __init__.py"))
    else:
        print("  [OK] TranslationModel is NOT exported from models (lazy import works!)")
        import_success.append("models (lazy import)")
except Exception as e:
    import_errors.append(("models", f"{type(e).__name__}: {e}"))
    print(f"  [FAIL] {type(e).__name__}: {e}")

# ========================================
# Results Summary
# ========================================
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print(f"\n[OK] Successful imports: {len(import_success)}")
for m in import_success:
    print(f"  - {m}")

if import_errors:
    print(f"\n[FAIL] Failed imports: {len(import_errors)}")
    for m, err in import_errors:
        print(f"  - {m}: {err}")
    print("\n[!] These errors would cause startup failures in the packaged app!")
else:
    print("\n[SUCCESS] All imports passed! The app should start successfully.")
