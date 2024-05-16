#! /usr/bin/env bash
# GETTING BASE DIR
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# SETTING UP CONSTANTS
TAGSTUDIO_NAME="TagStudio"
TAGSTUDIO_DIR="$SCRIPT_DIR/tagstudio"
TAGSTUDIO_DIR_RESOURCES="$TAGSTUDIO_DIR/resources"
TAGSTUDIO_ICON="$TAGSTUDIO_DIR/resources/icon.ico"
TAGSTUDIO_SRC="$TAGSTUDIO_DIR/src"
TAGSTUDIO_MAIN="$TAGSTUDIO_DIR/tag_studio.py"
DIST_PATH="$SCRIPT_DIR/dist"
BUILD_PATH="$SCRIPT_DIR/build"
LOGS_PATH="$BUILD_PATH/logs"

printf -- "🏁 Starting Script \n"

# CREATE VENV AND INSTALL REQUIREMENTS
printf -- "🐍 Creating Python virtual env\n"
python3 -m venv .venv 
source .venv/bin/activate

if [ ! -d $LOGS_PATH ]; then
  printf -- "📁 Creating Logs folder\n"
  mkdir -p $LOGS_PATH;
fi

printf -- "💻 Installing Requirements \n"
pip install -r requirements.txt > "$LOGS_PATH/pip.log" 2>&1
pip install PyInstaller > "$LOGS_PATH/pip.log" 2>&1


if [[ "$OSTYPE" == "darwin"* ]]; then
    printf -- "🍏 MacOS Detected \n"
    SYS_CMD="--windowed"
    OS=0
fi

SECONDS=0

# CREATE COMMAND 
printf -- "⏳ Building App \n"

COMMAND=$( python -m PyInstaller \
  --name "$TAGSTUDIO_NAME" \
  --icon "$TAGSTUDIO_ICON" \
  --add-data "$TAGSTUDIO_DIR_RESOURCES:./resources" \
  --add-data "$TAGSTUDIO_SRC:./src" \
  --distpath "$DIST_PATH" \
  -p "$TAGSTUDIO_DIR" \
  --noconsole \
  --workpath "$BUILD_PATH" \
  -y "$SYS_CMD" "$TAGSTUDIO_MAIN" \
  > "$LOGS_PATH/pyinstaller.log" 2>&1 )

duration=$SECONDS

if $COMMAND; then
  printf -- "✅ Build Successfull \n"
  printf -- "⌛ $((duration)) seconds of build\n"
    if [[ "$OS" == 0 ]]; then
      printf -- "📁 Opening App folder \n"
      open $DIST_PATH
    fi 
else
    printf -- "❌ Error Building the app\nPlease read the logs\navailable at build/logs\n"
fi

printf -- "🏁 END OF TRANSMISSION"
