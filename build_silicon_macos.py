#!/usr/bin/env python3
"""
Silicon macOS (Apple M1/M2/M3) 专用打包脚本
针对 ARM64 架构优化，处理所有平台特定依赖

Usage:
    python build_silicon_macos.py
"""

import subprocess
import sys
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
    
    project_dir = Path(__file__).parent
    main_script = str(project_dir / "main.py")
    
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
    
    # 不添加 libmpv (macOS 使用 AVPlayer)
    # libmpv_path = find_libmpv()
    # if libmpv_path:
    #     cmd.append(f"--add-binary={libmpv_path}:.")
    
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
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 构建失败 (退出码 {e.returncode})")
        return e.returncode
    except Exception as e:
        print(f"\n❌ 构建失败: {e}")
        return 1


def create_dmg():
    """创建 DMG 安装包"""
    print("\n是否创建 DMG 安装包? (y/N): ", end='')
    response = input()
    
    if response.lower() != 'y':
        return
    
    print("\n创建 DMG...")
    
    try:
        # 创建临时目录
        dmg_dir = Path("dist/dmg")
        dmg_dir.mkdir(exist_ok=True)
        
        # 复制 .app
        subprocess.run(['cp', '-r', 'dist/Canto-beats.app', 'dist/dmg/'], check=True)
        
        # 创建 DMG
        subprocess.run([
            'hdiutil', 'create',
            '-volname', 'Canto-beats',
            '-srcfolder', 'dist/dmg',
            '-ov', '-format', 'UDZO',
            'dist/Canto-beats-Silicon.dmg'
        ], check=True)
        
        # 清理
        subprocess.run(['rm', '-rf', 'dist/dmg'], check=True)
        
        print("✅ DMG 创建成功: dist/Canto-beats-Silicon.dmg")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG 创建失败: {e}")


def main():
    """主函数"""
    print("Canto-beats Silicon macOS 打包工具")
    print("=" * 60)
    
    # 检查架构
    check_architecture()
    
    # 检查依赖
    check_dependencies()
    
    # 构建
    result = build_app()
    
    if result == 0:
        # 创建 DMG
        create_dmg()
        
        print("\n" + "=" * 60)
        print("🎉 打包完成!")
        print("=" * 60)
        print("\n测试命令:")
        print("  open dist/Canto-beats.app")
        print("\n分发文件:")
        print("  dist/Canto-beats-Silicon.dmg (如已创建)")
    
    return result


if __name__ == "__main__":
    sys.exit(main())

