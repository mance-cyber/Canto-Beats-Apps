#!/usr/bin/env python3
"""清除書面語轉換緩存"""

from pathlib import Path
import shutil

cache_dir = Path.home() / ".canto-beats" / "style_cache"

if cache_dir.exists():
    try:
        shutil.rmtree(cache_dir)
        print(f"✅ 已清除緩存: {cache_dir}")
        print("請重新啟動應用程式，重新轉換書面語時會使用新的 prompt")
    except Exception as e:
        print(f"❌ 清除失敗: {e}")
else:
    print("⚠️ 緩存目錄不存在")

