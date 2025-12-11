"""
Debug script to capture full error stack trace
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_transcription():
    from models.whisper_asr import WhisperASR
    from models.vad_processor import VADProcessor
    from core.config import Config
    from utils.audio_utils import AudioPreprocessor
    
    # Use your actual audio file
    audio_path = "E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/ECF/Footage/H2.wav"
    
    config = Config()
    
    print("="*60)
    print("Testing full transcription pipeline")
    print("="*60)
    
    try:
        # Step 1: Extract audio if needed
        print("\n1. Extracting audio...")
        preprocessor = AudioPreprocessor()
        # For testing, assume audio already extracted
        
        # Step 2: Load Whisper
        print("\n2. Loading Whisper model...")
        asr = WhisperASR(config)
        asr.load_model()
        print("   ✅ Whisper loaded")
        
        # Step 3: Load VAD
        print("\n3. Loading VAD model...")
        vad = VADProcessor(config)
        vad.load_model()
        print("   ✅ VAD loaded")
        
        # Step 4: Detect language
        print("\n4. Detecting language...")
        lang = asr.detect_language(audio_path)
        print(f"   ✅ Detected: {lang}")
        
        # Step 5: Transcribe
        print("\n5. Transcribing...")
        result = asr.transcribe(audio_path, language=lang, word_timestamps=True)
        print(f"   ✅ Transcription complete")
        print(f"   Text: {result['text'][:100]}...")
        
        # Step 6: VAD processing
        print("\n6. VAD processing...")
        voice_segments = vad.detect_voice_segments(audio_path)
        print(f"   ✅ Detected {len(voice_segments)} voice segments")
        
        # Step 7: Merge
        print("\n7. Merging...")
        final_segments = vad.merge_with_transcription(
            result['segments'],
            voice_segments,
            max_gap=0.5,
            max_chars=30
        )
        print(f"   ✅ Created {len(final_segments)} final segments")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR OCCURRED")
        print("="*60)
        print(f"\nError: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "="*60)

if __name__ == "__main__":
    test_transcription()
