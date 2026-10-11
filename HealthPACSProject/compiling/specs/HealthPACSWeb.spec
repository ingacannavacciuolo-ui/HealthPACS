# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../../HealthPACSWeb.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/Projects/HealthPACS/HealthPACSProject/library', 'library'), ('D:/Projects/HealthPACS/HealthPACSProject/templates', 'templates'), ('D:/Projects/HealthPACS/HealthPACSProject/static', 'static')],
    hiddenimports=['engineio.async_drivers.threading'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pysqlite2', 'MySQLdb'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HealthPACSWeb',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HealthPACSWeb',
)
