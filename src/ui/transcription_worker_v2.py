"""
Background worker for AI transcription tasks V2.

Uses Python threading instead of QThread to avoid Qt thread crashes.
Communicates with Qt main thread via signals.
"""

import threading
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import QObject, Signal, QTimer

from core.config import Config
from pipeline.subtitle_pipeline_v2 import SubtitlePipelineV2
from utils.logger import setup_logger

logger = setup_logger()


class TranscribeWorkerV2(QObject):
    """
    Worker using Python threading for background transcription.
    Avoids QThread to prevent crashes during GPU cleanup.
    """
    
    progress = Signal(str, int)
    completed = Signal(dict)
    error = Signal(str)
    
    def __init__(self, config: Config, input_path: str, force_cpu: bool = False, enable_llm: bool = True, is_first_time: bool = False):
        super().__init__()
        self.config = config
        self.input_path = input_path
        self.force_cpu = force_cpu
        self.enable_llm = enable_llm
        self.is_first_time = is_first_time  # Whether models need to be downloaded
        self._is_cancelled = False
        self._thread = None
        self._result = None
        self._error_msg = None
        self._pipeline = None  # Keep pipeline alive to prevent GC crash
        
    def start(self):
        """Start the worker thread."""
        # Don't use daemon=True - it causes premature termination during long operations
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        
    def _run(self):
        """Execute pipeline in background thread."""
        try:
            input_path = Path(self.input_path)
            if not input_path.exists():
                self._emit_error(f"找不到檔案: {input_path}")
                return
            
            # Initialize pipeline - store as instance to prevent GC
            self._emit_progress("正在初始化...", 0)
            self._pipeline = SubtitlePipelineV2(
                self.config, 
                force_cpu=self.force_cpu,
                enable_llm=self.enable_llm
            )
            
            if self._is_cancelled:
                return
            
            # Run pipeline with progress callback
            def on_progress(pct: int):
                if self._is_cancelled:
                    return
                if pct <= 15:
                    if self.is_first_time:
                        msg = "首次下載 AI 工具中，請稍候..."
                    else:
                        msg = "正在加載 AI 工具..."
                elif pct <= 25:
                    msg = "正在提取音頻..."
                elif pct < 80:
                    msg = "正在生成字幕..."
                elif pct < 82:
                    if self.is_first_time:
                        msg = "首次下載 AI 工具中，請稍候..."
                    else:
                        msg = "正在加載 AI 工具..."
                elif pct < 95:
                    msg = "正在 AI 校正..."
                else:
                    msg = "正在完成處理..."
                self._emit_progress(msg, pct)
            
            # Status callback for detailed messages (e.g., download progress)
            def on_status(msg: str):
                if self._is_cancelled:
                    return
                # Emit status message while keeping current progress
                self._emit_progress(msg, -1)  # -1 means keep current progress
            
            subtitles = self._pipeline.process(
                str(input_path), 
                progress_callback=on_progress,
                status_callback=on_status
            )
            
            if self._is_cancelled:
                return
            
            # Convert to result format
            segments = []
            formal_segments = []
            
            for i, sub in enumerate(subtitles):
                seg = {
                    'id': i,
                    'start': sub.start,
                    'end': sub.end,
                    'text': sub.colloquial,
                }
                segments.append(seg)
                
                if sub.formal:
                    formal_seg = {
                        'id': i,
                        'start': sub.start,
                        'end': sub.end,
                        'text': sub.formal,
                    }
                    formal_segments.append(formal_seg)
            
            # Build result
            full_text = "\n".join([s['text'] for s in segments])
            profile = self._pipeline.get_profile()
            
            result = {
                'text': full_text,
                'segments': segments,
                'formal_segments': formal_segments if formal_segments else None,
                'language': 'yue',
                'audio_path': str(input_path),
                'original_path': str(input_path),
                'hardware_tier': profile.tier.value if profile else 'unknown',
            }
            
            self._emit_progress("處理完成！", 100)
            
            # Emit completed signal directly (Qt signals are thread-safe)
            self.completed.emit(result)
            
            logger.info("Worker thread complete - pipeline kept alive")
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            self.error.emit(f"處理失敗: {str(e)}")
    
    def _emit_progress(self, msg: str, pct: int):
        """Emit progress signal (Qt signals are thread-safe).
        
        Args:
            msg: Status message to display
            pct: Progress percentage (0-100), or -1 to keep current progress
        """
        if pct == -1:
            # Status-only update - keep current progress percentage
            pct = getattr(self, '_current_pct', 0)
        else:
            # Track current progress for status-only updates
            self._current_pct = pct
        self.progress.emit(msg, pct)
        
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True
        
    def cleanup(self):
        """Cleanup pipeline in main thread - call this when safe."""
        if self._pipeline:
            try:
                self._pipeline.cleanup()
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")
            self._pipeline = None
        
    def wait(self):
        """Wait for thread to finish."""
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
            
    def deleteLater(self):
        """Cleanup."""
        self.cancel()
        self.cleanup()  # Cleanup in main thread
        super().deleteLater()
