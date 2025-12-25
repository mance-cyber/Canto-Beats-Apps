# DMG 打包完成 - 快速參考

## ✅ 已完成

### 1. DMG 文件已創建
```
文件: dist/Canto-beats-Silicon.dmg
大小: 1304.4 MB
狀態: ✅ 可用（未簽名）
```

### 2. 測試命令
```bash
open dist/Canto-beats-Silicon.dmg
```

### 3. 用戶安裝步驟
1. 雙擊 `Canto-beats-Silicon.dmg`
2. 將 `Canto-beats.app` 拖到 `Applications` 文件夾
3. 首次打開：右鍵 > 打開（繞過 Gatekeeper）

---

## ⚠️  簽名和公證狀態

### 當前狀態
- **App 簽名**: ❌ adhoc（臨時簽名）
- **DMG 簽名**: ❌ 未簽名
- **公證狀態**: ❌ 未公證

### 用戶影響
用戶首次打開時會看到安全警告，需要：
1. 右鍵點擊 App
2. 選擇「打開」
3. 確認打開

---

## 🔐 如何簽名和公證

### 前置要求
- Apple Developer 帳號（$99/年）
- Developer ID Application 證書
- App-Specific Password

### 一鍵公證
```bash
# 設置環境變量
export SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your@email.com"
export TEAM_ID="YOUR_TEAM_ID"
export APP_PASSWORD="app-specific-password"

# 運行公證腳本
python notarize_macos.py
```

### 驗證公證狀態
```bash
python create_dmg_quick.py --check
```

---

## 📦 可用工具

| 工具 | 用途 | 命令 |
|------|------|------|
| `create_dmg_quick.py` | 快速創建 DMG | `python create_dmg_quick.py` |
| `create_dmg_quick.py --check` | 檢查簽名狀態 | `python create_dmg_quick.py --check` |
| `build_silicon_macos.py --dmg-only` | 僅創建 DMG | `python build_silicon_macos.py --dmg-only` |
| `notarize_macos.py` | 完整公證流程 | `python notarize_macos.py` |

---

## 📋 文件清單

```
dist/
├── Canto-beats.app              # App Bundle（1.3 GB）
└── Canto-beats-Silicon.dmg      # DMG 安裝包（1.3 GB）
```

---

## 🎯 下一步

### 選項 A: 直接分發（開發測試）
```bash
# 上傳到 GitHub Releases
gh release create v1.0.0 dist/Canto-beats-Silicon.dmg

# 或使用其他平台
# - Google Drive
# - Dropbox
# - 自建服務器
```

### 選項 B: 簽名後分發（推薦）
```bash
# 1. 簽名和公證
python notarize_macos.py

# 2. 驗證
python create_dmg_quick.py --check

# 3. 分發
gh release create v1.0.0 dist/Canto-beats-Silicon.dmg
```

---

## 💡 提示

### 開發階段
- ✅ 使用未簽名版本節省成本
- ✅ 團隊內部測試無需公證
- ✅ 提供安裝指南給測試用戶

### 公開發布
- ⚠️  **強烈建議**簽名和公證
- ⚠️  提升用戶信任度
- ⚠️  減少支持請求

---

## 📞 支持

如遇問題，請查看：
- `DMG_PACKAGING_REPORT.md` - 詳細報告
- `docs/guides/MACOS_NOTARIZATION_GUIDE.md` - 公證指南
- `docs/technical/MACOS_TECHNICAL_NOTES.md` - 技術細節

---

**狀態**: ✅ DMG 已創建並測試  
**日期**: 2025-01-XX  
**下一步**: 測試安裝或進行簽名/公證

