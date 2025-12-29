#!/bin/bash
# Canto-Beats 啟動腳本
# 確保在正確的虛擬環境中運行

# 切換到項目目錄
cd "$(dirname "$0")"

# 檢查虛擬環境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 錯誤：找不到虛擬環境 'venv'"
    echo "請先運行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虛擬環境
echo "🔄 激活虛擬環境..."
source venv/bin/activate

# 檢查 Python 版本
echo "✅ Python 版本: $(python --version)"

# 檢查關鍵依賴
echo "🔍 檢查依賴..."
python -c "import PySide6; print('✅ PySide6 已安裝')" 2>/dev/null || echo "❌ PySide6 未安裝"
python -c "import mlx; print('✅ MLX 已安裝')" 2>/dev/null || echo "❌ MLX 未安裝"
python -c "import mpv; print('✅ python-mpv 已安裝')" 2>/dev/null || echo "⚠️  python-mpv 未安裝（但 AVPlayer 可用）"

# 運行應用程序
echo ""
echo "🚀 啟動 Canto-Beats..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python main.py

# 退出虛擬環境
deactivate
