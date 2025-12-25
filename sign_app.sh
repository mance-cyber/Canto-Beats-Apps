#!/bin/bash
# 正確簽名 macOS app bundle 的所有組件
# 必須從內到外簽名：dylibs → frameworks → app bundle
# 移除頂層 Qt symlinks（Apple 公證不接受）

set -e

APP_PATH="dist/Canto-beats.app"
IDENTITY="Developer ID Application: Man Hin Li (678P6T2H5Q)"

echo "開始簽名流程..."
echo "Identity: $IDENTITY"
echo "App: $APP_PATH"
echo ""

# 0. 移除 Contents/Frameworks 下的 Qt symlinks（公證不接受）
# 注意：保留 Python symlink，這是 PyInstaller 必需的
echo "Step 0: 移除頂層 Qt symlinks..."
find "$APP_PATH/Contents/Frameworks" -maxdepth 1 -type l -name "Qt*" -delete
echo "  ✅ 已移除 Qt symlinks（保留 Python symlink）"
echo ""

# 1. 簽名所有 .dylib 檔案
echo "Step 1: 簽名 .dylib 檔案..."
find "$APP_PATH/Contents/Frameworks" -name "*.dylib" -type f | while read dylib; do
    echo "  簽名: $(basename $dylib)"
    codesign --force --sign "$IDENTITY" --timestamp --options runtime "$dylib" 2>&1 | grep -v "replacing existing signature" || true
done

# 2. 簽名所有 .so 檔案 (Python extensions)
echo ""
echo "Step 2: 簽名 .so 檔案..."
find "$APP_PATH/Contents" -name "*.so" -type f | while read so; do
    echo "  簽名: $(basename $so)"
    codesign --force --sign "$IDENTITY" --timestamp --options runtime "$so" 2>&1 | grep -v "replacing existing signature" || true
done

# 3. 簽名所有 frameworks (從內到外)
echo ""
echo "Step 3: 簽名 Frameworks..."
find "$APP_PATH/Contents/Frameworks" -name "*.framework" -type d | while read framework; do
    # 找到 framework 內的主執行檔
    framework_name=$(basename "$framework" .framework)
    framework_exec="$framework/Versions/A/$framework_name"
    
    # 如果沒有 Versions 目錄，直接用 framework 名稱
    if [ ! -f "$framework_exec" ]; then
        framework_exec="$framework/$framework_name"
    fi
    
    if [ -f "$framework_exec" ]; then
        echo "  簽名: $(basename $framework)"
        codesign --force --sign "$IDENTITY" --timestamp --options runtime "$framework" 2>&1 | grep -v "replacing existing signature" || true
    fi
done

# 4. 簽名主執行檔
echo ""
echo "Step 4: 簽名主執行檔..."
codesign --force --sign "$IDENTITY" --timestamp --options runtime "$APP_PATH/Contents/MacOS/Canto-beats"

# 5. 最後簽名整個 app bundle (不用 --deep)
echo ""
echo "Step 5: 簽名 app bundle..."
codesign --force --sign "$IDENTITY" --timestamp --options runtime "$APP_PATH"

# 6. 驗證簽名
echo ""
echo "驗證簽名..."
codesign --verify --verbose "$APP_PATH"
spctl -a -v "$APP_PATH" 2>&1 || true

echo ""
echo "✅ 簽名完成！"
