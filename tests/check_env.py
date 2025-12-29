#!/usr/bin/env python3
"""
環境檢查腳本 - 驗證所有依賴是否正確安裝
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """檢查 Python 版本"""
    print("=" * 60)
    print("🐍 Python 環境檢查")
    print("=" * 60)
    print(f"Python 版本: {sys.version}")
    print(f"Python 路徑: {sys.executable}")
    
    # 檢查是否在虛擬環境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ 在虛擬環境中運行")
    else:
        print("❌ 警告：不在虛擬環境中！")
        print("   請運行: source venv/bin/activate")
        return False
    
    return True

def check_dependencies():
    """檢查關鍵依賴"""
    print("\n" + "=" * 60)
    print("📦 依賴檢查")
    print("=" * 60)
    
    dependencies = {
        'PySide6': '必需 - Qt GUI 框架',
        'mlx': '必需 - Apple Silicon 加速',
        'mlx_whisper': '必需 - 語音識別',
        'mlx_lm': '必需 - 語言模型',
        'opencc': '必需 - 中文轉換',
        'faster_whisper': '可選 - 備用語音識別',
        'mpv': '可選 - 視頻播放（AVPlayer 優先）',
    }
    
    all_ok = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module:20s} - {description}")
        except ImportError:
            if '可選' in description:
                print(f"⚠️  {module:20s} - {description}")
            else:
                print(f"❌ {module:20s} - {description}")
                all_ok = False
    
    return all_ok

def check_system_dependencies():
    """檢查系統依賴"""
    print("\n" + "=" * 60)
    print("🔧 系統依賴檢查")
    print("=" * 60)
    
    # 檢查 FFmpeg
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✅ FFmpeg: {ffmpeg_path}")
    else:
        print("❌ FFmpeg 未找到")
        print("   請運行: brew install ffmpeg")
    
    # 檢查 libmpv
    if sys.platform == 'darwin':
        libmpv_paths = [
            '/opt/homebrew/lib/libmpv.dylib',
            '/usr/local/lib/libmpv.dylib',
        ]
        found = False
        for path in libmpv_paths:
            if Path(path).exists():
                print(f"✅ libmpv: {path}")
                found = True
                break
        if not found:
            print("⚠️  libmpv 未找到（AVPlayer 可用時不需要）")
            print("   可選安裝: brew install mpv")

def check_avplayer():
    """檢查 AVPlayer 可用性"""
    print("\n" + "=" * 60)
    print("🍎 AVPlayer 檢查 (macOS)")
    print("=" * 60)
    
    if sys.platform != 'darwin':
        print("⚠️  非 macOS 系統，AVPlayer 不可用")
        return
    
    try:
        # 嘗試導入 AVPlayer 相關模塊
        from ui.avplayer_widget import is_avplayer_available
        if is_avplayer_available():
            print("✅ AVPlayer 可用（推薦使用）")
        else:
            print("❌ AVPlayer 不可用")
    except Exception as e:
        print(f"⚠️  無法檢查 AVPlayer: {e}")

def check_mlx_metal():
    """檢查 MLX Metal 支持"""
    print("\n" + "=" * 60)
    print("⚡ MLX Metal 檢查")
    print("=" * 60)
    
    try:
        import mlx.core as mx
        
        # 測試 Metal
        test_array = mx.array([1, 2, 3])
        result = test_array + 1
        
        print("✅ MLX Metal 可用")
        print(f"   測試結果: {result}")
    except Exception as e:
        print(f"❌ MLX Metal 測試失敗: {e}")

def main():
    """主函數"""
    print("\n🔍 Canto-Beats 環境診斷工具\n")
    
    # 檢查 Python 環境
    if not check_python_version():
        print("\n❌ 請先激活虛擬環境！")
        print("   運行: source venv/bin/activate")
        sys.exit(1)
    
    # 檢查依賴
    deps_ok = check_dependencies()
    
    # 檢查系統依賴
    check_system_dependencies()
    
    # 檢查 AVPlayer
    check_avplayer()
    
    # 檢查 MLX
    check_mlx_metal()
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 診斷總結")
    print("=" * 60)
    
    if deps_ok:
        print("✅ 所有必需依賴已安裝")
        print("✅ 環境配置正確")
        print("\n🚀 您可以運行應用程序了！")
        print("   運行: python main.py")
    else:
        print("❌ 部分依賴缺失")
        print("\n🔧 修復方法:")
        print("   1. 確保在虛擬環境中: source venv/bin/activate")
        print("   2. 安裝依賴: pip install -r requirements.txt")
    
    print("=" * 60)

if __name__ == "__main__":
    # 切換到項目根目錄
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 添加 src 到路徑
    sys.path.insert(0, str(script_dir / 'src'))
    
    main()
