"""Receive-only ControlCAN interface for CANalyst-II compatible Windows drivers."""
import ctypes as C
from datetime import datetime
import os
import sys
from pathlib import Path
from protocol import CanFrame


class InitConfig(C.Structure):
    _fields_ = [("AccCode", C.c_uint32), ("AccMask", C.c_uint32), ("Reserved", C.c_uint32),
                ("Filter", C.c_ubyte), ("Timing0", C.c_ubyte), ("Timing1", C.c_ubyte), ("Mode", C.c_ubyte)]


class CanObject(C.Structure):
    _fields_ = [("ID", C.c_uint32), ("TimeStamp", C.c_uint32), ("TimeFlag", C.c_ubyte),
                ("SendType", C.c_ubyte), ("RemoteFlag", C.c_ubyte), ("ExternFlag", C.c_ubyte),
                ("DataLen", C.c_ubyte), ("Data", C.c_ubyte * 8), ("Reserved", C.c_ubyte * 3)]


TIMINGS = {1000000: (0x00, 0x14), 800000: (0x00, 0x16), 500000: (0x00, 0x1C),
           250000: (0x01, 0x1C), 125000: (0x03, 0x1C), 100000: (0x04, 0x1C),
           50000: (0x09, 0x1C), 20000: (0x18, 0x1C), 10000: (0x31, 0x1C), 5000: (0x63, 0x1C)}


def bundled_dll_path():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "vendor" / "canalyst" / "ControlCAN.dll"


class CanalystDevice:
    def __init__(self, dll_path=None, device_index=0, channel=0, bitrate=500000, *, library=None):
        if channel not in (0, 1) or not 0 <= device_index <= 15 or bitrate not in TIMINGS:
            raise ValueError("Ungültiger CANalyst-Kanal, Geräteindex oder Bitrate.")
        self.index, self.channel, self.bitrate = device_index, channel, bitrate
        self.opened = False
        self.directory_handle = None
        if library is None:
            if os.name != "nt": raise OSError("CANalyst über ControlCAN.dll benötigt Windows.")
            path = Path(dll_path).expanduser().resolve() if dll_path else bundled_dll_path()
            if not path.is_file(): raise OSError("Die mitgelieferte CANalyst-Bibliothek fehlt. Bitte den vollständigen Programmordner einschließlich _internal entpacken.")
            self.directory_handle = os.add_dll_directory(str(path.parent))
            try: library = C.WinDLL(str(path))
            except OSError as exc:
                self.directory_handle.close(); self.directory_handle = None
                bits = C.sizeof(C.c_void_p) * 8
                raise OSError(f"Hersteller-DLL kann nicht geladen werden ({bits}-Bit-Programm). DLL-Bitness, USB-Treiber und SDK-Begleitdateien prüfen. {exc}") from exc
        self.dll = library
        try:
            signatures = {"VCI_OpenDevice": ([C.c_uint32] * 3), "VCI_CloseDevice": ([C.c_uint32] * 2),
                          "VCI_InitCAN": ([C.c_uint32] * 3 + [C.POINTER(InitConfig)]),
                          "VCI_StartCAN": ([C.c_uint32] * 3),
                          "VCI_Receive": ([C.c_uint32] * 3 + [C.POINTER(CanObject), C.c_uint32, C.c_int32])}
            for name, args in signatures.items():
                function = getattr(self.dll, name)
                function.argtypes, function.restype = args, C.c_uint32
        except Exception:
            if self.directory_handle: self.directory_handle.close()
            raise OSError("DLL bietet nicht die erforderliche ControlCAN-Schnittstelle für CANalyst-II.") from None

    def open(self):
        try:
            if self.dll.VCI_OpenDevice(4, self.index, 0) != 1: raise OSError("CANalyst-II konnte nicht geöffnet werden. USB-Treiber, Geräteindex und andere laufende CAN-Programme prüfen.")
            self.opened = True
            timing0, timing1 = TIMINGS[self.bitrate]
            config = InitConfig(0, 0xFFFFFFFF, 0, 1, timing0, timing1, 1)  # mode 1: listen-only
            if self.dll.VCI_InitCAN(4, self.index, self.channel, C.byref(config)) != 1: raise OSError("Initialisierung im Nur-Lauschen-Modus fehlgeschlagen.")
            if self.dll.VCI_StartCAN(4, self.index, self.channel) != 1: raise OSError("CANalyst-Empfang konnte nicht gestartet werden.")
        except Exception:
            self.close()
            raise

    def read(self):
        if not self.opened: raise OSError("CANalyst ist nicht geöffnet.")
        buffer = (CanObject * 256)()
        count = self.dll.VCI_Receive(4, self.index, self.channel, buffer, 256, 50)
        if count == 0xFFFFFFFF: raise OSError("CANalyst meldet einen Empfangsfehler; USB-Verbindung und Treiber prüfen.")
        if count > 256: raise OSError("Ungültige Empfangsanzahl aus der Hersteller-DLL.")
        frames = []
        for item in buffer[:count]:
            extended, remote = bool(item.ExternFlag), bool(item.RemoteFlag)
            if item.DataLen > 8 or item.ID > (0x1FFFFFFF if extended else 0x7FF): continue
            frames.append(CanFrame(datetime.now(), item.ID, extended, remote, item.DataLen,
                                   b"" if remote else bytes(item.Data[:item.DataLen])))
        return frames

    def close(self):
        try:
            if self.opened:
                self.opened = False
                self.dll.VCI_CloseDevice(4, self.index)
        finally:
            if self.directory_handle:
                self.directory_handle.close()
                self.directory_handle = None
