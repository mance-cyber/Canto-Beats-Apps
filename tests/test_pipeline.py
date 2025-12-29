"""
Verification script for VAD + LLM Subtitle Pipeline.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

from core.config import Config
from pipeline.subtitle_pipeline import SubtitlePipeline
from models.llm_processor import LLMProcessor

def main():
    print("="*60)
    print("VAD + LLM Pipeline Verification")
    print("="*60)
    
    config = Config()
    
    # 1. Test LLM Connection
    print("\n[1] Testing LLM Connection...")
    llm = LLMProcessor(config)
    if llm.check_connection():
        print("    [PASS] Ollama is reachable.")
    else:
        print("    [FAIL] Ollama is NOT reachable. Make sure it's running.")
        print("           Run 'ollama serve' and 'ollama pull qwen:14b'")
        return

    # 2. Test Audio
    if len(sys.argv) < 2:
        print("\n[!] No audio file provided for full pipeline test.")
        print("    Usage: python test_pipeline.py <audio_file>")
        return
        
    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print(f"\n[Error] Audio file not found: {audio_path}")
        return

    # 3. Test Pipeline
    print(f"\n[2] Testing Pipeline on: {audio_path}")
    print("    Initializing pipeline...")
    
    pipeline = SubtitlePipeline(config)
    
    print("    Running processing (this may take a while)...")
    
    try:
        subtitles = pipeline.process(audio_path, progress_callback=lambda p: print(f"    Progress: {p}%", end='\r'))
        print("\n    Processing complete!")
        
        print("\n[3] Results:")
        print("-" * 40)
        for i, sub in enumerate(subtitles):
            print(f"#{i+1} [{sub.start:.2f}s -> {sub.end:.2f}s]")
            print(f"{sub.text}")
            print("-" * 40)
            
    except Exception as e:
        print(f"\n[FAIL] Pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline.cleanup()

if __name__ == "__main__":
    main()
