"""
Translation Model using MarianMT for offline English to Chinese translation.
"""

import torch
from transformers import MarianMTModel, MarianTokenizer
from models.model_manager import ModelManager
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger()

class TranslationModel(ModelManager):
    """
    Offline English to Chinese translation using MarianMT.
    """
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.tokenizer = None
        self.model_name = "Helsinki-NLP/opus-mt-en-zh"
        
    def load_model(self):
        """Load MarianMT model and tokenizer."""
        if self.is_loaded:
            return

        logger.info(f"Loading Translation model: {self.model_name}")
        
        try:
            # Load tokenizer and model
            self.tokenizer = MarianTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.get_model_cache_dir())
            )
            
            self.model = MarianMTModel.from_pretrained(
                self.model_name,
                cache_dir=str(self.get_model_cache_dir())
            )
            
            # Move to device
            self.model.to(self.device)
            self.is_loaded = True
            
            logger.info(f"Translation model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load Translation model: {e}")
            raise

    def unload_model(self):
        """Unload model to free memory."""
        if not self.is_loaded:
            return
            
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    def translate(self, text: str) -> str:
        """
        Translate English text to Chinese.
        
        Args:
            text: English text to translate
            
        Returns:
            Translated Chinese text
        """
        if not text or not text.strip():
            return text
            
        if not self.is_loaded:
            self.load_model()
            
        try:
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate translation
            translated = self.model.generate(**inputs)
            
            # Decode
            result = self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
            
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
