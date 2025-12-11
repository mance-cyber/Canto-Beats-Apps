"""
Test faster-whisper implementation with yue language support
"""

import sys
sys.path.insert(0, 'src')

from models.whisper_asr import WhisperASR
from core.config import Config

def test_model_loading():
    """Test if model loads correctly"""
    print("=" * 60)
    print("Testing faster-whisper Model Loading")
    print("=" * 60)
    
    config = Config()
    print(f"\nDefault language: {config.get('default_language')}")
    print(f"Compute type: {config.get('compute_type')}")
    
    asr = WhisperASR(config)
    print(f"\nModel info (before loading): {asr.get_model_info()}")
    
    print("\nLoading model...")
    asr.load_model()
    
    print(f"\nModel info (after loading): {asr.get_model_info()}")
    print("\n✅ Model loaded successfully!")
    
    # Cleanup
    asr.cleanup()
    print("✅ Cleanup complete!")

if __name__ == "__main__":
    test_model_loading()
