import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from subtitle.style_processor import StyleProcessor
from core.config import Config

def test_long_line_splitting():
    print("測試長句分行功能")
    print("=" * 60)
    
    # Initialize processor
    processor = StyleProcessor(Config())
    
    # Test segments with long lines
    test_segments = [
        {
            'start': 0.0,
            'end': 5.0,
            'text': '這是一個非常非常長的句子，長到需要被切分開來方便閱讀，你覺得呢？',
            'words': []
        },
        {
            'start': 5.0,
            'end': 10.0,
            'text': '香港係一個好靚嘅地方，有好多好食嘅嘢食，亦都有好多好玩嘅地方可以去玩。',
            'words': []
        },
        {
            'start': 10.0,
            'end': 12.0,
            'text': '短句不會被分割',
            'words': []
        }
    ]
    
    print("\n原始字幕：")
    print("-" * 60)
    for i, seg in enumerate(test_segments):
        print(f"片段 {i+1}:")
        print(f"  時間: {seg['start']:.2f}s - {seg['end']:.2f}s")
        print(f"  長度: {len(seg['text'])} 字")
        print(f"  內容: {seg['text']}")
        print()
    
    # Apply splitting
    print("\n應用長句分行後：")
    print("-" * 60)
    result = processor._split_long_lines(test_segments)
    
    for i, seg in enumerate(result):
        print(f"片段 {i+1}:")
        print(f"  時間: {seg['start']:.2f}s - {seg['end']:.2f}s")
        print(f"  長度: {len(seg['text'])} 字")
        print(f"  內容: {seg['text']}")
        print()
    
    print("=" * 60)
    print(f"原始片段數: {len(test_segments)}")
    print(f"分行後片段數: {len(result)}")
    print(f"新增片段數: {len(result) - len(test_segments)}")
    
    # Test with style options
    print("\n\n測試完整風格處理（含分行）：")
    print("=" * 60)
    
    options = {
        'style': 'spoken',
        'english': 'keep',
        'numbers': 'arabic',
        'profanity': 'keep',
        'split_long': True  # 開啟長句分行
    }
    
    processed = processor.process(test_segments, options)
    
    print(f"處理後總片段數: {len(processed)}")
    for i, seg in enumerate(processed):
        print(f"\n片段 {i+1}: [{seg['start']:.2f}s - {seg['end']:.2f}s]")
        print(f"  {seg['text']}")

if __name__ == "__main__":
    test_long_line_splitting()
