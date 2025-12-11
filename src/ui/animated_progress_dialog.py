"""
Simple Progress Dialog for Canto-Beats
Minimal design with no animation - maximum performance
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QProgressBar
)
from PySide6.QtCore import Qt, Signal


class AnimatedProgressDialog(QDialog):
    """Simple progress dialog without animation"""
    
    canceled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(420, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border-radius: 12px;
                border: 2px solid #334155;
            }
        """)
        
        self._init_ui()
        
        # Center on parent window
        if parent:
            parent_geo = parent.geometry()
            dialog_geo = self.geometry()
            x = parent_geo.x() + (parent_geo.width() - dialog_geo.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - dialog_geo.height()) // 2
            self.move(x, y)
        
    def _init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("AI 字幕生成中")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #f1f5f9;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        # Progress label
        self.progress_label = QLabel("正在初始化...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #334155;
                border-radius: 8px;
                background-color: #1e293b;
                text-align: center;
                color: #e2e8f0;
                height: 28px;
                font-size: 13px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #3b82f6);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def _on_cancel(self):
        """Handle cancel button click"""
        self.canceled.emit()
        self.close()
        
    def setLabelText(self, text: str):
        """Update progress text"""
        self.progress_label.setText(text)
        
    def setValue(self, value: int):
        """Update progress value (0-100)"""
        self.progress_bar.setValue(value)
