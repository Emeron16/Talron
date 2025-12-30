# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

spec_root = os.path.abspath(SPECPATH)
project_root = os.path.dirname(spec_root)

datas = [(os.path.join(project_root, 'src'), 'src'), (os.path.join(project_root, 'src/ui/assets'), 'src/ui/assets')]
binaries = []
hiddenimports = ['tkinter', 'pygame', 'cv2', 'PIL', 'dataclasses', 'typing_extensions', 'dataclasses_json']
# Skip collect_all for src as it's not a package

a = Analysis(
    [os.path.join(project_root, 'run_game_gui.py')],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Talron Word Search',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(project_root, 'app_icon.icns')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Talron Word Search',
)
app = BUNDLE(
    coll,
    name='Talron Word Search.app',
    icon=os.path.join(project_root, 'app_icon.icns'),
    bundle_identifier=None,
)
