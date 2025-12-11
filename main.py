"""
Canto-beats - 粤语通专业版
全球唯一一站式粤语影片处理 + 专业播放神器

Entry point for the application.
"""

import sys
import os
import traceback
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Global exception handler to catch crashes
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Handle any uncaught exceptions and log them before crash"""
    print("\n" + "=" * 60)
    print("FATAL ERROR - Uncaught Exception!")
    print("=" * 60)
    print(f"Type: {exc_type.__name__}")
    print(f"Value: {exc_value}")
    print("\nFull Traceback:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("=" * 60 + "\n")
    
    # Write to crash log file
    try:
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"\n{'='*60}\n")
            f.write(f"Crash at: {datetime.now()}\n")
            f.write(f"Type: {exc_type.__name__}\n")
            f.write(f"Value: {exc_value}\n")
            f.write("Traceback:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    except:
        pass
    
    # Call original handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
from core.config import Config
from utils.logger import setup_logger


def run_security_checks():
    """Run security checks before application starts."""
    try:
        from core.integrity_checker import check_integrity
        src_dir = Path(__file__).parent / "src"
        if not check_integrity(src_dir):
            print("[SECURITY] Integrity check failed!")
            # Continue anyway but log the issue
    except Exception as e:
        # Don't block app startup on security check failures
        pass


def main():
    """Application entry point"""
    
    # Setup logging
    logger = setup_logger()
    
    # Run security checks
    run_security_checks()
    
    # Check GPU availability and environment
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
        
        # Clear any leftover GPU memory from previous runs
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Show available VRAM after cleanup
        free_memory = torch.cuda.mem_get_info()[0] / (1024**3)
        print(f"VRAM Available: {free_memory:.1f} GB")
        print("[OK] GPU acceleration enabled!")
    else:
        print("[!] WARNING: GPU not detected - using CPU mode")
        print("\nFor GPU acceleration, please use:")
        print("  1. conda activate canto-env")
        print("  2. python main.py")
        print("\nOr create a shortcut with 'canto-env' activated.")
        print("\nContinuing with CPU (will be 3-5x slower)...")
    
    print("="*60 + "\n")
    
    logger.info("Starting Canto-beats...")
    
    # Load configuration
    config = Config()
    
    # High DPI is automatically enabled in PySide6 6.x+
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Canto-beats")
    app.setOrganizationName("Canto-beats")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon
    icon_path = Path(__file__).parent / "public" / "app icon_002.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        logger.info(f"App icon loaded: {icon_path}")
    else:
        logger.warning(f"App icon not found: {icon_path}")
    
    # Load custom fonts with tech-style fallbacks
    from PySide6.QtGui import QFontDatabase, QFont
    
    # Try to load custom font first (Source Han Sans / Noto Sans CJK) - Black version for maximum boldness
    font_path = src_path / "resources" / "fonts" / "NotoSansCJKtc-Black.otf"
    custom_font_loaded = False
    
    logger.info(f"Checking for custom font: {font_path}")
    logger.info(f"Font file exists: {font_path.exists()}")
    
    if font_path.exists():
        logger.info(f"Attempting to load font from: {font_path}")
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        logger.info(f"Font ID returned: {font_id}")
        
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            logger.info(f"Font families loaded: {families}")
            
            if families:
                family = families[0]
                logger.info(f"[OK] Loaded custom font: {family}")
                
                # Set as application default font
                default_font = QFont(family, 10)
                app.setFont(default_font)
                logger.info(f"Set application font to: {family}")
                custom_font_loaded = True
            else:
                logger.warning("Font loaded but no families found")
        else:
            logger.warning(f"Failed to load font (ID=-1): {font_path}")
            logger.warning("Possible reasons: corrupted file, unsupported format, or Qt limitation")
    else:
        logger.info(f"Custom font file not found: {font_path}")
    
    # If custom font not available, use system modern fonts
    if not custom_font_loaded:
        logger.info("Using system font fallback...")
        # Try modern tech-style fonts in order of preference
        font_families = [
            "Microsoft JhengHei",      # 微軟正黑體 (Windows)
            "PingFang TC",              # 蘋方 (macOS)
            "Noto Sans CJK TC",         # 思源黑體
            "Source Han Sans TC",       # 思源黑體 (Adobe name)
            "Microsoft YaHei",          # 微軟雅黑
            "Segoe UI",                 # Windows modern UI
            "Arial"                     # Universal fallback
        ]
        
        for font_family in font_families:
            font = QFont(font_family, 10)
            if QFontDatabase.hasFamily(font_family):
                app.setFont(font)
                logger.info(f"✅ Using system font: {font_family}")
                break
        else:
            logger.warning("No preferred fonts found, using system default")
    
    
    # Load modern UI stylesheet
    style_path = src_path / "ui" / "styles.qss"
    if style_path.exists():
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet loaded successfully")
    
    # Check license status (Non-blocking)
    from core.license_manager import LicenseManager
    license_mgr = LicenseManager(config)
    
    if license_mgr.is_licensed():
        logger.info("Valid license found")
    else:
        logger.info("No valid license found - Running in Trial/Free mode")

    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    logger.info("Application window displayed")
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
