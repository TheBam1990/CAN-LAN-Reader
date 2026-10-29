from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CanFrame:
    timestamp: datetime
    can_id: int
    extended: bool
    remote: bool
    dlc: int
    data: bytes

    @property
    def id_text(self): return f"0x{self.can_id:08X}" if self.extended else f"0x{self.can_id:03X}"
    @property
    def format(self): return "Extended" if self.extended else "Standard"
    @property
    def frame_type(self): return "Remote" if self.remote else "Data"
    @property
    def data_hex(self): return " ".join(f"{x:02X}" for x in self.data)
    @property
    def ascii(self): return "".join(chr(x) if 32 <= x <= 126 else "." for x in self.data)
    @property
    def raw(self):
        header = (0x80 if self.extended else 0) | (0x40 if self.remote else 0) | self.dlc
        return " ".join(f"{x:02X}" for x in bytes([header]) + self.can_id.to_bytes(4, "big") + self.data)


class WaveshareParser:
    def __init__(self): self.buffer = bytearray()

    def feed(self, chunk: bytes):
        self.buffer.extend(chunk)
        frames = []
        while len(self.buffer) >= 13:
            header = self.buffer[0]
            dlc = header & 0x0F
            extended, remote = bool(header & 0x80), bool(header & 0x40)
            can_id = int.from_bytes(self.buffer[1:5], "big")
            if dlc > 8 or (not extended and can_id > 0x7FF) or (extended and can_id > 0x1FFFFFFF):
                del self.buffer[0]
                continue
            data = b"" if remote else bytes(self.buffer[5:5 + dlc])
            frames.append(CanFrame(datetime.now(), can_id, extended, remote, dlc, data))
            del self.buffer[:13]
        return frames
