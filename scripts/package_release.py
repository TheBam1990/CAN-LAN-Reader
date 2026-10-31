"""Package the existing PyInstaller output; run again after makensis for installer checksums."""
from pathlib import Path
import datetime, hashlib, json, shutil, zipfile
ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.2.0'
bundle = ROOT/'dist/CAN-LAN-Reader'
release = ROOT/'dist'/f'release-{VERSION}'
release.mkdir(parents=True, exist_ok=True)
(bundle/'CAN-LAN-Reader-Log.txt').unlink(missing_ok=True)
shutil.copyfile(ROOT/'README.md', bundle/'README.md')
shutil.copytree(ROOT/'docs', bundle/'docs', dirs_exist_ok=True)
(bundle/'START-HIER.txt').write_text('CAN LAN / USB Reader '+VERSION+'\n\nCAN-LAN-Reader.exe starten. Der Ordner _internal muss daneben bleiben.\nDie CANalyst-II-Bibliothek ist integriert. Windows-USB-Treiber bei Bedarf separat installieren.\nKanal und CAN-Bitrate passend einstellen. Empfang erfolgt nur lesend.\nDie README beschreibt das Anlegen von Auswertungen mit Screenshots.\n',encoding='utf-8')
files = [ROOT/name for name in ['.gitignore','.gitattributes','app.py','i18n.py','protocol.py','decoding.py','canalyst.py','CAN-LAN-Reader.spec','requirements-build.txt','windows-version-info.txt','build-windows.bat','README.md','test_parser.py','installer.nsi']]
for folder in ['tests','docs','vendor','scripts']:
 files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
meta={'version':VERSION,'architecture':'Windows x64','packaging':'onedir','upx':False,'authenticode_signed':False,'physical_usb_receive_test':False,'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(bundle/'BUILD-INFO.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
(bundle/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(bundle).as_posix()+'\n' for p in sorted(bundle.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
portable=release/'CAN-LAN-Reader-Windows-x64-portable.zip'
with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(bundle.rglob('*')):
  if p.is_file(): z.write(p,p.relative_to(bundle).as_posix())
with zipfile.ZipFile(release/f'CAN-LAN-Reader-{VERSION}-source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,f'CAN-LAN-Reader-{VERSION}/'+p.relative_to(ROOT).as_posix())
installer=ROOT/'dist/CAN-LAN-Reader-Setup.exe'
if installer.exists():shutil.copyfile(installer,release/installer.name)
(release/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(release.iterdir()) if p.name in ['CAN-LAN-Reader-Setup.exe','CAN-LAN-Reader-Windows-x64-portable.zip',f'CAN-LAN-Reader-{VERSION}-source.zip']),encoding='utf-8')
print('PACKAGED',release)
