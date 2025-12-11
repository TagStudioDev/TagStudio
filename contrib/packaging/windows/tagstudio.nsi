; NSIS installer script for TagStudio
; Pass overrides when calling makensis, e.g.:
;   makensis.exe /DVERSION=9.5.6 /DBUILD_DIR="C:\path\to\dist\pyinstaller\windows\TagStudio" tagstudio.nsi

!include "MUI2.nsh"

!ifndef APP_NAME
!define APP_NAME "TagStudio"
!endif

!ifndef VERSION
!define VERSION "0.0.0"
!endif

!ifndef BUILD_DIR
!define BUILD_DIR "..\..\..\dist\pyinstaller\windows\TagStudio"
!endif

!ifndef OUTPUT_DIR
!define OUTPUT_DIR "..\..\..\dist"
!endif

!ifndef INSTALLER_NAME
!define INSTALLER_NAME "${OUTPUT_DIR}\${APP_NAME}-${VERSION}-win-setup.exe"
!endif

Name "${APP_NAME}"
OutFile "${INSTALLER_NAME}"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin
BrandingText "${APP_NAME} ${VERSION}"
Icon "..\..\..\src\tagstudio\resources\icon.ico"
UninstallIcon "..\..\..\src\tagstudio\resources\icon.ico"

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "${BUILD_DIR}\*.*"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_NAME}.exe"
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_NAME}.exe"

  WriteRegStr HKCU "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"

  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\${APP_NAME}"
SectionEnd

