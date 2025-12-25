# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src', 'src'), ('public', 'public'), ('/Users/nicleung/Public/Canto-Beats-Apps/venv_compat/lib/python3.12/site-packages/mlx/lib/mlx.metallib', 'mlx/lib')]
binaries = []
hiddenimports = ['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'torch', 'torchaudio', 'faster_whisper', 'transformers', 'cryptography', 'sentencepiece', 'accelerate', 'silero_vad', 'mlx', 'mlx.core', 'mlx.nn', 'mlx.utils', 'mlx._reprlib_fix', 'mlx_whisper', 'mlx_whisper.transcribe', 'mlx_whisper.audio', 'mlx_whisper.decoding', 'mlx_whisper.load_models', 'mlx_lm', 'mlx_lm.generate', 'mlx_lm.utils', 'opencc', 'pysrt', 'soundfile', 'pydub', 'ffmpeg', 'huggingface_hub', 'objc', 'Foundation', 'AppKit', 'AVFoundation', 'Quartz']
tmp_ret = collect_all('mlx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('mlx_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('mlx_lm')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['/Users/nicleung/Public/Canto-Beats-Apps/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthooks/rthook_mlx.py'],
    excludes=['tkinter', 'matplotlib', 'jupyter', 'IPython'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Canto-beats',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['public/icons/app_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Canto-beats',
)
app = BUNDLE(
    coll,
    name='Canto-beats.app',
    icon='public/icons/app_icon.icns',
    bundle_identifier='com.cantobeats.app',
)
