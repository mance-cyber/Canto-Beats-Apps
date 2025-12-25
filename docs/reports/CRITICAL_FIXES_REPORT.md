# 嚴重錯誤修復報告 (Critical Fixes Report)

> **修復時間**: 2025-12-20
> **狀態**: ✅ 已修復

---

## 🚫 發現的問題

從 Log 檔案中發現以下連鎖錯誤：

1. **MP4 格式不支持**
   - 錯誤: `soundfile.LibsndfileError: Format not recognised`
   - 原因: 嘗試直接用 `soundfile` 讀取 `.mp4` 影片檔，但該庫只支持音頻格式。

2. **進度條崩潰 (Crash)**
   - 錯誤: `AttributeError: 'NoneType' object has no attribute 'setValue'`
   - 原因: 轉錄取消或失敗時，`progress_dialog` 可能已被銷毀或為 `None`，但回調函數仍嘗試更新它。

3. **修復引入的新錯誤**
   - 錯誤: `NameError: name 'sip' is not defined`
   - 原因: 嘗試使用 PyQt 的 `sip.isdeleted` 檢測對象，但專案使用的是 PySide6，沒有 `sip` 模組。

---

## ✅ 已實施的修復

### 1. 支援 MP4 影片直接讀取
**文件**: `src/utils/audio_utils.py`

加入了格式檢測同 FFmpeg 自動提取功能：
```python
# 自動檢測影片格式並提取音頻
video_formats = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'}
if file_path.suffix.lower() in video_formats:
    # 調用 FFmpeg 轉換為 .wav
    AudioPreprocessor.extract_audio_from_video(file_path, temp_audio)
```

### 2. 安全的進度條更新
**文件**: `src/ui/main_window.py`

改用 PySide6 兼容的異常處理機制：
```python
if self.progress_dialog:
    try:
        # 嘗試更新進度
        self.progress_dialog.setValue(value)
    except RuntimeError:
        # 如果 C++ 對象已刪除，忽略錯誤 (Python 對象可能還在)
        pass
```

---

## 🔄 建議後續

請重新嘗試轉錄該 MP4 檔案。如果再次遇到問題，請查看新的 Log。
