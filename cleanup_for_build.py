#!/usr/bin/env python3
"""清理不需要打包的文件（創建清單，不實際刪除）"""

from pathlib import Path
import json

def scan_unnecessary_files():
    """掃描不需要打包的文件"""
    
    unnecessary = {
        'test_files': [],
        'debug_files': [],
        'build_files': [],
        'doc_files': [],
        'backup_files': [],
        'temp_files': [],
        'example_files': [],
    }
    
    root = Path('.')
    
    for file in root.rglob('*'):
        if file.is_file():
            # 跳過特定目錄
            if any(skip in str(file) for skip in ['venv', '.git', '__pycache__', 'dist', 'build']):
                continue
            
            name = file.name
            path_str = str(file)
            
            # 測試文件
            if name.startswith('test_') or name.endswith('_test.py') or 'tests/' in path_str:
                unnecessary['test_files'].append(str(file))
            
            # 調試文件
            elif name.startswith(('debug_', 'diagnose_', 'reproduce_', 'check_', 'analyze_')):
                unnecessary['debug_files'].append(str(file))
            
            # 構建文件
            elif name.startswith(('build_', 'setup_', 'install_')) and name.endswith('.py'):
                if name != 'build_silicon_macos.py':  # 保留主構建腳本
                    unnecessary['build_files'].append(str(file))
            
            # 文檔文件
            elif name.endswith(('.md', '.rst', '.pdf', '.txt')) and name not in ['requirements.txt']:
                unnecessary['doc_files'].append(str(file))
            
            # 備份文件
            elif name.endswith(('.backup', '.bak', '.old', '_old.py')):
                unnecessary['backup_files'].append(str(file))
            
            # 臨時文件
            elif name in ['crash_log.txt', 'debug_log.txt', 'error_log.txt', 'components.json', 'firebase.json']:
                unnecessary['temp_files'].append(str(file))
            
            # 示例文件
            elif 'examples/' in path_str or 'demos/' in path_str:
                unnecessary['example_files'].append(str(file))
    
    return unnecessary

def main():
    print("=" * 80)
    print("掃描不需要打包的文件")
    print("=" * 80)
    
    files = scan_unnecessary_files()
    
    total = 0
    for category, file_list in files.items():
        count = len(file_list)
        total += count
        print(f"\n{category.replace('_', ' ').title()}: {count} 個")
        for f in sorted(file_list)[:5]:
            print(f"  • {f}")
        if count > 5:
            print(f"  ... 還有 {count - 5} 個")
    
    print(f"\n{'=' * 80}")
    print(f"總計: {total} 個文件不需要打包")
    print("=" * 80)
    
    # 保存清單
    output_file = Path('unnecessary_files.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 清單已保存到: {output_file}")
    print("\n💡 這些文件不會影響打包，PyInstaller 只會打包 src/ 和 public/")
    print("   如果想清理項目，可以手動刪除這些文件")

if __name__ == "__main__":
    main()

