# -*- coding: utf-8 -*-
"""패치 ROM 검증: 게임 로직대로 디코드 + 글리프 렌더"""
import struct, sys, os, json
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
ROM = r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba"
rom = open(ROM, "rb").read()
FONT2 = 0x305274
TB2 = 0x30d6ce; N2 = 1869
table = [struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2)]
idx_of = {v: i for i, v in enumerate(table)}
charmap = json.load(open(S+r"\charmap.json", encoding="utf-8"))
slot2syl = {v: k for k, v in charmap.items()}

def decode_at(off, maxb=4096):
    """게임과 동일하게 파싱 -> (렌더용 글리프 리스트, 텍스트)"""
    glyphs = [[]]; txt = []
    i = off
    while i < len(rom) and rom[i] != 0 and i - off < maxb:
        b = rom[i]
        if b == 0x0A:
            glyphs.append([]); txt.append("\n"); i += 1; continue
        if b < 0x80 or 0xA1 <= b <= 0xDF:
            glyphs[-1].append(("a", chr(b) if b < 0x80 else "?"))
            txt.append(chr(b) if b < 0x80 else "?"); i += 1; continue
        v = (b << 8) | rom[i+1]
        gi = idx_of.get(v)
        glyphs[-1].append(("g", gi))
        if gi in slot2syl: txt.append(slot2syl[gi])
        elif gi is not None:
            try: txt.append(bytes([b, rom[i+1]]).decode("cp932"))
            except Exception: txt.append("?")
        else: txt.append("?")
        i += 2
    return glyphs, "".join(txt)

def draw(offsets, name, scale=3):
    lines = []
    for off in offsets:
        g, t = decode_at(off)
        lines.extend(g); lines.append(None)
    W = max((sum(7 if k=="a" else 13 for k,_ in ln) for ln in lines if ln), default=20) + 6
    H = len(lines)*15 + 6
    img = Image.new("L", (W, H), 255)
    y = 3
    for ln in lines:
        if ln is None: y += 15; continue
        x = 3
        for kind, v in ln:
            if kind == "a":
                # ASCII 를 8x12 폰트로 렌더
                c = ord(v) if isinstance(v, str) else 32
                if 0x20 <= c < 0x80:
                    ao = 0x304df4 + (c - 0x20)*12
                    for yy in range(12):
                        bb = rom[ao+yy]
                        for xx in range(8):
                            if (bb >> (7-xx)) & 1: img.putpixel((x+xx, y+yy), 0)
                x += 7; continue
            if v is None: x += 13; continue
            o = FONT2 + v*18
            bits = int.from_bytes(rom[o:o+18], "big")
            for yy in range(12):
                r = (bits >> (144-12*(yy+1))) & 0xFFF
                for xx in range(12):
                    if (r >> (11-xx)) & 1: img.putpixel((x+xx, y+yy), 0)
            x += 13
        y += 15
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    img.save(S+"\\"+name); print("saved", name)

if __name__ == "__main__":
    if sys.argv[1] == "text":
        for a in sys.argv[2:]:
            off = int(a, 16)
            print(f"--- {off:#x} ---")
            print(decode_at(off)[1])
    else:
        draw([int(a, 16) for a in sys.argv[2:]], sys.argv[1])
