"""
自動下載 libmpv-2.dll 到專案目錄
"""

import os
import sys
import urllib.request
import zipfile
from pathlib import Path

def download_libmpv():
    """下載 libmpv-2.dll"""
    
    print("🔍 正在準備下載 libmpv-2.dll...")
    
    # 使用 shinchiro 的預編譯版本 (常用的第三方構建)
    # 這是一個可靠的來源
    url = "https://sourceforge.net/projects/mpv-player-windows/files/libmpv/mpv-dev-x86_64-20241124-git-f6c1164.7z/download"
    
    print(f"📥 下載來源: SourceForge (mpv-player-windows)")
    print(f"⚠️  注意: 需要手動下載")
    print()
    print("請按照以下步驟操作:")
    print()
    print("1. 訪問: https://sourceforge.net/projects/mpv-player-windows/files/libmpv/")
    print("2. 下載最新的 mpv-dev-x86_64-*.7z 文件")
    print("3. 使用 7-Zip 解壓文件")
    print("4. 找到 libmpv-2.dll")
    print("5. 複製到以下位置:")
    print()
    
    target_dir = Path(__file__).parent
    print(f"   📁 {target_dir}\\libmpv-2.dll")
    print()
    print("或者,您可以使用以下 PowerShell 命令快速下載:")
    print()
    print("# 下載 mpv 完整安裝包 (包含 libmpv-2.dll)")
    print('Invoke-WebRequest -Uri "https://github.com/shinchiro/mpv-winbuild-cmake/releases/latest/download/mpv-x86_64-v3.7z" -OutFile "mpv.7z"')
    print()
    print("然後解壓並複製 libmpv-2.dll 到專案目錄")
    

if __name__ == "__main__":
    download_libmpv()
