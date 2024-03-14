# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['LEMS_DataENTRY_L2.py'],
    pathex=['C:\\Users\\Jaden\\Documents\\GitHub\\Data_Processing_aprogit\\Data-Processing-Software\\LEMS'],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name='LEMS_DataENTRY_L2',
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
)
