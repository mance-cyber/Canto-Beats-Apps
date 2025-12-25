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

    def _batch_ai_convert(self, segments: List[Dict], style: str, progress_callback=None) -> Dict[int, str]:
        """
        Batch convert segments using AI.
        Priority: MLX Qwen (Apple Silicon) > Transformers Qwen (fallback)
        Returns dict of {index: converted_text}.
        """
        result = {}
        batch_size = 5
        
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
                        # Show download confirmation dialog
                        from PySide6.QtWidgets import QMessageBox, QApplication
                        from ui.download_dialog import ModelDownloadDialog
                        
                        # Get parent window
                        parent = None
                        app = QApplication.instance()
                        if app:
                            for widget in app.topLevelWidgets():
                                if widget.isVisible():
                                    parent = widget
                                    break
                        
                        # Show confirmation
                        msg = QMessageBox(parent)
                        msg.setWindowTitle("下載 AI 書面語工具")
                        msg.setIcon(QMessageBox.Information)
                        msg.setText("需要下載 AI 書面語工具")
                        msg.setInformativeText(
                            "首次使用書面語功能需要下載 AI 模型 (約 6 GB)。\n"
                            "下載時間視網絡速度而定 (約 2-5 分鐘)。\n\n"
                            "是否繼續？"
                        )
                        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        msg.setDefaultButton(QMessageBox.Yes)
                        
                        if msg.exec() != QMessageBox.Yes:
                            logger.info("User cancelled Qwen download")
                            return result
                        
                        # Show download progress dialog
                        logger.info(f"Downloading MLX Qwen model: {model_id}")
                        download_dialog = ModelDownloadDialog(model_id, parent=parent)
                        download_dialog.setWindowTitle("下載 AI 書面語工具")
                        
                        # Create worker for MLX Qwen download
                        from ui.download_dialog import MLXWhisperDownloadWorker
                        
                        class MLXQwenDownloadWorker(MLXWhisperDownloadWorker):
                            def run(self):
                                try:
                                    from huggingface_hub import snapshot_download, list_repo_files
                                    from tqdm import tqdm
                                    
                                    self.progress.emit(5, "正在連接伺服器...")
                                    
                                    # Get list of files to download for better progress tracking
                                    try:
                                        all_files = list(list_repo_files(model_id))
                                        total_files = len(all_files)
                                    except Exception:
                                        total_files = 10  # Estimated fallback
                                    
                                    # Track current file being downloaded
                                    file_counter = {'current': 0, 'name': ''}
                                    
                                    class ProgressTqdm(tqdm):
                                        def __init__(self_tqdm, *args, **kwargs):
                                            super().__init__(*args, **kwargs)
                                            self_tqdm.worker = self
                                            # Extract filename from desc if available
                                            if hasattr(self_tqdm, 'desc') and self_tqdm.desc:
                                                file_counter['name'] = self_tqdm.desc
                                            file_counter['current'] += 1
                                        
                                        def update(self_tqdm, n=1):
                                            super().update(n)
                                            if self_tqdm.total and self_tqdm.total > 0:
                                                file_num = file_counter['current']
                                                # Calculate overall progress based on file count
                                                base_percent = int((file_num - 1) / total_files * 85) + 5
                                                file_percent = int((self_tqdm.n / self_tqdm.total) * (85 / total_files))
                                                percent = min(base_percent + file_percent, 95)
                                                
                                                downloaded_mb = self_tqdm.n / (1024 * 1024)
                                                total_mb = self_tqdm.total / (1024 * 1024)
                                                msg = f"文件 {file_num}/{total_files}: {downloaded_mb:.0f}MB / {total_mb:.0f}MB"
                                                self_tqdm.worker.progress.emit(percent, msg)
                                    
                                    snapshot_download(repo_id=model_id, tqdm_class=ProgressTqdm)
                                    
                                    self.progress.emit(100, "下載完成")
                                    self.finished.emit(True, "下載成功")
                                    
                                except Exception as e:
                                    logger.error(f"MLX Qwen download failed: {e}")
                                    self.finished.emit(False, f"下載失敗: {str(e)}")
                        
                        download_dialog.worker = MLXQwenDownloadWorker("bf16")
                        download_dialog.worker.progress.connect(download_dialog._on_progress)
                        download_dialog.worker.finished.connect(download_dialog._on_finished)
                        download_dialog.worker.start()
                        
                        result_dialog = download_dialog.exec()
                        
                        if not download_dialog.was_successful():
                            logger.warning("MLX Qwen download failed or cancelled")
                            return result
                        
                        logger.info("✅ MLX Qwen download completed")
                    
                    # Now load the model with robust error handling
                    try:
                        self.llm_processor = MLXQwenLLM(model_id=model_id)
                        self.llm_processor.load_model()
                        self._using_mlx = True
                        logger.info(f"⚡ {hw_config['description']} loaded")
                    except Exception as load_error:
                        logger.error(f"Failed to load MLX Qwen model: {load_error}", exc_info=True)
                        
                        # Show user-friendly error message
                        from PySide6.QtWidgets import QMessageBox, QApplication
                        parent = None
                        app = QApplication.instance()
                        if app:
                            for widget in app.topLevelWidgets():
                                if widget.isVisible():
                                    parent = widget
                                    break
                        
                        msg = QMessageBox(parent)
                        msg.setWindowTitle("AI 工具載入失敗")
                        msg.setIcon(QMessageBox.Warning)
                        msg.setText("書面語 AI 工具無法載入")
                        msg.setInformativeText(
                            f"錯誤：{str(load_error)[:100]}\n\n"
                            "將使用字典模式進行轉換（速度較快但準確度較低）。\n\n"
                            "如需完整 AI 功能，請重啟應用或聯繫技術支援。"
                        )
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec()
                        
                        # Fall back to dictionary mode
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
        
        # Process in batches
        total_batches = (len(segments) + batch_size - 1) // batch_size
        
        for batch_idx, batch_start in enumerate(range(0, len(segments), batch_size)):
            batch_end = min(batch_start + batch_size, len(segments))
            batch_texts = [segments[i].get('text', '') for i in range(batch_start, batch_end)]
            
            # Report progress
            if progress_callback:
                progress_callback(batch_idx, total_batches, f"AI 轉換 {batch_idx + 1}/{total_batches}...")
            
            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])

            # Professional prompt for thorough conversion (simplified - no English/number rules)
            prompt = f"""你是一位專業中文編輯與字幕轉寫師。你的任務是把「粵語口語字幕」徹底轉譯成「自然流暢的書面中文」。

【核心目標】
- 完全書面化：把口語、粵語語氣詞、口頭禪、潮語改成正式書面表達。
- 不改意思：保留原句資訊、語氣強弱，但用書面語呈現。
- 適合做字幕：句子要簡潔、易讀、自然。
- **英文必須保留**：所有英文單詞、品牌、人名、術語等，絕對不要翻譯成中文。

【轉譯規則】
1. 移除/改寫粵語語氣詞與填充詞：如「喎、啦、囉、咩、㗎、吓、呀、喇、啫」等。
2. 粗口處理：改成較文明的同等語氣（例如「好撚煩」→「非常煩人」）。
3. 句末標點要書面：疑問用「？」、感嘆用「！」，其餘用「。」或「，」。
4. 不要添加新資訊、不要解釋、不要評論。
5. 只輸出轉譯後文字，保持編號格式。
6. 保守轉換：如果唔確定，保留原詞，唔好猜測或創造新詞。
7. **英文必須保留**：所有英文單詞、人名、品牌、術語、數字等，一律保持原樣，絕對不要翻譯成中文。

【常見轉換】
係→是、喺→在、唔→不、冇→沒有、嘅→的、咗→了、嚟→來、佢→他/她
好彩→幸運、頭先→剛才、琴日→昨天、聽日→明天、今日→今天、而家→現在
個鐘→小時、蚊→元、即係→就是、點解→為什麼、乜嘢→什麼、邊度→哪裡

【重要】英文保留範例：
- "Apple" 保持 "Apple"，不要變成「蘋果」
- "iPhone" 保持 "iPhone"，不要變成「愛瘋」
- "CEO" 保持 "CEO"，不要變成「執行長」
- "AI" 保持 "AI"，不要變成「人工智能」

【風格】繁體中文書面語，清晰自然。嚴格度：最高，凡是口語化表達一律改成書面語。

【輸入】
{combined}

【輸出】（只輸出結果，保持編號）"""
            
            try:
                # Generate response - use correct method based on backend
                if getattr(self, '_using_mlx', False):
                    response = self.llm_processor.generate(
                        prompt,
                        max_tokens=1024,
                        temperature=0
                    )
                else:
                    response = self.llm_processor._generate(
                        prompt, 
                        self.llm_processor._model_a, 
                        self.llm_processor._tokenizer_a,
                        max_new_tokens=1024,
                        temperature=0  # Zero temp for fully deterministic output
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
                                # 1. 如果有箭頭符號，只取箭頭後面嘅內容
                                if '→' in text:
                                    text = text.split('→')[-1].strip()
                                if '->' in text:
                                    text = text.split('->')[-1].strip()
                                
                                # 2. 移除所有類型括號
                                for bracket in '()（）﹙﹚[]【】「」':
                                    text = text.replace(bracket, '')
                                
                                # 3. 清除異常尾部字符
                                while text and text[-1] in ')）」】是呢啦':
                                    text = text[:-1].strip()
                                
                                # 4. 去除多餘空白
                                text = ' '.join(text.split())
                                
                                if 0 <= num < len(batch_texts) and text:
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                logger.info(f"Batch {batch_idx + 1}: processed {len(batch_texts)} segments")
                
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}")
        
        # Report completion
        if progress_callback:
            progress_callback(total_batches, total_batches, "AI 轉換完成！")
        
        # Post-process with dictionary to fix AI missed conversions
        post_fix_map = {
            # === 基本粵語→書面語轉換 ===
            "蚊": "元",
            "個鐘": "小時",
            "即係": "就是",
            "喺": "在",
            "嘅": "的",
            "咗": "了",
            "冇": "沒有",
            "唔": "不",
            "係": "是",
            "佢": "他",
            "嚟": "來",
            "搵": "找",
            "好彩": "幸運",
            "頭先": "剛才",
            "琴日": "昨天",
            "聽日": "明天",
            "今日": "今天",
            "而家": "現在",
            "點解": "為什麼",
            "乜嘢": "什麼",
            "邊度": "哪裡",
            "呢啲": "這些",
            "唔係": "不是",
            "加埋": "加上",
            "啲": "一些",
            
            # === AI 錯誤轉換修正 ===
            # AI 可能會產生錯誤嘅諧音字
            "脫了": "除了",      # 除了被錯誤轉成脫了
            "便宜時": "平時",    # 平時被錯誤轉成便宜時
            "逢係": "凡是",      # 凡是被錯誤轉成逢係
            "逢是": "凡是",      # 凡是被錯誤轉成逢是
            # 注意: "個個" 係有效書面語 (意思係「每一個」)，唔應該替換
            # 注意: "啲" 會被上面嘅 "啲": "一些" 處理
            
            # === 常見 OCR/ASR 錯誤修正 ===
            "視顧": "覺得",
            "告運作": "就運作",
            "嘗": "是",          # 修正：之前錯誤地寫成 "係"
            "績優": "很多",
        }
        
        for idx in result:
            text = result[idx]
            for canto, written in post_fix_map.items():
                if canto in text:
                    text = text.replace(canto, written)
            result[idx] = text
        
        logger.info(f"Post-processed {len(result)} segments with dictionary cleanup")
        
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
                else:
                    logger.warning("LLM processor not available, using dictionary fallback")
                    
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
        
        # === LAYER 2: Qwen LLM (smart, context-aware) ===
        # Only use if already loaded (from Cantonese correction stage)
        if self.llm_processor is not None and self.llm_processor._model_a is not None:
            try:
                prompt = f"""將以下英文翻譯成繁體中文。只輸出翻譯結果，不要解釋。

英文：{text}
繁體中文："""
                
                result = self.llm_processor._generate(
                    prompt,
                    self.llm_processor._model_a,
                    self.llm_processor._tokenizer_a,
                    max_new_tokens=128,
                    temperature=0  # Deterministic output
                )
                
                # Clean up result
                if result:
                    result = result.strip()
                    # Remove common prefixes
                    for prefix in ['繁體中文：', '翻譯：', '結果：']:
                        if result.startswith(prefix):
                            result = result[len(prefix):].strip()

                    if result and result != text:
                        # Ensure Traditional Chinese output (in case LLM outputs Simplified)
                        if self.s2t_converter:
                            result = self.s2t_converter.convert(result)

                        logger.info(f"[Qwen LLM] '{text}' -> '{result}'")
                        # Cache for future use
                        self.translation_cache[text.lower()] = result
                        return result
                        
            except Exception as e:
                logger.warning(f"Qwen translation failed: {e}")
        
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
