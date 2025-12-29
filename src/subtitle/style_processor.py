"""
Style Processor for subtitle text transformation.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional

from utils.logger import setup_logger
# NOTE: TranslationModel is NOT imported here to avoid triggering
# full transformers loading at startup (causes torchcodec issues in PyInstaller).
# Import it lazily in _translate_with_ai() when needed.
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
            self.s2t_converter = OpenCC('s2hk')  # Simplified to Traditional (Hong Kong)
            logger.info("OpenCC S2HK converter initialized")
        else:
            self.s2t_converter = None
            logger.warning("⚠️  OpenCC not available - AI translations may output Simplified Chinese!")
            logger.warning("    Install with: pip install opencc-python-reimplemented")
        
        self._load_resources()
        
    def _load_resources(self):
        """Load mapping resources - uses get_resource_path for PyInstaller compatibility"""
        from core.path_setup import get_resource_path
        
        try:
            # Use get_resource_path for PyInstaller compatibility
            # This correctly resolves paths in both development and packaged app
            
            # Load Cantonese mapping
            canto_path = get_resource_path('resources/cantonese_mapping.json')
            if Path(canto_path).exists():
                with open(canto_path, 'r', encoding='utf-8') as f:
                    self.cantonese_map = json.load(f)
            else:
                logger.warning(f"Cantonese mapping not found at: {canto_path}")
            
            # Load Profanity mapping
            prof_path = get_resource_path('resources/profanity_mapping.json')
            if Path(prof_path).exists():
                with open(prof_path, 'r', encoding='utf-8') as f:
                    self.profanity_map = json.load(f)
            else:
                logger.warning(f"Profanity mapping not found at: {prof_path}")

            # Load English mapping
            eng_path = get_resource_path('resources/english_mapping.json')
            if Path(eng_path).exists():
                with open(eng_path, 'r', encoding='utf-8') as f:
                    self.english_map = json.load(f)
            else:
                self.english_map = {}
                logger.warning(f"English mapping not found at: {eng_path}")
                    
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
        # AI 校正：書面語和半書面自動啟用 AI（無需額外勾選）
        use_ai = style in ('semi', 'written')
        
        ai_converted_texts = {}  # index -> converted text
        if use_ai and style in ('semi', 'written'):
            result = self._batch_ai_convert(segments, style, progress_callback)
            if result is not None:
                ai_converted_texts = result
            else:
                logger.warning("_batch_ai_convert returned None, using dictionary fallback")
        
        for i, seg in enumerate(segments):
            original_text = seg.get('text', '')
            text = original_text

            # 1. Convert Cantonese style (use batch result if available)
            if use_ai and style in ('semi', 'written'):
                # When using AI mode, skip segments not in ai_converted_texts
                # (they were removed as duplicates or failed processing)
                if i not in ai_converted_texts:
                    logger.debug(f"Skipping segment {i} (removed as duplicate or failed AI processing)")
                    continue
                text = ai_converted_texts[i]
                # Homophone corrections already applied in _batch_ai_convert preprocessing
            elif style != 'spoken':
                text = self._convert_cantonese_dict(text, style)  # Dictionary fallback for semi/written
                # Apply homophone corrections for dictionary-only mode
                text = self._apply_homophone_corrections(text, style)
            else:
                # Spoken mode: apply homophone corrections
                text = self._apply_homophone_corrections(text, style)
            
            # 2. Handle English
            eng_mode = options.get('english', 'keep')
            text = self._process_english(text, eng_mode)
            
            # 3. Format numbers
            num_mode = options.get('numbers', 'arabic')
            text = self._format_numbers(text, num_mode)
            
            # 4. Filter profanity
            prof_mode = options.get('profanity', 'keep')
            text = self._filter_profanity(text, prof_mode)
            
            # 5. Handle punctuation based on user option
            punct_mode = options.get('punctuation', 'keep')
            if punct_mode == 'remove':
                text = self._remove_all_punctuation(text)
            else:
                # 5b. Remove trailing punctuation only (default behavior)
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
            max_chars = options.get('max_chars', 14)  # Get from options
            result_segments = self._split_long_lines(result_segments, max_chars)
        
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
        
        # 首先清理所有類型嘅括號（Whisper 經常產生）
        brackets_to_remove = '()（）﹙﹚[]【】「」'
        for bracket in brackets_to_remove:
            text = text.replace(bracket, '')
        
        # Define punctuation to remove (Chinese and English)
        trailing_punct = '。，！？；：、.!?,;:'
        
        # Remove trailing punctuation
        while text and text[-1] in trailing_punct:
            text = text[:-1]
        
        return text

    def _apply_homophone_corrections(self, text: str, style: str = 'spoken') -> str:
        """
        Apply homophone corrections to fix common Whisper transcription errors.
        Style-aware: some corrections only apply in spoken mode.
        
        Args:
            text: Input text with potential homophone errors
            style: 'spoken', 'semi', or 'written'
            
        Returns:
            Text with homophone errors corrected
        """
        if not text:
            return text
        
        # Universal homophone fixes (apply in ALL modes)
        universal_fixes = {
            # Common transcription errors
            "原費": "月費",
            "財源名單": "裁員名單",
            "財源": "裁員",
            "博殺": "搏殺",
            "禁入去": "撳入去",
            "友誼": "猶豫",
            "告名": "報名",
            "講濃": "講NO",
            "濃嘅底氣": "NO嘅底氣",
            "濃厚的底氣": "NO的底氣",  # 書面語版本
            "濃的底氣": "NO的底氣",
            "半份量": "半份糧",
            "第二份量": "第二份糧",
            "份量": "份糧",  # 通用修正
            "a啲ul": "Aesop",
            "pow啲er": "powder",
            "olivian": "Olive Young",
            "iPa啲": "iPad",
            "不知道道": "不知道",
            "知道道": "知道",
            "無人": "無印",  # Context: 無印良品
            "不看不看": "唔推唔推",
            "关闭电话": "解僱",  # call off
            "call off": "取消",  # 英文直譯錯誤
            "俾人call off": "被取消",
            "我才是": "我是",  # "我才是Linxia" 應該是 "我是Linxia"
            "即刻告名": "即刻報名",
            "立刻禁入": "立刻撳入",
            "撳入去": "點入去",  # 正確粵語用法

            # 從長影片分析發現的錯誤
            "處於一種": "陷入一個",  # 「處於一種兩難」→「陷入一個兩難」
            "那塊面": "嗰塊面",  # 書面語錯誤
            "那盞燈": "嗰盞燈",
            "那個": "嗰個",  # 除非已經是書面語模式
            "這樣做": "咁樣做",
            "這樣的": "咁樣嘅",
            "衝動消費": "衝動消費",  # 保持正確
            "淡剔": "清淡",  # 粵語→書面語

            # Simplified to Traditional Chinese fixes
            "灵": "靈",
            "迈克尔": "Michael",
            "一个": "一個",
            "这个": "這個",
            "觉得": "覺得",
        }
        
        # Spoken-mode-only fixes (書面語→粵語口語)
        # These should NOT apply in written mode
        spoken_only_fixes = {
            "哪一個": "邊一個",  # Whisper outputs 書面語, fix to 口語
        }
        
        original = text
        
        # Apply universal fixes
        for wrong, correct in universal_fixes.items():
            if wrong in text:
                text = text.replace(wrong, correct)
        
        # Apply spoken-only fixes ONLY in spoken mode
        if style == 'spoken':
            for wrong, correct in spoken_only_fixes.items():
                if wrong in text:
                    text = text.replace(wrong, correct)
        
        if text != original:
            logger.debug(f"[Homophone] Fixed: '{original[:30]}...' -> '{text[:30]}...'")
        
        return text

    def _remove_all_punctuation(self, text: str) -> str:
        """
        Remove all punctuation marks from subtitle text.
        
        Args:
            text: Input text
            
        Returns:
            Text with all punctuation removed
        """
        if not text:
            return text
        
        original_text = text
        
        # All punctuation to remove (Chinese and English)
        all_punct = '，。！？、；：,.!?;:；—…「」『』【】《》〈〉()（）﹙﹚[]'
        
        for p in all_punct:
            text = text.replace(p, '')
        
        if text != original_text:
            logger.info(f"[PUNCT] Removed punctuation: '{original_text[:30]}...' -> '{text[:30]}...'")
        
        return text

    def _batch_ai_convert(self, segments: List[Dict], style: str, progress_callback=None) -> Dict[int, str]:
        """
        Batch convert segments using AI.
        Priority: MLX Qwen (Apple Silicon) > Transformers Qwen (fallback)
        Returns dict of {index: converted_text}.
        """
        result = {}
        batch_size = 3  # Reduced from 5 for more reliable AI processing

        # DEBUG: Log the style value
        logger.info(f"🎨 [STYLE DEBUG] _batch_ai_convert called with style='{style}'")

        # ========================================
        # 【前處理】在 AI 轉換之前，先修正同音字錯誤
        # ========================================
        preprocessed_segments = []
        for seg in segments:
            text = seg.get('text', '')
            # 應用同音字修正（spoken mode，因為此時還是口語）
            text = self._apply_homophone_corrections(text, style='spoken')
            preprocessed_seg = seg.copy()
            preprocessed_seg['text'] = text
            preprocessed_segments.append(preprocessed_seg)

        # 使用預處理後的 segments
        segments = preprocessed_segments
        
        # Initialize LLM if needed - auto-detect best backend
        if self.llm_processor is None:
            try:
                import gc
                import torch
                
                # Clear GPU memory before loading model
                logger.info("Clearing GPU memory before loading Qwen model...")
                gc.collect()
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                    logger.info("MPS memory cleared")
                elif torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("CUDA memory cleared")
                
                # Auto-detect hardware and get best backend
                from utils.qwen_mlx import get_qwen_for_hardware, MLXQwenLLM
                
                hw_config = get_qwen_for_hardware()
                logger.info(f"🔍 Hardware detection: {hw_config['description']}")
                
                if hw_config['backend'] == 'mlx':
                    # Use MLX Qwen (Apple Silicon optimized)
                    from utils.qwen_mlx import MLXQwenLLM
                    from huggingface_hub import try_to_load_from_cache
                    
                    model_id = hw_config['model_id']
                    
                    # Check if model is cached
                    cache_result = try_to_load_from_cache(model_id, "config.json")
                    model_cached = cache_result is not None
                    
                    if not model_cached:
                        # 模型未缓存 - 应该已在主线程预先下载（main_window._ensure_llm_model_ready）
                        # 如果走到这里说明主线程的检查被跳过了
                        logger.warning("MLX Qwen model not cached - should be downloaded from main thread")
                        logger.warning("Falling back to dictionary mode (UI dialogs cannot be shown from worker thread)")
                        return result

                    # 模型已缓存，直接加载
                    try:
                        self.llm_processor = MLXQwenLLM(model_id=model_id)
                        self.llm_processor.load_model()
                        self._using_mlx = True
                        logger.info(f"⚡ {hw_config['description']} loaded")
                    except Exception as load_error:
                        logger.error(f"Failed to load MLX Qwen model: {load_error}", exc_info=True)
                        # 不显示 UI，直接返回（让调用者使用字典模式）
                        logger.warning("Falling back to dictionary mode due to model load failure")
                        return result
                else:
                    # Use Transformers Qwen (MPS/CUDA/CPU)
                    self._using_mlx = False
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
                    logger.info(f"✅ {hw_config['description']} loaded")
                    
            except Exception as e:
                logger.warning(f"LLM init failed: {e}")
                return result
        
        # CRITICAL CHECK: If LLM failed to initialize, don't proceed with AI conversion
        if self.llm_processor is None:
            logger.warning("LLM processor is None, cannot perform AI conversion - using dictionary fallback")
            return result
        
        # Process in batches with sliding window context
        total_batches = (len(segments) + batch_size - 1) // batch_size
        context_window = 2  # 前後各提供 2 句作為上下文

        for batch_idx, batch_start in enumerate(range(0, len(segments), batch_size)):
            batch_end = min(batch_start + batch_size, len(segments))
            batch_texts = [segments[i].get('text', '') for i in range(batch_start, batch_end)]

            # Report progress
            if progress_callback:
                progress_callback(batch_idx, total_batches, f"AI 轉換 {batch_idx + 1}/{total_batches}...")

            # ========================================
            # 【滑動窗口】提供前後上下文給 LLM
            # ========================================
            # 前文 (preceding context)
            context_before = []
            context_before_start = max(0, batch_start - context_window)
            if context_before_start < batch_start:
                context_before = [segments[i].get('text', '') for i in range(context_before_start, batch_start)]

            # 後文 (following context)
            context_after = []
            context_after_end = min(len(segments), batch_end + context_window)
            if batch_end < context_after_end:
                context_after = [segments[i].get('text', '') for i in range(batch_end, context_after_end)]

            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])

            # 構建完整上下文（如果有的話）
            context_prompt = ""
            if context_before:
                context_before_text = "\n".join([f"  {t}" for t in context_before])
                context_prompt += f"\n【前文上下文】（僅供參考，不要轉換）\n{context_before_text}\n"

            if context_after:
                context_after_text = "\n".join([f"  {t}" for t in context_after])
                context_prompt += f"\n【後續內容】（僅供參考，不要轉換）\n{context_after_text}\n"

            # Different prompts for semi vs written style
            if style == 'semi':
                # 半書面語：轉換部分粵語字，但保留最核心嘅粵語特色
                prompt = f"""你是一位專業粵語字幕編輯。任務是將口語字幕轉成「半書面語」風格 — 介乎純口語同純書面之間。

【核心目標】
- 部分轉換：將常見粵語字轉成書面語，但保留粵語嘅核心特色
- 移除語氣詞：囉、喎、嘞、㗎、吓、喇 等過度口語化嘅語氣詞
- 英文必須保留：所有英文單詞一律保持原樣
- 阿拉伯數字保留：5萬、10萬、2000 保持原樣
- **🔥 嚴格保持斷句邊界**：每一行輸入對應一行輸出，不要合併或拆分句子

【需要轉換】
係→是、喺→在、佢→他/她、佢哋→他們、嚟→來、咗→了
邊度→哪裡、點解→為什麼、乜嘢→什麼、呢個→這個、嗰個→那個
今日→今天、聽日→明天、琴日/尋日→昨天、而家→現在

【必須保留 - 粵語核心字】
嘅（保留，唔好變成「的」）、唔（保留，唔好變成「不」）、冇（保留，唔好變成「沒有」）
啲（保留）、咁（保留）、睇（保留）、靚（保留）
{context_prompt}
【需要轉換的內容】
{combined}

【輸出】（只輸出轉換結果，保持編號 1、2、3...）"""
            else:
                # 書面語：徹底轉換所有粵語字
                prompt = f"""你是一位專業中文編輯與字幕轉寫師。你的任務是把「粵語口語字幕」徹底轉譯成「自然流暢的書面中文」。

【🔥 視角設定 — 絕對不可違反】
- 說話者：一位 YouTuber（第一人稱），正在描述自己的日常生活
- 所有「我哋」→「我們」、「我」保持「我」
- **絕對禁止**：把「我」改成「他/她/你」、把「我們」改成「他們」
- 如果句子是「我去了...」，轉換後必須仍是「我去了...」，不能變成「他去了...」

【絕對要求】
- **必須使用繁體中文**：輸出必須是繁體字（Traditional Chinese），絕對不可以使用簡體字（Simplified Chinese）。
- 繁體字範例：儘管、覺得、嘗試、驗證、訊號、發現、問題、應該、這個、一個
- **簡體字黑名單**（絕對禁止）：尽管、觉得、尝试、验证、讯号、发现、问题、应该、这个、一个

【核心目標】
- 完全書面化：把口語、粵語語氣詞、口頭禪、潮語改成正式書面表達。
- 不改意思：保留原句資訊、語氣強弱，但用書面語呈現。
- 適合做字幕：句子要簡潔、易讀、自然。
- **英文必須保留**：所有英文單詞、品牌、人名、術語等，絕對不要翻譯成中文。

【轉譯規則】
1. **完全移除粵語語氣詞**：「喎、啦、囉、咩、㗎、吓、呀、喇、啫、嘛」等必須完全移除，不要保留。
2. 粗口處理：改成較文明的同等語氣（例如「好撚煩」→「非常煩人」）。
3. 句末標點要書面：疑問用「？」、感嘆用「！」，其餘用「。」或「，」。
4. 不要添加新資訊、不要解釋、不要評論。
5. 只輸出轉譯後文字，保持編號格式。
6. **絕對不可重複**：如果前一句已經說過相同內容，不要再次輸出。
7. **英文必須保留**：所有英文單詞、人名、品牌、術語、數字等，一律保持原樣，絕對不要翻譯成中文。
8. **🔥 嚴格保持斷句邊界**：每一行輸入對應一行輸出，絕對不要合併多行或拆分單行。每個編號的內容必須完整轉譯，不要截斷句子。

【常見轉換 - 必須全部執行】
係→是、喺→在、唔→不、冇→沒有、嘅→的、咗→了、嚟→來、佢→他/她
好彩→幸運、頭先→剛才、琴日→昨天、聽日→明天、今日→今天、而家→現在
個鐘→小時、蚊→元、即係→就是、點解→為什麼、乜嘢→什麼、邊度→哪裡
睇→看、靚→漂亮、啲→些、咁→這樣、唔該→謝謝/請
拎→拿、揾→找、攞→拿、畀→給、屋企→家、好似→好像

【🔥 英文/專有名詞保留 — 絕對不可翻譯】
- "Apple" 保持 "Apple"，不要變成「蘋果」
- "iPhone" 保持 "iPhone"，不要變成「愛瘋」
- "CEO" 保持 "CEO"，不要變成「執行長」
- "AI" 保持 "AI"，不要變成「人工智能」
- "flock" 保持 "flock"，不要變成「羊群」
- "freelance" 保持 "freelance"，不要變成「自由職業」
- "creator" 保持 "creator"，不要變成「創作者」
- "studio" 保持 "studio"，不要變成「工作室」或「學生」
- "color test" 保持 "color test"，不要變成「色彩測試」
- **原則**：所有英文單詞、品牌名、人名、專業術語一律保留原文

【重要】數字保留範例：
- "5萬" 保持 "5萬"，不要變成「五萬」
- "10萬" 保持 "10萬"，不要變成「十萬」
- "2000" 保持 "2000"，不要變成「二千」
- 所有阿拉伯數字一律保持原樣，絕對不要轉成中文數字

【風格】繁體中文書面語，清晰自然。嚴格度：最高，凡是口語化表達一律改成書面語。
{context_prompt}
【需要轉換的內容】
{combined}

【輸出】（只輸出轉換結果，保持編號 1、2、3...，不要輸出前文或後續內容）"""
            
            try:
                # Generate response - use correct method based on backend
                if getattr(self, '_using_mlx', False):
                    response = self.llm_processor.generate(
                        prompt,
                        max_tokens=1024,
                        temperature=0
                    )
                else:
                    # Fallback for non-MLX LLM (shouldn't happen with MLXQwenLLM)
                    response = self.llm_processor.generate(
                        prompt,
                        max_tokens=1024,
                        temperature=0
                    )
                
                # === DEBUG: Log raw AI response ===
                logger.info(f"=== RAW AI RESPONSE (Batch {batch_idx + 1}) ===")
                logger.info(response[:500] if len(response) > 500 else response)
                logger.info("=== END RAW RESPONSE ===")
                
                # Parse numbered response
                for line in response.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            try:
                                num = int(parts[0]) - 1
                                text = parts[1].strip()
                                
                                # === 嚴格清理 AI 輸出 ===
                                # 0. 移除 markdown 強調標記 ** 和 *
                                text = text.replace('**', '')
                                # Remove single * only if it appears to be markdown (not multiplication)
                                text = re.sub(r'(?<![\d\s])\*(?![\d\s])', '', text)
                                
                                # 1. 如果有箭頭符號，只取箭頭後面嘅內容
                                if '→' in text:
                                    text = text.split('→')[-1].strip()
                                if '->' in text:
                                    text = text.split('->')[-1].strip()
                                
                                # 2. 移除所有類型括號
                                for bracket in '()（）﹙﹚[]【】「」':
                                    text = text.replace(bracket, '')
                                
                                # 3. 清除異常尾部字符（不包括「是」因為是有效書面語）
                                while text and text[-1] in ')）」】呢啦':
                                    text = text[:-1].strip()
                                
                                # 4. 去除多餘空白
                                text = ' '.join(text.split())
                                
                                # ⚠️ 【關鍵】強制轉換為繁體中文（絕對禁忌簡體字）
                                if self.s2t_converter:
                                    text = self.s2t_converter.convert(text)
                                    logger.debug(f"[S2T] Converted AI output to Traditional: '{text[:30]}'")
                                
                                if 0 <= num < len(batch_texts) and text:
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                # Log how many were successfully parsed
                parsed_count = sum(1 for i in range(batch_start, batch_end) if i in result)
                logger.info(f"Batch {batch_idx + 1}/{total_batches}: parsed {parsed_count}/{len(batch_texts)} segments")
                
                # If batch completely failed, retry once with smaller input
                if parsed_count == 0 and len(response.strip()) == 0:
                    logger.warning(f"Batch {batch_idx + 1} returned empty, retrying...")
                    # Retry with same batch
                    try:
                        response = self.llm_processor.generate(prompt, max_tokens=1024, temperature=0.1)
                        if response and response.strip():
                            logger.info(f"Retry succeeded for batch {batch_idx + 1}")
                            # Parse again
                            for line in response.strip().split('\n'):
                                line = line.strip()
                                if line and line[0].isdigit():
                                    parts = line.split('.', 1)
                                    if len(parts) == 2:
                                        try:
                                            num = int(parts[0]) - 1
                                            text = parts[1].strip()
                                            if 0 <= num < len(batch_texts) and text:
                                                result[batch_start + num] = text
                                        except ValueError:
                                            pass
                    except Exception as retry_e:
                        logger.warning(f"Retry also failed: {retry_e}")
                
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}", exc_info=True)
        
        # Report completion
        if progress_callback:
            progress_callback(total_batches, total_batches, "AI 轉換完成！")
        
        # Post-process with dictionary to fix AI missed conversions
        # === SEMI MODE: 轉換部分粵語字，保留核心字 ===
        post_fix_map_semi = {
            # 半書面語：轉換呢啲字
            "係": "是",
            "喺": "在",
            "佢": "他",
            "佢哋": "他們",
            "嚟": "來",
            "咗": "了",
            "呢個": "這個",
            "嗰個": "那個",
            "呢啲": "這些",
            "嗰啲": "那些",
            "邊度": "哪裡",
            "點解": "為什麼",
            "乜嘢": "什麼",
            "今日": "今天",
            "聽日": "明天",
            "琴日": "昨天",
            "尋日": "昨天",
            "而家": "現在",
            "依家": "現在",
            # 保留：嘅、唔、冇、啲、咁、睇、靚（呢啲係粵語核心特色）
            # === 常見 OCR/ASR 錯誤修正 ===
            "原費": "月費",
            "財源名單": "裁員名單",
            "財源": "裁員",
        }
        
        # === WRITTEN MODE: Full conversions ===
        post_fix_map_written = {
            # === 基本粵語→書面語轉換（最高優先級）===
            "係": "是",
            "喺": "在",
            "嘅": "的",
            "咗": "了",
            "冇": "沒有",
            "唔": "不",
            "佢": "他",
            "嚟": "來",
            "啲": "些",
            
            # === 雙字/多字詞優先 ===
            "呢個": "這個",
            "嗰個": "那個",
            "呢啲": "這些",
            "嗰啲": "那些",
            "呢度": "這裡",
            "嗰度": "那裡",
            "呢條": "這條",
            "嗰條": "那條",
            "呢張": "這張",
            "嗰張": "那張",
            "呢間": "這間",
            "嗰間": "那間",
            "呢次": "這次",
            "嗰次": "那次",
            "呢排": "最近",
            "唔係": "不是",
            "唔好": "不要",
            "唔會": "不會",
            "唔知": "不知道",
            "唔使": "不用",
            "唔該": "謝謝",
            "唔駛": "不用",
            "佢哋": "他們",
            "我哋": "我們",
            "你哋": "你們",
            "同埋": "而且",
            "加埋": "加上",
            "埋嚟": "過來",
            "返嚟": "回來",
            "過嚟": "過來",
            "出嚟": "出來",
            "入嚟": "進來",
            "上嚟": "上來",
            "落嚟": "下來",
            "即係": "就是",
            "即刻": "立刻",
            "邊一個": "哪一個",
            "咁樣": "這樣",
            "點解": "為什麼",
            "點樣": "怎樣",
            "乜嘢": "什麼",
            "幾時": "什麼時候",
            "邊度": "哪裡",
            "邊個": "哪個",
            "嗰陣": "那時",
            "呢陣": "現在",
            "頭先": "剛才",
            "琴日": "昨天",
            "聽日": "明天",
            "今日": "今天",
            "尋日": "昨天",
            "舊陣時": "以前",
            "而家": "現在",
            "依家": "現在",
            "之後": "後來",
            "跟住": "然後",
            "睇": "看",
            "靚": "漂亮",
            "咁": "這樣",
            "好彩": "幸運",
            "好耐": "很久",
            "好多": "很多",
            "幾多": "多少",
            "啱啱": "剛剛",
            "咪": "不要",
            "試下": "試試",
            "諗下": "想想",
            "睇下": "看看",
            "行路": "走路",
            "食飯": "吃飯",
            "食嘢": "吃東西",
            "飲嘢": "喝東西",
            "瞓覺": "睡覺",
            "著衫": "穿衣",
            "除衫": "脫衣",
            "搵": "找",
            "畀": "給",
            "揾": "找",
            "攞": "拿",
            "執": "收拾",
            "搞掂": "完成",
            "搞定": "完成",
            "得閒": "有空",
            "冇問題": "沒問題",
            
            # === 常見 OCR/ASR 錯誤修正 ===
            "原費": "月費",
            "財源名單": "裁員名單",
            "財源": "裁員",
            "視顧": "覺得",
            "告運作": "就運作",
            "績優": "很多",
        }
        
        # Choose dictionary based on style
        # 書面語：完全轉換 (99+ rules) → 使用 post_fix_map_written
        # 半書面語：保留口語 (14 rules) → 使用 post_fix_map_semi
        if style == 'semi':
            post_fix_map = post_fix_map_semi
            logger.info(f"🎨 [STYLE] Using SEMI post_fix_map ({len(post_fix_map)} rules) - keeping oral words")
        else:  # written
            post_fix_map = post_fix_map_written
            logger.info(f"🎨 [STYLE] Using WRITTEN post_fix_map ({len(post_fix_map)} rules) - full conversion")
        
        # Sort by key length (longest first) to avoid partial replacement issues
        sorted_keys = sorted(post_fix_map.keys(), key=len, reverse=True)

        # Apply dictionary ONLY to segments that exist in result
        # (Avoid re-adding deleted duplicate indices)
        for i in range(len(segments)):
            # Skip segments not in result (they were removed as duplicates or failed AI processing)
            if i not in result:
                continue

            text = result[i]

            # Apply dictionary replacements
            for canto in sorted_keys:
                written = post_fix_map[canto]
                if canto in text:
                    text = text.replace(canto, written)

            result[i] = text
        
        logger.info(f"Post-processed {len(result)} segments with dictionary cleanup")
        
        # ========================================
        # 【第一階段】語氣詞移除 + 擴充粵語詞轉換
        # ========================================
        
        # 語氣詞移除（句尾）
        particles_to_remove = ['呀', '啦', '喎', '囉', '㗎', '咩', '吓', '喇', '啫', '嘛']
        
        # 擴充粵語詞轉換（只在 written 模式）
        if style == 'written':
            additional_conversions = {
                # 量詞/助詞（需謹慎處理「個」因為「一個」「這個」已處理）
                "嘅海鮮": "的海鮮",
                "嘅味": "的味",
                "嘅時候": "的時候",
                "嘅地方": "的地方",
                "個海鮮": "的海鮮",  
                "個味": "的味",
                
                # 動詞
                "拎了": "拿了",
                "拎住": "拿著",
                "拎返": "拿回",
                "拎起": "拿起",
                "揾": "找",
                "揾到": "找到",
                "攞": "拿",
                "攞住": "拿著",
                "畀": "給",
                "畀錢": "給錢",
                
                # 名詞
                "屋企": "家",
                "老竇": "父親",
                "老母": "母親",
                
                # 副詞/連接詞
                "好似": "好像",
                "咁樣": "這樣",
                "咁多": "這麼多",
                "幾咁": "多麼",
                "就好似": "就好像",
                
                # 粵語「來的」移除（語態問題）
                "來的": "",
                "星期六來的": "星期六",
                "星期日來的": "星期日",
            }
            
            # 應用額外轉換（從長到短排序避免部分替換）
            sorted_additional = sorted(additional_conversions.keys(), key=len, reverse=True)
            for idx, text in result.items():
                for canto, written in [(k, additional_conversions[k]) for k in sorted_additional]:
                    if canto in text:
                        text = text.replace(canto, written)
                result[idx] = text
        
        # 移除句尾語氣詞
        for idx, text in result.items():
            original = text
            # 移除句尾語氣詞（可能有多個）
            while text and text[-1] in particles_to_remove:
                text = text[:-1].strip()
            
            # 移除句中的語氣詞（帶逗號的情況）
            for particle in particles_to_remove:
                text = text.replace(f"{particle}，", "，")
                text = text.replace(f"{particle},", ",")
            
            if text != original:
                logger.debug(f"Removed particles: '{original}' -> '{text}'")
                result[idx] = text
        
        logger.info("Phase 1 complete: Particle removal + Cantonese word expansion")
        
        # ========================================
        # 【第二階段】同音字修正 + 重複去除
        # ========================================
        
        # 常見同音字/語音識別錯誤修正
        homophone_fixes = {
            "天氣來了": "天亮了",
            "中途假期": "週末假期",
            "不要要": "是不是要",
            "後來沒有": "之後沒有",
            "後來會": "之後會",
            "後來都": "之後都",
            "後來可以": "之後可以",
            "精品店": "家具店",  # 語境：買桌子
            "吃飯台": "餐桌",
            "個位": "位置",  # 「收銀機的個位」-> 「收銀台的位置」
            "原費": "月費",
            "財源": "裁員",
            "財源名單": "裁員名單",
        }
        
        for idx, text in result.items():
            for wrong, correct in homophone_fixes.items():
                if wrong in text:
                    text = text.replace(wrong, correct)
                    logger.debug(f"Homophone fix: '{wrong}' -> '{correct}'")
            result[idx] = text
        
        # 重複語句檢測與去除
        # 檢測連續兩個 segment 的相似度
        segments_to_remove = set()
        prev_text = None
        prev_idx = None
        
        for idx in sorted(result.keys()):
            text = result[idx].strip()
            
            if prev_text and text:
                # 計算相似度（簡單字符串匹配）
                if text == prev_text:
                    # 完全重複，標記移除當前
                    segments_to_remove.add(idx)
                    logger.warning(f"Duplicate detected: segment {idx} == {prev_idx}")
                elif len(text) > 10 and len(prev_text) > 10:
                    # 長句子，檢查是否包含
                    if text in prev_text or prev_text in text:
                        # 一個包含另一個，保留較長的
                        if len(text) > len(prev_text):
                            segments_to_remove.add(prev_idx)
                            logger.warning(f"Duplicate detected: segment {prev_idx} contained in {idx}")
                        else:
                            segments_to_remove.add(idx)
                            logger.warning(f"Duplicate detected: segment {idx} contained in {prev_idx}")
            
            prev_text = text
            prev_idx = idx
        
        # 移除重複
        for idx in segments_to_remove:
            del result[idx]
        
        if segments_to_remove:
            logger.info(f"Phase 2 complete: Removed {len(segments_to_remove)} duplicate segments")
        else:
            logger.info("Phase 2 complete: No duplicates found")
        
        # ========================================
        # 【第三階段】語句完整性 + 特殊錯別字
        # ========================================
        
        # 檢測不完整語句（結尾為連接詞但無下文）
        incomplete_endings = [
            '並且如此', '同有', '和有', '並且有', '而且有',  # 從實際錯誤中發現
            '但同時', '而且', '以及', '還有', '然後', '接著',
            '並且', '同時', '因此', '所以', '但是',  # 常見連接詞
            '不過', '只是', '只不過'  # 轉折詞
        ]
        
        for idx, text in result.items():
            for ending in incomplete_endings:
                if text.endswith(ending):
                    # 移除不完整的結尾
                    text = text[:-len(ending)].strip()
                    logger.warning(f"Incomplete sentence: removed '{ending}' from segment {idx}")
                    result[idx] = text
        
        logger.info("Phase 3 complete: Incomplete sentence cleanup")

        # ========================================
        # 【第四階段】簡體字強制轉換（雙重防禦）
        # ========================================
        # 即使 Prompt 要求繁體，LLM 仍可能輸出簡體字
        # 使用 OpenCC 強制轉換所有簡體字為繁體

        if self.s2t_converter:
            simplified_detected_count = 0
            for idx, text in result.items():
                # 使用 OpenCC 強制轉換
                text_traditional = self.s2t_converter.convert(text)
                if text != text_traditional:
                    simplified_detected_count += 1
                    logger.warning(f"❌ Simplified Chinese detected in segment {idx}: '{text[:50]}'")
                    logger.info(f"✅ Auto-converted to Traditional: '{text_traditional[:50]}'")
                    result[idx] = text_traditional

            if simplified_detected_count > 0:
                logger.warning(f"⚠️ Total {simplified_detected_count} segments had simplified Chinese and were auto-fixed")
            else:
                logger.info("✅ No simplified Chinese detected")

        logger.info("Phase 4 complete: Simplified to Traditional Chinese conversion")

        # ⚠️ 【舊的簡體字檢測】保留作為備份
        if False and self.s2t_converter:
            # 常見簡體字列表（用於快速檢測）
            simplified_chars = '尽觉尝试验证讯号发现问题应该这个怎么样时间'
            detected_count = 0
            for idx, text in result.items():
                if any(char in text for char in simplified_chars):
                    detected_count += 1
                    logger.error(f"❌ CRITICAL: Simplified Chinese detected in segment {idx}: '{text[:50]}'")
                    # 強制再轉一次
                    result[idx] = self.s2t_converter.convert(text)
                    logger.info(f"✅ Auto-fixed to Traditional: '{result[idx][:50]}'")
            
            if detected_count > 0:
                logger.warning(f"⚠️ Total {detected_count} segments had simplified Chinese and were auto-fixed")
        
        return result

    def _convert_cantonese_dict(self, text: str, style: str) -> str:
        """Dictionary-based Cantonese conversion (no AI)."""
        if style == 'spoken':
            return text
        
        # 半書面語：只保留最核心嘅粵語字
        # 轉換：係、喺、佢、咗、嚟 等
        # 保留：嘅、唔、冇（呢啲係粵語嘅靈魂，包含呢啲字嘅詞組都要保留）
        # 保留但唔做字符匹配：啲、咁、睇、靚（單字保留，但詞組可轉換）
        keep_chars_semi = set('嘅唔冇')  # 字符級保留
        keep_words_semi = ['啲', '咁', '睇', '靚']  # 單字保留
        
        result = text
        sorted_keys = sorted(self.cantonese_map.keys(), key=len, reverse=True)
        
        for canto_word, written_word in [(k, self.cantonese_map[k]) for k in sorted_keys]:
            # 如果詞組包含核心字符（嘅、唔、冇），跳過轉換
            if style == 'semi' and any(c in keep_chars_semi for c in canto_word):
                continue
            # 如果係單字保留詞，跳過轉換
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
        
        # AI conversion with Qwen2.5-3B (better quality than 1.5B)
        if use_ai and style in ('semi', 'written'):
            try:
                if self.llm_processor is None:
                    # Check if model needs to be downloaded first
                    try:
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
                            logger.info("Initializing Qwen2.5-3B for AI style conversion...")
                            from models.qwen_llm import QwenLLM
                            self.llm_processor = QwenLLM(self.config, profile)
                            self.llm_processor.load_models()
                            logger.info("Qwen2.5-3B loaded successfully")
                    except Exception as load_error:
                        logger.warning(f"Failed to load model for AI conversion: {load_error}")
                        # Fall through to dictionary conversion
                
                # CRITICAL: Check llm_processor is ready before using
                if self.llm_processor is not None:
                    # Use specialized prompt for colloquial-to-written conversion
                    from prompts.cantonese_prompts import COLLOQUIAL_TO_WRITTEN_PROMPT
                    prompt = COLLOQUIAL_TO_WRITTEN_PROMPT.format(text=text)
                    
                    # Generate response directly using MLXQwenLLM's generate method
                    converted = self.llm_processor.generate(prompt, max_tokens=512, temperature=0.3)
                    
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
                else:
                    logger.warning("LLM processor not available, using dictionary fallback")
                    
            except Exception as e:
                logger.warning(f"AI conversion failed, falling back to dictionary: {e}")
        
        # Dictionary-based conversion (fallback or default)
        # 半書面語：只保留最核心嘅粵語字
        # 轉換：係、喺、佢、咗、嚟 等
        # 保留：嘅、唔、冇（呢啲係粵語嘅靈魂，包含呢啲字嘅詞組都要保留）
        # 保留但唔做字符匹配：啲、咁、睇、靚（單字保留，但詞組可轉換）
        keep_chars_semi = set('嘅唔冇')  # 字符級保留
        keep_words_semi = ['啲', '咁', '睇', '靚']  # 單字保留
        
        result = text
        conversions = []
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_keys = sorted(self.cantonese_map.keys(), key=len, reverse=True)
        
        for canto_word, written_word in [(k, self.cantonese_map[k]) for k in sorted_keys]:
            # 如果詞組包含核心字符（嘅、唔、冇），跳過轉換
            if style == 'semi' and any(c in keep_chars_semi for c in canto_word):
                continue
            # 如果係單字保留詞，跳過轉換
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
        
        # Build translation map first (avoid modifying while iterating)
        translations = {}  # {english_text: translation}
        
        for match in matches:
            english_text = match.group(0).strip()
            
            if not english_text or english_text in translations:
                continue
            
            cache_key = english_text.lower()
            
            # Check global cache first
            if cache_key in self.translation_cache:
                translations[english_text] = self.translation_cache[cache_key]
                logger.debug(f"Using cache: '{english_text}' -> '{translations[english_text]}'")
                continue
            
            translation = None
            
            # First, check dictionary for exact match
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
                    
                    # Validate AI result - check for repetition/corruption
                    if translation:
                        # If translation contains repeated original text, it's corrupted
                        if english_text.lower() in translation.lower() and translation != english_text:
                            # Extract just the new part
                            translation = translation.replace(english_text, '').strip()
                            if not translation:
                                translation = english_text
                                logger.warning(f"AI returned corrupted result, keeping: '{english_text}'")
                    
                    # If AI also fails, keep original
                    if not translation or translation == english_text:
                        translation = english_text
                        logger.warning(f"AI translation failed, keeping: '{english_text}'")
            
            translations[english_text] = translation
            self.translation_cache[cache_key] = translation
        
        # Now replace all occurrences
        result = text
        for english_text, translation in translations.items():
            if english_text != translation:
                result = result.replace(english_text, translation)
                logger.debug(f"Replaced: '{english_text}' -> '{translation}'")
        
        if result != text:
            logger.info(f"Final: '{text}' -> '{result}'")
        return result
        return result

    def _should_use_ai_translation(self, text: str) -> bool:
        """Check if we should use AI translation (e.g. sentence vs single word)."""
        # If text has more than 2 words, use AI
        return len(text.split()) > 2

    def _translate_with_ai(self, text: str) -> str:
        """
        Hybrid translation strategy: Dictionary → Qwen LLM → MarianMT.
        
        Args:
            text: English text to translate
            
        Returns:
            Translated Chinese text, or original if translation fails
        """
        # === LAYER 1: Dictionary (fastest, 100% accurate) ===
        dict_result = self._dictionary_translate(text)
        if dict_result != text:
            logger.info(f"[Dictionary] '{text}' -> '{dict_result}'")
            return dict_result
        
        
        # === LAYER 2: Qwen LLM (DISABLED - causes hallucination issues) ===
        # Disabled due to: hallucinations, repetitions, wrong translations
        # Example issues: "灵灵灵...", "迈克尔·迈克尔", "call off -> 关闭电话"
        # Now using Dictionary -> MarianMT directly for reliability
        
        # if self.llm_processor is not None and hasattr(self.llm_processor, 'model') and self.llm_processor.model is not None:
        #     try:
        #         ... (Qwen code commented out)
        #     except Exception as e:
        #         logger.warning(f"Qwen translation failed: {e}")
        
        
        # === LAYER 3: MarianMT (fallback) ===
        try:
            if not self.translation_model:
                logger.info("Initializing MarianMT Translation Model...")
                from models.translation_model import TranslationModel
                self.translation_model = TranslationModel(self.config)

            result = self.translation_model.translate(text)

            if result and result.strip() and result != text:
                # MarianMT outputs Simplified Chinese, convert to Traditional immediately
                if self.s2t_converter:
                    result = self.s2t_converter.convert(result)
                    logger.info(f"[MarianMT+S2T] '{text}' -> '{result}'")
                else:
                    logger.warning(f"[MarianMT] OpenCC not available, output may be Simplified: '{text}' -> '{result}'")

                # Cache for future use
                self.translation_cache[text.lower()] = result
                return result
            else:
                logger.warning(f"MarianMT returned empty or same, keeping original")
                return text

        except Exception as e:
            logger.error(f"MarianMT failed: {e}", exc_info=True)
            return text
    
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

    def _split_long_lines(self, segments: List[Dict], max_chars: int = 14) -> List[Dict]:
        """Split long lines into two segments.
        
        Args:
            segments: List of subtitle segments
            max_chars: Maximum characters per line (from user settings)
        """
        new_segments = []
        
        logger.info(f"[SplitLong] Splitting lines with max_chars={max_chars}")
        
        for seg in segments:
            text = seg['text']
            if len(text) > max_chars:
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
