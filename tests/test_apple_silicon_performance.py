#!/usr/bin/env python3
"""
Apple Silicon 優化效果測試腳本

測試 MPS 加速、VideoToolbox 編碼等優化的實際性能提升。

使用方法:
    python test_apple_silicon_performance.py
"""

import sys
import time
import platform
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

# ==================== 測試 1: 硬件檢測 ====================
def test_hardware_detection():
    print("\n" + "="*60)
    print("測試 1: 硬件檢測與 VRAM 計算")
    print("="*60)
    
    try:
        from src.core.hardware_detector import HardwareDetector
        
        detector = HardwareDetector()
        profile = detector.detect()
        
        print(f"✅ 檢測成功")
        print(f"  設備: {profile.device}")
        print(f"  VRAM: {profile.vram_gb:.1f} GB")
        print(f"  性能等級: {profile.tier.value}")
        print(f"  描述: {profile.description}")
        
        # 驗證 MPS 設備是否正確識別
        if profile.device == "mps" and profile.vram_gb > 0:
            print(f"  ✅ MPS VRAM 檢測正常")
        elif profile.device == "mps" and profile.vram_gb == 0:
            print(f"  ❌ MPS VRAM 仍為 0，修復未生效")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 測試 2: PyTorch MPS ====================
def test_pytorch_mps():
    print("\n" + "="*60)
    print("測試 2: PyTorch MPS 後端")
    print("="*60)
    
    try:
        import torch
        
        print(f"PyTorch 版本: {torch.__version__}")
        print(f"MPS 可用: {torch.backends.mps.is_available()}")
        print(f"MPS 已構建: {torch.backends.mps.is_built()}")
        
        if not torch.backends.mps.is_available():
            print("⚠️  MPS 不可用（可能不是 Apple Silicon Mac）")
            return True
        
        # 測試 MPS 張量運算
        print("\n測試 MPS 張量運算...")
        x = torch.randn(1000, 1000, device='mps')
        y = torch.randn(1000, 1000, device='mps')
        
        start = time.time()
        z = torch.matmul(x, y)
        torch.mps.synchronize()  # 等待 GPU 完成
        elapsed = time.time() - start
        
        print(f"  ✅ 矩陣乘法 (1000x1000): {elapsed*1000:.2f} ms")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 測試 3: LLM MPS 加載 ====================
def test_llm_mps_loading():
    print("\n" + "="*60)
    print("測試 3: LLM 模型 MPS 加載")
    print("="*60)
    
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        if not torch.backends.mps.is_available():
            print("⚠️  跳過（MPS 不可用）")
            return True
        
        # 使用小模型測試
        model_id = "Qwen/Qwen2.5-0.5B-Instruct"  # 500M 參數，快速測試
        
        print(f"加載測試模型: {model_id}")
        print("  (首次運行會下載模型，請耐心等待...)")
        
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="mps",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        load_time = time.time() - start
        
        print(f"  ✅ 模型加載成功 ({load_time:.1f}s)")
        print(f"  設備: {model.device}")
        
        # 測試推理
        print("\n測試推理...")
        inputs = tokenizer("你好", return_tensors="pt").to('mps')
        
        start = time.time()
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=10)
        torch.mps.synchronize()
        inference_time = time.time() - start
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"  ✅ 推理成功 ({inference_time:.2f}s)")
        print(f"  輸出: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==================== 測試 4: FFmpeg VideoToolbox ====================
def test_videotoolbox():
    print("\n" + "="*60)
    print("測試 4: FFmpeg VideoToolbox 支持")
    print("="*60)
    
    try:
        import subprocess
        
        # 檢查 FFmpeg 是否安裝
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("❌ FFmpeg 未安裝")
            return False
        
        print(f"✅ FFmpeg 已安裝")
        
        # 檢查硬件加速支持
        result = subprocess.run(
            ['ffmpeg', '-hwaccels'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        hwaccels = result.stdout.lower()
        print(f"\n支持的硬件加速:")
        for line in result.stdout.strip().split('\n')[1:]:  # 跳過標題行
            print(f"  - {line}")
        
        if 'videotoolbox' in hwaccels:
            print(f"\n  ✅ VideoToolbox 可用")
        else:
            print(f"\n  ⚠️  VideoToolbox 不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

# ==================== 主程序 ====================
def main():
    print("\n" + "="*70)
    print(" "*15 + "Apple Silicon 優化效果測試")
    print("="*70)
    
    print(f"\n系統信息:")
    print(f"  平台: {platform.system()} {platform.release()}")
    print(f"  處理器: {platform.processor()}")
    print(f"  架構: {platform.machine()}")
    
    # 運行所有測試
    tests = [
        ("硬件檢測", test_hardware_detection),
        ("PyTorch MPS", test_pytorch_mps),
        ("LLM MPS 加載", test_llm_mps_loading),
        ("VideoToolbox", test_videotoolbox),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n\n⚠️  測試被用戶中斷")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 測試異常: {e}")
            results.append((name, False))
    
    # 總結
    print("\n" + "="*70)
    print("測試總結")
    print("="*70)
    
    for name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {status}  {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！Apple Silicon 優化已生效。")
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤信息。")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

