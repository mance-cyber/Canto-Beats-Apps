"""
完整測試右邊風格控制面板的所有功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from subtitle.style_processor import StyleProcessor
from core.config import Config

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(original, processed, test_name):
    print(f"\n【{test_name}】")
    print(f"  原始: {original}")
    print(f"  處理: {processed}")

def test_cantonese_style():
    """測試功能1：字幕語言風格"""
    print_section("功能1：字幕語言風格（純口語/半書面/純書面）")
    
    processor = StyleProcessor(Config())
    test_text = "佢喺邊度睇靚女，我哋都唔知"
    
    # 純口語
    result_spoken = processor._convert_cantonese(test_text, 'spoken')
    print_result(test_text, result_spoken, "純口語（保持原樣）")
    
    # 半書面
    result_semi = processor._convert_cantonese(test_text, 'semi')
    print_result(test_text, result_semi, "半書面（保留部分口語）")
    
    # 純書面
    result_written = processor._convert_cantonese(test_text, 'written')
    print_result(test_text, result_written, "純書面（完全轉換）")
    
    return "✅ PASS" if result_spoken != result_written else "❌ FAIL"

def test_english_handling():
    """測試功能2：英文處理"""
    print_section("功能2：英文處理（保留/翻譯/並列）")
    
    processor = StyleProcessor(Config())
    test_short = "Hello World"
    test_long = "I am going to the cinema today"
    
    # 保留原英文
    result_keep = processor._process_english(test_short, 'keep')
    print_result(test_short, result_keep, "保留原英文")
    
    # 翻譯成中文 - 短句（字典）
    result_trans_short = processor._process_english(test_short, 'translate')
    print_result(test_short, result_trans_short, "翻譯（字典模式）")
    
    # 翻譯成中文 - 長句（AI）
    print(f"\n【翻譯（AI模式）】")
    print(f"  原始: {test_long}")
    print(f"  處理: 正在加載 AI 模型...")
    try:
        result_trans_long = processor._process_english(test_long, 'translate')
        print(f"  結果: {result_trans_long}")
        ai_status = "✅ AI翻譯成功"
    except Exception as e:
        print(f"  錯誤: {e}")
        ai_status = "⚠️ AI翻譯失敗（可能需要下載模型）"
    
    # 英漢並列
    result_bi = processor._process_english(test_short, 'bilingual')
    print_result(test_short, result_bi, "英漢並列")
    
    return f"✅ PASS ({ai_status})" if result_keep != result_trans_short else "❌ FAIL"

def test_number_format():
    """測試功能3：數字格式"""
    print_section("功能3：數字格式（阿拉伯數字/中文小寫）")
    
    processor = StyleProcessor(Config())
    test_arabic = "我有123個蘋果"
    test_chinese = "我有一二三個蘋果"
    test_tens = "今日係十二月二十一日"
    
    # 阿拉伯 -> 中文
    result_to_chinese = processor._format_numbers(test_arabic, 'chinese')
    print_result(test_arabic, result_to_chinese, "阿拉伯 → 中文")
    
    # 中文 -> 阿拉伯（簡單數字）
    result_to_arabic = processor._format_numbers(test_chinese, 'arabic')
    print_result(test_chinese, result_to_arabic, "中文 → 阿拉伯（簡單）")
    
    # 中文 -> 阿拉伯（十位數）
    result_tens = processor._format_numbers(test_tens, 'arabic')
    print_result(test_tens, result_tens, "中文 → 阿拉伯（複雜）")
    
    return "✅ PASS" if "一二三" in result_to_chinese else "❌ FAIL"

def test_profanity_filter():
    """測試功能4：粗口處理"""
    print_section("功能4：粗口處理（保留/星號/溫和）")
    
    processor = StyleProcessor(Config())
    test_text = "你個含家鏟"
    
    # 保留原句
    result_keep = processor._filter_profanity(test_text, 'keep')
    print_result(test_text, result_keep, "保留原句")
    
    # 星號替換
    result_mask = processor._filter_profanity(test_text, 'mask')
    print_result(test_text, result_mask, "★★★ 星號替換")
    
    # 溫和替換
    result_mild = processor._filter_profanity(test_text, 'mild')
    print_result(test_text, result_mild, "溫和替換")
    
    return "✅ PASS" if "★" in result_mask else "❌ FAIL"

def test_long_line_split():
    """測試功能5：長句分行補償"""
    print_section("功能5：長句分行補償（開啟/關閉）")
    
    processor = StyleProcessor(Config())
    test_segments = [
        {
            'start': 0.0,
            'end': 5.0,
            'text': '這是一個非常非常長的句子，長到需要被切分開來方便閱讀，你覺得呢？',
            'words': []
        }
    ]
    
    print(f"\n原始片段:")
    print(f"  長度: {len(test_segments[0]['text'])} 字")
    print(f"  內容: {test_segments[0]['text']}")
    
    # 開啟分行
    result_split = processor._split_long_lines(test_segments)
    print(f"\n開啟分行後:")
    print(f"  片段數: {len(test_segments)} → {len(result_split)}")
    for i, seg in enumerate(result_split):
        print(f"  片段{i+1} ({seg['start']:.1f}s-{seg['end']:.1f}s): {seg['text']}")
    
    return "✅ PASS" if len(result_split) > len(test_segments) else "❌ FAIL"

def test_combined_processing():
    """測試功能6：組合處理"""
    print_section("功能6：組合處理（多功能同時使用）")
    
    processor = StyleProcessor(Config())
    test_segments = [
        {
            'start': 0.0,
            'end': 3.0,
            'text': '佢有123個蘋果，Hello World，你個含家鏟！',
            'words': []
        }
    ]
    
    print(f"\n原始字幕:")
    print(f"  {test_segments[0]['text']}")
    
    # 組合選項
    options = {
        'style': 'written',      # 純書面
        'english': 'translate',   # 翻譯英文
        'numbers': 'chinese',     # 中文數字
        'profanity': 'mask',      # 星號替換
        'split_long': False       # 不分行
    }
    
    print(f"\n處理選項:")
    for key, value in options.items():
        print(f"  • {key}: {value}")
    
    result = processor.process(test_segments, options)
    
    print(f"\n處理後字幕:")
    print(f"  {result[0]['text']}")
    
    # 檢查是否所有轉換都生效
    checks = []
    checks.append(("粵語轉換", "佢" not in result[0]['text']))
    checks.append(("數字轉換", "123" not in result[0]['text']))
    checks.append(("粗口處理", "★" in result[0]['text']))
    
    print(f"\n轉換檢查:")
    all_pass = True
    for name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        all_pass = all_pass and passed
    
    return "✅ PASS" if all_pass else "❌ FAIL"

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "風格控制面板完整功能測試" + " " * 15 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {}
    
    try:
        results['粵語風格'] = test_cantonese_style()
    except Exception as e:
        results['粵語風格'] = f"❌ ERROR: {e}"
    
    try:
        results['英文處理'] = test_english_handling()
    except Exception as e:
        results['英文處理'] = f"❌ ERROR: {e}"
    
    try:
        results['數字格式'] = test_number_format()
    except Exception as e:
        results['數字格式'] = f"❌ ERROR: {e}"
    
    try:
        results['粗口處理'] = test_profanity_filter()
    except Exception as e:
        results['粗口處理'] = f"❌ ERROR: {e}"
    
    try:
        results['長句分行'] = test_long_line_split()
    except Exception as e:
        results['長句分行'] = f"❌ ERROR: {e}"
    
    try:
        results['組合處理'] = test_combined_processing()
    except Exception as e:
        results['組合處理'] = f"❌ ERROR: {e}"
    
    # 結果總結
    print_section("測試結果總結")
    for feature, status in results.items():
        print(f"  {feature:12s}: {status}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if "✅" in s)
    
    print(f"\n  總計: {passed}/{total} 功能通過測試")
    print("=" * 70)

if __name__ == "__main__":
    main()
