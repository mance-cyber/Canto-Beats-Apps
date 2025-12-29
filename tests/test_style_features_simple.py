# -*- coding: utf-8 -*-
"""
Complete Style Control Panel Feature Test - Windows Compatible
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from subtitle.style_processor import StyleProcessor
from core.config import Config

def main():
    print("\n" + "=" * 70)
    print("Style Control Panel - All Features Test")
    print("=" * 70)
    
    processor = StyleProcessor(Config())
    results = []
    
    # Test 1: Cantonese Style
    print("\n[Test 1] Cantonese Style Conversion")
    text = "Kei5 hai2 bin1dou6 tai2 leng3 neoi2"
    spoken = processor._convert_cantonese(text, 'spoken')
    written = processor._convert_cantonese(text, 'written')
    print(f"  Spoken:  {spoken}")
    print(f"  Written: {written}")
    results.append(("Cantonese", spoken != written))
    
    # Test 2: English Handling
    print("\n[Test 2] English Handling")
    text = "Hello World"
    keep = processor._process_english(text, 'keep')
    translate = processor._process_english(text, 'translate')
    print(f"  Keep:      {keep}")
    print(f"  Translate: {translate}")
    results.append(("English", keep != translate))
    
    # Test 3: Number Format
    print("\n[Test 3] Number Format")
    text = "123"
    to_chinese = processor._format_numbers(text, 'chinese')
    to_arabic = processor._format_numbers(to_chinese, 'arabic')
    print(f"  Arabic:  {text}")
    print(f"  Chinese: {to_chinese}")
    print(f"  Back:    {to_arabic}")
    results.append(("Numbers", text != to_chinese))
    
    # Test 4: Profanity Filter
    print("\n[Test 4] Profanity Filter")
    from pathlib import Path
    prof_path = Path('src/resources/profanity_mapping.json')
    if prof_path.exists():
        import json
        with open(prof_path, 'r', encoding='utf-8') as f:
            prof_map = json.load(f)
        if prof_map:
            test_word = list(prof_map.keys())[0]
            keep = processor._filter_profanity(test_word, 'keep')
            mask = processor._filter_profanity(test_word, 'mask')
            print(f"  Original: {test_word}")
            print(f"  Masked:   {mask}")
            results.append(("Profanity", keep != mask))
        else:
            results.append(("Profanity", False))
    else:
        results.append(("Profanity", False))
    
    # Test 5: Long Line Split
    print("\n[Test 5] Long Line Splitting")
    segments = [{'start': 0, 'end': 5, 'text': 'A' * 30, 'words': []}]
    split = processor._split_long_lines(segments)
    print(f"  Original: {len(segments)} segment(s)")
    print(f"  Split:    {len(split)} segment(s)")
    results.append(("Split", len(split) > len(segments)))
    
    # Test 6: Combined Processing
    print("\n[Test 6] Combined Processing")
    test_seg = [{'start': 0, 'end': 3, 'text': '123 Hello', 'words': []}]
    options = {'style': 'written', 'english': 'translate', 
               'numbers': 'chinese', 'profanity': 'keep', 'split_long': False}
    processed = processor.process(test_seg, options)
    print(f"  Input:  {test_seg[0]['text']}")
    print(f"  Output: {processed[0]['text']}")
    results.append(("Combined", test_seg[0]['text'] != processed[0]['text']))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name:12s}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
