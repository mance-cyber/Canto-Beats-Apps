"""
DEBUG SCRIPT: Test SubtitlePipelineV2 without Qt
This script runs the pipeline directly to isolate whether the crash is in:
1. The pipeline itself
2. Qt/QThread integration
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import torch

print("=" * 60)
print("DEBUG: Testing SubtitlePipelineV2 without Qt")
print("=" * 60)
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print()

# Test video path - change this to your test video
TEST_VIDEO = r"E:/Mance/Mercury/Project/2. Reels/2025/11. Nov/Get client/RTC/test.mp4"

def test_pipeline():
    print("Step 1: Importing modules...")
    from core.config import Config
    from pipeline.subtitle_pipeline_v2 import SubtitlePipelineV2
    print("  ✓ Imports OK")
    
    print("\nStep 2: Creating config...")
    config = Config()
    print("  ✓ Config OK")
    
    print("\nStep 3: Creating pipeline...")
    pipeline = SubtitlePipelineV2(config, force_cpu=False)
    print("  ✓ Pipeline created")
    
    def progress_callback(pct):
        print(f"  Progress: {pct}%")
    
    print("\nStep 4: Running pipeline...")
    try:
        subtitles = pipeline.process(TEST_VIDEO, progress_callback=progress_callback)
        print(f"  ✓ Pipeline complete! Generated {len(subtitles)} subtitles")
        
        for i, sub in enumerate(subtitles[:3]):  # Show first 3
            print(f"    [{i}] {sub.start:.2f}-{sub.end:.2f}: {sub.colloquial[:50]}...")
            
    except Exception as e:
        print(f"  ✗ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\nStep 5: Cleaning up pipeline...")
    try:
        pipeline.cleanup()
        print("  ✓ Cleanup complete")
    except Exception as e:
        print(f"  ✗ Cleanup error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\nStep 6: Waiting 2 seconds...")
    import time
    time.sleep(2)
    print("  ✓ No crash after cleanup")
    
    print("\nStep 7: Forcing garbage collection...")
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("  ✓ GC complete")
    
    print("\nStep 8: Waiting 2 more seconds...")
    time.sleep(2)
    print("  ✓ No crash after GC")
    
    print("\n" + "=" * 60)
    print("SUCCESS: Pipeline works without Qt!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import traceback
    try:
        success = test_pipeline()
        if success:
            print("\nConclusion: The crash is in Qt/QThread integration, not the pipeline itself.")
        else:
            print("\nConclusion: The pipeline has issues.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        print("\nConclusion: Pipeline crash found!")
    
    input("\nPress Enter to exit...")
