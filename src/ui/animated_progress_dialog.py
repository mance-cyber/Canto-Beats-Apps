"""
Simple Progress Dialog for Canto-Beats
With three-dot cycling animation for visual feedback
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer


class AnimatedProgressDialog(QDialog):
    """Progress dialog with three-dot cycling animation"""
    
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
        
        # Animation state
        self._base_text = ""
        self._dot_count = 0
        self._dot_timer = None
        
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
    
    def _start_dot_animation(self):
        """Start the three-dot cycling animation"""
        if self._dot_timer is None:
            self._dot_timer = QTimer(self)
            self._dot_timer.timeout.connect(self._update_dots)
        if not self._dot_timer.isActive():
            self._dot_count = 0
            self._dot_timer.start(400)  # Update every 400ms
    
    def _stop_dot_animation(self):
        """Stop the dot animation"""
        if self._dot_timer and self._dot_timer.isActive():
            self._dot_timer.stop()
    
    def _update_dots(self):
        """Update the animated dots in the progress label"""
        if not self._base_text:
            return
        
        # Cycle through 1, 2, 3 dots
        self._dot_count = (self._dot_count % 3) + 1
        dots = "." * self._dot_count
        
        # Update label with animated dots
        self.progress_label.setText(f"{self._base_text}{dots}")
        
    def _on_cancel(self):
        """Handle cancel button click"""
        self._stop_dot_animation()
        self.canceled.emit()
        self.close()
        
    def setLabelText(self, text: str):
        """Update progress text with optional three-dot animation
        
        If text ends with "...", the dots will animate.
        If text ends with "!", animation stops (completion message).
        """
        from PySide6.QtWidgets import QApplication
        
        # Check if text should animate (ends with "...")
        if text.endswith("..."):
            # Store base text without dots
            self._base_text = text.rstrip(".")
            self._start_dot_animation()
            # Set initial text with one dot
            self.progress_label.setText(f"{self._base_text}.")
        else:
            # Static text - stop animation
            self._stop_dot_animation()
            self._base_text = ""
            self.progress_label.setText(text)
        
        # Force UI update
        QApplication.processEvents()
        
    def setValue(self, value: int):
        """Update progress value (0-100)"""
        self.progress_bar.setValue(value)
        # Force UI update
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def closeEvent(self, event):
        """Clean up timer when dialog closes"""
        self._stop_dot_animation()
        super().closeEvent(event)

