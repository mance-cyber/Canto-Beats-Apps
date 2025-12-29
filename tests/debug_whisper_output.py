"""
Debug script to check what data is being returned by Whisper
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import Config
from models.whisper_asr import WhisperASR
from utils.audio_utils import AudioPreprocessor

def debug_whisper_output(video_path):
    print("Debugging Whisper Output")
    print("=" * 70)
    
    config = Config()
    
    # Extract audio
    print("Extracting audio...")
    audio_path = AudioPreprocessor.extract_audio_from_video(video_path)
    
    # Load Whisper
    print("Loading Whisper...")
    asr = WhisperASR(config)
    asr.load_model()
    
    # Transcribe
    print("Transcribing...")
    result = asr.transcribe(audio_path, language='zh', word_timestamps=True)
    
    print(f"\nResult keys: {result.keys()}")
    print(f"Text: {result.get('text', 'NO TEXT')[:100]}")
    print(f"Number of segments: {len(result.get('segments', []))}")
    
    if result.get('segments'):
        print(f"\nFirst 3 segments:")
        for i, seg in enumerate(result['segments'][:3]):
            print(f"\nSegment {i}:")
            print(f"  Type: {type(seg)}")
            print(f"  {seg}")
    else:
        print("\nNO SEGMENTS FOUND - THIS IS THE PROBLEM!")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    video = r"E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/ECF/Footage/H2.MOV"
    debug_whisper_output(video)
