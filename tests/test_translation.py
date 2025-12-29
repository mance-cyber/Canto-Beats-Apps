"""
Test AI Translation functionality after torch upgrade
"""

import sys
sys.path.insert(0, 'src')

from core.config import Config
from models.translation_model import TranslationModel

def test_translation():
    print("=" * 60)
    print("Testing AI Translation Model")
    print("=" * 60)
    
    # Test cases
    test_texts = [
        "day one",
        "set up",
        "That's why",
        "campaign",
        "branding",
        "I love this product",
        "Let's start the meeting"
    ]
    
    try:
        # Initialize model
        print("\n1. Initializing Translation Model...")
        config = Config()
        model = TranslationModel(config)
        
        print("2. Loading model (this may take a while on first run)...")
        model.load_model()
        
        print("\n3. Testing translations:")
        print("-" * 60)
        
        for text in test_texts:
            result = model.translate(text)
            print(f"EN: {text:30} -> ZH: {result}")
        
        print("-" * 60)
        print("\n✅ AI Translation is working!")
        
        # Cleanup
        model.unload_model()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)
