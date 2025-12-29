#!/usr/bin/env python3
"""打包前全面檢查"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """檢查依賴"""
    print("\n1️⃣ 檢查依賴...")
    missing = []
    
    deps = [
        'PySide6', 'torch', 'torchaudio', 'transformers', 
        'mlx', 'mlx_whisper', 'faster_whisper', 'huggingface_hub',
        'ffmpeg', 'pydub', 'soundfile', 'pysrt', 'opencc'
    ]
    
    for dep in deps:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            missing.append(dep)
    
    return missing

def check_resources():
    """檢查資源文件"""
    print("\n2️⃣ 檢查資源文件...")

    resources = [
        'public/icons/app_icon.icns',
        'public/icons/app_icon.png',
        'src/resources/cantonese_mapping.json',
        'src/resources/profanity_mapping.json',
        'src/resources/english_mapping.json',
    ]

    missing = []
    for res in resources:
        if Path(res).exists():
            print(f"  ✅ {res}")
        else:
            print(f"  ❌ {res}")
            missing.append(res)

    return missing

def check_core_modules():
    """檢查核心模塊"""
    print("\n3️⃣ 檢查核心模塊...")
    
    sys.path.insert(0, 'src')
    
    modules = [
        'core.config',
        'core.hardware_detector',
        'models.whisper_asr',
        'models.qwen_llm',
        'models.vad_processor',
        'pipeline.subtitle_pipeline_v2',
        'ui.main_window',
        'ui.avplayer_widget',
        'utils.audio_utils',
        'utils.video_utils',
    ]
    
    errors = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except Exception as e:
            print(f"  ❌ {mod}: {e}")
            errors.append((mod, str(e)))
    
    return errors

def check_ffmpeg():
    """檢查 FFmpeg"""
    print("\n4️⃣ 檢查 FFmpeg...")
    
    import shutil
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    
    if ffmpeg:
        print(f"  ✅ ffmpeg: {ffmpeg}")
    else:
        print(f"  ❌ ffmpeg not found")
    
    if ffprobe:
        print(f"  ✅ ffprobe: {ffprobe}")
    else:
        print(f"  ❌ ffprobe not found")
    
    return ffmpeg and ffprobe

def check_libmpv():
    """檢查 libmpv"""
    print("\n5️⃣ 檢查 libmpv...")
    
    import ctypes.util
    libmpv = ctypes.util.find_library('mpv')
    
    if libmpv:
        print(f"  ✅ libmpv: {libmpv}")
        return True
    else:
        print(f"  ❌ libmpv not found")
        return False

def check_spec_file():
    """檢查 spec 文件"""
    print("\n6️⃣ 檢查 PyInstaller spec...")

    spec_files = list(Path('.').glob('*.spec'))

    if spec_files:
        for spec in spec_files:
            print(f"  ✅ {spec}")
        return True
    else:
        print(f"  ℹ️  沒有 .spec 文件（打包時會自動生成）")
        return True  # 不算錯誤

def main():
    print("=" * 60)
    print("打包前全面檢查")
    print("=" * 60)
    
    os.chdir(Path(__file__).parent)
    
    # 執行檢查
    missing_deps = check_dependencies()
    missing_res = check_resources()
    module_errors = check_core_modules()
    has_ffmpeg = check_ffmpeg()
    has_libmpv = check_libmpv()
    has_spec = check_spec_file()
    
    # 總結
    print("\n" + "=" * 60)
    print("檢查總結")
    print("=" * 60)
    
    issues = []
    
    if missing_deps:
        issues.append(f"❌ 缺少依賴: {', '.join(missing_deps)}")
    
    if missing_res:
        issues.append(f"❌ 缺少資源: {', '.join(missing_res)}")
    
    if module_errors:
        issues.append(f"❌ 模塊錯誤: {len(module_errors)} 個")
    
    if not has_ffmpeg:
        issues.append("❌ FFmpeg 未安裝")
    
    if not has_libmpv:
        issues.append("❌ libmpv 未安裝")
    
    if not has_spec:
        issues.append("❌ 缺少 spec 文件")
    
    if issues:
        print("\n⚠️  發現問題:")
        for issue in issues:
            print(f"  {issue}")
        print("\n請先解決這些問題再打包")
        return False
    else:
        print("\n✅ 所有檢查通過，可以開始打包！")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

