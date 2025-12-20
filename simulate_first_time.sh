#!/bin/bash
# 模擬首次使用（臨時重命名緩存）

echo "=========================================="
echo "模擬首次使用測試"
echo "=========================================="
echo ""
echo "這個腳本會："
echo "1. 臨時重命名 Whisper 模型緩存"
echo "2. 啟動應用程式"
echo "3. 測試完成後恢復緩存"
echo ""
read -p "是否繼續？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

CACHE_DIR="$HOME/.cache/huggingface/hub"
MODEL_DIR="models--mlx-community--whisper-large-v3-mlx"
BACKUP_DIR="${MODEL_DIR}.backup"

cd "$CACHE_DIR" || exit 1

# 備份模型
if [ -d "$MODEL_DIR" ]; then
    echo "✅ 備份模型緩存..."
    mv "$MODEL_DIR" "$BACKUP_DIR"
    echo "✅ 模型已臨時隱藏"
else
    echo "⚠️  模型緩存不存在，跳過備份"
fi

echo ""
echo "=========================================="
echo "請在應用程式中測試首次轉寫"
echo "應該會看到下載進度對話框"
echo "=========================================="
echo ""
echo "測試完成後，按 Enter 恢復緩存..."
read

# 恢復模型
if [ -d "$BACKUP_DIR" ]; then
    echo "✅ 恢復模型緩存..."
    mv "$BACKUP_DIR" "$MODEL_DIR"
    echo "✅ 模型已恢復"
else
    echo "⚠️  備份不存在，無需恢復"
fi

echo ""
echo "✅ 測試完成"

