
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import unittest
from subtitle.style_processor import StyleProcessor

class TestStyleProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = StyleProcessor()
        
    def test_cantonese_conversion(self):
        # Test Spoken (No change)
        text = "佢喺邊度睇靚女"
        res = self.processor._convert_cantonese(text, 'spoken')
        self.assertEqual(res, "佢喺邊度睇靚女")
        
        # Test Written (Convert All)
        # 佢->他, 喺->在, 邊度->哪裡, 睇->看, 靚->漂亮, 女->女兒
        res = self.processor._convert_cantonese(text, 'written')
        self.assertEqual(res, "他在哪裡看漂亮女兒")
        
        # Test Semi (Keep '睇', '靚', Convert '佢', '喺', '邊度')
        res = self.processor._convert_cantonese(text, 'semi')
        print(f"DEBUG: Semi result: '{res}'")
        # 佢->他, 喺->在, 邊度->哪裡 (not in keep list), 睇->睇 (keep), 靚->靚 (keep), 女->女兒 (mapped)
        self.assertEqual(res, "他在哪裡睇靚女兒")
        
    def test_profanity_filter(self):
        text = "你個含家鏟"
        
        # Test Keep
        res = self.processor._filter_profanity(text, 'keep')
        self.assertEqual(res, "你個含家鏟")
        
        # Test Mask
        res = self.processor._filter_profanity(text, 'mask')
        # Implementation uses '★'
        self.assertEqual(res, "你個★★★")
        
        # Test Mild
        res = self.processor._filter_profanity(text, 'mild')
        self.assertEqual(res, "你個全家餐")
        
    def test_number_format(self):
        # Test Arabic -> Chinese
        text = "我有123個蘋果"
        res = self.processor._format_numbers(text, 'chinese')
        self.assertEqual(res, "我有一二三個蘋果")
        
        # Test Chinese -> Arabic (Simple Digits)
        text = "我有一二三個蘋果"
        res = self.processor._format_numbers(text, 'arabic')
        self.assertEqual(res, "我有123個蘋果")
        
        # Test Chinese -> Arabic (Tens)
        self.assertEqual(self.processor._format_numbers("十一", 'arabic'), "11")
        self.assertEqual(self.processor._format_numbers("十二", 'arabic'), "12")
        self.assertEqual(self.processor._format_numbers("二十", 'arabic'), "20")
        self.assertEqual(self.processor._format_numbers("二十一", 'arabic'), "21")
        self.assertEqual(self.processor._format_numbers("九十九", 'arabic'), "99")
        self.assertEqual(self.processor._format_numbers("十", 'arabic'), "10")
        
    def test_english_handling(self):
        text = "Hello World"
        
        # Test Keep
        res = self.processor._process_english(text, 'keep')
        self.assertEqual(res, "Hello World")
        
        # Test Translate (Dictionary)
        # Hello->你好, World->世界
        res = self.processor._process_english(text, 'translate')
        self.assertEqual(res, "你好 世界")
        
        # Test Bilingual (Dictionary)
        res = self.processor._process_english(text, 'bilingual')
        self.assertEqual(res, "Hello World\n你好 世界")
        
        # Test Unknown Word
        text2 = "Hello Unknown"
        res = self.processor._process_english(text2, 'translate')
        self.assertEqual(res, "你好 Unknown")
        
    def test_long_line_splitting(self):
        # Create a long string > 25 chars
        text = "這是一個非常非常長的句子，長到需要被切分開來方便閱讀，你覺得呢？"
        segments = [{'start': 0, 'end': 10, 'text': text}]
        
        res = self.processor._split_long_lines(segments)
        self.assertEqual(len(res), 2)
        self.assertTrue(len(res[0]['text']) < len(text))
        self.assertTrue(len(res[1]['text']) < len(text))

if __name__ == '__main__':
    unittest.main()
