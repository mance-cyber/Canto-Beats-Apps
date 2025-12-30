"""
Style Control Panel UI.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton, 
    QCheckBox, QLabel, QButtonGroup, QScrollArea,
    QPushButton, QFrame, QToolButton, QHBoxLayout,
    QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon
import os

from core.path_setup import get_icon_path

class StyleControlPanel(QWidget):
    """
    Right-side panel for controlling subtitle styles.
    """
    
    style_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(4, 4, 4, 4)
        
        # 1. Language Style
        self.lang_card, lang_container_layout = self._create_card("字幕語言風格", "sparkles")
        lang_layout = QVBoxLayout()
        self.style_bg = QButtonGroup(self)
        
        
        self.rb_spoken = QRadioButton("口語")
        self.rb_semi = QRadioButton("半書面語")
        self.rb_written = QRadioButton("書面語")
        
        self.rb_spoken.setChecked(True)
        self.style_bg.addButton(self.rb_spoken, 1)
        self.style_bg.addButton(self.rb_semi, 2)
        self.style_bg.addButton(self.rb_written, 3)
        
        lang_layout.addWidget(self._create_radio_row(self.rb_spoken))
        lang_layout.addWidget(self._create_radio_row(self.rb_semi))
        lang_layout.addWidget(self._create_radio_row(self.rb_written))
        lang_container_layout.addLayout(lang_layout)
        content_layout.addWidget(self.lang_card)

        # 2. Ultimate Mode Section (放在語言風格下方)
        self.ultimate_card, ultimate_container_layout = self._create_card("終極模式", "zap")
        ultimate_layout = QVBoxLayout()
        ultimate_layout.setSpacing(8)

        # Status label
        self.ultimate_status_label = QLabel("標準模式")
        self.ultimate_status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        ultimate_layout.addWidget(self.ultimate_status_label)

        # Settings button
        self.ultimate_settings_btn = QPushButton("⚡ 設定終極模式")
        self.ultimate_settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5b21b6, stop:1 #7e22ce);
            }
        """)
        self.ultimate_settings_btn.clicked.connect(self._show_ultimate_settings)
        ultimate_layout.addWidget(self.ultimate_settings_btn)

        # Help text
        help_label = QLabel("極致準確度，處理時間約 2-3 倍")
        help_label.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic;")
        ultimate_layout.addWidget(help_label)

        ultimate_container_layout.addLayout(ultimate_layout)
        content_layout.addWidget(self.ultimate_card)

        # Update ultimate mode status
        self._update_ultimate_status()

        # 3. English Handling (原 #2)
        self.eng_card, eng_container_layout = self._create_card("英文處理", "globe")
        eng_layout = QVBoxLayout()
        
        # Toggle Buttons for English (Keep or Translate)
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(8)
        
        self.btn_eng_keep = self._create_toggle_btn("保留", True)
        self.btn_eng_trans = self._create_toggle_btn("翻譯", False)
        
        self.eng_bg = QButtonGroup(self)
        self.eng_bg.addButton(self.btn_eng_keep, 1)
        self.eng_bg.addButton(self.btn_eng_trans, 2)
        
        toggle_layout.addWidget(self.btn_eng_keep)
        toggle_layout.addWidget(self.btn_eng_trans)
        
        eng_layout.addLayout(toggle_layout)
        eng_container_layout.addLayout(eng_layout)
        content_layout.addWidget(self.eng_card)
        
        # 4. Number Format (原 #3)
        self.num_card, num_container_layout = self._create_card("數字格式", "hash")
        num_layout = QVBoxLayout()
        self.num_bg = QButtonGroup(self)
        
        self.rb_num_arabic = QRadioButton("同位置數字 (123)")
        self.rb_num_chinese = QRadioButton("中文小寫 (一二三)")
        
        self.rb_num_arabic.setChecked(True)
        self.num_bg.addButton(self.rb_num_arabic, 1)
        self.num_bg.addButton(self.rb_num_chinese, 2)
        
        num_layout.addWidget(self._create_radio_row(self.rb_num_arabic))
        num_layout.addWidget(self._create_radio_row(self.rb_num_chinese))
        num_container_layout.addLayout(num_layout)
        content_layout.addWidget(self.num_card)
        
        # 5. Punctuation Toggle (原 #4)
        self.punct_card, punct_container_layout = self._create_card("標點符號", "text")
        punct_layout = QHBoxLayout()
        punct_layout.setSpacing(8)
        
        self.btn_punct_keep = self._create_toggle_btn("保留", True)
        self.btn_punct_remove = self._create_toggle_btn("移除", False)
        
        self.punct_bg = QButtonGroup(self)
        self.punct_bg.addButton(self.btn_punct_keep, 1)
        self.punct_bg.addButton(self.btn_punct_remove, 2)
        
        punct_layout.addWidget(self.btn_punct_keep)
        punct_layout.addWidget(self.btn_punct_remove)
        punct_container_layout.addLayout(punct_layout)
        content_layout.addWidget(self.punct_card)

        # Initialize downloader (keeping for compatibility)
        from utils.model_downloader import ModelDownloader
        self.downloader = ModelDownloader()

        # Add stretch
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Connect signals
        self.style_bg.buttonClicked.connect(self._emit_change)
        self.eng_bg.buttonClicked.connect(self._emit_change)
        self.num_bg.buttonClicked.connect(self._emit_change)
        self.punct_bg.buttonClicked.connect(self._emit_change)
        

    def _create_card(self, title, icon_name):
        """Create a styled card with header"""
        card = QFrame()
        card.setObjectName("styleCard")
        card.setProperty("class", "styleCard") # For QSS targeting if objectName isn't enough
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # Header
        header_btn = QPushButton()
        header_btn.setObjectName("sectionHeader")
        header_btn.setProperty("class", "sectionHeader")
        
        # Header Layout
        header_layout = QHBoxLayout(header_btn)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon_label = QLabel()
        icon_path = get_icon_path(icon_name)
        if os.path.exists(icon_path):
            icon_label.setPixmap(QIcon(icon_path).pixmap(16, 16))
        else:
            icon_label.setText("")
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #e2e8f0; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Arrow
        arrow = QLabel("▼")
        arrow.setStyleSheet("color: #94a3b8; font-size: 10px; background: transparent;")
        header_layout.addWidget(arrow)
        
        card_layout.addWidget(header_btn)
        
        # Content Container (for padding)
        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(16, 0, 16, 16)
        card_layout.addWidget(content_container)
        
        return card, content_container_layout
        
    def _create_radio_row(self, radio):
        """Wrap radio in a layout for better spacing"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.addWidget(radio)
        return container

    def _create_toggle_btn(self, text, active=False):
        """Create a toggle button for segmented control"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setFixedHeight(32)
        if active:
            btn.setObjectName("activeToggleButton")
        else:
            btn.setObjectName("inactiveToggleButton")
        return btn

    def _emit_change(self, *args):
        """Collect options and emit signal"""
        # Update toggle button styles for English
        for btn in self.eng_bg.buttons():
            if btn.isChecked():
                btn.setObjectName("activeToggleButton")
            else:
                btn.setObjectName("inactiveToggleButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        # Update toggle button styles for Punctuation
        for btn in self.punct_bg.buttons():
            if btn.isChecked():
                btn.setObjectName("activeToggleButton")
            else:
                btn.setObjectName("inactiveToggleButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Get max_chars settings from config
        from core.config import Config
        config = Config()
        max_chars_enabled = config.get("max_chars_enabled", False)
        max_chars_limit = config.get("max_chars_limit", 14)

        options = {
            'ai_correction': self.downloader.is_model_installed(),
            'style': 'spoken' if self.rb_spoken.isChecked() else 
                     'semi' if self.rb_semi.isChecked() else 'written',
            'english': 'keep' if self.btn_eng_keep.isChecked() else
                       'translate' if self.btn_eng_trans.isChecked() else 'bilingual',
            'numbers': 'arabic' if self.rb_num_arabic.isChecked() else 'chinese',
            'punctuation': 'keep' if self.btn_punct_keep.isChecked() else 'remove',
            'profanity': 'keep', # Default for now
            'split_long': max_chars_enabled,  # Use config value
            'max_chars': max_chars_limit  # Pass the limit to processor
        }
        self.style_changed.emit(options)
        
    def get_current_options(self) -> dict:
        """Get current style options."""
        # AI correction always enabled (removed from UI)
        ai_enabled = self.downloader.is_model_installed()
        
        # Get max_chars settings from config
        from core.config import Config
        config = Config()
        max_chars_enabled = config.get("max_chars_enabled", False)
        max_chars_limit = config.get("max_chars_limit", 14)

        return {
            'ai_correction': ai_enabled,
            'style': 'spoken' if self.rb_spoken.isChecked() else 
                     'semi' if self.rb_semi.isChecked() else 'written',
            'english': 'keep' if self.btn_eng_keep.isChecked() else 'translate',
            'numbers': 'arabic' if self.rb_num_arabic.isChecked() else 'chinese',
            'punctuation': 'keep' if self.btn_punct_keep.isChecked() else 'remove',
            'profanity': 'keep', # Default for now
            'split_long': max_chars_enabled,  # Use config value
            'max_chars': max_chars_limit  # Pass the limit to processor
        }
    
    def _update_ai_status(self):
        """Update the AI model status display."""
        if self.downloader.is_model_installed():
            self.ai_status_label.setText("[OK] AI 模型已安裝")
            self.ai_status_label.setStyleSheet("color: #22c55e; font-size: 12px;")
            self.ai_download_btn.hide()
            self.ai_download_btn.setEnabled(False)
        else:
            self.ai_status_label.setText("[!] AI 模型未安裝 (~4.5GB)")
            self.ai_status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
            self.ai_download_btn.show()
            self.ai_download_btn.setEnabled(True)
    
    def _start_model_download(self):
        """Start downloading the AI model."""
        self.ai_download_btn.setEnabled(False)
        self.ai_download_btn.setText("下載中...")
        self.ai_progress_bar.show()
        self.ai_progress_bar.setText("正在連接...")
        
        self.downloader.download_model(
            progress_callback=self._on_download_progress,
            finished_callback=self._on_download_finished,
            error_callback=self._on_download_error
        )
    
    def _on_download_progress(self, percent: int, message: str):
        """Handle download progress updates."""
        self.ai_progress_bar.setText(f"{message} ({percent}%)")
    
    def _on_download_finished(self, path: str):
        """Handle download completion."""
        self.ai_progress_bar.setText("下載完成！")
        self.ai_download_btn.setText("已安裝")
        self._update_ai_status()
        # Emit change to notify main window that AI is now available
        self._emit_change()
    
    def _on_download_error(self, error: str):
        """Handle download error."""
        self.ai_progress_bar.setText(f"[X] 錯誤: {error}")
        self.ai_progress_bar.setStyleSheet("color: #ef4444; font-size: 11px;")
        self.ai_download_btn.setEnabled(True)
        self.ai_download_btn.setText("重試下載")

    def _update_ultimate_status(self):
        """Update ultimate mode status display."""
        from core.config import Config
        config = Config()
        enabled = config.get("enable_ultimate_transcription", False)

        if enabled:
            self.ultimate_status_label.setText("⚡ 終極模式已啟用")
            self.ultimate_status_label.setStyleSheet("color: #a855f7; font-size: 12px; font-weight: bold;")
        else:
            self.ultimate_status_label.setText("標準模式")
            self.ultimate_status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")

    def _show_ultimate_settings(self):
        """Show ultimate mode settings dialog."""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                       QCheckBox, QPushButton, QGroupBox, QFrame,
                                       QTableWidget, QTableWidgetItem, QHeaderView,
                                       QAbstractItemView, QMessageBox)
        from PySide6.QtCore import Qt
        from core.config import Config
        from core.hardware_detector import get_hardware_detector

        # Check VRAM first
        detector = get_hardware_detector()
        current_vram = detector.get_vram_gb()
        min_required_vram = 12.0  # Minimum for ultimate mode

        if current_vram < min_required_vram:
            # Show blocking warning dialog
            self._show_vram_warning(current_vram, min_required_vram)
            return  # Don't show settings dialog

        config = Config()

        dialog = QDialog(self)
        dialog.setWindowTitle("終極模式設定")
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumSize(500, 480)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 12px;
            }
            QLabel {
                color: #e2e8f0;
            }
            QCheckBox {
                color: #e2e8f0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #475569;
                background: #0f172a;
            }
            QCheckBox::indicator:checked {
                background: #a855f7;
                border-color: #a855f7;
            }
            QGroupBox {
                font-weight: bold;
                color: #94a3b8;
                border: 1px solid #475569;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("⚡ 終極模式設定")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #a855f7;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Close button
        close_x = QPushButton("✕")
        close_x.setFixedSize(28, 28)
        close_x.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        close_x.clicked.connect(dialog.reject)
        title_layout.addWidget(close_x)
        layout.addLayout(title_layout)

        # Description
        desc = QLabel("終極模式整合多項高級優化策略，顯著提升轉錄準確度。")
        desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # === Main Settings ===
        main_group = QGroupBox("轉錄設定")
        main_layout = QVBoxLayout(main_group)
        main_layout.setSpacing(12)

        # Ultimate mode toggle
        ultimate_check = QCheckBox("啟用終極轉錄模式")
        ultimate_check.setChecked(config.get("enable_ultimate_transcription", False))
        ultimate_check.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(ultimate_check)

        # Features list
        features_label = QLabel(
            "  • 音頻預處理（降噪 + 人聲增強）\n"
            "  • VAD 智能預分割\n"
            "  • 三階段高精度轉錄\n"
            "  • 錨點驗證系統\n"
            "  • 用戶詞彙個人化"
        )
        features_label.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 20px;")
        main_layout.addWidget(features_label)

        # LLM optimization
        llm_check = QCheckBox("啟用 AI 斷句優化")
        llm_check.setChecked(config.get("enable_llm_sentence_optimization", True))
        main_layout.addWidget(llm_check)

        layout.addWidget(main_group)

        # === Vocabulary Section ===
        vocab_group = QGroupBox("📚 用戶詞彙庫")
        vocab_layout = QVBoxLayout(vocab_group)
        vocab_layout.setSpacing(10)

        # Stats
        try:
            from utils.vocabulary_learner import get_vocabulary_learner
            vocab_learner = get_vocabulary_learner()
            stats = vocab_learner.get_statistics()
            stats_text = f"已學習 {stats['total_words']} 個詞彙，累計校正 {stats['total_corrections']} 次"
        except Exception:
            stats_text = "詞彙庫尚未初始化"
            vocab_learner = None

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        vocab_layout.addWidget(stats_label)

        # Buttons
        vocab_btn_layout = QHBoxLayout()

        view_btn = QPushButton("查看詞彙")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        view_btn.clicked.connect(lambda: self._show_vocabulary_list(dialog, vocab_learner))
        vocab_btn_layout.addWidget(view_btn)

        clear_btn = QPushButton("清空詞彙")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f1d1d;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #991b1b;
            }
        """)
        clear_btn.clicked.connect(lambda: self._clear_vocabulary_with_confirm(stats_label, vocab_learner))
        vocab_btn_layout.addWidget(clear_btn)

        vocab_btn_layout.addStretch()
        vocab_layout.addLayout(vocab_btn_layout)

        # Help
        vocab_help = QLabel("💡 當你手動修改字幕並導出時，系統會自動學習你的修正")
        vocab_help.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic;")
        vocab_help.setWordWrap(True)
        vocab_layout.addWidget(vocab_help)

        layout.addWidget(vocab_group)

        layout.addStretch()

        # === Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #64748b;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("儲存設定")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #a855f7);
                color: white;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #9333ea);
            }
        """)
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        if dialog.exec():
            # Save settings
            config.set("enable_ultimate_transcription", ultimate_check.isChecked())
            config.set("enable_llm_sentence_optimization", llm_check.isChecked())
            self._update_ultimate_status()

    def _show_vram_warning(self, current_vram: float, required_vram: float):
        """Show VRAM insufficient warning dialog."""
        from PySide6.QtWidgets import QMessageBox
        
        msg = QMessageBox(self)
        msg.setWindowTitle("VRAM 不足")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("⚠️ 無法啟用終極模式")
        msg.setInformativeText(
            f"終極模式需要至少 {required_vram:.0f} GB VRAM。\n\n"
            f"檢測到您的系統只有 {current_vram:.1f} GB VRAM，"
            f"不足以執行終極模式的高級功能。\n\n"
            f"建議：\n"
            f"• 使用標準模式進行轉錄\n"
            f"• 或升級至配備更大 VRAM 的 GPU"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e293b;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
            }
            QPushButton {
                background-color: #475569;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #64748b;
            }
        """)
        msg.exec()

    def _show_vocabulary_list(self, parent_dialog, vocab_learner):
        """Show vocabulary list in a sub-dialog."""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                       QPushButton, QTableWidget, QTableWidgetItem,
                                       QHeaderView, QAbstractItemView)
        from PySide6.QtCore import Qt

        if not vocab_learner:
            return

        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("用戶詞彙庫")
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setMinimumSize(550, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border: 1px solid #475569;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("📚 用戶詞彙庫")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #22d3ee;")
        layout.addWidget(title)

        # Table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["錯誤文字", "正確文字", "使用次數", "類別"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #e2e8f0;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #7c3aed;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #e2e8f0;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        vocabulary = vocab_learner.vocabulary
        table.setRowCount(len(vocabulary))
        for row, (word, entry) in enumerate(vocabulary.items()):
            wrong_variants = ", ".join(entry.wrong_variants) if entry.wrong_variants else ""
            table.setItem(row, 0, QTableWidgetItem(wrong_variants))
            table.setItem(row, 1, QTableWidgetItem(entry.correct_word))
            table.setItem(row, 2, QTableWidgetItem(str(entry.frequency)))
            table.setItem(row, 3, QTableWidgetItem(entry.category))

        layout.addWidget(table)

        # Close button
        close_btn = QPushButton("關閉")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        close_btn.clicked.connect(dialog.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def _clear_vocabulary_with_confirm(self, stats_label, vocab_learner):
        """Clear vocabulary with confirmation."""
        from PySide6.QtWidgets import QMessageBox

        if not vocab_learner:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("確認清空")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("確定要清空所有已學習的詞彙嗎？")
        msg.setInformativeText("此操作無法撤銷。")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e293b;
                color: #f1f5f9;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
            }
            QPushButton {
                background-color: #475569;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #64748b;
            }
        """)

        if msg.exec() == QMessageBox.Yes:
            vocab_learner.clear_all()
            stats_label.setText("已學習 0 個詞彙，累計校正 0 次")
