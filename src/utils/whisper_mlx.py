"""
MLX Whisper backend for Apple Silicon.

Uses Apple's MLX framework for optimal performance on Apple Silicon,
automatically leveraging CoreML (Neural Engine) or MPS (GPU).

Priority: CoreML (Neural Engine) > MPS (GPU) > CPU fallback
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Union
from dataclasses import dataclass

from utils.logger import setup_logger

logger = setup_logger()

# ============================================
# CRITICAL: Setup ffmpeg PATH at module load time
# This ensures mlx_whisper's subprocess calls find ffmpeg
# ============================================
def _setup_ffmpeg_path():
    """Ensure Homebrew ffmpeg is in PATH for subprocess calls."""
    homebrew_paths = [
        '/opt/homebrew/bin',  # Apple Silicon
        '/usr/local/bin',      # Intel Mac
    ]
    
    current_path = os.environ.get('PATH', '')
    paths_to_add = []
    
    for hp in homebrew_paths:
        if Path(hp).exists() and hp not in current_path:
            # Check if ffmpeg exists in this path
            if (Path(hp) / 'ffmpeg').exists():
                paths_to_add.append(hp)
                logger.debug(f"Found ffmpeg in {hp}")
    
    if paths_to_add:
        # Prepend to PATH so Homebrew ffmpeg is found first
        os.environ['PATH'] = os.pathsep.join(paths_to_add) + os.pathsep + current_path
        logger.info(f"Added Homebrew paths to PATH for ffmpeg: {paths_to_add}")

# Run at module load
_setup_ffmpeg_path()




@dataclass
class MLXTranscriptionSegment:
    """A segment of transcribed text with timing information."""
    
    id: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str
    confidence: float = 1.0
    language: str = "yue"
    words: List[Dict] = None


class MLXWhisperASR:
    """
    MLX Whisper Automatic Speech Recognition for Apple Silicon.
    
    Uses Apple's MLX framework which automatically leverages:
    - CoreML (Neural Engine) when available - fastest
    - MPS (Metal GPU) as fallback - fast
    
    This is significantly faster than faster-whisper on Apple Silicon.
    """
    
    _mlx_available = None
    
    def __init__(self, model_size: str = "large-v3"):
        """
        Initialize MLX Whisper ASR.
        
        Args:
            model_size: Model size (e.g., "large-v3", "medium", "small", "base", "tiny")
        """
        self.model_size = model_size
        self.model = None
        self.is_loaded = False
        self._backend_type = None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if MLX Whisper is available on this system."""
        if cls._mlx_available is not None:
            return cls._mlx_available
        
        # Only available on macOS with Apple Silicon
        if sys.platform != 'darwin':
            logger.info("MLX Whisper not available: Not macOS")
            cls._mlx_available = False
            return False
        
        # Check for ARM64 architecture
        import platform
        if platform.machine() != 'arm64':
            logger.info("MLX Whisper not available: Not Apple Silicon (ARM64)")
            cls._mlx_available = False
            return False
        
        # === Setup MLX paths for PyInstaller packaged app ===
        if getattr(sys, 'frozen', False):
            import os
            
            # Build list of possible mlx lib paths
            possible_paths = []
            
            # macOS .app bundle structure
            exe_dir = Path(sys.executable).parent  # Contents/MacOS
            contents_dir = exe_dir.parent  # Contents/
            possible_paths.append(contents_dir / 'Frameworks' / 'mlx' / 'lib')
            possible_paths.append(contents_dir / 'Frameworks' / 'mlx')
            possible_paths.append(contents_dir / 'Resources' / 'mlx' / 'lib')
            possible_paths.append(contents_dir / 'Resources' / 'mlx')
            
            # PyInstaller onefile _MEIPASS structure
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
                possible_paths.append(base_path / 'mlx' / 'lib')
                possible_paths.append(base_path / 'mlx')
                possible_paths.append(base_path)
            
            for mlx_lib_path in possible_paths:
                metallib_path = mlx_lib_path / 'mlx.metallib'
                if metallib_path.exists():
                    # Set environment variables for MLX
                    os.environ['DYLD_LIBRARY_PATH'] = str(mlx_lib_path) + ':' + os.environ.get('DYLD_LIBRARY_PATH', '')
                    os.environ['MLX_METAL_PATH'] = str(metallib_path)
                    logger.info(f"🍎 [Packaged App] Set MLX_METAL_PATH to: {metallib_path}")
                    break
            else:
                logger.warning(f"MLX metallib not found in packaged app. Searched: {[str(p) for p in possible_paths]}")
        
        # Try to import mlx.core and test Metal functionality
        try:
            import mlx.core as mx
            
            # Actually test Metal is working
            if mx.metal.is_available():
                # Quick test to ensure Metal works
                test_arr = mx.array([1.0, 2.0, 3.0])
                result = mx.sum(test_arr)
                mx.eval(result)  # Force evaluation on Metal
                logger.info("✅ MLX Metal test passed")
            else:
                logger.warning("MLX Metal not available")
                cls._mlx_available = False
                return False
                
        except Exception as e:
            logger.warning(f"MLX Whisper not available (MLX core failed): {e}")
            cls._mlx_available = False
            return False
        
        # Now try to import mlx_whisper
        try:
            import mlx_whisper
            logger.info("✅ MLX Whisper is available (Apple Silicon optimized)")
            cls._mlx_available = True
            return True
        except ImportError as e:
            logger.warning(f"MLX Whisper not available: {e}")
            cls._mlx_available = False
            return False
    
    def get_backend_type(self) -> str:
        """Get the current backend type being used."""
        if self._backend_type:
            return self._backend_type
        
        if not self.is_available():
            return "cpu"
        
        # MLX automatically uses the best available backend
        try:
            import mlx.core as mx
            # Check if we're using GPU (Metal)
            if mx.metal.is_available():
                self._backend_type = "mps"  # Metal/GPU
                logger.info("🍎 MLX using Metal (GPU) backend")
            else:
                self._backend_type = "cpu"
                logger.info("MLX using CPU backend")
            return self._backend_type
        except Exception as e:
            logger.warning(f"Could not determine MLX backend: {e}")
            self._backend_type = "cpu"  # Fallback to CPU
            return "cpu"
    
    def load_model(self, progress_callback=None):
        """Load MLX Whisper model.
        
        Args:
            progress_callback: Optional callback(message: str) for progress updates
        """
        if self.is_loaded:
            logger.warning("Model already loaded")
            return

        if not self.is_available():
            raise RuntimeError("MLX Whisper is not available on this system")

        logger.info(f"🍎 Loading MLX Whisper model: {self.model_size}")
        
        if progress_callback:
            progress_callback("正在準備 AI 工具...")

        try:
            import mlx_whisper
            from huggingface_hub import snapshot_download, try_to_load_from_cache

            # MLX Whisper uses model paths like "mlx-community/whisper-large-v3-mlx"
            model_path = f"mlx-community/whisper-{self.model_size}-mlx"
            
            # Check if model is already cached
            cache_result = try_to_load_from_cache(model_path, "config.json")
            # cache_result is a file path if cached, None if not cached
            model_cached = cache_result is not None
            
            if not model_cached:
                # Model needs download - show progress
                logger.info(f"Downloading model: {model_path} (this may take several minutes)")
                if progress_callback:
                    progress_callback("AI 工具下載中（約 3-5 GB），請稍候...")
                
                try:
                    # Custom tqdm class to report download progress via callback
                    from tqdm import tqdm
                    
                    class ProgressTqdm(tqdm):
                        def __init__(self_tqdm, *args, **kwargs):
                            super().__init__(*args, **kwargs)
                            self_tqdm.callback = progress_callback
                        
                        def update(self_tqdm, n=1):
                            super().update(n)
                            if self_tqdm.total and self_tqdm.total > 0 and self_tqdm.callback:
                                # Calculate download progress
                                downloaded_mb = self_tqdm.n / (1024 * 1024)
                                total_mb = self_tqdm.total / (1024 * 1024)
                                msg = f"AI 工具下載中... {downloaded_mb:.0f}MB / {total_mb:.0f}MB"
                                self_tqdm.callback(msg)
                    
                    # Download with progress tracking
                    snapshot_download(
                        repo_id=model_path, 
                        allow_patterns=["*.safetensors", "*.json", "*.npz"],
                        tqdm_class=ProgressTqdm if progress_callback else tqdm
                    )
                    logger.info("✅ Model downloaded successfully")
                    if progress_callback:
                        progress_callback("AI 工具下載完成！")
                except Exception as e:
                    logger.warning(f"Model download issue: {e}")
                    if progress_callback:
                        progress_callback("AI 工具下載中...")
            else:
                logger.info("Model already cached, loading from cache...")
                if progress_callback:
                    progress_callback("正在加載 AI 工具...")

            # The model will be used when transcribing
            logger.info(f"Model path: {model_path}")

            self.is_loaded = True
            self.model_path = model_path

            backend = self.get_backend_type()
            logger.info(f"⚡ MLX Whisper ready on {backend.upper()}")
            
            if progress_callback:
                progress_callback("AI 工具就緒！")

        except Exception as e:
            logger.error(f"Failed to load MLX Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: str = "yue",
        task: str = "transcribe",
        initial_prompt: Optional[str] = None,
        word_timestamps: bool = True,
        **kwargs
    ) -> Dict:
        """
        Transcribe audio using MLX Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., "yue" for Cantonese)
            task: "transcribe" or "translate"
            initial_prompt: Optional prompt to guide the model
            word_timestamps: Enable word-level timestamps
            **kwargs: Additional options
            
        Returns:
            Dict with transcription results
        """
        if not self.is_loaded:
            self.load_model()
        
        audio_path = Path(audio_path)
        logger.info(f"🍎 Transcribing with MLX Whisper: {audio_path.name}")
        
        # Default Cantonese vocabulary (約 60 個常用廣東話口語字)
        DEFAULT_CANTONESE_VOCAB = (
            "佢、喺、睇、嘅、咁、啲、咗、嚟、冇、諗、唔、咩、乜、點、邊、噉、嗰、呢、哋、咪、"
            "囉、喎、啦、㗎、吖、喇、嘞、嘢、喱、嗱、呀、咋、嘛、啱、攞、擺、執、嬲、瞓、慳、"
            "揀、搵、嗌、靚、掂、叻、畀、嚿、啖、撐、揸、嗮、噃、咧、嘥、揈、仲、系、嚫、唞"
        )
        
        # Domain-specific vocabulary for specialized content
        # 修復字幕辨識錯誤：新增旅遊、購物、日常生活常用詞彙
        DOMAIN_VOCAB = {
            "music": "歌詞、旋律、編曲、和弦、音階、作曲、填詞、主歌、副歌、間奏、前奏、尾奏、節拍、拍子、調、升Key、降Key、唱片、專輯、單曲、MV、音樂會、演唱會",
            "business": "營銷、客戶、銷售、利潤、成本、投資、股份、合作、談判、簽約、合同、項目、業務、市場、品牌、推廣、策略、競爭、優勢、增長",
            "daily": "飲茶、飲食、行街、睇戲、打機、返工、放假、拍拖、食飯、去街、買餸、煮飯、做家務、睇書、聽歌、運動、休息、放鬆、娛樂、消遣",
            "tech": "程式、編程、軟件、硬件、系統、網絡、伺服器、數據、算法、網站、應用、App、平台、開發、測試、部署、維護、優化、更新、升級",
            "travel": "上野、秋葉原、阿美橫丁、淺草、新宿、澀谷、銀座、築地、台場、富士山、箱根、京都、大阪、沖繩、北海道、酒店、旅館、機場、車站、景點、觀光、旅遊、行李箱、護照、簽證",
            "shopping": "商場、百貨公司、便利店、藥妝店、超市、手信、禮物、紀念品、化妝品、護膚品、figure、模型、公仔、電器、電子產品、名牌、打折、減價、特價、信用卡、現金、找換店"
        }
        
        if initial_prompt is None and language in ["yue", "zh"]:
            # Get language style from kwargs (passed from config)
            language_style = kwargs.pop("language_style", "formal")
            
            # Build prompt based on language style
            if language_style == "colloquial":
                # 口語模式：使用粵語口語字（強化版，明確要求粵語詞彙+常見誤判修正）
                base_prompt = (
                    f"以下係廣東話對白，請用粵語口語字幕，全程保持一致嘅口語風格。"
                    f"必須使用粵語詞彙：{DEFAULT_CANTONESE_VOCAB}。"
                    "例如：用「邊一個」唔好用「哪一個」，用「點解」唔好用「為什麼」，"
                    "用「乜嘢」唔好用「什麼」，用「邊度」唔好用「哪裡」。"
                    "常見詞彙正確寫法：「行李」、「過馬路」、「最後一日」、「好多嘢買」、"
                    "「figure」（模型）、「premium」（優質）、「執行李」、「阿美橫丁」。"
                    "數字正確讀法：「21」讀作「二十一」，唔係「尾21」。"
                )
                logger.info("📝 Using colloquial Cantonese style (口語) with correction hints")
            else:
                # 書面語模式：使用正式中文
                base_prompt = (
                    "以下是廣東話對白，請用正式書面中文字幕，"
                    "不要使用粵語口語字（如佢、喺、睇、嘅、咁、啲、咗等），"
                    "全程保持一致的書面語風格。"
                    "例如：使用「他在看」而不是「佢喺睇」，使用「這樣」而不是「噉」。"
                )
                logger.info("📝 Using formal written Chinese style (書面語)")
            
            # Check for domain-specific vocabulary from kwargs
            domain = kwargs.pop("domain", None)
            if domain and domain in DOMAIN_VOCAB:
                domain_vocab = DOMAIN_VOCAB[domain]
                base_prompt = f"{base_prompt}。{domain}相關詞彙：{domain_vocab}"
                logger.info(f"📚 Using domain vocab: {domain}")
            
            # Check for custom prompt from kwargs (passed from config)
            custom_prompt = kwargs.pop("custom_prompt", "")
            if custom_prompt:
                initial_prompt = f"{base_prompt}。用戶指定詞彙：{custom_prompt}。"
                logger.info(f"🎤 Using custom prompt: {custom_prompt[:50]}...")
            else:
                initial_prompt = f"{base_prompt}。"
        

        
        try:
            import mlx_whisper
            import os  # Import os at the top of try block
            
            # Disable tqdm progress bars in packaged environment to avoid Broken pipe errors
            # when stdout is closed in GUI apps
            if getattr(sys, 'frozen', False):
                os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
                os.environ['TQDM_DISABLE'] = '1'
            
            # === CRITICAL FIX: Monkeypatch mlx_whisper to use full ffmpeg path ===
            # Problem: mlx_whisper.audio.load_audio() calls subprocess.run(['ffmpeg', ...])
            # In packaged .app bundles, subprocess doesn't find 'ffmpeg' even if in PATH
            # Solution: Patch load_audio to use absolute ffmpeg path
            import mlx_whisper.audio
            from core.path_setup import get_ffmpeg_path
            
            _original_load_audio = mlx_whisper.audio.load_audio
            ffmpeg_full_path = get_ffmpeg_path()
            
            def _patched_load_audio(file: str, sr: int = 16000):
                """Patched load_audio that uses full ffmpeg path."""
                import subprocess
                import numpy as np
                import mlx.core as mx
                
                cmd = [
                    ffmpeg_full_path,  # Use absolute path instead of 'ffmpeg'
                    "-nostdin",
                    "-threads", "0",
                    "-i", file,
                    "-f", "s16le",
                    "-ac", "1",
                    "-acodec", "pcm_s16le",
                    "-ar", str(sr),
                    "-"
                ]
                
                try:
                    out = subprocess.run(cmd, capture_output=True, check=True).stdout
                except FileNotFoundError:
                    raise FileNotFoundError(
                        f"FFmpeg not found at: {ffmpeg_full_path}\n"
                        f"Please install FFmpeg: brew install ffmpeg"
                    )
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")
                
                # CRITICAL FIX: Return MLX array, not NumPy array!
                # This matches the original mlx_whisper.audio.load_audio return type
                return mx.array(np.frombuffer(out, np.int16)).flatten().astype(mx.float32) / 32768.0
            
            # Apply the patch
            mlx_whisper.audio.load_audio = _patched_load_audio
            logger.info(f"🔧 Patched mlx_whisper to use ffmpeg at: {ffmpeg_full_path}")

            
            # Transcribe using MLX Whisper with optimized parameters
            # NOTE: MLX Whisper doesn't support beam_size/best_of yet
            # 修復字幕辨識錯誤：調整參數以提升準確度
            result = mlx_whisper.transcribe(
                str(audio_path),
                path_or_hf_repo=self.model_path,
                language=language,
                task=task,
                initial_prompt=initial_prompt,
                word_timestamps=word_timestamps,
                # Optimization parameters (MLX compatible only)
                temperature=0.0,                    # Deterministic output (no randomness)
                condition_on_previous_text=True,    # Use context from previous segments
                no_speech_threshold=0.4,            # 降低 no_speech 閾值（0.6→0.4），減少靜音誤判
                logprob_threshold=-0.8,             # 降低 logprob 閾值（-1.0→-0.8），保留更多低信心段落
                compression_ratio_threshold=2.4,    # 放寬壓縮率閾值（2.4→2.4），減少重複檢測誤殺
                **kwargs
            )
            
            # Extract segments
            segment_list = self._extract_segments(result.get('segments', []), language)
            
            # Full text
            full_text = result.get('text', '')
            
            logger.info(f"⚡ MLX transcription complete: {len(segment_list)} segments")
            
            return {
                'text': full_text,
                'segments': segment_list,
                'language': result.get('language', language),
                'language_probability': 1.0,
                'backend': 'mlx-whisper'
            }
            
        except Exception as e:
            logger.error(f"MLX transcription failed: {e}")
            raise
    
    def _extract_segments(self, segments: List[Dict], language: str) -> List[MLXTranscriptionSegment]:
        """
        Extract segments from MLX Whisper output with confidence filtering.
        Filters out low-confidence segments (background music, noise).
        """
        segment_list = []
        filtered_count = 0
        
        for i, seg in enumerate(segments):
            # Filter out segments with high no_speech_prob (likely background noise/music)
            no_speech_prob = seg.get('no_speech_prob', 0.0)
            if no_speech_prob > 0.6:  # 60% threshold
                filtered_count += 1
                logger.debug(f"Filtered segment {i}: no_speech_prob={no_speech_prob:.2f}")
                continue
            
            words = []
            if 'words' in seg and seg['words']:
                words = [
                    {
                        'word': w.get('word', ''),
                        'start': w.get('start', 0),
                        'end': w.get('end', 0),
                        'probability': w.get('probability', 1.0)
                    }
                    for w in seg['words']
                ]
            
            segment = MLXTranscriptionSegment(
                id=len(segment_list),  # Use filtered index
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', ''),
                confidence=1.0 - no_speech_prob,  # Convert to confidence score
                language=language,
                words=words
            )
            segment_list.append(segment)
        
        if filtered_count > 0:
            logger.info(f"🔍 Filtered {filtered_count} low-confidence segments")
        
        return segment_list
    
    def cleanup(self):
        """Clean up resources."""
        self.model = None
        self.is_loaded = False
        
        # Clear MLX memory
        try:
            import gc
            gc.collect()
        except:
            pass
        
        logger.info("MLX Whisper resources cleaned up")
    
    def unload_model(self):
        """Unload the model (alias for cleanup for API compatibility)."""
        self.cleanup()
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        return {
            'model_size': self.model_size,
            'is_loaded': self.is_loaded,
            'backend': 'mlx-whisper',
            'device': self.get_backend_type(),
            'platform': 'Apple Silicon',
            'available': self.is_available()
        }


def get_best_whisper_backend(config=None, model_size: str = "large-v3"):
    """
    Get the best available Whisper backend for the current system.
    
    Priority:
    1. MLX Whisper (CoreML/MPS) - Apple Silicon
    2. faster-whisper (CPU) - Fallback
    
    Args:
        config: Application config (for faster-whisper fallback)
        model_size: Model size to use
        
    Returns:
        Whisper ASR instance (either MLXWhisperASR or WhisperASR)
    """
    # Try MLX Whisper first (Apple Silicon)
    if MLXWhisperASR.is_available():
        logger.info("🍎 Using MLX Whisper (Apple Silicon optimized)")
        return MLXWhisperASR(model_size=model_size)
    
    # Fallback to faster-whisper
    logger.info("Using faster-whisper (CPU) as fallback")
    from models.whisper_asr import WhisperASR
    if config is None:
        from core.config import Config
        config = Config()
    return WhisperASR(config, model_size=model_size)


# Test function
if __name__ == "__main__":
    print(f"MLX Whisper available: {MLXWhisperASR.is_available()}")
    
    if MLXWhisperASR.is_available():
        asr = MLXWhisperASR()
        print(f"Backend type: {asr.get_backend_type()}")
        print(f"Model info: {asr.get_model_info()}")
    else:
        print("MLX Whisper not available, would use faster-whisper fallback")
