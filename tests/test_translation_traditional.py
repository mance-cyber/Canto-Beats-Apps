#!/usr/bin/env python3
"""
測試英文翻譯是否正確輸出繁體中文

測試流程：
1. 字典翻譯（應該是繁體）
2. Qwen LLM 翻譯（應該是繁體）
3. MarianMT 翻譯 + OpenCC 轉換（應該是繁體）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import Config
from subtitle.style_processor import StyleProcessor

def is_simplified(text: str) -> bool:
    """檢測是否包含簡體字（簡單檢測）"""
    simplified_chars = '个为来国产发现实际说话'
    traditional_chars = '個為來國產發現實際說話'
    
    for s, t in zip(simplified_chars, traditional_chars):
        if s in text and t not in text:
            return True
    return False

def test_translation():
    print("=" * 70)
    print("測試英文翻譯 - 繁體中文輸出驗證")
    print("=" * 70)
    
    # 測試用例
    test_cases = [
        # (英文, 預期包含的繁體字)
        ("hello", "你好"),
        ("world", "世界"),
        ("computer", "計算機"),  # MarianMT 使用大陸詞彙「計算機」而非港台「電腦」
        ("I love you", "愛"),
        ("thank you", "謝謝"),
        ("good morning", "早"),
    ]
    
    try:
        print("\n1. 初始化 StyleProcessor...")
        config = Config()
        processor = StyleProcessor(config)
        
        print(f"   OpenCC 可用: {processor.s2t_converter is not None}")
        
        print("\n2. 測試翻譯結果:")
        print("-" * 70)
        
        passed = 0
        failed = 0
        
        for english, expected_char in test_cases:
            # 模擬一個包含英文的句子
            test_text = f"這是測試 {english} 的句子"
            
            # 使用 translate 模式處理
            result = processor._process_english(test_text, mode='translate')
            
            # 檢查結果
            has_simplified = is_simplified(result)
            has_expected = expected_char in result if expected_char else True
            
            status = "✅" if (not has_simplified and has_expected) else "❌"
            
            if not has_simplified and has_expected:
                passed += 1
            else:
                failed += 1
            
            print(f"{status} '{english}' -> '{result}'")
            
            if has_simplified:
                print(f"   ⚠️  檢測到簡體字！")
            if not has_expected and expected_char:
                print(f"   ⚠️  未包含預期字符 '{expected_char}'")
        
        print("-" * 70)
        print(f"\n測試結果: {passed} 通過, {failed} 失敗")
        
        if failed == 0:
            print("\n✅ 所有測試通過！翻譯正確輸出繁體中文。")
            return True
        else:
            print(f"\n❌ {failed} 個測試失敗，請檢查 OpenCC 是否正確安裝。")
            return False
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)

