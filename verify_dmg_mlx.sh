#!/bin/bash
# 驗證 DMG 中的 MLX

DMG_PATH="dist/Canto-beats.dmg"

echo "🔍 驗證 DMG 中的 MLX..."
echo ""

# 1. 檢查 DMG 是否存在
if [ ! -f "$DMG_PATH" ]; then
    echo "❌ 找不到: $DMG_PATH"
    exit 1
fi

echo "✅ DMG 存在: $DMG_PATH"
echo "   大小: $(du -h "$DMG_PATH" | cut -f1)"
echo ""

# 2. 掛載 DMG
echo "📦 掛載 DMG..."
MOUNT_OUTPUT=$(hdiutil attach "$DMG_PATH" 2>&1)
VOLUME=$(echo "$MOUNT_OUTPUT" | grep "/Volumes" | awk '{print $3}')

if [ -z "$VOLUME" ]; then
    echo "❌ 無法掛載 DMG"
    exit 1
fi

echo "✅ 已掛載到: $VOLUME"
echo ""

# 3. 檢查 MLX 文件
echo "🔍 檢查 MLX 文件..."

APP_PATH="$VOLUME/Canto-beats.app"
RESOURCES="$APP_PATH/Contents/Resources"

FILES=(
    "$RESOURCES/mlx/core.cpython-311-darwin.so"
    "$RESOURCES/mlx/_reprlib_fix.py"
    "$RESOURCES/mlx/nn"
    "$RESOURCES/mlx_whisper/transcribe.py"
)

ALL_OK=true
for file in "${FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "  ✅ $(basename $file)"
    else
        echo "  ❌ $(basename $file)"
        ALL_OK=false
    fi
done

echo ""

# 4. 卸載
echo "📤 卸載 DMG..."
hdiutil detach "$VOLUME" > /dev/null 2>&1

# 5. 結果
echo ""
if [ "$ALL_OK" = true ]; then
    echo "✅ DMG 驗證通過！MLX 已正確包含"
    echo ""
    echo "可以安全分發此 DMG："
    echo "  $DMG_PATH"
else
    echo "❌ DMG 驗證失敗，MLX 文件缺失"
    exit 1
fi

