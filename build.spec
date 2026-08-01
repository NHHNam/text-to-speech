# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Automatically find all internal assets/JSONs inside the 'vieneu' and 'sea_g2p' packages
vieneu_datas = collect_data_files('vieneu')
sea_g2p_datas = collect_data_files('sea_g2p')

# Include our QML UI file, the offline model cache folder, and the package assets
added_files = [
    ('main.qml', '.'),
    ('hf_cache', 'hf_cache'),
    ('tts_process.py', '.'),   # subprocess worker — runs in its own process to free ONNX memory
    ('voices_output.txt', '.'),
] + vieneu_datas + sea_g2p_datas

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['vieneu', 'sea_g2p'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    'assets\\splash.jpg',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    [],
    exclude_binaries=True,
    name='VanBanThanhGiongNoi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False, # Set to False to hide the terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\VanBanThanhGiongNoi.ico' # You can add an icon if you have one
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='VanBanThanhGiongNoi',
)
