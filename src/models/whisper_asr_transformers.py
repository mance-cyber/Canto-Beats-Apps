"""
Whisper Automatic Speech Recognition (ASR) integration.

Provides Cantonese speech-to-text using Hugging Face Transformers.
Supports Cantonese-finetuned models like alvanlii/whisper-small-cantonese.
"""

import os
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Union
from dataclasses import dataclass

from transformers import (
    WhisperProcessor, 
    WhisperForConditionalGeneration,
    pipeline
)

from models.model_manager import ModelManager
from core.config import Config
from utils.logger import setup_logger
from utils.audio_utils import AudioPreprocessor


logger = setup_logger()


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing information."""
    
    id: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str
    confidence: float = 1.0
    language: str = "yue"
    words: List[Dict] = None  # Word-level timestamps


class WhisperASR(ModelManager):
    """
    Whisper Automatic Speech Recognition for Cantonese.
    
    Uses Hugging Face Transformers with Cantonese-finetuned models.
    
    Supports:
    - Cantonese-specific models (alvanlii/whisper-small-cantonese, khleeloo/whisper-large-v3-cantonese)
    - Official OpenAI Whisper models as fallback
    - Word-level timestamps
    - GPU acceleration with FP16
    - Optimized inference with Flash Attention
    """
    
    def __init__(self, config: Config, model_id: Optional[str] = None):
        """
        Initialize Whisper ASR.
        
        Args:
            config: Application configuration
            model_id: Model ID override (default from config)
        """
        super().__init__(config)
        
        self.audio_preprocessor = AudioPreprocessor()
        
        # Determine model ID from config
        if model_id:
            self.model_id = model_id
        elif config.get('use_cantonese_model', True):
            # Use Cantonese-specific model based on build type
            build_type = config.get('build_type', 'lite')
            if build_type == 'flagship':
                self.model_id = config.get('cantonese_model_flagship', 'khleeloo/whisper-large-v3-cantonese')
            else:
                self.model_id = config.get('cantonese_model_lite', 'alvanlii/whisper-small-cantonese')
        else:
            # Fallback to official OpenAI Whisper
            model_size = config.get('whisper_model', 'base')
            self.model_id = f"openai/whisper-{model_size}"
        
        # Determine compute type
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model and processor
        self.processor = None
        
        logger.info(f"Whisper ASR initialized with model: {self.model_id}")
        logger.info(f"Device: {self.device}, dtype: {self.torch_dtype}")
    
    def load_model(self):
        """Load Whisper model using Transformers."""
        if self.is_loaded:
            logger.warning("Model already loaded")
            return
        
        logger.info(f"Loading Whisper model: {self.model_id}")
        
        try:
            # Load processor
            self.processor = WhisperProcessor.from_pretrained(
                self.model_id,
                cache_dir=str(self.get_model_cache_dir())
            )
            
            # Load model with optimizations
            self.model = WhisperForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                attn_implementation="sdpa",  # Flash Attention for speed
                cache_dir=str(self.get_model_cache_dir())
            ).to(self.device)
            
            self.is_loaded = True
            logger.info(f"Whisper model loaded successfully on {self.device}")
            logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()) / 1e6:.1f}M")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def unload_model(self):
        """Unload Whisper model and free memory."""
        if not self.is_loaded:
            return
        
        logger.info("Unloading Whisper model")
        
        del self.model
        del self.processor
        self.model = None
        self.processor = None
        self.is_loaded = False
        
        # Clear GPU cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
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
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: "yue" for Cantonese)
            task: "transcribe" or "translate"
            initial_prompt: Optional prompt to guide the model
            word_timestamps: Enable word-level timestamps (WIP)
            **kwargs: Additional options
            
        Returns:
            Dict with transcription results
        """
        if not self.is_loaded:
            self.load_model()
        
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Validate audio file
        if not self.audio_preprocessor.validate_audio_file(audio_path):
            raise ValueError(f"Invalid audio file: {audio_path}")
        
        # Cantonese-specific prompt with rich vocabulary
        if initial_prompt is None and language in ["yue", "zh"]:
            initial_prompt = "以下係廣東話對白，請用粵語口語字幕：佢、喺、睇、嘅、咁、啲、咗、嚟、冇、諗、唔、咩、乜、點、邊、噉、嗰、呢、哋、咪、囉、喎、啦、㗎、吖。"
        
        try:
            # Load and preprocess audio
            import librosa
            audio_array, sr = librosa.load(str(audio_path), sr=16000)
            
            # Process audio
            inputs = self.processor(
                audio_array,
                sampling_rate=sr,
                return_tensors="pt"
            ).to(self.device)
            
            # Set language for decoder
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                language=language if language != "yue" else "zh",  # Use "zh" for Cantonese
                task=task
            )
            
            # Generate transcription
            with torch.no_grad():
                generated_ids = self.model.generate(
                    inputs.input_features,
                    forced_decoder_ids=forced_decoder_ids,
                    max_new_tokens=448,
                    num_beams=self.config.get('beam_size', 5),
                    return_dict_in_generate=True,
                    output_scores=True,
                )
            
            # Decode transcription
            transcription = self.processor.batch_decode(
                generated_ids.sequences,
                skip_special_tokens=True
            )[0]
            
            logger.info(f"Transcription complete: {len(transcription)} characters")
            
            # Create a single segment for now
            # TODO: Implement proper segmentation based on VAD
            segment = TranscriptionSegment(
                id=0,
                start=0.0,
                end=len(audio_array) / sr,
                text=transcription,
                confidence=1.0,
                language=language,
                words=None  # Word timestamps not yet implemented
            )
            
            return {
                'text': transcription,
                'segments': [segment],
                'language': language,
                'language_probability': 1.0
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def detect_language(self, audio_path: Union[str, Path]) -> str:
        """
        Detect the spoken language in audio.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Detected language code
        """
        if not self.is_loaded:
            self.load_model()
        
        logger.info(f"Detecting language: {audio_path}")
        
        try:
            # For Cantonese models, always return Cantonese
            if "cantonese" in self.model_id.lower():
                logger.info("Using Cantonese model, defaulting to 'yue'")
                return 'yue'
            
            # For generic models, use Transformers pipeline
            # (Language detection is complex, for now just default to yue)
            logger.warning("Language detection not fully implemented, defaulting to 'yue'")
            return 'yue'
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            logger.warning("Defaulting to 'yue'")
            return 'yue'
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dict with model information
        """
        return {
            'model_id': self.model_id,
            'is_loaded': self.is_loaded,
            'is_cantonese': 'cantonese' in self.model_id.lower(),
            'device': str(self.device),
            'torch_dtype': str(self.torch_dtype),
            'backend': 'Hugging Face Transformers',
            **self.get_device_info()
        }


def test_whisper():
    """Test Whisper ASR with sample audio file."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.models.whisper_asr_transformers <audio_file>")
        return
    
    audio_file = sys.argv[1]
    
    # Initialize
    from core.config import Config
    config = Config()
    
    asr = WhisperASR(config)
    
    # Load model
    print("Loading model...")
    asr.load_model()
    
    print(f"Model info: {asr.get_model_info()}")
    
    # Detect language
    print("\nDetecting language...")
    lang = asr.detect_language(audio_file)
    print(f"Detected: {lang}")
    
    # Transcribe
    print("\nTranscribing...")
    result = asr.transcribe(audio_file, language=lang)
    
    print(f"\nTranscription:")
    print(result['text'])
    
    print(f"\nSegments ({len(result['segments'])}):")
    for seg in result['segments'][:5]:  # Show first 5
        print(f"  [{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}")
    
    # Cleanup
    asr.cleanup()
    print("\nDone!")


if __name__ == "__main__":
    test_whisper()
