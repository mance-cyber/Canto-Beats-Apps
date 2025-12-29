#!/usr/bin/env python3
"""測試首次下載進度框"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from ui.download_dialog import ModelDownloadDialog, MLXWhisperDownloadWorker

def test_whisper_download():
    """測試 Whisper 模型下載對話框"""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 創建下載對話框
    dialog = ModelDownloadDialog(model_id="mlx-community/whisper-large-v3-mlx")
    dialog.setWindowTitle("測試：下載 Whisper 模型")
    dialog.title_label.setText("首次下載 Whisper 模型（測試）")
    
    # 使用 MLX Worker
    dialog.worker = MLXWhisperDownloadWorker("large-v3")
    dialog.worker.progress.connect(dialog._on_progress)
    dialog.worker.finished.connect(dialog._on_finished)
    dialog.worker.start()
    
    result = dialog.exec()
    print(f"\n結果: {'成功' if dialog.was_successful() else '失敗/取消'}")
    
    app.quit()

if __name__ == "__main__":
    test_whisper_download()

