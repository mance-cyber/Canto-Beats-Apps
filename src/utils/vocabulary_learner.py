"""
Vocabulary Learner - 用戶詞彙學習模組

從用戶的修正中學習，提高個人化辨識準確度：
1. 記錄用戶修正的詞彙
2. 建立個人化詞彙庫
3. 生成 Whisper 提示詞
4. 自動校正常見錯誤
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger()


@dataclass
class VocabularyEntry:
    """詞彙條目"""
    correct_word: str           # 正確寫法
    wrong_variants: List[str]   # 錯誤變體列表
    frequency: int              # 使用頻率
    category: str               # 類別（人名、地名、專有名詞等）
    last_used: str              # 最後使用時間
    user_added: bool = True     # 是否由用戶添加


class VocabularyLearner:
    """
    用戶詞彙學習器

    功能：
    1. 從用戶修正中自動學習
    2. 建立個人化詞彙庫
    3. 生成 Whisper prompt 提高辨識率
    4. 自動校正已知錯誤
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化詞彙學習器

        Args:
            data_dir: 數據存儲目錄
        """
        if data_dir is None:
            data_dir = Path.home() / ".canto_beats"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.vocab_file = self.data_dir / "user_vocabulary.json"
        self.corrections_file = self.data_dir / "user_corrections.json"

        # 加載現有數據
        self.vocabulary: Dict[str, VocabularyEntry] = {}
        self.corrections_history: List[Dict] = []

        self._load_data()

    # ==================== 數據持久化 ====================

    def _load_data(self):
        """加載保存的詞彙數據"""
        # 加載詞彙庫
        if self.vocab_file.exists():
            try:
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for word, entry_data in data.items():
                        self.vocabulary[word] = VocabularyEntry(**entry_data)
                logger.info(f"✅ 加載 {len(self.vocabulary)} 個用戶詞彙")
            except Exception as e:
                logger.warning(f"加載詞彙庫失敗: {e}")

        # 加載修正歷史
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    self.corrections_history = json.load(f)
                logger.info(f"✅ 加載 {len(self.corrections_history)} 條修正歷史")
            except Exception as e:
                logger.warning(f"加載修正歷史失敗: {e}")

    def _save_data(self):
        """保存詞彙數據"""
        # 保存詞彙庫
        try:
            vocab_data = {
                word: asdict(entry)
                for word, entry in self.vocabulary.items()
            }
            with open(self.vocab_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存詞彙庫失敗: {e}")

        # 保存修正歷史
        try:
            with open(self.corrections_file, 'w', encoding='utf-8') as f:
                json.dump(self.corrections_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存修正歷史失敗: {e}")

    # ==================== 學習功能 ====================

    def learn_from_correction(
        self,
        original: str,
        corrected: str,
        context: str = "",
        category: str = "general"
    ):
        """
        從用戶修正中學習

        Args:
            original: 原始（錯誤）文字
            corrected: 修正後文字
            context: 上下文（可選）
            category: 類別（人名、地名等）
        """
        if original == corrected:
            return

        # 提取差異詞彙
        diff_pairs = self._extract_diff_pairs(original, corrected)

        for wrong, correct in diff_pairs:
            if not correct or not wrong:
                continue

            # 記錄到修正歷史
            self.corrections_history.append({
                "timestamp": datetime.now().isoformat(),
                "wrong": wrong,
                "correct": correct,
                "context": context,
                "category": category
            })

            # 更新詞彙庫
            if correct in self.vocabulary:
                # 已存在，更新
                entry = self.vocabulary[correct]
                if wrong not in entry.wrong_variants:
                    entry.wrong_variants.append(wrong)
                entry.frequency += 1
                entry.last_used = datetime.now().isoformat()
            else:
                # 新詞彙
                self.vocabulary[correct] = VocabularyEntry(
                    correct_word=correct,
                    wrong_variants=[wrong],
                    frequency=1,
                    category=category,
                    last_used=datetime.now().isoformat(),
                    user_added=True
                )

            logger.info(f"📚 學習新修正: '{wrong}' → '{correct}'")

        # 保存
        self._save_data()

    def _extract_diff_pairs(
        self,
        original: str,
        corrected: str
    ) -> List[Tuple[str, str]]:
        """
        提取原始和修正文字之間的差異詞彙對

        使用簡單的字符比對算法
        """
        pairs = []

        # 簡單策略：按空格/標點分詞，比較差異
        import re

        # 分詞
        orig_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', original)
        corr_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', corrected)

        # 使用 SequenceMatcher 找差異
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, orig_words, corr_words)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # 替換的詞
                orig_segment = ''.join(orig_words[i1:i2])
                corr_segment = ''.join(corr_words[j1:j2])
                if orig_segment and corr_segment:
                    pairs.append((orig_segment, corr_segment))

        return pairs

    # ==================== 自動校正 ====================

    def auto_correct(self, text: str) -> str:
        """
        使用學習的詞彙自動校正文本

        Args:
            text: 原始文本

        Returns:
            校正後文本
        """
        if not self.vocabulary:
            return text

        result = text
        corrections_made = []

        # 按頻率排序（高頻詞優先）
        sorted_vocab = sorted(
            self.vocabulary.items(),
            key=lambda x: x[1].frequency,
            reverse=True
        )

        for correct_word, entry in sorted_vocab:
            for wrong in entry.wrong_variants:
                if wrong in result:
                    result = result.replace(wrong, correct_word)
                    corrections_made.append((wrong, correct_word))

        if corrections_made:
            logger.info(f"📝 自動校正 {len(corrections_made)} 處")
            for wrong, correct in corrections_made[:5]:
                logger.debug(f"  '{wrong}' → '{correct}'")

        return result

    # ==================== Whisper Prompt 生成 ====================

    def generate_whisper_prompt(
        self,
        max_words: int = 50,
        category_filter: Optional[str] = None
    ) -> str:
        """
        生成 Whisper 提示詞

        將高頻詞彙加入提示，幫助 Whisper 更準確辨識

        Args:
            max_words: 最大詞彙數
            category_filter: 只包含特定類別

        Returns:
            Whisper prompt 字串
        """
        if not self.vocabulary:
            return ""

        # 篩選和排序
        filtered_vocab = [
            entry for entry in self.vocabulary.values()
            if category_filter is None or entry.category == category_filter
        ]

        # 按頻率排序
        sorted_vocab = sorted(
            filtered_vocab,
            key=lambda x: x.frequency,
            reverse=True
        )[:max_words]

        # 生成提示詞
        words = [entry.correct_word for entry in sorted_vocab]
        prompt = "以下係常用詞彙：" + "、".join(words)

        logger.info(f"📋 生成 Whisper prompt（{len(words)} 個詞彙）")
        return prompt

    # ==================== 詞彙管理 ====================

    def add_vocabulary(
        self,
        word: str,
        wrong_variants: List[str] = None,
        category: str = "general"
    ):
        """
        手動添加詞彙

        Args:
            word: 正確詞彙
            wrong_variants: 可能的錯誤變體
            category: 類別
        """
        if word in self.vocabulary:
            entry = self.vocabulary[word]
            if wrong_variants:
                entry.wrong_variants.extend(
                    [v for v in wrong_variants if v not in entry.wrong_variants]
                )
            entry.frequency += 1
        else:
            self.vocabulary[word] = VocabularyEntry(
                correct_word=word,
                wrong_variants=wrong_variants or [],
                frequency=1,
                category=category,
                last_used=datetime.now().isoformat(),
                user_added=True
            )

        self._save_data()
        logger.info(f"➕ 添加詞彙: '{word}'")

    def remove_vocabulary(self, word: str):
        """移除詞彙"""
        if word in self.vocabulary:
            del self.vocabulary[word]
            self._save_data()
            logger.info(f"➖ 移除詞彙: '{word}'")

    def get_vocabulary_list(self) -> List[Dict]:
        """獲取所有詞彙列表"""
        return [
            {
                "word": entry.correct_word,
                "variants": entry.wrong_variants,
                "frequency": entry.frequency,
                "category": entry.category
            }
            for entry in sorted(
                self.vocabulary.values(),
                key=lambda x: x.frequency,
                reverse=True
            )
        ]

    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        if not self.vocabulary:
            return {
                "total_words": 0,
                "total_corrections": 0,
                "average_confidence": 0.0,
                "categories": {}
            }

        # 類別統計
        categories = Counter(entry.category for entry in self.vocabulary.values())

        # 總修正次數
        total_corrections = sum(entry.frequency for entry in self.vocabulary.values())

        # 計算平均信心度（基於使用頻率）
        total_freq = total_corrections
        avg_confidence = min(1.0, total_freq / (len(self.vocabulary) * 5)) if self.vocabulary else 0

        return {
            "total_words": len(self.vocabulary),
            "total_corrections": total_corrections,
            "average_confidence": avg_confidence,
            "categories": dict(categories),
            "top_words": [
                entry.correct_word
                for entry in sorted(
                    self.vocabulary.values(),
                    key=lambda x: x.frequency,
                    reverse=True
                )[:10]
            ]
        }

    def clear_all(self):
        """清空所有詞彙和歷史記錄"""
        self.vocabulary.clear()
        self.corrections_history.clear()
        self._save_data()
        logger.info("🗑️ 已清空用戶詞彙庫")

    # ==================== 批量導入/導出 ====================

    def export_vocabulary(self, output_path: str):
        """導出詞彙庫到 JSON"""
        vocab_list = self.get_vocabulary_list()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vocab_list, f, ensure_ascii=False, indent=2)
        logger.info(f"📤 導出 {len(vocab_list)} 個詞彙到 {output_path}")

    def import_vocabulary(self, input_path: str, merge: bool = True):
        """
        從 JSON 導入詞彙庫

        Args:
            input_path: JSON 文件路徑
            merge: 是否合併（否則覆蓋）
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            vocab_list = json.load(f)

        if not merge:
            self.vocabulary.clear()

        for item in vocab_list:
            word = item.get('word', '')
            if word:
                self.add_vocabulary(
                    word,
                    wrong_variants=item.get('variants', []),
                    category=item.get('category', 'general')
                )

        self._save_data()
        logger.info(f"📥 導入 {len(vocab_list)} 個詞彙")


# ==================== 便利函數 ====================

_learner_instance: Optional[VocabularyLearner] = None


def get_vocabulary_learner() -> VocabularyLearner:
    """獲取全局詞彙學習器實例"""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = VocabularyLearner()
    return _learner_instance


def learn_correction(original: str, corrected: str, category: str = "general"):
    """快捷方法：學習一個修正"""
    learner = get_vocabulary_learner()
    learner.learn_from_correction(original, corrected, category=category)


def auto_correct_text(text: str) -> str:
    """快捷方法：自動校正文本"""
    learner = get_vocabulary_learner()
    return learner.auto_correct(text)


def get_whisper_prompt() -> str:
    """快捷方法：獲取 Whisper prompt"""
    learner = get_vocabulary_learner()
    return learner.generate_whisper_prompt()
