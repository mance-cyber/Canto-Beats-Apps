#!/bin/bash
# Canto-beats 診斷腳本
# 用於在新 Mac 上診斷應用程式啟動問題

echo "🔍 Canto-beats 診斷工具"
echo "========================"
echo ""

# 1. 檢查 macOS 版本
echo "1️⃣ macOS 版本:"
sw_vers
echo ""

# 2. 檢查硬體架構
echo "2️⃣ 硬體架構:"
uname -m
sysctl -n machdep.cpu.brand_string
echo ""

# 3. 檢查應用程式是否存在
APP_PATH="/Applications/Canto-beats.app"
echo "3️⃣ 檢查應用程式:"
if [ -d "$APP_PATH" ]; then
    echo "✅ 應用程式已安裝: $APP_PATH"
    ls -lh "$APP_PATH"
else
    echo "❌ 應用程式未找到: $APP_PATH"
    echo "請確保已從 DMG 複製到 Applications 資料夾"
    exit 1
fi
echo ""

# 4. 檢查 Gatekeeper 狀態
echo "4️⃣ Gatekeeper 檢查:"
spctl -a -v "$APP_PATH" 2>&1
echo ""

# 5. 檢查簽名
echo "5️⃣ 簽名檢查:"
codesign --verify --verbose "$APP_PATH" 2>&1
echo ""

# 6. 嘗試從終端啟動並捕獲錯誤
echo "6️⃣ 嘗試從終端啟動 (捕獲錯誤):"
echo "執行: $APP_PATH/Contents/MacOS/Canto-beats"
echo ""
"$APP_PATH/Contents/MacOS/Canto-beats" 2>&1 &
APP_PID=$!
sleep 3

# 檢查進程是否仍在運行
if ps -p $APP_PID > /dev/null; then
    echo "✅ 應用程式已啟動 (PID: $APP_PID)"
    echo "如果看不到視窗，請檢查 Dock 或活動監視器"
else
    echo "❌ 應用程式啟動失敗"
    echo ""
    echo "請檢查上面的錯誤訊息"
fi
echo ""

# 7. 檢查系統日誌
echo "7️⃣ 最近的系統日誌 (Canto-beats 相關):"
log show --predicate 'process == "Canto-beats"' --last 5m --style compact 2>/dev/null || \
log show --predicate 'processImagePath CONTAINS "Canto-beats"' --last 5m --style compact 2>/dev/null || \
echo "無法讀取系統日誌（需要權限）"
echo ""

# 8. 檢查 Python 庫
echo "8️⃣ 檢查 Python 共享庫:"
PYTHON_LIB="$APP_PATH/Contents/Frameworks/Python"
if [ -L "$PYTHON_LIB" ]; then
    echo "✅ Python symlink 存在"
    ls -la "$PYTHON_LIB"
    PYTHON_TARGET=$(readlink "$PYTHON_LIB")
    PYTHON_REAL="$APP_PATH/Contents/Frameworks/$PYTHON_TARGET"
    if [ -f "$PYTHON_REAL" ]; then
        echo "✅ Python 庫存在: $PYTHON_TARGET"
        file "$PYTHON_REAL"
        
        # 檢查依賴
        echo ""
        echo "Python 庫依賴:"
        otool -L "$PYTHON_REAL" | head -10
    else
        echo "❌ Python 庫不存在: $PYTHON_REAL"
    fi
else
    echo "❌ Python symlink 不存在: $PYTHON_LIB"
fi
echo ""

# 9. 檢查主執行檔依賴
echo "9️⃣ 主執行檔依賴檢查:"
MAIN_EXEC="$APP_PATH/Contents/MacOS/Canto-beats"
if [ -f "$MAIN_EXEC" ]; then
    otool -L "$MAIN_EXEC" | head -15
else
    echo "❌ 主執行檔不存在"
fi
echo ""

# 10. 診斷總結
echo "🔟 診斷建議:"
echo "============"
echo ""
echo "如果應用程式無法啟動，請檢查："
echo "1. macOS 版本是否為 15.0 或更新（建議）"
echo "2. 硬體是否為 Apple Silicon (ARM64)"
echo "3. 是否有權限問題（Gatekeeper）"
echo "4. Python 庫是否正確"
echo "5. 查看上面的錯誤訊息"
echo ""
echo "請將上述診斷結果截圖或複製發送給開發者"
