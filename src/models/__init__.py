"""
AI Models package for Canto-beats.

Note: TranslationModel is NOT imported here to avoid triggering
full transformers loading at startup. Import it directly when needed:
    from models.translation_model import TranslationModel
"""

from .model_manager import ModelManager
from .whisper_asr import WhisperASR
from .vad_processor import VADProcessor

# TranslationModel uses MarianMT which triggers heavy transformers loading
# Do NOT import it here - import directly when needed

__all__ = [
    'ModelManager',
    'WhisperASR',
    'VADProcessor',
    # 'TranslationModel',  # Import directly to avoid startup overhead
]

