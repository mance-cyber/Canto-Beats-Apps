# macOS Silicon 打包文件索引

## 📁 核心文件

### 打包脚本
```
build_silicon_macos.py          # Silicon Mac 专用打包脚本 (主要)
build_pyinstaller_macos.py      # 通用 macOS 打包脚本
build_nuitka_macos.py           # Nuitka 编译脚本 (实验性)
setup_macos_silicon.sh          # 一键环境配置脚本
```

### 文档
```
MACOS_QUICK_START.md            # 快速开始 (3 条命令)
MACOS_SILICON_BUILD_GUIDE.md    # 完整打包指南
MACOS_TECHNICAL_NOTES.md        # 技术细节文档
MACOS_SILICON_SUMMARY.md        # 方案总结
MACOS_FILES_INDEX.md            # 本文件索引
PACKAGING_COMPARISON.md         # 跨平台对比
```

### 配置文件
```
requirements.txt                # Python 依赖 (通用)
requirements-macos-silicon.txt  # macOS Silicon 依赖 (自动生成)
.github/workflows/build-macos.yml  # CI/CD 配置
```

---

## 📊 文件关系图

```
用户入口
  ├─ MACOS_QUICK_START.md ────────> 快速开始
  │
  ├─ setup_macos_silicon.sh ──────> 环境配置
  │   └─> requirements.txt
  │
  └─ build_silicon_macos.py ──────> 打包执行
      ├─> main.py
      ├─> src/
      └─> public/

深入学习
  ├─ MACOS_SILICON_BUILD_GUIDE.md ─> 完整指南
  ├─ MACOS_TECHNICAL_NOTES.md ─────> 技术细节
  └─ PACKAGING_COMPARISON.md ──────> 跨平台对比

架构文档
  ├─ CLAUDE.MD ────────────────────> 架构总览
  └─ MACOS_SILICON_SUMMARY.md ─────> 方案总结
```

---

## 🎯 使用场景

### 场景 1: 首次打包 (新手)
1. 阅读 `MACOS_QUICK_START.md`
2. 运行 `setup_macos_silicon.sh`
3. 运行 `build_silicon_macos.py`

### 场景 2: 深入了解 (开发者)
1. 阅读 `MACOS_SILICON_BUILD_GUIDE.md`
2. 阅读 `MACOS_TECHNICAL_NOTES.md`
3. 手动配置和打包

### 场景 3: 跨平台对比 (架构师)
1. 阅读 `PACKAGING_COMPARISON.md`
2. 阅读 `MACOS_TECHNICAL_NOTES.md`
3. 评估技术方案

### 场景 4: 问题排查 (维护者)
1. 查看 `MACOS_TECHNICAL_NOTES.md` 的常见问题
2. 检查 `build/` 目录的构建日志
3. 参考 `MACOS_SILICON_BUILD_GUIDE.md` 的故障排除

---

## 📝 文件详细说明

### build_silicon_macos.py
**用途**: Silicon Mac 专用打包脚本  
**功能**:
- 自动检测 ARM64 架构
- 自动查找 libmpv 路径
- 自动移除隔离属性
- 可选创建 DMG

**使用**:
```bash
python build_silicon_macos.py
```

---

### setup_macos_silicon.sh
**用途**: 一键环境配置脚本  
**功能**:
- 安装 Homebrew (如未安装)
- 安装系统依赖 (mpv, ffmpeg)
- 创建虚拟环境
- 安装 Python 依赖
- 验证安装

**使用**:
```bash
chmod +x setup_macos_silicon.sh
./setup_macos_silicon.sh
```

---

### MACOS_QUICK_START.md
**用途**: 快速开始指南  
**内容**:
- 3 条命令完成打包
- 分发方式说明
- 常见问题 FAQ

**目标读者**: 所有用户

---

### MACOS_SILICON_BUILD_GUIDE.md
**用途**: 完整打包指南  
**内容**:
- 快速开始 (推荐)
- 手动配置步骤
- 常见问题解决
- 验证清单

**目标读者**: 开发者

---

### MACOS_TECHNICAL_NOTES.md
**用途**: 技术细节文档  
**内容**:
- 架构概览
- 依赖分析
- PyInstaller 配置详解
- 代码签名指南
- 性能优化建议

**目标读者**: 高级开发者、架构师

---

### PACKAGING_COMPARISON.md
**用途**: 跨平台打包对比  
**内容**:
- Windows vs macOS 对比
- Intel vs Silicon 对比
- 打包工具对比
- CI/CD 方案对比

**目标读者**: 架构师、技术决策者

---

### MACOS_SILICON_SUMMARY.md
**用途**: 方案总结  
**内容**:
- 已完成的工作
- 使用方式
- 技术亮点
- 核心技术决策

**目标读者**: 项目管理者、技术评审者

---

## 🔗 外部依赖

### Homebrew 包
- `python@3.11` - Python 运行时
- `mpv` - 视频播放库
- `ffmpeg` - 音视频处理

### Python 包 (requirements.txt)
- `PySide6` - Qt6 GUI 框架
- `torch` - PyTorch 深度学习框架
- `faster-whisper` - Whisper 语音识别
- `transformers` - Hugging Face 模型库
- `pyinstaller` - 打包工具

---

## 📦 输出产物

### 开发输出
```
dist/
├── Canto-beats.app/              # macOS App Bundle
└── Canto-beats-Silicon.dmg       # DMG 安装包 (可选)

build/
├── Canto-beats/                  # PyInstaller 构建目录
└── *.spec                        # PyInstaller 配置文件
```

### 分发文件
- `Canto-beats-Silicon.dmg` - 推荐分发格式
- `Canto-beats.app.zip` - 备选分发格式

---

## 🔄 更新流程

### 添加新功能
1. 修改源代码
2. 测试功能
3. 运行 `python build_silicon_macos.py`
4. 测试打包后的 App
5. 分发给用户

### 更新依赖
1. 修改 `requirements.txt`
2. 重新运行 `setup_macos_silicon.sh`
3. 重新打包

### 更新文档
1. 修改对应的 `.md` 文件
2. 更新 `CLAUDE.MD` 的变更记录
3. 提交 Git

---

## 📞 支持

遇到问题？按以下顺序查找：
1. `MACOS_QUICK_START.md` - 快速问题
2. `MACOS_TECHNICAL_NOTES.md` - 技术问题
3. `MACOS_SILICON_BUILD_GUIDE.md` - 配置问题
4. GitHub Issues - 未解决的问题

---

**最后更新**: 2024-01-XX  
**维护者**: Canto-beats Team

