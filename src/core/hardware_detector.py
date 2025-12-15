"""
Hardware detection for Canto-beats V2.0.

Detects GPU availability and VRAM to determine optimal performance profile.
"""

import torch
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from utils.logger import setup_logger

logger = setup_logger()


class PerformanceTier(Enum):
    """Performance tier enumeration."""
    ULTIMATE = "ultimate"      # >16GB VRAM - Full features
    MAINSTREAM = "mainstream"  # 10-16GB VRAM - Full features
    ENTRY = "entry"            # 6-10GB VRAM - Basic features
    CPU_ONLY = "cpu_only"      # <6GB or no GPU - Basic features


@dataclass
class PerformanceProfile:
    """Performance profile configuration based on hardware."""
    
    tier: PerformanceTier
    device: str  # "cuda" or "cpu"
    vram_gb: float
    
    # ASR Configuration
    asr_model: str
    asr_compute_type: str  # "float16", "int8", "float32"
    
    # LLM-A (Lightweight) Configuration
    llm_a_model: str
    llm_a_quantization: Optional[str]  # "fp16", "4bit", "3bit", None
    llm_a_enabled: bool
    
    # LLM-B (Heavyweight) Configuration
    llm_b_model: str
    llm_b_quantization: Optional[str]
    llm_b_enabled: bool
    
    # Feature Flags
    formal_translation_enabled: bool  # 書面語翻譯
    bilingual_output_enabled: bool    # 雙語對照
    
    @property
    def description(self) -> str:
        """Human-readable description of the profile."""
        descriptions = {
            PerformanceTier.ULTIMATE: "究極性能模式 - 三模型GPU共存，全功能",
            PerformanceTier.MAINSTREAM: "主流性能模式 - 三模型GPU共存，全功能",
            PerformanceTier.ENTRY: "入門性能模式 - 雙模型GPU共存，基礎校對",
            PerformanceTier.CPU_ONLY: "純CPU模式 - 雙模型CPU運行，基礎校對",
        }
        return descriptions.get(self.tier, "未知模式")


class HardwareDetector:
    """
    Detects hardware capabilities and determines optimal performance profile.
    
    Run at application startup to configure the processing pipeline.
    """
    
    # VRAM thresholds (in GB)
    ULTIMATE_THRESHOLD = 16.0
    MAINSTREAM_THRESHOLD = 10.0
    ENTRY_THRESHOLD = 6.0
    
    # Model configurations per tier
    PROFILES = {
        PerformanceTier.ULTIMATE: {
            "asr_model": "large-v3",
            "asr_compute_type": "float16",
            "llm_a_model": "Qwen/Qwen2.5-7B-Instruct",  # 7B model - good balance
            "llm_a_quantization": "fp16",  # Full precision with 16GB+ VRAM
            "llm_b_model": "",
            "llm_b_quantization": None,
            "llm_b_enabled": False,
            "formal_translation_enabled": True,
            "bilingual_output_enabled": True,
        },
        PerformanceTier.MAINSTREAM: {
            "asr_model": "large-v3",
            "asr_compute_type": "int8",
            "llm_a_model": "Qwen/Qwen2.5-7B-Instruct",  # 7B model - good balance
            "llm_a_quantization": "int8",  # INT8 for 10-16GB VRAM
            "llm_b_model": "",
            "llm_b_quantization": None,
            "llm_b_enabled": False,
            "formal_translation_enabled": True,
            "bilingual_output_enabled": True,
        },
        PerformanceTier.ENTRY: {
            "asr_model": "large-v3",
            "asr_compute_type": "int8",
            "llm_a_model": "Qwen/Qwen2.5-3B-Instruct",  # 3B model - faster and lighter
            "llm_a_quantization": "4bit",  # 4-bit for 6-10GB VRAM (your RTX 3070 Ti)
            "llm_b_model": "",
            "llm_b_quantization": None,
            "llm_b_enabled": False,
            "formal_translation_enabled": True,
            "bilingual_output_enabled": True,
        },
        PerformanceTier.CPU_ONLY: {
            "asr_model": "distil-medium.en",  # Smaller model for CPU
            "asr_compute_type": "float32",
            "llm_a_model": "Qwen/Qwen2.5-3B-Instruct",  # Keep 3B for CPU
            "llm_a_quantization": None,  # Full precision on CPU
            "llm_b_model": "",
            "llm_b_quantization": None,
            "llm_b_enabled": False,
            "formal_translation_enabled": False,
            "bilingual_output_enabled": False,
        },
    }
    
    def __init__(self):
        self._cached_profile: Optional[PerformanceProfile] = None
    
    def detect(self, force_cpu: bool = False) -> PerformanceProfile:
        """
        Detect hardware and return optimal performance profile.
        
        Args:
            force_cpu: Force CPU-only mode regardless of GPU availability.
            
        Returns:
            PerformanceProfile with optimal configuration.
        """
        if self._cached_profile is not None and not force_cpu:
            return self._cached_profile
        
        device, vram_gb = self._detect_gpu()
        
        if force_cpu:
            device = "cpu"
            vram_gb = 0.0
            logger.info("Forced CPU mode")
        
        tier = self._determine_tier(vram_gb, device)
        profile = self._create_profile(tier, device, vram_gb)
        
        self._cached_profile = profile
        self._log_profile(profile)
        
        return profile
    
    def _detect_gpu(self) -> Tuple[str, float]:
        """
        Detect GPU availability and VRAM.
        
        Returns:
            Tuple of (device, vram_in_gb)
        """
        if not torch.cuda.is_available():
            logger.info("CUDA not available, using CPU mode")
            return "cpu", 0.0
        
        try:
            # Get GPU properties
            device_id = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device_id)
            
            vram_bytes = props.total_memory
            vram_gb = vram_bytes / (1024 ** 3)
            
            gpu_name = props.name
            logger.info(f"GPU detected: {gpu_name}")
            logger.info(f"VRAM capacity: {vram_gb:.2f} GB")
            
            return "cuda", vram_gb
            
        except Exception as e:
            logger.warning(f"GPU檢測失敗: {e}，將使用CPU模式")
            return "cpu", 0.0
    
    def _determine_tier(self, vram_gb: float, device: str) -> PerformanceTier:
        """Determine performance tier based on VRAM."""
        if device == "cpu" or vram_gb < self.ENTRY_THRESHOLD:
            return PerformanceTier.CPU_ONLY
        elif vram_gb < self.MAINSTREAM_THRESHOLD:
            return PerformanceTier.ENTRY
        elif vram_gb < self.ULTIMATE_THRESHOLD:
            return PerformanceTier.MAINSTREAM
        else:
            return PerformanceTier.ULTIMATE
    
    def _create_profile(
        self, 
        tier: PerformanceTier, 
        device: str, 
        vram_gb: float
    ) -> PerformanceProfile:
        """Create a PerformanceProfile from tier configuration."""
        config = self.PROFILES[tier]
        
        return PerformanceProfile(
            tier=tier,
            device=device,
            vram_gb=vram_gb,
            asr_model=config["asr_model"],
            asr_compute_type=config["asr_compute_type"],
            llm_a_model=config["llm_a_model"],
            llm_a_quantization=config["llm_a_quantization"],
            llm_a_enabled=True,  # Always enabled
            llm_b_model=config["llm_b_model"],
            llm_b_quantization=config["llm_b_quantization"],
            llm_b_enabled=config["llm_b_enabled"],
            formal_translation_enabled=config["formal_translation_enabled"],
            bilingual_output_enabled=config["bilingual_output_enabled"],
        )
    
    def _log_profile(self, profile: PerformanceProfile):
        """Log the selected performance profile."""
        logger.info("=" * 50)
        logger.info(f"Performance Profile: {profile.description}")
        logger.info(f"   Device: {profile.device.upper()}")
        logger.info(f"   VRAM: {profile.vram_gb:.2f} GB")
        logger.info(f"   ASR Model: {profile.asr_model} ({profile.asr_compute_type})")
        logger.info(f"   LLM-A: {profile.llm_a_model} ({profile.llm_a_quantization or 'full'})")
        if profile.llm_b_enabled:
            logger.info(f"   LLM-B: {profile.llm_b_model} ({profile.llm_b_quantization})")
        else:
            logger.info("   LLM-B: Disabled")
        logger.info(f"   Formal translation: {'Enabled' if profile.formal_translation_enabled else 'Disabled'}")
        logger.info(f"   Bilingual output: {'Enabled' if profile.bilingual_output_enabled else 'Disabled'}")
        logger.info("=" * 50)
    
    def get_vram_gb(self) -> float:
        """Get available VRAM in GB."""
        _, vram = self._detect_gpu()
        return vram
    
    def get_device(self) -> str:
        """Get the detected device type."""
        device, _ = self._detect_gpu()
        return device
    
    @staticmethod
    def get_available_vram() -> float:
        """Get currently available (free) VRAM in GB."""
        if not torch.cuda.is_available():
            return 0.0
        
        try:
            free_memory = torch.cuda.mem_get_info()[0]
            return free_memory / (1024 ** 3)
        except Exception:
            return 0.0


# Singleton instance for application-wide use
_detector_instance: Optional[HardwareDetector] = None


def get_hardware_detector() -> HardwareDetector:
    """Get the global HardwareDetector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = HardwareDetector()
    return _detector_instance


def detect_performance_profile(force_cpu: bool = False) -> PerformanceProfile:
    """
    Convenience function to detect and return the optimal performance profile.
    
    Args:
        force_cpu: Force CPU-only mode.
        
    Returns:
        PerformanceProfile for the current hardware.
    """
    return get_hardware_detector().detect(force_cpu=force_cpu)


if __name__ == "__main__":
    # Test hardware detection
    profile = detect_performance_profile()
    print(f"\nDetected Profile: {profile.tier.value}")
    print(f"Device: {profile.device}")
    print(f"VRAM: {profile.vram_gb:.2f} GB")
