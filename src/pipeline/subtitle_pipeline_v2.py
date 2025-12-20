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
from models.qwen_llm import QwenLLM
from models.vad_processor import VADProcessor
from utils.logger import setup_logger

# Try to import MLX Whisper for Apple Silicon acceleration
try:
    from utils.whisper_mlx import MLXWhisperASR, get_best_whisper_backend
    HAS_MLX_WHISPER = MLXWhisperASR.is_available()
except ImportError:
    HAS_MLX_WHISPER = False

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
    
    def __init__(self, config: Config, force_cpu: bool = False, enable_llm: bool = True):
        """
        Initialize pipeline.
        
        Args:
            config: Application configuration
            force_cpu: Force CPU mode
            enable_llm: Enable LLM refinement for better conversion
        """
        self.config = config
        self.force_cpu = force_cpu
        self.enable_llm = enable_llm
        self.profile = None
        self.asr = None
        self.llm = None
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
    
    def _load_llm(self, progress_callback: Optional[Callable] = None):
        """Load LLM model (call after ASR is unloaded for memory efficiency)."""
        if not self.enable_llm or not self.profile.llm_a_enabled:
            logger.info("LLM refinement disabled, skipping LLM load")
            return
            
        if self.llm is not None:
            return
            
        logger.info("Loading LLM for AI refinement...")
        if progress_callback:
            progress_callback(82)
        self.llm = QwenLLM(self.config, self.profile)
        self.llm.load_models()
        logger.info("LLM loaded successfully")
    
    def _extract_audio(self, video_path: Path) -> str:
        """Extract audio from video file."""
        import subprocess
        from core.path_setup import get_ffmpeg_path
        
        audio_path = self.temp_dir / f"{video_path.stem}_audio.wav"
        
        logger.info(f"Extracting audio from video: {video_path}")
        
        # Use get_ffmpeg_path() to get full path (works in packaged app)
        ffmpeg_path = get_ffmpeg_path()
        logger.info(f"Using FFmpeg: {ffmpeg_path}")
        
        # Check if FFmpeg actually exists at that path
        ffmpeg_exists = Path(ffmpeg_path).exists() if ffmpeg_path != 'ffmpeg' else True
        if not ffmpeg_exists and ffmpeg_path != 'ffmpeg':
            logger.error(f"FFmpeg not found at: {ffmpeg_path}")
            raise FileNotFoundError(
                f"FFmpeg 未找到！請安裝 FFmpeg:\n"
                f"  macOS: brew install ffmpeg\n"
                f"  預期路徑: {ffmpeg_path}"
            )
        
        cmd = [
            ffmpeg_path, '-y', '-i', str(video_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(audio_path)
        ]
        
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        
        try:
            # Add timeout (5 minutes should be enough for most videos)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg stderr: {result.stderr}")
                raise RuntimeError(f"FFmpeg 失敗: {result.stderr[:500]}")
            
            # Verify output file exists
            if not audio_path.exists():
                raise RuntimeError(f"音頻檔案未生成: {audio_path}")
            
            logger.info(f"Audio extracted to: {audio_path}")
            return str(audio_path)
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout after 5 minutes")
            raise RuntimeError("FFmpeg 超時（超過5分鐘），請檢查影片檔案是否正確")
        except FileNotFoundError as e:
            logger.error(f"FFmpeg not found: {e}")
            raise FileNotFoundError(
                f"FFmpeg 未找到！請安裝 FFmpeg:\n"
                f"  macOS: brew install ffmpeg"
            )
    
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
    
    def _needs_llm_correction(self, text: str) -> bool:
        """檢查文字是否包含需要 LLM 校正嘅錯誤。
        
        [全部 LLM 模式] - 所有句子都經過 LLM 校正，確保成語同俗語正確處理。
        """
        # 全部句子都需要 LLM 校正
        return True
    
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
    
    def _refine_with_llm(self, segments: List, progress_callback: Optional[Callable] = None) -> List[SubtitleEntryV2]:
        """
        使用 LLM 智能校正 Whisper segments。
        
        【智能過濾模式】：
        - 有錯字 → 調用 LLM 校正
        - 冇錯字 → 直接做簡單替換（超快）
        
        Args:
            segments: Whisper TranscriptionSegment 列表
            progress_callback: 進度回調 (80-95%)
            
        Returns:
            SubtitleEntryV2 列表
        """
        # 無 LLM 時，只做簡單替換
        if not self.llm:
            logger.info("No LLM available, applying simple corrections only...")
            return [
                SubtitleEntryV2(
                    start=seg.start,
                    end=seg.end,
                    colloquial=self._apply_simple_corrections(seg.text.strip()),
                    formal=None
                )
                for seg in segments
            ]
        
        # 統計需要 LLM 嘅 segment 數量
        needs_llm_count = sum(1 for seg in segments if self._needs_llm_correction(seg.text.strip()))
        logger.info(f"Smart LLM: {needs_llm_count}/{len(segments)} segments need LLM correction")
        
        refined_entries = []
        total = len(segments)
        llm_calls = 0
        
        # 提取所有文本用於上下文
        all_texts = [seg.text.strip() for seg in segments]
        
        for i, seg in enumerate(segments):
            # 更新進度 (80-95%)
            if progress_callback:
                pct = 80 + int((i / total) * 15)
                progress_callback(pct)
            
            original_text = seg.text.strip()
            
            # 檢查是否需要 LLM 校正
            if self._needs_llm_correction(original_text):
                llm_calls += 1
                try:
                    # 構建前文後理 context (前2句 + 後2句)
                    context_before = all_texts[max(0, i-2):i]
                    context_after = all_texts[i+1:min(len(all_texts), i+3)]
                    
                    # 組合上下文
                    context_text = ""
                    if context_before:
                        context_text += "【前文】" + " | ".join(context_before) + "\n"
                    context_text += "【當前句子】" + original_text + "\n"
                    if context_after:
                        context_text += "【後文】" + " | ".join(context_after)
                    
                    # 調用 LLM 校正（帶上下文）
                    result = self.llm.refine_text_with_context(original_text, context_text)
                    refined_sentences = result.get('sentences', [])
                    
                    if refined_sentences:
                        refined_text = refined_sentences[0] if len(refined_sentences) == 1 else ''.join(refined_sentences)
                        formal = refined_text if refined_text != original_text else None
                    else:
                        formal = None
                    
                    # 同時應用簡單替換
                    corrected = self._apply_simple_corrections(original_text)
                    
                    entry = SubtitleEntryV2(
                        start=seg.start,
                        end=seg.end,
                        colloquial=corrected,
                        formal=formal
                    )
                except Exception as e:
                    logger.warning(f"LLM error for segment {i}: {e}")
                    entry = SubtitleEntryV2(
                        start=seg.start,
                        end=seg.end,
                        colloquial=self._apply_simple_corrections(original_text),
                        formal=None
                    )
            else:
                # 唔需要 LLM，直接簡單替換
                entry = SubtitleEntryV2(
                    start=seg.start,
                    end=seg.end,
                    colloquial=self._apply_simple_corrections(original_text),
                    formal=None
                )
            
            refined_entries.append(entry)
        
        saved = len(segments) - llm_calls
        logger.info(f"LLM refinement complete: {llm_calls} LLM calls, saved {saved} calls ({saved/len(segments)*100:.0f}% faster)")
        return refined_entries
    
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
        logger.info(f"Starting V2 pipeline for: {input_path}")
        logger.info("Using sequential model loading (memory efficient mode)")
        input_file = Path(input_path)
        
        # Step 0: Pre-clear GPU memory (0-5%)
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
        
        # Get custom prompt from config (user-defined vocabulary for better recognition)
        custom_prompt = self.config.get("whisper_custom_prompt", "")
        result = self.asr.transcribe(audio_path, language='yue', custom_prompt=custom_prompt)
        
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
            # Initialize VAD processor (高敏感度配置)
            if self.vad is None:
                self.vad = VADProcessor(
                    self.config,
                    threshold=0.1,              # 降低閾值 (0.5->0.35)，更敏感檢測語音
                    min_silence_duration_ms=20, # 降低靜音門檻 (200->150)，更精細斷句
                    min_speech_duration_ms=50,  # 降低語音門檻 (250->200)，保留短句
                    speech_pad_ms=300            # 減少填充 (400->300)，更貼近實際邊界
                )
            
            # Detect voice segments
            voice_segments = self.vad.detect_voice_segments(audio_path)
            logger.info(f"VAD detected {len(voice_segments)} voice segments")
            
            if progress_callback:
                progress_callback(68)
            
            # Merge Whisper + VAD for smart segmentation
            optimized_segments = self.vad.merge_with_transcription(
                whisper_segments,
                voice_segments,
                max_gap=0.2,  # 縮短合併間隔 (0.8->0.5s)，更多獨立句子
                max_chars=22  # 縮短每段最大字數 (25->22)，更適合字幕
            )
            logger.info(f"VAD optimization: {len(whisper_segments)} -> {len(optimized_segments)} segments")
            
            # Use optimized segments
            whisper_segments = optimized_segments
            
        except Exception as e:
            logger.warning(f"VAD segmentation failed, using original Whisper segments: {e}")
            # Continue with original Whisper segments
        
        if progress_callback:
            progress_callback(75)
        
        # Step 5: Unload Whisper to free GPU memory (75-80%)
        if self.enable_llm and self.profile.llm_a_enabled:
            self._unload_asr()
            if progress_callback:
                progress_callback(80)
        
        # Step 6: LLM refinement (80-95%)
        if self.enable_llm:
            # Load LLM now that Whisper is unloaded
            self._load_llm(progress_callback)
            
            logger.info("Starting LLM refinement...")
            final_subtitles = self._refine_with_llm(whisper_segments, progress_callback)
        else:
            # No LLM, but still apply simple corrections
            final_subtitles = [
                SubtitleEntryV2(
                    start=seg.start,
                    end=seg.end,
                    colloquial=self._apply_simple_corrections(seg.text.strip()),
                    formal=None
                )
                for seg in whisper_segments
            ]
        
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
        
        if self.llm:
            try:
                self.llm.unload_models()
            except Exception as e:
                logger.warning(f"LLM cleanup error: {e}")
            self.llm = None
        
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
