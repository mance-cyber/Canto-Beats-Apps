"""
Background worker for AI transcription tasks.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List
import time

from PySide6.QtCore import QThread, Signal, QObject

import re
from core.config import Config
from models.whisper_asr import WhisperASR, TranscriptionSegment
from models.vad_processor import VADProcessor
from models.llama_corrector import LlamaCorrector
from utils.audio_utils import AudioPreprocessor
from utils.logger import setup_logger

logger = setup_logger()

class TranscribeWorker(QThread):
    """
    Worker thread for executing AI transcription pipeline.
    
    Signals:
        progress (str, int): Status message and progress percentage (0-100)
        finished (dict): Transcription results
        error (str): Error message
    """
    
    progress = Signal(str, int)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, config: Config, input_path: str, ai_correction_enabled: bool = False, ai_model_path: Optional[str] = None):
        super().__init__()
        self.config = config
        self.input_path = input_path
        self.ai_correction_enabled = ai_correction_enabled
        self.ai_model_path = ai_model_path
        self._is_cancelled = False
        
        # Components
        self.asr = None
        self.vad = None
        self.corrector = None
        
    def run(self):
        """Execute the pipeline sequentially."""
        try:
            input_path = Path(self.input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"File not found: {input_path}")
            
            # 1. Initialize & Load Models (0-30%)
            self.progress.emit("正在加載 AI 模型...", 10)
            
            self.asr = WhisperASR(self.config)
            self.vad = VADProcessor(self.config)
            
            # Load models
            self.asr.load_model()
            if self._is_cancelled: return
            self.progress.emit("正在加載 AI 模型...", 20)
            
            self.vad.load_model()
            if self._is_cancelled: return
            self.progress.emit("模型加載完成", 30)
            
            # 2. Transcription (30-50%)
            self.progress.emit("正在生成字幕...", 30)
            
            # Check/Extract audio if needed
            audio_path = input_path
            # Quick check if video, though Whisper can handle many inputs, 
            # might be safer to ensure it's audio or let Whisper handle it.
            # Assuming input is compatible for now.
            
            # Start transcription
            # We don't have a callback for Whisper's internal progress easily without callbacks,
            # so we just show "Processing..." at 30% and jump to 50% when done.
            # Or effectively it stays at 30% until done, then 50%.
            # User said "Then 50% start processing", implying 30->50 transition.
            
            transcription_result = self.asr.transcribe(
                str(audio_path),
                language='yue'
            )
            
            if self._is_cancelled: return
            self.progress.emit("字幕生成完成", 50)
            
            # 3. Optimization / VAD Merge (Wait until 80%)
            # User said: "Then 80% start optimization"
            # So we might jump to 50, do some processing, then 80.
            
            segments = transcription_result['segments']
            full_text = transcription_result['text']
            
            self.progress.emit("正在優化斷句 (VAD)...", 80)
            
            # Detect voice segments
            voice_segments = self.vad.detect_voice_segments(audio_path)
            
            # Merge with 9:16 optimized parameters from config
            max_chars = self.config.get('subtitle_max_chars', 15)
            max_gap = self.config.get('subtitle_max_gap', 0.8)
            
            optimized_segments = self.vad.merge_with_transcription(
                segments,
                voice_segments,
                max_gap=max_gap,
                max_chars=max_chars
            )
            
            if self._is_cancelled: return
            
            # 4. AI Correction (80-100%)
            final_segments = optimized_segments
            
            if self.ai_correction_enabled and self.ai_model_path:
                self.progress.emit("正在進行 AI 校正...", 90)
                
                try:
                    self.corrector = LlamaCorrector(self.ai_model_path)
                    
                    # Extract texts
                    texts = [seg.text for seg in final_segments]
                    
                    # Correct batch
                    corrected_texts = self.corrector.correct_batch(texts)
                    
                    # Update segments
                    for seg, new_text in zip(final_segments, corrected_texts):
                        seg.text = new_text
                        
                except Exception as e:
                    logger.error(f"AI Correction failed: {e}")
                    # Continue without correction
            
            if self._is_cancelled: return
            
            # Prepare result
            final_text = "\n".join([seg.text for seg in final_segments])
            
            result = {
                'text': final_text,
                'segments': final_segments,
                'language': transcription_result.get('language', 'yue'),
                'audio_path': str(input_path),
                'original_path': str(input_path)
            }
            
            self.progress.emit("處理完成!", 100)
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            self.error.emit(f"處理失敗: {str(e)}")
            
        finally:
            # Cleanup
            if self.asr: self.asr.unload_model()
            if self.vad: self.vad.unload_model()
            if self.corrector: self.corrector.unload_model()

    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True
