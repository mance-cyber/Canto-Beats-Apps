"""
Canto-beats UI Test - 僅測試界面,不載入 AI 模型
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QSplitter,
    QStatusBar, QMenuBar, QMenu, QMessageBox,
    QTextEdit, QProgressDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent

from core.config import Config
from utils.logger import setup_logger
from ui.style_panel import StyleControlPanel


class TestMainWindow(QMainWindow):
    """簡化版主窗口 - 僅用於 UI 測試"""
    
    video_loaded = Signal(str)
    
    def __init__(self, config: Config):
        super().__init__()
        
        self.config = config
        self.logger = setup_logger()
        self.current_video_path = None
        
        self._init_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def _init_ui(self):
        """Initialize user interface"""
        
        self.setWindowTitle("Canto-beats - 粤语通专业版 [UI 測試模式]")
        self.setMinimumSize(1280, 720)
        self.resize(1600, 900)
        
        # Apply theme
        self._apply_theme()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Video player + timeline
        left_panel = self._create_left_panel()
        
        # Right panel: Controls
        right_panel = self._create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes (70% left, 30% right)
        splitter.setSizes([1120, 480])
        
        main_layout.addWidget(splitter)
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with video player and timeline placeholders"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Video Player Placeholder
        video_placeholder = QLabel("🎬 影片播放器\n\n(需要安裝 python-mpv)")
        video_placeholder.setAlignment(Qt.AlignCenter)
        video_placeholder.setStyleSheet("""
            QLabel {
                background-color: #000;
                color: #666;
                border: 2px dashed #333;
                border-radius: 8px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        # Timeline Placeholder
        timeline_placeholder = QLabel("📊 時間軸編輯器\n\n(波形圖 + 字幕片段)")
        timeline_placeholder.setAlignment(Qt.AlignCenter)
        timeline_placeholder.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                color: #666;
                border: 2px dashed #333;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(video_placeholder, stretch=3)
        layout.addWidget(timeline_placeholder, stretch=2)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with style controls"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("字幕風格控制")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #fff;
                padding: 10px;
            }
        """)
        
        # Transcription Button
        self.transcribe_btn = QPushButton("開始 AI 轉寫")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setMinimumHeight(40)
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #666;
            }
        """)
        self.transcribe_btn.clicked.connect(self._test_transcription)
        
        # Style Control Panel
        self.style_panel = StyleControlPanel()
        self.style_panel.style_changed.connect(self._on_style_changed)
        
        # Wrap in a container to control layout if needed, or just add directly
        # The StyleControlPanel is a QWidget with its own layout
        
        # Result Log
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("轉寫日誌將顯示在這裡...")
        self.log_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        
        # Add welcome message
        self.log_view.append("🎉 歡迎使用 Canto-beats!")
        self.log_view.append("📌 當前為 UI 測試模式")
        self.log_view.append("💡 請使用「文件 > 打開影片」載入影片")
        self.log_view.append("")
        
        layout.addWidget(title)
        layout.addWidget(self.transcribe_btn)
        layout.addWidget(title)
        layout.addWidget(self.transcribe_btn)
        layout.addWidget(self.style_panel, stretch=1)
        layout.addWidget(QLabel("運行日誌:"))
        layout.addWidget(self.log_view, stretch=1)
        
        return panel

    def _on_style_changed(self, options: dict):
        """Handle style changes in test mode"""
        self.log_view.append("\n🎨 風格設定已更新:")
        for key, value in options.items():
            self.log_view.append(f"  • {key}: {value}")
        
        # Scroll to bottom
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def _setup_menu_bar(self):
        """Setup application menu bar"""
        
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打開影片(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("幫助(&H)")
        
        about_action = QAction("關於 Canto-beats(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup status bar"""
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就緒 - UI 測試模式")
    
    def _apply_theme(self):
        """Apply dark theme"""
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border-bottom: 1px solid #3a3a3a;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: #888;
                border-top: 1px solid #3a3a3a;
            }
        """)
    
    def _open_file(self):
        """Open file dialog to select video"""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇影片",
            "",
            "視頻文件 (*.mp4 *.mkv *.mov *.avi *.rmvb *.ts *.flv *.webm *.mpg *.wmv);;所有文件 (*.*)"
        )
        
        if file_path:
            self._load_video(file_path)
    
    def _load_video(self, file_path: str):
        """Load video file (test mode)"""
        
        self.current_video_path = file_path
        self.logger.info(f"Loading video: {file_path}")
        self.status_bar.showMessage(f"已載入: {Path(file_path).name}")
        
        # Enable transcribe button
        self.transcribe_btn.setEnabled(True)
        self.transcribe_btn.setText("開始 AI 轉寫")
        
        # Log
        self.log_view.append(f"\n✅ 已載入影片: {Path(file_path).name}")
        self.log_view.append(f"📁 路徑: {file_path}")
        
        # Emit signal
        self.video_loaded.emit(file_path)
    
    def _test_transcription(self):
        """Test transcription (mock)"""
        
        if not self.current_video_path:
            return
        
        self.log_view.append("\n🔄 開始模擬 AI 轉寫...")
        self.log_view.append("⚠️ 注意: 當前為測試模式,不會執行真實的 AI 處理")
        self.log_view.append("")
        self.log_view.append("如需完整功能,請安裝以下依賴:")
        self.log_view.append("  • openai-whisper")
        self.log_view.append("  • torch")
        self.log_view.append("  • silero-vad")
        self.log_view.append("  • python-mpv")
        self.log_view.append("  • ffmpeg-python")
        
        QMessageBox.information(
            self,
            "測試模式",
            "當前為 UI 測試模式\n\n"
            "如需完整的 AI 轉寫功能,請安裝完整依賴:\n"
            "pip install -r requirements.txt"
        )
    
    def _show_about(self):
        """Show about dialog"""
        
        QMessageBox.about(
            self,
            "關於 Canto-beats",
            "<h2>Canto-beats 粵語通專業版</h2>"
            "<p>版本: 1.0.0 (UI 測試版)</p>"
            "<p>全球唯一一站式粵語影片處理 + 專業播放神器</p>"
            "<p>100% 離線運行</p>"
            "<hr>"
            "<p>© 2025 Canto-beats. All rights reserved.</p>"
        )
    
    # Drag and drop events
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        
        urls = event.mimeData().urls()
        
        if urls:
            file_path = urls[0].toLocalFile()
            
            # Check if file is a video
            video_extensions = {'.mp4', '.mkv', '.mov', '.avi', '.rmvb', 
                               '.ts', '.flv', '.webm', '.mpg', '.wmv'}
            
            if Path(file_path).suffix.lower() in video_extensions:
                self._load_video(file_path)
            else:
                self.status_bar.showMessage("不支持的文件格式", 3000)


def main():
    """Application entry point"""
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Canto-beats UI Test...")
    
    # Load configuration
    config = Config()
    
    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Canto-beats")
    app.setOrganizationName("Canto-beats")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = TestMainWindow(config)
    window.show()
    
    logger.info("UI Test window displayed")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
