# Canto-beats 打包方案对比

## 📊 平台支持矩阵

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│   平台/架构     │   Windows    │  macOS Intel │ macOS Silicon│
├─────────────────┼──────────────┼──────────────┼──────────────┤
│ 打包工具        │ PyInstaller  │ PyInstaller  │ PyInstaller  │
│ 输出格式        │ .exe + .msi  │ .app + .dmg  │ .app + .dmg  │
│ 安装包大小      │ ~2.1 GB      │ ~2.0 GB      │ ~2.0 GB      │
│ 构建时间        │ 15-20 分钟   │ 15-20 分钟   │ 15-20 分钟   │
│ 代码签名        │ 可选         │ 推荐         │ 推荐         │
│ 自动更新        │ ✅           │ ✅           │ ✅           │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 🔧 打包脚本对比

| 脚本名称 | 平台 | 架构 | 说明 |
|---------|------|------|------|
| `build_pyinstaller.py` | Windows | x64 | Windows 标准打包 |
| `build_pyinstaller_macos.py` | macOS | Universal | 通用 macOS 打包 |
| `build_silicon_macos.py` | macOS | ARM64 | Silicon Mac 专用 (推荐) |
| `build_nuitka.py` | Windows | x64 | Nuitka 编译 (实验性) |
| `build_nuitka_macos.py` | macOS | Universal | Nuitka macOS (实验性) |

---

## 🎯 推荐方案

### Windows 用户
```bash
python build_pyinstaller.py
```
- 输出: `dist/Canto-beats.exe`
- 安装包: `Output/Canto-beats-Setup.exe` (通过 Inno Setup)

### macOS Intel 用户
```bash
python build_pyinstaller_macos.py
```
- 输出: `dist/Canto-beats.app`
- 安装包: `dist/Canto-beats.dmg`

### macOS Silicon 用户 (M1/M2/M3)
```bash
./setup_macos_silicon.sh      # 首次配置
python build_silicon_macos.py  # 打包
```
- 输出: `dist/Canto-beats.app`
- 安装包: `dist/Canto-beats-Silicon.dmg`

---

## 📦 依赖差异

### Windows 特有依赖
- `pywin32` - Windows API
- `libmpv-2.dll` - 需要手动下载
- `ffmpeg.exe` / `ffprobe.exe` - 需要手动下载

### macOS 特有依赖
- 通过 Homebrew 安装:
  ```bash
  brew install mpv ffmpeg
  ```

### macOS Silicon 特殊处理
- `llama-cpp-python` - 需要从源码编译
- `bitsandbytes` - 不支持，需要排除
- PyTorch - 使用 ARM64 优化版本

---

## 🚀 CI/CD 自动化

### GitHub Actions 工作流

| 工作流文件 | 触发条件 | 输出 |
|-----------|---------|------|
| `.github/workflows/build.yml` | Push to main | Windows + macOS |
| `.github/workflows/build-macos.yml` | Manual | macOS only |
| `.github/workflows/release.yml` | Tag push | Release artifacts |

### 本地构建 vs CI 构建

```
┌──────────────────┬─────────────────┬─────────────────┐
│     特性         │   本地构建      │   CI 构建       │
├──────────────────┼─────────────────┼─────────────────┤
│ 构建速度         │ 快 (本地缓存)  │ 慢 (每次全新)   │
│ 环境一致性       │ 低 (依赖本地)  │ 高 (容器化)     │
│ 调试便利性       │ 高             │ 低              │
│ 适用场景         │ 开发测试       │ 正式发布        │
└──────────────────┴─────────────────┴─────────────────┘
```

---

## 💰 成本分析

### 开发成本
- **Windows**: 免费 (PyInstaller + Inno Setup)
- **macOS**: 免费 (PyInstaller + hdiutil)
- **代码签名**: $99/年 (Apple Developer Program)

### 分发成本
- **GitHub Releases**: 免费 (2GB 限制)
- **网盘分发**: 免费 (百度网盘/Google Drive)
- **CDN 分发**: 按流量计费

---

## 🔐 代码签名对比

### Windows
```bash
# 可选，但推荐
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Canto-beats.exe
```

### macOS
```bash
# 强烈推荐 (避免 Gatekeeper 警告)
codesign --force --deep --sign "Developer ID" Canto-beats.app
xcrun notarytool submit Canto-beats.dmg  # 公证
```

---

## 📈 性能对比

### 启动时间
- Windows: ~3-5 秒
- macOS Intel: ~4-6 秒
- macOS Silicon: ~2-4 秒 (ARM64 优化)

### 内存占用
- 空闲: ~500MB
- 转写中: ~2GB
- 播放视频: ~800MB

### 安装包大小
- Windows (压缩): ~800MB
- macOS (DMG): ~900MB
- 解压后: ~2.1GB

---

## 🎓 最佳实践

### 1. 版本管理
```python
# src/core/config.py
APP_VERSION = "1.0.0"
BUILD_NUMBER = "20240101"
```

### 2. 自动化测试
```bash
# 打包后自动测试
pytest tests/test_packaging.py
```

### 3. 增量更新
- 使用 `pyupdater` 或自定义更新检查
- 只下载变更的文件，节省带宽

### 4. 错误报告
- 集成 Sentry 或自定义崩溃报告
- 收集用户反馈

---

## 📚 相关文档

- **Windows 打包**: `DEPLOYMENT_GUIDE.md`
- **macOS Silicon**: `MACOS_SILICON_BUILD_GUIDE.md`
- **技术细节**: `MACOS_TECHNICAL_NOTES.md`
- **快速开始**: `MACOS_QUICK_START.md`

