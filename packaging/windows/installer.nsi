; ==============================================================================
; MemScreen Windows Installer Script
;
; This script creates a Windows installer using NSIS (Nullsoft Scriptable Install System)
;
; Prerequisites:
; - NSIS 3.0+: https://nsis.sourceforge.io/
; - SWORD plug-in for x64 detection (included in modern NSIS)
;
; Build:
;   makensis installer.nsi
;
; Usage:
;   Run the generated .exe installer on Windows
; ==============================================================================

!include "MUI2.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"

; ==============================================================================
; Configuration
; ==============================================================================

!define APPNAME "MemScreen"
!define VERSION "0.5.0"
!define PUBLISHER "Jixiang Luo"
!define WEBSITE "https://github.com/smileformylove/MemScreen"

; Installer filenames
!define INSTALLER_NAME "MemScreen-Setup-${VERSION}.exe"
!define UNINSTALLER_NAME "uninstall.exe"

; Installation directories
!define INSTALL_DIR "$LOCALAPPDATA\${APPNAME}"
!define OLLAMA_INSTALL_DIR "$APPDATA\Ollama"

; Registry keys
!define REGKEY "Software\${APPNAME}"
!define UNINSTALL_REGKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

; ==============================================================================
; Installer Settings
; ==============================================================================

Name "${APPNAME}"
OutFile "${INSTALLER_NAME}"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

SetCompressor /SOLID lzma

; ==============================================================================
; Version Information
; ==============================================================================

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "FileDescription" "${APPNAME} - AI-Powered Visual Memory"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "© 2026 ${PUBLISHER}"
VIAddVersionKey "OriginalFilename" "${INSTALLER_NAME}"

; ==============================================================================
; Interface Settings
; ==============================================================================

!define MUI_ABORTWARNING
!define MUI_ICON "assets\logo.ico"
!define MUI_UNICON "assets\logo.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\logo.bmp" ; Optional header image

; ==============================================================================
; Pages
; ==============================================================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Completion page with options
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApp"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View documentation"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION "ShowDocumentation"
!define MUI_FINISHPAGE_LINK "Visit ${APPNAME} on GitHub"
!define MUI_FINISHPAGE_LINK_LOCATION "${WEBSITE}"

!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; ==============================================================================
; Languages
; ==============================================================================

!insertmacro MUI_LANGUAGE "English"

; ==============================================================================
; Sections
; ==============================================================================

; Section: Main Application
Section "Main Application" SEC01
  SectionIn RO ; Always install

  SetOutPath $INSTDIR

  ; Install main files
  File /r "dist\MemScreen\*.*"

  ; Create directories
  CreateDirectory "$INSTDIR\data"
  CreateDirectory "$INSTDIR\logs"

  ; Create shortcuts
  CreateShortcut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\MemScreen.exe" \
      "" "" "${APPNAME} - AI-Powered Visual Memory"

  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\MemScreen.exe" \
      "" "" "${APPNAME} - AI-Powered Visual Memory"

  ; Write uninstaller
  WriteUninstaller "$INSTDIR\${UNINSTALLER_NAME}"

  ; Write registry keys
  WriteRegStr HKLM "${REGKEY}" "InstallPath" $INSTDIR
  WriteRegStr HKLM "${REGKEY}" "Version" "${VERSION}"

  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "UninstallString" "$INSTDIR\${UNINSTALLER_NAME}"
  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "DisplayIcon" "$INSTDIR\MemScreen.exe"
  WriteRegStr HKLM "${UNINSTALL_REGKEY}" "URLInfoAbout" "${WEBSITE}"
  WriteRegDWORD HKLM "${UNINSTALL_REGKEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTALL_REGKEY}" "NoRepair" 1

  ; Create file association
  WriteRegStr HKCR ".memscreen" "" "${APPNAME} Database File"
  WriteRegStr HKCR ".memscreen" "Content Type" "application/x-memscreen"
  WriteRegStr HKCR "${APPNAME} Database File\DefaultIcon" "" "$INSTDIR\MemScreen.exe,0"
  WriteRegStr HKCR "${APPNAME} Database File\shell\open\command" "" '$INSTDIR\MemScreen.exe "%1"'

SectionEnd

; Section: Ollama
Section "Ollama AI Runtime" SEC02
  SectionIn RO ; Always install

  ; Check if Ollama is already installed
  ReadRegStr $0 HKLM "Software\Ollama" "InstallPath"
  ${If} $0 == ""
    ; Ollama not found - download and install
    SetOutPath $TEMP
    DetailPrint "Downloading Ollama..."
    NSISdl::download /QUIET "https://ollama.com/download/Ollama-windows-amd64.zip" "$TEMP\ollama.zip"
    Pop $0 ; Return value

    ${If} $0 == "success"
      DetailPrint "Extracting Ollama..."
      nsisunz::UnzipToLog "$TEMP\ollama.zip" "$TEMP\ollama_temp"
      Pop $0

      DetailPrint "Installing Ollama..."
      CopyFiles "$TEMP\ollama_temp\*" "${OLLAMA_INSTALL_DIR}\" /SILENT

      ; Add to PATH
      EnVar::SetCurrentValue "PATH" "%PATH%;${OLLAMA_INSTALL_DIR}"
      EnVar::SetValue "PATH" "%PATH%;${OLLAMA_INSTALL_DIR}"

      ; Clean up
      Delete "$TEMP\ollama.zip"
      RMDir /r "$TEMP\ollama_temp"
    ${Else}
      MessageBox MB_OK "Failed to download Ollama. Please install manually from https://ollama.com/"
    ${EndIf}
  ${Else}
    DetailPrint "Ollama already installed at: $0"
  ${EndIf}

SectionEnd

; Section: AI Models
Section "AI Models (~3GB)" SEC03
  SectionIn RO ; Always install

  DetailPrint "Checking Ollama service..."

  ; Start Ollama service if not running
  nsExec::ExecToLog 'tasklist /FI "IMAGENAME eq ollama.exe"'
  Pop $0
  ${If} $0 != 0
    DetailPrint "Starting Ollama service..."
    ExecShell "" '"${OLLAMA_INSTALL_DIR}\ollama.exe"' "serve" SW_SHOWNOACTIVATE
    Sleep 5000 ; Wait for service to start
  ${EndIf}

  DetailPrint "Downloading AI models..."

  ; Download vision model
  DetailPrint "Downloading qwen2.5vl:3b (vision model, ~2GB)..."
  nsExec::ExecToLog '"${OLLAMA_INSTALL_DIR}\ollama.exe" pull qwen2.5vl:3b'
  Pop $0

  ; Download embedding model
  DetailPrint "Downloading mxbai-embed-large (embedding model, ~1GB)..."
  nsExec::ExecToLog '"${OLLAMA_INSTALL_DIR}\ollama.exe" pull mxbai-embed-large'
  Pop $0

SectionEnd

; Section: Start Menu Shortcuts
Section "Start Menu Shortcuts" SEC04
  CreateDirectory "$SMPROGRAMS\${APPNAME}"

  ; Create various shortcuts
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\MemScreen.exe"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\${UNINSTALLER_NAME}"

  ; Add "Read Me" shortcut
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Documentation.lnk" "https://github.com/smileformylove/MemScreen"

SectionEnd

; ==============================================================================
; Section Descriptions
; ==============================================================================

LangString DESC_SEC01 ${LANG_ENGLISH} "Main application files (required)"
LangString DESC_SEC02 ${LANG_ENGLISH} "Ollama AI Runtime for running local models (required)"
LangString DESC_SEC03 ${LANG_ENGLISH} "Download required AI models (~3GB download)"
LangString DESC_SEC04 ${LANG_ENGLISH} "Create shortcuts in Start Menu"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} $(DESC_SEC01)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} $(DESC_SEC02)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} $(DESC_SEC03)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC04} $(DESC_SEC04)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; ==============================================================================
; Functions
; ==============================================================================

Function .onInit
  ; Check Windows version
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_OK|MB_ICONSTOP "${APPNAME} requires Windows 10 or later."
    Abort
  ${EndIf}

  ; Check for running instance
  FindProcDLL::FindProc "MemScreen.exe"
  ${If} $R0 == "1"
    MessageBox MB_OK|MB_ICONEXCLAMATION "${APPNAME} is already running. Please close it first."
    Abort
  ${EndIf}

FunctionEnd

Function LaunchApp
  ExecShell "" "$INSTDIR\MemScreen.exe"
FunctionEnd

Function ShowDocumentation
  ExecShell "open" "${WEBSITE}/blob/main/README.md"
FunctionEnd

; ==============================================================================
; Uninstaller Section
; ==============================================================================

Section "Uninstall"
  ; Stop Ollama service
  DetailPrint "Stopping Ollama service..."
  nsExec::ExecToLog 'taskkill /F /IM ollama.exe'
  Pop $0

  ; Remove files
  DetailPrint "Removing application files..."
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  Delete "$DESKTOP\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Documentation.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"

  ; Remove registry entries
  DeleteRegKey HKLM "${REGKEY}"
  DeleteRegKey HKLM "${UNINSTALL_REGKEY}"
  DeleteRegKey HKCR ".memscreen"
  DeleteRegKey HKCR "${APPNAME} Database File"

  ; Display completion message
  MessageBox MB_OK "${APPNAME} has been uninstalled successfully."

SectionEnd

Function un.onInit
  MessageBox MB_YESNO "Are you sure you want to completely uninstall ${APPNAME}?" IDYES +2
  Abort
FunctionEnd
