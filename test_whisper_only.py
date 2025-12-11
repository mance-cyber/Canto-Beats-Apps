"""
Detailed debug script with full error traceback
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import traceback
from core.config import Config
from models.whisper_asr import WhisperASR
from utils.audio_utils import AudioPreprocessor

def test_whisper_only(video_path):
    print("=" * 70)
    print("Testing Whisper Transcription Only")
    print("=" * 70)
    
    config = Config()
    
    try:
        # Extract audio
        print("\n[1/2] Extracting audio...")
        audio_path = AudioPreprocessor.extract_audio_from_video(video_path)
        print(f"  Audio: {audio_path}")
        
        # Load and test Whisper
        print("\n[2/2] Testing Whisper...")
        asr = WhisperASR(config)
        asr.load_model()
        print("  Model loaded")
        
        # Detect language
        print("\n  Detecting language...")
        detected_lang = asr.detect_language(audio_path)
        print(f"  Detected: {detected_lang}")
        
        # Transcribe
        print("\n  Transcribing (this will show full error if it fails)...")
        transcription = asr.transcribe(
            audio_path,
            language=detected_lang,
            word_timestamps=True
        )
        
        print(f"\n  SUCCESS!")
        print(f"  Segments: {len(transcription['segments'])}")
        print(f"  Text preview: {transcription['text'][:100]}...")
        
    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"ERROR OCCURRED: {type(e).__name__}: {e}")
        print(f"{'=' * 70}")
        print("\nFull Traceback:")
        traceback.print_exc()
        print(f"{'=' * 70}")

if __name__ == "__main__":
    test_path = r"E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/ECF/Footage/H2.MOV"
    test_whisper_only(test_path)
