"""
Debug script to test transcription with detailed error logging
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import Config
from models.whisper_asr import WhisperASR
from models.vad_processor import VADProcessor
from utils.audio_utils import AudioPreprocessor

def test_transcription_debug(video_path):
    print("=" * 70)
    print("Debug Transcription Test")
    print("=" * 70)
    print(f"Video: {video_path}")
    
    config = Config()
    
    try:
        # Step 1: Extract audio
        print("\n[1/4] Extracting audio...")
        audio_path = AudioPreprocessor.extract_audio_from_video(video_path)
        print(f"  Audio extracted: {audio_path}")
        
        # Step 2: Load Whisper
        print("\n[2/4] Loading Whisper model...")
        asr = WhisperASR(config)
        asr.load_model()
        print("  Whisper loaded")
        
        # Step 3: Transcribe
        print("\n[3/4] Transcribing...")
        detected_lang = asr.detect_language(audio_path)
        print(f"  Detected language: {detected_lang}")
        
        transcription = asr.transcribe(
            audio_path,
            language=detected_lang,
            word_timestamps=True
        )
        print(f"  Transcription complete: {len(transcription['segments'])} segments")
        
        # Step 4: VAD Processing
        print("\n[4/4] VAD processing...")
        vad = VADProcessor(config)
        vad.load_model()
        
        voice_segments = vad.detect_voice_segments(audio_path)
        print(f"  Voice segments detected: {len(voice_segments)}")
        
        print("\n  Merging with transcription...")
        print(f"  Transcription segments: {len(transcription['segments'])}")
        
        # Debug: Check segment structure
        if transcription['segments']:
            seg = transcription['segments'][0]
            print(f"  Sample segment type: {type(seg)}")
            print(f"  Sample segment: {seg}")
            if hasattr(seg, 'words'):
                print(f"  Has words: {seg.words}")
        
        final_segments = vad.merge_with_transcription(
            transcription['segments'],
            voice_segments,
            max_gap=0.5,
            max_chars=30
        )
        
        print(f"\n  Final segments: {len(final_segments)}")
        print("\n" + "=" * 70)
        print("SUCCESS - No errors!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n" + "=" * 70)
        print(f"ERROR: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_path = r"E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/ECF/Footage/H2.MOV"
    test_transcription_debug(test_path)
