"""
Custom title bar for frameless windows.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent


class CustomTitleBar(QWidget):
    """Custom title bar with minimize, maximize, and close buttons."""
    
    def __init__(self, parent=None, title="Canto-beats"):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_position = QPoint()
        self.setFixedHeight(40)
        self._setup_ui(title)
    
    def _setup_ui(self, title):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Spacer
        layout.addStretch()
        
        # Minimize button
        self.min_btn = self._create_button("−")
        self.min_btn.clicked.connect(self._minimize)
        layout.addWidget(self.min_btn)
        
        # Maximize/Restore button
        self.max_btn = self._create_button("□")
        self.max_btn.clicked.connect(self._maximize_restore)
        layout.addWidget(self.max_btn)
        
        # Close button
        self.close_btn = self._create_button("✕")
        self.close_btn.clicked.connect(self._close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                padding: 0;
                font-size: 16px;
                width: 46px;
                height: 40px;
            }
            QPushButton:hover {
                background-color: #E81123;
            }
        """)
        layout.addWidget(self.close_btn)
        
        # Title bar style
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #1A1A2E;
            }
        """)
    
    def _create_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                padding: 0;
                font-size: 16px;
                width: 46px;
                height: 40px;
            }
            QPushButton:hover {
                background-color: #374151;
            }
        """)
        return btn
    
    def _minimize(self):
        if self.parent_window:
            self.parent_window.showMinimized()
    
    def _maximize_restore(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
                self.max_btn.setText("□")
            else:
                self.parent_window.showMaximized()
                self.max_btn.setText("❐")
    
    def _close(self):
        if self.parent_window:
            self.parent_window.close()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start dragging window."""
        if event.button() == Qt.LeftButton and self.parent_window:
            self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Drag window."""
        if event.buttons() == Qt.LeftButton and self.parent_window:
            self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click to maximize/restore."""
        if event.button() == Qt.LeftButton:
            self._maximize_restore()
