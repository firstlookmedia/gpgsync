!define APPNAME "GPG Sync"
!define BINPATH "..\dist\gpgsync"
!define ABOUTURL "https://github.com/firstlookmedia/gpgsync"

# change these with each release
!define INSTALLSIZE 38746
!define VERSIONMAJOR 0
!define VERSIONMINOR 2
!define VERSIONSTRING "0.2.0"

RequestExecutionLevel admin

Name "GPG Sync"
InstallDir "$PROGRAMFILES\${APPNAME}"
Icon "gpgsync.ico"

!include LogicLib.nsh

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
    SetOutPath "$INSTDIR"
    File "gpgsync.ico"

    File "${BINPATH}\api-ms-win-core-console-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-datetime-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-debug-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-errorhandling-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-file-l2-1-0.dll"
    File "${BINPATH}\api-ms-win-core-handle-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-heap-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-interlocked-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-libraryloader-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-localization-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-memory-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-namedpipe-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processenvironment-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processthreads-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-processthreads-l1-1-1.dll"
    File "${BINPATH}\api-ms-win-core-profile-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-rtlsupport-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-string-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-synch-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-synch-l1-2-0.dll"
    File "${BINPATH}\api-ms-win-core-sysinfo-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-timezone-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-core-util-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-conio-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-convert-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-environment-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-filesystem-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-heap-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-locale-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-math-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-multibyte-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-process-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-runtime-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-stdio-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-string-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-time-l1-1-0.dll"
    File "${BINPATH}\api-ms-win-crt-utility-l1-1-0.dll"
    File "${BINPATH}\base_library.zip"
    File "${BINPATH}\gpgsync.exe"
    File "${BINPATH}\gpgsync.exe.manifest"
    File "${BINPATH}\MSVCP140.dll"
    File "${BINPATH}\pyexpat.pyd"
    File "${BINPATH}\PyQt5.Qt.pyd"
    File "${BINPATH}\PyQt5.QtCore.pyd"
    File "${BINPATH}\PyQt5.QtGui.pyd"
    File "${BINPATH}\PyQt5.QtPrintSupport.pyd"
    File "${BINPATH}\PyQt5.QtWidgets.pyd"
    File "${BINPATH}\python3.dll"
    File "${BINPATH}\python36.dll"
    File "${BINPATH}\pywintypes36.dll"
    File "${BINPATH}\Qt5Core.dll"
    File "${BINPATH}\Qt5Gui.dll"
    File "${BINPATH}\Qt5PrintSupport.dll"
    File "${BINPATH}\Qt5Svg.dll"
    File "${BINPATH}\Qt5Widgets.dll"
    File "${BINPATH}\select.pyd"
    File "${BINPATH}\sip.pyd"
    File "${BINPATH}\ucrtbase.dll"
    File "${BINPATH}\unicodedata.pyd"
    File "${BINPATH}\VCRUNTIME140.dll"
    File "${BINPATH}\win32process.pyd"
    File "${BINPATH}\win32wnet.pyd"
    File "${BINPATH}\_bz2.pyd"
    File "${BINPATH}\_ctypes.pyd"
    File "${BINPATH}\_decimal.pyd"
    File "${BINPATH}\_hashlib.pyd"
    File "${BINPATH}\_lzma.pyd"
    File "${BINPATH}\_socket.pyd"
    File "${BINPATH}\_ssl.pyd"

    SetOutPath "$INSTDIR\certifi"
    File "${BINPATH}\certifi\cacert.pem"

    SetOutPath "$INSTDIR\PyQt5\Qt\bin"
    File "${BINPATH}\PyQt5\Qt\bin\qt.conf"

    SetOutPath "$INSTDIR\PyQt5\Qt\plugins\iconengines"
    File "${BINPATH}\PyQt5\Qt\plugins\iconengines\qsvgicon.dll"

    SetOutPath "$INSTDIR\PyQt5\Qt\plugins\imageformats"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qgif.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qicns.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qico.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qjpeg.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qsvg.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qtga.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qtiff.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qwbmp.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\imageformats\qwebp.dll"

    SetOutPath "$INSTDIR\PyQt5\Qt\plugins\platforms"
    File "${BINPATH}\PyQt5\Qt\plugins\platforms\qminimal.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\platforms\qoffscreen.dll"
    File "${BINPATH}\PyQt5\Qt\plugins\platforms\qwindows.dll"

    SetOutPath "$INSTDIR\PyQt5\Qt\plugins\printsupport"
    File "${BINPATH}\PyQt5\Qt\plugins\printsupport\windowsprintersupport.dll"

    SetOutPath "$INSTDIR\share"
    File "${BINPATH}\share\gpgsync-bw.png"
    File "${BINPATH}\share\gpgsync.desktop"
    File "${BINPATH}\share\gpgsync.png"
    File "${BINPATH}\share\org.firstlook.gpgsync.plist"
    File "${BINPATH}\share\sks-keyservers.netCA.pem"
    File "${BINPATH}\share\sks-keyservers.netCA.pem.asc"
    File "${BINPATH}\share\syncing-bw.png"
    File "${BINPATH}\share\syncing.png"
    File "${BINPATH}\share\version"

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

        Delete "$INSTDIR\api-ms-win-core-console-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-datetime-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-debug-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-errorhandling-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-file-l2-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-handle-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-heap-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-interlocked-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-libraryloader-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-localization-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-memory-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-namedpipe-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processenvironment-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processthreads-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-processthreads-l1-1-1.dll"
        Delete "$INSTDIR\api-ms-win-core-profile-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-rtlsupport-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-string-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-synch-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-synch-l1-2-0.dll"
        Delete "$INSTDIR\api-ms-win-core-sysinfo-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-timezone-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-core-util-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-conio-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-convert-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-environment-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-filesystem-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-heap-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-locale-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-math-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-multibyte-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-process-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-runtime-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-stdio-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-string-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-time-l1-1-0.dll"
        Delete "$INSTDIR\api-ms-win-crt-utility-l1-1-0.dll"
        Delete "$INSTDIR\base_library.zip"
        Delete "$INSTDIR\gpgsync.exe"
        Delete "$INSTDIR\gpgsync.exe.manifest"
        Delete "$INSTDIR\MSVCP140.dll"
        Delete "$INSTDIR\pyexpat.pyd"
        Delete "$INSTDIR\PyQt5.Qt.pyd"
        Delete "$INSTDIR\PyQt5.QtCore.pyd"
        Delete "$INSTDIR\PyQt5.QtGui.pyd"
        Delete "$INSTDIR\PyQt5.QtPrintSupport.pyd"
        Delete "$INSTDIR\PyQt5.QtWidgets.pyd"
        Delete "$INSTDIR\python3.dll"
        Delete "$INSTDIR\python36.dll"
        Delete "$INSTDIR\pywintypes36.dll"
        Delete "$INSTDIR\Qt5Core.dll"
        Delete "$INSTDIR\Qt5Gui.dll"
        Delete "$INSTDIR\Qt5PrintSupport.dll"
        Delete "$INSTDIR\Qt5Svg.dll"
        Delete "$INSTDIR\Qt5Widgets.dll"
        Delete "$INSTDIR\select.pyd"
        Delete "$INSTDIR\sip.pyd"
        Delete "$INSTDIR\ucrtbase.dll"
        Delete "$INSTDIR\unicodedata.pyd"
        Delete "$INSTDIR\VCRUNTIME140.dll"
        Delete "$INSTDIR\win32process.pyd"
        Delete "$INSTDIR\win32wnet.pyd"
        Delete "$INSTDIR\_bz2.pyd"
        Delete "$INSTDIR\_ctypes.pyd"
        Delete "$INSTDIR\_decimal.pyd"
        Delete "$INSTDIR\_hashlib.pyd"
        Delete "$INSTDIR\_lzma.pyd"
        Delete "$INSTDIR\_socket.pyd"
        Delete "$INSTDIR\_ssl.pyd"
        Delete "$INSTDIR\certifi\cacert.pem"
        Delete "$INSTDIR\PyQt5\Qt\bin\qt.conf"
        Delete "$INSTDIR\PyQt5\Qt\plugins\iconengines\qsvgicon.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qgif.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qicns.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qico.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qjpeg.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qsvg.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qtga.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qtiff.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qwbmp.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\imageformats\qwebp.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\platforms\qminimal.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\platforms\qoffscreen.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\platforms\qwindows.dll"
        Delete "$INSTDIR\PyQt5\Qt\plugins\printsupport\windowsprintersupport.dll"
        Delete "$INSTDIR\share\gpgsync-bw.png"
        Delete "$INSTDIR\share\gpgsync.desktop"
        Delete "$INSTDIR\share\gpgsync.png"
        Delete "$INSTDIR\share\org.firstlook.gpgsync.plist"
        Delete "$INSTDIR\share\sks-keyservers.netCA.pem"
        Delete "$INSTDIR\share\sks-keyservers.netCA.pem.asc"
        Delete "$INSTDIR\share\syncing-bw.png"
        Delete "$INSTDIR\share\syncing.png"
        Delete "$INSTDIR\share\version"

        Delete "$INSTDIR\gpgsync.ico"
        Delete "$INSTDIR\uninstall.exe"

        rmDir "$INSTDIR\certifi"
        rmDir "$INSTDIR\PyQt5\Qt\bin"
        rmDir "$INSTDIR\PyQt5\Qt\plugins\iconengines"
        rmDir "$INSTDIR\PyQt5\Qt\plugins\imageformats"
        rmDir "$INSTDIR\PyQt5\Qt\plugins\platforms"
        rmDir "$INSTDIR\PyQt5\Qt\plugins\printsupport"
        rmDir "$INSTDIR\PyQt5\Qt\plugins"
        rmDir "$INSTDIR\PyQt5\Qt"
        rmDir "$INSTDIR\PyQt5"
        rmDir "$INSTDIR\share"
        rmDir "$INSTDIR"

        # remove uninstaller information from the registry
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    SectionEnd
!endif
