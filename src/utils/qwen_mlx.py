"""
MLX Qwen backend for Apple Silicon.

Uses Apple's MLX framework for optimal performance on Apple Silicon,
replacing the Transformers-based qwen_llm.py for faster inference.
"""

import sys
import gc
from pathlib import Path
from typing import Optional, Dict, List

from utils.logger import setup_logger

logger = setup_logger()


class MLXQwenLLM:
    """
    MLX Qwen LLM for Apple Silicon optimized inference.
    
    Uses mlx-lm for fast text generation on Apple Silicon.
    Replaces Transformers-based QwenLLM for 書面語 conversion.
    """
    
    _mlx_available = None
    
    def __init__(self, model_id: str = "mlx-community/Qwen2.5-3B-Instruct-bf16"):
        """
        Initialize MLX Qwen LLM.
        
        Args:
            model_id: MLX model ID from Hugging Face (mlx-community)
        """
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if MLX LM is available on this system."""
        if cls._mlx_available is not None:
            return cls._mlx_available
        
        # Only available on macOS with Apple Silicon
        if sys.platform != 'darwin':
            logger.info("MLX Qwen not available: Not macOS")
            cls._mlx_available = False
            return False
        
        # Check for ARM64 architecture
        import platform
        if platform.machine() != 'arm64':
            logger.info("MLX Qwen not available: Not Apple Silicon (ARM64)")
            cls._mlx_available = False
            return False
        
        # Try to import mlx_lm
        try:
            import mlx_lm
            logger.info("✅ MLX LM is available (Apple Silicon optimized)")
            cls._mlx_available = True
            return True
        except ImportError as e:
            logger.warning(f"MLX LM not available: {e}")
            cls._mlx_available = False
            return False
        except Exception as e:
            logger.warning(f"MLX LM failed to initialize: {e}")
            cls._mlx_available = False
            return False
    
    def load_model(self, progress_callback=None):
        """
        Load MLX Qwen model.
        
        Args:
            progress_callback: Optional callback(message: str) for progress updates
        """
        if self.is_loaded:
            logger.warning("Model already loaded")
            return
        
        if not self.is_available():
            raise RuntimeError("MLX LM is not available on this system")
        
        logger.info(f"🍎 Loading MLX Qwen model: {self.model_id}")
        
        if progress_callback:
            progress_callback("正在加載 AI 書面語工具...")
        
        try:
            from mlx_lm import load
            from huggingface_hub import snapshot_download, try_to_load_from_cache
            
            # Check if model is cached
            cache_result = try_to_load_from_cache(self.model_id, "config.json")
            model_cached = cache_result is not None
            
            if not model_cached:
                logger.info(f"Downloading model: {self.model_id}")
                if progress_callback:
                    progress_callback("正在下載 AI 書面語工具...")
                
                # Download with progress tracking
                from tqdm import tqdm
                
                class ProgressTqdm(tqdm):
                    def __init__(self_tqdm, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self_tqdm.callback = progress_callback
                    
                    def update(self_tqdm, n=1):
                        super().update(n)
                        if self_tqdm.total and self_tqdm.total > 0 and self_tqdm.callback:
                            downloaded_mb = self_tqdm.n / (1024 * 1024)
                            total_mb = self_tqdm.total / (1024 * 1024)
                            msg = f"下載中... {downloaded_mb:.0f}MB / {total_mb:.0f}MB"
                            self_tqdm.callback(msg)
                
                snapshot_download(
                    repo_id=self.model_id,
                    tqdm_class=ProgressTqdm if progress_callback else tqdm
                )
                logger.info("✅ Model downloaded successfully")
            else:
                logger.info("Model already cached, loading from cache...")
            
            if progress_callback:
                progress_callback("正在加載模型...")
            
            # Load model and tokenizer with mlx_lm
            self.model, self.tokenizer = load(self.model_id)
            
            self.is_loaded = True
            logger.info(f"⚡ MLX Qwen ready")
            
            if progress_callback:
                progress_callback("AI 書面語工具就緒！")
            
        except Exception as e:
            logger.error(f"Failed to load MLX Qwen model: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.0,
        **kwargs
    ) -> str:
        """
        Generate text using MLX Qwen.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0 = deterministic)
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.is_loaded:
            self.load_model()
        
        try:
            from mlx_lm import generate
            
            # Format as chat message
            messages = [{"role": "user", "content": prompt}]
            
            # Apply chat template
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate response
            response = generate(
                self.model,
                self.tokenizer,
                prompt=formatted_prompt,
                max_tokens=max_tokens,
                temp=temperature,
                verbose=False
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"MLX generation failed: {e}")
            raise
    
    def batch_convert_to_written(
        self,
        segments: List[str],
        batch_size: int = 5,
        progress_callback=None
    ) -> Dict[int, str]:
        """
        Batch convert segments from colloquial to written Chinese.
        
        Args:
            segments: List of text segments
            batch_size: Number of segments per batch
            progress_callback: Optional callback(current, total, message)
            
        Returns:
            Dict of {index: converted_text}
        """
        if not self.is_loaded:
            self.load_model()
        
        result = {}
        total_batches = (len(segments) + batch_size - 1) // batch_size
        
        for batch_idx, batch_start in enumerate(range(0, len(segments), batch_size)):
            batch_end = min(batch_start + batch_size, len(segments))
            batch_texts = segments[batch_start:batch_end]
            
            if progress_callback:
                progress_callback(batch_idx, total_batches, f"AI 轉換 {batch_idx + 1}/{total_batches}...")
            
            # Combine texts with markers
            combined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(batch_texts)])
            
            prompt = f"""你是一位專業中文編輯與字幕轉寫師。你的任務是把「粵語口語字幕」徹底轉譯成「自然流暢的書面中文」。

【核心目標】
- 完全書面化：把口語、粵語語氣詞、口頭禪、潮語改成正式書面表達。
- 不改意思：保留原句資訊、語氣強弱，但用書面語呈現。
- 適合做字幕：句子要簡潔、易讀、自然。
- **英文必須保留**：所有英文單詞、品牌、人名、術語等，絕對不要翻譯成中文。

【轉譯規則】
1. 移除/改寫粵語語氣詞與填充詞：如「喎、啦、囉、咩、㗎、吓、呀、喇、啫」等。
2. 粗口處理：改成較文明的同等語氣。
3. 只輸出轉譯後文字，保持編號格式。
4. **英文必須保留**：所有英文單詞一律保持原樣。

【常見轉換】
係→是、喺→在、唔→不、冇→沒有、嘅→的、咗→了、嚟→來、佢→他/她
好彩→幸運、頭先→剛才、琴日→昨天、聽日→明天、今日→今天、而家→現在

【輸入】
{combined}

【輸出】（只輸出結果，保持編號）"""
            
            try:
                response = self.generate(prompt, max_tokens=1024, temperature=0)
                
                # Parse numbered response
                for line in response.strip().split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        parts = line.split('.', 1)
                        if len(parts) == 2:
                            try:
                                num = int(parts[0]) - 1
                                text = parts[1].strip()
                                
                                # Clean up
                                if '→' in text:
                                    text = text.split('→')[-1].strip()
                                for bracket in '()（）﹙﹚[]【】「」':
                                    text = text.replace(bracket, '')
                                
                                if 0 <= num < len(batch_texts) and text:
                                    result[batch_start + num] = text
                            except ValueError:
                                pass
                
                logger.info(f"Batch {batch_idx + 1}: processed {len(batch_texts)} segments")
                
            except Exception as e:
                logger.warning(f"Batch processing failed: {e}")
        
        if progress_callback:
            progress_callback(total_batches, total_batches, "AI 轉換完成")
        
        return result
    
    def cleanup(self):
        """Clean up resources."""
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        # Clear memory
        gc.collect()
        
        logger.info("MLX Qwen resources cleaned up")
    
    def unload_model(self):
        """Unload the model (alias for cleanup)."""
        self.cleanup()


def get_best_llm_backend(model_size: str = "3B"):
    """
    Get the best available LLM backend for the current system.
    
    Automatically detects hardware and selects optimal backend:
    - Apple Silicon: MLX Qwen (fastest, uses Neural Engine/GPU)
    - MPS available: Transformers Qwen with MPS (Apple GPU)
    - CUDA available: Transformers Qwen with CUDA (NVIDIA GPU)
    - CPU only: Transformers Qwen with CPU (slowest)
    
    Args:
        model_size: Model size (e.g., "3B", "0.5B")
        
    Returns:
        Tuple of (LLM instance, backend_type string)
    """
    import sys
    import platform
    
    backend_type = "unknown"
    
    # Check platform
    is_mac = sys.platform == 'darwin'
    is_apple_silicon = is_mac and platform.machine() == 'arm64'
    
    # Priority 1: MLX on Apple Silicon (fastest for Apple devices)
    if is_apple_silicon:
        try:
            import mlx_lm
            if MLXQwenLLM.is_available():
                logger.info("🍎 Detected Apple Silicon - using MLX Qwen (fastest)")
                model_id = f"mlx-community/Qwen2.5-{model_size}-Instruct"
                return MLXQwenLLM(model_id=model_id), "mlx"
        except ImportError:
            logger.info("MLX not available, trying MPS fallback")
    
    # Priority 2: Check for GPU (MPS or CUDA)
    try:
        import torch
        
        # Apple MPS (Metal)
        if torch.backends.mps.is_available():
            logger.info("🍎 Detected MPS (Metal) - using Transformers Qwen with GPU")
            backend_type = "mps"
        # NVIDIA CUDA
        elif torch.cuda.is_available():
            logger.info("🎮 Detected CUDA - using Transformers Qwen with GPU")
            backend_type = "cuda"
        else:
            logger.info("💻 No GPU detected - using Transformers Qwen with CPU")
            backend_type = "cpu"
            
    except ImportError:
        logger.warning("PyTorch not available, defaulting to CPU")
        backend_type = "cpu"
    
    # Fallback to Transformers Qwen
    logger.info(f"Using Transformers Qwen on {backend_type.upper()}")
    from models.qwen_llm import QwenLLM
    from core.config import Config
    from core.hardware_detector import HardwareDetector
    
    config = Config()
    detector = HardwareDetector()
    profile = detector.detect()
    return QwenLLM(config, profile), backend_type


def get_qwen_for_hardware():
    """
    Get the optimal Qwen model configuration based on hardware.
    
    Returns:
        Dict with:
        - model_id: The model to download
        - backend: "mlx", "mps", "cuda", or "cpu"
        - device: Torch device string
        - description: Human-readable description
    """
    import sys
    import platform
    
    is_mac = sys.platform == 'darwin'
    is_apple_silicon = is_mac and platform.machine() == 'arm64'
    
    # Apple Silicon with MLX
    if is_apple_silicon:
        try:
            import mlx_lm
            return {
                "model_id": "mlx-community/Qwen2.5-3B-Instruct-bf16",
                "backend": "mlx",
                "device": "mlx",
                "description": "🍎 MLX Qwen (Apple Silicon 優化，最快速)"
            }
        except ImportError:
            pass
    
    # Check GPU availability
    try:
        import torch
        
        if torch.backends.mps.is_available():
            return {
                "model_id": "Qwen/Qwen2.5-3B-Instruct",
                "backend": "mps",
                "device": "mps",
                "description": "🍎 MPS Qwen (Apple Metal GPU)"
            }
        elif torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return {
                "model_id": "Qwen/Qwen2.5-3B-Instruct",
                "backend": "cuda",
                "device": "cuda",
                "description": f"🎮 CUDA Qwen (NVIDIA GPU, {vram:.1f}GB VRAM)"
            }
    except ImportError:
        pass
    
    # CPU fallback
    return {
        "model_id": "Qwen/Qwen2.5-3B-Instruct",
        "backend": "cpu",
        "device": "cpu",
        "description": "💻 CPU Qwen (無 GPU，較慢)"
    }


# Test function
if __name__ == "__main__":
    print(f"MLX Qwen available: {MLXQwenLLM.is_available()}")
    
    if MLXQwenLLM.is_available():
        llm = MLXQwenLLM()
        print("Loading model...")
        llm.load_model()
        
        # Test generation
        test_prompt = "將以下粵語口語轉成書面語：「你成日話你做生意你係老闆」"
        result = llm.generate(test_prompt)
        print(f"Result: {result}")
        
        llm.cleanup()
    else:
        print("MLX Qwen not available")
