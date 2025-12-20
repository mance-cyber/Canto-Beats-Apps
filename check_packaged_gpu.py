#!/usr/bin/env python3
"""檢查打包版本的 GPU 配置"""

import sys
import torch

print("=" * 60)
print("GPU 配置檢查")
print("=" * 60)

# 1. PyTorch 版本
print(f"\nPyTorch: {torch.__version__}")

# 2. MPS 可用性
print(f"\nMPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

# 3. 當前設備
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print(f"✅ Using MPS device")
    
    # 測試 tensor
    x = torch.randn(100, 100).to(device)
    y = torch.randn(100, 100).to(device)
    z = torch.matmul(x, y)
    print(f"✅ MPS tensor operations work")
else:
    print(f"❌ MPS not available, using CPU")

# 4. 檢查 MLX
try:
    import mlx.core as mx
    print(f"\n✅ MLX available: {mx.__version__}")
except:
    print(f"\n❌ MLX not available")

# 5. 檢查環境變量
import os
print(f"\nOMP_NUM_THREADS: {os.environ.get('OMP_NUM_THREADS', 'not set')}")
print(f"MKL_NUM_THREADS: {os.environ.get('MKL_NUM_THREADS', 'not set')}")

# 6. 檢查 Whisper 配置
sys.path.insert(0, 'src')
from core.hardware_detector import HardwareDetector

detector = HardwareDetector()
profile = detector.detect()

print(f"\n{'=' * 60}")
print(f"Hardware Profile")
print(f"{'=' * 60}")
print(f"Device: {profile.device}")
print(f"VRAM: {profile.vram_gb} GB")
print(f"Tier: {profile.tier}")
print(f"ASR Model: {profile.asr_model}")

