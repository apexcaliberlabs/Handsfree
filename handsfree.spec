# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

base_dir = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(base_dir, 'handsfree', 'models', 'hand_landmarker.task'), 'handsfree/models'),
    (os.path.join(base_dir, 'handsfree', 'ui', 'assets', 'handsfree.png'), 'handsfree/ui/assets'),
    (os.path.join(base_dir, 'handsfree', 'ui', 'assets', 'handsfree.ico'), 'handsfree/ui/assets'),
]

# Collect mediapipe internal assets
try:
    import mediapipe
    mp_path = os.path.dirname(mediapipe.__file__)
    datas.append((mp_path, 'mediapipe'))
except Exception:
    pass

a = Analysis(
    [os.path.join(base_dir, 'handsfree', 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.ImageTk',
        'mediapipe',
        'mediapipe.tasks.python.vision',
        'cv2',
        'win32gui',
        'win32con',
        'win32api'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'scipy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Handsfree',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Run in background system tray (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_dir, 'handsfree', 'ui', 'assets', 'handsfree.ico')
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Handsfree'
)
