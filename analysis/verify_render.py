# -*- coding: utf-8 -*-
"""패치된 ROM의 폰트+테이블로 게임과 동일하게 문자열을 렌더링해 검증"""
import struct
from PIL import Image

ROM = r"D:\gba\NOBU2\Nobunaga no Yabou (Korean-Reading).gba"
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
rom = open(ROM, "rb").read()
FONT2 = 0x305274
TB2 = 0x30d6ce
N2 = 1869

table = [struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2)]

def glyph_idx(ch):
    b = ch.encode("cp932")
    if len(b) != 2: return None
    v = (b[0] << 8) | b[1]
    lo, hi = 0, N2-1
    while lo <= hi:
        mid = (lo+hi)//2
        if table[mid] == v: return mid
        if v > table[mid]: lo = mid+1
        else: hi = mid-1
    return None

def draw_text(lines, name, scale=3):
    W = max(len(l) for l in lines)*13 + 4
    H = len(lines)*15 + 4
    img = Image.new("L", (W, H), 255)
    for li, line in enumerate(lines):
        for ci, ch in enumerate(line):
            gi = glyph_idx(ch)
            if gi is None: continue
            off = FONT2 + gi*18
            bits = int.from_bytes(rom[off:off+18], "big")
            for y in range(12):
                r = (bits >> (144-12*(y+1))) & 0xFFF
                for x in range(12):
                    if (r >> (11-x)) & 1:
                        img.putpixel((2+ci*13+x, 2+li*15+y), 0)
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    img.save(S+"\\"+name)
    print("saved", name)

draw_text([
    "入門モード",
    "実力モード",
    "デモモード",
    "どのモードにしますか？",
    "織田信長　豊臣秀吉",
    "徳川家康　武田信玄",
    "上杉謙信　伊達政宗",
    "天下統一　戦国時代",
], "verify_text.png")
