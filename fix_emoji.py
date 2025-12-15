# -*- coding: utf-8 -*-
"""Remove emoji from Python files to prevent GBK encoding errors on Windows."""

import os

# Define emoji replacements
replacements = {
    '\U0001F3B5': '',      # 🎵
    '\u26A0\uFE0F': '[!]', # ⚠️
    '\u26A0': '[!]',       # ⚠
    '\u2705': '[OK]',      # ✅
    '\u274C': '[X]',       # ❌
    '\U0001F50D': '',      # 🔍
    '\U0001F680': '',      # 🚀
    '\U0001F310': '',      # 🌐
    '\U0001F4B3': '',      # 💳
    '\u2139\uFE0F': '[i]', # ℹ️
    '\u2139': '[i]',       # ℹ
    '\uFE0F': '',          # variation selector
}

# Files to process
files = [
    'src/ui/license_dialog.py',
    'src/ui/main_window.py',
    'src/ui/notification_system.py',
    'src/ui/style_panel.py',
    'src/ui/timeline_tracks.py',
    'src/utils/video_utils.py',
    'src/models/qwen_llm.py',
    'src/core/hardware_detector.py',
    'src/ui/transcription_worker_v2.py',
]

def fix_file(filepath):
    """Remove emoji from a single file."""
    if not os.path.exists(filepath):
        print(f'  Not found: {filepath}')
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for emoji, replacement in replacements.items():
        content = content.replace(emoji, replacement)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  Fixed: {filepath}')
        return True
    else:
        print(f'  No emoji: {filepath}')
        return False

if __name__ == '__main__':
    print('Removing emoji from Python files...')
    fixed_count = 0
    for f in files:
        if fix_file(f):
            fixed_count += 1
    print(f'\nDone. Fixed {fixed_count} files.')
