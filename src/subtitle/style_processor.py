"""
Style Processor for subtitle text transformation.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from utils.logger import setup_logger
from models.translation_model import TranslationModel
from core.config import Config

# OpenCC for simplified to traditional conversion
try:
    from opencc import OpenCC
    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False

logger = setup_logger()

class StyleProcessor:
    """
    Process subtitle text based on style options.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config() # Fallback for tests
        self.cantonese_map = {}
        self.profanity_map = {}
        self.english_map = {}  # Initialize to prevent AttributeError
        self.translation_model = None
        self.llm_processor = None  # For AI-powered style conversion
        self.translation_cache = {}  # Cache for English translations: {english: chinese}
        
        # Initialize OpenCC for S2T conversion
        if HAS_OPENCC:
            self.s2t_converter = OpenCC('s2t')  # Simplified to Traditional
            logger.info("OpenCC S2T converter initialized")
        else:
            self.s2t_converter = None
            logger.warning("OpenCC not available, S2T conversion disabled")
        
        self._load_resources()
        
    def _load_resources(self):
        """Load mapping resources"""
        try:
            resource_dir = Path(__file__).parent.parent / 'resources'
            
            # Load Cantonese mapping
            canto_path = resource_dir / 'cantonese_mapping.json'
            if canto_path.exists():
                with open(canto_path, 'r', encoding='utf-8') as f:
                    self.cantonese_map = json.load(f)
            
            # Load Profanity mapping
            prof_path = resource_dir / 'profanity_mapping.json'
            if prof_path.exists():
                with open(prof_path, 'r', encoding='utf-8') as f:
                    self.profanity_map = json.load(f)

            # Load English mapping
            eng_path = resource_dir / 'english_mapping.json'
            if eng_path.exists():
                with open(eng_path, 'r', encoding='utf-8') as f:
                    self.english_map = json.load(f)
            else:
                self.english_map = {}
                    
            logger.info(f"Loaded resources: Canto={len(self.cantonese_map)}, Prof={len(self.profanity_map)}, Eng={len(self.english_map)}")
            
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")

    def process(self, segments: List[Dict], options: Dict, progress_callback=None) -> List[Dict]:
        """
        Main processing method - applies all style transformations.
        
        Args:
            segments: List of subtitle segments with 'start', 'end', 'text'
            options: Dict with style options from StyleControlPanel
            progress_callback: Optional callback function(current, total, message)
            
        Returns:
            Processed segments
        """
        if not segments:
            return []
            
        logger.info(f"Processing {len(segments)} segments with options: {options}")
        
        result_segments = []
        changes_made = 0
        
        # Batch AI processing (5 sentences at a time for speed)
        style = options.get('style', 'spoken')
        use_ai = options.get('ai_correction', False)
        
        ai_converted_texts = {}  # index -> converted text
        if use_ai and style in ('semi', 'written'):
            ai_converted_texts = self._batch_ai_convert(segments, style, progress_callback)
        
        for i, seg in enumerate(segments):
            original_text = seg.get('text', '')
            text = original_text
            
            # 1. Convert Cantonese style (use batch result if available)
            if i in ai_converted_texts:
                text = ai_converted_texts[i]
            elif style != 'spoken':
                text = self._convert_cantonese_dict(text, style)  # Dictionary fallback
            
            # 2. Handle English
            eng_mode = options.get('english', 'keep')
            text = self._process_english(text, eng_mode)
            
            # 3. Format numbers
            num_mode = options.get('numbers', 'arabic')
            text = self._format_numbers(text, num_mode)
            
            # 4. Filter profanity
            prof_mode = options.get('profanity', 'keep')
            text = self._filter_profanity(text, prof_mode)
            
            # 5. Remove trailing punctuation
            text = self._remove_trailing_punctuation(text)
            
            # 6. Convert any simplified Chinese to Traditional (final step)
            if self.s2t_converter:
                text = self.s2t_converter.convert(text)
            
            # Log changes for debugging
            if text != original_text:
                changes_made += 1
                if i < 5:  # Only log first 5 changes to avoid spam
                    logger.info(f"[StyleProcessor] Seg {i}: '{original_text[:30]}' -> '{text[:30]}'")
            
            # Create new segment with processed text
            new_seg = {
                'start': seg.get('start', 0),
                'end': seg.get('end', 0),
                'text': text,
                'words': seg.get('words', [])
            }
            result_segments.append(new_seg)
        
        # 6. Split long lines if requested
        if options.get('split_long', False):
            result_segments = self._split_long_lines(result_segments)
        
        logger.info(f"Processing complete: {len(result_segments)} segments, {changes_made} changes made")
        return result_segments
    
    def _remove_trailing_punctuation(self, text: str) -> str:
        """
        Remove trailing punctuation from subtitle text.
        
        Args:
            text: Input text
            
        Returns:
            Text with trailing punctuation removed
        """
        if not text:
            return text
        
        # Define punctuation to remove (Chinese and English)
        trailing_punct = '。，！？；：、.!?,;:'
        
        # Remove trailing punctuation
        while text and text[-1] in trailing_punct:
            text = text[:-1]
        
        return text

    def _batch_ai_convert(self, segments: List[Dict], style: str, progress_callback=None) -> Dict[int, str]:
        """
        Batch convert segments using AI (5 at a time).
        Returns dict of {index: converted_text}.
        """
        result = {}
        batch_size = 5
        
        # Initialize LLM if needed
        if self.llm_processor is None:
            try:
                from ui.download_dialog import check_and_download_model
                from core.hardware_detector import HardwareDetector
                from models.qwen_llm import QwenLLM
                
                detector = HardwareDetector()
                profile = detector.detect()
                
                model_ready = check_and_download_model(
                    profile.llm_a_model,
                    profile.llm_a_quantization,
                    parent=None
                )
                
                if not model_ready:
                    logger.warning("Model not ready, using dictionary")
                    return result
                
                self.llm_processor = QwenLLM(self.config, profile)
                self.llm_processor.load_models()
                logger.info("Qwen2.5-7B loaded for batch processing")
            except Exception as e:
                logger.warning(f"LLM init failed: {e}")
                return result
        
        # Process in batches
        from prompts.cantonese_prompts import COLLOQUIAL_TO_WRITTEN_PROMPT
        
        total_batches = (len(segments) + batch_size - 1) // batch_size
        
        for batch_idx, batch_start in enumerate(range(0, len(segments), batch_size)):
            batch_end = min(batch_start + batch_size, len(segments))
            batch_texts = [segments[i].get('text', '') for i in range(batch_start, batch_end)]
            
            # Report progress
            if progress_callback:
                progress = int((batch_idx / total_batches) * 100)
                progress_callback(batch_idx, total_batches, f"正在處理批次 {batch_idx + 1}/{total_batches}...")
            
            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])
            prompt = f"""# Role
你是一位專精香港粵語的語言轉換專家。

# Task
將以下粵語口語**完全轉換**成標準普通話書面語。每句需要獨立輸出並保持編號格式。

# Rules
1. **務必轉換所有粵語詞彙**，不是只添加標點符號
2. **絕對不要翻譯或修改任何英文**，英文必須原樣保留
3. 使用以下對照表進行轉換：
   - 係 → 是
   - 喺 → 在
   - 佢 → 他/她
   - 嘅 → 的
   - 唔 → 不
   - 冇 → 沒有
   - 咗 → 了
   - 嚟 → 來
   - 而家 → 現在
   - 成日 → 總是/經常
   - 返到 → 回到
   - 俾 → 給
   - 話 → 說
   - 諗 → 想
   - 睇 → 看
   - 搵 → 找
   - 去咗 → 去了
   - 嗰個 → 那個
   - 呢個 → 這個
   - 點解 → 為什麼
   - 乜嘢 → 什麼
4. 保持原意，使句子通順自然
5. 每句獨立處理，保持編號格式

# Example
輸入：
1. 你成日話你做生意 你係老闆
2. 佢琴日返到嚟
3. 我用 iPhone 打電話

輸出：
1. 你總是說你做生意，你是老闆
2. 他昨天回來了
3. 我用 iPhone 打電話

# 原文
{combined}

# 書面語輸出（保持編號）"""
            
            try:
                response = self.llm_processor._generate(
                    prompt, 
                    self.llm_processor._model_a, 
                    self.llm_processor._tokenizer_a,
                    max_new_tokens=1024,
                    temperature=0.05  # Low temperature for consistent conversion
                )
                
                # Parse numbered response
                for line in response.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            try:
                                num = int(parts[0]) - 1
                                text = parts[1].strip()
                                if 0 <= num < len(batch_texts):
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                logger.info(f"Batch {batch_idx + 1}: processed {len(batch_texts)} segments")
                
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}")
        
        # Report completion
        if progress_callback:
            progress_callback(total_batches, total_batches, "AI 轉換完成")
        
        return result
        """
        Batch convert segments using AI (5 at a time).
        Returns dict of {index: converted_text}.
        """
        result = {}
        batch_size = 5
        
        # Initialize LLM if needed
        if self.llm_processor is None:
            try:
                from ui.download_dialog import check_and_download_model
                from core.hardware_detector import HardwareDetector
                from models.qwen_llm import QwenLLM
                
                detector = HardwareDetector()
                profile = detector.detect()
                
                model_ready = check_and_download_model(
                    profile.llm_a_model,
                    profile.llm_a_quantization,
                    parent=None
                )
                
                if not model_ready:
                    logger.warning("Model not ready, using dictionary")
                    return result
                
                self.llm_processor = QwenLLM(self.config, profile)
                self.llm_processor.load_models()
                logger.info("Qwen2.5-7B loaded for batch processing")
            except Exception as e:
                logger.warning(f"LLM init failed: {e}")
                return result
        
        # Process in batches
        from prompts.cantonese_prompts import COLLOQUIAL_TO_WRITTEN_PROMPT
        
        for batch_start in range(0, len(segments), batch_size):
            batch_end = min(batch_start + batch_size, len(segments))
            batch_texts = [segments[i].get('text', '') for i in range(batch_start, batch_end)]
            
            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])
            prompt = f"""# Role
你是一位專精香港粵語的語言轉換專家。

# Task
將以下粵語口語**完全轉換**成標準普通話書面語。每句需要獨立輸出並保持編號格式。

# Rules
1. **務必轉換所有粵語詞彙**，不是只添加標點符號
2. **絕對不要翻譯或修改任何英文**，英文必須原樣保留
3. 使用以下對照表進行轉換：
   - 係 → 是
   - 喺 → 在
   - 佢 → 他/她
   - 嘅 → 的
   - 唔 → 不
   - 冇 → 沒有
   - 咗 → 了
   - 嚟 → 來
   - 而家 → 現在
   - 成日 → 總是/經常
   - 返到 → 回到
   - 俾 → 給
   - 話 → 說
   - 諗 → 想
   - 睇 → 看
   - 搵 → 找
   - 去咗 → 去了
   - 嗰個 → 那個
   - 呢個 → 這個
   - 點解 → 為什麼
   - 乜嘢 → 什麼
4. 保持原意，使句子通順自然
5. 每句獨立處理，保持編號格式

# Example
輸入：
1. 你成日話你做生意 你係老闆
2. 佢琴日返到嚟
3. 我用 iPhone 打電話

輸出：
1. 你總是說你做生意，你是老闆
2. 他昨天回來了
3. 我用 iPhone 打電話

# 原文
{combined}

# 書面語輸出（保持編號）"""
            
            try:
                response = self.llm_processor._generate(
                    prompt, 
                    self.llm_processor._model_a, 
                    self.llm_processor._tokenizer_a,
                    max_new_tokens=1024,
                    temperature=0.05  # Low temperature for consistent conversion
                )
                
                # Parse numbered response
                for line in response.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            try:
                                num = int(parts[0]) - 1
                                text = parts[1].strip()
                                if 0 <= num < len(batch_texts):
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                logger.info(f"Batch {batch_start//batch_size + 1}: processed {len(batch_texts)} segments")
                
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}")
        
        return result
    
    def _convert_cantonese_dict(self, text: str, style: str) -> str:
        """Dictionary-based Cantonese conversion (no AI)."""
        if style == 'spoken':
            return text
        
        keep_words_semi = ['睇', '靚', '啲', '咁', '咗', '嘅', '冇', '唔']
        result = text
        sorted_keys = sorted(self.cantonese_map.keys(), key=len, reverse=True)
        
        for canto_word, written_word in [(k, self.cantonese_map[k]) for k in sorted_keys]:
            if style == 'semi' and canto_word in keep_words_semi:
                continue
            if canto_word in result:
                result = result.replace(canto_word, written_word)
        
        return result

    def _convert_cantonese(self, text: str, style: str, use_ai: bool = False) -> str:
        """
        Convert Cantonese text based on style.
        
        Args:
            text: Input text
            style: 'spoken', 'semi', or 'written'
            use_ai: Use AI (QwenLLM) for context-aware conversion
            
        Returns:
            Converted text
        """
        if style == 'spoken':
            # Keep original Cantonese
            return text
        
        # AI conversion with Qwen2.5-7B (better quality than 1.5B)
        if use_ai and style in ('semi', 'written'):
            try:
                if self.llm_processor is None:
                    # Check if model needs to be downloaded first
                    from ui.download_dialog import check_and_download_model
                    from core.hardware_detector import HardwareDetector
                    
                    detector = HardwareDetector()
                    profile = detector.detect()
                    
                    # Show download dialog if model not cached
                    model_ready = check_and_download_model(
                        profile.llm_a_model,
                        profile.llm_a_quantization,
                        parent=None
                    )
                    
                    if not model_ready:
                        logger.warning("Model download cancelled or failed, using dictionary")
                        # Fall through to dictionary conversion
                    else:
                        # Load the model
                        logger.info("Initializing Qwen2.5-7B for AI style conversion...")
                        from models.qwen_llm import QwenLLM
                        self.llm_processor = QwenLLM(self.config, profile)
                        self.llm_processor.load_models()
                        logger.info("Qwen2.5-7B loaded successfully")
                
                # Use specialized prompt for colloquial-to-written conversion
                from prompts.cantonese_prompts import COLLOQUIAL_TO_WRITTEN_PROMPT
                prompt = COLLOQUIAL_TO_WRITTEN_PROMPT.format(text=text)
                
                # Generate response directly
                converted = self.llm_processor._generate(prompt, self.llm_processor._model_a, self.llm_processor._tokenizer_a,  max_new_tokens=512, temperature=0.3)
                
                # Clean up LLM output - remove common prefixes
                if converted:
                    converted = converted.strip()
                    # Remove common output prefixes
                    prefixes_to_remove = [
                        "書面語翻譯結果：", "書面語：", "翻譯結果：", 
                        "結果：", "翻譯：", "書面語版本："
                    ]
                    for prefix in prefixes_to_remove:
                        if converted.startswith(prefix):
                            converted = converted[len(prefix):].strip()
                    
                    if converted and converted != text.strip():
                        logger.info(f"AI conversion: '{text[:30]}...' -> '{converted[:30]}...'")
                        return converted
                    else:
                        logger.warning(f"AI returned same text or empty, using dictionary")
                    
            except Exception as e:
                logger.warning(f"AI conversion failed, falling back to dictionary: {e}")
        
        # Dictionary-based conversion (fallback or default)
        # For semi-written, keep certain colloquial words
        keep_words_semi = ['睇', '靚', '啲', '咁', '咗', '嘅', '冇', '唔']
        
        result = text
        conversions = []
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_keys = sorted(self.cantonese_map.keys(), key=len, reverse=True)
        
        for canto_word, written_word in [(k, self.cantonese_map[k]) for k in sorted_keys]:
            if style == 'semi' and canto_word in keep_words_semi:
                continue  # Skip conversion for semi-written style
            
            if canto_word in result:
                result = result.replace(canto_word, written_word)
                conversions.append(f"{canto_word}→{written_word}")
        
        if conversions:
            logger.debug(f"[Cantonese] Conversions: {', '.join(conversions[:5])}")
        
        return result

    def _filter_profanity(self, text: str, mode: str) -> str:
        """Filter profanity based on mode."""
        if mode == 'keep':
            return text
        
        result = text    
        # Sort by length to match phrases first
        sorted_keys = sorted(self.profanity_map.keys(), key=len, reverse=True)
        
        for prof_word in sorted_keys:
            if prof_word in result:
                if mode == 'mask':
                    result = result.replace(prof_word, '★' * len(prof_word))
                elif mode == 'mild':
                    mild_replacement = self.profanity_map[prof_word]
                    result = result.replace(prof_word, mild_replacement)
        
        return result

    def _format_numbers(self, text: str, mode: str) -> str:
        """Format numbers to Arabic or Chinese."""
        chinese_nums = '零一二三四五六七八九十百千萬'
        
        if mode == 'chinese':
            # Convert Arabic to Chinese
            digit_map = {'0': '零', '1': '一', '2': '二', '3': '三', 
                        '4': '四', '5': '五', '6': '六', '7': '七',
                        '8': '八', '9': '九'}
            
            def replace_digit(match):
                return ''.join(digit_map.get(d, d) for d in match.group(0))
            
            return re.sub(r'\d+', replace_digit, text)
        
        elif mode == 'arabic':
            # CRITICAL: Do NOT convert common words containing "一", "二", etc.
            # Exclusion list for common words that should NOT be converted
            exclude_words = [
                '一定', '一起', '一樣', '一直', '一切', '第一', '統一', '唯一', 
                '一下', '一次', '一個', '一點', '一些', '一般', '一邊', '一旦',
                '二手', '二次', '不二', '十分', '九成', '七十二', '三十六',
                '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日',
                '第三', '第四', '第五', '第六', '第七', '第八', '第九', '第十'
            ]
            
            # Create protection: temporarily replace excluded words with placeholders
            protected = {}
            for i, word in enumerate(exclude_words):
                if word in text:
                    placeholder = f"__PROTECTED_{i}__"
                    text = text.replace(word, placeholder)
                    protected[placeholder] = word
            
            # Convert Chinese to Arabic (basic patterns)
            # Map Chinese digits
            digit_map = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
                        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
            
            def convert_chinese_number(match):
                num_str = match.group(0)
                
                # Handle tens (十, 二十, 九十九, etc.)
                if '十' in num_str:
                    if num_str == '十':
                        return '10'
                    elif num_str[0] == '十':  # 十一, 十二...
                        ones = digit_map.get(num_str[1], 0) if len(num_str) > 1 else 0
                        return str(10 + ones)
                    else:  # 二十, 九十九...
                        tens = digit_map.get(num_str[0], 0)
                        ones = digit_map.get(num_str[2], 0) if len(num_str) > 2 else 0
                        return str(tens * 10 + ones)
                
                # Handle simple digit sequences ONLY if it's a standalone number
                # Single character numbers like "一" "二" should NOT be converted
                # unless they are truly numeric (e.g. "一月" -> keep, but standalone "一" in number context -> convert)
                if len(num_str) == 1:
                    # Single digit: likely part of a word, don't convert
                    return num_str
                    
                result = ''
                for char in num_str:
                    if char in digit_map:
                        result += str(digit_map[char])
                return result if result else num_str
            
            # Match Chinese number patterns (at least 2 consecutive digits or with 十)
            pattern = r'[零一二三四五六七八九]{2,}|[零一二三四五六七八九十]十[零一二三四五六七八九]?'
            text = re.sub(pattern, convert_chinese_number, text)
            
            # Restore protected words
            for placeholder, original in protected.items():
                text = text.replace(placeholder, original)
        
        return text

    # ... (other methods) ...

    def _process_english(self, text: str, mode: str) -> str:
        """Process English text with smart AI translation."""
        logger.debug(f"_process_english called: mode={mode}, text='{text[:50]}'")
        
        if mode == 'keep':
            return text
            
        # Detect English words
        if not re.search(r'[a-zA-Z]', text):
            logger.debug("No English detected, returning original")
            return text
        
        logger.info(f"English detected in '{text[:30]}...', mode={mode}")
        
        if mode == 'translate':
            # Smart translation: extract English portions and translate them
            return self._smart_translate_english(text)
            
        elif mode == 'bilingual':
            # Bilingual: Show both original and translated
            translated = self._smart_translate_english(text)
            if translated != text:
                return f"{text}\n{translated}"
            return text
            
        return text
    
    def _smart_translate_english(self, text: str) -> str:
        """
        Smart English translation for mixed Chinese-English text.
        Extracts English segments and translates them contextually.
        """
        # Pattern WITHOUT word boundaries (\b doesn't work with Chinese)
        # Match English words including hyphens and apostrophes
        english_pattern = re.compile(r"[a-zA-Z]+(?:[\s\-'][a-zA-Z]+)*", re.IGNORECASE)
        
        matches = list(english_pattern.finditer(text))
        
        if not matches:
            return text
        
        logger.info(f"Found {len(matches)} English segments in: '{text}'")
        
        # Process matches from end to start to preserve string indices
        result = text
        translated_cache = {}
        
        for match in reversed(matches):
            english_text = match.group(0).strip()
            
            if not english_text:
                continue
            
            # Check global cache first
            cache_key = english_text.lower()
            if cache_key in self.translation_cache:
                translation = self.translation_cache[cache_key]
                logger.debug(f"Using global cache: '{english_text}' -> '{translation}'")
            # Check local cache
            elif cache_key in translated_cache:
                translation = translated_cache[cache_key]
                logger.debug(f"Using local cache: '{english_text}' -> '{translation}'")
            else:
                translation = None
                
                # First, check dictionary for exact match (including phrases)
                if cache_key in self.english_map:
                    translation = self.english_map[cache_key]
                    logger.info(f"Dictionary exact: '{english_text}' -> '{translation}'")
                else:
                    # Try word-by-word translation for multi-word phrases
                    words = english_text.split()
                    if len(words) > 1:
                        translated_words = []
                        all_found = True
                        for word in words:
                            word_clean = word.lower().strip("-'.,!?")
                            if word_clean in self.english_map:
                                translated_words.append(self.english_map[word_clean])
                            else:
                                all_found = False
                                break
                        
                        if all_found and translated_words:
                            translation = ''.join(translated_words)
                            logger.info(f"Dictionary word-by-word: '{english_text}' -> '{translation}'")
                    
                    
                    # If still no translation, use AI translation
                    if not translation:
                        logger.info(f"Not in dictionary, using AI: '{english_text}'")
                        translation = self._translate_with_ai(english_text)
                        # If AI also fails, keep original
                        if not translation or translation == english_text:
                            translation = english_text
                            logger.warning(f"AI translation failed, keeping: '{english_text}'")
                
                # Cache result (both local and global)
                translated_cache[cache_key] = translation
                self.translation_cache[cache_key] = translation
            
            # Replace in text
            start, end = match.span()
            result = result[:start] + translation + result[end:]
            logger.debug(f"Replaced [{start}:{end}]: '{english_text}' -> '{translation}'")
        
        if result != text:
            logger.info(f"Final: '{text}' -> '{result}'")
        return result

    def _should_use_ai_translation(self, text: str) -> bool:
        """Check if we should use AI translation (e.g. sentence vs single word)."""
        # If text has more than 2 words, use AI
        return len(text.split()) > 2

    def _translate_with_ai(self, text: str) -> str:
        """
        Translate using dictionary-first approach, fallback to AI model.
        
        Args:
            text: English text to translate
            
        Returns:
            Translated Chinese text, or original if translation fails
        """
        # OPTIMIZATION: Try dictionary first (much faster)
        dict_result = self._dictionary_translate(text)
        if dict_result != text:
            # Found in dictionary, return immediately
            logger.info(f"Dictionary translated: '{text}' -> '{dict_result}'")
            return dict_result
        
        # Dictionary didn't have it, use AI model
        try:
            if not self.translation_model:
                logger.info("Initializing Translation Model...")
                self.translation_model = TranslationModel(self.config)
            
            result = self.translation_model.translate(text)
            
            # Validate result
            if result and result.strip() and result != text:
                logger.info(f"AI translated: '{text}' -> '{result}'")
                return result
            else:
                logger.warning(f"AI translation returned empty or same, keeping original")
                return text
                
        except Exception as e:
            logger.error(f"AI translation failed: {e}", exc_info=True)
            logger.warning("Falling back to dictionary translation")
            return self._dictionary_translate(text)
    
    def _dictionary_translate(self, text: str) -> str:
        """
        Fallback dictionary translation.
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text using dictionary
        """
        # Try word-by-word translation
        words = text.split()
        translated_words = []
        
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in self.english_map:
                translated_words.append(self.english_map[word_lower])
            else:
                translated_words.append(word)  # Keep original if not in dictionary
        
        result = ' '.join(translated_words)
        
        # If no translation happened, return original
        return result if result != text else text

    def _split_long_lines(self, segments: List[Dict]) -> List[Dict]:
        """Split long lines into two segments."""
        new_segments = []
        MAX_LEN = 25  # Threshold for splitting
        
        for seg in segments:
            text = seg['text']
            if len(text) > MAX_LEN:
                # Simple split at middle
                mid = len(text) // 2
                # Try to find punctuation near middle
                split_idx = mid
                
                # Search for punctuation
                punctuations = '，。！？、,.;?! '
                best_dist = float('inf')
                
                for i, char in enumerate(text):
                    if char in punctuations:
                        dist = abs(i - mid)
                        if dist < best_dist:
                            best_dist = dist
                            split_idx = i + 1
                
                # Split
                part1 = text[:split_idx].strip()
                part2 = text[split_idx:].strip()
                
                duration = seg['end'] - seg['start']
                mid_time = seg['start'] + (len(part1) / len(text)) * duration
                
                if part1:
                    new_segments.append({
                        'start': seg['start'],
                        'end': mid_time,
                        'text': part1,
                        'words': [] # Lost word info for now
                    })
                if part2:
                    new_segments.append({
                        'start': mid_time,
                        'end': seg['end'],
                        'text': part2,
                        'words': []
                    })
            else:
                new_segments.append(seg)
                
        return new_segments
