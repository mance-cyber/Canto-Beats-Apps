#!/bin/bash
# 打包後處理：修復 MLX 並創建 DMG

set -e

APP_PATH="dist/Canto-beats.app"
RESOURCES="$APP_PATH/Contents/Resources"
DMG_NAME="Canto-beats.dmg"

echo "=" * 60
echo "打包後處理"
echo "=" * 60

# 1. 檢查 app
if [ ! -d "$APP_PATH" ]; then
    echo "❌ 找不到: $APP_PATH"
    exit 1
fi

# 2. 修復 MLX
echo ""
echo "🔧 修復 MLX..."

if [ ! -d "$RESOURCES/mlx" ]; then
    echo "  📦 複製 mlx..."
    cp -r venv/lib/python3.11/site-packages/mlx "$RESOURCES/"
fi

if [ ! -d "$RESOURCES/mlx_whisper" ]; then
    echo "  📦 複製 mlx_whisper..."
    cp -r venv/lib/python3.11/site-packages/mlx_whisper "$RESOURCES/"
fi

# 3. 驗證
echo ""
echo "✅ 驗證文件..."
if [ -f "$RESOURCES/mlx/core.cpython-311-darwin.so" ]; then
    echo "  ✅ mlx.core"
fi
if [ -f "$RESOURCES/mlx/_reprlib_fix.py" ]; then
    echo "  ✅ mlx._reprlib_fix"
fi
if [ -f "$RESOURCES/mlx_whisper/transcribe.py" ]; then
    echo "  ✅ mlx_whisper"
fi

# 4. 移除隔離屬性
echo ""
echo "🔓 移除隔離屬性..."
xattr -cr "$APP_PATH"
echo "  ✅ 完成"

# 5. 創建 DMG
echo ""
echo "📦 創建 DMG..."
if [ -f "dist/$DMG_NAME" ]; then
    rm "dist/$DMG_NAME"
fi

# 創建臨時目錄用於 DMG 內容
DMG_TEMP="dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# 複製應用
cp -R "$APP_PATH" "$DMG_TEMP/"

# 創建 Applications 符號鏈接
ln -s /Applications "$DMG_TEMP/Applications"

# 創建安裝說明
cat > "$DMG_TEMP/安裝說明.txt" << 'EOF'
📦 Canto-beats 安裝說明

⚠️ 重要：請將 Canto-beats.app 拖到 Applications 文件夾

為什麼需要這樣做？
- MLX GPU 加速需要可寫入的目錄
- 從 DMG 直接運行會使用 CPU 模式（很慢）
- 安裝到 Applications 後會使用 GPU 加速（快 5-10 倍）

安裝步驟：
1. 將 Canto-beats.app 拖到 Applications 文件夾
2. 從 Applications 文件夾啟動應用
3. 享受 GPU 加速的快速轉寫！

---
📦 Canto-beats Installation Guide

⚠️ Important: Drag Canto-beats.app to Applications folder

Why?
- MLX GPU acceleration requires writable directory
- Running from DMG uses CPU mode (slow)
- Installing to Applications uses GPU acceleration (5-10x faster)

Steps:
1. Drag Canto-beats.app to Applications folder
2. Launch from Applications folder
3. Enjoy fast GPU-accelerated transcription!
EOF

# 創建 DMG
hdiutil create -volname "Canto-beats" \
  -srcfolder "$DMG_TEMP" \
  -ov -format UDZO \
  "dist/$DMG_NAME"

# 清理
rm -rf "$DMG_TEMP"

echo ""
echo "=" * 60
echo "✅ 完成！"
echo "=" * 60
echo ""
echo "輸出文件:"
echo "  • App: $APP_PATH"
echo "  • DMG: dist/$DMG_NAME"
echo ""
echo "測試:"
echo "  open $APP_PATH"

