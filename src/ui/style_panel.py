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
        
        # 2. English Handling
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
        
        # 3. Number Format
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
        
        # 4. Punctuation Toggle
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
        
        # 5. Profanity Filter (Optional, keeping simple for now)
        # ...
        
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
