# -*- mode: python ; coding: utf-8 -*-
# vi: ft=python


import sys
from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE


name = 'TagStudio' if sys.platform == 'win32' else 'tagstudio'
icon = None
if sys.platform == 'win32':
    icon = 'tagstudio/resources/icon.ico'
elif sys.platform == 'darwin':
    icon = 'tagstudio/resources/icon.icns'


a = Analysis(
    ['tagstudio/tag_studio.py'],
    pathex=[],
    binaries=[],
    datas=[('tagstudio/resources', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    bootloader_ignore_signals=False,
    console=True,
    hide_console='hide-early',
    disable_windowed_traceback=False,
    debug=False,
    name=name,
    exclude_binaries=True,
    icon=icon,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    strip=False,
    upx=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name=name,
    strip=False,
    upx=True,
    upx_exclude=[],
)

app = BUNDLE(
    coll,
    name='TagStudio.app',
    icon=icon,
    bundle_identifier='com.github.tagstudiodev',
    version='0.0.0',
    info_plist={
        'NSAppleScriptEnabled': False,
        'NSPrincipalClass': 'NSApplication',
    }
)
