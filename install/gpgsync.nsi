!define APPNAME "GPG Sync"
!define BINPATH "..\dist\gpgsync"
!define ABOUTURL "https://github.com/firstlookmedia/gpgsync"
!define APP_EXE "gpgsync.exe"

# change these with each release
!define INSTALLSIZE 76759
!define VERSIONMAJOR 0
!define VERSIONMINOR 3
!define VERSIONSTRING "0.3.6"

RequestExecutionLevel admin

Name "GPG Sync"
InstallDir "$PROGRAMFILES\${APPNAME}"
Icon "gpgsync.ico"

!include LogicLib.nsh
!include "nsProcess.nsh"

Page directory
Page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin" ;Require admin rights on NT4+
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
    quit
${EndIf}
!macroend

!macro CloseIfRunning
    # If app is running, close it first
    ${nsProcess::FindProcess} "${APP_EXE}" $R0
    ${If} $R0 == 0
        DetailPrint "${AppName} is running. Closing it down"
        ${nsProcess::CloseProcess} "${APP_EXE}" $R0
        DetailPrint "Waiting for ${AppName} to close"
        Sleep 2000
    ${Else}
        DetailPrint "${APP_EXE} was not found to be running"
    ${EndIf}
    ${nsProcess::Unload}
!macroend

# in order to code sign uninstall.exe, we need to do some hacky stuff outlined
# here: http:\\nsis.sourceforge.net\Signing_an_Uninstaller
!ifdef INNER
    !echo "Creating uninstall.exe"
    OutFile "$%TEMP%\tempinstaller.exe"
    SetCompress off
!else
    !echo "Creating normal installer"
    !system "makensis.exe /DINNER gpgsync.nsi" = 0
    !system "$%TEMP%\tempinstaller.exe" = 2
    !system "signtool.exe sign /v /d $\"Uninstall GPG Sync$\" /a /tr http://time.certum.pl/ $%TEMP%\uninstall.exe" = 0

    # all done, now we can build the real installer
    OutFile "..\dist\gpgsync-setup.exe"
    SetCompressor /FINAL /SOLID lzma
!endif

Function .onInit
    !ifdef INNER
        WriteUninstaller "$%TEMP%\uninstall.exe"
        Quit # bail out early
    !endif

    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
FunctionEnd

Section "install"
    !insertmacro CloseIfRunning

    SetOutPath "$INSTDIR"
    File "gpgsync.ico"
    File /a /r "${BINPATH}\"

    # uninstaller
    !ifndef INNER
        SetOutPath $INSTDIR
        File $%TEMP%\uninstall.exe
    !endif

    # start menu
    CreateShortCut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\gpgsync.exe" "" "$INSTDIR\gpgsync.ico"

    # registry information for add\remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" \S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\gpgsync.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" ${VERSIONSTRING}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    # there is no option for modifying or repairing the install
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    # set the INSTALLSIZE constant (!defined at the top of this script) so Add\Remove Programs can accurately report the size
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
SectionEnd

# uninstaller
Function un.onInit
    SetShellVarContext all

    #Verify the uninstaller - last chance to back out
    MessageBox MB_OKCANCEL "Uninstall ${APPNAME}?" IDOK next
        Abort
    next:
    !insertmacro VerifyUserIsAdmin
FunctionEnd

!ifdef INNER
    Section "uninstall"
        Delete "$SMPROGRAMS\${APPNAME}.lnk"
        !insertmacro CloseIfRunning

        # remove files
        RMDir /r $INSTDIR

        # remove uninstaller information from the registry
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    SectionEnd
!endif
