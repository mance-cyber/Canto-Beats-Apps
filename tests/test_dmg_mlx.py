#!/usr/bin/env python3
"""測試 DMG 應用的 MLX 狀態"""

import sys
import os

# 設置路徑到 DMG 應用
dmg_app = "/Volumes/Canto-beats/Canto-beats.app/Contents/Resources"
sys.path.insert(0, dmg_app)

print("=" * 60)
print("測試 DMG 應用的 MLX 狀態")
print("=" * 60)

# 1. 檢查 MLX 模塊
print("\n1️⃣ 檢查 MLX 模塊...")
try:
    import mlx.core as mx
    print(f"✅ MLX 可用: {mx.__version__ if hasattr(mx, '__version__') else 'OK'}")
except Exception as e:
    print(f"❌ MLX 導入失敗: {e}")
    sys.exit(1)

# 2. 檢查 MLX Whisper
print("\n2️⃣ 檢查 MLX Whisper...")
try:
    import mlx_whisper
    print(f"✅ MLX Whisper 可用")
except Exception as e:
    print(f"❌ MLX Whisper 導入失敗: {e}")
    sys.exit(1)

# 3. 檢查 PyTorch MPS
print("\n3️⃣ 檢查 PyTorch MPS...")
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"MPS available: {torch.backends.mps.is_available()}")
    print(f"MPS built: {torch.backends.mps.is_built()}")
except Exception as e:
    print(f"❌ PyTorch 檢查失敗: {e}")

print("\n" + "=" * 60)
print("✅ DMG 應用的 MLX 配置正常！")
print("=" * 60)

