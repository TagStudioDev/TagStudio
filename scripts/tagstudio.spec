#!/usr/bin/env -S python -m PyInstaller
# vi: ft=python
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import argparse
import platform
from argparse import ArgumentParser
from pathlib import Path
from tomllib import load

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.osx import BUNDLE

parser = ArgumentParser()
# HACK: Without this, the script will fail if empty arguments are passed.
parser.add_argument("_", nargs="*", help=argparse.SUPPRESS)
parser.add_argument("--portable", action="store_true")
options = parser.parse_args()

with open("pyproject.toml", "rb") as file:
    pyproject = load(file)["project"]

system = platform.system()

project_root = Path("..", "src/tagstudio")
name = pyproject["name"] if system == "Windows" else "tagstudio"
icon = None
if system == "Windows":
    icon = Path(project_root, "resources/icon.ico")
elif system == "Darwin":
    icon = Path(project_root, "resources/icon.icns")


datafiles = [
    (f"{project_root}/qt/*.json", "tagstudio/qt"),
    (f"{project_root}/qt/*.qrc", "tagstudio/qt"),
    (f"{project_root}/resources", "tagstudio/resources"),
]

a = Analysis(
    [Path(project_root, "main.py")],
    pathex=[],
    binaries=[],
    datas=datafiles,
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
if options.portable:
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
    exclude_binaries=not options.portable,
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
    if options.portable
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
