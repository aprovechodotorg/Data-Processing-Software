# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = []
datas += collect_data_files('gooey')
datas += collect_data_files('message')


a = Analysis(
    ['test_UI.py'],
    pathex=["C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\PEMS"],
    binaries=[],
    datas=[("C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\PEMS\\message.py", '.')],
    hiddenimports=['message'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='test_UI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
