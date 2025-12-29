#!/usr/bin/env python3
"""
將 README.txt 添加到已簽名公證的 DMG
不需要重新簽名，只是添加文檔文件
"""

import subprocess
import shutil
import os
from pathlib import Path

def add_readme_to_dmg():
    """添加 README.txt 到已簽名的 DMG"""
    
    # README 內容
    readme_content = """╔═══════════════════════════════════════════════════════════════╗
║                   Canto-beats 安裝說明                        ║
║              粵語字幕自動生成與校正工具                         ║
╚═══════════════════════════════════════════════════════════════╝

歡迎使用 Canto-beats！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 安裝步驟

1. 將 Canto-beats.app 拖曳到 Applications 資料夾
2. 首次啟動時，如果系統提示「無法打開」，請執行以下步驟：
   • 前往「系統設定」→「隱私權與安全性」
   • 找到 Canto-beats 並點擊「仍要打開」
   • 或在終端機執行：xattr -cr /Applications/Canto-beats.app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💻 系統需求

• macOS 15.0 或更新版本
• Apple Silicon (M1/M2/M3) 處理器
• 至少 8GB RAM（建議 16GB 以上）
• 至少 15GB 可用儲存空間

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 使用說明

1. 啟動 Canto-beats.app
2. 點擊「選擇影片」載入您的影片檔案
3. 選擇字幕風格：
   • 口語：保留粵語口語詞彙（嘅、唔、冇等）
   • 半書面語：部分轉換為書面語
   • 書面語：完全轉換為正式書面語
4. 點擊「開始轉錄」
5. 完成後可編輯字幕並導出 SRT 檔案

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ 主要功能

• 🎯 高精度粵語語音辨識
• 📝 智能粵語字幕校正
• 🎨 三種字幕風格轉換
• ⚡ Apple Silicon GPU 加速
• 🎬 即時預覽與編輯
• 💾 導出標準 SRT,ASS,XML 格式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 技術支援

如遇到問題，請檢查：
• 系統是否符合最低需求
• 是否有足夠的儲存空間
• 影片格式是否支援（建議使用 MP4/MOV）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© 2024 Canto-beats | 版本 1.0.0a | Apple Silicon 優化版
"""
    
    print("=" * 60)
    print("添加 README.txt 到已簽名的 DMG")
    print("=" * 60)
    
    # 檢查源 DMG 是否存在
    source_dmg = Path("dist/Canto-beats-macOS-Notarized.dmg")
    if not source_dmg.exists():
        print(f"❌ 找不到源 DMG: {source_dmg}")
        return 1
    
    print(f"\n✅ 找到源 DMG: {source_dmg}")
    print(f"   大小: {source_dmg.stat().st_size / (1024*1024):.1f} MB")
    
    # 創建臨時目錄
    temp_dir = Path("dist/dmg_temp")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 1. 掛載源 DMG（唯讀）
        print("\n📀 掛載源 DMG...")
        mount_result = subprocess.run(
            ['hdiutil', 'attach', str(source_dmg), '-readonly', '-nobrowse'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 解析掛載點
        mount_point = None
        for line in mount_result.stdout.split('\n'):
            if '/Volumes/' in line:
                mount_point = line.split('\t')[-1].strip()
                break
        
        if not mount_point:
            print("❌ 無法找到掛載點")
            return 1
        
        print(f"✅ 已掛載到: {mount_point}")
        
        # 2. 複製所有內容到臨時目錄
        print("\n📋 複製 DMG 內容...")
        for item in Path(mount_point).iterdir():
            # Skip old 使用說明.txt file
            if item.name == "使用說明.txt":
                print(f"   ⏭️  跳過舊檔案: {item.name}")
                continue
                
            dest = temp_dir / item.name
            
            # Special handling for symlinks (like Applications shortcut)
            if item.is_symlink():
                # Get the symlink target
                link_target = os.readlink(item)
                # Recreate the symlink in temp_dir
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
                os.symlink(link_target, dest)
                print(f"   ✅ 重建符號連結: {item.name} -> {link_target}")
            elif item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest, symlinks=True)
                print(f"   ✅ 複製目錄: {item.name}")
            else:
                shutil.copy2(item, dest)
                print(f"   ✅ 複製檔案: {item.name}")
        
        # 3. 卸載源 DMG
        print("\n💿 卸載源 DMG...")
        subprocess.run(['hdiutil', 'detach', mount_point], check=True)
        print("✅ 已卸載")
        
        # 4. 創建 README.txt
        print("\n📝 創建 README.txt...")
        readme_path = temp_dir / "README.txt"
        readme_path.write_text(readme_content, encoding='utf-8')
        print("✅ README.txt 已創建")
        
        # 5. 確保 Applications 捷徑存在
        apps_link = temp_dir / "Applications"
        if not apps_link.exists():
            print("\n🔗 創建 Applications 捷徑...")
            subprocess.run(['ln', '-s', '/Applications', str(apps_link)], check=True)
            print("✅ Applications 捷徑已創建")
        else:
            print("\n✅ Applications 捷徑已存在")
        
        # 6. 創建新的 DMG
        print("\n📦 創建新 DMG...")
        output_dmg = Path("dist/Canto-beats-Final.dmg")
        
        # 刪除舊的 Final DMG（如果存在）
        if output_dmg.exists():
            output_dmg.unlink()
            print(f"   🗑️  已刪除舊的 {output_dmg.name}")
        
        subprocess.run([
            'hdiutil', 'create',
            '-volname', 'Canto-beats',
            '-srcfolder', str(temp_dir),
            '-ov', '-format', 'UDZO',
            str(output_dmg)
        ], check=True)
        
        print(f"\n✅ 新 DMG 創建成功: {output_dmg}")
        print(f"   大小: {output_dmg.stat().st_size / (1024*1024):.1f} MB")
        
        # 7. 清理臨時目錄
        print("\n🧹 清理臨時檔案...")
        shutil.rmtree(temp_dir)
        print("✅ 清理完成")
        
        print("\n" + "=" * 60)
        print("🎉 完成！")
        print("=" * 60)
        print(f"\n新的 DMG 檔案: {output_dmg}")
        print("\n內容包含:")
        print("  • Canto-beats.app (已簽名公證)")
        print("  • README.txt (安裝說明)")
        print("  • Applications (捷徑)")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 錯誤: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        return 1
    finally:
        # 確保清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    import sys
    sys.exit(add_readme_to_dmg())
