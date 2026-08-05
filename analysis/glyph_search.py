from PIL import Image
import numpy as np
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
img = Image.open(S+r"\bg3_menu.png").convert("RGB")
a = np.array(img)

# check colors used in text area
sub = a[30:150, 8:150].reshape(-1,3)
uniq = np.unique(sub, axis=0)
print("unique colors in text area:", uniq[:10])

g = np.array(img.convert("L")) > 100

def cell(x0, y0):
    return g[y0:y0+12, x0:x0+12]

# line1: 入門モード at y=34, x=88..; line2: 実力モード y=50?; check
ys = np.where(g.any(1))[0]
print("occupied rows:", ys.min(), ys.max())
# find line starts: groups of consecutive occupied rows
lines = []
prev = -10
for y in ys:
    if y != prev+1:
        lines.append(y)
    prev = y
print("line start rows:", lines)

chars = {}
# line 1: 入門モード
for i, ch in enumerate("入門モード"):
    chars[ch] = cell(88+12*i, lines[0])
# line 2: 実力モード
for i, ch in enumerate("実力モード"):
    if ch in chars: continue
    chars[ch] = cell(88+12*i, lines[1])
# line 3: デモモード
for i, ch in enumerate("デモモード"):
    if ch in chars: continue
    chars[ch] = cell(88+12*i, lines[2])
# line 4: どのモードにしますか?
for i, ch in enumerate("どのモードにしますか?"):
    if ch in chars: continue
    chars[ch] = cell(10+12*i, lines[3])

for ch, c in chars.items():
    print(ch, "popcount", int(c.sum()))

def needles(c):
    """generate (label, bytes) candidate encodings of a 12x12 glyph"""
    out = []
    rows = []
    for y in range(12):
        v = 0
        for x in range(12):
            v = (v<<1) | (1 if c[y,x] else 0)
        rows.append(v)  # 12-bit, MSB=leftmost
    # (a) 2B/row, glyph in bits 15..4 (left aligned)
    out.append(("2B-left-BE", b"".join(((r<<4)).to_bytes(2,"big") for r in rows)))
    out.append(("2B-left-LE", b"".join(((r<<4)).to_bytes(2,"little") for r in rows)))
    # (b) right aligned
    out.append(("2B-right-BE", b"".join(r.to_bytes(2,"big") for r in rows)))
    out.append(("2B-right-LE", b"".join(r.to_bytes(2,"little") for r in rows)))
    # (c) packed 12-bit stream
    bits = 0; n = 0; ba = bytearray()
    for r in rows:
        bits = (bits<<12)|r; n += 12
        while n >= 8:
            ba.append((bits >> (n-8)) & 0xFF); n -= 8
    if n: ba.append((bits << (8-n)) & 0xFF)
    out.append(("packed12", bytes(ba)))
    # (d) mirrored bit order variants
    rowsR = []
    for y in range(12):
        v = 0
        for x in range(12):
            v = (v<<1) | (1 if c[y,11-x] else 0)
        rowsR.append(v)
    out.append(("2B-left-BE-mirror", b"".join(((r<<4)).to_bytes(2,"big") for r in rowsR)))
    out.append(("2B-right-LE-mirror", b"".join(r.to_bytes(2,"little") for r in rowsR)))
    return out

rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

print("\n=== search ===")
for ch, c in chars.items():
    found = []
    for label, nd in needles(c):
        # search with a partial needle first (first 8 rows worth) to allow tail mismatch
        idx = rom.find(nd[:16])
        while idx >= 0:
            found.append((label, idx, rom[idx:idx+len(nd)] == nd))
            idx = rom.find(nd[:16], idx+1)
            if len(found) > 6: break
    print(ch, found if found else "NOT FOUND")
