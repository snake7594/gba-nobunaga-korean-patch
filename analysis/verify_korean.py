# -*- coding: utf-8 -*-
"""패치 ROM 검증: 게임 로직대로 문자열을 글리프 렌더링"""
import struct, json, sys, os
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
ROM = r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba"
rom = open(ROM, "rb").read()
FONT2 = 0x305274
TB2 = 0x30d6ce; N2 = 1869
table = [struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2)]

def glyph_idx(v):
    lo, hi = 0, N2-1
    while lo <= hi:
        mid = (lo+hi)//2
        if table[mid] == v: return mid
        if v > table[mid]: lo = mid+1
        else: hi = mid-1
    return None

def render_at(off, maxb=2048):
    """ROM 오프셋의 널종단 문자열을 글리프로 렌더 (여러 줄)"""
    lines = [[]]
    i = off
    while i < len(rom) and rom[i] != 0 and i - off < maxb:
        b = rom[i]
        if b == 0x0A:
            lines.append([]); i += 1; continue
        if b < 0x80:
            lines[-1].append(("a", b)); i += 1; continue
        if 0xA1 <= b <= 0xDF:
            lines[-1].append(("a", b)); i += 1; continue
        v = (b << 8) | rom[i+1]
        gi = glyph_idx(v)
        lines[-1].append(("g", gi)); i += 2
    return lines

def draw(offsets, name, scale=3):
    all_lines = []
    for off in offsets:
        all_lines.extend(render_at(off))
        all_lines.append(None)  # 구분 빈줄
    W = max((sum(6 if t=="a" else 13 for t,_ in ln) for ln in all_lines if ln), default=10) + 4
    H = len(all_lines)*15 + 4
    img = Image.new("L", (W, H), 255)
    y = 2
    for ln in all_lines:
        if ln is None: y += 15; continue
        x = 2
        for t, v in ln:
            if t == "a":
                x += 6  # ASCII 는 표시 생략(폭만)
                continue
            if v is None: x += 13; continue
            o = FONT2 + v*18
            bits = int.from_bytes(rom[o:o+18], "big")
            for yy in range(12):
                r = (bits >> (144-12*(yy+1))) & 0xFFF
                for xx in range(12):
                    if (r >> (11-xx)) & 1:
                        img.putpixel((x+xx, y+yy), 0)
            x += 13
        y += 15
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    img.save(S+"\\"+name)
    print("saved", name)

if __name__ == "__main__":
    offs = [int(a, 16) for a in sys.argv[2:]]
    draw(offs, sys.argv[1])
