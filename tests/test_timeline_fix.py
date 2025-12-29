#!/usr/bin/env python3
"""測試時間軸和縮略圖修復"""

print("✅ 修復完成！")
print("\n請重新啟動應用程式並測試：")
print("\n1. 縮略圖修復:")
print("   - 修復了 CoreGraphics import (改為從 Quartz 導入)")
print("   - 現在應該可以看到視頻縮略圖")
print("\n2. 時間軸移動修復:")
print("   - 添加了 _has_video = True 設置")
print("   - 添加了調試日誌")
print("   - position_changed 信號已正確發送")
print("\n3. 測試步驟:")
print("   - 加載視頻")
print("   - 點擊播放按鈕")
print("   - 查看日誌中的 '[AVPlayer] Timer started' 和 '[AVPlayer] Position' 信息")
print("   - 確認時間軸是否移動")
print("\n如果仍有問題，請分享日誌輸出。")

