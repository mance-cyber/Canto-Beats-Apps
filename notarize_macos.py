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
        subprocess.run(cmd, check=check)
        return None


def get_env(name):
    """获取环境变量"""
    value = os.environ.get(name)
    if not value:
        print(f"错误: 环境变量 {name} 未设置")
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
    for tool in ["codesign", "notarytool", "stapler", "hdiutil"]:
        try:
            subprocess.run(["which", tool], capture_output=True, check=True)
            print(f"  [OK] {tool}")
        except subprocess.CalledProcessError:
            print(f"  [FAIL] {tool} 未找到")
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
    """签名 .app 包"""
    print("\n" + "=" * 60)
    print("Step 1: 代码签名")
    print("=" * 60)
    
    identity = get_env("SIGNING_IDENTITY")
    
    # 遍历并签名所有二进制文件
    print("\n签名所有二进制文件...")
    
    # 1. 签名所有 .dylib 和 .so 文件
    for pattern in ["**/*.dylib", "**/*.so", "**/*.framework"]:
        for file in APP_PATH.rglob(pattern.replace("**/", "")):
            if file.is_file():
                print(f"  签名: {file.name}")
                run([
                    "codesign", "--force", "--deep", "--verbose",
                    "--sign", identity,
                    "--options", "runtime",
                    "--entitlements", str(ENTITLEMENTS),
                    str(file)
                ], check=False)  # 某些可能已签名
    
    # 2. 签名主可执行文件
    main_executable = APP_PATH / "Contents" / "MacOS" / APP_NAME
    if main_executable.exists():
        print(f"\n签名主可执行文件: {main_executable.name}")
        run([
            "codesign", "--force", "--verbose",
            "--sign", identity,
            "--options", "runtime",
            "--entitlements", str(ENTITLEMENTS),
            str(main_executable)
        ])
    
    # 3. 签名整个 .app 包
    print(f"\n签名整个应用包: {APP_PATH.name}")
    run([
        "codesign", "--force", "--deep", "--verbose",
        "--sign", identity,
        "--options", "runtime",
        "--entitlements", str(ENTITLEMENTS),
        str(APP_PATH)
    ])
    
    # 验证签名
    print("\n验证签名...")
    run(["codesign", "--verify", "--deep", "--verbose", str(APP_PATH)])
    
    print("\n[OK] 签名完成")


# ============================================================
# 创建 DMG
# ============================================================

def create_dmg():
    """创建签名的 DMG"""
    print("\n" + "=" * 60)
    print("Step 2: 创建 DMG")
    print("=" * 60)
    
    identity = get_env("SIGNING_IDENTITY")
    
    # 创建临时目录
    dmg_dir = Path("dist/dmg_temp")
    if dmg_dir.exists():
        shutil.rmtree(dmg_dir)
    dmg_dir.mkdir()
    
    # 复制 .app
    print(f"\n复制 {APP_PATH.name} 到临时目录...")
    shutil.copytree(APP_PATH, dmg_dir / APP_PATH.name)
    
    # 创建 Applications 链接
    (dmg_dir / "Applications").symlink_to("/Applications")
    
    # 删除旧 DMG
    if DMG_PATH.exists():
        DMG_PATH.unlink()
    
    # 创建 DMG
    print(f"\n创建 DMG: {DMG_PATH.name}")
    run([
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", str(dmg_dir),
        "-ov", "-format", "UDZO",
        str(DMG_PATH)
    ])
    
    # 签名 DMG
    print(f"\n签名 DMG...")
    run([
        "codesign", "--force", "--verbose",
        "--sign", identity,
        str(DMG_PATH)
    ])
    
    # 清理
    shutil.rmtree(dmg_dir)
    
    print(f"\n[OK] DMG 创建完成: {DMG_PATH}")


# ============================================================
# 公证
# ============================================================

def notarize():
    """提交公证"""
    print("\n" + "=" * 60)
    print("Step 3: 提交公证")
    print("=" * 60)
    
    apple_id = get_env("APPLE_ID")
    team_id = get_env("TEAM_ID")
    app_password = get_env("APP_PASSWORD")
    
    print(f"\n提交 {DMG_PATH.name} 到 Apple 公证服务...")
    print("(这可能需要 5-30 分钟)\n")
    
    run([
        "xcrun", "notarytool", "submit",
        str(DMG_PATH),
        "--apple-id", apple_id,
        "--team-id", team_id,
        "--password", app_password,
        "--wait"
    ])
    
    print("\n[OK] 公证完成")


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
