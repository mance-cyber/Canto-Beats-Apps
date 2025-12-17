# macOS Silicon (Apple M1/M2/M3) 打包指南

## 🎯 目标
为 Apple Silicon Mac 用户打包完整可用的 Canto-beats.app

---

## 🚀 快速开始 (推荐)

### 一键配置环境
```bash
# 1. 克隆项目
git clone <your-repo-url> canto-beats
cd canto-beats

# 2. 运行自动配置脚本
chmod +x setup_macos_silicon.sh
./setup_macos_silicon.sh

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 运行打包脚本
python build_silicon_macos.py
```

完成！你的 `Canto-beats.app` 将在 `dist/` 目录中。

---

## ⚠️ 前置条件 (手动配置)

### 硬件要求
- Apple Silicon Mac (M1/M2/M3/M4)
- 至少 16GB RAM
- 至少 20GB 可用磁盘空间

### 软件要求
```bash
# 1. 安装 Homebrew (ARM64 版本)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 确认 Homebrew 架构
arch -arm64 brew --version

# 3. 安装系统依赖
arch -arm64 brew install python@3.11 mpv ffmpeg
```

---

## 📦 打包步骤

### Step 1: 克隆项目
```bash
git clone <your-repo-url> canto-beats
cd canto-beats
```

### Step 2: 创建虚拟环境
```bash
# 使用 ARM64 原生 Python
arch -arm64 python3.11 -m venv venv
source venv/bin/activate

# 确认架构
python -c "import platform; print(platform.machine())"
# 应该输出: arm64
```

### Step 3: 安装依赖
```bash
# 升级 pip
pip install --upgrade pip wheel setuptools

# 安装 PyTorch (ARM64 优化版本)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 过滤掉不兼容的依赖
grep -v -E "llama-cpp-python|bitsandbytes" requirements.txt > requirements-macos-silicon.txt

# 安装其他依赖
pip install -r requirements-macos-silicon.txt

# 安装 PyInstaller
pip install pyinstaller

# (可选) 如果需要 llama-cpp-python，从源码编译
CMAKE_ARGS="-DCMAKE_OSX_ARCHITECTURES=arm64" pip install llama-cpp-python --no-cache-dir
```

### Step 4: 验证依赖
```bash
# 测试 PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"

# 测试 Whisper
python -c "import faster_whisper; print('Faster-Whisper: OK')"

# 测试 PySide6
python -c "from PySide6.QtWidgets import QApplication; print('PySide6: OK')"

# 测试 mpv
python -c "import mpv; print('python-mpv: OK')"
```

### Step 5: 构建 .app
```bash
# 使用现有脚本
python build_pyinstaller_macos.py

# 或手动构建
python -m PyInstaller main.py \
  --onedir \
  --windowed \
  --name=Canto-beats \
  --add-data=src:src \
  --add-data=public:public \
  --hidden-import=PySide6.QtCore \
  --hidden-import=torch \
  --hidden-import=faster_whisper \
  --osx-bundle-identifier=com.cantobeats.app \
  --clean \
  --noconfirm
```

### Step 6: 测试 .app
```bash
# 直接运行
open dist/Canto-beats.app

# 或从命令行运行查看日志
dist/Canto-beats.app/Contents/MacOS/Canto-beats
```

### Step 7: 创建 DMG 安装包
```bash
# 创建临时目录
mkdir -p dist/dmg
cp -r dist/Canto-beats.app dist/dmg/

# 创建 DMG
hdiutil create -volname "Canto-beats" \
  -srcfolder dist/dmg \
  -ov -format UDZO \
  dist/Canto-beats-Silicon.dmg

# 清理
rm -rf dist/dmg
```

---

## 🔧 常见问题

### 问题 1: libmpv 找不到
**症状**: `OSError: cannot load library 'libmpv'`

**解决方案**:
```bash
# 确认 libmpv 安装位置
brew list mpv | grep libmpv

# 添加到 PyInstaller 配置
--add-binary="/opt/homebrew/lib/libmpv.dylib:."
```

### 问题 2: PyTorch 架构不匹配
**症状**: `RuntimeError: Incompatible architecture`

**解决方案**:
```bash
# 卸载并重装 ARM64 版本
pip uninstall torch torchaudio
arch -arm64 pip install torch torchaudio
```

### 问题 3: App 无法打开 (代码签名)
**症状**: "App is damaged and can't be opened"

**解决方案**:
```bash
# 移除隔离属性
xattr -cr dist/Canto-beats.app

# 或进行代码签名 (需要 Apple Developer 账号)
codesign --force --deep --sign - dist/Canto-beats.app
```

---

## 📊 预期输出大小

| 组件 | 大小 |
|------|------|
| PySide6 | ~150 MB |
| PyTorch (CPU) | ~200 MB |
| Whisper Models | ~1.5 GB |
| FFmpeg/libmpv | ~50 MB |
| 其他依赖 | ~100 MB |
| **总计** | **~2.0 GB** |

---

## ✅ 验证清单

- [ ] App 可以正常启动
- [ ] 可以拖入视频文件
- [ ] Whisper 转写功能正常
- [ ] 播放器可以播放视频
- [ ] 字幕编辑功能正常
- [ ] 导出 SRT/ASS 正常
- [ ] 无控制台错误输出

---

## 🚀 分发

### 方式 1: 直接分发 .app
```bash
# 压缩
zip -r Canto-beats-Silicon.zip dist/Canto-beats.app

# 上传到 GitHub Releases / Google Drive / 百度网盘
```

### 方式 2: 分发 DMG
```bash
# 已在 Step 7 创建
# 直接分发 dist/Canto-beats-Silicon.dmg
```

### 方式 3: 通过 GitHub Actions 自动构建
- 已有 `.github/workflows/build-macos.yml`
- 推送代码后自动构建
- 从 Actions 页面下载 Artifact

---

## 📝 注意事项

1. **不要在 Rosetta 2 下构建** - 必须使用原生 ARM64 环境
2. **模型文件不打包** - 首次运行时自动下载
3. **代码签名** - 如需 App Store 分发，需要完整签名流程
4. **Gatekeeper** - 用户首次打开需要右键 → 打开

---

## 🔗 相关文件

- `build_pyinstaller_macos.py` - 自动化打包脚本
- `.github/workflows/build-macos.yml` - CI/CD 配置
- `requirements.txt` - Python 依赖列表

