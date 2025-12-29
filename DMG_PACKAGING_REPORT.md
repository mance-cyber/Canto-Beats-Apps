# DMG 打包和公證狀態報告

## 📦 當前狀態

### DMG 文件
- **文件名**: `dist/Canto-beats-Silicon.dmg`
- **大小**: 1304.4 MB
- **創建時間**: 2025-01-XX
- **簽名狀態**: ❌ 未簽名（adhoc）
- **公證狀態**: ❌ 未公證

### App Bundle
- **文件名**: `dist/Canto-beats.app`
- **簽名狀態**: ❌ 臨時簽名（adhoc）
- **Bundle ID**: `com.cantobeats.app`
- **架構**: ARM64 (Apple Silicon)

---

## ⚠️  用戶體驗影響

### 當前狀態（未簽名/未公證）
用戶首次打開時會看到：
```
"Canto-beats.app" 無法打開，因為無法驗證開發者。
```

用戶需要：
1. 右鍵點擊 App
2. 選擇「打開」
3. 在彈出的對話框中再次點擊「打開」

### 簽名後（使用 Developer ID）
用戶首次打開時會看到：
```
"Canto-beats.app" 是從互聯網下載的應用程式。您確定要打開它嗎？
```

用戶只需點擊「打開」即可。

### 公證後（Notarized）
用戶可以直接雙擊打開，**無任何警告**。

---

## 🔐 簽名和公證流程

### 前置要求
1. **Apple Developer 帳號**（$99/年）
2. **Developer ID Application 證書**
3. **App-Specific Password**（用於公證）

### 快速開始

#### 1. 設置環境變量
```bash
export SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your@email.com"
export TEAM_ID="YOUR_TEAM_ID"
export APP_PASSWORD="app-specific-password"
```

#### 2. 運行公證腳本
```bash
python notarize_macos.py
```

這會自動完成：
- ✅ 簽名所有二進制文件
- ✅ 簽名 App Bundle
- ✅ 創建簽名的 DMG
- ✅ 提交到 Apple 公證服務
- ✅ 裝訂公證票據
- ✅ 驗證公證狀態

#### 3. 驗證結果
```bash
python create_dmg_quick.py --check
```

---

## 📋 詳細步驟（手動）

### Step 1: 簽名 App
```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  --entitlements entitlements.plist \
  dist/Canto-beats.app
```

### Step 2: 創建 DMG
```bash
python create_dmg_quick.py
```

### Step 3: 簽名 DMG
```bash
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/Canto-beats-Silicon.dmg
```

### Step 4: 提交公證
```bash
xcrun notarytool submit dist/Canto-beats-Silicon.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait
```

### Step 5: 裝訂公證票據
```bash
xcrun stapler staple dist/Canto-beats.app
xcrun stapler staple dist/Canto-beats-Silicon.dmg
```

### Step 6: 驗證
```bash
xcrun stapler validate dist/Canto-beats-Silicon.dmg
spctl -a -vv -t install dist/Canto-beats-Silicon.dmg
```

---

## 🛠️  可用工具

### 1. 快速創建 DMG
```bash
python create_dmg_quick.py
```

### 2. 檢查簽名狀態
```bash
python create_dmg_quick.py --check
```

### 3. 完整打包（含 DMG）
```bash
python build_silicon_macos.py --auto-dmg
```

### 4. 僅創建 DMG（跳過構建）
```bash
python build_silicon_macos.py --dmg-only
```

### 5. 完整公證流程
```bash
python notarize_macos.py
```

### 6. 僅簽名（不公證）
```bash
python notarize_macos.py --sign-only
```

---

## 📊 文件對比

```
┌─────────────────────────────┬──────────┬──────────┬──────────┐
│          文件               │  簽名    │  公證    │ 用戶體驗 │
├─────────────────────────────┼──────────┼──────────┼──────────┤
│ Canto-beats.app (當前)      │ ❌ adhoc │ ❌ 無    │ ⚠️  警告  │
│ Canto-beats-Silicon.dmg     │ ❌ 無    │ ❌ 無    │ ⚠️  警告  │
│ (當前)                      │          │          │          │
├─────────────────────────────┼──────────┼──────────┼──────────┤
│ 簽名後                      │ ✅ Dev ID│ ❌ 無    │ ⚠️  輕微  │
├─────────────────────────────┼──────────┼──────────┼──────────┤
│ 公證後                      │ ✅ Dev ID│ ✅ 已公證│ ✅ 無警告 │
└─────────────────────────────┴──────────┴──────────┴──────────┘
```

---

## 💡 建議

### 開發測試階段
- ✅ 使用當前未簽名版本
- ✅ 通過「右鍵 > 打開」繞過 Gatekeeper
- ✅ 節省 Apple Developer 費用

### 公開分發階段
- ⚠️  **強烈建議**簽名和公證
- ⚠️  提升用戶信任度
- ⚠️  避免用戶困惑和支持請求

### 企業內部分發
- ✅ 簽名即可（可選公證）
- ✅ 提供安裝指南
- ✅ IT 部門可以預先批准

---

## 🔗 相關文檔

- `notarize_macos.py` - 自動化公證腳本
- `create_dmg_quick.py` - 快速 DMG 創建工具
- `build_silicon_macos.py` - 完整打包腳本
- `entitlements.plist` - App 權限配置
- `docs/guides/MACOS_NOTARIZATION_GUIDE.md` - 詳細公證指南

---

## ✅ 總結

### 當前狀態
- ✅ DMG 已創建: `dist/Canto-beats-Silicon.dmg` (1304.4 MB)
- ❌ 未簽名和公證
- ⚠️  用戶需要手動繞過 Gatekeeper

### 下一步
1. **測試 DMG**: `open dist/Canto-beats-Silicon.dmg`
2. **（可選）簽名和公證**: `python notarize_macos.py`
3. **分發**: 上傳到 GitHub Releases 或其他平台

---

**創建日期**: 2025-01-XX  
**工具版本**: v1.0  
**狀態**: ✅ DMG 已創建，等待簽名/公證

