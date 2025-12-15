"""
Qwen LLM Processor for Canto-beats V2.0.

Local LLM processing using Qwen2 models for Cantonese subtitle refinement.
Replaces the Ollama-based llm_processor.py.
"""

import json
import re
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path

from core.config import Config
from core.hardware_detector import PerformanceProfile, PerformanceTier
from prompts.cantonese_prompts import (
    BASIC_CORRECTION_PROMPT,
    COMPLEXITY_JUDGE_PROMPT,
    SIMPLE_PROCESS_PROMPT,
    FULL_PROCESS_PROMPT_V3,
    protect_proper_nouns,
    restore_proper_nouns,
)
from utils.logger import setup_logger

logger = setup_logger()


@dataclass
class ProcessedSentence:
    """A processed sentence with both colloquial and formal versions."""
    colloquial: str
    formal: Optional[str] = None


class QwenLLM:
    """
    Local Qwen2 LLM processor for Cantonese subtitle refinement.
    
    Supports:
    - Basic correction mode (Entry/CPU-Only tiers)
    - Full processing mode with dual outputs (Ultimate/Mainstream tiers)
    - Dual-model workflow (LLM-A for preprocessing, LLM-B for heavy lifting)
    """
    
    def __init__(
        self, 
        config: Config,
        profile: PerformanceProfile,
        model_a_path: Optional[str] = None,
        model_b_path: Optional[str] = None,
    ):
        """
        Initialize Qwen LLM processor.
        
        Args:
            config: Application configuration
            profile: Performance profile from hardware detection
            model_a_path: Override path for LLM-A model
            model_b_path: Override path for LLM-B model
        """
        self.config = config
        self.profile = profile
        
        # Model paths
        self.model_a_id = model_a_path or profile.llm_a_model
        self.model_b_id = model_b_path or profile.llm_b_model
        
        # Models (lazy loaded)
        self._model_a = None
        self._model_b = None
        self._tokenizer_a = None
        self._tokenizer_b = None
        
        # Proper nouns dictionary (can be loaded from file)
        self.proper_nouns: List[str] = []
        
        logger.info(f"QwenLLM initialized with profile: {profile.tier.value}")
        logger.info(f"  LLM-A: {self.model_a_id}")
        if profile.llm_b_enabled:
            logger.info(f"  LLM-B: {self.model_b_id}")
    
    def load_models(self):
        """Load LLM models based on performance profile."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import transformers.utils.logging as hf_logging
            import torch
            
            # Disable tqdm progress bars to prevent sys.stderr.flush() errors in GUI
            hf_logging.disable_progress_bar()
            
            device = self.profile.device
            
            # Load LLM-A (always enabled)
            logger.info(f"Loading LLM-A: {self.model_a_id}...")
            
            # Determine quantization config based on VRAM
            model_a_kwargs = {
                "device_map": "auto" if device == "cuda" else "cpu",
                "trust_remote_code": True,
            }
            
            quantization = self.profile.llm_a_quantization
            logger.info(f"Using quantization: {quantization}")
            
            if quantization == "4bit":
                # DISABLED: 4bit quantization causes quality degradation
                # Force fp16 for consistent quality (same as when bitsandbytes unavailable)
                logger.info("Using FP16 precision (4bit disabled for quality)")
                model_a_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32
            elif quantization == "int8":
                try:
                    from transformers import BitsAndBytesConfig
                    model_a_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_8bit=True,
                    )
                    logger.info("Using INT8 quantization")
                except ImportError:
                    logger.warning("bitsandbytes not available, using full precision")
                    model_a_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32
            elif quantization == "fp16":
                model_a_kwargs["torch_dtype"] = torch.float16
                logger.info("Using FP16 precision")
            else:
                model_a_kwargs["torch_dtype"] = torch.float32
                logger.info("Using FP32 precision")
            
            self._tokenizer_a = AutoTokenizer.from_pretrained(
                self.model_a_id, 
                trust_remote_code=True
            )
            self._model_a = AutoModelForCausalLM.from_pretrained(
                self.model_a_id,
                **model_a_kwargs
            )
            
            logger.info("[OK] LLM-A loaded successfully")
            
            # Load LLM-B if enabled
            if self.profile.llm_b_enabled and self.model_b_id:
                logger.info(f"Loading LLM-B: {self.model_b_id}...")
                
                model_b_kwargs = {
                    "device_map": "auto",
                    "trust_remote_code": True,
                }
                
                if self.profile.llm_b_quantization in ("4bit", "3bit"):
                    try:
                        from transformers import BitsAndBytesConfig
                        model_b_kwargs["quantization_config"] = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                        )
                    except ImportError:
                        logger.warning("bitsandbytes not available for LLM-B")
                        model_b_kwargs["torch_dtype"] = torch.float16
                
                self._tokenizer_b = AutoTokenizer.from_pretrained(
                    self.model_b_id,
                    trust_remote_code=True
                )
                self._model_b = AutoModelForCausalLM.from_pretrained(
                    self.model_b_id,
                    **model_b_kwargs
                )
                
                logger.info("[OK] LLM-B loaded successfully")
                
        except Exception as e:
            logger.error(f"Failed to load LLM models: {e}")
            raise
    
    def unload_models(self):
        """Unload models and free memory."""
        import gc
        
        logger.info("Unloading LLM models...")
        
        try:
            if self._model_a is not None:
                del self._model_a
                self._model_a = None
            if self._model_b is not None:
                del self._model_b
                self._model_b = None
            if self._tokenizer_a is not None:
                del self._tokenizer_a
                self._tokenizer_a = None
            if self._tokenizer_b is not None:
                del self._tokenizer_b
                self._tokenizer_b = None
            
            gc.collect()
            
            # Don't call torch.cuda.empty_cache() here - can cause segfault when called from thread
            # Let the main thread handle GPU memory cleanup
            
            logger.info("LLM models unloaded successfully")
        except Exception as e:
            logger.warning(f"Error during LLM unload: {e}")
    
    def _generate(
        self, 
        prompt: str, 
        model, 
        tokenizer,
        max_new_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """Generate text using the specified model."""
        import torch
        
        messages = [{"role": "user", "content": prompt}]
        
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer([text], return_tensors="pt")
        if self.profile.device == "cuda":
            inputs = inputs.to("cuda")
        
        with torch.no_grad():
            # Use greedy decoding when temperature=0 (no sampling parameters)
            if temperature <= 0:
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,  # Greedy decoding
                    pad_token_id=tokenizer.eos_token_id,
                )
            else:
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                )
        
        # Decode only the new tokens
        generated = outputs[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(generated, skip_special_tokens=True)
        
        return response.strip()
    
    def _parse_json_response(self, response: str) -> Union[List, Dict, None]:
        """Parse JSON from LLM response."""
        # Clean up response
        text = response.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON array or object
        json_match = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
        if json_match:
            text = json_match.group()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            logger.debug(f"Response was: {response}")
            return None
    
    def process_basic(self, text: str) -> List[str]:
        """
        Basic processing mode - correction and segmentation only.
        Used for Entry and CPU-Only tiers.
        
        Args:
            text: Raw ASR text
            
        Returns:
            List of corrected sentences
        """
        if not text or not text.strip():
            return []
        
        if self._model_a is None:
            logger.error("LLM-A not loaded")
            return [text]
        
        # Protect proper nouns
        protected_text, mapping = protect_proper_nouns(text, self.proper_nouns)
        
        prompt = BASIC_CORRECTION_PROMPT.format(text=protected_text)
        response = self._generate(prompt, self._model_a, self._tokenizer_a, max_new_tokens=768)
        
        # Parse response
        result = self._parse_json_response(response)
        
        if result is None:
            # Parsing failed, return original text
            logger.warning("Failed to parse basic correction response (None)")
            return [text]
        
        if isinstance(result, list):
            # Restore proper nouns
            sentences = [restore_proper_nouns(s, mapping) for s in result]
            return sentences
        else:
            # Fallback: return original text
            logger.warning("Failed to parse basic correction response")
            return [text]
    
    def refine_text_with_context(self, text: str, context: str) -> Dict:
        """
        Refine text with surrounding context for better idiom/slang correction.
        
        Args:
            text: The current sentence to refine
            context: Formatted context with 前文/當前/後文
            
        Returns:
            Dict with 'sentences' key containing refined text
        """
        if not text or not text.strip():
            return {'sentences': []}
        
        if self._model_a is None:
            logger.error("LLM-A not loaded")
            return {'sentences': [text]}
        
        # Protect proper nouns
        protected_text, mapping = protect_proper_nouns(text, self.proper_nouns)
        protected_context = context.replace(text, protected_text)
        
        # Enhanced prompt with idiom correction examples
        prompt = f"""你是粵語字幕編輯，專門校正語音識別的錯別字。

{protected_context}

【常見成語/俗語同音字校正】:
- 「克苦來路」→「刻苦耐勞」
- 「無微不至」→「無微不至」
- 「一視同人」→「一視同仁」
- 「心曠神怡」→「心曠神怡」
- 「專心至志」→「專心致志」
- 「事倍公半」→「事倍功半」

規則：
- 只輸出校正後的句子
- 修正成語/俗語的同音字錯誤
- 保持粵語口語風格

校正後："""
        
        response = self._generate(prompt, self._model_a, self._tokenizer_a, max_new_tokens=128)
        
        # Clean up response - direct text, no JSON
        cleaned = response.strip()
        
        # Remove any prefixes that LLM might add
        prefixes_to_remove = ["校正後：", "校正後:", "校正：", "校正:", "【當前句子】", 
                              "輸出：", "輸出:", "結果：", "結果:"]
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove surrounding quotes
        for (start, end) in [('"', '"'), ("'", "'"), ("「", "」"), ("'", "'"), (""", """)]:
            if cleaned.startswith(start) and cleaned.endswith(end):
                cleaned = cleaned[1:-1]
        
        # Remove trailing explanations (anything after newline)
        if '\n' in cleaned:
            cleaned = cleaned.split('\n')[0].strip()
        
        # Use cleaned text if valid, otherwise fallback to original
        if cleaned and len(cleaned) > 0:
            restored = restore_proper_nouns(cleaned, mapping)
            return {'sentences': [restored]}
        
        return {'sentences': [text]}
    
    def judge_complexity(self, text: str) -> bool:
        """
        Judge if text requires complex processing.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if complex, False if simple
        """
        if self._model_a is None:
            return True  # Default to complex if can't judge
        
        prompt = COMPLEXITY_JUDGE_PROMPT.format(text=text)
        response = self._generate(
            prompt, 
            self._model_a, 
            self._tokenizer_a,
            max_new_tokens=10,
            temperature=0.0,
        )
        
        is_complex = "complex" in response.lower()
        logger.debug(f"Complexity judgment: {'complex' if is_complex else 'simple'}")
        return is_complex
    
    def process_full(self, text: str) -> List[ProcessedSentence]:
        """
        Full processing mode with colloquial and formal outputs.
        Used for Ultimate and Mainstream tiers.
        
        Args:
            text: Raw ASR text
            
        Returns:
            List of ProcessedSentence with both versions
        """
        if not text or not text.strip():
            return []
        
        # Protect proper nouns
        protected_text, mapping = protect_proper_nouns(text, self.proper_nouns)
        
        # Determine which model to use
        is_complex = self.judge_complexity(protected_text)
        
        if is_complex and self._model_b is not None:
            # Use LLM-B for complex processing
            logger.info("Using LLM-B for complex processing")
            prompt = FULL_PROCESS_PROMPT_V3.format(text=protected_text)
            response = self._generate(
                prompt, 
                self._model_b, 
                self._tokenizer_b,
                max_new_tokens=2048,
            )
        else:
            # Use LLM-A for simple processing
            logger.info("Using LLM-A for simple processing")
            prompt = SIMPLE_PROCESS_PROMPT.format(text=protected_text)
            response = self._generate(prompt, self._model_a, self._tokenizer_a, max_new_tokens=512)
        
        # Parse response
        result = self._parse_json_response(response)
        
        if result is None:
            # Parsing failed, return original text
            logger.warning("Failed to parse full processing response (None)")
            return [ProcessedSentence(colloquial=text, formal=None)]
        
        if isinstance(result, list):
            sentences = []
            for item in result:
                if isinstance(item, dict):
                    colloquial = item.get("colloquial_sentence") or item.get("colloquial", "")
                    formal = item.get("formal_sentence") or item.get("formal", "")
                    
                    # Restore proper nouns
                    colloquial = restore_proper_nouns(colloquial, mapping)
                    formal = restore_proper_nouns(formal, mapping)
                    
                    sentences.append(ProcessedSentence(
                        colloquial=colloquial,
                        formal=formal if formal else None,
                    ))
                elif isinstance(item, str):
                    sentences.append(ProcessedSentence(
                        colloquial=restore_proper_nouns(item, mapping),
                        formal=None,
                    ))
            return sentences
        else:
            # Fallback
            logger.warning("Failed to parse full processing response")
            return [ProcessedSentence(colloquial=text, formal=None)]
    
    def refine_text(self, raw_text: str) -> Dict:
        """
        Main entry point for text refinement.
        Automatically selects processing mode based on profile.
        
        Args:
            raw_text: Raw ASR text
            
        Returns:
            Dict with processing results:
            - "sentences": List of colloquial sentences
            - "formal_sentences": List of formal sentences (if available)
            - "mode": "basic" or "full"
        """
        if self.profile.tier in (PerformanceTier.ENTRY, PerformanceTier.CPU_ONLY):
            # Basic mode - fast, no formal translation
            sentences = self.process_basic(raw_text)
            return {
                "sentences": sentences,
                "formal_sentences": None,
                "mode": "basic",
            }
        else:
            # Full mode (MAINSTREAM, ULTIMATE only)
            processed = self.process_full(raw_text)
            return {
                "sentences": [p.colloquial for p in processed],
                "formal_sentences": [p.formal for p in processed if p.formal],
                "mode": "full",
            }
    
    def load_proper_nouns(self, file_path: Union[str, Path]):
        """Load proper nouns dictionary from file."""
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.proper_nouns = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.proper_nouns)} proper nouns")
