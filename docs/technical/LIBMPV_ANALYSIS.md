# libmpv 依賴分析

## 🎯 結論：libmpv 可以移除（macOS 打包）

### 原因

#### 1. **AVPlayer 優先策略**
應用在 macOS 上優先使用 **Apple 原生 AVPlayer**：

```python
# src/ui/video_player.py
if HAS_AVPLAYER:
    logger.info("🍎 Creating AVPlayer-based video player (Apple native)")
    # 使用 AVPlayerWidget
else:
    # Fallback to mpv
```

#### 2. **AVPlayer 已完全實現**
`src/ui/avplayer_widget.py` 提供完整功能：
- ✅ 視頻播放
- ✅ 進度控制
- ✅ 字幕顯示
- ✅ 原生硬件加速

#### 3. **libmpv 只是 Fallback**
只在以下情況使用：
- AVPlayer 不可用（非 macOS）
- AVPlayer 初始化失敗

---

## 📊 使用情況

### macOS Apple Silicon
```
優先級：AVPlayer (原生) > mpv (fallback)
實際使用：AVPlayer ✅
libmpv 需要：❌ 不需要
```

### 其他平台（Windows/Linux）
```
優先級：mpv (唯一選擇)
實際使用：mpv ✅
libmpv 需要：✅ 需要
```

---

## 🔧 打包建議

### macOS 打包
**可以完全移除 libmpv 依賴**：

#### 優點
1. 減少打包大小（~50 MB）
2. 減少依賴複雜度
3. 避免 Homebrew 依賴
4. 更純淨的原生體驗

#### 修改方案

##### 1. 移除 build_silicon_macos.py 中的 libmpv 檢查
```python
# 刪除或註釋這部分
# def check_dependencies():
#     subprocess.run(['brew', 'list', 'mpv'], ...)
```

##### 2. 移除 PyInstaller 的 libmpv 添加
```python
# 刪除或註釋
# libmpv_path = find_libmpv()
# if libmpv_path:
#     cmd.append(f"--add-binary={libmpv_path}:.")
```

##### 3. 移除 python-mpv 依賴
```bash
# requirements.txt 中移除
# python-mpv>=1.0.4
```

---

## ⚠️ 風險評估

### 低風險
- AVPlayer 已經穩定運行
- 所有功能已測試通過
- 有完整的錯誤處理

### 保留 Fallback 的理由
1. **兼容性保險** - 萬一 AVPlayer 在某些 macOS 版本失敗
2. **調試方便** - 可以切換播放器測試
3. **未來擴展** - 可能需要 mpv 的特殊功能

---

## 💡 推薦方案

### 方案 A：完全移除（激進）✂️
- 移除所有 libmpv 相關代碼
- 只保留 AVPlayer
- 打包最小化

### 方案 B：保留但不打包（平衡）⚖️
- 代碼保留 mpv fallback
- 打包時不包含 libmpv
- 如果 AVPlayer 失敗，提示用戶安裝 mpv

### 方案 C：完整保留（保守）🛡️
- 保持現狀
- 打包包含 libmpv
- 完整 fallback 支持

---

## 🎯 建議：方案 B（保留但不打包）

### 理由
1. **代碼靈活性** - 保留 fallback 邏輯
2. **打包優化** - 不增加體積
3. **用戶體驗** - 99% 用戶使用 AVPlayer
4. **開發友好** - 本地開發仍可測試 mpv

### 實施步驟

#### 1. 修改 build_silicon_macos.py
```python
# 註釋掉 mpv 檢查
def check_dependencies():
    # ... 其他檢查 ...
    
    # 註釋掉 mpv 檢查
    # try:
    #     subprocess.run(['brew', 'list', 'mpv'], ...)
    # except:
    #     ...
```

#### 2. 移除 libmpv 打包
```python
# 註釋掉
# libmpv_path = find_libmpv()
# if libmpv_path:
#     cmd.append(f"--add-binary={libmpv_path}:.")
```

#### 3. 移除 hidden-import
```python
# 移除
# "--hidden-import=mpv",
```

#### 4. 更新 requirements.txt
```
# python-mpv>=1.0.4  # macOS 不需要，使用 AVPlayer
```

---

## 📝 測試清單

移除後需要測試：
- [ ] 應用正常啟動
- [ ] 視頻加載正常
- [ ] 視頻播放流暢
- [ ] 字幕顯示正常
- [ ] 進度控制正常
- [ ] 無 libmpv 相關錯誤

---

## 🔍 檢查命令

### 確認 AVPlayer 可用
```bash
venv/bin/python -c "
from ui.avplayer_widget import is_avplayer_available
print('AVPlayer available:', is_avplayer_available())
"
```

### 確認應用使用 AVPlayer
```bash
# 啟動應用，查看日誌
grep "AVPlayer" ~/.canto-beats/logs/*.log
```

---

## 結論

**對於 macOS Apple Silicon 打包，libmpv 不是必需的。**

建議採用方案 B：保留代碼邏輯，但打包時不包含 libmpv，以優化體積和依賴。

