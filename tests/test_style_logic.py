
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from subtitle.style_processor import StyleProcessor

def test_style_logic():
    print("Testing StyleProcessor Logic...")
    
    processor = StyleProcessor()
    
    # Test Data
    segments = [
        {'text': '我哋喺邊度食飯？', 'start': 0, 'end': 1},
        {'text': '佢話冇問題，搞掂晒。', 'start': 1, 'end': 2},
        {'text': '我有 123 個蘋果。', 'start': 2, 'end': 3}
    ]
    
    print(f"\nOriginal: {[s['text'] for s in segments]}")
    
    # Test 1: Written Style
    options_written = {'style': 'written', 'numbers': 'arabic'}
    result_written = processor.process(segments, options_written)
    print(f"\nWritten Style: {[s['text'] for s in result_written]}")
    
    # Test 2: Chinese Numbers
    options_nums = {'style': 'spoken', 'numbers': 'chinese'}
    result_nums = processor.process(segments, options_nums)
    print(f"\nChinese Numbers: {[s['text'] for s in result_nums]}")
    
    # Verify mappings
    print(f"\nCantonese Map Size: {len(processor.cantonese_map)}")
    if '我哋' in processor.cantonese_map:
        print(f"'我哋' -> '{processor.cantonese_map['我哋']}'")
    else:
        print("'我哋' NOT found in map")

if __name__ == "__main__":
    test_style_logic()
