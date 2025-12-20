# macOS Silicon 打包技术说明

## 🏗️ 架构概览

### 核心挑战
1. **ARM64 原生支持** - 所有依赖必须是 ARM64 原生或通用二进制
2. **动态库依赖** - libmpv、FFmpeg 等系统库的路径处理
3. **PyTorch 优化** - 使用 Apple Silicon 优化的 PyTorch 版本
4. **代码签名** - macOS Gatekeeper 和公证要求

---

## 📦 依赖分析

### Python 依赖 (requirements.txt)

| 依赖 | ARM64 支持 | 说明 |
|------|-----------|------|
| PySide6 | ✅ 原生 | Qt6 完整支持 ARM64 |
| torch | ✅ 原生 | 使用 CPU 版本，Apple 优化 |
| faster-whisper | ✅ 原生 | 基于 CTranslate2，支持 ARM64 |
| transformers | ✅ 原生 | Hugging Face，纯 Python |
| llama-cpp-python | ⚠️ 需编译 | 需要从源码编译 ARM64 版本 |
| bitsandbytes | ❌ 不支持 | 仅支持 CUDA，macOS 不可用 |

### 系统依赖 (Homebrew)

| 依赖 | 用途 | 打包方式 |
|------|------|---------|
| libmpv | 视频播放核心 | 通过 `--add-binary` 打包 |
| ffmpeg | 音频提取、缩略图 | 通过 `--add-binary` 打包 |
| ffprobe | 视频信息读取 | 通过 `--add-binary` 打包 |

---

## 🔧 PyInstaller 配置详解

### 关键参数

```python
--target-arch=arm64          # 强制 ARM64 架构
--osx-bundle-identifier      # App Bundle ID
--windowed                   # GUI 应用，无终端窗口
--onedir                     # 目录模式，便于调试
```

### 隐藏导入 (Hidden Imports)

PyInstaller 无法自动检测的模块：
- `torch` - PyTorch 动态加载
- `faster_whisper` - CTranslate2 后端
- `transformers` - Hugging Face 模型
- `silero_vad` - VAD 模型
- `sentencepiece` - 分词器

### 数据文件 (Data Files)

```python
--add-data=src:src           # 源代码目录
--add-data=public:public     # 资源文件 (图标、样式)
--add-binary=libmpv.dylib:.  # 动态库
```

---

## 🐛 常见问题与解决方案

### 1. Rosetta 2 兼容性问题

**问题**: 在 Rosetta 2 下构建的 App 可能在原生 ARM64 环境下崩溃

**解决方案**:
```bash
# 确认当前架构
python -c "import platform; print(platform.machine())"

# 如果输出 x86_64，需要重新安装 ARM64 Python
arch -arm64 brew install python@3.11
```

### 2. libmpv 找不到

**问题**: `OSError: cannot load library 'libmpv'`

**解决方案**:
```python
# 在 build_silicon_macos.py 中自动处理
libmpv_path = subprocess.run(['brew', '--prefix', 'mpv'], 
                            capture_output=True, text=True).stdout.strip()
libmpv_path += '/lib/libmpv.dylib'
```

### 3. PyTorch 导入失败

**问题**: `ImportError: cannot import name '_C' from 'torch'`

**解决方案**:
```bash
# 卸载并重装 ARM64 版本
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. App 被 Gatekeeper 阻止

**问题**: "App is damaged and can't be opened"

**解决方案**:
```bash
# 方案 1: 移除隔离属性 (已在脚本中自动执行)
xattr -cr dist/Canto-beats.app

# 方案 2: 临时代码签名
codesign --force --deep --sign - dist/Canto-beats.app

# 方案 3: 完整签名 (需要 Apple Developer 账号)
codesign --force --deep --sign "Developer ID Application: Your Name" \
  --options runtime dist/Canto-beats.app
```

---

## 📊 性能优化

### PyTorch CPU 优化

Apple Silicon 的 PyTorch 使用 Accelerate 框架优化：
```python
import torch
torch.set_num_threads(4)  # 根据 CPU 核心数调整
```

### 模型加载优化

```python
# 使用 mmap 加载大模型
model = WhisperModel("large-v3", device="cpu", 
                     compute_type="int8",
                     cpu_threads=4)
```

---

## 🔐 代码签名与公证

### 开发者签名 (Developer ID)

```bash
# 1. 签名 App
codesign --force --deep \
  --sign "Developer ID Application: Your Name" \
  --options runtime \
  --entitlements entitlements.plist \
  dist/Canto-beats.app

# 2. 创建 DMG
hdiutil create -volname "Canto-beats" \
  -srcfolder dist/Canto-beats.app \
  -ov -format UDZO \
  dist/Canto-beats.dmg

# 3. 签名 DMG
codesign --force --sign "Developer ID Application: Your Name" \
  dist/Canto-beats.dmg

# 4. 公证 (Notarization)
xcrun notarytool submit dist/Canto-beats.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait

# 5. 装订公证票据
xcrun stapler staple dist/Canto-beats.dmg
```

### entitlements.plist 示例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

---

## 📁 打包产物结构

```
dist/
└── Canto-beats.app/
    └── Contents/
        ├── MacOS/
        │   └── Canto-beats          # 主可执行文件
        ├── Resources/
        │   ├── src/                 # Python 源码
        │   ├── public/              # 资源文件
        │   └── libmpv.dylib         # 动态库
        ├── Frameworks/              # Python 运行时
        └── Info.plist               # App 元数据
```

---

## 🧪 测试清单

### 功能测试
- [ ] App 可以正常启动
- [ ] 拖入视频文件正常识别
- [ ] Whisper 转写功能正常
- [ ] 播放器可以播放视频
- [ ] 字幕编辑功能正常
- [ ] 导出 SRT/ASS 正常

### 兼容性测试
- [ ] M1 Mac 测试
- [ ] M2 Mac 测试
- [ ] M3 Mac 测试
- [ ] macOS 12 (Monterey) 测试
- [ ] macOS 13 (Ventura) 测试
- [ ] macOS 14 (Sonoma) 测试

### 性能测试
- [ ] 启动时间 < 5 秒
- [ ] 内存占用 < 2GB (空闲)
- [ ] CPU 占用 < 50% (转写时)
- [ ] 播放 4K 视频流畅

---

## 📚 参考资源

- [PyInstaller macOS 文档](https://pyinstaller.org/en/stable/usage.html#macos-specific-options)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [PyTorch macOS 安装](https://pytorch.org/get-started/locally/)
- [Homebrew ARM64 支持](https://docs.brew.sh/Installation)

