# 公證流程進行中（第二次嘗試）

## 當前狀態

**進程**: 正在運行
**階段**: Step 1 - 代碼簽名（使用正確的簽名順序）
**進度**: 簽名動態庫和 Frameworks...
**Terminal ID**: 2

## 第一次失敗原因

**Submission ID**: bdc1d1e2-aba0-43ee-8fe4-d4c0794fe9d4
**狀態**: Invalid
**原因**: 簽名無效 - 使用了 `--deep` 選項破壞了 Qt Frameworks 的內部簽名

## 修復方案

已修改簽名策略為正確的從內到外順序：
1. 先簽名所有 .dylib 和 .so 文件（最內層）
2. 簽名所有 Frameworks（不使用 --deep）
3. 簽名主可執行文件
4. 最後簽名整個 .app 包（不使用 --deep）

---

## 公證流程步驟

### Step 1: 代碼簽名 (進行中)
- ✅ 簽名所有 .dylib 文件
- ⏳ 簽名主執行文件
- ⏳ 簽名整個 .app 包
- ⏳ 驗證簽名

### Step 2: 創建 DMG (待執行)
- ⏳ 創建臨時目錄
- ⏳ 複製已簽名的 .app
- ⏳ 創建 DMG
- ⏳ 簽名 DMG

### Step 3: 提交公證 (待執行)
- ⏳ 上傳 DMG 到 Apple
- ⏳ 等待 Apple 審核（5-30 分鐘）
- ⏳ 獲取公證結果

### Step 4: 裝訂公證票據 (待執行)
- ⏳ 裝訂 .app
- ⏳ 重新創建 DMG
- ⏳ 裝訂 DMG
- ⏳ 驗證公證狀態

---

## 預計時間

- **簽名**: 5-10 分鐘
- **創建 DMG**: 1-2 分鐘
- **提交公證**: 1-2 分鐘
- **Apple 審核**: 5-30 分鐘
- **裝訂**: 2-3 分鐘

**總計**: 約 15-50 分鐘

---

## 環境變量

```bash
APPLE_ID="mance1991@icloud.com"
TEAM_ID="678P6T2H5Q"
APP_PASSWORD="xxxg-bmsk-meej-hqkw"
SIGNING_IDENTITY="Developer ID Application: Man Hin Li (678P6T2H5Q)"
```

---

## 監控進度

### 查看實時輸出
進程正在 Terminal ID 24 運行，可以通過以下方式查看進度：

```python
# 在 Python 中
read_process(terminal_id=24, wait=False, max_wait_seconds=10)
```

### 檢查進程狀態
```python
list_processes()
```

---

## 完成後的文件

### 已簽名的文件
```
dist/Canto-beats.app              # 已簽名的 App
dist/Canto-beats-macOS-Notarized.dmg  # 已公證的 DMG
```

### 驗證命令
```bash
# 驗證簽名
codesign -dvv dist/Canto-beats.app

# 驗證公證
xcrun stapler validate dist/Canto-beats-macOS-Notarized.dmg

# 檢查 Gatekeeper
spctl -a -vv -t install dist/Canto-beats-macOS-Notarized.dmg
```

---

## 可能的問題

### 1. 簽名失敗
- **原因**: 證書過期或無效
- **解決**: 檢查證書狀態

### 2. 公證失敗
- **原因**: App 包含不允許的內容
- **解決**: 查看公證日誌

### 3. 網絡超時
- **原因**: 上傳到 Apple 服務器超時
- **解決**: 重新運行公證腳本

---

**開始時間**: 2025-01-XX  
**狀態**: ⏳ 進行中  
**Terminal ID**: 24

