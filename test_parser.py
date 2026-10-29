from protocol import WaveshareParser

raw = bytes.fromhex("88 00 00 42 10 BA 14 48 75 F6 04 5A 64")
p = WaveshareParser()
assert p.feed(raw[:4]) == []
f = p.feed(raw[4:])[0]
assert f.can_id == 0x4210 and f.extended and f.dlc == 8
assert f.data_hex == "BA 14 48 75 F6 04 5A 64"
assert len(p.feed(raw + raw)) == 2
print("Alle Parser-Tests erfolgreich.")
