# 🧠 VRAM 管理機制

## ✅ 當前實現

### 每次轉寫開始時的 VRAM 清空流程

```
用戶點擊「開始轉寫」
  ↓
創建新的 TranscribeWorkerV2 (main_window.py:1017)
  ↓
創建新的 SubtitlePipelineV2 (transcription_worker_v2.py:60)
  ↓
調用 pipeline.process() (transcription_worker_v2.py:100)
  ↓
Step 0: Pre-clear GPU memory (subtitle_pipeline_v2.py:515-531)
  ├─ gc.collect()
  ├─ torch.mps.empty_cache() (MPS)
  └─ torch.cuda.empty_cache() (CUDA)
  ↓
開始加載模型和轉寫
```

---

## 📍 VRAM 清空的關鍵位置

### 1. **轉寫開始前** (subtitle_pipeline_v2.py:515-531)
```python
# Step 0: Pre-clear GPU memory (0-5%)
logger.info("Pre-clearing GPU memory before pipeline start...")
gc.collect()
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
    logger.info("MPS memory cache cleared, ready for model loading")
elif torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
```

**觸發時機**: 每次調用 `pipeline.process()` 開始時

### 2. **ASR 模型卸載後** (subtitle_pipeline_v2.py:143-150)
```python
gc.collect()
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
elif torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
logger.info("ASR unloaded, GPU memory freed")
```

**觸發時機**: ASR 轉寫完成，準備加載 LLM 時

### 3. **Pipeline 清理時** (subtitle_pipeline_v2.py:673-683)
```python
try:
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
        logger.info("MPS memory cache cleared")
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
except Exception as e:
    logger.warning(f"GPU cache clear error: {e}")
```

**觸發時機**: Pipeline 完成或取消時

---

## 🔄 完整的 VRAM 生命週期

### 第一次轉寫
```
1. 啟動應用 (VRAM: 0 MB)
2. 點擊「開始轉寫」
3. Pre-clear VRAM (VRAM: 0 MB)
4. 加載 MLX Whisper (VRAM: ~2 GB)
5. 轉寫完成
6. 卸載 ASR + clear VRAM (VRAM: ~0 MB)
7. 加載 Qwen LLM (VRAM: ~6 GB) - 如果啟用
8. LLM 處理完成
9. Pipeline cleanup + clear VRAM (VRAM: ~0 MB)
```

### 第二次轉寫
```
1. 點擊「開始轉寫」
2. Pre-clear VRAM (VRAM: 0 MB) ✅ 清空上次殘留
3. 加載 MLX Whisper (VRAM: ~2 GB)
4. ... (同上)
```

---

## 📊 VRAM 使用峰值

### Apple Silicon (MPS)
- **MLX Whisper large-v3**: ~2 GB
- **Qwen 2.5-3B (fp16)**: ~6 GB
- **峰值**: ~6 GB (不會同時加載)

### 順序加載策略
```
Time ──────────────────────────────────────>
      ┌─────────┐              ┌─────────┐
ASR   │ 2 GB    │              │         │
      └─────────┘              │         │
                 ┌─────────────┤ 6 GB    │
LLM              │             │         │
                 └─────────────┴─────────┘
      ↑         ↑              ↑         ↑
    Load    Unload+Clear    Load      Clear
```

---

## ✅ 驗證方法

### 1. 查看日誌
```bash
tail -f ~/.canto-beats/logs/*.log | grep -i "memory\|cache\|clear"
```

應該看到：
```
INFO: Pre-clearing GPU memory before pipeline start...
INFO: MPS memory cache cleared, ready for model loading
INFO: ASR unloaded, GPU memory freed
INFO: MPS memory cache cleared
INFO: Pipeline cleanup complete
```

### 2. 監控 GPU 使用
```bash
# 使用 Activity Monitor
# 查看 "GPU History" 圖表
```

### 3. 測試多次轉寫
```
1. 轉寫第一個視頻
2. 完成後立即轉寫第二個視頻
3. 檢查是否有 VRAM 累積
```

---

## 🐛 潛在問題

### 問題 1: VRAM 未完全釋放
**症狀**: 多次轉寫後速度變慢

**原因**: 
- Python GC 延遲
- PyTorch 緩存未清空
- 模型引用未釋放

**解決**: 已實現 `gc.collect()` + `torch.mps.empty_cache()`

### 問題 2: 模型重複加載
**症狀**: 每次轉寫都很慢

**原因**: 
- Pipeline 每次都創建新實例
- 模型每次都重新加載

**解決**: 這是設計選擇，確保乾淨狀態

---

## 💡 優化建議

### 當前策略（已實現）✅
- 每次轉寫創建新 pipeline
- 轉寫前清空 VRAM
- 順序加載模型（ASR → LLM）
- 完成後清理

### 可能的優化（未實現）
1. **保持 pipeline 實例**
   - 優點：模型保持加載，更快
   - 缺點：VRAM 持續佔用，可能累積

2. **模型池**
   - 優點：複用已加載模型
   - 缺點：複雜度高，內存管理困難

3. **延遲清理**
   - 優點：連續轉寫更快
   - 缺點：可能 VRAM 不足

---

## 🎯 結論

✅ **當前實現已經很好**：
- 每次轉寫前清空 VRAM
- 順序加載避免峰值
- 完成後徹底清理
- 適合單次轉寫場景

⚠️ **如果需要連續轉寫優化**：
- 可以考慮保持 pipeline 實例
- 但需要更複雜的內存管理

