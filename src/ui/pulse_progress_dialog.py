"""
Modern Pulse Progress Dialog for Canto-Beats
Features a sleek pulse animation instead of rainbow spinner
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QProgressBar, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen, QBrush


class PulseCircle(QWidget):
    """Animated pulsing circle widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self._pulse_value = 0.0
        self._animation = None
        
        # Setup pulse animation
        self._setup_animation()
    
    def _get_pulse(self):
        return self._pulse_value
    
    def _set_pulse(self, value):
        self._pulse_value = value
        self.update()
    
    pulse = Property(float, _get_pulse, _set_pulse)
    
    def _setup_animation(self):
        """Setup the pulse animation"""
        self._animation = QPropertyAnimation(self, b"pulse")
        self._animation.setDuration(1200)  # 1.2 seconds per cycle
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setLoopCount(-1)  # Infinite loop
        self._animation.setEasingCurve(QEasingCurve.InOutSine)
    
    def start(self):
        """Start the animation"""
        if self._animation:
            self._animation.start()
    
    def stop(self):
        """Stop the animation"""
        if self._animation:
            self._animation.stop()
    
    def paintEvent(self, event):
        """Draw the pulsing circles"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw multiple concentric circles with varying opacity
        base_color = QColor(6, 182, 212)  # Cyan/teal
        
        # Outer pulse ring
        outer_radius = 20 + (self._pulse_value * 8)
        outer_opacity = int(255 * (1.0 - self._pulse_value) * 0.5)
        outer_color = QColor(base_color)
        outer_color.setAlpha(outer_opacity)
        painter.setPen(QPen(outer_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - outer_radius, center_y - outer_radius, 
                           outer_radius * 2, outer_radius * 2)
        
        # Middle ring
        mid_radius = 15 + (self._pulse_value * 4)
        mid_opacity = int(255 * (0.8 - self._pulse_value * 0.3))
        mid_color = QColor(base_color)
        mid_color.setAlpha(mid_opacity)
        painter.setPen(QPen(mid_color, 2))
        painter.drawEllipse(center_x - mid_radius, center_y - mid_radius,
                           mid_radius * 2, mid_radius * 2)
        
        # Inner solid circle
        inner_radius = 8
        inner_color = QColor(34, 211, 238)  # Lighter cyan
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(inner_color))
        painter.drawEllipse(center_x - inner_radius, center_y - inner_radius,
                           inner_radius * 2, inner_radius * 2)


class PulseProgressDialog(QDialog):
    """Modern progress dialog with pulse animation"""
    
    canceled = Signal()
    
    def __init__(self, parent=None, title="處理中"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setFixedSize(380, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                border-radius: 16px;
                border: 1px solid #334155;
            }
        """)
        
        self._title_text = title
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
        layout.setContentsMargins(30, 30, 30, 25)
        layout.setSpacing(16)
        
        # Pulse animation widget
        pulse_container = QHBoxLayout()
        pulse_container.addStretch()
        self.pulse_widget = PulseCircle()
        pulse_container.addWidget(self.pulse_widget)
        pulse_container.addStretch()
        layout.addLayout(pulse_container)
        
        # Title
        self.title_label = QLabel(self._title_text)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #f1f5f9;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #1e293b;
                text-align: center;
                color: #e2e8f0;
                height: 12px;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:0.5 #22d3ee, stop:1 #06b6d4);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #475569;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f1f5f9;
                border-color: #64748b;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def showEvent(self, event):
        """Start animation when dialog is shown"""
        super().showEvent(event)
        self.pulse_widget.start()
    
    def hideEvent(self, event):
        """Stop animation when dialog is hidden"""
        self.pulse_widget.stop()
        super().hideEvent(event)
    
    def _on_cancel(self):
        """Handle cancel button click"""
        self.pulse_widget.stop()
        self.canceled.emit()
        self.close()
    
    def set_title(self, title: str):
        """Set dialog title"""
        self.title_label.setText(title)
    
    def set_status(self, status: str):
        """Set status text"""
        self.status_label.setText(status)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def set_progress(self, value: int):
        """Set progress value (0-100)"""
        self.progress_bar.setValue(value)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
    
    def setLabelText(self, text: str):
        """Alias for set_status (compatibility)"""
        self.set_status(text)
    
    def setValue(self, value: int):
        """Alias for set_progress (compatibility)"""
        self.set_progress(value)
    
    def closeEvent(self, event):
        """Clean up when dialog closes"""
        self.pulse_widget.stop()
        super().closeEvent(event)
