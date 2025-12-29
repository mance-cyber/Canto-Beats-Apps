#!/usr/bin/env python3
"""
Apple Silicon 優化 - 快速修復腳本

自動應用關鍵優化到 Canto-Beats 代碼庫。
執行前請備份代碼！

使用方法:
    python apply_apple_silicon_fixes.py --dry-run  # 預覽變更
    python apply_apple_silicon_fixes.py --apply    # 應用變更
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# ==================== 配置 ====================
PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT / "backups" / "pre_apple_silicon_optimization"

# ==================== 修復定義 ====================
FIXES = [
    {
        "name": "修復 MPS VRAM 檢測",
        "file": "src/core/hardware_detector.py",
        "line_range": (153, 170),
        "old_code": '''        # 1. Check Apple Silicon MPS (Metal Performance Shaders)
        try:
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                logger.info("Apple MPS (Metal) detected - Apple Silicon GPU")
                # MPS shares system memory, no dedicated VRAM concept
                # Return 0 to trigger appropriate tier selection
                return "mps", 0.0
        except Exception as e:
            logger.debug(f"MPS check failed: {e}")''',
        "new_code": '''        # 1. Check Apple Silicon MPS (Metal Performance Shaders)
        try:
            if torch.backends.mps.is_available() and torch.backends.mps.is_built():
                logger.info("Apple MPS (Metal) detected - Apple Silicon GPU")
                
                # MPS shares unified memory - calculate effective VRAM (70% of system RAM)
                try:
                    import psutil
                    system_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
                    effective_vram = system_ram_gb * 0.7
                    logger.info(f"MPS effective VRAM: {effective_vram:.1f} GB (70% of {system_ram_gb:.1f} GB system RAM)")
                    return "mps", effective_vram
                except ImportError:
                    logger.warning("psutil not available, assuming 16GB effective VRAM")
                    return "mps", 16.0  # Conservative estimate for M1/M2 Macs
        except Exception as e:
            logger.debug(f"MPS check failed: {e}")''',
    },
    {
        "name": "啟用 LLM MPS 設備映射",
        "file": "src/models/qwen_llm.py",
        "line_range": (98, 102),
        "old_code": '''            # Determine quantization config based on VRAM
            model_a_kwargs = {
                "device_map": "auto" if device == "cuda" else "cpu",
                "trust_remote_code": True,
            }''',
        "new_code": '''            # Determine device map (support MPS)
            def get_device_map(device: str):
                if device == "cuda":
                    return "auto"
                elif device == "mps":
                    return "mps"  # PyTorch 2.0+ native MPS support
                else:
                    return "cpu"
            
            model_a_kwargs = {
                "device_map": get_device_map(device),
                "trust_remote_code": True,
                "torch_dtype": torch.float16 if device in ["cuda", "mps"] else torch.float32,
            }''',
    },
]

# ==================== 工具函數 ====================
def backup_file(file_path: Path):
    """備份文件到 backups 目錄"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / file_path.name
    backup_path.write_text(file_path.read_text())
    print(f"  ✅ 已備份: {backup_path}")

def apply_fix(fix: dict, dry_run: bool = True) -> bool:
    """應用單個修復"""
    file_path = PROJECT_ROOT / fix["file"]
    
    if not file_path.exists():
        print(f"  ❌ 文件不存在: {file_path}")
        return False
    
    content = file_path.read_text()
    
    if fix["old_code"] not in content:
        print(f"  ⚠️  未找到目標代碼，可能已修復或代碼已變更")
        return False
    
    if dry_run:
        print(f"  📝 [預覽] 將替換 {fix['line_range'][1] - fix['line_range'][0] + 1} 行代碼")
        return True
    
    # 備份原文件
    backup_file(file_path)
    
    # 應用修復
    new_content = content.replace(fix["old_code"], fix["new_code"])
    file_path.write_text(new_content)
    
    print(f"  ✅ 已應用修復")
    return True

# ==================== 主程序 ====================
def main():
    parser = argparse.ArgumentParser(description="Apple Silicon 優化快速修復")
    parser.add_argument("--dry-run", action="store_true", help="預覽變更（不實際修改文件）")
    parser.add_argument("--apply", action="store_true", help="應用變更")
    args = parser.parse_args()
    
    if not args.dry_run and not args.apply:
        parser.print_help()
        sys.exit(1)
    
    mode = "預覽模式" if args.dry_run else "應用模式"
    print(f"\n{'='*60}")
    print(f"Apple Silicon 優化 - {mode}")
    print(f"{'='*60}\n")
    
    success_count = 0
    for i, fix in enumerate(FIXES, 1):
        print(f"[{i}/{len(FIXES)}] {fix['name']}")
        print(f"  文件: {fix['file']}")
        
        if apply_fix(fix, dry_run=args.dry_run):
            success_count += 1
        print()
    
    print(f"{'='*60}")
    print(f"完成: {success_count}/{len(FIXES)} 個修復成功")
    
    if args.dry_run:
        print("\n💡 使用 --apply 參數來實際應用變更")
    else:
        print(f"\n✅ 備份位置: {BACKUP_DIR}")
        print("⚠️  請運行測試確保一切正常！")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

