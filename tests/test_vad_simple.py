
import sys
import os
from pathlib import Path
import torch
import torchaudio

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.config import Config
from models.vad_processor import VADProcessor

def test_vad():
    print(f"Torch version: {torch.__version__}")
    print(f"Torchaudio version: {torchaudio.__version__}")
    
    try:
        import torchcodec
        print(f"Torchcodec version: {torchcodec.__version__}")
    except ImportError:
        print("Torchcodec NOT installed")

    # Find a wav file to test
    wav_files = list(Path(".").rglob("*.wav"))
    if not wav_files:
        print("No .wav files found for testing.")
        return

    test_file = wav_files[0]
    print(f"Testing VAD on: {test_file}")

    config = Config()
    vad = VADProcessor(config)
    
    try:
        vad.load_model()
        segments = vad.detect_voice_segments(test_file)
        print(f"Successfully detected {len(segments)} segments.")
        for seg in segments[:3]:
            print(f"  - {seg.start:.2f}s to {seg.end:.2f}s")
    except Exception as e:
        print(f"VAD Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vad()
