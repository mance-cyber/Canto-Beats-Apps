"""
LLM Processor for Canto-beats.
Handles interaction with Ollama for subtitle refinement.
"""

import json
import requests
import logging
from typing import List, Dict, Optional
from core.config import Config
from utils.logger import setup_logger

logger = setup_logger()

class LLMProcessor:
    """
    Handles interaction with Ollama LLM for Cantonese subtitle correction and segmentation.
    """

    def __init__(self, config: Config):
        self.config = config
        self.api_url = config.get("llm_api_url", "http://localhost:11434/api/generate")
        self.model = config.get("llm_model", "qwen:14b")
        
        # SECURITY: Validate that API URL is localhost to prevent data leakage
        self._validate_api_url()
        
        logger.info(f"LLMProcessor initialized with model: {self.model} at {self.api_url}")
    
    def _validate_api_url(self):
        """Validate API URL is localhost for security."""
        from urllib.parse import urlparse
        parsed = urlparse(self.api_url)
        
        allowed_hosts = ['localhost', '127.0.0.1', '::1']
        if parsed.hostname not in allowed_hosts:
            logger.warning(
                f"SECURITY WARNING: LLM API URL '{self.api_url}' is not localhost. "
                f"This may expose data to external servers. Allowed hosts: {allowed_hosts}"
            )

    def check_connection(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            # Try a simple prompt
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": "Hi",
                    "stream": False
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"LLM Connection failed: {e}")
            return False

    def refine_text(self, raw_text: str) -> List[str]:
        """
        Refine raw ASR text using LLM.
        
        Args:
            raw_text: Raw text from ASR.
            
        Returns:
            List of corrected, segmented sentences.
        """
        if not raw_text or not raw_text.strip():
            return []
            
        logger.info(f"Sending text to LLM for refinement ({len(raw_text)} chars)")
        
        prompt = self._build_prompt(raw_text)
        
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for deterministic output
                        "top_p": 0.9,
                    }
                },
                timeout=60  # Longer timeout for processing
            )
            
            if response.status_code != 200:
                logger.error(f"LLM Error {response.status_code}: {response.text}")
                return [raw_text] # Fallback
                
            result = response.json()
            response_text = result.get("response", "").strip()
            
            # Parse JSON output
            try:
                # Clean up potential markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                    
                sentences = json.loads(response_text)
                
                if isinstance(sentences, list):
                    logger.info(f"LLM returned {len(sentences)} sentences")
                    return sentences
                else:
                    logger.warning("LLM returned valid JSON but not a list")
                    return [raw_text]
                    
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM output as JSON: {response_text}")
                # Try to salvage if it's just a string, or fallback
                return [raw_text]
                
        except Exception as e:
            logger.error(f"LLM Processing failed: {e}")
            return [raw_text]

    def _build_prompt(self, raw_text: str) -> str:
        """Build the specific prompt for qwen:14b."""
        return f"""
# Role:
你是一個精通香港粵語的專業字幕編輯。

# Task:
你的任務是處理一段由語音識別（ASR）轉錄的原始文本。你需要執行以下兩個步驟：
1.  **全文校對**：修正文本中的所有錯別字、同音字錯誤（例如「C度」->「喺度」），並確保用詞符合香港粵語的口語習慣。
2.  **語義斷句與重組**：這段文本可能包含因為語速過快而被錯誤切分嘅片段，請根據語義將佢哋智能地合併或重新切分，成為多個獨立、通順的句子。

# Rules:
- **校對規則**:
    - 使用最地道的粵語口語詞彙（例如保留「搞掂」、「冇問題」、「勁」）。
- 如有潮語的粵語口語詞彙可這樣翻譯(例如「甩底」等於「爽約」,「大癲」等於「非常誇張」,「好Kam」等於「十分尷尬」)    
- 確保標點符號使用正確，特別是句末的語氣詞（如「呀、啦、喎、囉」）。
- **斷句規則**:
    - 每個句子都應該是一個完整的思想單元。
    - 即使原文沒有標點，也要根據語氣和停頓智能地切分。
- **輸出格式**:
    - 嚴格按照 Python List of Strings 的 JSON 格式輸出，例如 `["句子一。", "句子二。"]`。
    - **絕對不要**在最終輸出中包含任何 markdown 標記 (例如 ```json) 或任何解釋性文字。

# ASR 原始文本:
{raw_text}
"""
