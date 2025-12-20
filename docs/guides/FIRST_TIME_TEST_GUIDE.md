# 首次下載進度框測試指南

## 🎯 目標
測試首次使用時，下載 AI 模型是否會彈出進度對話框。

---

## ✅ 方案 A：安全測試（推薦）

### 步驟 1：備份模型緩存
```bash
cd ~/.cache/huggingface/hub
mv models--mlx-community--whisper-large-v3-mlx models--mlx-community--whisper-large-v3-mlx.backup
```

### 步驟 2：啟動應用程式
```bash
cd /Users/nicleung/Public/Canto-Beats-Apps
venv/bin/python main.py
```

### 步驟 3：測試轉寫
1. 加載一個視頻文件
2. 點擊「開始轉寫」按鈕
3. **應該會看到下載進度對話框**，顯示：
   - 標題：「下載 AI 模型」
   - 進度條
   - 狀態訊息：「AI 工具下載中...」

### 步驟 4：恢復緩存
```bash
cd ~/.cache/huggingface/hub
mv models--mlx-community--whisper-large-v3-mlx.backup models--mlx-community--whisper-large-v3-mlx
```

---

## 🔍 方案 B：檢查代碼邏輯

如果你不想真的測試下載，可以檢查代碼：

### 1. 檢查下載觸發點
```bash
venv/bin/python test_download_trigger.py
```

### 2. 查看關鍵代碼
```bash
# Pipeline 中的下載邏輯
grep -A 20 "ModelDownloadDialog" src/pipeline/subtitle_pipeline_v2.py

# 下載對話框實現
cat src/ui/download_dialog.py | head -100
```

---

## 📊 預期結果

### ✅ 正常情況
1. 檢測到模型未緩存
2. 彈出下載對話框
3. 顯示進度：「AI 工具下載中...」
4. 進度條更新（0% → 100%）
5. 顯示「下載完成」
6. 對話框自動關閉
7. 繼續轉寫流程

### ❌ 異常情況
1. 沒有彈出對話框 → 檢查 `_load_asr()` 邏輯
2. 對話框卡住 → 檢查 Worker 線程
3. 下載失敗 → 檢查網絡連接

---

## 🐛 調試方法

### 查看日誌
```bash
tail -f ~/.canto-beats/logs/canto-beats_*.log
```

### 關鍵日誌訊息
- `MLX Whisper model not cached, showing download dialog...`
- `Model path: mlx-community/whisper-large-v3-mlx`
- `AI 工具下載中...`
- `下載完成`

---

## 🔧 快速恢復命令

如果測試中斷，使用此命令恢復：
```bash
cd ~/.cache/huggingface/hub
if [ -d "models--mlx-community--whisper-large-v3-mlx.backup" ]; then
    rm -rf models--mlx-community--whisper-large-v3-mlx
    mv models--mlx-community--whisper-large-v3-mlx.backup models--mlx-community--whisper-large-v3-mlx
    echo "✅ 緩存已恢復"
fi
```

---

## 💡 提示

- 測試前確保網絡連接正常
- 下載大約需要 3-5 分鐘（取決於網速）
- 可以隨時點擊「取消」中止下載
- 取消後緩存會保持未下載狀態，下次仍會彈出對話框

