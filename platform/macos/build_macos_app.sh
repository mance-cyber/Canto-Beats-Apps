#!/bin/bash
# macOS 打包腳本

set -e  # 遇到錯誤立即退出

echo "=========================================="
echo "Canto-Beats macOS 打包"
echo "=========================================="
echo ""

# 1. 打包前檢查
echo "1️⃣ 執行打包前檢查..."
venv/bin/python pre_build_check.py
if [ $? -ne 0 ]; then
    echo "❌ 打包前檢查失敗，請先解決問題"
    exit 1
fi

echo ""
echo "2️⃣ 清理舊的打包文件..."
rm -rf build dist
rm -f *.spec

echo ""
echo "3️⃣ 開始打包..."
venv/bin/python build_silicon_macos.py

echo ""
echo "4️⃣ 打包後處理..."
./post_build.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 打包成功！"
    echo "=========================================="
    echo ""
    echo "打包文件位置:"
    echo "  • App: dist/Canto-beats.app"
    echo "  • DMG: dist/Canto-beats.dmg"
    echo ""
    echo "測試應用:"
    echo "  open dist/Canto-beats.app"
else
    echo ""
    echo "=========================================="
    echo "❌ 打包失敗"
    echo "=========================================="
    exit 1
fi

