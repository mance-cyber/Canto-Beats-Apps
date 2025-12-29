"""
下載思源黑體 Light 版本（較細）
"""

import requests
from pathlib import Path

def download_noto_sans_light():
    """Download Noto Sans CJK TC Light font"""
    
    # Font URL - Light version
    font_url = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Light.otf"
    
    # Target directory
    script_dir = Path(__file__).parent
    fonts_dir = script_dir / "src" / "resources" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    # Target file
    target_file = fonts_dir / "NotoSansCJKtc-Light.otf"
    
    print("正在下載思源黑體 Light 版本（較細）...")
    print(f"下載地址: {font_url}")
    print(f"保存位置: {target_file}")
    print("\n這可能需要幾分鐘，請耐心等待...")
    
    try:
        response = requests.get(font_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(target_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 50
                        filled = int(bar_length * downloaded / total_size)
                        bar = '=' * filled + '-' * (bar_length - filled)
                        print(f'\r[{bar}] {percent:.1f}% ({downloaded}/{total_size} bytes)', end='')
        
        print(f"\n\n✅ 下載完成！")
        print(f"字體已保存到: {target_file}")
        print(f"\n接下來需要修改 main.py 第 106 行，將檔名改為:")
        print(f"   font_path = src_path / \"resources\" / \"fonts\" / \"NotoSansCJKtc-Light.otf\"")
        print(f"\n然後重新啟動應用即可！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 下載失敗: {e}")
        return False

if __name__ == "__main__":
    download_noto_sans_light()
