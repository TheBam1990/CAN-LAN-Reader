"""Explicit byte/bit extraction. Bit zero is the LSB of the decoded byte block."""
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation, DecimalException
import math
import struct


@dataclass(frozen=True)
class Signal:
    name: str
    can_id: int
    extended: bool = False
    start: int = 0
    length: int = 2
    endian: str = "little"
    kind: str = "unsigned"
    bit_offset: int = 0
    bit_length: int = 0
    factor: str = "1"
    offset: str = "0"
    unit: str = ""
    divisor: str = "1"

    def validate(self):
        if not self.name.strip(): raise ValueError("Ein Name ist erforderlich.")
        if not 0 <= self.can_id <= (0x1FFFFFFF if self.extended else 0x7FF): raise ValueError("CAN-ID passt nicht zum gewählten Format.")
        if not 0 <= self.start <= 7 or not 1 <= self.length <= 8 or self.start + self.length > 8: raise ValueError("Bytebereich muss innerhalb von Byte 0 bis 7 liegen.")
        if self.endian not in ("little", "big") or self.kind not in ("unsigned", "signed", "float32", "float64"): raise ValueError("Unbekanntes Zahlenformat.")
        width = self.length * 8
        if not 0 <= self.bit_offset < width or not 0 <= self.bit_length <= width - self.bit_offset: raise ValueError("Bitbereich liegt außerhalb des Byteblocks.")
        if self.kind.startswith("float") and (self.length != (4 if self.kind == "float32" else 8) or self.bit_offset or self.bit_length): raise ValueError("Float32 benötigt 4, Float64 8 Bytes ohne Bit-Auswahl.")
        try:
            if not all(Decimal(x).is_finite() for x in (self.factor, self.offset, self.divisor)) or Decimal(self.divisor) == 0: raise ValueError
        except (InvalidOperation, ValueError): raise ValueError("Faktor, Teiler und Offset müssen endliche Zahlen sein; der Teiler darf nicht 0 sein.") from None
        return self

    def decode(self, data: bytes, remote=False):
        self.validate()
        if remote: raise ValueError("Remote-Frame hat keine Nutzdaten.")
        if self.start + self.length > len(data): raise ValueError("DLC zu kurz für diesen Bytebereich.")
        block = data[self.start:self.start + self.length]
        if self.kind.startswith("float"):
            raw = struct.unpack(("<" if self.endian == "little" else ">") + ("f" if self.kind == "float32" else "d"), block)[0]
            if not math.isfinite(raw): raise ValueError("Float-Wert ist NaN oder unendlich.")
        else:
            width = self.bit_length or self.length * 8 - self.bit_offset
            raw = (int.from_bytes(block, self.endian) >> self.bit_offset) & ((1 << width) - 1)
            if self.kind == "signed" and raw & (1 << (width - 1)): raw -= 1 << width
        # Decimal preserves 64-bit integers and user-supplied decimal factors.
        from decimal import localcontext
        try:
            with localcontext() as ctx:
                ctx.prec = 80
                result = Decimal(str(raw)) * Decimal(self.factor) / Decimal(self.divisor) + Decimal(self.offset)
        except DecimalException:
            raise ValueError("Ergebnis der Skalierung ist zu groß.") from None
        return raw, result

    def to_dict(self): return asdict(self)


def parse_id(text):
    text = text.strip()
    return int(text, 16) if text.lower().startswith("0x") or any(c in "abcdefABCDEF" for c in text) else int(text, 10)


def number_text(value):
    if isinstance(value, Decimal):
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    return str(value)
