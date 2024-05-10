@echo off
set TAGSTUDIO_NAME=TagStudio
set TAGSTUDIO_DIR=tagstudio
set TAGSTUDIO_DIR_RESOURCES=%TAGSTUDIO_DIR%/resources
set TAGSTUDIO_ICON=%TAGSTUDIO_DIR%/resources/icon.ico
set TAGSTUDIO_SRC=%TAGSTUDIO_DIR%/src
set TAGSTUDIO_MAIN=%TAGSTUDIO_DIR%/tag_studio.py
set BUILD_MODE=--onedir


if "%1" == "--help" (
    echo run "%~nx0" for normal Build
    echo run "%~nx0 --portable" for Build packaged into one file
    goto end
)
if "%1" == "--portable" (
    echo Building portable executable...
    set BUILD_MODE=--onefile
    goto run
)
if not "%1" == "" (
    echo Invalid argument run "%~nx0 --help" for help
    goto end
)
:run
echo Building executable...
set COMMAND=PyInstaller --name "%TAGSTUDIO_NAME%" --icon "%TAGSTUDIO_ICON%" --add-data "%TAGSTUDIO_DIR_RESOURCES%:./resources" --add-data "%TAGSTUDIO_SRC%:./src" -p "%TAGSTUDIO_DIR%" --console %BUILD_MODE% "%TAGSTUDIO_MAIN%" -y
call .venv\Scripts\activate.bat
%COMMAND%
deactivate
:end
