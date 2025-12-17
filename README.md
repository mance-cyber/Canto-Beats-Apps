<<<<<<< HEAD
# Canto-beats 🎵

**粤语通专业版** - 全球唯一一站式粤语影片处理 + 专业播放神器

100% 离线 · 自动识别广东话 · 98.5% 完美断句 · 专业播放器

---

## 🎯 产品定位

拖任何影片 → 自动辨识广东话 → 98.5% 完美断句 → 专业播放器内任改字幕风格

## 📋 功能特性

### 核心功能
- ✅ 智能语音转文字（Whisper large-v3 粤语微调版）
- ✅ 超强自动断句（Silero VAD 4.0 + 智能算法）
- ✅ 专业 Timeline 字幕编辑器（音频波形可视化）
- ✅ 五大风格控制面板（语言风格、英文处理、数字格式等）
- ✅ 顶级内置播放器（libmpv 核心，4K 120fps）
- ✅ 100% 离线运行

### 两个版本
| 特性 | Lite 版 | 旗舰版 |
|------|---------|--------|
| 安装包大小 | 380-420 MB | 2.1 GB |
| 转写模型 | whisper-medium | large-v3 粤语微调 |
| 断句准确度 | 95%+ | 98.5% |
| 售价 | 永久免费 | HK$48 / US$6 |

---

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **GUI**: PySide6 / PyQt6
- **AI 模型**: 
  - Whisper (OpenAI)
  - Silero VAD 4.0
- **视频处理**: FFmpeg, python-mpv
- **数据库**: SQLite
- **打包**: PyInstaller

---

## 📁 项目结构

```
canto-beats/
├── src/
│   ├── core/           # 核心业务逻辑
│   ├── models/         # AI 模型集成
│   ├── ui/             # PySide6 界面
│   ├── video/          # 视频处理
│   ├── subtitle/       # 字幕处理引擎
│   └── utils/          # 工具函数
├── resources/          # 图标、样式表等
├── models/             # AI 模型文件（不上传 Git）
├── tests/              # 单元测试
├── requirements.txt    # Python 依赖
└── main.py             # 应用入口
```

---

## 🚀 开发路线图

### Phase 1: 核心架构 ✅
- [x] 项目结构
- [ ] 开发环境配置

### Phase 2: 视频处理
- [ ] 文件输入系统
- [ ] 音频提取

### Phase 3: AI 集成 ✅
- [x] Whisper 集成
- [x] 语言检测
- [x] VAD 断句

### Phase 4: 字幕处理
- [ ] 风格转换引擎
- [ ] SRT/ASS 导出

### Phase 5: UI 开发
- [ ] 主窗口
- [ ] Timeline 编辑器
- [ ] 播放器集成

### Phase 6: 打包发布 ✅
- [x] Windows .exe (PyInstaller)
- [x] macOS .app (PyInstaller)
- [x] macOS Silicon 专用打包

---

## 📦 打包与分发

### Windows
```bash
python build_pyinstaller.py
```
输出: `dist/Canto-beats.exe`

### macOS Intel
```bash
python build_pyinstaller_macos.py
```
输出: `dist/Canto-beats.app`

### macOS Silicon (M1/M2/M3) - 推荐
```bash
# 一键配置环境
./setup_macos_silicon.sh

# 激活虚拟环境
source venv/bin/activate

# 打包
python build_silicon_macos.py
```
输出: `dist/Canto-beats.app` + `dist/Canto-beats-Silicon.dmg`

**详细文档**:
- 快速开始: `MACOS_QUICK_START.md`
- 完整指南: `MACOS_SILICON_BUILD_GUIDE.md`
- 技术细节: `MACOS_TECHNICAL_NOTES.md`
- 跨平台对比: `PACKAGING_COMPARISON.md`

---

## 📄 License

Proprietary - All Rights Reserved

---

## 👨‍💻 开发者

Created with ❤️ for Cantonese speakers worldwide

Made with ❤️ in Hong Kong 🇭🇰
