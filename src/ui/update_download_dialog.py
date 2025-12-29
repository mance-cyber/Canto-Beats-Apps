"""
Update Download Dialog for Canto-beats.
自動下載和安裝更新的對話框。
"""

from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QMovie

from utils.logger import setup_logger

logger = setup_logger()


class UpdateDownloadWorker(QThread):
    """後台更新 Worker"""

    progress = Signal(int, str)  # (百分比 0-100, 狀態訊息)
    finished = Signal(bool, str, str)  # (成功, 訊息, 安裝路徑)

    def __init__(self, download_url: str):
        super().__init__()
        self.download_url = download_url
        self._cancelled = False
        self._updater = None

    def run(self):
        try:
            from core.auto_updater import AutoUpdater

            self._updater = AutoUpdater()

            # 執行完整更新流程
            success, result = self._updater.perform_update(
                self.download_url,
                progress_callback=self._on_progress
            )

            if self._cancelled:
                self.finished.emit(False, "用戶取消", "")
                return

            if success:
                self.finished.emit(True, "更新完成！", result)
            else:
                self.finished.emit(False, result, "")

        except Exception as e:
            logger.error(f"更新失敗: {e}")
            self.finished.emit(False, f"更新失敗: {e}", "")

    def _on_progress(self, percent: int, message: str):
        """進度回調"""
        if not self._cancelled:
            self.progress.emit(percent, message)

    def cancel(self):
        """取消更新"""
        self._cancelled = True
        if self._updater:
            self._updater.cancel()


class UpdateDownloadDialog(QDialog):
    """更新下載對話框"""

    def __init__(self, download_url: str, version: str = "", parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.version = version
        self.worker = None
        self._success = False
        self._installed_path = ""

        # 無框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedWidth(450)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)

        # GIF 動畫
        self._add_animation(layout)

        # 標題
        version_text = f" v{self.version}" if self.version else ""
        self.title_label = QLabel(f"正在下載更新{version_text}...")
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #FFFFFF;"
        )
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # 狀態訊息
        self.status_label = QLabel("準備中...")
        self.status_label.setStyleSheet("font-size: 13px; color: #00D4AA;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333333;
                border-radius: 8px;
                background-color: #1A1A2E;
                height: 22px;
                text-align: center;
                color: #FFFFFF;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D4AA, stop:1 #00A8CC);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 大小提示
        info_label = QLabel("更新包約 1.3GB，請耐心等待")
        info_label.setStyleSheet("font-size: 11px; color: #888888;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        # 取消按鈕
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: none;
                padding: 10px 40px;
                border-radius: 5px;
                font-size: 13px;
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

        # 對話框樣式
        self.setStyleSheet("""
            QDialog {
                background-color: #16213E;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)

    def _add_animation(self, layout):
        """添加動畫"""
        try:
            # 查找 GIF 路徑
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
                contents_dir = exe_dir.parent
                gif_path = contents_dir / "Resources" / "public" / "Dnlooping.gif"
                if not gif_path.exists():
                    gif_path = contents_dir / "Resources" / "Dnlooping.gif"
            else:
                gif_path = Path(__file__).parent.parent.parent / "public" / "Dnlooping.gif"

            if gif_path.exists():
                animation_label = QLabel()
                animation_label.setFixedSize(100, 100)
                animation_label.setAlignment(Qt.AlignCenter)

                movie = QMovie(str(gif_path))
                movie.setScaledSize(animation_label.size())
                animation_label.setMovie(movie)
                movie.start()

                anim_container = QHBoxLayout()
                anim_container.addStretch()
                anim_container.addWidget(animation_label)
                anim_container.addStretch()
                layout.addLayout(anim_container)
            else:
                self._add_emoji_animation(layout)
        except Exception:
            self._add_emoji_animation(layout)

    def _add_emoji_animation(self, layout):
        """Emoji 動畫（備用）"""
        animation_label = QLabel("🔄")
        animation_label.setFixedSize(100, 100)
        animation_label.setAlignment(Qt.AlignCenter)
        animation_label.setStyleSheet("font-size: 50px;")

        anim_container = QHBoxLayout()
        anim_container.addStretch()
        anim_container.addWidget(animation_label)
        anim_container.addStretch()
        layout.addLayout(anim_container)

    def start_download(self):
        """開始下載更新"""
        self.worker = UpdateDownloadWorker(self.download_url)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        self.show()

    def _on_progress(self, percent: int, message: str):
        """進度更新"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)

    def _on_finished(self, success: bool, message: str, installed_path: str):
        """下載完成"""
        self._success = success
        self._installed_path = installed_path

        if success:
            self.title_label.setText("✅ 更新完成！")
            self.status_label.setText("新版本已安裝")
            self.status_label.setStyleSheet("font-size: 13px; color: #00FF00;")
            self.cancel_btn.setText("關閉")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self._ask_restart)
        else:
            self.title_label.setText("❌ 更新失敗")
            self.status_label.setText(message)
            self.status_label.setStyleSheet("font-size: 13px; color: #FF6B6B;")
            self.cancel_btn.setText("關閉")

    def _on_cancel(self):
        """取消下載"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)  # 等待最多 3 秒
        self.reject()

    def _ask_restart(self):
        """詢問是否重啟"""
        self.hide()

        reply = QMessageBox.question(
            self.parent(),
            "重啟應用",
            "更新已完成！是否立即重啟以使用新版本？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self._restart_app()
        else:
            self.accept()

    def _restart_app(self):
        """重啟應用"""
        try:
            from core.auto_updater import AutoUpdater
            updater = AutoUpdater()
            updater.restart_app(self._installed_path)
        except Exception as e:
            logger.error(f"重啟失敗: {e}")
            QMessageBox.warning(
                self.parent(),
                "重啟失敗",
                f"無法自動重啟，請手動重新打開應用。\n\n錯誤: {e}"
            )
            self.accept()

    def was_successful(self) -> bool:
        """返回是否更新成功"""
        return self._success

    def get_installed_path(self) -> str:
        """返回安裝路徑"""
        return self._installed_path
