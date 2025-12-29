"""
Complete AI Pipeline Example

Demonstrates the full AI workflow:
1. Load audio/video
2. Transcribe with Whisper
3. Detect voice segments with VAD
4. Merge and optimize segments
5. Export results
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import Config
from models.whisper_asr import WhisperASR
from models.vad_processor import VADProcessor
from utils.logger import setup_logger


logger = setup_logger()


def run_ai_pipeline(input_file: str, model_size: str = "medium"):
    """
    Run complete AI pipeline on audio/video file.
    
    Args:
        input_file: Path to audio or video file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        logger.error(f"File not found: {input_file}")
        return
    
    logger.info("=" * 60)
    logger.info("Canto-beats AI Pipeline Demo")
    logger.info("=" * 60)
    
    # Initialize config
    config = Config()
    
    # Step 1: Initialize models
    logger.info("\n[1/5] Initializing AI models...")
    whisper_asr = WhisperASR(config, model_size=model_size)
    vad_processor = VADProcessor(
        config,
        threshold=config.get('vad_threshold', 0.5),
        min_silence_duration_ms=config.get('min_silence_duration_ms', 500),
        min_speech_duration_ms=config.get('min_speech_duration_ms', 250)
    )
    
    logger.info(f"  ✓ Whisper ASR ({model_size})")
    logger.info(f"  ✓ Silero VAD")
    logger.info(f"  ✓ Device: {whisper_asr.device}")
    
    # Step 2: Load models
    logger.info("\n[2/5] Loading models...")
    whisper_asr.load_model()
    vad_processor.load_model()
    logger.info("  ✓ Models loaded")
    
    # Step 3: Detect language (optional)
    logger.info("\n[3/5] Detecting language...")
    detected_lang = whisper_asr.detect_language(input_file)
    logger.info(f"  ✓ Detected language: {detected_lang}")
    
    # Step 4: Transcribe
    logger.info("\n[4/5] Transcribing audio...")
    transcription = whisper_asr.transcribe(
        input_file,
        language=detected_lang,
        word_timestamps=True
    )
    
    logger.info(f"  ✓ Transcription complete")
    logger.info(f"  ✓ Segments: {len(transcription['segments'])}")
    logger.info(f"\n  Full text:\n  {transcription['text']}\n")
    
    # Step 5: Voice Activity Detection
    logger.info("[5/5] Detecting voice segments...")
    voice_segments = vad_processor.detect_voice_segments(input_file)
    logger.info(f"  ✓ Voice segments detected: {len(voice_segments)}")
    
    # Get speech ratio
    speech_ratio = vad_processor.get_speech_ratio(input_file)
    logger.info(f"  ✓ Speech ratio: {speech_ratio:.2%}")
    
    # Step 6: Merge transcription with VAD
    logger.info("\n[Bonus] Merging transcription with VAD segments...")
    merged_segments = vad_processor.merge_with_transcription(
        transcription['segments'],
        voice_segments,
        max_gap=1.0
    )
    
    logger.info(f"  ✓ Merged segments: {len(merged_segments)}")
    
    # Display results
    logger.info("\n" + "=" * 60)
    logger.info("RESULTS")
    logger.info("=" * 60)
    
    logger.info(f"\nOriginal segments: {len(transcription['segments'])}")
    logger.info(f"VAD segments: {len(voice_segments)}")
    logger.info(f"Merged segments: {len(merged_segments)}")
    
    logger.info("\nFirst 5 merged segments:")
    for i, seg in enumerate(merged_segments[:5]):
        duration = seg.end - seg.start
        logger.info(f"  {i+1}. [{seg.start:.2f}s - {seg.end:.2f}s] ({duration:.2f}s)")
        logger.info(f"     {seg.text}")
    
    # Cleanup
    logger.info("\n" + "=" * 60)
    logger.info("Cleaning up...")
    whisper_asr.cleanup()
    vad_processor.cleanup()
    logger.info("✓ Done!")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python examples/ai_pipeline_demo.py <audio_or_video_file> [model_size]")
        print("\nModel sizes: tiny, base, small, medium (default), large-v3")
        print("\nExample:")
        print("  python examples/ai_pipeline_demo.py video.mp4")
        print("  python examples/ai_pipeline_demo.py audio.wav large-v3")
        return
    
    input_file = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "medium"
    
    try:
        run_ai_pipeline(input_file, model_size)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
