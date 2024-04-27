@echo off
echo Building windows executable...


set TAGSTUDIO_NAME=TagStudio
set TAGSTUDIO_DIR=tagstudio
set TAGSTUDIO_DIR_RESOURCES=%TAGSTUDIO_DIR%/resources
set TAGSTUDIO_ICON=%TAGSTUDIO_DIR%/resources/icon.ico
set TAGSTUDIO_SRC=%TAGSTUDIO_DIR%/src
set TAGSTUDIO_MAIN=%TAGSTUDIO_DIR%/tag_studio.py

set COMMAND=PyInstaller --name "%TAGSTUDIO_NAME%" --icon "%TAGSTUDIO_ICON%" --add-data "%TAGSTUDIO_DIR_RESOURCES%:./resources" --add-data "%TAGSTUDIO_SRC%:./src" --distpath "%DIST_PATH%" -p "%TAGSTUDIO_DIR%" --console --onefile "%TAGSTUDIO_MAIN%" -y
call .venv\Scripts\activate.bat
%COMMAND%
deactivate