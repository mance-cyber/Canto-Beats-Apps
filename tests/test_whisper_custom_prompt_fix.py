#!/usr/bin/env python3
"""
測試 Whisper custom_prompt 修復

驗證：
1. WhisperASR.transcribe() 接受 initial_prompt 參數
2. SubtitlePipelineV2 正確傳遞 custom_prompt
3. TranscribeWorker 正確傳遞 custom_prompt
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_whisper_asr_signature():
    """測試 WhisperASR.transcribe() 方法簽名"""
    print("=" * 70)
    print("測試 1: WhisperASR.transcribe() 方法簽名")
    print("=" * 70)
    
    try:
        from models.whisper_asr import WhisperASR
        import inspect
        
        # 獲取方法簽名
        sig = inspect.signature(WhisperASR.transcribe)
        params = list(sig.parameters.keys())
        
        print(f"參數列表: {params}")
        
        # 檢查是否有 initial_prompt
        if 'initial_prompt' in params:
            print("✅ 支持 initial_prompt 參數")
        else:
            print("❌ 不支持 initial_prompt 參數")
            return False
        
        # 檢查是否錯誤地有 custom_prompt
        if 'custom_prompt' in params:
            print("❌ 錯誤：仍然有 custom_prompt 參數")
            return False
        else:
            print("✅ 沒有 custom_prompt 參數（正確）")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_pipeline_v2_usage():
    """測試 SubtitlePipelineV2 是否正確使用 initial_prompt"""
    print("\n" + "=" * 70)
    print("測試 2: SubtitlePipelineV2 使用 initial_prompt")
    print("=" * 70)
    
    try:
        # 讀取源碼檢查
        with open('src/pipeline/subtitle_pipeline_v2.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有錯誤的 custom_prompt 參數傳遞
        if 'custom_prompt=custom_prompt' in content:
            print("❌ 仍然使用 custom_prompt 參數傳遞")
            return False
        else:
            print("✅ 沒有使用 custom_prompt 參數傳遞")
        
        # 檢查是否正確使用 initial_prompt
        if 'initial_prompt=initial_prompt' in content:
            print("✅ 正確使用 initial_prompt 參數")
        else:
            print("❌ 沒有使用 initial_prompt 參數")
            return False
        
        # 檢查是否有構建 initial_prompt 的邏輯
        if 'initial_prompt = f"{base_prompt}' in content:
            print("✅ 正確構建 initial_prompt")
        else:
            print("⚠️  可能沒有構建 initial_prompt（檢查邏輯）")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_transcribe_worker_usage():
    """測試 TranscribeWorker 是否正確使用 initial_prompt"""
    print("\n" + "=" * 70)
    print("測試 3: TranscribeWorker 使用 initial_prompt")
    print("=" * 70)
    
    try:
        # 讀取源碼檢查
        with open('src/ui/transcription_worker.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有錯誤的 custom_prompt 參數傳遞
        if 'custom_prompt=custom_prompt' in content:
            print("❌ 仍然使用 custom_prompt 參數傳遞")
            return False
        else:
            print("✅ 沒有使用 custom_prompt 參數傳遞")
        
        # 檢查是否正確使用 initial_prompt
        if 'initial_prompt=initial_prompt' in content:
            print("✅ 正確使用 initial_prompt 參數")
        else:
            print("⚠️  可能沒有使用 initial_prompt 參數（檢查是否需要）")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def main():
    print("Whisper custom_prompt 修復驗證")
    print("=" * 70)
    
    results = []
    
    # 測試 1
    results.append(("WhisperASR 方法簽名", test_whisper_asr_signature()))
    
    # 測試 2
    results.append(("SubtitlePipelineV2 使用", test_pipeline_v2_usage()))
    
    # 測試 3
    results.append(("TranscribeWorker 使用", test_transcribe_worker_usage()))
    
    # 總結
    print("\n" + "=" * 70)
    print("測試總結")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {name}")
    
    print("-" * 70)
    print(f"總計: {passed}/{total} 通過")
    
    if passed == total:
        print("\n✅ 所有測試通過！修復成功。")
        return 0
    else:
        print(f"\n❌ {total - passed} 個測試失敗，請檢查修復。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

