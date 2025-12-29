#!/usr/bin/env python3
"""測試書面語系統絕不輸出簡體字"""

import sys
import os

# Add src to path
sys.path.insert(0, '/Users/user/Downloads/Canto-Beats-Apps-main/src')

from subtitle.style_processor import StyleProcessor
from core.config import Config

def test_no_simplified_chinese():
    """測試：簡體字輸入必須轉為繁體"""
    print("=" * 60)
    print("測試：書面語系統繁體中文強制執行")
    print("=" * 60)
    
    processor = StyleProcessor(Config())
    
    # 測試案例：包含簡體字的文本
    test_cases = [
        ("尽管外面看上去很漂亮", "儘管外面看上去很漂亮"),  # 尽 -> 儘
        ("我觉得这个很好", "我覺得這個很好"),  # 觉 -> 覺, 这个 -> 這個
        ("尝试一下", "嘗試一下"),  # 尝试 -> 嘗試
        ("应该没问题", "應該沒問題"),  # 应该 -> 應該, 问题 -> 問題
        ("发现讯号验证", "發現訊號驗證"),  # 发现 -> 發現, 讯号 -> 訊號, 验证 -> 驗證
    ]
    
    segments = [{'start': i, 'end': i+1, 'text': text} for i, (text, _) in enumerate(test_cases)]
    
    options = {
        'style': 'spoken',  # Use spoken to avoid AI conversion, just test S2T
        'english': 'keep',
        'numbers': 'arabic',
        'punctuation': 'keep',
        'profanity': 'keep',
        'ai_correction': False,
        'split_long': False
    }
    
    print(f"\n處理 {len(test_cases)} 個測試案例...")
    result = processor.process(segments, options)
    
    # 驗證：不應包含簡體字
    simplified_chars = '尽觉尝试验证讯号发现问题应该这个怎么样时间'
    
    passed = 0
    failed = 0
    
    print("\n測試結果：")
    print("-" * 60)
    
    for i, (original, expected) in enumerate(test_cases):
        actual = result[i]['text']
        has_simplified = any(char in actual for char in simplified_chars)
        
        if has_simplified:
            print(f"❌ 案例 {i+1} 失敗")
            print(f"   原文: {original}")
            print(f"   實際: {actual}")
            print(f"   包含簡體字！")
            failed += 1
        else:
            print(f"✅ 案例 {i+1} 通過")
            print(f"   原文: {original}")
            print(f"   結果: {actual}")
            passed += 1
    
    print("-" * 60)
    print(f"\n總結：{passed} 通過 / {failed} 失敗 (總數: {len(test_cases)})")
    
    if processor.s2t_converter is None:
        print("\n⚠️  警告：OpenCC 未安裝，簡轉繁功能不可用！")
        print("   請安裝：pip install opencc-python-reimplemented")
        return False
    
    if failed == 0:
        print("\n✅ 所有測試通過！系統已正確強制繁體中文。")
        return True
    else:
        print(f"\n❌ {failed} 個測試失敗，系統仍有簡體字問題。")
        return False

if __name__ == '__main__':
    try:
        success = test_no_simplified_chinese()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行錯誤：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
