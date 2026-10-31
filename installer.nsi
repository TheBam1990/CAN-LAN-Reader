Unicode True
!include "MUI2.nsh"
!include "x64.nsh"
Name "CAN LAN / USB Reader"
OutFile "dist/CAN-LAN-Reader-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\CAN-LAN-Reader"
InstallDirRegKey HKCU "Software\TheBam1990\CAN-LAN-Reader" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
VIProductVersion "1.2.0.0"
VIAddVersionKey /LANG=1031 "ProductName" "CAN LAN / USB Reader"
VIAddVersionKey /LANG=1031 "FileDescription" "CAN LAN / USB Reader Installation"
VIAddVersionKey /LANG=1031 "FileVersion" "1.2.0.0"
VIAddVersionKey /LANG=1031 "LegalCopyright" "TheBam1990"
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "German"
Function .onInit
 ${IfNot} ${RunningX64}
  MessageBox MB_ICONSTOP "Dieses Programm benoetigt Windows mit 64 Bit."
  Abort
 ${EndIf}
FunctionEnd
Section "CAN LAN / USB Reader"
 SetOutPath "$INSTDIR"
 File /r "dist/CAN-LAN-Reader/*"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateShortcut "$SMPROGRAMS\CAN LAN USB Reader.lnk" "$INSTDIR\CAN-LAN-Reader.exe"
 CreateShortcut "$DESKTOP\CAN LAN USB Reader.lnk" "$INSTDIR\CAN-LAN-Reader.exe"
 WriteRegStr HKCU "Software\TheBam1990\CAN-LAN-Reader" "InstallDir" "$INSTDIR"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "DisplayName" "CAN LAN / USB Reader"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "DisplayVersion" "1.2.0"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "Publisher" "TheBam1990"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "DisplayIcon" "$INSTDIR\CAN-LAN-Reader.exe"
 WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "UninstallString" '"$INSTDIR\Uninstall.exe"'
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "NoModify" 1
 WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader" "NoRepair" 1
SectionEnd
Section "Uninstall"
 Delete "$SMPROGRAMS\CAN LAN USB Reader.lnk"
 Delete "$DESKTOP\CAN LAN USB Reader.lnk"
 Delete "$INSTDIR\CAN-LAN-Reader.exe"
 Delete "$INSTDIR\README.md"
 Delete "$INSTDIR\START-HIER.txt"
 Delete "$INSTDIR\BUILD-INFO.json"
 Delete "$INSTDIR\SHA256SUMS.txt"
 RMDir /r "$INSTDIR\_internal"
 RMDir /r "$INSTDIR\docs"
 Delete "$INSTDIR\Uninstall.exe"
 RMDir "$INSTDIR"
 DeleteRegKey HKCU "Software\TheBam1990\CAN-LAN-Reader"
 DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CAN-LAN-Reader"
SectionEnd
