#!/usr/bin/env python3
"""創建應用圖標"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_app_icon():
    """創建應用圖標"""
    
    # 創建 1024x1024 的圖標
    size = 1024
    img = Image.new('RGB', (size, size), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # 繪製圓形背景
    margin = 100
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#16213e')
    
    # 繪製內圓
    margin2 = 200
    draw.ellipse([margin2, margin2, size-margin2, size-margin2], fill='#0f3460')
    
    # 繪製文字 "CB"
    try:
        # 嘗試使用系統字體
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 400)
    except:
        font = ImageFont.load_default()
    
    text = "CB"
    
    # 計算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 50
    
    # 繪製文字
    draw.text((x, y), text, fill='#e94560', font=font)
    
    # 保存 PNG
    png_path = Path('public/icons/app_icon.png')
    img.save(png_path, 'PNG')
    print(f"✅ 創建 PNG: {png_path}")
    
    # 創建 ICNS（macOS）
    icns_path = Path('public/icons/app_icon.icns')
    
    # 創建多個尺寸
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    iconset_dir = Path('public/icons/app_icon.iconset')
    iconset_dir.mkdir(exist_ok=True)
    
    for s in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / f'icon_{s}x{s}.png')
        
        # @2x 版本
        if s <= 512:
            resized2x = img.resize((s*2, s*2), Image.Resampling.LANCZOS)
            resized2x.save(iconset_dir / f'icon_{s}x{s}@2x.png')
    
    # 使用 iconutil 創建 icns
    import subprocess
    try:
        subprocess.run([
            'iconutil', '-c', 'icns', 
            str(iconset_dir), 
            '-o', str(icns_path)
        ], check=True)
        print(f"✅ 創建 ICNS: {icns_path}")
    except Exception as e:
        print(f"⚠️  無法創建 ICNS: {e}")
    
    # 清理 iconset
    import shutil
    shutil.rmtree(iconset_dir)

if __name__ == "__main__":
    create_app_icon()

