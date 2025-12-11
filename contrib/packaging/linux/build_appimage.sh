#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_ROOT="${DIST_ROOT:-$ROOT/dist/pyinstaller}"
BUILD_ROOT="${BUILD_ROOT:-$ROOT/build/pyinstaller}"
APPDIR="${APPDIR:-$DIST_ROOT/linux/AppDir}"
LINUXDEPLOY="${LINUXDEPLOY:-linuxdeploy-x86_64.AppImage}"
LINUXDEPLOY_PLUGIN_QT="${LINUXDEPLOY_PLUGIN_QT:-linuxdeploy-plugin-qt-x86_64.AppImage}"
FPM_FLAGS="${FPM_FLAGS:-}"

version="$(python - <<'PY'
import pathlib, tomllib
pyproject = tomllib.loads(pathlib.Path("pyproject.toml").read_text("utf-8"))
print(pyproject["project"]["version"])
PY
)"

echo "==> Building PyInstaller app..."
python "$ROOT/contrib/packaging/build_pyinstaller.py" --distpath "$DIST_ROOT" --workpath "$BUILD_ROOT" ${CLEAN_FLAG:+--clean}

platform_stage="$DIST_ROOT/linux"
stage_dir="$(find "$platform_stage" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$stage_dir" ]]; then
  echo "PyInstaller output not found in $platform_stage"
  exit 1
fi

echo "==> Preparing AppDir..."
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib/tagstudio" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -R "$stage_dir/"* "$APPDIR/usr/lib/tagstudio/"
ln -s "../lib/tagstudio/tagstudio" "$APPDIR/usr/bin/tagstudio"

cp "$ROOT/src/tagstudio/resources/tagstudio.desktop" "$APPDIR/usr/share/applications/tagstudio.desktop"
cp "$ROOT/src/tagstudio/resources/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/tagstudio.png"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/tagstudio:$LD_LIBRARY_PATH"
exec "$HERE/usr/lib/tagstudio/tagstudio" "$@"
EOF
chmod +x "$APPDIR/AppRun"

echo "==> Running linuxdeploy..."
chmod +x "$LINUXDEPLOY" "$LINUXDEPLOY_PLUGIN_QT" 2>/dev/null || true
"$LINUXDEPLOY" --appdir "$APPDIR" --desktop-file "$APPDIR/usr/share/applications/tagstudio.desktop" --icon-file "$ROOT/src/tagstudio/resources/icon.png"
"$LINUXDEPLOY_PLUGIN_QT" --appdir "$APPDIR"

"$LINUXDEPLOY" --appdir "$APPDIR" --output appimage

appimage_path="$(find "$APPDIR" -maxdepth 1 -type f -name '*.AppImage' | head -n 1)"
if [[ -z "$appimage_path" ]]; then
  appimage_path="$(find "$ROOT" -maxdepth 2 -type f -name '*.AppImage' | head -n 1)"
fi

mkdir -p "$ROOT/dist"
final_appimage="$ROOT/dist/TagStudio-${version}-linux.AppImage"
if [[ -n "$appimage_path" ]]; then
  mv "$appimage_path" "$final_appimage"
  echo "==> AppImage: $final_appimage"
else
  echo "AppImage output not found."
  exit 1
fi

if command -v fpm >/dev/null 2>&1; then
  echo "==> Building .deb via fpm..."
  fpm -s dir -t deb -n tagstudio -v "$version" \
    --prefix /opt/tagstudio \
    --after-install "$ROOT/contrib/packaging/linux/postinst.sh" \
    --description "TagStudio desktop application" \
    --url "https://docs.tagstud.io" \
    $FPM_FLAGS \
    -C "$stage_dir" .
else
  echo "==> Skipping .deb build (fpm not available)."
fi

