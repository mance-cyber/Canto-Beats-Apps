"""
Configuration management for Canto-beats
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """Application configuration"""
    
    # Version info
    version: str = "1.0.0a"
    build_type: str = "lite"  # "lite" or "flagship"
    
    # First-time flags
    first_transcription_done: bool = False  # Track if user has ever transcribed
    
    # Paths
    app_dir: str = ""
    models_dir: str = ""
    data_dir: str = ""
    cache_dir: str = ""
    
    # AI Models
    whisper_model: str = "large-v3"  # Best accuracy model
    use_cantonese_model: bool = True  # Use Cantonese-finetuned models from HuggingFace
    cantonese_model_flagship: str = "khleeloo/whisper-large-v3-cantonese"
    cantonese_model_lite: str = "alvanlii/whisper-small-cantonese"
    whisper_custom_prompt: str = ""  # User-defined custom prompt for Whisper (e.g., singer names, song titles)
    vad_model: str = "silero_vad"
    device: str = "auto"  # Auto-detect: MPS (Apple Silicon), CUDA, or CPU
    
    # VAD Settings
    # VAD Settings
    vad_threshold: float = 0.45  # Voice detection threshold (0.0-1.0) - Optimized for sensitivity
    min_silence_duration_ms: int = 400  # Minimum silence to split sentences (reduced to 350-500ms for fast speech)
    min_speech_duration_ms: int = 200  # Minimum speech duration (reduced to 150-200ms)
    vad_speech_pad_ms: int = 180  # Padding around speech segments (reduced to 150-200ms)
    
    
    # Subtitle Segmentation Settings (Optimized for 9:16 vertical video)
    # 修復字幕過度合併問題：進一步縮短參數，保持 1-2 句短字幕
    subtitle_max_chars: int = 15  # Maximum characters per subtitle line (18→15，強制更短)
    subtitle_max_gap: float = 0.2  # Maximum gap between segments to merge (0.3→0.2s，減少合併)

    # ==================== 斷句邊界優化配置 ====================
    # 解決「斬頭斬尾」問題：為時間戳添加安全邊距
    segment_start_pad_ms: int = 100  # 開頭安全邊距 (毫秒)，防止句首被截斷
    segment_end_pad_ms: int = 150  # 結尾安全邊距 (毫秒)，防止句尾被截斷
    segment_particle_end_pad_ms: int = 200  # 粵語句尾詞額外邊距 (毫秒)，如「囉」「嘅」「啦」

    # LLM 智能斷句優化 (新增)
    enable_llm_sentence_optimization: bool = True  # 使用 LLM 檢測並合併語意不完整的句子

    # 終極轉錄模式
    enable_ultimate_transcription: bool = False  # 啟用終極模式（音頻增強 + 三階段轉錄 + 詞彙學習）
    
    # Subtitle Language Style
    subtitle_language_style: str = "colloquial"  # "formal" (書面語/正式中文) or "colloquial" (口語/粵語口語字)
    
    # Transcription Settings
    default_language: str = "yue"  # "yue" for Cantonese (ISO 639-3 code, supported by faster-whisper)
    enable_word_timestamps: bool = True
    beam_size: int = 5  # Default value for faster transcription speed
    
    # Processing settings
    confidence_threshold: float = 0.7
    max_video_size_gb: int = 50
    chunk_audio: bool = True  # Chunk long audio for processing
    max_audio_chunk_s: float = 30.0  # Maximum audio chunk length
    
    
    # Subtitle Line Splitting
    max_chars_enabled: bool = False  # Enable automatic line splitting
    max_chars_limit: int = 14  # Maximum characters per line when enabled

    # Scene Alignment
    scene_align_enabled: bool = False  # Enable automatic scene alignment after transcription
    scene_align_tolerance: float = 0.5  # Tolerance in seconds for aligning to scene cuts
    
    # UI settings
    theme: str = "dark"  # "dark" or "light"
    language: str = "zh_HK"
    
    # Performance
    use_gpu: bool = True
    num_threads: int = 4
    compute_type: str = "auto"  # "auto", "float16", "int8", "int8_float16" for faster-whisper


class Config:
    """Configuration manager"""
    
    def __init__(self):
        self.app_config = AppConfig()
        self._setup_paths()
        self._load_config()
    
    def _setup_paths(self):
        """Setup application directories"""
        # Get user's app data directory
        if os.name == 'nt':  # Windows
            app_data = Path(os.environ.get('APPDATA', ''))
        else:  # macOS/Linux
            app_data = Path.home() / '.config'
        
        # Create Canto-beats directories
        self.app_dir = app_data / 'Canto-beats'
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        self.models_dir = self.app_dir / 'models'
        self.models_dir.mkdir(exist_ok=True)
        
        self.data_dir = self.app_dir / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        self.cache_dir = self.app_dir / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
        
        # Update config
        self.app_config.app_dir = str(self.app_dir)
        self.app_config.models_dir = str(self.models_dir)
        self.app_config.data_dir = str(self.data_dir)
        self.app_config.cache_dir = str(self.cache_dir)
    
    def _load_config(self):
        """Load configuration from file"""
        config_file = self.app_dir / 'config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Update config with saved values
                    for key, value in data.items():
                        if hasattr(self.app_config, key):
                            setattr(self.app_config, key, value)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        config_file = self.app_dir / 'config.json'
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.app_config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self.app_config, key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        if hasattr(self.app_config, key):
            setattr(self.app_config, key, value)
            self.save_config()
    
    def is_model_cached(self, model_type: str = "whisper") -> bool:
        """
        Check if AI models are already cached locally.
        
        Args:
            model_type: "whisper", "llm", or "all"
            
        Returns:
            True if model(s) are cached, False if download is needed
        """
        from pathlib import Path
        import os
        
        # Check Whisper model cache (MLX Whisper uses huggingface cache)
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        whisper_cached = False
        
        # MLX Whisper model path
        mlx_whisper_folder = hf_cache / "models--mlx-community--whisper-large-v3-mlx"
        
        print(f"[DEBUG] Checking Whisper cache: {mlx_whisper_folder}")
        print(f"[DEBUG] Folder exists: {mlx_whisper_folder.exists()}")
        
        if mlx_whisper_folder.exists():
            # Check blobs directory for actual model content (weights.npz is ~3GB)
            blobs = mlx_whisper_folder / "blobs"
            if blobs.exists():
                blob_files = list(blobs.iterdir())
                # Need at least 1GB of content (weights.npz is ~3GB)
                total_size = sum(f.stat().st_size for f in blob_files if f.is_file())
                print(f"[DEBUG] Blobs total size: {total_size / 1_000_000_000:.2f} GB")
                if total_size > 1_000_000_000:  # At least 1GB
                    whisper_cached = True
                    print(f"[DEBUG] Whisper cached via blobs (size check passed)")
            
            # Also check snapshots for .npz or .safetensors files
            if not whisper_cached:
                snapshots = mlx_whisper_folder / "snapshots"
                if snapshots.exists():
                    for snapshot_dir in snapshots.iterdir():
                        if snapshot_dir.is_dir():
                            # Look for .npz (MLX format) or .safetensors
                            files = list(snapshot_dir.glob("*.npz")) + list(snapshot_dir.glob("*.safetensors"))
                            if files:
                                print(f"[DEBUG] Found model files in snapshot: {[f.name for f in files]}")
                                whisper_cached = True
                                break
        
        print(f"[DEBUG] Whisper cached: {whisper_cached}")
        
        # Check LLM model cache (Qwen/MLX Qwen)
        llm_cached = False
        if hf_cache.exists():
            for folder in hf_cache.iterdir():
                folder_name = folder.name.lower()
                # Check for both Transformers Qwen and MLX Qwen
                if "qwen" in folder_name:
                    # Verify model has actual content (not just empty folder)
                    blobs = folder / "blobs"
                    if blobs.exists():
                        blob_files = list(blobs.iterdir())
                        total_size = sum(f.stat().st_size for f in blob_files if f.is_file())
                        # Qwen 3B is ~5-6GB
                        if total_size > 1_000_000_000:  # At least 1GB
                            llm_cached = True
                            break
        
        if model_type == "whisper":
            return whisper_cached
        elif model_type == "llm":
            return llm_cached
        else:  # "all"
            return whisper_cached and llm_cached
