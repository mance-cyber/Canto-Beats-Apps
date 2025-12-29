#!/usr/bin/env python3
"""測試首次下載觸發邏輯"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_download_trigger():
    """測試下載對話框是否會在首次使用時觸發"""
    
    print("=" * 60)
    print("測試：首次下載觸發邏輯")
    print("=" * 60)
    
    # 1. 檢查 MLX Whisper 模型是否已緩存
    print("\n1. 檢查 MLX Whisper 模型緩存...")
    try:
        from huggingface_hub import try_to_load_from_cache
        
        model_path = "mlx-community/whisper-large-v3-mlx"
        cache_path = try_to_load_from_cache(model_path, "config.json")
        
        if cache_path is None or cache_path == "_CACHED_":
            print(f"   ❌ 模型未緩存: {model_path}")
            print(f"   ✅ 首次轉寫時「應該」彈出下載對話框")
        else:
            print(f"   ✅ 模型已緩存: {cache_path}")
            print(f"   ⚠️  首次轉寫時「不會」彈出下載對話框")
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
    
    # 2. 檢查 Qwen LLM 模型是否已緩存
    print("\n2. 檢查 Qwen LLM 模型緩存...")
    try:
        from core.config import Config
        config = Config()
        
        llm_cached = config.is_model_cached("llm")
        
        if llm_cached:
            print(f"   ✅ Qwen 模型已緩存")
            print(f"   ⚠️  書面語轉換時「不會」彈出下載對話框")
        else:
            print(f"   ❌ Qwen 模型未緩存")
            print(f"   ✅ 書面語轉換時「應該」彈出下載對話框")
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
    
    # 3. 測試下載對話框組件
    print("\n3. 測試下載對話框組件...")
    try:
        from ui.download_dialog import ModelDownloadDialog, MLXWhisperDownloadWorker
        print(f"   ✅ ModelDownloadDialog 可導入")
        print(f"   ✅ MLXWhisperDownloadWorker 可導入")
    except Exception as e:
        print(f"   ❌ 導入失敗: {e}")
    
    # 4. 檢查 pipeline 中的下載邏輯
    print("\n4. 檢查 pipeline 下載邏輯...")
    try:
        with open("src/pipeline/subtitle_pipeline_v2.py", "r") as f:
            content = f.read()
            
        if "ModelDownloadDialog" in content:
            print(f"   ✅ Pipeline 包含下載對話框邏輯")
        else:
            print(f"   ❌ Pipeline 缺少下載對話框邏輯")
            
        if "MLXWhisperDownloadWorker" in content:
            print(f"   ✅ Pipeline 包含 MLX 下載 Worker")
        else:
            print(f"   ❌ Pipeline 缺少 MLX 下載 Worker")
    except Exception as e:
        print(f"   ❌ 檢查失敗: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
    
    print("\n💡 如何測試首次下載對話框：")
    print("1. 刪除 MLX Whisper 緩存:")
    print("   rm -rf ~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-mlx")
    print("\n2. 重新啟動應用程式")
    print("\n3. 加載視頻並點擊「開始轉寫」")
    print("\n4. 應該會看到下載進度對話框")

if __name__ == "__main__":
    test_download_trigger()

