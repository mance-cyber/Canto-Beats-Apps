#!/bin/bash
# 修復打包版本的 MLX 問題

set -e

APP_PATH="dist/Canto-beats.app"
RESOURCES="$APP_PATH/Contents/Resources"

echo "🔧 修復 MLX 打包問題..."

# 1. 檢查 app 是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 找不到: $APP_PATH"
    echo "   請先運行: ./build_macos_app.sh"
    exit 1
fi

# 2. 檢查 mlx 目錄
if [ -d "$RESOURCES/mlx" ]; then
    echo "✅ mlx 目錄已存在"
else
    echo "📦 複製 mlx 模塊..."
    cp -r venv/lib/python3.11/site-packages/mlx "$RESOURCES/"
    echo "✅ mlx 已複製"
fi

# 3. 檢查 mlx_whisper
if [ -d "$RESOURCES/mlx_whisper" ]; then
    echo "✅ mlx_whisper 已存在"
else
    echo "📦 複製 mlx_whisper 模塊..."
    cp -r venv/lib/python3.11/site-packages/mlx_whisper "$RESOURCES/"
    echo "✅ mlx_whisper 已複製"
fi

# 4. 驗證關鍵文件
echo ""
echo "🔍 驗證關鍵文件..."

FILES=(
    "$RESOURCES/mlx/__init__.py"
    "$RESOURCES/mlx/core.cpython-311-darwin.so"
    "$RESOURCES/mlx/_reprlib_fix.py"
    "$RESOURCES/mlx_whisper/__init__.py"
    "$RESOURCES/mlx_whisper/transcribe.py"
)

ALL_OK=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $(basename $file)"
    else
        echo "  ❌ $(basename $file)"
        ALL_OK=false
    fi
done

echo ""
if [ "$ALL_OK" = true ]; then
    echo "✅ 所有文件已就緒！"
    echo ""
    echo "測試應用:"
    echo "  open dist/Canto-beats.app"
else
    echo "❌ 部分文件缺失，請檢查"
    exit 1
fi

