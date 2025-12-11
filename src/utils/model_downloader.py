"""
Model Downloader utility for fetching large AI models.
"""

import os
import requests
import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict
from huggingface_hub import hf_hub_download, snapshot_download
from PySide6.QtCore import QObject, Signal, QThread

from utils.logger import setup_logger

logger = setup_logger()

class DownloadWorker(QObject):
    """Worker for downloading models in a background thread."""
    
    progress = Signal(int, str)  # percentage, status message
    finished = Signal(str)       # file path
    error = Signal(str)          # error message
    
    def __init__(self, repo_id: str, filename: str, local_dir: str):
        super().__init__()
        self.repo_id = repo_id
        self.filename = filename
        self.local_dir = local_dir
        self._is_cancelled = False
        
    def run(self):
        try:
            self.progress.emit(0, "Initializing download...")
            
            # Ensure directory exists
            os.makedirs(self.local_dir, exist_ok=True)
            
            # Check if file already exists and is complete (simple check)
            local_path = Path(self.local_dir) / self.filename
            if local_path.exists():
                # TODO: Implement hash check if needed
                pass

            # Use requests for direct download to have better progress control
            # or use hf_hub_download with a custom callback if possible.
            # For simplicity and reliability with GGUF, we'll use hf_hub_download
            # but getting granular progress from it is tricky without a custom callback.
            # Let's use the 'resume_download' feature of hf_hub_download.
            
            # Actually, to show a progress bar in UI, we might want to use requests stream
            # if we can get the direct URL.
            # But hf_hub_download handles auth and mirrors better.
            # Let's try to use hf_hub_download directly first.
            
            logger.info(f"Starting download: {self.repo_id}/{self.filename}")
            self.progress.emit(1, "Connecting to Hugging Face...")
            
            file_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.filename,
                local_dir=self.local_dir,
                local_dir_use_symlinks=False,
                resume_download=True
            )
            
            self.progress.emit(100, "Download complete")
            self.finished.emit(file_path)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.error.emit(str(e))
            
    def cancel(self):
        self._is_cancelled = True

class ModelDownloader:
    """
    Manages the download of AI models.
    """
    
    # Configuration for Qwen2.5-0.5B (fast, compact model)
    MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    MODEL_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default to user directory
            self.cache_dir = Path.home() / ".canto_beats" / "models"
            
        self.worker = None
        self.thread = None
        
    def get_model_path(self) -> Path:
        # Check local project models dir first
        local_path = Path("models") / self.MODEL_FILENAME
        if local_path.exists():
            return local_path.absolute()
            
        # Then check cache dir
        return self.cache_dir / self.MODEL_FILENAME
        
    def is_model_installed(self) -> bool:
        # Check local project models dir
        local_path = Path("models") / self.MODEL_FILENAME
        if local_path.exists() and local_path.stat().st_size > 0:
            return True
            
        # Check cache dir
        path = self.cache_dir / self.MODEL_FILENAME
        return path.exists() and path.stat().st_size > 0
        
    def download_model(self, 
                       progress_callback: Callable[[int, str], None],
                       finished_callback: Callable[[str], None],
                       error_callback: Callable[[str], None]):
        """
        Start downloading the model in a background thread.
        """
        if self.thread and self.thread.isRunning():
            return
            
        self.thread = QThread()
        self.worker = DownloadWorker(
            self.MODEL_REPO, 
            self.MODEL_FILENAME, 
            str(self.cache_dir)
        )
        
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(progress_callback)
        self.worker.finished.connect(lambda path: self._on_finished(path, finished_callback))
        self.worker.error.connect(lambda err: self._on_error(err, error_callback))
        
        # Clean up
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()
        
    def _on_finished(self, path, callback):
        logger.info(f"Model downloaded to: {path}")
        callback(path)
        self.thread = None
        self.worker = None
        
    def _on_error(self, err, callback):
        logger.error(f"Model download error: {err}")
        callback(err)
        self.thread = None
        self.worker = None
