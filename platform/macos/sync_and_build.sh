#!/bin/bash
# 同步最新代碼並打包

set -e

echo "🔄 同步最新代碼到打包版本..."

# 1. 清理舊打包
echo "1️⃣ 清理舊打包..."
rm -rf build dist *.spec

# 2. 確認當前代碼是最新的
echo "2️⃣ 確認代碼狀態..."
echo "   主要文件最後修改時間:"
ls -lh main.py
ls -lh src/models/qwen_llm.py
ls -lh src/ui/avplayer_widget.py
ls -lh src/pipeline/subtitle_pipeline_v2.py

# 3. 執行打包前檢查
echo ""
echo "3️⃣ 執行打包前檢查..."
venv/bin/python pre_build_check.py

# 4. 開始打包
echo ""
echo "4️⃣ 開始打包（使用最新代碼）..."
venv/bin/python build_silicon_macos.py

echo ""
echo "✅ 打包完成！"
echo "   打包版本包含所有最新修改"

