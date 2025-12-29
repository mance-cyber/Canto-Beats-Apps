#!/bin/bash
# Silicon macOS 一键环境配置脚本
# 自动安装所有依赖并准备打包环境

set -e  # 遇到错误立即退出

echo "======================================"
echo "Canto-beats Silicon macOS 环境配置"
echo "======================================"

# 检查架构
ARCH=$(uname -m)
echo "当前架构: $ARCH"

if [ "$ARCH" != "arm64" ]; then
    echo "⚠️  警告: 不是 ARM64 架构"
    echo "建议在原生 Apple Silicon 环境下运行"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew 未安装"
    echo "正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew 已安装"
fi

# 安装系统依赖
echo ""
echo "安装系统依赖..."
brew install python@3.11 mpv ffmpeg

# 创建虚拟环境
echo ""
echo "创建 Python 虚拟环境..."
python3.11 -m venv venv
source venv/bin/activate

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip wheel setuptools

# 安装 PyTorch (ARM64 优化版本)
echo ""
echo "安装 PyTorch (ARM64)..."
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 过滤不兼容的依赖
echo ""
echo "准备依赖列表..."
grep -v -E "llama-cpp-python|bitsandbytes" requirements.txt > requirements-macos-silicon.txt

# 安装其他依赖
echo ""
echo "安装 Python 依赖..."
pip install -r requirements-macos-silicon.txt

# 安装 PyInstaller
echo ""
echo "安装 PyInstaller..."
pip install pyinstaller

# 验证安装
echo ""
echo "======================================"
echo "验证安装..."
echo "======================================"

python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')"
python -c "import faster_whisper; print('✅ Faster-Whisper: OK')"
python -c "from PySide6.QtWidgets import QApplication; print('✅ PySide6: OK')"
python -c "import mpv; print('✅ python-mpv: OK')"

echo ""
echo "======================================"
echo "🎉 环境配置完成!"
echo "======================================"
echo ""
echo "下一步:"
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 运行打包脚本: python build_silicon_macos.py"
echo ""

