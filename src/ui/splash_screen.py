"""
Splash Screen for Canto-beats startup.
Shows loading progress while the application initializes.
"""

from PySide6.QtWidgets import QSplashScreen, QApplication, QProgressBar, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QLinearGradient
from pathlib import Path
import sys


class SplashScreen(QSplashScreen):
    """
    Custom splash screen showing loading progress during startup.
    """
    
    def __init__(self):
        # Create a pixmap for the splash
        pixmap = self._create_splash_pixmap()
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        
        self._progress = 0
        self._message = "正在啟動..."
        
    def _create_splash_pixmap(self) -> QPixmap:
        """Create the splash screen background."""
        width, height = 500, 300
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#1a1a2e"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background
        gradient = QLinearGradient(0, 0, width, height)
        gradient.setColorAt(0, QColor("#1a1a2e"))
        gradient.setColorAt(1, QColor("#16213e"))
        painter.fillRect(0, 0, width, height, gradient)
        
        # Draw title
        painter.setPen(QColor("#00d4ff"))
        title_font = QFont("Segoe UI", 32, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(0, 60, width, 60, Qt.AlignCenter, "Canto-beats")
        
        # Draw subtitle
        painter.setPen(QColor("#888888"))
        subtitle_font = QFont("Segoe UI", 12)
        painter.setFont(subtitle_font)
        painter.drawText(0, 110, width, 30, Qt.AlignCenter, "粵語字幕神器")
        
        # Draw version
        painter.setPen(QColor("#666666"))
        version_font = QFont("Segoe UI", 10)
        painter.setFont(version_font)
        painter.drawText(0, height - 30, width, 20, Qt.AlignCenter, "版本 1.0.0")
        
        painter.end()
        return pixmap
    
    def set_progress(self, value: int, message: str = None):
        """Update the progress and message."""
        self._progress = value
        if message:
            self._message = message
        self.repaint()
        self.showMessage(
            f"{self._message} ({self._progress}%)",
            Qt.AlignBottom | Qt.AlignHCenter,
            QColor("#00d4ff")
        )
        QApplication.processEvents()
    
    def drawContents(self, painter: QPainter):
        """Draw the progress bar and message."""
        super().drawContents(painter)
        
        width = self.pixmap().width()
        height = self.pixmap().height()
        
        # Draw progress bar background
        bar_x = 50
        bar_y = height - 80
        bar_width = width - 100
        bar_height = 8
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#333355"))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 4, 4)
        
        # Draw progress bar fill
        if self._progress > 0:
            fill_width = int(bar_width * self._progress / 100)
            gradient = QLinearGradient(bar_x, bar_y, bar_x + fill_width, bar_y)
            gradient.setColorAt(0, QColor("#00d4ff"))
            gradient.setColorAt(1, QColor("#0099cc"))
            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_x, bar_y, fill_width, bar_height, 4, 4)


def show_splash() -> SplashScreen:
    """Create and show the splash screen."""
    splash = SplashScreen()
    splash.show()
    splash.set_progress(0, "正在啟動...")
    return splash


def update_splash(splash: SplashScreen, progress: int, message: str):
    """Update splash screen progress."""
    if splash:
        splash.set_progress(progress, message)


def close_splash(splash: SplashScreen):
    """Close the splash screen."""
    if splash:
        splash.close()
