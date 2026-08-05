# -*- coding: utf-8 -*-
"""완성된 롬에서 실제 바이트를 읽어 게임과 동일한 규칙으로 화면을 렌더한다."""
import sys, struct
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = paths.read_rom_kr()
FONT = paths.FONT_BASE
TB, N = paths.TABLE_BASE, paths.TABLE_N
table = [struct.unpack_from("<H", rom, TB+i*2)[0] for i in range(N)]
idx = {v: i for i, v in enumerate(table)}
ADV = rom[0x3EAC]          # 실제 롬에 기록된 전각 전진폭
print("롬의 전각 전진폭:", ADV, "px")


import json
ASCII_FONT = 0x304DF4          # 8x12, 12바이트/자
ASCII_TB = 0x30D604
atab = [struct.unpack_from("<H", rom, ASCII_TB+i*2)[0] for i in range(96)]

_es = json.load(open(paths.inp('master_strings.json'), encoding="utf-8"))
_by = {e["off"]: e for e in _es}


def follow(off):
    """재배치된 문자열은 포인터를 따라 현재 주소를 얻는다"""
    e = _by.get(off)
    if e and e["refs"]:
        v = struct.unpack_from("<I", rom, e["refs"][0])[0]
        if 0x08000000 <= v < 0x08400000:
            return v - 0x08000000
    return off


def rows(slot):
    o = FONT + slot*18
    b = int.from_bytes(rom[o:o+18], "big")
    return [(b >> (144-12*(y+1))) & 0xFFF for y in range(12)]


def arows(code):
    """1바이트 문자 글리프 (8x12).
    테이블 0x30D604 는 지원 코드를 u16 에 2개씩 담아 오름차순 나열한다
    (index0 = 0x2120 -> 0x20,0x21). 따라서 0x20..0x7E 는 glyph = code-0x20."""
    if not (0x20 <= code <= 0x7E):
        return None
    o = ASCII_FONT + (code - 0x20) * 12
    return [rom[o+y] << 4 for y in range(12)]


def draw(off, limit_px, maxlines, scale=3, maxb=4096):
    L = 15
    start = follow(off)
    img = Image.new("RGB", (limit_px+4, L*(maxlines+2)+6), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, limit_px+2, 1+L*maxlines], outline=(60, 120, 220))
    i, x, line = start, 0, 0
    while i < len(rom) and rom[i] != 0 and i - start < maxb:
        b = rom[i]
        if b == 0x0A:
            line += 1; x = 0; i += 1; continue
        if b < 0x80 or 0xA1 <= b <= 0xDF:
            w, g = 8, arows(b)
            i += 1
        else:
            v = (b << 8) | rom[i+1]
            s = idx.get(v)
            g = rows(s) if s is not None else None
            w = ADV
            i += 2
        if x + w > limit_px:
            line += 1; x = 0
        if g is not None:
            col = (200, 0, 0) if line >= maxlines else (0, 0, 0)
            for yy in range(12):
                for xx in range(12):
                    if (g[yy] >> (11-xx)) & 1:
                        px, py = 2+x+xx, 3+line*L+yy
                        if 0 <= px < img.width and 0 <= py < img.height:
                            img.putpixel((px, py), col)
        x += w
    return img.resize((img.width*scale, img.height*scale), Image.NEAREST), line+1


SHOTS = [
    ("모드 선택",        0x23035C, 216, 4),
    ("질문 메시지",      0x230488, 240, 2),
    ("인물 열전(모리)",  0x240ACC, 216, 4),
    ("인물 열전(정종)",  0x24FB60, 216, 4),
    ("도움말(수송)",     0x228148, 240, 8),
    ("커맨드 라벨",      0x2259D8, 240, 2),
]
outs = []
for label, off, lim, ml in SHOTS:
    im, n = draw(off, lim, ml)
    outs.append((f"{label}  @{off:#x}  ({n}줄 / 창 {ml}줄)", im))

try:
    f = ImageFont.truetype("malgun.ttf", 15)
except Exception:
    f = ImageFont.load_default()
W = max(im.width for _, im in outs) + 8
H = sum(im.height + 26 for _, im in outs) + 8
canvas = Image.new("RGB", (W, H), (255, 255, 255))
dc = ImageDraw.Draw(canvas)
y = 4
for label, im in outs:
    dc.text((4, y), label, fill=(20, 20, 20), font=f)
    y += 20
    canvas.paste(im, (4, y)); y += im.height + 6
canvas.save(paths.out("final_screens.png"))
print("saved build/final_screens.png")
