"""
Test script to compare Cantonese transcription with the new model.
Tests the Transformers-based Cantonese Whisper model.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.whisper_asr import WhisperASR
from core.config import Config


def test_cantonese_model():
    """Test the new Cantonese Whisper model."""
    print("=" * 70)
    print("Canto-beats: 粵語專用 Whisper 模型測試")
    print("=" * 70)
    
    config = Config()
    
    print(f"\n配置信息：")
    print(f"  Build type: {config.get('build_type')}")
    print(f"  使用粵語模型: {config.get('use_cantonese_model')}")
    print(f"  Flagship 模型: {config.get('cantonese_model_flagship')}")
    print(f"  Lite 模型: {config.get('cantonese_model_lite')}")
    
    # Initialize ASR
    asr = WhisperASR(config)
    print(f"\n選擇的模型: {asr.model_id}")
    print(f"設備: {asr.device}")
    print(f"數據類型: {asr.torch_dtype}")
    
    print("\n正在加載模型...")
    print("(首次運行時會下載模型，可能需要幾分鐘)")
    
    try:
        asr.load_model()
        print("✅ 模型加載成功！")
        
        model_info = asr.get_model_info()
        print(f"\n模型信息：")
        print(f"  模型 ID: {model_info['model_id']}")
        print(f"  設備: {model_info['device']}")
        print(f"  粵語模型: {model_info['is_cantonese']}")
        print(f"  後端: {model_info['backend']}")
        print(f"  已加載: {model_info['is_loaded']}")
        
        # Test with audio file if provided
        if len(sys.argv) > 1:
            audio_file = sys.argv[1]
            print(f"\n\n正在轉寫音頻: {audio_file}")
            print("-" * 70)
            
            result = asr.transcribe(audio_file, language='yue')
            
            print(f"\n轉寫結果:")
            print(f"語言: {result['language']}")
            print(f"文本長度: {len(result['text'])} 字符")
            print(f"分段數量: {len(result['segments'])}")
            
            print(f"\n完整文本:")
            print(result['text'])
            
            print(f"\n分段詳情:")
            for seg in result['segments']:
                print(f"  [{seg.start:.2f}s - {seg.end:.2f}s]")
                print(f"    {seg.text}")
            
            # Check for Cantonese characters
            cantonese_chars = ['佢', '喺', '睇', '嘅', '咁', '啲', '咗', '嚟', '冇', '諗', '唔', '咩', '乜', '點', '邊', '噉', '嗰', '呢', '哋', '咪', '囉', '喎', '啦', '㗎', '吖']
            found_chars = [char for char in cantonese_chars if char in result['text']]
            
            print(f"\n粵語口語字識別:")
            if found_chars:
                print(f"  ✅ 找到 {len(found_chars)} 個粵語口語字: {', '.join(found_chars)}")
            else:
                print(f"  ⚠️ 未找到常見粵語口語字")
        else:
            print("\n\n提示：如需測試轉寫，請提供音頻文件路徑：")
            print("  python test_cantonese_transcription.py <audio_file>")
        
        print("\n" + "=" * 70)
        print("✅ 測試成功！粵語模型集成完成！")
        print("=" * 70)
        
        print("\n下一步：")
        print("  1. 運行主程序 python main.py")
        print("  2. 載入粵語影片進行轉寫")
        print("  3. 檢查轉寫結果中的粵語口語字")
        print("  4. 對比之前的轉寫結果")
        
        asr.cleanup()
        return True
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_cantonese_model()
