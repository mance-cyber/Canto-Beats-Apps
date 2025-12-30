"""
Subtitle Pipeline V2 - AI-powered transcription with context-aware conversion.

Uses Whisper for ASR + Qwen2 LLM for intelligent colloquial-to-written conversion.
"""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass

from core.config import Config
from core.hardware_detector import HardwareDetector, PerformanceProfile
from models.whisper_asr import WhisperASR
# QwenLLM removed - 書面語 conversion handled by StyleControlPanel
from models.vad_processor import VADProcessor
from utils.logger import setup_logger

# Try to import MLX Whisper for Apple Silicon acceleration
try:
    from utils.whisper_mlx import MLXWhisperASR, get_best_whisper_backend
    HAS_MLX_WHISPER = MLXWhisperASR.is_available()
except ImportError:
    HAS_MLX_WHISPER = False

# 高級轉錄模組（可選）
try:
    from utils.audio_enhancer import AudioEnhancer
    from utils.advanced_transcription import AdvancedTranscriber
    from utils.vocabulary_learner import get_vocabulary_learner, auto_correct_text
    HAS_ADVANCED_FEATURES = True
except ImportError:
    HAS_ADVANCED_FEATURES = False

logger = setup_logger()


@dataclass
class SubtitleEntryV2:
    """A single subtitle entry with dual-language support."""
    start: float
    end: float
    colloquial: str  # 口語 - spoken Cantonese
    formal: Optional[str] = None  # 書面語 - written Chinese


class SubtitlePipelineV2:
    """
    V2 pipeline with AI-powered colloquial-to-written conversion.
    
    Pipeline stages:
    1. Hardware detection
    2. Model loading (Whisper ASR + optional Qwen LLM)
    3. Audio extraction (if video)
    4. Whisper transcription (native segmentation)
    5. Optional LLM refinement (context-aware conversion)
    """
    
    def __init__(self, config: Config, force_cpu: bool = False, enable_llm: bool = False):
        """
        Initialize pipeline.
        
        Args:
            config: Application configuration
            force_cpu: Force CPU mode
            enable_llm: Deprecated, kept for API compatibility (always False)
        """
        self.config = config
        self.force_cpu = force_cpu
        self.enable_llm = False  # LLM is handled by StyleControlPanel, not here
        self.profile = None
        self.asr = None
        self.vad = None  # VAD processor for smart segmentation
        self._models_loaded = False
        
        # Create temp directory
        self.temp_dir = Path(tempfile.gettempdir()) / "canto_beats_v2"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize hardware detection
        self._setup_hardware()
    
    def _setup_hardware(self):
        """Detect hardware and determine optimal configuration."""
        logger.info("Detecting hardware configuration...")
        detector = HardwareDetector()
        self.profile = detector.detect(force_cpu=self.force_cpu)
        
        logger.info(f"Hardware tier: {self.profile.tier.value}")
        logger.info(f"Device: {self.profile.device}")
        logger.info(f"VRAM: {self.profile.vram_gb} GB")
        logger.info(f"LLM refinement: {'enabled' if self.enable_llm else 'disabled'}")
    
    def _load_asr(self, progress_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None):
        """Load ASR model with Apple Silicon priority: CoreML > MPS > CPU.
        
        Args:
            progress_callback: Callback for progress percentage (0-100)
            status_callback: Callback for status message updates (e.g., "正在下載模型...")
        """
        if self.asr is not None and self.asr.is_loaded:
            return

        if progress_callback:
            progress_callback(10)

        # Priority: MLX Whisper (CoreML/MPS) > faster-whisper (CPU)
        if HAS_MLX_WHISPER:
            logger.info(f"🍎 Loading MLX Whisper (Apple Silicon optimized): {self.profile.asr_model}")
            try:
                if status_callback:
                    status_callback("正在準備 AI 工具...")
                
                self.asr = MLXWhisperASR(model_size=self.profile.asr_model)
                
                # Pass status callback to load_model for download progress
                self.asr.load_model(progress_callback=status_callback)
                
                logger.info(f"⚡ MLX Whisper loaded on {self.asr.get_backend_type().upper()}")
                
                if status_callback:
                    status_callback("AI 工具加載完成！")
                return
            except Exception as e:
                logger.warning(f"MLX Whisper failed, falling back to faster-whisper: {e}")
                if status_callback:
                    status_callback("正在切換 AI 工具...")

        # Fallback: faster-whisper (CPU)
        logger.info(f"Loading faster-whisper ASR model: {self.profile.asr_model}")
        if status_callback:
            status_callback("正在加載 AI 工具...")
        self.asr = WhisperASR(self.config, model_size=self.profile.asr_model)
        self.asr.load_model()
        logger.info("ASR model loaded successfully (CPU mode)")
    
    def _unload_asr(self):
        """Unload ASR model to free GPU memory for LLM."""
        import gc
        import torch
        
        if self.asr:
            logger.info("Unloading ASR model to free GPU memory...")
            try:
                self.asr.unload_model()
            except Exception as e:
                logger.warning(f"ASR unload error: {e}")
            self.asr = None
            
            # Force garbage collection and clear GPU cache
            gc.collect()
            # Cross-platform GPU memory cleanup
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            logger.info("ASR unloaded, GPU memory freed")
    
    # _load_llm removed - 書面語 conversion is handled by StyleControlPanel

    
    def _extract_audio(self, video_path: Path) -> str:
        """Extract audio from video file."""
        import numpy as np
        
        audio_path = self.temp_dir / f"{video_path.stem}_audio.wav"
        
        logger.info(f"Extracting audio from video: {video_path}")
        
        try:
            # Use PyAV for audio extraction (includes FFmpeg libraries internally)
            import av
            import soundfile as sf
            
            container = av.open(str(video_path))
            
            # Get audio stream
            if not container.streams.audio:
                raise RuntimeError("影片中沒有找到音頻軌道")
            
            audio_stream = container.streams.audio[0]
            logger.info(f"Audio stream: {audio_stream.rate}Hz, {audio_stream.channels} channels")
            
            # Extract and decode audio frames
            audio_frames = []
            for frame in container.decode(audio_stream):
                # Convert frame to numpy array
                audio_frames.append(frame.to_ndarray())
            
            container.close()
            
            if not audio_frames:
                raise RuntimeError("無法從影片提取音頻幀")
            
            # Concatenate all frames
            audio_data = np.concatenate(audio_frames, axis=1)
            
            # Resample to 16kHz if needed
            target_sr = 16000
            if audio_stream.rate != target_sr:
                try:
                    import scipy.signal
                    num_samples = int(len(audio_data[0]) * target_sr / audio_stream.rate)
                    audio_data = scipy.signal.resample(audio_data, num_samples, axis=1)
                    sample_rate = target_sr
                    logger.info(f"Resampled from {audio_stream.rate}Hz to {target_sr}Hz")
                except ImportError:
                    # Fallback: use original sample rate if scipy not available
                    sample_rate = audio_stream.rate
                    logger.warning("scipy not available, using original sample rate")
            else:
                sample_rate = audio_stream.rate
            
            # Convert to mono if stereo
            if audio_data.shape[0] > 1:
                audio_data = np.mean(audio_data, axis=0)
            else:
                audio_data = audio_data[0]
            
            # Save as WAV
            sf.write(str(audio_path), audio_data, sample_rate, subtype='PCM_16')
            
            logger.info(f"Audio extracted to: {audio_path}")
            return str(audio_path)
            
        except ImportError as e:
            logger.error(f"Required library not available: {e}")
            raise RuntimeError(f"音頻處理庫未找到: {e}")
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise RuntimeError(f"音頻提取失敗: {e}")
    
    # ==================== 粵語錯字清單 (擴展版) ====================
    # Whisper 常見粵語轉錄錯誤 → 正確寫法
    CANTONESE_CORRECTIONS = {
        # ===== 常見字符錯誤 =====
        "既": "嘅",      # 的 (possessive)
        "系": "係",      # 是 (to be)
        "距": "佢",      # 他/她 (he/she)
        "尼": "呢",      # 這 (this)
        "黎": "嚟",      # 來 (come)
        "畀": "俾",      # 給 (give)
        "野": "嘢",      # 東西 (thing)
        "嚟": "來",      # 有時 Whisper 會反向錯
        "吾": "唔",      # 不
        "边": "邊",      # 哪裡
        "噉": "咁",      # 這樣
        "嗰": "個",      # 那個 (sometimes reversed)
        "D": "啲",       # 些
        "d": "啲",
        "仲": "重",      # still (有時會反向)
        "嘛": "吖嘛",    # 語氣詞
        
        # ===== 同音字/諧音錯誤 =====
        "緊係": "梗係",   # 當然 (of course)
        "梗系": "梗係",
        "点解": "點解",   # 為什麼
        "点样": "點樣",   # 怎樣
        "点算": "點算",   # 怎麼辦
        "咩事": "乜事",   # 什麼事
        "乜野": "乜嘢",   # 什麼東西
        "系咪": "係咪",   # 是不是
        "系唔系": "係唔係",
        "唔系": "唔係",   # 不是
        "有無": "有冇",   # 有沒有
        "有没": "有冇",
        "冇無": "冇",
        "有D": "有啲",
        
        # ===== 成語同音字校正 (重要!) =====
        "克苦來路": "刻苦耐勞",
        "刻苦來勞": "刻苦耐勞",
        "克苦耐勞": "刻苦耐勞",
        "一視同人": "一視同仁",
        "專心至志": "專心致志",
        "事倍公半": "事倍功半",
        "事半公倍": "事半功倍",
        "心曠神宜": "心曠神怡",
        "無微不至": "無微不至",
        "迫不得已": "迫不得已",
        "堅持不懈": "堅持不懈",
        "力不從心": "力不從心",
        "莫名奇妙": "莫名其妙",
        "一鳴驚人": "一鳴驚人",
        "自作自受": "自作自受",
        "不知所謂": "不知所謂",
        "親力親維": "親力親為",
        "親力親為": "親力親為",
        
        # ===== 粵語俗語 =====
        "甩底": "甩底",   # 爽約 (保持原樣)
        "收皮": "收皮",   # 閉嘴 (保持原樣)
        "屈機": "屈機",   # 作弊 (保持原樣)
        "好Kam": "好kam", # 尷尬
        "好kam": "好尷尬",
        "chur": "chur",   # 辛苦 (保留英文)
        "Chur": "chur",
        
        # ===== 簡體字 → 繁體字 =====
        "这": "呢",
        "个": "個",
        "说": "講",
        "话": "話",
        "时": "時",
        "间": "間",
        "来": "嚟",
        "会": "會",
        "没": "冇",
        "对": "對",
        "于": "於",
        "为": "為",
        "问": "問",
        "题": "題",
        "东": "東",
        "儿": "兒",
        "们": "哋",
        "让": "俾",
        "给": "畀",
        "这个": "呢個",
        "那个": "嗰個",
        "什么": "乜嘢",
        "怎么": "點樣",
        "为什么": "點解",
        "现在": "而家",
        "知道": "知道",
        "可以": "可以",
        "需要": "需要",
        "应该": "應該",
        "还是": "定係",
        "或者": "或者",
        "因为": "因為",
        "所以": "所以",
        "但是": "但係",
        "虽然": "雖然",
        "如果": "如果",
        "当然": "梗係",
        
        # ===== 數字相關 =====
        "两": "兩",
        "万": "萬",
        "亿": "億",
        
        # ===== 英文相關 =====
        "o k": "OK",
        "o K": "OK",
        "O K": "OK",
        "O k": "OK",
        "bye bye": "bye bye",
        "thank you": "thank you",
        
        # ===== 粵語同音字校正 (Whisper 常見錯誤) =====
        "執粒": "執笠",       # 執笠 = 結業
        "執左粒": "執左笠",
        "執咗粒": "執咗笠",
        "抽薪": "抽身",       # 抽身 (金蟬脫殼)
        "多日倍": "多一倍",   # 多一倍
        "多日賠": "多一倍",   # 多一倍 (另一變體)
        "係統": "系統",       # 系統
        "專位": "專為",       # 專為
        "化巧": "花巧",       # 花巧
        "冇巨大": "冒巨大",   # 冒巨大風險
        "冇風險": "冒風險",   # 冒風險
        "遊意": "猶豫",       # 猶豫
        
        # New User Reported (2025-12-20)
        "有冤無老訴": "有冤無路訴",
        "凌射": "零舍",
        "心希感受": "身同感受",
        "心痛感受": "身同感受",
        "物外": "默哀",
        "Porn": "Point",
        "porn": "point",
        "Grip": "Group",
        "grip": "group",
        
        # ===== User Reported Errors (2025-12-28) =====
        "菜數": "彩數",       # 彩數
        "曬光": "採光",       # 採光
        "睡唔得": "恨不得",   # 恨不得
        "喇不喇": "䁽一䁽",   # 䁽一䁽 (看一看)
        "怕氣": "客氣",       # 客氣
        "紫上": "市場",       # 市場
        "潛移食": "潛意識",   # 潛意識
        "經過老國": "經過路過", # 經過路過
        "怪嘢": "貴嘢",       # 貴嘢 (貴東西)
        
        # ===== 英文字中 d 被識別為 啲 的修正 =====
        "IPA啲": "iPad",
        "en啲ing": "ending",
        "pro啲uct": "product",
        "pro啲ucts": "products",
        "goo啲": "good",
        "nee啲": "need",
        "rea啲y": "ready",
        "bo啲y": "body",
        "to啲ay": "today",
        "alrea啲y": "already",
        "frien啲": "friend",
        "frien啲s": "friends",
        "hol啲": "hold",
        "buil啲": "build",
        "fiel啲": "field",
        "wor啲": "word",
        "worl啲": "world",
        "bran啲": "brand",
        "stan啲": "stand",
        "han啲": "hand",
        "han啲s": "hands",
        "min啲": "mind",
        "fin啲": "find",
        "kin啲": "kind",
        "soun啲": "sound",
        "atten啲": "attend",
        "deman啲": "demand",
        "expan啲": "expand",
        "depen啲": "depend",
        "respon啲": "respond",
        "recommen啲": "recommend",
        "understan啲": "understand",
        "backgroun啲": "background",
        "groun啲": "ground",
        
        # ===== 標點符號清理 =====
        "﹚": "",         # 移除多餘括號
        "﹙": "",
        "（": "",
        "）": "",
        "(": "",
        ")": "",
    }
    
    # 需要 LLM 校正嘅觸發字符（快速查找）
    TRIGGER_CHARS = set("既系距尼黎俾这个说话时间来会没对于为问题东儿们让给")

    # 粵語句尾語氣詞（用於後處理）
    # 當呢啲字出現喺句首，通常係 VAD 斷句錯誤，應該移到上一句句尾
    SENTENCE_FINAL_PARTICLES = {
        '嗎', '呀', '啦', '喎', '囉', '咩', '嘅', '啊', '呢', '喇',
        '㗎', '咋', '啩', '嘛', '咯', '噃', '咧', '喏', '嚟', '㖭',
        '唄', '嘎', '吖', '哇', '喔', '哦', '耶', '嘢'
    }

    # _needs_llm_correction removed - LLM is handled by StyleControlPanel
    
    def _apply_simple_corrections(self, text: str) -> str:
        """應用簡單字符替換（無需 LLM）。"""
        result = text
        # 刪除多餘嘅括號（所有類型）
        result = result.replace(")", "").replace("(", "")
        result = result.replace("）", "").replace("（", "")
        result = result.replace("﹚", "").replace("﹙", "")  # 特殊全角括號
        result = result.replace("」", "").replace("「", "")  # 引號
        result = result.replace("】", "").replace("【", "")  # 方括號
        # 應用錯字校正
        for error, correction in self.CANTONESE_CORRECTIONS.items():
            result = result.replace(error, correction)
        return result

    def _fix_particle_punctuation(self, text: str) -> str:
        """
        Fix punctuation appearing before sentence-final particles.
        
        Transforms: "嘅話,呢" → "嘅話呢,"
                    "咁樣，啦" → "咁樣啦，"
        
        Does NOT transform: "嘅話,呢個" → keeps as-is (呢個 is a word)
        
        Args:
            text: Input text
        
        Returns:
            Corrected text
        """
        result = text
        
        # Define punctuation that can appear after particles
        movable_punctuation = ['，', ',', '。', '.', '！', '!', '？', '?']
        
        # Common word patterns that should NOT be treated as particles
        # 呢個, 呢啲, 嗰個, 嗰啲, etc.
        demonstrative_words = {
            '呢個', '呢啲', '呢度', '呢邊', '呢次', '呢樣', '呢陣',
            '嗰個', '嗰啲', '嗰度', '嗰邊', '嗰次', '嗰樣', '嗰陣',
        }
        
        # For each punctuation
        for punct in movable_punctuation:
            # For each particle
            for particle in self.SENTENCE_FINAL_PARTICLES:
                # Pattern: [punct][particle]
                wrong_pattern = f"{punct}{particle}"
                
                # Find all occurrences
                index = 0
                while True:
                    index = result.find(wrong_pattern, index)
                    if index == -1:
                        break
                    
                    # Check what comes after the particle
                    char_after_index = index + len(wrong_pattern)
                    
                    # If at end of string, it's a true particle
                    if char_after_index >= len(result):
                        result = result[:index] + f"{particle}{punct}" + result[char_after_index:]
                        index += len(f"{particle}{punct}")
                        continue
                    
                    char_after = result[char_after_index]
                    
                    # Check if this forms a demonstrative word
                    is_word = False
                    for word in demonstrative_words:
                        if result[index + len(punct):].startswith(word):
                            is_word = True
                            break
                    
                    if is_word:
                        # Skip this occurrence (it's part of a word like 呢個)
                        index += len(wrong_pattern)
                        continue
                    
                    # If followed by punctuation, whitespace, or end of string, it's a true particle
                    if char_after in movable_punctuation or char_after.isspace():
                        # Move punctuation after particle
                        result = result[:index] + f"{particle}{punct}" + result[char_after_index:]
                        index += len(f"{particle}{punct}")
                    else:
                        # Followed by another character, might be part of a word
                        # Be conservative and skip
                        index += len(wrong_pattern)
        
        return result

    def _fix_sentence_final_particles(
        self,
        subtitles: List[SubtitleEntryV2]
    ) -> List[SubtitleEntryV2]:
        """
        修正句首語氣詞問題。

        VAD 有時會將句尾語氣詞（如「嗎」「呀」「啦」）切分到下一句開頭，
        例如「嗎茶葉蛋的味道呀」應該係「茶葉蛋的味道呀」，而「嗎」應該喺上一句。

        修正邏輯：
        1. 檢測句首是否有語氣詞
        2. 如果有，將語氣詞移到上一句句尾
        3. 調整時間戳以反映變化

        Args:
            subtitles: 字幕列表

        Returns:
            修正後的字幕列表
        """
        if len(subtitles) < 2:
            return subtitles

        fixed_subtitles = []
        fixed_count = 0

        for i, sub in enumerate(subtitles):
            text = sub.colloquial.strip()

            # 檢查是否以語氣詞開頭
            if text and text[0] in self.SENTENCE_FINAL_PARTICLES:
                # 找出連續的語氣詞（可能有多個，如「呀啦」）
                particle_end = 0
                for j, char in enumerate(text):
                    if char in self.SENTENCE_FINAL_PARTICLES:
                        particle_end = j + 1
                    else:
                        break

                particles = text[:particle_end]
                remaining_text = text[particle_end:].strip()

                # 只有當有上一句且剩餘文字不為空時才修正
                if fixed_subtitles and remaining_text:
                    # 將語氣詞移到上一句句尾
                    prev_sub = fixed_subtitles[-1]
                    prev_text = prev_sub.colloquial.strip()

                    # 更新上一句（加入語氣詞）
                    fixed_subtitles[-1] = SubtitleEntryV2(
                        start=prev_sub.start,
                        end=prev_sub.end,  # 保持原時間
                        colloquial=prev_text + particles,
                        formal=prev_sub.formal
                    )

                    # 更新當前句（移除語氣詞）
                    fixed_subtitles.append(SubtitleEntryV2(
                        start=sub.start,
                        end=sub.end,
                        colloquial=remaining_text,
                        formal=sub.formal
                    ))

                    fixed_count += 1
                    logger.info(f"[語氣詞修正] 移動 '{particles}' 從句 {i+1} 到句 {i}: "
                               f"'{prev_text}' → '{prev_text}{particles}'")
                elif not remaining_text:
                    # 如果移除語氣詞後沒有剩餘文字，整句都是語氣詞
                    if fixed_subtitles:
                        # 直接加到上一句
                        prev_sub = fixed_subtitles[-1]
                        prev_text = prev_sub.colloquial.strip()
                        fixed_subtitles[-1] = SubtitleEntryV2(
                            start=prev_sub.start,
                            end=sub.end,  # 延長時間到當前句結束
                            colloquial=prev_text + particles,
                            formal=prev_sub.formal
                        )
                        fixed_count += 1
                        logger.info(f"[語氣詞修正] 合併純語氣詞句 '{particles}' 到上一句")
                    else:
                        # 第一句就是純語氣詞，保持原樣
                        fixed_subtitles.append(sub)
                else:
                    # 沒有上一句，保持原樣
                    fixed_subtitles.append(sub)
            else:
                # 不是以語氣詞開頭，保持原樣
                fixed_subtitles.append(sub)

        if fixed_count > 0:
            logger.info(f"📊 語氣詞後處理：修正了 {fixed_count} 處句首語氣詞")

        # NEW: Also fix punctuation appearing before particles within segments
        punctuation_fixed_count = 0
        final_subtitles = []
        for sub in fixed_subtitles:
            text = sub.colloquial
            corrected_text = self._fix_particle_punctuation(text)
            
            if corrected_text != text:
                final_subtitles.append(SubtitleEntryV2(
                    start=sub.start,
                    end=sub.end,
                    colloquial=corrected_text,
                    formal=sub.formal
                ))
                punctuation_fixed_count += 1
                logger.info(f"[標點修正] '{text}' → '{corrected_text}'")
            else:
                final_subtitles.append(sub)
        
        if punctuation_fixed_count > 0:
            logger.info(f"📊 標點修正：修正了 {punctuation_fixed_count} 處標點位置")

        return final_subtitles

    def _remove_ending_hallucinations(self, subtitles: List[SubtitleEntryV2]) -> List[SubtitleEntryV2]:
        """
        Remove Whisper hallucinations at the end of subtitles.

        Whisper often hallucinates repetitive short words (like "不是 不是 不是")
        when only background music exists at the end of the video.

        Detection criteria:
        1. Short repetitive words within a single segment (e.g., "不是 不是 不是")
        2. Multiple consecutive segments with identical or similar text
        3. Occurring in the last 20% of the video duration

        Args:
            subtitles: List of subtitle entries

        Returns:
            Filtered subtitle list with hallucinations removed
        """
        if not subtitles:
            return subtitles

        # 計算影片總時長和檢測範圍
        total_duration = subtitles[-1].end if subtitles else 0
        # 修復「嘩」字幻覺問題：擴大檢測範圍 95% → 70%，捕捉中後段的幻覺重複
        hallucination_threshold = total_duration * 0.70  # 最後 30% 時間範圍（幻覺可能從 70% 開始）

        # 常見的幻聽詞（Whisper 在背景音樂中經常誤識別的詞）
        # 修復「嘩」字幻覺：新增「嘩」「嘻」等感嘆詞到幻覺列表
        common_hallucinations = {
            '不是', '是', '嗯', '啊', '哦', '喔', '呃', '欸',
            '好', '對', '唔', '咦', '呀', '啦', '囉', '吖',
            '嘩', '嘻', '哇', '喂', '哎', '嗨'  # 新增感嘆詞
        }

        # 檢測重複段落的函數
        def is_repetitive_text(text: str) -> bool:
            """檢測文本是否是重複的短詞（如「嘩 嘩 嘩」或「不是 不是 不是 不是 不是」）"""
            # 移除標點符號，只保留文字
            clean_text = text.replace('!', ' ').replace('！', ' ').replace(',', ' ').replace('，', ' ').strip()
            words = [w for w in clean_text.split() if w]

            if len(words) < 2:
                return False

            # 檢查是否所有詞都相同
            first_word = words[0]
            if all(word == first_word for word in words):
                # 檢測兩種情況：
                # 1. 感嘆詞（嘩、嘻）：≥2 次重複即為幻覺
                # 2. 其他詞：≥5 次重複才算幻覺（避免誤刪「好好好」「係係係」）
                if first_word in {'嘩', '嘻', '哇', '喂', '哎', '嗨'}:
                    if len(words) >= 2 and first_word in common_hallucinations:
                        return True
                else:
                    if len(words) >= 5 and first_word in common_hallucinations:
                        return True

            return False

        # 第一階段：標記需要移除的索引
        indices_to_remove = set()

        # 檢測單個段落內的重複（如「不是 不是 不是」）
        for i, sub in enumerate(subtitles):
            # 只檢查最後 20% 時間範圍內的字幕
            if sub.start < hallucination_threshold:
                continue

            if is_repetitive_text(sub.colloquial):
                indices_to_remove.add(i)
                logger.warning(f"Hallucination detected (repetitive): segment {i} - '{sub.colloquial}'")

        # 檢測連續相同段落（3 個及以上）
        consecutive_count = 1
        prev_text = None
        consecutive_start = -1

        for i, sub in enumerate(subtitles):
            # 只檢查最後 20% 時間範圍內的字幕
            if sub.start < hallucination_threshold:
                prev_text = sub.colloquial.strip()
                consecutive_count = 1
                continue

            current_text = sub.colloquial.strip()

            if current_text == prev_text and current_text:
                if consecutive_count == 1:
                    consecutive_start = i - 1
                consecutive_count += 1
            else:
                # 如果連續 3 個及以上相同，標記為移除（除了第一個）
                if consecutive_count >= 3:
                    for idx in range(consecutive_start + 1, consecutive_start + consecutive_count):
                        indices_to_remove.add(idx)
                        logger.warning(f"Hallucination detected (consecutive): segment {idx} - '{subtitles[idx].colloquial}'")

                consecutive_count = 1
                consecutive_start = -1

            prev_text = current_text

        # 處理最後一組連續段落
        if consecutive_count >= 3:
            for idx in range(consecutive_start + 1, consecutive_start + consecutive_count):
                indices_to_remove.add(idx)
                logger.warning(f"Hallucination detected (consecutive end): segment {idx} - '{subtitles[idx].colloquial}'")

        # 第二階段：移除標記的段落
        if indices_to_remove:
            filtered_subtitles = [sub for i, sub in enumerate(subtitles) if i not in indices_to_remove]
            # 增強日誌：詳細記錄幻覺移除情況
            logger.info(f"📊 Hallucination check: {len(indices_to_remove)} segments flagged for removal")
            logger.info(f"Subtitle count: {len(subtitles)} -> {len(filtered_subtitles)}")
            return filtered_subtitles
        else:
            logger.info("📊 Hallucination check: No hallucinations detected")
            return subtitles

    def _optimize_sentence_boundaries(
        self,
        subtitles: List[SubtitleEntryV2],
        progress_callback: Optional[Callable] = None
    ) -> List[SubtitleEntryV2]:
        """
        Use LLM to optimize sentence boundaries for semantic completeness.

        VAD splits by audio pauses, which may break sentences mid-thought.
        This method uses LLM to:
        1. Detect incomplete sentences (e.g., "你份穩定，")
        2. Merge them with the next segment for completeness
        3. Split overly long segments if needed
        4. Preserve accurate timestamps

        Args:
            subtitles: List of subtitle entries from VAD
            progress_callback: Optional progress callback

        Returns:
            Optimized subtitle list with complete sentences
        """
        if not subtitles or len(subtitles) < 2:
            return subtitles

        # 初始化 LLM（使用 MLX Qwen）
        from utils.qwen_mlx import MLXQwenLLM

        try:
            llm = MLXQwenLLM(model_id="mlx-community/Qwen2.5-3B-Instruct-bf16")
            logger.info("LLM loaded for sentence boundary optimization")
        except Exception as e:
            logger.warning(f"Failed to load LLM for sentence optimization: {e}")
            logger.info("Skipping sentence optimization, returning original subtitles")
            return subtitles

        # 批量處理（每次處理 5 句，提供前後更多上下文）
        batch_size = 5
        context_window = 3  # 增強上下文：從 2 句擴展到 3 句
        optimized_subtitles = []
        merge_instructions = {}  # {index: "merge_with_next" / "keep" / "split"}

        total_batches = (len(subtitles) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(subtitles), batch_size):
            batch_end = min(batch_idx + batch_size, len(subtitles))
            batch = subtitles[batch_idx:batch_end]

            # 構建上下文（擴展窗口以提供更多語境）
            context_before = []
            if batch_idx > 0:
                context_start = max(0, batch_idx - context_window)
                context_before = [sub.colloquial for sub in subtitles[context_start:batch_idx]]

            context_after = []
            if batch_end < len(subtitles):
                context_end = min(len(subtitles), batch_end + context_window)
                context_after = [sub.colloquial for sub in subtitles[batch_end:context_end]]

            # 構建 Prompt（增強上下文利用）
            batch_texts = "\n".join([f"{i+1}. {sub.colloquial}" for i, sub in enumerate(batch)])
            context_prompt = ""

            if context_before:
                context_prompt += "\n【前文上下文】（用於理解語境和話題連貫性）\n" + "\n".join([f"  • {t}" for t in context_before])

            if context_after:
                context_prompt += "\n【後續上下文】（用於判斷當前句是否完整）\n" + "\n".join([f"  • {t}" for t in context_after])

            prompt = f"""你是粵語字幕斷句優化專家。任務：判斷每句話是否需要合併或拆分，目標是保持 1-2 句的短字幕。

【核心原則】
1. 短字幕優先：每條字幕最多 1-2 句話（理想是 1 句）
2. 激進拆分策略：遇到長句（>20 字）優先拆分，而非合併
3. 語意完整性：只在句子明顯不完整時才合併（如缺主句、從句未完）
4. 粵語停頓特性：語氣詞（如"嘅話"、"咁樣"）通常是自然斷句點

【判斷標準】
✅ keep（保持原狀）- 符合以下任一條件：
  • 句子語意完整（即使較短也 keep，短字幕更好）
  • 有明確語氣停頓（如逗號、語氣詞後）
  • 與下一句話題不同
  • 句子長度已經較長（>15 字），不應再合併

❌ merge（合併下一句）- **僅在**符合以下條件時才合併：
  • 句子明顯不完整（如"你份穩定，"後缺主句）
  • 明顯的從句或條件句未完（如"如果你..."、"因為..."後沒主句）
  • 合併後總長度 ≤20 字

⚠️ split（建議拆分）- 符合以下條件時應拆分：
  • 句子過長（>25 字）
  • 包含多個子句或並列句
  • 可在逗號、語氣詞處自然拆分

【示例分析】
例 1: "你份穩定，" (8 字) + 後續："只是一個假象"
  → 判斷：merge（逗號後缺主句，且合併後 <20 字）

例 2: "今天這部影片想記錄我在韓國的日常生活" (18 字)
  → 判斷：keep（語意完整，長度適中，不應再合併）

例 3: "如果你今日唔建立第二糧倉，10年後你都重要為你嘅第一糧倉嘅博殺" (28 字)
  → 判斷：split（過長，應拆成"如果你今日唔建立第二糧倉" + "10年後你都重要為你嘅第一糧倉嘅博殺"）

例 4: "好好好" (3 字) + 後續："我明白了"
  → 判斷：keep（雖然短，但語意完整，保持短字幕更佳）
{context_prompt}

【需要分析的句子】
{batch_texts}

【重要提示】
- **優先保持短字幕**（1-2 句），避免過度合併
- 只有在句子明顯不完整時才 merge
- 遇到長句優先考慮 keep 或 split，而非 merge
- 短字幕（<10 字）即使看起來簡短，也應 keep（短字幕更易閱讀）

【輸出格式】（只輸出以下格式，不要額外解釋）
1. keep 或 merge
2. keep 或 merge
3. keep 或 merge
...

【輸出】"""

            try:
                response = llm.generate(prompt, max_tokens=256, temperature=0)
                lines = response.strip().split('\n')

                # 解析 LLM 的建議
                for i, line in enumerate(lines[:len(batch)]):
                    parts = line.split('.')
                    if len(parts) >= 2:
                        action = parts[1].strip().lower()
                        global_idx = batch_idx + i
                        if 'merge' in action:
                            merge_instructions[global_idx] = 'merge_with_next'
                        elif 'split' in action:
                            merge_instructions[global_idx] = 'split'
                        else:
                            merge_instructions[global_idx] = 'keep'

            except Exception as e:
                logger.warning(f"LLM sentence analysis failed for batch {batch_idx}: {e}")
                # 失敗時保持原樣
                for i in range(len(batch)):
                    merge_instructions[batch_idx + i] = 'keep'

            # Report progress
            if progress_callback:
                progress = 90 + int((batch_idx / len(subtitles)) * 10)
                progress_callback(progress)

        # 根據 LLM 建議執行合併
        i = 0
        while i < len(subtitles):
            action = merge_instructions.get(i, 'keep')

            if action == 'merge_with_next' and i + 1 < len(subtitles):
                # 合併當前和下一句
                merged_text = subtitles[i].colloquial + " " + subtitles[i + 1].colloquial
                
                # NEW: Validate merged length (max 40 chars)
                if len(merged_text) > 40:
                    logger.warning(f"Merged segment too long ({len(merged_text)} chars), keeping separate: '{merged_text[:30]}...'")
                    # Keep current segment and continue to next
                    optimized_subtitles.append(subtitles[i])
                    i += 1
                    continue
                
                merged_sub = SubtitleEntryV2(
                    start=subtitles[i].start,
                    end=subtitles[i + 1].end,
                    colloquial=merged_text.strip(),
                    formal=None
                )
                optimized_subtitles.append(merged_sub)
                logger.info(f"Merged segments {i} and {i+1}: '{merged_text[:50]}...'")
                i += 2  # 跳過下一句（已合併）
            else:
                # 保持原樣
                optimized_subtitles.append(subtitles[i])
                i += 1

        # 清理 LLM
        del llm
        import gc
        gc.collect()

        # 增強日誌：記錄 LLM 優化結果
        merged_count = len(subtitles) - len(optimized_subtitles)
        logger.info(f"📊 LLM optimization: {len(subtitles)} -> {len(optimized_subtitles)} segments (merged {merged_count} segments)")
        return optimized_subtitles

    # _refine_with_llm removed - 書面語 conversion is handled by StyleControlPanel

    # ==================== 終極模式 ====================

    def process_ultimate(
        self,
        input_path: str,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> List[SubtitleEntryV2]:
        """
        終極轉錄模式 - 極致準確度

        整合所有高級優化策略：
        1. 音頻預處理（降噪 + 人聲增強）
        2. VAD 預分割（確保不在句中切斷）
        3. 三階段轉錄（粗轉錄 → 重轉錄低信心 → LLM 校正）
        4. 錨點系統（高信心驗證低信心）
        5. 用戶詞彙學習（個人化校正）

        注意：處理時間約為標準模式的 2-3 倍

        Args:
            input_path: 音頻/視頻文件路徑
            progress_callback: 進度回調 (0-100)
            status_callback: 狀態訊息回調

        Returns:
            字幕列表
        """
        if not HAS_ADVANCED_FEATURES:
            logger.warning("高級轉錄模組未安裝，使用標準模式")
            return self.process(input_path, progress_callback, status_callback)

        logger.info("🚀 啟動終極轉錄模式...")
        input_file = Path(input_path)

        import gc
        import torch

        if progress_callback:
            progress_callback(0)

        # Step 1: 清理內存
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Step 2: 準備音頻
        if status_callback:
            status_callback("準備音頻...")

        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
        if input_file.suffix.lower() in video_extensions:
            audio_path = self._extract_audio(input_file)
        else:
            audio_path = str(input_file)

        if progress_callback:
            progress_callback(5)

        # Step 3: 音頻預處理
        if status_callback:
            status_callback("音頻預處理（降噪增強）...")

        enhancer = AudioEnhancer(self.temp_dir)
        quality = enhancer.analyze_audio_quality(audio_path)
        logger.info(f"音頻質量: SNR={quality['snr_estimate']:.1f}dB")

        if quality['needs_enhancement']:
            logger.info("音頻需要增強...")
            audio_path = enhancer.quick_enhance(audio_path)

        if progress_callback:
            progress_callback(15)

        # Step 4: 加載 ASR 模型
        if status_callback:
            status_callback("加載 AI 模型...")

        self._load_asr(progress_callback, status_callback)

        if progress_callback:
            progress_callback(25)

        # Step 5: 初始化高級轉錄器
        advanced_transcriber = AdvancedTranscriber(self.config)

        # 初始化 VAD
        if self.vad is None:
            self.vad = VADProcessor(
                self.config,
                threshold=0.10,
                min_silence_duration_ms=300,
                min_speech_duration_ms=50,
                speech_pad_ms=500
            )

        # Step 6: 執行三階段轉錄
        if status_callback:
            status_callback("執行高精度轉錄...")

        def transcribe_progress(p):
            if progress_callback:
                # 映射 0-100 到 25-80
                progress_callback(25 + int(p * 0.55))

        transcription_chunks = advanced_transcriber.three_stage_transcribe(
            audio_path,
            self.asr,
            self.vad,
            progress_callback=transcribe_progress,
            status_callback=status_callback
        )

        if progress_callback:
            progress_callback(80)

        # Step 7: 轉換為 SubtitleEntryV2 格式
        if status_callback:
            status_callback("後處理校正...")

        # 獲取用戶詞彙
        vocab_learner = get_vocabulary_learner()
        user_prompt = vocab_learner.generate_whisper_prompt()
        if user_prompt:
            logger.info(f"應用用戶詞彙: {len(vocab_learner.vocabulary)} 個")

        final_subtitles = []
        for chunk in transcription_chunks:
            # 應用簡單校正
            text = self._apply_simple_corrections(chunk.text.strip())

            # 應用用戶詞彙自動校正
            text = auto_correct_text(text)

            final_subtitles.append(SubtitleEntryV2(
                start=chunk.start,
                end=chunk.end,
                colloquial=text,
                formal=None
            ))

        # Step 8: 語氣詞修正
        final_subtitles = self._fix_sentence_final_particles(final_subtitles)

        # Step 9: 幻覺移除
        final_subtitles = self._remove_ending_hallucinations(final_subtitles)

        if progress_callback:
            progress_callback(90)

        # Step 10: LLM 斷句優化（如果啟用）
        enable_llm_segmentation = self.config.get("enable_llm_sentence_optimization", True)
        if enable_llm_segmentation:
            if status_callback:
                status_callback("AI 斷句優化...")

            gc.collect()
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

            final_subtitles = self._optimize_sentence_boundaries(
                final_subtitles, progress_callback
            )

        if progress_callback:
            progress_callback(100)

        # 清理
        advanced_transcriber.cleanup()
        enhancer.cleanup()

        logger.info(f"✅ 終極轉錄完成：{len(final_subtitles)} 個字幕")
        return final_subtitles

    def process(
        self,
        input_path: str,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> List[SubtitleEntryV2]:
        """
        Run the subtitle generation pipeline with sequential model loading.
        
        Pipeline stages (memory efficient - one model at a time):
        1. Load ASR (Whisper)
        2. Extract audio if needed
        3. Transcribe with Whisper
        4. Unload Whisper to free GPU memory
        5. Load LLM (if enabled)
        6. Refine with LLM
        
        Args:
            input_path: Path to audio/video file
            progress_callback: Progress callback (0-100)
            status_callback: Status message callback for UI updates
            
        Returns:
            List of SubtitleEntryV2 with colloquial (and optional formal) text
        """
        # 檢查是否啟用終極模式
        ultimate_mode = self.config.get("enable_ultimate_transcription", False)
        if ultimate_mode and HAS_ADVANCED_FEATURES:
            logger.info("🚀 終極模式已啟用，使用高精度轉錄...")
            return self.process_ultimate(input_path, progress_callback, status_callback)

        logger.info(f"Starting V2 pipeline for: {input_path}")
        logger.info("Using sequential model loading (memory efficient mode)")
        input_file = Path(input_path)

        # Step 0: Check LLM availability and download if needed (0-5%)
        # 修復首次使用問題：轉譯前檢查 LLM，未下載時先提示並下載
        enable_llm_optimization = self.config.get("enable_llm_sentence_optimization", True)

        if enable_llm_optimization:
            from huggingface_hub import try_to_load_from_cache

            # 檢查 LLM 是否已下載
            llm_model_id = "mlx-community/Qwen2.5-3B-Instruct-bf16"
            cache_result = try_to_load_from_cache(llm_model_id, "config.json")
            llm_cached = cache_result is not None

            if not llm_cached:
                logger.warning(f"⚠️ LLM 模型未下載，首次使用需下載 3-6GB 模型")
                if status_callback:
                    status_callback("首次使用需下載 AI 模型（3-6GB），請稍候...")

                # 預下載 LLM 模型（避免轉譯中途卡住）
                try:
                    from utils.qwen_mlx import MLXQwenLLM
                    llm_temp = MLXQwenLLM(model_id=llm_model_id)

                    def llm_progress_callback(msg):
                        if status_callback:
                            status_callback(f"正在下載 AI 模型：{msg}")
                        logger.info(msg)

                    llm_temp.load_model(progress_callback=llm_progress_callback)
                    del llm_temp
                    logger.info("✅ LLM 模型預下載完成")
                    if status_callback:
                        status_callback("AI 模型下載完成，開始轉譯...")
                except Exception as e:
                    logger.warning(f"LLM 預下載失敗: {e}")
                    logger.info("將在轉譯過程中自動下載（可能較慢）")
                    if status_callback:
                        status_callback("AI 模型下載失敗，將使用基礎模式...")

        # Step 0.5: Pre-clear GPU memory (0-5%)
        import gc
        import torch

        if progress_callback:
            progress_callback(0)
        
        logger.info("Pre-clearing GPU memory before pipeline start...")
        gc.collect()
        # Cross-platform GPU memory cleanup
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
            logger.info("MPS memory cache cleared, ready for model loading")
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.info("CUDA memory cache cleared, ready for model loading")
        
        if progress_callback:
            progress_callback(5)
        
        # Step 1: Load ASR model only (5-15%)
        self._load_asr(progress_callback, status_callback=status_callback)
        
        # Step 2: Prepare audio (15-20%)
        if progress_callback:
            progress_callback(15)
        
        # Check if video needs audio extraction
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
        if input_file.suffix.lower() in video_extensions:
            audio_path = self._extract_audio(input_file)
        else:
            audio_path = str(input_file)
        
        # Step 3: Transcribe with Whisper (20-60%)
        if progress_callback:
            progress_callback(20)
        
        logger.info("Running Whisper transcription...")

        # Get language style from config
        language_style = self.config.get("subtitle_language_style", "formal")
        
        # Get custom prompt from config (user-defined vocabulary for better recognition)
        custom_prompt = self.config.get("whisper_custom_prompt", "")

        # Build kwargs for transcribe based on language style
        transcribe_kwargs = {
            'language': 'yue',
            'language_style': language_style,
        }

        # 修復字幕辨識錯誤：自動啟用旅遊+購物詞彙（涵蓋大部分日常影片場景）
        # 啟用 travel 和 shopping domain 可大幅提升地名、商品名稱的辨識準確度
        transcribe_kwargs['domain'] = 'travel'  # 預設使用旅遊詞彙（涵蓋地名、景點、酒店等）
        logger.info("🗺️ Enabled travel domain vocabulary for better location/place name recognition")

        # Add custom prompt if provided
        if custom_prompt:
            transcribe_kwargs['custom_prompt'] = custom_prompt
            logger.info(f"Using custom prompt: {custom_prompt[:50]}...")
        
        logger.info(f"📝 Transcription language style: {language_style}")

        result = self.asr.transcribe(audio_path, **transcribe_kwargs)
        
        whisper_segments = result.get('segments', [])
        logger.info(f"Whisper produced {len(whisper_segments)} segments")
        
        if not whisper_segments:
            logger.warning("No segments from Whisper")
            return []
        
        if progress_callback:
            progress_callback(60)
        
        # Step 4: VAD-based smart segmentation (60-75%)
        logger.info("Running VAD-based smart segmentation...")
        if progress_callback:
            progress_callback(62)
        
        try:
            # Initialize VAD processor (優化斷句連貫性)
            if self.vad is None:
                # 修復字幕遺漏問題：優化 VAD 參數，減少漏檢
                self.vad = VADProcessor(
                    self.config,
                    threshold=0.10,                # 降低門檻 (0.15→0.10)，更敏感，減少漏檢輕聲說話
                    min_silence_duration_ms=300,   # 縮短靜音判斷 (500→300ms)，避免過度拆分
                    min_speech_duration_ms=50,     # 允許更短語音 (100→50ms)，保留快速說話
                    speech_pad_ms=500              # 增加填充 (300→500ms)，保留完整語句
                )

            # Detect voice segments
            voice_segments = self.vad.detect_voice_segments(audio_path)
            logger.info(f"VAD detected {len(voice_segments)} voice segments")

            if progress_callback:
                progress_callback(68)

            # Merge Whisper + VAD for smart segmentation
            # 修復字幕過度合併問題：縮短合併參數，保持 1-2 句的短字幕
            # 啟用保守模式：保留無 VAD 重疊但有意義的段落，減少文字遺漏
            optimized_segments = self.vad.merge_with_transcription(
                whisper_segments,
                voice_segments,
                max_gap=0.8,           # 縮短停頓閾值 (1.5→0.8s)，減少合併，保持短句
                max_chars=30,          # 縮短字數限制 (50→30字)，強制拆分長句
                conservative_mode=True # 保守模式：保留可疑段落，減少文字遺漏
            )
            logger.info(f"VAD optimization: {len(whisper_segments)} -> {len(optimized_segments)} segments")
            
            # Use optimized segments
            whisper_segments = optimized_segments
            
        except Exception as e:
            logger.warning(f"VAD segmentation failed, using original Whisper segments: {e}")
            # Continue with original Whisper segments
        
        if progress_callback:
            progress_callback(75)
        
        # Step 5: Apply simple corrections and create final subtitles (75-95%)
        # Note: 書面語 conversion is handled by StyleControlPanel, not here
        if progress_callback:
            progress_callback(85)

        final_subtitles = [
            SubtitleEntryV2(
                start=seg.start,
                end=seg.end,
                colloquial=self._apply_simple_corrections(seg.text.strip()),
                formal=None  # Will be filled by StyleControlPanel if user selects 書面語
            )
            for seg in whisper_segments
        ]

        # Step 5.4: Fix sentence-final particles at wrong position (82-85%)
        # 修正 VAD 斷句錯誤導致語氣詞出現喺句首（如「嗎茶葉蛋的味道呀」）
        if progress_callback:
            progress_callback(82)

        logger.info("Fixing sentence-final particles at wrong position...")
        final_subtitles = self._fix_sentence_final_particles(final_subtitles)

        # Step 5.5: Remove Whisper hallucination at the end (85-90%)
        # Whisper often hallucinates repetitive short words at the end when only background music exists
        if progress_callback:
            progress_callback(85)

        final_subtitles = self._remove_ending_hallucinations(final_subtitles)

        # Step 6: LLM intelligent sentence boundary optimization (90-100%)
        # Use LLM to merge incomplete sentences and ensure semantic completeness
        if progress_callback:
            progress_callback(90)

        # Check if LLM sentence optimization is enabled
        enable_llm_segmentation = self.config.get("enable_llm_sentence_optimization", True)
        if enable_llm_segmentation:
            # 清理 VRAM（在加載 LLM 之前釋放 Whisper/VAD 使用的內存）
            logger.info("Pre-clearing VRAM before LLM sentence optimization...")
            gc.collect()
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
                logger.info("MPS cache cleared for LLM")
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.info("CUDA cache cleared for LLM")

            logger.info("Starting LLM sentence boundary optimization...")
            final_subtitles = self._optimize_sentence_boundaries(final_subtitles, progress_callback)
        else:
            logger.info("LLM sentence optimization disabled, skipping...")

        if progress_callback:
            progress_callback(100)

        logger.info(f"Pipeline complete. Generated {len(final_subtitles)} subtitles")
        return final_subtitles
    
    def cleanup(self):
        """Release all resources."""
        import gc
        import torch
        
        logger.info("Cleaning up pipeline resources...")
        
        if self.asr:
            try:
                self.asr.unload_model()
            except Exception as e:
                logger.warning(f"ASR cleanup error: {e}")
            self.asr = None
        
        # LLM cleanup removed - LLM is handled by StyleControlPanel
        
        if self.vad:
            try:
                self.vad.unload_model()
            except Exception as e:
                logger.warning(f"VAD cleanup error: {e}")
            self.vad = None
        
        self._models_loaded = False
        
        # Force garbage collection
        gc.collect()
        
        # Cross-platform GPU memory cleanup
        try:
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
                logger.info("MPS memory cache cleared")
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.info("CUDA memory cache cleared")
        except Exception as e:
            logger.warning(f"GPU cache clear error: {e}")
        
        logger.info("Pipeline cleanup complete")
    
    def get_profile(self) -> Optional[PerformanceProfile]:
        """Get the current hardware profile."""
        return self.profile
