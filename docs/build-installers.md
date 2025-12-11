# Building Installers

This repo includes helper scripts to create platform installers from the existing PyInstaller spec. Builds are expected to run on their native OS (Windows for NSIS, macOS for DMG, Linux for AppImage).

## Prerequisites
- Python 3.12 with project dependencies installed (`pip install .` or `pip install -e .[dev]`)
- PyInstaller available (included in `[dev]` extras)
- Assets already in the repo under `src/tagstudio/resources`

### Windows
- [NSIS](https://nsis.sourceforge.io/Main_Page) with `makensis.exe` on `PATH`
- Optional: `signtool.exe` plus certificate (`TS_SIGNTOOL`, `TS_CERT_PATH`, `TS_CERT_PASS`)

### macOS
- Xcode Command Line Tools (for `hdiutil` and `codesign`)
- Optional: signing identity via `TS_IDENTITY`

### Linux
- `linuxdeploy` and `linuxdeploy-plugin-qt` AppImages available/executable
- Optional: [`fpm`](https://fpm.readthedocs.io/) for `.deb` output

## PyInstaller (all platforms)
Runs the shared spec and writes to `dist/pyinstaller/<platform>`:

```sh
python contrib/packaging/build_pyinstaller.py --clean
# add --portable to bundle binaries/datas directly
# (internally sets TS_PORTABLE=1 for the PyInstaller spec)
```

## Windows (.exe installer)
```pwsh
pwsh -File contrib/packaging/windows/build_windows.ps1
# add -Portable for a portable PyInstaller build
# add -Clean to clear PyInstaller cache
```
Outputs: `dist/TagStudio-<version>-win-setup.exe`

Signing (optional): set `TS_SIGNTOOL`, `TS_CERT_PATH`, and `TS_CERT_PASS` before running; the script signs the staged EXE and final installer if available.

## macOS (.dmg)
```bash
bash contrib/packaging/macos/build_dmg.sh
```
Outputs: `dist/TagStudio-<version>-macOS.dmg`

Signing (optional): set `TS_IDENTITY="Developer ID Application: Your Name (TEAMID)"` to sign the `.app` before packing. Notarization should be performed separately using `notarytool` after the DMG is produced.

## Linux (AppImage, optional .deb)
```bash
LINUXDEPLOY=./linuxdeploy-x86_64.AppImage \
LINUXDEPLOY_PLUGIN_QT=./linuxdeploy-plugin-qt-x86_64.AppImage \
bash contrib/packaging/linux/build_appimage.sh
```
Outputs: `dist/TagStudio-<version>-linux.AppImage`

If `fpm` is available, a `.deb` is also produced with the same version. Icon and desktop entry are pulled from `src/tagstudio/resources`.
