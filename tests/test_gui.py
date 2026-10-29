import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import socket
import threading
import time
import unittest
from unittest.mock import patch

from app import App
from protocol import CanFrame
from decoding import Signal


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'APPDATA': self.temp.name}); self.env.start()
        self.cwd = os.getcwd(); os.chdir(self.temp.name)
        self.log_patch = patch('app.executable_dir', return_value=Path(self.temp.name)); self.log_patch.start()
        self.warning = patch("app.messagebox.showwarning"); self.warning.start()
        self.app = App(); self.app.withdraw()

    def tearDown(self):
        self.app.close(); self.warning.stop(); self.log_patch.stop(); self.env.stop(); os.chdir(self.cwd); self.temp.cleanup()

    def test_receive_decode_filter_persist(self):
        self.app.signals = [Signal('Spannung', 0x123, factor='0.1', unit='V')]
        f = CanFrame(datetime.now(), 0x123, False, False, 2, bytes.fromhex('34 12'))
        self.app.add_frame(f, 'USB CAN1'); self.app.add_frame(f, 'USB CAN1')
        self.app.apply_filters(); self.app.render_signals()
        row = next(iter(self.app.rows.values()))
        self.assertEqual(row['count'], '2'); self.assertEqual(row['decimal'], '52 18'); self.assertEqual(row['id_dec'], '291')
        self.assertEqual(self.app.signal_values[0]['result'], '466')
        self.assertEqual(len(self.app.signal_tree.get_children()), 1)
        self.app.filters['id'].set('does-not-match'); self.assertFalse(self.app.tree.get_children())
        self.assertEqual(self.app.signal_values[0]['result'], '466')
        self.app.save_settings()
        file = Path(self.temp.name) / 'CAN-LAN-Reader/settings.json'
        self.assertEqual(json.loads(file.read_text())['signals'][0]['name'], 'Spannung')
        self.assertIn('USB CAN1', Path(self.app.log_path).read_text(encoding='utf-8-sig'))

    def test_sources_have_separate_rows_and_short_frame_is_explicit(self):
        self.app.signals = [Signal('Wert', 0x123)]
        f = CanFrame(datetime.now(), 0x123, False, False, 1, b'\x34')
        self.app.add_frame(f, 'LAN'); self.app.add_frame(f, 'USB CAN2')
        self.assertEqual(len(self.app.rows), 2); self.assertIn('DLC', self.app.signal_values[0]['status'])

    def test_lan_receives_fragmented_frames_without_sending(self):
        listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen(1); listener.settimeout(3)
        received = []; errors = []
        def server():
            try:
                conn, _ = listener.accept()
                with conn:
                    data = bytes.fromhex('88 00 00 42 10 BA 14 48 75 F6 04 5A 64')
                    conn.sendall(data[:4]); time.sleep(.03); conn.sendall(data[4:])
                    conn.settimeout(.3)
                    try: received.append(conn.recv(32))
                    except socket.timeout: received.append(b'')
            except Exception as exc: errors.append(exc)
            finally: listener.close()
        thread = threading.Thread(target=server, daemon=True); thread.start()
        self.app.host.set('127.0.0.1'); self.app.port.set(str(listener.getsockname()[1])); self.app.toggle()
        until = time.monotonic() + 4
        while time.monotonic() < until and (not received or self.app.frames < 1):
            self.app.update(); time.sleep(.01)
        thread.join(timeout=1)
        self.assertEqual(errors, []); self.assertEqual(received, [b'']); self.assertEqual(self.app.frames, 1)
        row = next(iter(self.app.rows.values())); self.assertEqual(row['id'], '0x00004210')
