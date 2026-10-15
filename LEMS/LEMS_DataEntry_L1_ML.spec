# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['LEMS_DataEntry_L1_ML.py'],
    pathex=['/Users/user/Documents/UCET software/Data-Processing-Software/LEMS'],
    binaries=[],
    datas=[('lang', 'lang')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='LEMS_DataEntry_L1_ML',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/user/Documents/UCET software/Data-Processing-Software/LEMS/ARC-Logo.ico'],
)
