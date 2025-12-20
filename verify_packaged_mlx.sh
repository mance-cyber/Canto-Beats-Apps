#!/bin/bash
# 驗證打包版本中的 MLX

echo "🔍 檢查打包版本中的 MLX..."

APP_PATH="dist/Canto-beats.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 打包版本不存在: $APP_PATH"
    echo "   請先運行: ./build_macos_app.sh"
    exit 1
fi

echo ""
echo "1️⃣ 檢查 MLX 庫文件..."
find "$APP_PATH" -name "*mlx*" -type f | head -20

echo ""
echo "2️⃣ 檢查 MLX Python 模塊..."
find "$APP_PATH" -name "mlx" -type d

echo ""
echo "3️⃣ 檢查 _reprlib_fix..."
find "$APP_PATH" -name "_reprlib_fix*"

echo ""
echo "4️⃣ 測試打包版本..."
"$APP_PATH/Contents/MacOS/Canto-beats" --version 2>&1 | head -20

echo ""
echo "✅ 檢查完成"

