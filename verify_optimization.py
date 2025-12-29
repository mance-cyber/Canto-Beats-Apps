#!/usr/bin/env python3
"""快速驗證 Apple Silicon 優化是否生效"""

import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("\n" + "="*60)
print("Apple Silicon 優化驗證")
print("="*60)

# 測試 1: PyTorch MPS
print("\n[1/3] 測試 PyTorch MPS...")
try:
    import torch
    if torch.backends.mps.is_available():
        print("  ✅ MPS 可用")
        # 測試張量運算
        x = torch.randn(100, 100, device='mps')
        y = torch.matmul(x, x)
        print("  ✅ MPS 張量運算正常")
    else:
        print("  ⚠️  MPS 不可用（可能不是 Apple Silicon Mac）")
except Exception as e:
    print(f"  ❌ 錯誤: {e}")

# 測試 2: 硬件檢測
print("\n[2/3] 測試硬件檢測...")
try:
    from core.hardware_detector import HardwareDetector
    
    detector = HardwareDetector()
    profile = detector.detect()
    
    print(f"  ✅ 設備: {profile.device}")
    print(f"  ✅ VRAM: {profile.vram_gb:.1f} GB")
    print(f"  ✅ 性能等級: {profile.tier.value}")
    
    if profile.device == "mps" and profile.vram_gb > 0:
        print("  🎉 MPS VRAM 檢測修復成功！")
    elif profile.device == "mps" and profile.vram_gb == 0:
        print("  ❌ MPS VRAM 仍為 0，修復未生效")
        
except Exception as e:
    print(f"  ❌ 錯誤: {e}")

# 測試 3: VideoToolbox
print("\n[3/3] 測試 VideoToolbox...")
try:
    import subprocess
    result = subprocess.run(
        ['ffmpeg', '-hwaccels'],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if 'videotoolbox' in result.stdout.lower():
        print("  ✅ VideoToolbox 可用")
        
        # 測試編碼器函數
        from utils.video_utils import get_optimal_video_encoder
        encoder = get_optimal_video_encoder()
        print(f"  ✅ 最佳編碼器: {encoder['vcodec']}")
    else:
        print("  ⚠️  VideoToolbox 不可用")
        
except Exception as e:
    print(f"  ❌ 錯誤: {e}")

print("\n" + "="*60)
print("驗證完成！")
print("="*60 + "\n")

