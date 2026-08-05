import struct
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

TB = 0x30d604
# decode as u16 LE SJIS codes
vals = [struct.unpack_from("<H", rom, TB+i*2)[0] for i in range(0, 1400)]
def sj(v):
    if v < 0x100:
        b = bytes([v])
    else:
        b = bytes([v>>8, v&0xFF])
    try:
        return b.decode("shift_jis")
    except Exception:
        return "?"

# find where table stops making sense
line = []
for i, v in enumerate(vals):
    line.append(f"{i}:{v:04x}({sj(v)})")
    if (i+1) % 8 == 0:
        print(" ".join(line)); line = []
    if i > 700: break
if line: print(" ".join(line))
