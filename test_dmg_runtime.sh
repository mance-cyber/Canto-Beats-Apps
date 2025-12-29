#!/bin/bash
# 從 DMG 運行應用並監控日誌

echo "🚀 從 DMG 啟動應用..."
open "/Volumes/Canto-beats/Canto-beats.app"

echo ""
echo "⏳ 等待應用啟動..."
sleep 5

echo ""
echo "📋 查看最新日誌（關於 MLX）..."
echo ""

# 查看日誌（如果是加密的，顯示提示）
LOG_DIR="$HOME/.canto-beats/logs"
LATEST_LOG=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)

if [ -f "$LATEST_LOG" ]; then
    echo "日誌文件: $LATEST_LOG"
    echo ""
    tail -100 "$LATEST_LOG" | grep -i "mlx\|whisper\|mps\|available" | tail -20
else
    echo "⚠️  日誌已加密，無法直接讀取"
    echo ""
    echo "請在應用中："
    echo "1. 加載視頻"
    echo "2. 點擊「開始轉寫」"
    echo "3. 觀察速度"
    echo ""
    echo "如果很慢（0.5x 實時），說明在用 CPU"
    echo "如果很快（3-5x 實時），說明在用 MLX"
fi

