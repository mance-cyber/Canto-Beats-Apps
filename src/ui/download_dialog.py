"""
Model Download Dialog for Canto-beats.

Shows progress when downloading models from HuggingFace for the first time.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, 
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QMovie

from utils.logger import setup_logger

logger = setup_logger()


class MLXWhisperDownloadWorker(QThread):
    """Worker thread for downloading MLX Whisper models."""

    progress = Signal(int, str)  # progress %, status message
    finished = Signal(bool, str)  # success, message

    def __init__(self, model_size: str = "large-v3"):
        super().__init__()
        self.model_size = model_size
        self._cancelled = False

    def run(self):
        try:
            from huggingface_hub import snapshot_download
            from tqdm import tqdm

            self.progress.emit(5, "準備下載...")
            model_path = f"mlx-community/whisper-{self.model_size}-mlx"
            
            # Custom tqdm class to emit progress signals
            class ProgressTqdm(tqdm):
                def __init__(self_tqdm, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self_tqdm.worker = self
                
                def update(self_tqdm, n=1):
                    super().update(n)
                    if self_tqdm.total and self_tqdm.total > 0:
                        # Calculate percentage
                        percent = int((self_tqdm.n / self_tqdm.total) * 90) + 10  # 10-100%
                        # Format downloaded size
                        downloaded_mb = self_tqdm.n / (1024 * 1024)
                        total_mb = self_tqdm.total / (1024 * 1024)
                        msg = f"下載中... {downloaded_mb:.1f}MB / {total_mb:.1f}MB"
                        self_tqdm.worker.progress.emit(percent, msg)

            snapshot_download(
                repo_id=model_path,
                allow_patterns=["*.safetensors", "*.json", "*.npz"],
                tqdm_class=ProgressTqdm
            )

            if self._cancelled:
                return

            self.progress.emit(100, "下載完成")
            self.finished.emit(True, "下載成功")

        except Exception as e:
            logger.error(f"MLX Whisper download failed: {e}")
            self.finished.emit(False, f"下載失敗: {str(e)}")

    def cancel(self):
        self._cancelled = True


class ModelDownloadWorker(QThread):
    """Worker thread for downloading models."""
    
    progress = Signal(int, str)  # progress %, status message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, model_id: str, quantization: str = None):
        super().__init__()
        self.model_id = model_id
        self.quantization = quantization
        self._cancelled = False
    
    def run(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            self.progress.emit(10, "AI 工具下載中...")

            # Load tokenizer first (smaller)
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )

            if self._cancelled:
                return

            self.progress.emit(50, "AI 工具下載中...")

            model_kwargs = {
                "device_map": "auto",
                "trust_remote_code": True,
            }

            if self.quantization == "4bit":
                try:
                    from transformers import BitsAndBytesConfig
                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                    )
                except ImportError:
                    model_kwargs["torch_dtype"] = torch.float16
            else:
                model_kwargs["torch_dtype"] = torch.float16
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                **model_kwargs
            )

            # Clean up
            del model
            del tokenizer

            import gc
            gc.collect()
            # Cross-platform GPU memory cleanup
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.progress.emit(100, "下載完成")
            self.finished.emit(True, "下載成功")
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            self.finished.emit(False, f"下載失敗: {str(e)}")
    
    def cancel(self):
        self._cancelled = True


class ModelDownloadDialog(QDialog):
    """Dialog showing model download progress."""
    
    def __init__(self, model_id: str, quantization: str = None, parent=None):
        super().__init__(parent)
        self.model_id = model_id
        self.quantization = quantization
        self.worker = None
        self._success = False
        
        # Frameless window (no title bar)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedWidth(450)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # GIF animation using QMovie
        try:
            from pathlib import Path
            
            gif_path = Path(__file__).parent.parent.parent / "public" / "Dnlooping.gif"
            
            if gif_path.exists():
                # Load GIF animation
                animation_label = QLabel()
                animation_label.setFixedSize(120, 120)
                animation_label.setAlignment(Qt.AlignCenter)
                
                movie = QMovie(str(gif_path))
                movie.setScaledSize(animation_label.size())
                animation_label.setMovie(movie)
                movie.start()
                
                # Center the animation
                anim_container = QHBoxLayout()
                anim_container.addStretch()
                anim_container.addWidget(animation_label)
                anim_container.addStretch()
                layout.addLayout(anim_container)
            else:
                # Fallback to emoji if GIF not found
                self._add_emoji_animation(layout)
        except Exception as e:
            # Fallback on any error
            self._add_emoji_animation(layout)
        
        # Simple title
        self.title_label = QLabel("AI 工具下載中...")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Status (hidden for clean UI)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 13px; color: #00D4AA;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()  # Hide status text
        # layout.addWidget(self.status_label)  # Commented out
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #1A1A2E;
                height: 20px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D4AA, stop:1 #00A8CC);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Size info
        info_label = QLabel("下載大小約 4-5GB")
        info_label.setStyleSheet("font-size: 11px; color: #888888;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Cancel button
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: none;
                padding: 8px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #16213E;
            }
        """)
    
    def _add_emoji_animation(self, layout):
        """Fallback emoji animation when Lottie/WebEngine not available."""
        animation_label = QLabel("⏳")
        animation_label.setFixedSize(120, 120)
        animation_label.setAlignment(Qt.AlignCenter)
        animation_label.setStyleSheet("font-size: 60px;")
        
        anim_container = QHBoxLayout()
        anim_container.addStretch()
        anim_container.addWidget(animation_label)
        anim_container.addStretch()
        layout.addLayout(anim_container)
    
    def start_download(self):
        """Start the download in background."""
        self.worker = ModelDownloadWorker(self.model_id, self.quantization)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def _on_finished(self, success: bool, message: str):
        self._success = success
        if success:
            self.status_label.setText("✓ " + message)
            self.status_label.setStyleSheet("font-size: 14px; color: #00FF00;")
            self.title_label.setText("✅ 下載完成！")
            self.cancel_btn.hide()  # Hide button
            
            # Auto-close after 1 second
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText("✗ " + message)
            self.status_label.setStyleSheet("font-size: 14px; color: #FF6666;")
            self.cancel_btn.setText("關閉")
    
    def _on_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        self.reject()
    
    def was_successful(self) -> bool:
        return self._success


def check_and_download_model(model_id: str, quantization: str = None, parent=None) -> bool:
    """
    Check if model exists, if not show download dialog.
    
    Returns True if model is available (already exists or downloaded successfully).
    """
    from pathlib import Path
    import os
    
    # Check if model already cached
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_cache_name = f"models--{model_id.replace('/', '--')}"
    model_path = cache_dir / model_cache_name
    
    # Check if model files exist
    if model_path.exists():
        snapshots = model_path / "snapshots"
        if snapshots.exists() and any(snapshots.iterdir()):
            logger.info(f"Model {model_id} already cached")
            return True
    
    # Model not found, show download dialog
    logger.info(f"Model {model_id} not found, starting download...")
    
    dialog = ModelDownloadDialog(model_id, quantization, parent)
    dialog.start_download()
    dialog.exec()
    
    return dialog.was_successful()
