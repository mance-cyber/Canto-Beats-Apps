#!/usr/bin/env python3
"""
快速創建 DMG 並檢查簽名/公證狀態

用法:
  python create_dmg_quick.py              # 創建 DMG
  python create_dmg_quick.py --check      # 檢查簽名狀態
  python create_dmg_quick.py --notarize   # 創建 DMG 並提示公證
"""

import sys
import subprocess
from pathlib import Path
import argparse


def check_signature(path):
    """檢查簽名狀態"""
    print(f"\n檢查簽名: {path}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            ["codesign", "-dvv", str(path)],
            capture_output=True,
            text=True
        )
        
        output = result.stderr  # codesign 輸出到 stderr
        
        if "adhoc" in output:
            print("❌ 臨時簽名（adhoc）- 未使用 Developer ID")
            print("   用戶首次打開時會看到 Gatekeeper 警告")
            return False
        elif "Developer ID" in output:
            print("✅ 已使用 Developer ID 簽名")
            
            # 檢查是否公證
            stapler_result = subprocess.run(
                ["xcrun", "stapler", "validate", str(path)],
                capture_output=True,
                text=True
            )
            
            if stapler_result.returncode == 0:
                print("✅ 已公證並裝訂")
                print("   用戶可以直接雙擊安裝，無警告")
                return True
            else:
                print("⚠️  已簽名但未公證")
                print("   用戶首次打開時仍會看到警告")
                return False
        else:
            print("❌ 未簽名")
            return False
            
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return False


def create_dmg():
    """創建 DMG"""
    app_path = Path("dist/Canto-beats.app")
    
    if not app_path.exists():
        print("❌ 錯誤: dist/Canto-beats.app 不存在")
        print("   請先運行: python build_silicon_macos.py")
        return None
    
    print("\n創建 DMG...")
    print("-" * 60)
    
    try:
        # 創建臨時目錄
        dmg_dir = Path("dist/dmg")
        dmg_dir.mkdir(exist_ok=True)
        
        # 複製 .app
        print("複製 App...")
        subprocess.run(["cp", "-r", str(app_path), "dist/dmg/"], check=True)
        
        # 創建 Applications 符號鏈接
        print("創建 Applications 鏈接...")
        subprocess.run(
            ["ln", "-s", "/Applications", "dist/dmg/Applications"],
            check=False  # 可能已存在
        )
        
        # 創建 DMG
        dmg_path = Path("dist/Canto-beats-Silicon.dmg")
        print(f"打包 DMG: {dmg_path.name}...")
        
        subprocess.run([
            "hdiutil", "create",
            "-volname", "Canto-beats",
            "-srcfolder", "dist/dmg",
            "-ov", "-format", "UDZO",
            str(dmg_path)
        ], check=True)
        
        # 清理
        subprocess.run(["rm", "-rf", "dist/dmg"], check=True)
        
        # 獲取文件大小
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        
        print("\n" + "=" * 60)
        print("✅ DMG 創建成功!")
        print("=" * 60)
        print(f"文件: {dmg_path}")
        print(f"大小: {size_mb:.1f} MB")
        
        return dmg_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG 創建失敗: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="快速創建 DMG 並檢查簽名狀態")
    parser.add_argument("--check", action="store_true", help="檢查現有文件的簽名狀態")
    parser.add_argument("--notarize", action="store_true", help="創建 DMG 並提示公證步驟")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Canto-beats DMG 工具")
    print("=" * 60)
    
    # 檢查模式
    if args.check:
        app_path = Path("dist/Canto-beats.app")
        dmg_path = Path("dist/Canto-beats-Silicon.dmg")
        
        if app_path.exists():
            check_signature(app_path)
        else:
            print(f"\n⚠️  {app_path} 不存在")
        
        if dmg_path.exists():
            check_signature(dmg_path)
        else:
            print(f"\n⚠️  {dmg_path} 不存在")
        
        return 0
    
    # 創建 DMG
    dmg_path = create_dmg()
    
    if not dmg_path:
        return 1
    
    # 檢查簽名狀態
    is_notarized = check_signature(dmg_path)
    
    # 提示後續步驟
    print("\n" + "=" * 60)
    print("後續步驟")
    print("=" * 60)
    
    print("\n1. 測試 DMG:")
    print(f"   open {dmg_path}")
    
    if not is_notarized:
        print("\n2. 簽名和公證（可選，需要 Apple Developer 帳號）:")
        print("   python notarize_macos.py")
        print("\n   需要設置環境變量:")
        print("   export SIGNING_IDENTITY='Developer ID Application: Your Name (TEAM_ID)'")
        print("   export APPLE_ID='your@email.com'")
        print("   export TEAM_ID='YOUR_TEAM_ID'")
        print("   export APP_PASSWORD='app-specific-password'")
        
        if args.notarize:
            print("\n" + "-" * 60)
            print("是否現在運行公證流程? (需要 Apple Developer 帳號)")
            print("按 Enter 跳過，輸入 'y' 繼續: ", end='')
            response = input()
            
            if response.lower() == 'y':
                print("\n運行公證腳本...")
                subprocess.run(["python", "notarize_macos.py"])
    else:
        print("\n✅ DMG 已簽名並公證，可以直接分發!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

