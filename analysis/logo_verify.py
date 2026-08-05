# -*- coding: utf-8 -*-
"""패치 전/후 타이틀 화면을 나란히 렌더 (릴리즈 노트용)"""
import sys, os, struct
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
pram = open(os.path.join(S, "pram_s01_title.bin"), "rb").read()
vram = open(os.path.join(S, "vram_s01_title.bin"), "rb").read()
SEG = [(0, 204, 0x08002C), (208, 640, 0x0596F0)]


def col(i):
    v = struct.unpack_from("<H", pram, i*2)[0]
    return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)


def ro(t):
    for lo, hi, b in SEG:
        if lo <= t < hi:
            return b + (t-lo)*64
    return None


def render(rom, name):
    img = Image.new("RGB", (240, 160))
    px = img.load()
    for sy in range(20):
        for sx in range(30):
            e = struct.unpack_from("<H", vram, 0xE000 + (sy*32+sx)*2)[0]
            o = ro(e & 0x3FF)
            for y in range(8):
                for x in range(8):
                    px[sx*8+x, sy*8+y] = col(rom[o+y*8+x] if o is not None else 0)
    img.save(os.path.join(paths.BUILD, name))
    return img


before = render(paths.read_rom_jp(), "title_before.png")
after = render(paths.read_rom_kr(), "title_after.png")

SC = 2
W, H = 240*SC, 160*SC
cv = Image.new("RGB", (W*2+24, H+34), (245, 245, 245))
d = ImageDraw.Draw(cv)
try:
    f = ImageFont.truetype("malgunbd.ttf", 16)
except Exception:
    f = ImageFont.load_default()
d.text((8, 6), "패치 전", fill=(20, 20, 20), font=f)
d.text((W+16, 6), "패치 후", fill=(20, 20, 20), font=f)
cv.paste(before.resize((W, H), Image.NEAREST), (8, 26))
cv.paste(after.resize((W, H), Image.NEAREST), (W+16, 26))
cv.save(os.path.join(paths.BUILD, "title_ba.png"))
print("saved build/title_before.png, title_after.png, title_ba.png")
