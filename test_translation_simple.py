import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("Step 1: Importing modules...")
    from core.config import Config
    from models.translation_model import TranslationModel
    print("  OK")
    
    print("\nStep 2: Creating model instance...")
    config = Config()
    model = TranslationModel(config)
    print(f"  OK - Device: {model.device}")
    
    print("\nStep 3: Loading model...")
    model.load_model()
    print("  OK")
    
    print("\nStep 4: Translating...")
    result = model.translate("Hello world")
    print(f"  Result: {result}")
    
    print("\nALL TESTS PASSED!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
