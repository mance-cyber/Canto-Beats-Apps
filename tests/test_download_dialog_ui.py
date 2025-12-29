#!/usr/bin/env python3
"""測試下載對話框 UI（模擬進度）"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.download_dialog import ModelDownloadDialog

def test_download_dialog_ui():
    """測試下載對話框 UI（模擬進度，不真實下載）"""
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 創建對話框
    dialog = ModelDownloadDialog(model_id="mlx-community/whisper-large-v3-mlx")
    dialog.setWindowTitle("測試：首次下載進度框")
    dialog.title_label.setText("首次下載 Whisper 模型（模擬）")
    
    # 模擬進度更新
    progress_steps = [
        (10, "正在連接 HuggingFace..."),
        (20, "正在下載 Whisper 模型 (large-v3)..."),
        (40, "正在下載 Whisper 模型 (large-v3)..."),
        (60, "正在下載 Whisper 模型 (large-v3)..."),
        (80, "正在下載 Whisper 模型 (large-v3)..."),
        (90, "正在驗證模型..."),
        (100, "下載完成!"),
    ]
    
    current_step = [0]
    
    def update_progress():
        if current_step[0] < len(progress_steps):
            percent, message = progress_steps[current_step[0]]
            dialog._on_progress(percent, message)
            current_step[0] += 1
        else:
            # 模擬完成
            dialog._on_finished(True, "模型下載成功（模擬）")
            timer.stop()
    
    # 每 500ms 更新一次進度
    timer = QTimer()
    timer.timeout.connect(update_progress)
    timer.start(500)
    
    # 顯示對話框
    dialog.show()
    
    result = app.exec()
    
    print(f"\n✅ 測試完成")
    print(f"對話框結果: {'成功' if dialog.was_successful() else '取消'}")
    
    return result

if __name__ == "__main__":
    print("=" * 60)
    print("測試：首次下載進度對話框 UI")
    print("=" * 60)
    print("\n這是一個模擬測試，不會真的下載模型")
    print("你會看到一個進度對話框，模擬下載過程\n")
    
    test_download_dialog_ui()

