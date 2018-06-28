REM delete old dist files
rmdir /s /q dist

REM build gpgsync.exe
pyinstaller install\pyinstaller.spec -y
