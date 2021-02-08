REM delete old dist files
rmdir /s /q dist

REM build gpgsync.exe
python -m poetry run pyinstaller install\pyinstaller.spec -y

REM codesign gpgsync.exe
signtool.exe sign /v /d "GPG Sync" /a /tr http://time.certum.pl/ dist\gpgsync\gpgsync.exe

REM build an installer, dist\gpgsync-setup.exe
makensis.exe install\gpgsync.nsi

REM sign gpgsync-setup.exe
signtool.exe sign /v /d "GPG Sync" /a /tr http://time.certum.pl/ dist\gpgsync-setup.exe
