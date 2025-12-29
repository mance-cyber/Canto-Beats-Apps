#!/usr/bin/env python3
"""檢查 DMG 應用的 MLX Whisper 實際使用情況"""

import sys
sys.path.insert(0, '/Volumes/Canto-beats/Canto-beats.app/Contents/Resources')

print("=" * 60)
print("檢查 DMG 應用的 MLX Whisper")
print("=" * 60)

# 1. 檢查 utils.whisper_mlx
print("\n1️⃣ 檢查 whisper_mlx 模塊...")
try:
    from utils.whisper_mlx import MLXWhisperASR, is_available
    print(f"✅ whisper_mlx 可導入")
    print(f"MLX Whisper available: {is_available()}")
except Exception as e:
    print(f"❌ whisper_mlx 導入失敗: {e}")
    sys.exit(1)

# 2. 檢查 pipeline 是否會使用 MLX
print("\n2️⃣ 檢查 pipeline 配置...")
try:
    from pipeline.subtitle_pipeline_v2 import HAS_MLX_WHISPER
    print(f"HAS_MLX_WHISPER: {HAS_MLX_WHISPER}")
except Exception as e:
    print(f"❌ Pipeline 檢查失敗: {e}")

# 3. 測試創建 MLX Whisper 實例
print("\n3️⃣ 測試創建 MLX Whisper...")
try:
    asr = MLXWhisperASR(model_size="base")
    print(f"✅ MLX Whisper 實例創建成功")
    print(f"Backend: {asr.get_backend_type()}")
except Exception as e:
    print(f"❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

