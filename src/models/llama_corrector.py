"""
Llama Corrector for offline Cantonese text correction.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
import time

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from utils.logger import setup_logger
from core.config import Config

logger = setup_logger()

class LlamaCorrector:
    """
    Handles offline text correction using a local Llama model.
    Optimized for batch processing to speed up corrections.
    """
    
    def __init__(self, model_path: str, n_ctx: int = 512, n_gpu_layers: int = -1):
        self.model_path = model_path
        self.n_ctx = n_ctx  # Reduced for faster inference
        self.n_gpu_layers = n_gpu_layers  # -1 = all layers on GPU
        self.llm = None
        self.is_loaded = False
        
    def load_model(self):
        """Load the Llama model with GPU priority."""
        if self.is_loaded:
            return

        if Llama is None:
            raise ImportError("llama-cpp-python is not installed. Please install it to use offline correction.")
            
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
        logger.info(f"Loading Llama model from: {self.model_path}")
        logger.info(f"GPU layers setting: {self.n_gpu_layers} (-1 = all layers on GPU)")
        
        try:
            # Initialize Llama model with GPU priority
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,  # -1 offloads all layers to GPU
                n_batch=512,  # Larger batch for faster processing
                n_threads=4,  # Use multiple threads for CPU fallback
                verbose=True,  # Show GPU layer allocation
                use_mmap=True,  # Memory-mapped for faster loading
            )
            self.is_loaded = True
            logger.info("Llama model loaded successfully with GPU acceleration")
            
        except Exception as e:
            logger.error(f"Failed to load Llama model: {e}")
            raise
            
    def unload_model(self):
        """Unload the model to free memory."""
        if self.llm:
            del self.llm
            self.llm = None
        self.is_loaded = False
        logger.info("Llama model unloaded")
    
    def correct_batch(self, texts: list) -> list:
        """
        Correct multiple texts in batch for faster processing.
        """
        if not self.is_loaded:
            self.load_model()
        
        results = []
        batch_size = 5  # Process 5 sentences at a time
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_prompt = self._construct_batch_prompt(batch)
            
            try:
                output = self.llm(
                    batch_prompt,
                    max_tokens=sum(len(t) for t in batch) + 50,
                    stop=["---", "\n\n\n"],
                    echo=False,
                    temperature=0
                )
                
                # Parse batch response
                response = output['choices'][0]['text'].strip()
                corrected = self._parse_batch_response(response, batch)
                results.extend(corrected)
                
            except Exception as e:
                logger.error(f"Batch correction failed: {e}")
                results.extend(batch)  # Fallback to original
        
        return results
        
    def correct_text(self, text: str) -> str:
        """
        Correct a single text. Use correct_batch for multiple texts.
        """
        if not self.is_loaded:
            self.load_model()
            
        if not text or not text.strip():
            return text
        
        # Skip very short texts (likely no correction needed)
        if len(text) < 3:
            return text
            
        # Construct simple prompt for single text
        prompt = f"修正粵語同音字並加標點：{text}\n修正："
        
        try:
            output = self.llm(
                prompt,
                max_tokens=len(text) + 20,
                stop=["\n"],
                echo=False,
                temperature=0
            )
            
            corrected = output['choices'][0]['text'].strip()
            return corrected if corrected else text
            
        except Exception as e:
            logger.error(f"Correction failed: {e}")
            return text
    
    def _construct_batch_prompt(self, texts: list) -> str:
        """Construct a simple batch prompt."""
        lines = []
        for i, t in enumerate(texts, 1):
            lines.append(f"{i}. {t}")
        
        prompt = f"""修正以下粵語句子的同音字並加標點（繁體中文）：
{chr(10).join(lines)}
---
修正結果："""
        return prompt
    
    def _parse_batch_response(self, response: str, original: list) -> list:
        """Parse batch response, fallback to original if parsing fails."""
        lines = [l.strip() for l in response.split('\n') if l.strip()]
        results = []
        
        for i, orig in enumerate(original):
            if i < len(lines):
                # Remove numbering if present
                line = lines[i]
                if line and line[0].isdigit() and '.' in line[:3]:
                    line = line.split('.', 1)[-1].strip()
                results.append(line if line else orig)
            else:
                results.append(orig)
        
        return results
            
    def _construct_prompt(self, text: str) -> str:
        """
        Construct the prompt for Cantonese correction.
        Using Qwen2.5 ChatML format for fast inference.
        """
        # Simple, concise prompt for fast inference
        system = "你是粵語字幕校對員。修正同音字錯誤，加標點符號。只輸出修正結果，用繁體中文。"
        
        # Qwen2.5 ChatML format
        prompt = f"""<|im_start|>system
{system}<|im_end|>
<|im_start|>user
修正：{text}<|im_end|>
<|im_start|>assistant
"""
        return prompt


