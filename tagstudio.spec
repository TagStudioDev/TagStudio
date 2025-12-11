import os
import platform

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
from tomllib import load

PORTABLE = os.environ.get("TS_PORTABLE", "0") == "1"
with open("pyproject.toml", "rb") as file:
    pyproject = load(file)["project"]

system = platform.system()

name = pyproject["name"] if system == "Windows" else "tagstudio"
icon = None
if system == "Windows":
    icon = "src/tagstudio/resources/icon.ico"
elif system == "Darwin":
    icon = "src/tagstudio/resources/icon.icns"


datafiles = [
    ("src/tagstudio/qt/*.json", "tagstudio/qt"),
    ("src/tagstudio/qt/*.qrc", "tagstudio/qt"),
    ("src/tagstudio/resources", "tagstudio/resources"),
]
pyside_datas = collect_data_files("PySide6", include_py_files=False)
pyside_binaries = collect_dynamic_libs("PySide6")

a = Analysis(
    ["src/tagstudio/main.py"],
    pathex=["src"],
    binaries=pyside_binaries,
    datas=datafiles + pyside_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    excludes=[],
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

include = [a.scripts]
if PORTABLE:
    include += (a.binaries, a.datas)
exe = EXE(
    pyz,
    *include,
    [],
    bootloader_ignore_signals=False,
    console=False,
    hide_console="hide-early",
    disable_windowed_traceback=False,
    debug=False,
    name=name,
    exclude_binaries=not PORTABLE,
    icon=icon,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
)

coll = (
    None
    if PORTABLE
    else COLLECT(
        exe,
        a.binaries,
        a.datas,
        name=name,
        strip=False,
        upx=True,
        upx_exclude=[],
    )
)

if system == "Darwin":
    app = BUNDLE(
        exe if coll is None else coll,
        name=f"{pyproject['name']}.app",
        icon=icon,
        bundle_identifier="com.cyanvoxel.tagstudio",
        version=pyproject["version"],
        info_plist={
            "NSAppleScriptEnabled": False,
            "NSPrincipalClass": "NSApplication",
        },
    )

# vi: ft=python
