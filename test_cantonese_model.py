"""
Quick test script to verify Cantonese Whisper model integration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.whisper_asr import WhisperASR
from core.config import Config

def test_model_loading():
    """Test if the new Cantonese model can be loaded."""
    print("=" * 60)
    print("Canto-beats: Cantonese Whisper Model Test")
    print("=" * 60)
    
    config = Config()
    print(f"\nConfiguration:")
    print(f"  Build type: {config.get('build_type')}")
    print(f"  Use Cantonese model: {config.get('use_cantonese_model')}")
    print(f"  Flagship model: {config.get('cantonese_model_flagship')}")
    print(f"  Lite model: {config.get('cantonese_model_lite')}")
    
    asr = WhisperASR(config)
    print(f"\nSelected model: {asr.model_id}")
    
    print("\nLoading model...")
    print("(This may take a while on first run as it downloads ~3GB)")
    
    try:
        asr.load_model()
        print("✅ Model loaded successfully!")
        
        model_info = asr.get_model_info()
        print(f"\nModel Info:")
        print(f"  Model ID: {model_info['model_id']}")
        print(f"  Device: {model_info['device']}")
        print(f"  Is Cantonese: {model_info['is_cantonese']}")
        print(f"  Loaded: {model_info['is_loaded']}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS: Cantonese model integration working!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Run the main application")
        print("  2. Load a Cantonese video")
        print("  3. Transcribe to get Cantonese characters (佢、喺、睇、嘅)")
        print("  4. Use style conversion (口語 → 書面語)")
        
        asr.cleanup()
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_model_loading()
