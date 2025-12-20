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
        
        # Try to import mlx_whisper
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
        
        if initial_prompt is None and language in ["yue", "zh"]:
            # Build prompt: base instruction + default vocab + user custom vocab
            base_prompt = f"以下係廣東話對白，請用粵語口語字幕：{DEFAULT_CANTONESE_VOCAB}"
            
            # Check for custom prompt from kwargs (passed from config)
            custom_prompt = kwargs.pop("custom_prompt", "")
            if custom_prompt:
                initial_prompt = f"{base_prompt}。用戶指定詞彙：{custom_prompt}。"
                logger.info(f"🎤 Using custom prompt: {custom_prompt[:50]}...")
            else:
                initial_prompt = f"{base_prompt}。"
        
        try:
            import mlx_whisper
            
            # Transcribe using MLX Whisper
            result = mlx_whisper.transcribe(
                str(audio_path),
                path_or_hf_repo=self.model_path,
                language=language,
                task=task,
                initial_prompt=initial_prompt,
                word_timestamps=word_timestamps,
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
        """Extract segments from MLX Whisper output."""
        segment_list = []
        
        for i, seg in enumerate(segments):
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
                id=i,
                start=seg.get('start', 0),
                end=seg.get('end', 0),
                text=seg.get('text', ''),
                confidence=seg.get('avg_logprob', 1.0) if 'avg_logprob' in seg else 1.0,
                language=language,
                words=words
            )
            segment_list.append(segment)
        
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
