"""
Main Window for Canto-beats
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QSplitter,
    QStatusBar, QMenuBar, QMenu, QMessageBox,
    QTextEdit, QProgressDialog, QApplication, QFrame, QToolButton,
    QSizePolicy, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from pathlib import Path
from typing import Optional, List, Dict
import tempfile
import shutil
import os

from core.config import Config
from utils.logger import setup_logger
from ui.transcription_worker_v2 import TranscribeWorkerV2
from ui.video_player import VideoPlayer, create_video_player
from ui.timeline_editor import TimelineEditor
from ui.style_panel import StyleControlPanel
from subtitle.subtitle_exporter import SubtitleExporter
from subtitle.style_processor import StyleProcessor


class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self, config: Config):
        super().__init__()
        
        self.config = config
        self.logger = setup_logger()
        self.current_video_path: Optional[str] = None
        self.original_segments: List[Dict] = []  # Store original segments for style processing
        self.current_segments: List[Dict] = []   # Store processed segments
        self.exporter = SubtitleExporter()
        self.style_processor = StyleProcessor(self.config)
        self.current_style_options = {}
        
        # Resize edge detection for frameless window
        self.RESIZE_MARGIN = 8  # Pixels from edge to trigger resize
        self._resize_direction = None
        self._resize_start_pos = None
        self._resize_start_geometry = None

        # Session-only cache for processed results (cleared on app exit)
        self.cache_dir = Path(tempfile.mkdtemp(prefix="canto-beats-style-"))
        self.processed_cache: Dict[str, List[Dict]] = {}  # In-memory cache
        
        # Initialize notification manager
        from ui.notification_system import NotificationManager
        self.notification_manager = NotificationManager()
        
        self._init_ui()
        self._setup_status_bar()
        self._setup_shortcuts()
        
        # Connect notification signals
        self.notification_manager.notification_count_changed.connect(self._update_notification_badge)
        self._update_notification_badge(self.notification_manager.unread_count)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Install global event filter
        QApplication.instance().installEventFilter(self)
    
    def _toggle_maximize(self):
        """Toggle between maximize and normal window state."""
        if self.isMaximized():
            self.showNormal()
            if hasattr(self, 'max_btn'):
                self.max_btn.setText("□")
        else:
            self.showMaximized()
            if hasattr(self, 'max_btn'):
                self.max_btn.setText("❐")
    
    def _menubar_mouse_press(self, event):
        """Handle menubar mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def _menubar_mouse_move(self, event):
        """Handle menubar mouse move for dragging."""
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_position'):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
        
    def _init_ui(self):
        """Initialize user interface"""
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Enable mouse tracking for resize cursor updates
        self.setMouseTracking(True)
        
        self.setWindowTitle("Canto-beats")
        self.resize(1400, 900)
        
        # Main layout
        central_widget = QWidget()
        central_widget.setMouseTracking(True)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Add edge margins for resize detection (top, bottom edges need space)
        main_layout.setContentsMargins(self.RESIZE_MARGIN, self.RESIZE_MARGIN, 
                                        self.RESIZE_MARGIN, self.RESIZE_MARGIN)
        main_layout.setSpacing(0)
        
        # Custom menu bar (top row with menus + window controls)
        self.custom_menubar = self._create_custom_menubar()
        main_layout.addWidget(self.custom_menubar)
        
        # Content area with padding
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        main_layout.addWidget(content_widget)
        
        # Header Section (now includes menus and window controls)
        header = self._create_header()
        content_layout.addWidget(header)
        
        # Content Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # Left Panel (Video + Timeline)
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right Panel (Controls + Log)
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes (2:1 ratio)
        splitter.setSizes([900, 450])
    
    def _create_custom_menubar(self) -> QWidget:
        """Create custom menu bar for frameless window with menus and window controls."""
        menubar = QWidget()
        menubar.setFixedHeight(32)
        menubar.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
            }
        """)
        
        layout = QHBoxLayout(menubar)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)
        
        # Menu buttons style (VS Code style - clean, centered text)
        menu_btn_style = """
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(90, 93, 94, 0.31);
            }
            QPushButton::menu-indicator {
                width: 0px;
                height: 0px;
            }
        """
        
        # File menu button
        self.file_menu_btn = QPushButton("檔案")
        self.file_menu_btn.setStyleSheet(menu_btn_style)
        self.file_menu_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.file_menu = QMenu(self)
        self._setup_file_menu(self.file_menu)
        self.file_menu_btn.setMenu(self.file_menu)
        layout.addWidget(self.file_menu_btn)
        
        # Help menu button
        self.help_menu_btn = QPushButton("說明")
        self.help_menu_btn.setStyleSheet(menu_btn_style)
        self.help_menu_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.help_menu = QMenu(self)
        self._setup_help_menu(self.help_menu)
        self.help_menu_btn.setMenu(self.help_menu)
        layout.addWidget(self.help_menu_btn)
        
        # Spacer (draggable area)
        spacer = QWidget()
        spacer.setStyleSheet("background: transparent;")
        spacer.mousePressEvent = self._menubar_mouse_press
        spacer.mouseMoveEvent = self._menubar_mouse_move
        spacer.mouseDoubleClickEvent = lambda e: self._toggle_maximize()
        layout.addWidget(spacer, 1)  # Stretch
        
        # Window control buttons
        layout.addStretch()
        
        window_btn_style = """
            QPushButton {
                background: transparent;
                color: #e2e8f0;
                border: none;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(51, 65, 85, 0.8);
            }
        """
        
        # Minimize button
        min_btn = QPushButton("−")
        min_btn.setStyleSheet(window_btn_style)
        min_btn.clicked.connect(self.showMinimized)
        min_btn.setFixedSize(40, 32)
        layout.addWidget(min_btn)
        
        # Close button (special red hover)
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e2e8f0;
                border: none;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ef4444;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(40, 32)
        layout.addWidget(close_btn)
        
        # Apply menu styling
        menu_style = """
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 10px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
            }
            QMenu::separator {
                height: 1px;
                background: #334155;
                margin: 6px 12px;
            }
        """
        self.file_menu.setStyleSheet(menu_style)
        self.help_menu.setStyleSheet(menu_style)
        
        return menubar
    
    def _setup_file_menu(self, menu):
        """Setup file menu actions."""
        open_action = QAction("開啟影片(O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        # Export submenu
        export_menu = menu.addMenu("導出字幕(E)")
        
        export_srt = QAction("導出為 SRT...", self)
        export_srt.triggered.connect(lambda: self._export_subtitles('srt'))
        export_menu.addAction(export_srt)
        
        export_ass = QAction("導出為 ASS...", self)
        export_ass.triggered.connect(lambda: self._export_subtitles('ass'))
        export_menu.addAction(export_ass)
        
        export_txt = QAction("導出為 TXT...", self)
        export_txt.triggered.connect(lambda: self._export_subtitles('txt'))
        export_menu.addAction(export_txt)
        
        menu.addSeparator()
        
        license_action = QAction("授權管理...", self)
        license_action.triggered.connect(self._show_license_dialog)
        menu.addAction(license_action)
        
        clear_license_action = QAction("清除本地授權...", self)
        clear_license_action.triggered.connect(self._clear_license)
        menu.addAction(clear_license_action)
        
        menu.addSeparator()
        
        exit_action = QAction("退出(X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
    
    def _setup_help_menu(self, menu):
        """Setup help menu actions."""
        about_action = QAction("關於 Canto-beats", self)
        about_action.triggered.connect(self._show_about_dialog)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # Dynamic purchase/website button based on license status
        from core.license_manager import LicenseManager
        license_mgr = LicenseManager(self.config)
        
        if license_mgr.is_licensed():
            web_action = QAction("前往官網...", self)
        else:
            web_action = QAction("立即購買...", self)
        
        web_action.triggered.connect(self._open_purchase_or_website)
        menu.addAction(web_action)

    
    def _show_about_dialog(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a,
                    stop:0.5 #1e293b,
                    stop:1 #0f172a
                );
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4,
                    stop:1 #3b82f6
                );
                border-radius: 8px;
                border: none;
                padding: 10px 24px;
                color: white;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2,
                    stop:1 #2563eb
                );
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        # Title with version
        title = QLabel(f"Canto-beats v{self.config.get('version', '1.0.0-macOS')}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #22d3ee;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("AI 粵語字幕生成工具")
        desc.setStyleSheet("font-size: 13px; color: #cbd5e1;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # Copyright
        copyright = QLabel("© 2025 M-pro Team")
        copyright.setStyleSheet("font-size: 12px; color: #64748b;")
        copyright.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright)
        
        layout.addSpacing(8)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setFixedWidth(120)
        ok_btn.setCursor(Qt.PointingHandCursor)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _show_frameless_message(self, title: str, message: str, icon_type: str = "info"):
        """Show a frameless message dialog matching app design.
        
        Args:
            title: Dialog title
            message: Message text
            icon_type: "info", "warning", or "error"
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a,
                    stop:0.5 #1e293b,
                    stop:1 #0f172a
                );
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4,
                    stop:1 #3b82f6
                );
                border-radius: 8px;
                border: none;
                padding: 10px 24px;
                color: white;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2,
                    stop:1 #2563eb
                );
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        icon_map = {
            "info": "[i]",
            "warning": "[!]",
            "error": "[X]"
        }
        icon_emoji = icon_map.get(icon_type, "[i]")
        
        icon_label = QLabel(icon_emoji)
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #22d3ee;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size: 14px; color: #cbd5e1; line-height: 1.5;")
        layout.addWidget(msg_label)
        
        layout.addSpacing(8)
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setFixedWidth(120)
        ok_btn.setCursor(Qt.PointingHandCursor)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()
        
    def _show_debug_menu(self):
        """Show debug menu with test options."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 10px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
            }
        """)
        
        # Test progress dialog
        test_progress_action = QAction("測試進度對話框", self)
        test_progress_action.triggered.connect(self._test_progress_dialog)
        menu.addAction(test_progress_action)
        
        # Test download dialog
        test_download_action = QAction("測試下載對話框", self)
        test_download_action.triggered.connect(self._test_download_dialog)
        menu.addAction(test_download_action)
        
        # Show menu at button position
        menu.exec(self.debug_btn.mapToGlobal(self.debug_btn.rect().bottomLeft()))
    
    def _test_progress_dialog(self):
        """Test progress dialog with simulated processing."""
        import time
        
        progress = QProgressDialog(self)
        progress.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        progress.setWindowTitle("風格處理")
        progress.setLabelText("正在進行 AI 轉譯中... (0%)")
        progress.setRange(0, 0)  # Indeterminate
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Simulate processing
        QApplication.processEvents()
        for i in range(30):
            time.sleep(0.1)
            QApplication.processEvents()
        
        progress.close()
        QMessageBox.information(self, "測試完成", "進度對話框測試完成！")
    
    def _test_download_dialog(self):
        """Test download dialog."""
        from ui.download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(
            model_id="Qwen/Qwen2.5-3B-Instruct",
            quantization="4bit",
            parent=self
        )
        dialog.start_download()
        dialog.exec()
    
    
    def _create_header(self) -> QWidget:
        """Create header with app branding and utilities"""
        header = QWidget()
        header.setObjectName("appHeader")
        header.setMaximumHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left: App branding
        brand_container = QWidget()
        brand_layout = QHBoxLayout(brand_container)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(12)
        
        # Logo Icon - Using app icon
        logo_box = QLabel()
        logo_box.setFixedSize(32, 32)
        logo_box.setStyleSheet("""
            border-radius: 8px;
            padding: 2px;
        """)
        logo_box.setAlignment(Qt.AlignCenter)
        
        # Use the new app icon
        from core.path_setup import get_resource_path
        app_icon_path = get_resource_path("resources/app_icon.png")
        # Try alternate paths
        if not os.path.exists(app_icon_path):
            app_icon_path = get_resource_path("../public/app icon_002.png")
        if not os.path.exists(app_icon_path):
            # Try CWD paths
            for path in ["public/app icon_002.png", "app/public/app icon_002.png"]:
                if os.path.exists(path):
                    app_icon_path = path
                    break
        if os.path.exists(app_icon_path):
            icon = QIcon(app_icon_path)
            logo_box.setPixmap(icon.pixmap(28, 28))
        else:
            # Fallback
            logo_box.setText("CB")
            
        brand_layout.addWidget(logo_box)
        
        # App Title
        title = QLabel("Canto-beats")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #f1f5f9;
            font-family: "Segoe UI", "Microsoft YaHei";
        """)
        brand_layout.addWidget(title)
        
        layout.addWidget(brand_container)
        
        # Action buttons next to logo/title
        action_container = QWidget()
        action_layout = QHBoxLayout(action_container)
        action_layout.setContentsMargins(16, 0, 0, 0)
        action_layout.setSpacing(8)
        
        # License Key Button
        self.license_btn = QPushButton("輸入授權碼")
        self.license_btn.setCursor(Qt.PointingHandCursor)
        self.license_btn.setMinimumHeight(32)
        self.license_btn.setToolTip("輸入授權碼以啟用完整功能")
        self.license_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #a855f7);
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #7e22ce);
            }
        """)
        self.license_btn.clicked.connect(self._show_license_dialog)
        action_layout.addWidget(self.license_btn)
        
        # Export Subtitles Button
        self.export_btn = QPushButton("匯出字幕")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setMinimumHeight(32)
        self.export_btn.setToolTip("匯出字幕檔案 (SRT/ASS) - 需要授權")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #14b8a6, stop:1 #2dd4bf);
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d9488, stop:1 #14b8a6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f766e, stop:1 #0d9488);
            }
        """)
        self.export_btn.clicked.connect(self._show_export_dialog)
        action_layout.addWidget(self.export_btn)
        
        layout.addWidget(action_container)
        layout.addStretch()
        
        # Right: Utility buttons with functionality
        utils_container = QWidget()
        utils_layout = QHBoxLayout(utils_container)
        utils_layout.setContentsMargins(0, 0, 0, 0)
        utils_layout.setSpacing(8)
        
        def create_util_btn(icon_name, tooltip):
            btn = QToolButton()
            from core.path_setup import get_icon_path
            icon_path = get_icon_path(icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(20, 20))
            else:
                # Use emoji fallback
                icons = {"search": "S", "bell": "N", "settings": "G"}
                btn.setText(icons.get(icon_name, icon_name))
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                }
                QToolButton:hover {
                    background: rgba(255,255,255,0.1);
                }
            """)
            return btn
        
        
        # DEBUG: Button to test dialogs (HIDDEN for production)
        # self.debug_btn = create_util_btn("bug", "🔧 調試功能")
        # self.debug_btn.setText("🔧")
        # self.debug_btn.clicked.connect(self._show_debug_menu)
        # utils_layout.addWidget(self.debug_btn)
        
        # Purchase/Website button - Dynamic based on license status
        from core.license_manager import LicenseManager
        license_mgr = LicenseManager(self.config)
        
        self.purchase_btn = QPushButton()
        self.purchase_btn.setCursor(Qt.PointingHandCursor)
        self.purchase_btn.setMinimumHeight(32)
        
        if license_mgr.is_licensed():
            self.purchase_btn.setText("前往官網")
            self.purchase_btn.setToolTip("訪問官方網站")
        else:
            self.purchase_btn.setText("立即購買")
            self.purchase_btn.setToolTip("購買授權以解鎖完整功能")
        
        self.purchase_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:0.5 #ee5a6f, stop:1 #f06292);
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13pt;
                font-weight: bold;
                border: 2px solid #ff8787;
                margin-right: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5252, stop:0.5 #ff4081, stop:1 #f50057);
                border: 2px solid #ff6b6b;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e53935, stop:0.5 #d81b60, stop:1 #c2185b);
            }
        """)
        self.purchase_btn.clicked.connect(self._open_purchase_or_website)
        utils_layout.addWidget(self.purchase_btn)
        
        # Search button - search in subtitles
        self.search_btn = create_util_btn("search", "搜尋字幕 (Ctrl+F)")
        self.search_btn.clicked.connect(self._show_search_dialog)
        utils_layout.addWidget(self.search_btn)
        
        # Bell button - notifications
        self.bell_btn = create_util_btn("bell", "通知中心")
        self.bell_btn.clicked.connect(self._show_notifications)
        utils_layout.addWidget(self.bell_btn)
        
        # Notification badge (unread count)
        self.notification_badge = QLabel("", self.bell_btn)
        self.notification_badge.setStyleSheet("""
            QLabel {
                background-color: #ef4444;
                color: white;
                border-radius: 8px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 5px;
                min-width: 14px;
            }
        """)
        self.notification_badge.setAlignment(Qt.AlignCenter)
        self.notification_badge.move(20, 0)
        self.notification_badge.hide()
        
        # Settings button - open settings
        self.settings_btn = create_util_btn("settings", "設置")
        self.settings_btn.clicked.connect(self._show_settings_dialog)
        utils_layout.addWidget(self.settings_btn)
        
        layout.addWidget(utils_container)
        
        return header
        
    def _create_left_panel(self) -> QWidget:
        """Create left panel with video player and timeline"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)  # Add gap between video and timeline
        
        # Video Player
        self.video_player = create_video_player()
        self.video_player.setObjectName("videoPlayerContainer")
        self.video_player.position_changed.connect(self._on_player_position_changed)
        self.video_player.duration_changed.connect(self._on_player_duration_changed)
        self.video_player.load_video_requested.connect(self._open_file)
        
        # Timeline Editor
        self.timeline = TimelineEditor()
        self.timeline.setObjectName("timelineContainer")
        # Connect timeline seek signal
        self.timeline.seek_requested.connect(self.video_player.seek)
        # Connect subtitle edit signal
        self.timeline.segment_edited.connect(self._on_subtitle_edited)
        
        layout.addWidget(self.video_player, stretch=3)
        layout.addWidget(self.timeline, stretch=2)
        
        return panel
        
    def _on_player_position_changed(self, time_pos: float):
        """Sync timeline with player - update all three tracks"""
        # Use the centralized method that handles auto-scrolling
        self.timeline.set_playhead_position(time_pos)
        
    def _on_player_duration_changed(self, duration: float):
        """Update timeline duration for all tracks"""
        self.timeline.subtitle_track.set_duration(duration)
        self.timeline.video_track.set_duration(duration)
        self.timeline.waveform_track.set_duration(duration)
        
    def _create_right_panel(self) -> QWidget:
        """Create right panel with controls and logs"""
        panel = QWidget()
        panel.setObjectName("controlPanelRoot")
        layout = QVBoxLayout(panel)
        
        # Action Buttons
        self.transcribe_btn = QPushButton("開始 AI 轉寫")
        self.transcribe_btn.setObjectName("primaryButton")
        self.transcribe_btn.setMinimumHeight(48)
        self.transcribe_btn.clicked.connect(self._start_transcription)
        layout.addWidget(self.transcribe_btn)
        
        # Custom Whisper Prompt Input
        prompt_label = QLabel("🎤 自定義詞彙 (可選):")
        prompt_label.setToolTip("輸入歌手名、歌曲名等專有名詞，提高識別準確度")
        prompt_label.setStyleSheet("color: #94a3b8; font-size: 11px; margin-top: 8px;")
        layout.addWidget(prompt_label)
        
        self.custom_prompt_input = QLineEdit()
        self.custom_prompt_input.setPlaceholderText("例如：陳奕迅、張學友、Eason...")
        self.custom_prompt_input.setToolTip("輸入歌手名、歌曲名等，用逗號或頓號分隔")
        self.custom_prompt_input.setText(self.config.get("whisper_custom_prompt", ""))
        self.custom_prompt_input.textChanged.connect(self._on_custom_prompt_changed)
        self.custom_prompt_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                color: #f1f5f9;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        layout.addWidget(self.custom_prompt_input)
        
        # AI Correction feature removed - LLM disabled by default
        
        # Style Control Panel
        layout.addWidget(QLabel("風格控制:"))
        self.style_panel = StyleControlPanel()
        self.style_panel.style_changed.connect(self._on_style_changed)
        layout.addWidget(self.style_panel, stretch=1)
        
        # Log View - HIDDEN
        # layout.addWidget(QLabel("執行日誌:"))
        # self.log_view = QTextEdit()
        # self.log_view.setObjectName("execLog")
        # self.log_view.setReadOnly(True)
        # layout.addWidget(self.log_view, stretch=1)
        
        return panel
        

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就緒")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Space: toggle play (Application-level to avoid focus issues)
        # Note: We also use eventFilter for robustness
        space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        space_shortcut.setContext(Qt.ApplicationShortcut)
        space_shortcut.activated.connect(self.video_player.toggle_play)
        
        # Right arrow: skip forward 5s
        right_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        right_shortcut.activated.connect(lambda: self.video_player.skip(5))
        
        # Left arrow: skip backward 5s
        left_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        left_shortcut.activated.connect(lambda: self.video_player.skip(-5))
        
        # Shift+Right: skip forward 30s
        shift_right = QShortcut(QKeySequence(Qt.SHIFT | Qt.Key_Right), self)
        shift_right.activated.connect(lambda: self.video_player.skip(30))
        
        
        # Shift+Left: skip backward 30s
        shift_left = QShortcut(QKeySequence(Qt.SHIFT | Qt.Key_Left), self)
        shift_left.activated.connect(lambda: self.video_player.skip(-30))
        
        # Undo/Redo (Timeline)
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.timeline.undo)
        
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.timeline.redo)
        
        redo_shift_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shift_shortcut.activated.connect(self.timeline.redo)
    
    def eventFilter(self, obj, event):
        """Global event filter for shortcuts"""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                self.video_player.toggle_play()
                return True
        return super().eventFilter(obj, event)
    
    def _get_resize_direction(self, pos):
        """Determine resize direction based on mouse position."""
        rect = self.rect()
        margin = self.RESIZE_MARGIN
        
        left = pos.x() < margin
        right = pos.x() > rect.width() - margin
        top = pos.y() < margin
        bottom = pos.y() > rect.height() - margin
        
        if top and left:
            return 'top-left'
        elif top and right:
            return 'top-right'
        elif bottom and left:
            return 'bottom-left'
        elif bottom and right:
            return 'bottom-right'
        elif left:
            return 'left'
        elif right:
            return 'right'
        elif top:
            return 'top'
        elif bottom:
            return 'bottom'
        return None
    
    def _update_cursor_shape(self, direction):
        """Update cursor shape based on resize direction."""
        cursor_map = {
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'top-left': Qt.SizeFDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor,
        }
        if direction in cursor_map:
            self.setCursor(cursor_map[direction])
        else:
            self.unsetCursor()
    
    def mousePressEvent(self, event):
        """Handle mouse press for resizing."""
        if event.button() == Qt.LeftButton:
            direction = self._get_resize_direction(event.position().toPoint())
            if direction:
                self._resize_direction = direction
                self._resize_start_pos = event.globalPosition().toPoint()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for resizing."""
        if self._resize_direction and self._resize_start_pos:
            # Currently resizing
            delta = event.globalPosition().toPoint() - self._resize_start_pos
            geo = self._resize_start_geometry
            new_geo = self.geometry()
            
            min_width = 600
            min_height = 10
            
            if 'left' in self._resize_direction:
                new_left = geo.left() + delta.x()
                new_width = geo.width() - delta.x()
                if new_width >= min_width:
                    new_geo.setLeft(new_left)
            if 'right' in self._resize_direction:
                new_width = geo.width() + delta.x()
                if new_width >= min_width:
                    new_geo.setWidth(new_width)
            if 'top' in self._resize_direction:
                new_top = geo.top() + delta.y()
                new_height = geo.height() - delta.y()
                if new_height >= min_height:
                    new_geo.setTop(new_top)
            if 'bottom' in self._resize_direction:
                new_height = geo.height() + delta.y()
                if new_height >= min_height:
                    new_geo.setHeight(new_height)
            
            self.setGeometry(new_geo)
            event.accept()
            return
        else:
            # Update cursor shape based on position
            direction = self._get_resize_direction(event.position().toPoint())
            self._update_cursor_shape(direction)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after resizing."""
        if event.button() == Qt.LeftButton and self._resize_direction:
            self._resize_direction = None
            self._resize_start_pos = None
            self._resize_start_geometry = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _open_file(self):
        """Open a video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "開啟影片", "", "Video Files (*.mp4 *.mkv *.avi *.mov)"
        )
        
        if file_path:
            self._load_video(file_path)
            
    def _load_video(self, file_path: str):
        """Load and prepare video"""
        self.current_video_path = file_path
        
        # Clear ALL old data when loading a new video
        self.original_segments = []
        self.current_segments = []
        self.processed_cache = {}
        self.timeline.subtitle_track.set_segments([])
        self.timeline.subtitle_track.update()
        self.logger.info("[OK] Cleared all segment data and cache")
        
        # Clear pipeline audio cache to avoid using stale audio
        import tempfile
        import shutil
        cache_dir = Path(tempfile.gettempdir()) / "canto_beats_v2"
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                self.logger.info(f"[OK] Cleared pipeline cache: {cache_dir}")
            except Exception as e:
                self.logger.warning(f"Could not clear cache: {e}")
        
        self.video_player.load_video(file_path)
        self.timeline.load_video(file_path)  # Extract and load thumbnails
        self.status_bar.showMessage(f"已載入: {Path(file_path).name}")
        self.logger.info(f"[OK] Opened file: {file_path}")
        
        # Auto-prompt removed by user request
        # User will manually click the "Start Transcription" button
            
    def _start_transcription(self):
        """Start AI transcription V2."""
        self.logger.info("[DEBUG] _start_transcription START")
        
        # Prevent multiple simultaneous transcriptions
        self.logger.info(f"[DEBUG] worker check: {hasattr(self, 'worker')}, {getattr(self, 'worker', None)}")
        if hasattr(self, 'worker') and self.worker:
            self.logger.warning("[!] Transcription already in progress")
            self.status_bar.showMessage("[!] Transcription in progress", 3000)
            return
        
        self.logger.info(f"[DEBUG] video_path: {self.current_video_path}")
        if not self.current_video_path:
            self.logger.info("[DEBUG] No video - showing warning")
            self._show_frameless_message(
                "Please open video",
                "Please open a video file first",
                "warning"
            )
            return
        
        # Check if Whisper model is cached (Qwen is only needed for written Chinese)
        self.logger.info("[DEBUG] Checking Whisper model cache...")
        is_first_time = not self.config.is_model_cached("whisper")
        self.logger.info(f"[DEBUG] is_first_time (Whisper not cached): {is_first_time}")
        
        if is_first_time:
            # ========================================
            # STEP 1: Show confirmation dialog FIRST
            # ========================================
            self.logger.info("[DEBUG] Showing first-time confirmation dialog...")
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("首次設定")
            msg.setIcon(QMessageBox.Information)
            msg.setText("首次設定 - 需要下載 AI 工具")
            msg.setInformativeText(
                "首次轉寫需要下載 AI 工具 (約 3-5 GB)。\n"
                "下載時間視網絡速度而定 (約 5-15 分鐘)。\n\n"
                "下載完成後，可離線使用！\n\n"
                "是否繼續？"
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            # Apply dark theme style
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #1e293b;
                    color: #f1f5f9;
                }
                QMessageBox QLabel {
                    color: #f1f5f9;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            
            if msg.exec() != QMessageBox.Yes:
                return
            
            # ========================================
            # STEP 2: Download AI tools in MAIN THREAD
            # with visible progress dialog
            # ========================================
            self.logger.info("[DEBUG] Starting AI tools download...")
            from ui.download_dialog import ModelDownloadDialog, MLXWhisperDownloadWorker
            
            # Create download dialog for MLX Whisper
            model_path = "mlx-community/whisper-large-v3-mlx"
            download_dialog = ModelDownloadDialog(model_path, parent=self)
            download_dialog.setWindowTitle("AI 工具下載")
            
            # Use MLX Whisper worker
            download_dialog.worker = MLXWhisperDownloadWorker("large-v3")
            download_dialog.worker.progress.connect(download_dialog._on_progress)
            download_dialog.worker.finished.connect(download_dialog._on_finished)
            download_dialog.worker.start()
            
            # Show dialog and wait for download to complete
            result = download_dialog.exec()
            
            if not download_dialog.was_successful():
                self.logger.warning("AI tools download failed or cancelled")
                self._show_frameless_message(
                    "下載失敗",
                    "AI 工具下載失敗或已取消。\n請稍後重試。",
                    "warning"
                )
                return
            
            self.logger.info("[DEBUG] AI tools download completed successfully")
        
        # ========================================
        # STEP 3: Start normal transcription
        # ========================================
        self.logger.info("[START] Beginning AI transcription...")
        
        # Disable button during processing
        self.transcribe_btn.setEnabled(False)

        # LLM disabled during transcription - only used for 書面語 conversion
        enable_llm = False

        # Create worker (is_first_time=False now since download is done)
        from ui.transcription_worker_v2 import TranscribeWorkerV2
        self.worker = TranscribeWorkerV2(
            self.config,
            self.current_video_path,
            force_cpu=False,
            enable_llm=enable_llm,
            is_first_time=False  # Download already done
        )
        self.worker.progress.connect(self._on_transcription_progress)
        self.worker.completed.connect(self._on_transcription_finished)
        self.worker.error.connect(self._on_transcription_error)
        
        # Show animated progress dialog
        from ui.animated_progress_dialog import AnimatedProgressDialog
        self.progress_dialog = AnimatedProgressDialog(self)
        self.progress_dialog.setLabelText("正在加載 AI 工具...")
        self.progress_dialog.canceled.connect(self._on_transcription_canceled)
        self.progress_dialog.show()
        
        self.worker.start()
        
    def _on_transcription_canceled(self):
        """Handle transcription cancellation"""
        self.logger.info("[CANCEL] User cancelled transcription")
        
        # Cancel worker
        if self.worker:
            self.worker.cancel()
            # Wait for worker to finish (with timeout)
            try:
                self.worker.wait()
            except Exception as e:
                self.logger.error(f"Error waiting for worker: {e}")
            
            # Cleanup worker resources
            try:
                self.worker.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up worker: {e}")
            
            # Clear worker reference
            self.worker = None
        
        # Close dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Re-enable button
        self.transcribe_btn.setEnabled(True)
        self.status_bar.showMessage("已取消轉寫", 3000)
        
    def _on_transcription_progress(self, msg: str, value: int):
        """Update progress"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(msg)
            self.progress_dialog.setValue(value)
        self.status_bar.showMessage(msg)
        
    def _on_transcription_finished(self, result: dict):
        """Handle successful transcription"""
        try:
            self.transcribe_btn.setEnabled(True)
            if self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            # Cleanup worker
            if self.worker:
                try:
                    self.worker.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up worker: {e}")
                self.worker = None
                
            # Log to log_view
            if hasattr(self, 'log_view'):
                self.log_view.append("[OK] Transcription complete!")
                self.log_view.append(f"語言: {result.get('language', 'unknown')}")
                tier = result.get('hardware_tier', 'unknown')
                self.log_view.append(f"硬件層級: {tier}")
            
            # Show result summary
            segments = result.get('segments', [])
            audio_path = result.get('audio_path', '')
            lang = result.get('language', 'unknown')
            
            # V2 segments are already dicts with 'text' key
            segments_dicts = []
            for seg in segments:
                if isinstance(seg, dict):
                    segments_dicts.append(seg)
                elif hasattr(seg, '__dict__'):
                    segments_dicts.append({
                        'start': seg.start,
                        'end': seg.end,
                        'text': getattr(seg, 'text', getattr(seg, 'colloquial', '')),
                    })
            
            # Store segments for export and processing
            self.original_segments = segments_dicts
            self.current_segments = segments_dicts
            
            # Get current options from panel
            self.logger.info("Step 5: Getting style options")
            if hasattr(self, 'style_panel'):
                self.current_style_options = self.style_panel.get_current_options()
            
            # Apply current style options immediately
            self.logger.info("Step 6: Applying style or setting segments")
            if self.current_style_options:
                self._apply_style_processing()
            else:
                # Update Timeline with segments and audio
                self.timeline.set_segments(segments_dicts)
                self._update_video_subtitles()
            
            self.logger.info("Step 7: Loading audio to timeline")
            if audio_path:
                print("DEBUG: Loading audio to timeline...")
                self.timeline.load_audio(audio_path, self.video_player.duration)
                print("DEBUG: Audio loaded to timeline")
                
            # Update video player subtitles
            print("DEBUG: Final subtitle update...")
            self._update_video_subtitles()
            print("DEBUG: Subtitle updated, showing message...")
            
            # Show completion in log_view instead of QMessageBox to avoid thread issues
            num_segs = len(segments)
            if hasattr(self, 'log_view'):
                self.log_view.append(f"字幕片段: {num_segs}")
                self.log_view.append("─" * 20)
            
            # Update status bar
            self.status_bar.showMessage(f"AI 轉寫完成! 共 {num_segs} 個字幕片段", 5000)
            
            print("DEBUG: All done!")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Error in transcription callback: {e}", exc_info=True)
            if hasattr(self, 'log_view'):
                self.log_view.append(f"[X] Error displaying results: {str(e)}")
        
    def _on_transcription_error(self, error_msg: str):
        """Handle transcription error"""
        self.transcribe_btn.setEnabled(True)
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Cleanup worker
        if self.worker:
            try:
                self.worker.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up worker after error: {e}")
            self.worker = None
            
        self.logger.error(f"Transcription error: {error_msg}")
        # self.log_view.append(f"❌ 錯誤: {error_msg}")
        QMessageBox.critical(self, "錯誤", f"轉寫失敗:\n{error_msg}")
        
    def _on_subtitle_edited(self, index: int, new_text: str):
        """Handle subtitle text edit/add/delete from timeline"""
        
        # Handle deletion (index = -1)
        if index == -1:
            self.logger.info("Subtitle deleted from timeline")
            # Sync current_segments with timeline
            self.current_segments = self.timeline.track.segments.copy()
            # self.log_view.append(f"🗑️ 已刪除字幕")
            self.status_bar.showMessage(f"已刪除字幕", 3000)
            self._update_video_subtitles()
            return
        
        # Handle edit or add
        self.logger.info(f"Subtitle {index} edited/added: {new_text[:50]}...")
        
        # Sync current_segments with timeline (handles both edit and add)
        self.current_segments = self.timeline.track.segments.copy()
        
        # Log the operation
        if index >= 0 and index < len(self.current_segments):
            action = "已編輯" if new_text else "已添加"
            # self.log_view.append(f"✏️ {action}字幕 #{index+1}: {new_text[:30]}...")
            self.status_bar.showMessage(f"{action}字幕 #{index+1}", 3000)
        
        # Update video player subtitles
        self._update_video_subtitles()
    
    def _on_custom_prompt_changed(self, text: str):
        """Handle custom Whisper prompt change."""
        self.config.set("whisper_custom_prompt", text.strip())
        self.logger.info(f"Custom prompt updated: {text[:50]}..." if len(text) > 50 else f"Custom prompt updated: {text}")
    
    def _on_style_changed(self, options: dict):
        """Handle style options change from StyleControlPanel."""
        self.current_style_options = options
        self.logger.info(f"Style options updated: {options}")
        
        # If we have segments, immediately reprocess them
        if self.original_segments:
            self._apply_style_processing()
    
    def _apply_style_processing(self):
        """Apply style processing to original segments and update display."""
        if not self.original_segments:
            return

        # Create cache key from video path + options
        import json
        import hashlib

        video_hash = hashlib.md5(str(self.current_video_path).encode()).hexdigest()[:8]
        options_str = json.dumps(self.current_style_options, sort_keys=True)
        cache_key = f"{video_hash}_{hashlib.md5(options_str.encode()).hexdigest()[:8]}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Check disk cache first
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    self.current_segments = cached_data['segments']
                    self.timeline.set_segments(self.current_segments)
                    self._update_video_subtitles()
                    self.logger.info(f"✅ [CACHE] Loaded from disk: {cache_file.name}")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
            
        self.logger.info("[STYLE] Applying style processing...")
        
        # Check if AI processing is needed
        # AI is only needed for:
        # 1. Language style conversion (書面語 or 半書面語)
        # 2. English translation (translate mode, not keep)
        style = self.current_style_options.get('style', 'spoken')
        english_mode = self.current_style_options.get('english', 'keep')
        
        # AI only needed for style conversion or english translation
        needs_ai = style in ('semi', 'written') or english_mode == 'translate'
        
        # Show progress dialog if AI processing is needed
        progress_dialog = None
        if needs_ai:
            progress_dialog = QProgressDialog(self)
            progress_dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            progress_dialog.setWindowTitle("風格處理")
            progress_dialog.setLabelText("正在進行 AI 轉譯中... (0%)")
            progress_dialog.setRange(0, 100)  # Determinate progress 0-100%
            progress_dialog.setValue(0)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setCancelButton(None)  # No cancel button
            progress_dialog.setMinimumDuration(0)  # Show immediately
            progress_dialog.setAutoClose(True)
            progress_dialog.setAutoReset(True)
            progress_dialog.show()
            QApplication.processEvents()  # Force UI update
        
        # Progress callback function
        def update_progress(current, total, message):
            if progress_dialog:
                percentage = int((current / total) * 100) if total > 0 else 0
                progress_dialog.setValue(percentage)
                progress_dialog.setLabelText(f"{message} ({percentage}%)")
                QApplication.processEvents()
        
        try:
            # Process segments with StyleProcessor
            processed_segments = self.style_processor.process(
                self.original_segments,
                self.current_style_options,
                progress_callback=update_progress if needs_ai else None
            )

            # Save to disk cache
            try:
                cache_data = {
                    'video_path': str(self.current_video_path),
                    'options': self.current_style_options,
                    'segments': processed_segments
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"💾 Saved to cache: {cache_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to save cache: {e}")

            # Update current segments
            self.current_segments = processed_segments
            
            # Update timeline display
            self.timeline.set_segments(processed_segments)
            
            # Update video subtitles
            self._update_video_subtitles()
            
            self.logger.info("[OK] Style processing complete")
            
        except Exception as e:
            self.logger.error(f"Style processing failed: {e}")
            self.logger.error(f"[X] Style processing failed: {str(e)}")
        finally:
            # Close progress dialog
            if progress_dialog:
                progress_dialog.setValue(100)
                progress_dialog.close()
    
    
    
    def _update_video_subtitles(self):
        """Generate temp SRT and update video player"""
        if not self.current_segments:
            return
            
        try:
            # Create temp file
            fd, path = tempfile.mkstemp(suffix='.srt')
            os.close(fd)
            
            # Export to temp file
            if self.exporter.export_srt(self.current_segments, path):
                self.video_player.load_subtitle(path)
                # Note: We don't delete immediately as mpv needs to load it
                # In a real app we'd manage temp files better
        except Exception as e:
            self.logger.error(f"Failed to update video subtitles: {e}")
    
    def _export_subtitles(self, format_type: str):
        """Export subtitles to specified format"""
        # Check license status first
        from core.license_manager import LicenseManager
        license_mgr = LicenseManager(self.config)
        
        if not license_mgr.is_licensed():
            self._show_frameless_message(
                "需要授權",
                "此功能需要授權才能使用\n\n"
                "您需要啟用授權才能導出字幕檔。\n\n"
                "請前往我們的官方網站購買授權以解鎖完整功能 ✨",
                "error"
            )
            self.logger.warning("[X] Export failed: Unauthorized")
            return
        
        if not self.current_segments:
            QMessageBox.warning(
                self,
                "無法導出",
                "請先完成 AI 轉寫以產生字幕。"
            )
            return

        
        # File extensions
        extensions = {
            'srt': ('SRT 字幕檔案 (*.srt)', '.srt'),
            'ass': ('ASS 字幕檔案 (*.ass)', '.ass'),
            'txt': ('純文本檔案 (*.txt)', '.txt')
        }
        
        ext_filter, ext =extensions[format_type]
        
        # Default filename
        default_name = ""
        if self.current_video_path:
            default_name = Path(self.current_video_path).stem + ext
        
        # Save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"導出 {format_type.upper()} 字幕",
            default_name,
            ext_filter
        )
        
        if not file_path:
            return
        
        # Export
        success = False
        if format_type == 'srt':
            success = self.exporter.export_srt(self.current_segments, file_path)
        elif format_type == 'ass':
            success = self.exporter.export_ass(self.current_segments, file_path)
        elif format_type == 'txt':
            success = self.exporter.export_txt(self.current_segments, file_path)
        
        if success:
            self.status_bar.showMessage(f"已導出至: {Path(file_path).name}", 5000)
            self.logger.info(f"[OK] Export success: {file_path}")
            QMessageBox.information(
                self,
                "導出成功",
                f"字幕已成功導出至:\n{file_path}"
            )
        else:
            self.status_bar.showMessage("導出失敗", 3000)
            QMessageBox.critical(
                self,
                "導出失敗",
                "無法導出字幕檔案。"
            )
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "關於 Canto-beats",
            "<h3>Canto-beats 粵語通專業版</h3>"
            "<p>版本: 0.1.0</p>"
            "<p>基於先進AI技術的粵語視頻字幕生成工具。</p>"
            "<p>開發者: Antigravity</p>"
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            file_path = files[0]
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv']
            if Path(file_path).suffix.lower() in video_extensions:
                self._load_video(file_path)
            else:
                self.status_bar.showMessage("不支援的檔案格式", 3000)
    
    def _show_debug_download_dialog(self):
        """DEBUG: Show download dialog for testing."""
        from ui.download_dialog import ModelDownloadDialog
        
        # Test with Qwen2.5-7B model
        dialog = ModelDownloadDialog(
            "Qwen/Qwen2.5-3B-Instruct", 
            quantization="4bit",
            parent=self
        )
        dialog.start_download()
        dialog.exec()
    
    def _show_search_dialog(self):
        """Show search dialog to find text in subtitles."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
        from PySide6.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(350)
        
        # Dark theme styling
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1d23;
                color: #e2e8f0;
                border: 1px solid #374151;
                border-radius: 8px;
            }
            QLineEdit {
                background-color: #252a34;
                color: #e2e8f0;
                border: 1px solid #3b82f6;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #60a5fa;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
            }
            QListWidget {
                background-color: #252a34;
                color: #e2e8f0;
                border: 1px solid #374151;
                border-radius: 6px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #374151;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
            }
            QListWidget::item:hover {
                background-color: #374151;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        
        # Title
        title = QLabel("搜索字幕")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 20px;
                font-weight: bold;
                margin: 0;
                padding: 0;
            }
            QPushButton:hover {
                background: #374151;
                color: #ef4444;
                border-radius: 4px;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dialog.reject)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Search input
        search_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("輸入搜索文字...")
        search_btn = QPushButton("搜索")
        search_layout.addWidget(search_input, 1)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # Results list
        results_label = QLabel("搜索結果:")
        layout.addWidget(results_label)
        
        results_list = QListWidget()
        layout.addWidget(results_list, 1)
        
        # Status label
        status_label = QLabel("")
        status_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(status_label)
        
        def do_search():
            text = search_input.text().strip()
            if not text:
                return
                
            results_list.clear()
            
            if hasattr(self, 'subtitle_segments') and self.subtitle_segments:
                found = []
                for i, seg in enumerate(self.subtitle_segments):
                    seg_text = seg.get('text', '')
                    if text.lower() in seg_text.lower():
                        item = QListWidgetItem(f"[{i+1}] {seg_text}")
                        item.setData(Qt.UserRole, i)
                        results_list.addItem(item)
                        found.append(i)
                
                if found:
                    status_label.setText(f"[OK] Found {len(found)} matches")
                    status_label.setStyleSheet("color: #22c55e;")
                else:
                    status_label.setText(f"[X] Not found: {text}")
                    status_label.setStyleSheet("color: #ef4444;")
            else:
                status_label.setText("[!] Please transcribe first")
                status_label.setStyleSheet("color: #f59e0b;")
        
        def on_item_clicked(item):
            idx = item.data(Qt.UserRole)
            if idx is not None and hasattr(self, 'timeline_editor'):
                seg = self.subtitle_segments[idx]
                # Jump to the segment
                if 'start' in seg:
                    self.video_player.seek(seg['start'])
                dialog.accept()
        
        search_btn.clicked.connect(do_search)
        search_input.returnPressed.connect(do_search)
        results_list.itemDoubleClicked.connect(on_item_clicked)
        
        dialog.exec()
    
    def _show_status_info(self):
        """Show system status information."""
        import torch
        from PySide6.QtWidgets import QMessageBox
        
        # Gather status info - cross-platform GPU detection
        if torch.backends.mps.is_available():
            gpu_status = "已啟用 (Apple Metal)"
            gpu_name = "Apple Silicon GPU"
        elif torch.cuda.is_available():
            gpu_status = "已啟用"
            gpu_name = torch.cuda.get_device_name(0)
        else:
            gpu_status = "未啟用"
            gpu_name = "N/A"
        
        # Check AI model status
        ai_status = "未安裝"
        if hasattr(self, 'style_panel') and hasattr(self.style_panel, 'downloader'):
            if self.style_panel.downloader.is_model_installed():
                ai_status = "已安裝"
        
        # Subtitle count
        sub_count = len(self.subtitle_segments) if hasattr(self, 'subtitle_segments') and self.subtitle_segments else 0
        
        info = f"""
系統狀態:
─────────────
GPU 加速: {gpu_status}
GPU 型號: {gpu_name}
AI 校正模型: {ai_status}
當前字幕數: {sub_count}
OpenCC 轉換: 已啟用
        """
        
        QMessageBox.information(self, "系統狀態", info.strip())
    
    def _show_settings_dialog(self):
        """Show settings dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QSpinBox, QCheckBox, QDialogButtonBox, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setWindowTitle("設置")
        dialog.setMinimumWidth(350)
        
        # Dark theme styling for the dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #374151;
                border-radius: 8px;
            }
            QLabel {
                color: #f1f5f9;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #06b6d4;
            }
            QCheckBox {
                color: #f1f5f9;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #475569;
                background: #334155;
            }
            QCheckBox::indicator:checked {
                background: #06b6d4;
                border-color: #06b6d4;
            }
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #06b6d4;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # VAD settings
        max_gap_spin = QSpinBox()
        max_gap_spin.setRange(100, 2000)
        max_gap_spin.setValue(300)
        max_gap_spin.setSuffix(" ms")
        form.addRow("斷句間隔:", max_gap_spin)
        
        max_chars_spin = QSpinBox()
        max_chars_spin.setRange(10, 50)
        max_chars_spin.setValue(22)
        form.addRow("每行最大字數:", max_chars_spin)
        
        # Options
        auto_scroll = QCheckBox("啟用")
        auto_scroll.setChecked(True)
        form.addRow("時間軸自動滾動:", auto_scroll)
        
        layout.addLayout(form)
        
        # === Update Section ===
        from PySide6.QtWidgets import QFrame, QHBoxLayout
        
        update_frame = QFrame()
        update_frame.setStyleSheet("""
            QFrame {
                background-color: #334155;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        update_layout = QVBoxLayout(update_frame)
        update_layout.setSpacing(8)
        
        update_title = QLabel("軟體更新")
        update_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #22d3ee;")
        update_layout.addWidget(update_title)
        
        # Auto update checkbox
        auto_update_check = QCheckBox("啟動時自動檢查更新")
        auto_update_check.setChecked(self.config.get("auto_check_update", True))
        update_layout.addWidget(auto_update_check)
        
        # Check update button
        check_update_btn = QPushButton("檢查更新")
        check_update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #3b82f6);
                color: white;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #2563eb);
            }
        """)
        check_update_btn.clicked.connect(lambda: self._check_for_update(dialog))
        update_layout.addWidget(check_update_btn)
        
        # Version info
        version_label = QLabel(f"目前版本: v1.0.0")
        version_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        update_layout.addWidget(version_label)
        
        layout.addWidget(update_frame)
        
        # Note
        note = QLabel("注意: 設置會在下次轉寫時生效")
        note.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(note)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            # Save auto update setting
            self.config.set("auto_check_update", auto_update_check.isChecked())
    
    def _check_for_update(self, parent_dialog=None):
        """Check for application updates."""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        from core.update_checker import UpdateChecker
        
        # Show progress
        progress = QProgressDialog("正在檢查更新...", None, 0, 0, parent_dialog or self)
        progress.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()
        
        try:
            # Use GitHub Releases API
            checker = UpdateChecker()
            has_update, update_info = checker.check_for_update()
            
            progress.close()
            
            if has_update and update_info:
                # Show update available dialog
                msg = QMessageBox(parent_dialog or self)
                msg.setWindowTitle("發現新版本")
                msg.setIcon(QMessageBox.Information)
                msg.setText(f"新版本 v{update_info.version} 可用！")
                msg.setInformativeText(
                    f"發布日期: {update_info.release_date}\n\n"
                    f"更新內容:\n{update_info.changelog}\n\n"
                    "是否前往下載？"
                )
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)
                
                # Apply dark theme
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #1e293b;
                        color: #f1f5f9;
                    }
                    QMessageBox QLabel {
                        color: #f1f5f9;
                    }
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 6px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
                
                if msg.exec() == QMessageBox.Yes:
                    checker.open_download_page(update_info.download_url)
            else:
                # No update available
                self._show_frameless_message(
                    "已是最新版本",
                    "你的 Canto-beats 已經是最新版本！",
                    "info"
                )
                
        except Exception as e:
            progress.close()
            self.logger.error(f"Update check failed: {e}")
            self._show_frameless_message(
                "檢查失敗",
                f"無法檢查更新，請稍後再試。\n錯誤: {str(e)}",
                "error"
            )

    def _show_notifications(self):
        """Show notification center dialog."""
        from ui.notification_system import NotificationDialog
        dialog = NotificationDialog(self.notification_manager, self)
        dialog.exec()
        # Update badge after closing
        self._update_notification_badge(self.notification_manager.unread_count)

    def _show_license_dialog(self):
        """Show license activation dialog."""
        from core.license_manager import LicenseManager
        from ui.license_dialog import LicenseDialog
        
        license_mgr = LicenseManager(self.config)
        dialog = LicenseDialog(license_mgr, self)
        if dialog.exec() == LicenseDialog.Accepted:
            self.status_bar.showMessage("[OK] License activated!", 5000)
            self.logger.info("[OK] License activated successfully")

    def _clear_license(self):
        """Clear local license with 'delete' verification"""
        from core.license_manager import LicenseManager
        license_mgr = LicenseManager(self.config)
        
        # Create custom confirmation dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 12px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("清除本地授權")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ef4444;")
        layout.addWidget(title)
        
        # Warning text
        warning = QLabel(
            "⚠️ 請慎重執行此操作！\n\n"
            "清除後，本機的授權記錄將被永久刪除。\n"
            "若您的序號已綁定此設備，將消耗一次轉移機會。\n\n"
            "請在下方輸入 'delete' 以確認清除："
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("font-size: 12px; color: #fbbf24; line-height: 1.6;")
        layout.addWidget(warning)
        
        # Input field
        input_field = QLineEdit()
        input_field.setPlaceholderText("輸入 delete")
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 2px solid #444;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ef4444;
            }
        """)
        layout.addWidget(input_field)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("確認清除")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef4444;
            }
        """)
        confirm_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)
        
        # Show dialog
        if dialog.exec() == QDialog.Accepted:
            if input_field.text() == "delete":
                if license_mgr.clear_license():
                    self.status_bar.showMessage("[OK] 本地授權已清除", 5000)
                    QMessageBox.information(self, "成功", "本地授權已成功清除。")
                else:
                    QMessageBox.warning(self, "失敗", "未找到本地授權文件或清除失敗。")
            else:
                QMessageBox.warning(self, "驗證失敗", "輸入內容不符，操作已取消。")

    def _show_export_dialog(self):
        """Show export format selection menu."""
        # Check license first
        from core.license_manager import LicenseManager
        license_mgr = LicenseManager(self.config)
        
        if not license_mgr.is_licensed():
            self._show_frameless_message(
                "需要授權",
                "匯出字幕功能需要啟用授權。\n\n請點擊「輸入授權碼」按鈕啟用授權，\n或點擊「立即購買」購買授權。",
                "warning"
            )
            return
        
        if not self.current_segments or len(self.current_segments) == 0:
            self._show_frameless_message(
                "無法匯出",
                "請先進行 AI 轉寫以生成字幕。",
                "warning"
            )
            return
        
        # Show format selection menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 10px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #14b8a6;
            }
        """)
        
        srt_action = menu.addAction("SRT 字幕檔 (.srt)")
        srt_action.triggered.connect(lambda: self._export_subtitles('srt'))
        
        ass_action = menu.addAction("ASS 字幕檔 (.ass)")
        ass_action.triggered.connect(lambda: self._export_subtitles('ass'))
        
        txt_action = menu.addAction("純文字 (.txt)")
        txt_action.triggered.connect(lambda: self._export_subtitles('txt'))
        
        # Show menu at button position
        menu.exec(self.export_btn.mapToGlobal(self.export_btn.rect().bottomLeft()))

    def _open_purchase_or_website(self):
        """Open purchase page or website based on license status."""
        import webbrowser
        from core.license_manager import LicenseManager
        
        license_mgr = LicenseManager(self.config)
        
        if license_mgr.is_licensed():
            # Open official website for licensed users
            url = "https://cantobeats.com" # TODO: Replace with actual website URL
            self.logger.info(f"[WEB] Opening website: {url}")
        else:
            # Open purchase page for unlicensed users
            url = "https://buy.stripe.com/7sY28j6nTahud3Mfxa4Vy01"
            self.logger.info(f"[BUY] Opening purchase page: {url}")
        
        try:
            webbrowser.open(url)
            self.status_bar.showMessage(f"已開啟網頁: {url}", 3000)
        except Exception as e:
            self.logger.error(f"無法開啟網頁: {e}")
            QMessageBox.warning(self, "錯誤", f"無法開啟網頁瀏覽器\n{str(e)}")

    def _update_notification_badge(self, count: int):
        """Update the notification badge count."""
        if count > 0:
            self.notification_badge.setText(str(count) if count < 10 else "9+")
            self.notification_badge.show()
        else:
            self.notification_badge.hide()

    def _show_debug_menu(self):
        """Show debug menu with various testing options."""
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #334155;
            }
            QMenu::separator {
                height: 1px;
                background-color: #475569;
                margin: 4px 10px;
            }
        """)
        
        # Model cache status
        action_cache = menu.addAction("Check model cache status")
        action_cache.triggered.connect(self._debug_check_cache)
        
        # GPU status
        action_gpu = menu.addAction("顯示 GPU 狀態")
        action_gpu.triggered.connect(self._debug_show_gpu_status)
        
        menu.addSeparator()
        
        # Clear model cache
        action_clear = menu.addAction("Clear model cache")
        action_clear.triggered.connect(self._debug_clear_cache)
        
        # Simulate first-time download
        action_simulate = menu.addAction("Simulate first download prompt")
        action_simulate.triggered.connect(self._debug_simulate_first_time)
        
        # Simulate first-time download progress
        action_simulate_progress = menu.addAction("模擬首次下載進度")
        action_simulate_progress.triggered.connect(self._debug_simulate_first_time_progress)
        
        menu.addSeparator()
        
        # Test progress dialog
        action_progress = menu.addAction("測試進度對話框")
        action_progress.triggered.connect(self._test_progress_dialog)
        
        # Test download dialog
        action_download = menu.addAction("測試下載對話框")
        action_download.triggered.connect(self._test_download_dialog)
        
        # Show menu at button position
        menu.exec(self.debug_btn.mapToGlobal(self.debug_btn.rect().bottomLeft()))
    
    def _debug_check_cache(self):
        """Check and display model cache status."""
        whisper_cached = self.config.is_model_cached("whisper")
        llm_cached = self.config.is_model_cached("llm")
        
        status = (
            f"Model Cache Status\n\n"
            f"Whisper ASR: {'Cached' if whisper_cached else 'Not Downloaded'}\n"
            f"Qwen LLM: {'Cached' if llm_cached else 'Not Downloaded'}\n\n"
            f"緩存目錄: {self.config.get('models_dir')}"
        )
        
        QMessageBox.information(self, "模型緩存狀態", status)
    
    def _debug_show_gpu_status(self):
        """Show GPU status information."""
        import torch
        
        if torch.backends.mps.is_available():
            # Apple Silicon with MPS
            import platform
            chip_info = platform.processor() or "Apple Silicon"
            status = (
                f"GPU 狀態\n\n"
                f"GPU: Apple Silicon ({chip_info})\n"
                f"加速: Metal Performance Shaders (MPS)\n"
                f"記憶體: 共享系統記憶體\n\n"
                f"PyTorch 版本: {torch.__version__}"
            )
        elif torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free_memory = torch.cuda.mem_get_info()[0] / (1024**3)
            used_memory = total_memory - free_memory
            
            status = (
                f"GPU 狀態\n\n"
                f"GPU: {gpu_name}\n"
                f"VRAM 總量: {total_memory:.1f} GB\n"
                f"VRAM 已用: {used_memory:.1f} GB\n"
                f"VRAM 可用: {free_memory:.1f} GB\n\n"
                f"PyTorch 版本: {torch.__version__}"
            )
        else:
            status = "❌ GPU 不可用\n\n系統將使用 CPU 模式運行。"
        
        QMessageBox.information(self, "GPU 狀態", status)
    
    def _debug_clear_cache(self):
        """Clear model cache (for testing first-time download)."""
        reply = QMessageBox.question(
            self, 
            "清除緩存", 
            "確定要清除模型緩存嗎？\n\n"
            "這將刪除已下載的 AI 模型，\n"
            "下次轉譯時需要重新下載。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import shutil
            from pathlib import Path
            
            # Clear HuggingFace cache for our models
            hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
            cleared = []
            
            if hf_cache.exists():
                for folder in hf_cache.iterdir():
                    folder_name = folder.name.lower()
                    if "whisper" in folder_name or "qwen" in folder_name:
                        try:
                            shutil.rmtree(folder)
                            cleared.append(folder.name)
                        except Exception as e:
                            self.logger.warning(f"Failed to clear {folder}: {e}")
            
            if cleared:
                QMessageBox.information(
                    self, "清除完成", 
                    f"已清除以下緩存:\n" + "\n".join(cleared)
                )
            else:
                QMessageBox.information(self, "清除完成", "沒有找到需要清除的緩存。")
    
    def _debug_simulate_first_time(self):
        """Simulate first-time download prompt."""
        msg = QMessageBox(self)
        msg.setWindowTitle("首次使用提示")
        msg.setIcon(QMessageBox.Information)
        msg.setText("First time setup - AI model download required")
        msg.setInformativeText(
            "First transcription requires ~3-5 GB AI models.\n"
            "Download time: about 5-15 minutes.\n\n"
            "After download, offline use is available!\n\n"
            "是否繼續？"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e293b;
                color: #f1f5f9;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        msg.exec()
    
    def _debug_simulate_first_time_progress(self):
        """Simulate first-time download progress dialog."""
        import time
        from PySide6.QtWidgets import QApplication
        from ui.animated_progress_dialog import AnimatedProgressDialog
        
        dialog = AnimatedProgressDialog(self)
        dialog.show()
        
        # Simulate first-time download progress stages
        stages = [
            (5, "首次下載 AI 模型中，請稍候（約 5-10 分鐘）..."),
            (10, "首次下載 AI 模型中，請稍候（約 5-10 分鐘）..."),
            (15, "首次下載 AI 模型中，請稍候（約 5-10 分鐘）..."),
            (20, "正在提取音頻..."),
            (25, "正在提取音頻..."),
            (35, "正在生成字幕..."),
            (50, "正在生成字幕..."),
            (70, "正在生成字幕..."),
            (75, "正在生成字幕..."),
            (80, "首次下載 LLM 模型中，請稍候（約 3-5 分鐘）..."),
            (82, "首次下載 LLM 模型中，請稍候（約 3-5 分鐘）..."),
            (85, "正在 AI 校正..."),
            (90, "正在 AI 校正..."),
            (95, "正在 AI 校正..."),
            (100, "正在完成處理..."),
        ]
        
        for pct, msg in stages:
            dialog.setValue(pct)
            dialog.setLabelText(msg)
            QApplication.processEvents()
            time.sleep(0.5)
        
        time.sleep(0.5)
        dialog.close()
        
        QMessageBox.information(self, "模擬完成", "首次下載進度模擬完成！")

    def eventFilter(self, obj, event):
        """Global event filter to handle shortcuts even when specialized widgets have focus"""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                if self.isFullScreen():
                    self._exit_fullscreen()
                    return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Clean up session-only cache when app closes"""
        try:
            if hasattr(self, 'cache_dir') and self.cache_dir.exists():
                shutil.rmtree(self.cache_dir, ignore_errors=True)
                self.logger.info(f"🗑️ Cleaned up session cache: {self.cache_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to clean cache: {e}")
        
        event.accept()
