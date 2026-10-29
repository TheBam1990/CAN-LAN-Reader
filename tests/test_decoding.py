import struct
import unittest
from decimal import Decimal
from decoding import Signal, number_text, parse_id


class DecodingTests(unittest.TestCase):
    def test_byte_slices_and_endian(self):
        data = bytes.fromhex('AA 34 12 FF')
        self.assertEqual(Signal('v', 0x123, start=1).decode(data), (4660, Decimal(4660)))
        self.assertEqual(Signal('v', 0x123, start=1, endian='big').decode(data)[0], 13330)

    def test_negative_temperature_and_scaling(self):
        raw, scaled = Signal('Temperatur', 0x123, kind='signed', factor='0.1', offset='-5').decode(bytes.fromhex('9C FF'))
        self.assertEqual(raw, -100); self.assertEqual(scaled, Decimal('-15.0'))

    def test_explicit_division(self):
        raw, result = Signal("U", 1, divisor="100").decode(bytes.fromhex("34 12"))
        self.assertEqual(raw, 4660); self.assertEqual(result, Decimal("46.6"))
        with self.assertRaises(ValueError): Signal("bad", 1, divisor="0").validate()

    def test_bit_fields(self):
        self.assertEqual(Signal('b', 1, length=1, bit_offset=4, bit_length=3).decode(bytes([0b11010000]))[0], 5)
        self.assertEqual(Signal('b', 1, length=1, kind='signed', bit_offset=4, bit_length=3).decode(bytes([0b11010000]))[0], -3)

    def test_big_endian_bit_numbering(self):
        self.assertEqual(Signal('b', 1, endian='big', bit_offset=8, bit_length=8).decode(bytes.fromhex('12 34'))[0], 0x12)

    def test_64_bit_precision(self):
        value = (1 << 64) - 1
        raw, scaled = Signal('counter', 1, length=8).decode(value.to_bytes(8, 'little'))
        self.assertEqual(raw, value); self.assertEqual(number_text(scaled), str(value))

    def test_float32_and_float64(self):
        for kind, length, fmt, endian in [('float32', 4, '<f', 'little'), ('float64', 8, '>d', 'big')]:
            self.assertEqual(Signal('f', 1, length=length, kind=kind, endian=endian).decode(struct.pack(fmt, -12.5))[1], Decimal('-12.5'))

    def test_invalid_ranges_and_remote(self):
        for signal in [Signal('bad', 1, start=7), Signal('bad', 1, bit_offset=16), Signal('bad', 1, kind='float32'), Signal('bad', 0x800), Signal('bad', 1, factor='NaN')]:
            with self.assertRaises(ValueError): signal.validate()
        with self.assertRaisesRegex(ValueError, 'DLC'): Signal('a', 1).decode(b'\x01')
        with self.assertRaisesRegex(ValueError, 'Remote'): Signal('a', 1).decode(b'', remote=True)

    def test_definition_roundtrip(self):
        s = Signal('U', 0x18FF1234, True, factor='0.01', unit='V')
        self.assertEqual(Signal(**s.to_dict()), s)
        self.assertEqual(parse_id('0x123'), 291); self.assertEqual(parse_id('123'), 123)
