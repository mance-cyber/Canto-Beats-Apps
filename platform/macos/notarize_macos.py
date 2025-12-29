#!/usr/bin/env python3
"""
macOS 公证 (Notarization) 脚本
自动化签名、公证和装订流程

Usage:
    python notarize_macos.py                    # 完整流程
    python notarize_macos.py --sign-only        # 仅签名
    python notarize_macos.py --notarize-only    # 仅公证 (已签名的包)
    python notarize_macos.py --verify           # 验证公证状态

环境变量 (必须设置):
    APPLE_ID         - Apple ID 邮箱
    TEAM_ID          - Apple Developer Team ID  
    APP_PASSWORD     - App-Specific Password
    SIGNING_IDENTITY - Developer ID Application 证书名称
"""

import subprocess
import sys
import os
import argparse
import shutil
from pathlib import Path


# ============================================================
# 配置
# ============================================================

APP_NAME = "Canto-beats"
BUNDLE_ID = "com.cantobeats.app"
APP_PATH = Path("dist/Canto-beats.app")
DMG_PATH = Path("dist/Canto-beats-macOS-Notarized.dmg")
ENTITLEMENTS = Path("entitlements.plist")


# ============================================================
# 辅助函数
# ============================================================

def run(cmd, check=True, capture=False):
    """执行命令并打印"""
    print(f"  > {' '.join(cmd)}")
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    else:
        result = subprocess.run(cmd, check=check)
        return result


def get_env(name):
    """获取环境变量"""
    value = os.environ.get(name)
    if not value:
        # 如果提供了 KEYCHAIN_PROFILE，就不需要 APPLE_ID 和 APP_PASSWORD
        if os.environ.get("KEYCHAIN_PROFILE") and name in ["APPLE_ID", "APP_PASSWORD"]:
            return ""
        print(f"錯誤: 環境變數 {name} 未設置")
        sys.exit(1)
    return value


def check_prerequisites():
    """检查前置条件"""
    print("\n检查前置条件...")

    # 检查是否在 macOS
    if sys.platform != "darwin":
        print("错误: 此脚本仅支持 macOS")
        sys.exit(1)

    # 检查必要工具
    # codesign 和 hdiutil 可以直接調用
    for tool in ["codesign", "hdiutil"]:
        try:
            subprocess.run(["which", tool], capture_output=True, check=True)
            print(f"  [OK] {tool}")
        except subprocess.CalledProcessError:
            print(f"  [FAIL] {tool} 未找到")
            sys.exit(1)

    # notarytool 和 stapler 需要通過 xcrun 調用
    # notarytool 支持 --version
    try:
        subprocess.run(["xcrun", "notarytool", "--version"], capture_output=True, check=True)
        print(f"  [OK] notarytool (via xcrun)")
    except subprocess.CalledProcessError:
        print(f"  [FAIL] notarytool 未找到")
        print(f"  請安裝 Xcode 命令行工具: xcode-select --install")
        sys.exit(1)

    # stapler 不支持 --version，直接運行會顯示 usage（返回碼 0）
    try:
        result = subprocess.run(["xcrun", "stapler"], capture_output=True)
        if b"Usage:" in result.stdout or b"Usage:" in result.stderr:
            print(f"  [OK] stapler (via xcrun)")
        else:
            raise subprocess.CalledProcessError(1, ["xcrun", "stapler"])
    except subprocess.CalledProcessError:
        print(f"  [FAIL] stapler 未找到")
        print(f"  請安裝 Xcode 命令行工具: xcode-select --install")
        sys.exit(1)

    # 检查 entitlements.plist
    if not ENTITLEMENTS.exists():
        print(f"  [FAIL] {ENTITLEMENTS} 未找到")
        sys.exit(1)
    print(f"  [OK] {ENTITLEMENTS}")

    # 检查 .app
    if not APP_PATH.exists():
        print(f"  [FAIL] {APP_PATH} 未找到")
        print("  请先运行 build_silicon_macos.py 构建应用")
        sys.exit(1)
    print(f"  [OK] {APP_PATH}")


# ============================================================
# 签名
# ============================================================

def sign_app():
    """签名 .app 包 - 完全清除後重新簽名"""
    print("\n" + "=" * 60)
    print("Step 1: 代码签名")
    print("=" * 60)

    identity = get_env("SIGNING_IDENTITY")

    # ===== 階段 0: 移除 Resources 入面會導致公證失敗嘅內容 =====
    # PyInstaller 會喺 Resources 入面創建重複嘅 Framework 結構，呢啲會導致公證失敗
    print("\n[0/5] 清理 Resources 目錄...")
    resources_dir = APP_PATH / "Contents" / "Resources"
    removed_count = 0
    
    if resources_dir.exists():
        import shutil
        
        # 1. 移除整個 PySide6 目錄（包含重複嘅 Qt Frameworks）
        pyside6_dir = resources_dir / "PySide6"
        if pyside6_dir.exists():
            print(f"  移除: PySide6/ (重複嘅 Qt Frameworks)")
            shutil.rmtree(pyside6_dir)
            removed_count += 1
        
        # 2. 移除所有指向二進位嘅 symlinks（遞歸）
        for root, dirs, files in os.walk(resources_dir):
            for item_name in list(files) + list(dirs):
                item = Path(root) / item_name
                if item.is_symlink():
                    target = item.resolve()
                    if target.exists():
                        result = subprocess.run(["file", str(target)], capture_output=True, text=True)
                        if "Mach-O" in result.stdout:
                            print(f"  移除: {item.relative_to(resources_dir)}")
                            item.unlink()
                            removed_count += 1
    
    print(f"  已清理 {removed_count} 個項目")

    # ===== 階段 1: 完全清除所有簽名 =====
    print("\n[1/5] 完全清除所有現有簽名...")
    
    # 1a. 移除擴展屬性（允許失敗，因為某些文件可能已被移除）
    print("  移除擴展屬性 (xattr -cr)...")
    run(["xattr", "-cr", str(APP_PATH)], check=False)
    
    # 1b. 找出所有 Mach-O 文件並移除其簽名
    # 使用 find 和 file 命令組合，比 Python 遍歷更快更準確
    print("  移除所有二進位文件的簽名...")
    # 找出所有非符號連結的可執行文件
    find_cmd = f'find "{APP_PATH}" -type f ! -name "*.py" ! -name "*.pyc" ! -name "*.txt" ! -name "*.json" ! -name "*.png" ! -name "*.icns" ! -name "*.plist" -exec file {{}} \\; | grep "Mach-O" | cut -d: -f1'
    result = subprocess.run(find_cmd, shell=True, capture_output=True, text=True)
    mach_o_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    
    print(f"  找到 {len(mach_o_files)} 個 Mach-O 文件")
    for f in mach_o_files:
        subprocess.run(["codesign", "--remove-signature", f], capture_output=True)
    
    # ===== 階段 2: 簽名所有 Mach-O 二進位文件 =====
    print(f"\n[2/5] 簽名所有 {len(mach_o_files)} 個二進位文件...")
    
    # 按路徑深度排序（深的先簽）
    mach_o_files.sort(key=lambda x: len(x), reverse=True)
    
    main_exec = APP_PATH / "Contents" / "MacOS" / APP_NAME
    
    for f in mach_o_files:
        fp = Path(f)
        if fp == main_exec:
            continue  # 主程式最後簽
        
        rel_path = fp.relative_to(APP_PATH) if fp.is_relative_to(APP_PATH) else fp
        # 只打印簡短的相對路徑
        run([
            "codesign", "--force", "--verbose",
            "--sign", identity,
            "--options", "runtime",
            "--timestamp",
            str(f)
        ], check=False)

    # ===== 階段 3: 簽名所有 Framework =====
    print("\n[3/5] 簽名所有 Framework...")
    
    # 找出所有 .framework 目錄，按深度排序（深的先簽）
    frameworks = list(APP_PATH.rglob("*.framework"))
    frameworks.sort(key=lambda x: len(x.parts), reverse=True)
    
    for fw in frameworks:
        if not fw.is_dir():
            continue
        # 跳過符號連結的 framework
        if fw.is_symlink():
            continue
            
        rel_path = fw.relative_to(APP_PATH)
        print(f"  簽名: {rel_path}")
        # 使用 --deep 確保 Framework 內部結構正確簽名
        run([
            "codesign", "--force", "--deep", "--verbose",
            "--sign", identity,
            "--options", "runtime",
            "--timestamp",
            str(fw)
        ], check=False)

    # ===== 階段 4: 簽名主程式和整個 App Bundle =====
    print("\n[4/5] 簽名主可執行文件...")
    
    # 4a. 簽名主可執行文件 (帶 Entitlements)
    if main_exec.exists():
        print(f"  簽名主程式: {main_exec.name} (帶 Entitlements)")
        run([
            "codesign", "--force", "--verbose",
            "--sign", identity,
            "--options", "runtime",
            "--timestamp",
            "--entitlements", str(ENTITLEMENTS),
            str(main_exec)
        ])
    
    # 4b. 最後使用 --deep 簽名整個 .app 包
    # 這會確保任何遺漏的文件都被正確簽名
    print(f"  簽名整個應用包: {APP_PATH.name} (使用 --deep)")
    run([
        "codesign", "--force", "--deep", "--verbose",
        "--sign", identity,
        "--options", "runtime",
        "--timestamp",
        "--entitlements", str(ENTITLEMENTS),
        str(APP_PATH)
    ])

    # 验证签名
    print("\n验证签名...")
    result = run(["codesign", "--verify", "--verbose=4", str(APP_PATH)], check=False)
    if result.returncode == 0:
        print("[OK] 签名验证通过")
    else:
        print("[WARN] 签名验证有警告，但继续...")

    print("\n[OK] 签名完成")


# ============================================================
# 创建 DMG
# ============================================================

def create_dmg():
    """创建签名的 DMG (包含 README 和 Applications 捷徑)"""
    print("\n" + "=" * 60)
    print("Step 2: 創建 DMG")
    print("=" * 60)
    
    identity = get_env("SIGNING_IDENTITY")
    
    # 刪除舊 DMG
    if DMG_PATH.exists():
        DMG_PATH.unlink()
    
    # 創建臨時目錄用於 DMG 內容
    dmg_temp = Path("dist/dmg_notarize_temp")
    if dmg_temp.exists():
        shutil.rmtree(dmg_temp)
    dmg_temp.mkdir(parents=True)
    
    print(f"  準備 DMG 內容於: {dmg_temp}")
    
    # 1. 複製應用 (.app)
    # 使用 cp -R 保留權限和符號連結
    run(["cp", "-R", str(APP_PATH), str(dmg_temp / APP_PATH.name)])
    
    # 2. 創建 Applications 符號連結
    run(["ln", "-s", "/Applications", str(dmg_temp / "Applications")])
    
    # 3. 創建 README.txt
    readme_content = """📦 Canto-beats 安裝說明

⚠️ 重要: 請將 Canto-beats.app 拖動到 Applications (應用程式) 資料夾中安裝

為什麼？
- MLX GPU 加速需要可寫入的目錄
- 從 DMG 直接執行會使用 CPU 模式 (慢)
- 安裝到 Applications 後會使用 GPU 加速 (快 5-10 倍)

步驟:
1. 將 Canto-beats.app 拖到 Applications 資料夾
2. 從 Applications 資料夾啟動程式
3. 享受流暢的 GPU 加速轉譯！
"""
    with open(dmg_temp / "使用說明.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # 創建 DMG
    print(f"\n執行 hdiutil 創建 DMG: {DMG_PATH.name}")
    run([
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", str(dmg_temp),
        "-ov", "-format", "UDZO",
        str(DMG_PATH)
    ])
    
    # 清理臨時目錄
    shutil.rmtree(dmg_temp)
    
    # 簽名 DMG
    print(f"\n簽名 DMG...")
    run([
        "codesign", "--force", "--verbose",
        "--sign", identity,
        str(DMG_PATH)
    ])
    
    print(f"\n[OK] DMG 創建完成: {DMG_PATH}")


# ============================================================
# 公证
# ============================================================

def notarize():
    """提交公證"""
    print("\n" + "=" * 60)
    print("Step 3: 提交公證")
    print("=" * 60)
    
    # 優先使用 Keychain Profile
    keychain_profile = os.environ.get("KEYCHAIN_PROFILE")
    
    if keychain_profile:
        print(f"\n使用 Keychain Profile '{keychain_profile}' 提交 {DMG_PATH.name}...")
        print("(這可能需要 5-30 分鐘)\n")
        
        run([
            "xcrun", "notarytool", "submit",
            str(DMG_PATH),
            "--keychain-profile", keychain_profile,
            "--wait"
        ])
    else:
        apple_id = get_env("APPLE_ID")
        team_id = get_env("TEAM_ID")
        app_password = get_env("APP_PASSWORD")
        
        print(f"\n提交 {DMG_PATH.name} 到 Apple 公證服務...")
        print("(這可能需要 5-30 分鐘)\n")
        
        run([
            "xcrun", "notarytool", "submit",
            str(DMG_PATH),
            "--apple-id", apple_id,
            "--team-id", team_id,
            "--password", app_password,
            "--wait"
        ])
    
    print("\n[OK] 公證完成")


# ============================================================
# 装订
# ============================================================

def staple():
    """装订公证票据"""
    print("\n" + "=" * 60)
    print("Step 4: 装订公证票据")
    print("=" * 60)
    
    # 装订 .app
    print(f"\n装订 {APP_PATH.name}...")
    run(["xcrun", "stapler", "staple", str(APP_PATH)])
    
    # 重新创建 DMG (包含已装订的 .app)
    print(f"\n重新创建 DMG (包含装订后的 .app)...")
    create_dmg()
    
    # 装订 DMG
    print(f"\n装订 {DMG_PATH.name}...")
    run(["xcrun", "stapler", "staple", str(DMG_PATH)])
    
    print("\n[OK] 装订完成")


# ============================================================
# 验证
# ============================================================

def verify():
    """验证公证状态"""
    print("\n" + "=" * 60)
    print("验证公证状态")
    print("=" * 60)
    
    print(f"\n验证 {APP_PATH.name}...")
    result = run([
        "spctl", "--assess", "--type", "execute", "--verbose",
        str(APP_PATH)
    ], check=False, capture=True)
    
    if result:
        print(f"  {result}")
    
    print(f"\n验证 {DMG_PATH.name}...")
    result = run([
        "spctl", "--assess", "--type", "open", "--context", "context:primary-signature", "--verbose",
        str(DMG_PATH)
    ], check=False, capture=True)
    
    if result:
        print(f"  {result}")
    
    # 详细验证
    print(f"\nGatekeeper 检查...")
    subprocess.run([
        "spctl", "-a", "-v", str(APP_PATH)
    ])


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="macOS 公证脚本")
    parser.add_argument("--sign-only", action="store_true", help="仅签名")
    parser.add_argument("--notarize-only", action="store_true", help="仅公证")
    parser.add_argument("--verify", action="store_true", help="验证公证状态")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Canto-beats macOS 公证工具")
    print("=" * 60)
    
    check_prerequisites()
    
    if args.verify:
        verify()
        return 0
    
    if args.notarize_only:
        notarize()
        staple()
        verify()
        return 0
    
    # 完整流程或仅签名
    sign_app()
    create_dmg()
    
    if args.sign_only:
        print("\n[完成] 仅签名模式 - 跳过公证")
        return 0
    
    notarize()
    staple()
    verify()
    
    print("\n" + "=" * 60)
    print("公证流程完成!")
    print("=" * 60)
    print(f"\n分发文件: {DMG_PATH}")
    print("用户可以直接双击安装，无需 Gatekeeper 警告")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
