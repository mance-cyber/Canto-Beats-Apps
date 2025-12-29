# macOS Silicon 快速打包指南

## 🎯 一句话总结
在 Apple Silicon Mac 上，3 条命令完成打包。

---

## ⚡ 快速开始

```bash
# 1. 配置环境 (首次运行，约 10 分钟)
chmod +x setup_macos_silicon.sh && ./setup_macos_silicon.sh

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 打包 (约 15 分钟)
python build_silicon_macos.py
```

**完成！** 你的 App 在 `dist/Canto-beats.app`

---

## 📦 分发给用户

### 方式 1: 直接分发 .app (简单)
```bash
# 压缩
zip -r Canto-beats-Silicon.zip dist/Canto-beats.app

# 上传到网盘或 GitHub Releases
```

用户下载后：
1. 解压
2. 右键点击 `Canto-beats.app` → 打开
3. 点击"打开"确认

### 方式 2: 创建 DMG (专业)
```bash
# 在打包脚本中选择 "y" 创建 DMG
# 或手动创建：
hdiutil create -volname "Canto-beats" \
  -srcfolder dist/Canto-beats.app \
  -ov -format UDZO \
  dist/Canto-beats-Silicon.dmg
```

用户下载后：
1. 双击 DMG
2. 拖动 App 到 Applications 文件夹
3. 打开 Applications，右键 → 打开

---

## ⚠️ 常见问题

### Q: "App 已损坏，无法打开"
**A**: 运行以下命令移除隔离属性：
```bash
xattr -cr /Applications/Canto-beats.app
```

### Q: 打包失败，提示找不到 libmpv
**A**: 确保已安装 Homebrew 和 mpv：
```bash
brew install mpv
```

### Q: 打包后 App 很大 (>2GB)
**A**: 正常，包含了：
- PyTorch (~200MB)
- Whisper 模型 (~1.5GB)
- PySide6 (~150MB)
- 其他依赖 (~150MB)

### Q: 可以在 Intel Mac 上运行吗？
**A**: 不行，这是 ARM64 专用版本。Intel Mac 需要单独打包。

---

## 📊 系统要求

### 开发环境 (打包用)
- Apple Silicon Mac (M1/M2/M3/M4)
- macOS 12.0+
- 16GB+ RAM
- 20GB+ 可用空间

### 用户环境 (运行用)
- Apple Silicon Mac
- macOS 12.0+
- 8GB+ RAM
- 5GB+ 可用空间

---

## 🔗 详细文档

- **完整指南**: `MACOS_SILICON_BUILD_GUIDE.md`
- **技术细节**: `MACOS_TECHNICAL_NOTES.md`
- **自动化脚本**: `build_silicon_macos.py`
- **环境配置**: `setup_macos_silicon.sh`

---

## 💡 提示

1. **首次打包** - 需要下载依赖，约 30 分钟
2. **后续打包** - 只需 10-15 分钟
3. **测试 App** - 打包后务必测试所有功能
4. **分发前** - 在不同 Mac 上测试兼容性

---

## 🎉 成功标志

打包成功后，你应该看到：
```
✅ 构建成功!
输出: dist/Canto-beats.app
✅ DMG 创建成功: dist/Canto-beats-Silicon.dmg

🎉 打包完成!

测试命令:
  open dist/Canto-beats.app

分发文件:
  dist/Canto-beats-Silicon.dmg
```

---

## 📞 需要帮助？

1. 查看 `MACOS_TECHNICAL_NOTES.md` 的常见问题章节
2. 检查 `build/` 目录下的构建日志
3. 在 GitHub Issues 提问

