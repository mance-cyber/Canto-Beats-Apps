"""
GGUF LLM Processor for Canto-beats.

Uses llama-cpp-python for fast local inference with GGUF models.
Replaces Transformers-based QwenLLM for 2-3x faster performance.
"""

from pathlib import Path
from typing import List, Dict, Optional
from utils.logger import setup_logger

logger = setup_logger()


class GGUFLM:
    """
    GGUF-based LLM processor using llama-cpp-python.
    
    Provides fast local inference with GPU acceleration.
    """
    
    # Default model path relative to project root
    DEFAULT_MODEL_PATH = "models/qwen2.5-3b-instruct-q6_k.gguf"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        n_gpu_layers: int = -1,  # -1 = offload all layers to GPU
        n_ctx: int = 4096,       # Context window
        n_batch: int = 512,      # Batch size for prompt processing
        verbose: bool = False,
    ):
        """
        Initialize GGUF LLM.
        
        Args:
            model_path: Path to GGUF model file
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
            n_ctx: Context window size
            n_batch: Batch size for prompt processing
            verbose: Enable verbose output
        """
        self.model_path = model_path or self.DEFAULT_MODEL_PATH
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.verbose = verbose
        
        self._model = None
        self._is_loaded = False
        
        logger.info(f"GGUFLM initialized with model: {self.model_path}")
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    def load_model(self):
        """Load the GGUF model."""
        if self._is_loaded:
            logger.warning("Model already loaded")
            return
        
        # Check if model exists
        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"GGUF model not found: {self.model_path}")
        
        logger.info(f"Loading GGUF model: {self.model_path}")
        logger.info(f"GPU layers: {self.n_gpu_layers}, Context: {self.n_ctx}")
        
        try:
            from llama_cpp import Llama
            
            self._model = Llama(
                model_path=str(model_file),
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                verbose=self.verbose,
            )
            
            self._is_loaded = True
            logger.info("[OK] GGUF model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load GGUF model: {e}")
            raise
    
    def unload_model(self):
        """Unload the model and free memory."""
        if not self._is_loaded:
            return
        
        logger.info("Unloading GGUF model...")
        
        try:
            if self._model is not None:
                del self._model
                self._model = None
            
            self._is_loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("GGUF model unloaded")
            
        except Exception as e:
            logger.warning(f"Error during GGUF unload: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            top_p: Top-p sampling
            stop: Stop sequences
            
        Returns:
            Generated text
        """
        if not self._is_loaded:
            self.load_model()
        
        # Format as chat message for instruction-tuned model
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self._model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
            )
            
            # Extract generated text
            content = response["choices"][0]["message"]["content"]
            return content.strip()
            
        except Exception as e:
            logger.error(f"GGUF generation failed: {e}")
            return ""
    
    def batch_convert_to_written(
        self,
        texts: List[str],
        progress_callback=None,
    ) -> Dict[int, str]:
        """
        Batch convert Cantonese colloquial to written Chinese.
        
        Args:
            texts: List of texts to convert
            progress_callback: Optional callback(current, total, message)
            
        Returns:
            Dict of {index: converted_text}
        """
        if not self._is_loaded:
            self.load_model()
        
        result = {}
        batch_size = 5
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for batch_idx, batch_start in enumerate(range(0, len(texts), batch_size)):
            batch_end = min(batch_start + batch_size, len(texts))
            batch_texts = texts[batch_start:batch_end]
            
            # Report progress
            if progress_callback:
                progress = int((batch_idx / total_batches) * 100)
                progress_callback(batch_idx, total_batches, f"AI converting batch {batch_idx + 1}/{total_batches}...")
            
            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])
            
            prompt = f"""你是粵語轉書面語專家。將每句粵語口語完全轉換成標準普通話書面語。

【強制轉換規則 - 必須全部執行】
粵語 → 書面語：
- 係/系 → 是
- 喺 → 在  
- 唔 → 不
- 冇 → 沒有
- 嘅 → 的
- 咗 → 了
- 嚟/黎 → 來
- 佢 → 他/她
- 啲 → 些/點
- 咁 → 這樣/這麼
- 嗰 → 那
- 呢 → 這
- 俾/畀 → 給
- 搵 → 找
- 睇 → 看
- 諗 → 想
- 話 → 說
- 好彩 → 幸運
- 頭先 → 剛才
- 琴日 → 昨天
- 聽日 → 明天
- 今日 → 今天
- 而家 → 現在
- 個鐘 → 小時
- 蚊 → 元
- 入面/裏面 → 裡面
- 出面 → 外面
- 返工 → 上班
- 收工 → 下班
- 食嘢 → 吃東西
- 飲嘢 → 喝東西
- 點解 → 為什麼
- 乜嘢 → 什麼
- 幾時 → 什麼時候
- 邊度 → 哪裡

【重要】
1. 必須轉換所有粵語詞彙，不能保留任何一個
2. 英文保持原樣不翻譯
3. 只輸出編號和轉換結果

輸入：
{combined}

輸出："""
            
            try:
                response = self.generate(
                    prompt,
                    max_tokens=1024,
                    temperature=0.3,  # Higher temperature for more aggressive conversion
                )
                
                # Parse numbered response
                for line in response.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            try:
                                num = int(parts[0]) - 1
                                text = parts[1].strip()
                                if 0 <= num < len(batch_texts):
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                logger.info(f"GGUF Batch {batch_idx + 1}: processed {len(batch_texts)} segments")
                
            except Exception as e:
                logger.warning(f"GGUF batch processing failed: {e}")
        
        # Report completion
        if progress_callback:
            progress_callback(total_batches, total_batches, "AI conversion complete")
        
        return result


def test_gguf():
    """Test GGUF LLM."""
    llm = GGUFLM()
    
    try:
        print("Loading model...")
        llm.load_model()
        
        print("\nTesting generation...")
        response = llm.generate(
            "將以下粵語翻譯成書面語：「我今日去咗超市買嘢」",
            max_tokens=128,
        )
        print(f"Response: {response}")
        
        print("\nTesting batch conversion...")
        texts = [
            "我今日去咗超市買嘢",
            "佢係我嘅朋友",
            "你睇吓呢個嘢",
        ]
        results = llm.batch_convert_to_written(texts)
        for idx, text in results.items():
            print(f"  {idx}: {text}")
        
    finally:
        llm.unload_model()
        print("\nTest complete!")


if __name__ == "__main__":
    test_gguf()
