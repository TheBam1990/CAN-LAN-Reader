import ctypes as C
import unittest
from canalyst import CanalystDevice, InitConfig, CanObject


class Fn:
    def __init__(self, callback): self.callback = callback
    def __call__(self, *args): return self.callback(*args)


class FakeDLL:
    def __init__(self, fail_init=False):
        self.closed = 0; self.config = None; self.calls = []
        self.VCI_OpenDevice = Fn(lambda *args: self.calls.append(('open', args)) or 1)
        self.VCI_CloseDevice = Fn(self.close)
        self.VCI_InitCAN = Fn(self.init)
        self.VCI_StartCAN = Fn(lambda *args: self.calls.append(('start', args)) or 1)
        self.VCI_Receive = Fn(self.receive); self.fail_init = fail_init

    def init(self, typ, index, channel, config):
        self.config = InitConfig.from_buffer_copy(C.string_at(config, C.sizeof(InitConfig)))
        self.calls.append(('init', (typ, index, channel)))
        return 0 if self.fail_init else 1

    def close(self, *_): self.closed += 1; return 1

    def receive(self, typ, index, channel, buffer, length, timeout):
        buffer[0].ID = 0x18FF1234; buffer[0].ExternFlag = 1; buffer[0].DataLen = 3
        buffer[0].Data[:3] = [0x34, 0x12, 0xFF]
        buffer[1].ID = 0x123; buffer[1].RemoteFlag = 1; buffer[1].DataLen = 8
        return 2


class CanalystTests(unittest.TestCase):
    def test_abi_layout(self):
        self.assertEqual(C.sizeof(InitConfig), 16); self.assertEqual(C.sizeof(CanObject), 24)
        self.assertEqual(CanObject.Data.offset, 13)

    def test_listen_only_and_channel(self):
        dll = FakeDLL(); d = CanalystDevice('', 0, 1, 500000, library=dll); d.open()
        self.assertEqual(dll.config.Mode, 1); self.assertEqual(dll.config.AccMask, 0xFFFFFFFF)
        self.assertEqual((dll.config.Timing0, dll.config.Timing1), (0, 0x1C))
        self.assertIn(('start', (4, 0, 1)), dll.calls)
        frames = d.read(); self.assertEqual(frames[0].can_id, 0x18FF1234)
        self.assertEqual(frames[0].data, bytes.fromhex('34 12 FF'))
        self.assertEqual(frames[1].data, b''); self.assertTrue(frames[1].remote)
        d.close(); d.close(); self.assertEqual(dll.closed, 1)

    def test_initialization_failure_closes_device(self):
        dll = FakeDLL(True); d = CanalystDevice('', library=dll)
        with self.assertRaises(OSError): d.open()
        self.assertEqual(dll.closed, 1); self.assertFalse(d.opened)

    def test_receive_error(self):
        dll = FakeDLL(); d = CanalystDevice('', library=dll); d.open()
        dll.VCI_Receive = Fn(lambda *_: 0xFFFFFFFF)
        with self.assertRaisesRegex(OSError, 'Empfangsfehler'): d.read()
        d.close()
