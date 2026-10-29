@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto failed
call .venv\Scripts\activate.bat
python -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
python -m unittest discover -s tests -v
if errorlevel 1 goto failed
python test_parser.py
if errorlevel 1 goto failed
python -m PyInstaller --clean --noconfirm CAN-LAN-Reader.spec
if errorlevel 1 goto failed
echo Fertig: dist\CAN-LAN-Reader\CAN-LAN-Reader.exe
pause
exit /b 0
:failed
echo Build fehlgeschlagen.
pause
exit /b 1
