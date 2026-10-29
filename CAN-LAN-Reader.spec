# -*- mode: python ; coding: utf-8 -*-
a = Analysis(['app.py'], pathex=[], binaries=[('vendor/canalyst/ControlCAN.dll', 'vendor/canalyst')], datas=[('vendor/canalyst/SOURCE.txt', 'vendor/canalyst')], hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CAN-LAN-Reader', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          disable_windowed_traceback=False, uac_admin=False, version='windows-version-info.txt')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='CAN-LAN-Reader')
