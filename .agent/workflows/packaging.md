---
description: How to package Canto-Beats into a standalone macOS App
---

# Canto-Beats macOS 打包工作流程

## 前置要求

// turbo
```bash
# 安裝 Homebrew (如未安裝)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安裝 FFmpeg
brew install ffmpeg

# 安裝打包工具
pip install pyinstaller cryptography
```

## 一鍵構建

### 開發測試版（無簽名）
// turbo
```bash
python build_silicon_macos.py --auto-dmg
```

### 發佈版（需簽名）
```bash
python build_silicon_macos.py --auto-dmg
python notarize_macos.py
```

## 輸出位置
- **App**: `dist/Canto-beats.app`
- **DMG**: `dist/Canto-beats-Silicon.dmg`

## 測試打包後的 App
// turbo
```bash
# 測試 App 是否正常啟動
open dist/Canto-beats.app

# 查看啟動日誌（出錯時）
/dist/Canto-beats.app/Contents/MacOS/Canto-beats
```

## 常見問題

### 1. MLX 相關錯誤
- **症狀**: `Failed to load metallib`
- **解決**: 確保 `rthooks/rthook_mlx.py` 存在且正確設置路徑

### 2. 模組缺失
- **症狀**: `ModuleNotFoundError: No module named 'xxx'`
- **解決**: 在 `build_silicon_macos.py` 添加 `--hidden-import=xxx` 或 `--collect-all=xxx`

### 3. 資源路徑錯誤
- **症狀**: 找不到圖標、字體等資源
- **解決**: 檢查 `src/core/path_setup.py` 中的 `get_resource_path()` 函數

## 已包含的關鍵依賴

| 類別 | 套件 |
|------|------|
| AI/ML | mlx, mlx_whisper, mlx_lm, transformers, tokenizers |
| 介面 | PySide6 (含 Multimedia, Network, Svg) |
| 音視頻 | ffmpeg (系統), soundfile, pydub |
| 中文處理 | opencc, pysrt |
| 模型下載 | huggingface_hub, safetensors |
| macOS | objc, Foundation, AppKit, AVFoundation, Quartz |
