"""
Canto-beats - 粤语通专业版
全球唯一一站式粤语影片处理 + 专业播放神器

Entry point for the application.
IMPORTANT: This file is designed to show splash screen IMMEDIATELY
before loading heavy libraries like PyTorch, PySide6, etc.
"""

import sys
import os
from pathlib import Path

# ============================================
# TORCHCODEC METADATA PATCH - FIX TRANSFORMERS IMPORT
# transformers.audio_utils tries to get torchcodec version which fails in PyInstaller
# NOTE: Do NOT patch subprocess.Popen globally - it breaks asyncio on Windows!
# ============================================
import importlib.metadata
_original_version = importlib.metadata.version

def _patched_version(package):
    """Patch to provide fake version for torchcodec to prevent import failures."""
    if package == 'torchcodec':
        return '0.0.0'  # Fake version to prevent PackageNotFoundError
    return _original_version(package)

importlib.metadata.version = _patched_version

# Add src directory to Python path FIRST
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Setup all external dependency paths (FFmpeg, libmpv, etc.) BEFORE any other imports
# This is critical for packaged applications where dependencies are bundled
from core.path_setup import setup_all_paths
_path_setup_result = setup_all_paths()



def show_splash_early():
    """
    Show splash screen as early as possible, before heavy imports.
    Uses minimal imports to ensure fast startup.
    """
    # Only import what's absolutely necessary for splash
    from PySide6.QtWidgets import QApplication, QSplashScreen
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QLinearGradient
    
    # Create app if not exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("Canto-beats")
    
    # Create splash pixmap - larger size for better layout
    width, height = 500, 350
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#1a1a2e"))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw gradient background
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0, QColor("#1a1a2e"))
    gradient.setColorAt(1, QColor("#16213e"))
    painter.fillRect(0, 0, width, height, gradient)
    
    # Draw title - centered vertically in upper area
    painter.setPen(QColor("#00d4ff"))
    title_font = QFont("Segoe UI", 36, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(0, 80, width, 50, Qt.AlignCenter, "Canto-beats")
    
    # Draw subtitle - below title with good spacing
    painter.setPen(QColor("#888888"))
    subtitle_font = QFont("Segoe UI", 14)
    painter.setFont(subtitle_font)
    painter.drawText(0, 140, width, 30, Qt.AlignCenter, "廣東話字幕神器")
    
    # Draw version - middle area
    painter.setPen(QColor("#555555"))
    version_font = QFont("Segoe UI", 10)
    painter.setFont(version_font)
    painter.drawText(0, 185, width, 20, Qt.AlignCenter, "版本 1.0.0")
    
    # Leave bottom 80px clear for the progress message (showMessage will draw there)
    # Draw a subtle separator line
    painter.setPen(QColor("#333355"))
    painter.drawLine(50, height - 75, width - 50, height - 75)
    
    painter.end()
    
    # Create and show splash
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
    splash.show()
    
    # Force display update
    app.processEvents()
    
    return app, splash


def update_splash(splash, app, message):
    """Update splash screen message."""
    if splash:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        splash.showMessage(
            message,
            int(Qt.AlignBottom | Qt.AlignHCenter),
            QColor("#00d4ff")
        )
        app.processEvents()


def main():
    """Application entry point"""
    
    # STEP 1: Show splash IMMEDIATELY (before any heavy imports)
    print("Starting Canto-beats...")
    app, splash = show_splash_early()
    
    # Import Qt after splash is shown
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QIcon
    
    # STEP 2: Now do heavy imports with splash visible
    update_splash(splash, app, "載入日誌系統...")
    from utils.logger import setup_logger
    logger = setup_logger()
    
    # Global exception handler
    import traceback
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        print("\n" + "=" * 60)
        print("FATAL ERROR - Uncaught Exception!")
        print("=" * 60)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        try:
            with open("crash_log.txt", "a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"\nCrash at: {datetime.now()}\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = global_exception_handler
    
    # Run security checks
    update_splash(splash, app, "執行安全檢查...")
    try:
        from core.integrity_checker import check_integrity
        check_integrity(src_path)
    except:
        pass
    
    # Set application icon
    update_splash(splash, app, "載入圖示...")
    icon_path = Path(__file__).parent / "public" / "app icon_002.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Check GPU availability (heavy import: torch)
    update_splash(splash, app, "檢查 GPU 狀態...")
    import torch
    cuda_available = torch.cuda.is_available()
    
    print("\n" + "="*60)
    print("Canto-beats - GPU Status Check")
    print("="*60)
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"GPU Device: {gpu_name}")
        print(f"VRAM Total: {vram_gb:.1f} GB")
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        free_memory = torch.cuda.mem_get_info()[0] / (1024**3)
        print(f"VRAM Available: {free_memory:.1f} GB")
        print("[OK] GPU acceleration enabled!")
    else:
        print("[!] Using CPU mode")
    
    print("="*60 + "\n")
    
    logger.info("Starting Canto-beats...")
    
    # Load configuration
    update_splash(splash, app, "載入設定...")
    from core.config import Config
    config = Config()
    
    # Load custom fonts
    update_splash(splash, app, "載入字體...")
    from PySide6.QtGui import QFontDatabase, QFont
    
    font_path = src_path / "resources" / "fonts" / "NotoSansCJKtc-Black.otf"
    custom_font_loaded = False
    
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QFont(families[0], 10))
                custom_font_loaded = True
    
    if not custom_font_loaded:
        for font_family in ["Microsoft JhengHei", "PingFang TC", "Segoe UI"]:
            if QFontDatabase.hasFamily(font_family):
                app.setFont(QFont(font_family, 10))
                break
    
    # Load stylesheet
    update_splash(splash, app, "載入介面樣式...")
    style_path = src_path / "ui" / "styles.qss"
    if style_path.exists():
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    
    # Check license
    update_splash(splash, app, "檢查授權...")
    from core.license_manager import LicenseManager
    license_mgr = LicenseManager(config)
    if license_mgr.is_licensed():
        logger.info("Valid license found")
    else:
        logger.info("Running in Trial/Free mode")
    
    # Initialize main window (heaviest import)
    update_splash(splash, app, "初始化主視窗...")
    from ui.main_window import MainWindow
    window = MainWindow(config)
    
    update_splash(splash, app, "完成！")
    
    # Close splash and show main window
    splash.close()
    window.show()
    
    logger.info("Application window displayed")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
