#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DIST_ROOT="${DIST_ROOT:-$ROOT/dist/pyinstaller}"
BUILD_ROOT="${BUILD_ROOT:-$ROOT/build/pyinstaller}"
CLEAN_FLAG="${CLEAN_FLAG:-}"
PYTHON="${PYTHON:-python}"
SKIP_BUILD="${SKIP_BUILD:-}"

version="$($PYTHON - <<'PY'
import pathlib, tomllib
pyproject = tomllib.loads(pathlib.Path("pyproject.toml").read_text("utf-8"))
print(pyproject["project"]["version"])
PY
)"

if [[ -z "$SKIP_BUILD" ]]; then
  echo "==> Building PyInstaller bundle..."
  "$PYTHON" "$ROOT/contrib/packaging/build_pyinstaller.py" --distpath "$DIST_ROOT" --workpath "$BUILD_ROOT" ${CLEAN_FLAG:+--clean}
else
  echo "==> Skipping PyInstaller build (SKIP_BUILD set)"
fi

APP_STAGE="$DIST_ROOT/darwin/TagStudio.app"
if [[ ! -d "$APP_STAGE" ]]; then
  echo "App bundle not found at $APP_STAGE"
  exit 1
fi

if [[ -n "${TS_IDENTITY:-}" ]]; then
  echo "==> Codesigning with identity: $TS_IDENTITY"
  codesign --deep --force --options runtime --sign "$TS_IDENTITY" "$APP_STAGE"
else
  echo "==> Skipping codesign (set TS_IDENTITY to enable)"
fi

DMG_DIR="$ROOT/dist"
mkdir -p "$DMG_DIR"
arch="$(uname -m)"
DMG_PATH="$DMG_DIR/TagStudio-${version}-macOS-${arch}.dmg"

echo "==> Creating DMG..."
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

APP_BUNDLE_DIR="$TMP_DIR/TagStudio"
mkdir -p "$APP_BUNDLE_DIR"
cp -R "$APP_STAGE" "$APP_BUNDLE_DIR/"

hdiutil create -volname "TagStudio" -srcfolder "$APP_BUNDLE_DIR" -ov -format UDZO "$DMG_PATH"

echo "==> Output: $DMG_PATH"
echo "Note: Notarization not performed. Set TS_IDENTITY and run notarytool separately if needed."
