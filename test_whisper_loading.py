
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.whisper_asr import WhisperASR
from core.config import Config

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_load_whisper():
    print("Testing Whisper model loading...")
    
    config = Config()
    # Use 'tiny' for faster testing
    asr = WhisperASR(config, model_size='tiny')

    try:
        asr.load_model()
        print("Successfully loaded Whisper model!")
        return True
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_load_whisper()
