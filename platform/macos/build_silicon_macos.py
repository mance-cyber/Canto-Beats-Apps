#!/usr/bin/env python3
"""
Silicon macOS (Apple M1/M2/M3) 专用打包脚本
针对 ARM64 架构优化，处理所有平台特定依赖

Usage:
    python build_silicon_macos.py
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def check_architecture():
    """检查是否在 ARM64 架构下运行"""
    arch = platform.machine()
    if arch != 'arm64':
        print(f"⚠️  警告: 当前架构是 {arch}，不是 arm64")
        print("建议在原生 ARM64 环境下构建，避免 Rosetta 2 兼容性问题")
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print(f"✅ 架构检查通过: {arch}")


def check_dependencies():
    """检查必要的系统依赖"""
    print("\n检查系统依赖...")
    
    # 检查 Homebrew
    try:
        result = subprocess.run(['brew', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Homebrew: {result.stdout.split()[1]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Homebrew 未安装")
        print("安装命令: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        sys.exit(1)
    
    # 检查 mpv (可選 - macOS 使用 AVPlayer)
    # try:
    #     subprocess.run(['brew', 'list', 'mpv'],
    #                   capture_output=True, check=True)
    #     print("✅ mpv 已安装")
    # except subprocess.CalledProcessError:
    #     print("⚠️  mpv 未安装（macOS 使用 AVPlayer，不影響打包）")
    
    # 检查 ffmpeg
    try:
        subprocess.run(['brew', 'list', 'ffmpeg'], 
                      capture_output=True, check=True)
        print("✅ ffmpeg 已安装")
    except subprocess.CalledProcessError:
        print("⚠️  ffmpeg 未安装，正在安装...")
        subprocess.run(['brew', 'install', 'ffmpeg'], check=True)


def find_libmpv():
    """查找 libmpv 动态库路径"""
    try:
        result = subprocess.run(['brew', '--prefix', 'mpv'],
                              capture_output=True, text=True, check=True)
        mpv_prefix = result.stdout.strip()
        libmpv_path = Path(mpv_prefix) / 'lib' / 'libmpv.dylib'
        
        if libmpv_path.exists():
            print(f"✅ 找到 libmpv: {libmpv_path}")
            return str(libmpv_path)
        else:
            print(f"⚠️  libmpv 不在预期位置: {libmpv_path}")
            return None
    except subprocess.CalledProcessError:
        print("⚠️  无法定位 libmpv")
        return None


def build_app():
    """构建 .app 包"""
    print("\n" + "=" * 60)
    print("开始构建 Canto-beats.app (Silicon macOS)")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.parent.parent  # Go up to project root
    main_script = str(project_dir / "main.py")
    
    # 获取 venv 的 site-packages 路径
    venv_site_packages = Path(sys.executable).parent.parent / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    
    # 動態查找 MLX metallib 文件
    mlx_metallib_arg = None
    try:
        import mlx
        if mlx.__file__:
            mlx_dir = Path(os.path.dirname(mlx.__file__))
            mlx_metallib = mlx_dir / "lib" / "mlx.metallib"
            
            if mlx_metallib.exists():
                mlx_metallib_arg = f"--add-data={mlx_metallib}:mlx/lib"
                print(f"✅ 找到 MLX metallib: {mlx_metallib}")
            else:
                print(f"⚠️ MLX metallib 不存在: {mlx_metallib}")
                print(f"   MLX 目錄: {mlx_dir}")
        else:
            print("⚠️ MLX 模組沒有 __file__ 屬性，跳過 metallib 打包")
    except ImportError:
        print("⚠️ MLX 未安裝，跳過 metallib 打包")
    except Exception as e:
        print(f"⚠️ MLX 檢測失敗: {e}，跳過 metallib 打包")
    
    # 基础 PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        main_script,

        # === 输出配置 ===
        "--onedir",
        "--windowed",  # 創建 .app bundle（方案一需要後續添加終端啟動器）
        "--name=Canto-beats",
        "--icon=public/icons/app_icon.icns",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        
        # === 数据文件 (macOS 使用 :) ===
        "--add-data=src:src",
        "--add-data=public:public",
        
        # === 隐藏导入 ===
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=torch",
        "--hidden-import=torchaudio",
        "--hidden-import=faster_whisper",
        "--hidden-import=transformers",
        "--hidden-import=cryptography",
        "--hidden-import=sentencepiece",
        "--hidden-import=accelerate",
        "--hidden-import=silero_vad",
        # === MLX (Apple Silicon GPU acceleration) ===
        "--hidden-import=mlx",
        "--hidden-import=mlx.core",
        "--hidden-import=mlx.nn",
        "--hidden-import=mlx.utils",
        "--hidden-import=mlx._reprlib_fix",
        "--hidden-import=mlx_whisper",
        "--hidden-import=mlx_whisper.transcribe",
        "--hidden-import=mlx_whisper.audio",
        "--hidden-import=mlx_whisper.decoding",
        "--hidden-import=mlx_whisper.load_models",
        # MLX LM (Apple Silicon accelerated Qwen) for 書面語 conversion
        "--hidden-import=mlx_lm",
        "--hidden-import=mlx_lm.generate",
        "--hidden-import=mlx_lm.utils",
        # Collect all MLX data files
        "--collect-all=mlx",
        "--collect-all=mlx_whisper",
        "--collect-all=mlx_lm",
        # === 完整收集這些套件（避免 runtime 缺失模組）===
        "--collect-all=opencc",          # 繁簡轉換
        "--collect-all=transformers",    # Qwen 模型依賴
        "--collect-all=tokenizers",      # tokenizers 庫
        "--collect-all=huggingface_hub", # 模型下載
        "--collect-all=safetensors",     # 模型權重格式
        "--collect-all=tqdm",            # 進度條
        "--collect-all=regex",           # transformers 依賴
        "--collect-all=filelock",        # huggingface 依賴
        # === PySide6 完整模組 ===
        # 不使用 --collect-all=PySide6 (會導致符號連結衝突)
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtMultimedia",
        "--hidden-import=PySide6.QtMultimediaWidgets",
        "--hidden-import=PySide6.QtNetwork",
        "--hidden-import=PySide6.QtSvg",
        "--hidden-import=PySide6.QtSvgWidgets",
        "--hidden-import=opencc",
        "--hidden-import=pysrt",
        "--hidden-import=soundfile",
        "--hidden-import=pydub",
        "--hidden-import=ffmpeg",
        "--hidden-import=huggingface_hub",
        "--hidden-import=objc",
        "--hidden-import=Foundation",
        "--hidden-import=AppKit",
        "--hidden-import=AVFoundation",
        "--hidden-import=Quartz",
        # === 其他缺失的隱藏導入 ===
        "--hidden-import=charset_normalizer",
        "--hidden-import=packaging",
        "--hidden-import=packaging.version",
        "--hidden-import=yaml",
        "--hidden-import=fsspec",
        "--hidden-import=aiohttp",
        
        # === Runtime Hooks ===
        "--runtime-hook=rthooks/rthook_mlx.py",  # MLX library path setup
        
        # === macOS 特定 ===
        "--osx-bundle-identifier=com.cantobeats.app",
        "--target-arch=arm64",  # 强制 ARM64
        
        # === 优化 ===
        "--clean",
        "--noconfirm",
        
        # === 排除不需要的模块 ===
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=jupyter",
        "--exclude-module=IPython",
    ]
    
    # 添加 MLX metallib（如果找到）
    if mlx_metallib_arg:
        cmd.insert(-8, mlx_metallib_arg)  # 插入在 Runtime Hooks 之前
    
    
    # === 打包 FFmpeg 二進位文件 ===
    # 從 Homebrew 複製 ffmpeg 和 ffprobe 到 .app bundle
    ffmpeg_paths = [
        '/opt/homebrew/bin/ffmpeg',   # Apple Silicon
        '/opt/homebrew/bin/ffprobe',
        '/usr/local/bin/ffmpeg',      # Intel Mac (fallback)
        '/usr/local/bin/ffprobe',
    ]
    
    for ffmpeg_bin in ffmpeg_paths:
        if Path(ffmpeg_bin).exists():
            # 添加到 PyInstaller 的 --add-binary
            # 格式: source:destination_folder
            # 目標: Contents/MacOS/ (與主執行檔同目錄)
            cmd.append(f"--add-binary={ffmpeg_bin}:.")
            print(f"✅ 將打包 FFmpeg: {ffmpeg_bin}")
    
    # 不添加 libmpv (macOS 使用 AVPlayer)
    
    print("\n构建命令:")
    print(" ".join(cmd))
    print("\n" + "-" * 60)
    print("开始 PyInstaller 构建 (预计 10-20 分钟)...")
    print("-" * 60 + "\n")
    
    try:
        subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("✅ 构建成功!")
        print(f"输出: dist/Canto-beats.app")
        print("=" * 60)
        
        # 移除隔离属性
        print("\n移除隔离属性...")
        subprocess.run(['xattr', '-cr', 'dist/Canto-beats.app'], check=False)
        
        # === Fix MLX metallib path ===
        # MLX C++ core at Frameworks/mlx/core.cpython-311-darwin.so has rpath @loader_path/..
        # This means it loads libmlx.dylib from Frameworks/
        # MLX then searches for mlx.metallib NEXT TO libmlx.dylib (in same directory)
        # So we need to create Contents/Frameworks/mlx.metallib
        print("\n修復 MLX metallib 路徑...")
        frameworks_dir = Path('dist/Canto-beats.app/Contents/Frameworks')
        metallib_src = Path('dist/Canto-beats.app/Contents/Resources/mlx/lib/mlx.metallib')
        
        if metallib_src.exists():
            # Place metallib directly in Frameworks/ (same level as libmlx.dylib)
            metallib_dst = frameworks_dir / 'mlx.metallib'
            
            if metallib_dst.exists() or metallib_dst.is_symlink():
                metallib_dst.unlink()
            
            # Create symlink - relative path from Frameworks/ to Resources/mlx/lib/
            relative_path = os.path.relpath(metallib_src, frameworks_dir)
            metallib_dst.symlink_to(relative_path)
            print(f"  ✅ Created: {metallib_dst} -> {relative_path}")
            
            # Also put one in Frameworks/lib/ as backup
            frameworks_lib = frameworks_dir / 'lib'
            frameworks_lib.mkdir(parents=True, exist_ok=True)
            metallib_dst2 = frameworks_lib / 'mlx.metallib'
            if metallib_dst2.exists() or metallib_dst2.is_symlink():
                metallib_dst2.unlink()
            relative_path2 = os.path.relpath(metallib_src, frameworks_lib)
            metallib_dst2.symlink_to(relative_path2)
            print(f"  ✅ Created: {metallib_dst2} -> {relative_path2}")
        else:
            print(f"  ⚠️ metallib not found at: {metallib_src}")
        
        # === 公證前清理：移除 Resources 入面會導致公證失敗嘅內容 ===
        # 成功公證嘅 DMG 冇 Resources/ 入面嘅二進位，所以我哋要移除佢哋
        print("\n清理 Resources 目錄 (公證必需)...")
        resources_dir = Path('dist/Canto-beats.app/Contents/Resources')
        removed_count = 0
        
        if resources_dir.exists():
            import shutil
            
            # 1. 移除整個 PySide6 目錄（包含重複嘅 Qt Frameworks）
            pyside6_dir = resources_dir / 'PySide6'
            if pyside6_dir.exists():
                print(f"  ❌ 移除: PySide6/ (重複嘅 Qt Frameworks)")
                shutil.rmtree(pyside6_dir)
                removed_count += 1
            
            # 2. 移除所有 symlinks（包括壞嘅同有效嘅）
            # 原因：Resources/ 唔應該有任何 symlinks，有嘅話會導致 spctl 失敗
            for item in resources_dir.iterdir():
                if item.is_symlink():
                    print(f"  ❌ 移除: {item.name} (symlink)")
                    item.unlink()
                    removed_count += 1
        
        # 3. 搵出並移除所有 broken symlinks（遞歸搜尋）
        print("\n清理所有壞 symlinks (遞歸)...")
        broken_symlinks = []
        for root, dirs, files in os.walk('dist/Canto-beats.app'):
            for name in files + dirs:
                path = Path(root) / name
                if path.is_symlink() and not path.exists():
                    broken_symlinks.append(path)
        
        for symlink in broken_symlinks:
            print(f"  ❌ 移除壞 symlink: {symlink.relative_to('dist/Canto-beats.app')}")
            symlink.unlink()
            removed_count += 1
        
        print(f"  ✅ 已清理 {removed_count} 個項目")
        
        # 4. 驗證 spctl（確保 Gatekeeper 接受）
        print("\n驗證 spctl (Gatekeeper 檢查)...")
        try:
            result = subprocess.run(
                ['spctl', '-a', '-v', 'dist/Canto-beats.app'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"  ✅ spctl 驗證成功: {result.stderr.strip()}")
            else:
                # spctl 失敗 - 再次嘗試清理並重試
                print(f"  ⚠️ spctl 初次驗證失敗，執行深度清理...")
                
                # 移除所有殘留嘅 broken symlinks
                subprocess.run(['find', 'dist/Canto-beats.app', '-type', 'l', '!', '-exec', 'test', '-e', '{}', ';', '-delete'], check=False)
                
                # 重新驗證
                result2 = subprocess.run(['spctl', '-a', '-v', 'dist/Canto-beats.app'], capture_output=True, text=True, timeout=30)
                if result2.returncode == 0:
                    print(f"  ✅ spctl 重試成功: {result2.stderr.strip()}")
                else:
                    print(f"  ⚠️ spctl 仍然失敗: {result2.stderr.strip()}")
                    print(f"     原因: {result2.stderr}")
                    print(f"     提示: App 可能需要重新簽名")
        except subprocess.TimeoutExpired:
            print("  ⚠️ spctl 驗證超時")
        except Exception as e:
            print(f"  ⚠️ spctl 驗證出錯: {e}")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败 (退出码 {e.returncode})")
        return e.returncode
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        return 1


def create_dmg(auto_yes=False):
    """创建 DMG 安装包"""
    if not auto_yes:
        print("\n是否创建 DMG 安装包? (y/N): ", end='')
        response = input()

        if response.lower() != 'y':
            return None

    print("\n创建 DMG...")

    try:
        # 创建临时目录
        dmg_dir = Path("dist/dmg")
        dmg_dir.mkdir(exist_ok=True)

        # 复制 .app
        subprocess.run(['cp', '-r', 'dist/Canto-beats.app', 'dist/dmg/'], check=True)

        # 创建 Applications 符号链接（方便用户拖拽安装）
        subprocess.run(['ln', '-s', '/Applications', 'dist/dmg/Applications'], check=False)

        # 创建 README.txt（繁體中文安裝說明）
        readme_content = """╔═══════════════════════════════════════════════════════════════╗
║                   Canto-beats 安裝說明                        ║
║              粵語字幕自動生成與校正工具                         ║
╚═══════════════════════════════════════════════════════════════╝

歡迎使用 Canto-beats！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 安裝步驟

1. 將 Canto-beats.app 拖曳到 Applications 資料夾
2. 安裝 FFmpeg（必須）：
   • 開啟終端機（Terminal.app）
   • 執行：brew install ffmpeg
   • 如未安裝 Homebrew，請先安裝：
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

3. 首次啟動時，如果系統提示「無法打開」，請執行以下步驟：
   • 前往「系統設定」→「隱私權與安全性」
   • 找到 Canto-beats 並點擊「仍要打開」
   • 或在終端機執行：xattr -cr /Applications/Canto-beats.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💻 系統需求

• macOS 15.0 或更新版本
• Apple Silicon (M1/M2/M3) 處理器
• 至少 8GB RAM（建議 16GB 以上）
• 至少 15GB 可用儲存空間
• FFmpeg（透過 Homebrew 安裝）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 使用說明

1. 啟動 Canto-beats.app
2. 點擊「選擇影片」載入您的影片檔案
3. 選擇字幕風格：
   • 口語：保留粵語口語詞彙（嘅、唔、冇等）
   • 半書面語：部分轉換為書面語
   • 書面語：完全轉換為正式書面語
4. 點擊「開始轉錄」
5. 完成後可編輯字幕並導出 SRT 檔案

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ 主要功能

• 🎯 高精度粵語語音辨識
• 📝 智能粵語字幕校正
• 🎨 三種字幕風格轉換
• ⚡ Apple Silicon GPU 加速
• 🎬 即時預覽與編輯
• 💾 導出標準 SRT,ASS,XML 格式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 技術支援

如遇到問題，請檢查：
• 系統是否符合最低需求
• 是否有足夠的儲存空間
• 影片格式是否支援（建議使用 MP4/MOV）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© 2024 Canto-beats | 版本 1.0.0a | Apple Silicon 優化版
"""
        readme_path = dmg_dir / "README.txt"
        readme_path.write_text(readme_content, encoding='utf-8')
        print(f"✅ 已創建 README.txt")

        # 创建 DMG
        dmg_path = 'dist/Canto-beats-Final.dmg'
        subprocess.run([
            'hdiutil', 'create',
            '-volname', 'Canto-beats',
            '-srcfolder', 'dist/dmg',
            '-ov', '-format', 'UDZO',
            dmg_path
        ], check=True)

        # 清理
        subprocess.run(['rm', '-rf', 'dist/dmg'], check=True)

        print(f"✅ DMG 创建成功: {dmg_path}")

        # 获取文件大小
        size_mb = Path(dmg_path).stat().st_size / (1024 * 1024)
        print(f"   大小: {size_mb:.1f} MB")

        return dmg_path

    except subprocess.CalledProcessError as e:
        print(f"❌ DMG 创建失败: {e}")
        return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Canto-beats Silicon macOS 打包工具")
    parser.add_argument("--auto-dmg", action="store_true", help="自動創建 DMG（不詢問）")
    parser.add_argument("--dmg-only", action="store_true", help="僅創建 DMG（跳過構建）")
    args = parser.parse_args()

    print("Canto-beats Silicon macOS 打包工具")
    print("=" * 60)

    # 如果只創建 DMG
    if args.dmg_only:
        if not Path("dist/Canto-beats.app").exists():
            print("❌ 錯誤: dist/Canto-beats.app 不存在")
            print("   請先運行構建: python build_silicon_macos.py")
            return 1

        dmg_path = create_dmg(auto_yes=True)
        if dmg_path:
            print("\n" + "=" * 60)
            print("🎉 DMG 創建完成!")
            print("=" * 60)
            print(f"\n分發文件: {dmg_path}")
            print("\n後續步驟:")
            print("  1. 測試 DMG: open dist/Canto-beats-Silicon.dmg")
            print("  2. 簽名和公證: python notarize_macos.py")
        return 0

    # 检查架构
    check_architecture()

    # 检查依赖
    check_dependencies()

    # 构建
    result = build_app()

    if result == 0:
        # 创建 DMG
        dmg_path = create_dmg(auto_yes=args.auto_dmg)

        print("\n" + "=" * 60)
        print("🎉 打包完成!")
        print("=" * 60)
        print("\n測試命令:")
        print("  open dist/Canto-beats.app")

        if dmg_path:
            print("\n分發文件:")
            print(f"  {dmg_path}")
            print("\n後續步驟:")
            print("  1. 測試 DMG: open dist/Canto-beats-Silicon.dmg")
            print("  2. 簽名和公證: python notarize_macos.py")
        else:
            print("\n如需創建 DMG:")
            print("  python build_silicon_macos.py --dmg-only")

    return result


if __name__ == "__main__":
    sys.exit(main())

