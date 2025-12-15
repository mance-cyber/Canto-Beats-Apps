# Canto-beats 安裝程式方案

## 📦 安裝程式架構

```
Canto-beats-Installer/
├── python/                    # 完整 Python 環境
│   ├── python.exe
│   ├── pythonw.exe
│   └── Lib/site-packages/     # 所有依賴
├── app/                       # 應用程式檔案
│   ├── main.py
│   ├── src/
│   └── public/
├── models/                    # AI 模型（用戶首次運行時下載）
├── Canto-beats.exe           # 啟動器（很小）
└── uninstall.exe             # 解除安裝程式
```

## ✅ 優點

1. **成功率 90%+** - 不需要打包成單一 exe
2. **維護簡單** - 可以單獨更新 Python 或應用程式
3. **兼容性好** - 避免了各種打包工具的問題
4. **專業外觀** - 有完整的安裝/解除安裝流程

## 🔧 實現步驟

### 步驟 1：創建啟動器 (launcher.py → launcher.exe)
一個小型 exe 只負責啟動 Python 環境

### 步驟 2：導出 Python 環境
使用 pip freeze 導出依賴

### 步驟 3：創建 Inno Setup 腳本
定義安裝流程

### 步驟 4：編譯安裝程式
生成最終的 Setup.exe
