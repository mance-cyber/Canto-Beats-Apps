
from src.pipeline.subtitle_pipeline_v2 import SubtitlePipelineV2
from src.core.config import Config

def test_corrections():
    config = Config()
    pipeline = SubtitlePipelineV2(config)
    
    test_cases = [
        ("這裡有冤無老訴啊", "這裡有冤無路訴啊"),
        ("佢零舍不同", "佢零舍不同"),  # 凌射 -> 零舍 correction
        ("佢凌射不同", "佢零舍不同"),
        ("That is the Porn", "That is the Point"),
        ("Get a Grip", "Get a Group"),
        ("我感覺身同感受", "我感覺身同感受"),
        ("我感覺心希感受", "我感覺身同感受"),
        ("默哀", "默哀"),
        ("物外", "默哀"),
    ]
    
    print("Testing Corrections...")
    for original, expected in test_cases:
        corrected = pipeline._apply_simple_corrections(original)
        status = "✅ PASS" if corrected == expected else f"❌ FAIL (Got: {corrected})"
        print(f"'{original}' -> '{corrected}' : {status}")

if __name__ == "__main__":
    test_corrections()
