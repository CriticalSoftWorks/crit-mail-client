# -*- mode: python ; coding: utf-8 -*-
import sys

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    name='CritMail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == 'darwin'),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['critmail.ico'] if sys.platform == 'win32' else ['assets/critmail.png'],
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='CritMail.app',
        icon='assets/critmail.png',
        bundle_identifier='net.theintelligenceagency.critmail',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleDisplayName': 'CritMail',
            'CFBundleName': 'CritMail',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
        },
    )
