# Canto-Beats 項目文件架構

## 📊 統計摘要

- **Python 源碼**: 90 個
- **測試文件**: 33 個
- **構建腳本**: 10 個
- **資源文件**: 384 個
- **文檔文件**: 225 個

---

## ✅ 必須打包的文件

### 1. 核心源碼 (src/)

#### UI 模塊 (src/ui/)
- ✅ `main_window.py` - 主窗口
- ✅ `avplayer_widget.py` - AVPlayer 視頻播放器
- ✅ `video_player.py` - 視頻播放器（含 mpv fallback）
- ✅ `timeline_editor.py` - 時間軸編輯器
- ✅ `style_panel.py` - 樣式控制面板
- ✅ `download_dialog.py` - 模型下載對話框
- ✅ `transcription_worker_v2.py` - 轉寫工作線程
- ✅ `notification_system.py` - 通知系統
- ✅ `animated_progress_dialog.py` - 動畫進度對話框
- ✅ `timeline_tracks.py` - 時間軸軌道
- ✅ `timeline_config.py` - 時間軸配置
- ✅ `edit_history.py` - 編輯歷史
- ✅ `splash_screen.py` - 啟動畫面
- ✅ `custom_title_bar.py` - 自定義標題欄
- ✅ `license_dialog.py` - 授權對話框
- ✅ `utils/waveform_renderer.py` - 波形渲染器

#### Models 模塊 (src/models/)
- ✅ `whisper_asr.py` - Whisper 語音識別
- ✅ `qwen_llm.py` - Qwen 語言模型
- ✅ `vad_processor.py` - VAD 語音活動檢測
- ✅ `translation_model.py` - 翻譯模型
- ✅ `model_manager.py` - 模型管理器

#### Pipeline 模塊 (src/pipeline/)
- ✅ `subtitle_pipeline_v2.py` - 字幕生成流程 V2

#### Core 模塊 (src/core/)
- ✅ `config.py` - 配置管理
- ✅ `hardware_detector.py` - 硬件檢測
- ✅ `path_setup.py` - 路徑設置
- ✅ `security.py` - 安全模塊
- ✅ `license_manager.py` - 授權管理

#### Utils 模塊 (src/utils/)
- ✅ `audio_utils.py` - 音頻工具
- ✅ `video_utils.py` - 視頻工具
- ✅ `logger.py` - 日誌工具
- ✅ `avf_thumbnail.py` - AVFoundation 縮略圖

#### Subtitle 模塊 (src/subtitle/)
- ✅ `style_processor.py` - 樣式處理器
- ✅ `subtitle_exporter.py` - 字幕導出器

### 2. 資源文件 (public/)

#### 圖標 (public/icons/)
- ✅ `app_icon.icns` - macOS 應用圖標
- ✅ `app_icon.png` - PNG 圖標

### 3. 字典資源 (src/resources/)
- ✅ `cantonese_mapping.json` - 粵語字典 (1267 條)
- ✅ `english_mapping.json` - 英文字典 (414 條)
- ✅ `profanity_mapping.json` - 粗口字典 (20 條)

### 4. 入口文件
- ✅ `main.py` - 應用入口

---

## ❌ 不需要打包的文件

### 測試文件 (33 個)
```
test*.py
*_test.py
tests/
```

### 調試腳本
```
debug*.py
diagnose*.py
reproduce*.py
check*.py
analyze*.py
```

### 構建腳本
```
build*.py
setup*.py
install*.py
pre_build_check.py
```

### 文檔文件 (225 個)
```
*.md
*.rst
*.pdf
LICENSE
README
```

### 臨時/備份文件
```
*.backup
*.bak
*.tmp
*_old.py
crash_log.txt
debug_log.txt
error_log.txt
```

### 開發工具
```
.git/
.github/
.vscode/
.idea/
__pycache__/
*.pyc
*.pyo
venv/
.env
```

### 示例/演示
```
examples/
demos/
```

### 其他不需要
```
components.json
firebase.json
license_keys.txt
license_server/
debug_thumbs/
.idx/
```

---

## 📦 PyInstaller 配置

### --add-data 參數
```python
"--add-data=src:src",
"--add-data=public:public",
```

### --exclude-module 參數
```python
"--exclude-module=tkinter",
"--exclude-module=matplotlib",
"--exclude-module=jupyter",
"--exclude-module=IPython",
"--exclude-module=pytest",
"--exclude-module=unittest",
```

---

## 🔍 核心模塊依賴圖

```
main.py
  └── ui.main_window
      ├── ui.avplayer_widget (視頻播放)
      ├── ui.timeline_editor (時間軸)
      │   ├── ui.timeline_tracks
      │   └── utils.waveform_renderer
      ├── ui.style_panel (樣式控制)
      ├── ui.transcription_worker_v2 (轉寫)
      │   └── pipeline.subtitle_pipeline_v2
      │       ├── models.whisper_asr
      │       ├── models.vad_processor
      │       └── models.qwen_llm (可選)
      └── subtitle.subtitle_exporter (導出)
```

---

## ✅ 檢查清單

### 核心功能模塊
- [x] UI 主窗口
- [x] 視頻播放器 (AVPlayer)
- [x] 時間軸編輯器
- [x] 字幕生成流程
- [x] Whisper ASR
- [x] VAD 處理
- [x] Qwen LLM
- [x] 樣式處理
- [x] 字幕導出

### 資源文件
- [x] 應用圖標
- [x] 粵語字典
- [x] 英文字典
- [x] 粗口字典

### 系統依賴
- [x] FFmpeg
- [x] ~~libmpv~~ (使用 AVPlayer)

---

## 📝 打包命令

```bash
./build_macos_app.sh
```

這會自動：
1. 檢查所有必需文件
2. 排除測試和調試文件
3. 打包核心功能
4. 生成 .app 文件

