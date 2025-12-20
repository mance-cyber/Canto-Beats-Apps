#!/usr/bin/env python3
"""全面分析項目文件架構"""

import os
import sys
from pathlib import Path
from collections import defaultdict

def analyze_imports(file_path):
    """分析文件的導入"""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('from ') or line.startswith('import '):
                    imports.add(line)
    except:
        pass
    return imports

def scan_directory(root_dir):
    """掃描目錄結構"""
    structure = {
        'python_files': [],
        'resource_files': [],
        'config_files': [],
        'doc_files': [],
        'test_files': [],
        'build_files': [],
        'other_files': []
    }
    
    for root, dirs, files in os.walk(root_dir):
        # 跳過
        if any(skip in root for skip in ['venv', '.git', '__pycache__', 'build', 'dist', '.pytest_cache']):
            continue
            
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(root_dir)
            
            if file.endswith('.py'):
                if 'test' in str(rel_path).lower():
                    structure['test_files'].append(rel_path)
                elif any(x in file for x in ['build', 'setup', 'install']):
                    structure['build_files'].append(rel_path)
                else:
                    structure['python_files'].append(rel_path)
            elif file.endswith(('.json', '.txt', '.csv')):
                structure['resource_files'].append(rel_path)
            elif file.endswith(('.md', '.rst', '.pdf')):
                structure['doc_files'].append(rel_path)
            elif file.endswith(('.yaml', '.yml', '.toml', '.ini', '.cfg', '.spec')):
                structure['config_files'].append(rel_path)
            elif file.endswith(('.png', '.jpg', '.icns', '.ico')):
                structure['resource_files'].append(rel_path)
            else:
                structure['other_files'].append(rel_path)
    
    return structure

def analyze_core_modules():
    """分析核心模塊"""
    sys.path.insert(0, 'src')
    
    core_modules = {
        'ui': [
            'ui.main_window',
            'ui.avplayer_widget',
            'ui.video_player',
            'ui.timeline_editor',
            'ui.style_control_panel',
            'ui.download_dialog',
        ],
        'models': [
            'models.whisper_asr',
            'models.qwen_llm',
            'models.vad_processor',
            'models.translation_model',
        ],
        'pipeline': [
            'pipeline.subtitle_pipeline_v2',
        ],
        'core': [
            'core.config',
            'core.hardware_detector',
        ],
        'utils': [
            'utils.audio_utils',
            'utils.video_utils',
        ],
        'subtitle': [
            'subtitle.style_processor',
            'subtitle.exporter',
        ]
    }
    
    results = {}
    for category, modules in core_modules.items():
        results[category] = {}
        for mod in modules:
            try:
                __import__(mod)
                results[category][mod] = 'OK'
            except Exception as e:
                results[category][mod] = f'ERROR: {str(e)[:50]}'
    
    return results

def main():
    print("=" * 80)
    print("Canto-Beats 項目架構分析")
    print("=" * 80)
    
    root = Path('.')
    
    # 1. 掃描文件結構
    print("\n📁 文件結構掃描...")
    structure = scan_directory(root)
    
    print(f"\n✅ Python 文件 ({len(structure['python_files'])} 個):")
    for f in sorted(structure['python_files'])[:20]:
        print(f"  • {f}")
    if len(structure['python_files']) > 20:
        print(f"  ... 還有 {len(structure['python_files']) - 20} 個")
    
    print(f"\n✅ 資源文件 ({len(structure['resource_files'])} 個):")
    for f in sorted(structure['resource_files'])[:15]:
        print(f"  • {f}")
    if len(structure['resource_files']) > 15:
        print(f"  ... 還有 {len(structure['resource_files']) - 15} 個")
    
    print(f"\n📝 文檔文件 ({len(structure['doc_files'])} 個):")
    for f in sorted(structure['doc_files'])[:10]:
        print(f"  • {f}")
    if len(structure['doc_files']) > 10:
        print(f"  ... 還有 {len(structure['doc_files']) - 10} 個")
    
    print(f"\n🧪 測試文件 ({len(structure['test_files'])} 個):")
    for f in sorted(structure['test_files']):
        print(f"  • {f}")
    
    print(f"\n🔧 構建文件 ({len(structure['build_files'])} 個):")
    for f in sorted(structure['build_files']):
        print(f"  • {f}")
    
    # 2. 分析核心模塊
    print("\n" + "=" * 80)
    print("核心模塊檢查")
    print("=" * 80)
    
    modules = analyze_core_modules()
    for category, mods in modules.items():
        print(f"\n{category.upper()}:")
        for mod, status in mods.items():
            icon = "✅" if status == "OK" else "❌"
            print(f"  {icon} {mod}: {status}")
    
    # 3. 統計
    print("\n" + "=" * 80)
    print("統計摘要")
    print("=" * 80)
    
    total_py = len(structure['python_files'])
    total_test = len(structure['test_files'])
    total_build = len(structure['build_files'])
    total_resource = len(structure['resource_files'])
    total_doc = len(structure['doc_files'])
    
    print(f"\n總計:")
    print(f"  • Python 源碼: {total_py} 個")
    print(f"  • 測試文件: {total_test} 個")
    print(f"  • 構建腳本: {total_build} 個")
    print(f"  • 資源文件: {total_resource} 個")
    print(f"  • 文檔文件: {total_doc} 個")
    
    # 4. 打包建議
    print("\n" + "=" * 80)
    print("打包建議")
    print("=" * 80)
    
    print("\n✅ 必須包含:")
    print("  • src/ (所有源碼)")
    print("  • public/ (圖標、資源)")
    print("  • main.py (入口)")
    
    print("\n❌ 不需要包含:")
    print("  • test*.py (測試文件)")
    print("  • *_test.py (測試文件)")
    print("  • debug*.py (調試腳本)")
    print("  • reproduce*.py (問題重現腳本)")
    print("  • build*.py (構建腳本)")
    print("  • *.md (文檔)")
    print("  • *.backup (備份文件)")
    print("  • venv/ (虛擬環境)")
    print("  • .git/ (版本控制)")
    print("  • __pycache__/ (緩存)")

if __name__ == "__main__":
    main()

