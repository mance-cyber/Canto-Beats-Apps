#!/bin/bash
# Script to backup and remove AI models for testing first-time download

echo "🔍 AI 模型備份與移除工具"
echo "================================"
echo ""

# Hugging Face cache directory
HF_CACHE="$HOME/.cache/huggingface/hub"
BACKUP_DIR="$HOME/ai_models_backup_$(date +%Y%m%d_%H%M%S)"

# Check if models exist
if [ ! -d "$HF_CACHE" ]; then
    echo "❌ 找不到 Hugging Face 緩存目錄: $HF_CACHE"
    exit 1
fi

echo "📁 找到以下 AI 模型："
echo ""
du -sh "$HF_CACHE"/models--* 2>/dev/null
echo ""

# Ask user for action
echo "請選擇操作："
echo "  1) 移動模型到備份目錄 (可以稍後還原)"
echo "  2) 完全刪除模型 (無法還原)"
echo "  3) 取消"
echo ""
read -p "請輸入選項 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "📦 正在備份模型到: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        
        # Move models to backup
        mv "$HF_CACHE"/models--mlx-community--whisper* "$BACKUP_DIR/" 2>/dev/null
        mv "$HF_CACHE"/models--Qwen* "$BACKUP_DIR/" 2>/dev/null
        
        echo "✅ 模型已備份！"
        echo ""
        echo "📍 備份位置: $BACKUP_DIR"
        echo ""
        echo "要還原模型，請執行："
        echo "  mv $BACKUP_DIR/* $HF_CACHE/"
        ;;
    
    2)
        echo ""
        read -p "⚠️  確定要完全刪除所有 AI 模型嗎？ (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  正在刪除模型..."
            rm -rf "$HF_CACHE"/models--mlx-community--whisper*
            rm -rf "$HF_CACHE"/models--Qwen*
            echo "✅ 模型已刪除！"
        else
            echo "❌ 已取消刪除"
            exit 0
        fi
        ;;
    
    3)
        echo "❌ 已取消操作"
        exit 0
        ;;
    
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

echo ""
echo "🎉 完成！現在可以測試首次下載功能了"
echo ""
echo "💡 提示：首次啟動應用時，系統會自動下載所需的 AI 模型"
