# -*- coding: utf-8 -*-
"""VRAM 덤프로 실제 화면을 재구성해 PNG 저장 (BG 레이어별 + 합성)"""
import sys, os, struct
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1] if len(sys.argv) > 1 else "title"
vram = open(os.path.join(S, f"vram_{tag}.bin"), "rb").read()
pram = open(os.path.join(S, f"pram_{tag}.bin"), "rb").read()
io = open(os.path.join(S, f"io_{tag}.bin"), "rb").read()
dispcnt = struct.unpack_from("<H", io, 0)[0]


def col(i):
    v = struct.unpack_from("<H", pram, i*2)[0]
    return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)


def render_bg(n):
    bg = struct.unpack_from("<H", io, 8+n*2)[0]
    char = ((bg >> 2) & 3) * 0x4000
    scr = ((bg >> 8) & 31) * 0x800
    bpp8 = (bg >> 7) & 1
    size = (bg >> 14) & 3
    W = 256 if size in (0, 2) else 512
    H = 256 if size in (0, 1) else 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for sy in range(H//8):
        for sx in range(W//8):
            sbx, sby = sx//32, sy//32
            e = struct.unpack_from("<H", vram,
                                   scr + (sby*(W//256)+sbx)*0x800 + ((sy % 32)*32+(sx % 32))*2)
            e = e[0] if isinstance(e, tuple) else e
            tile = e & 0x3FF
            hf, vf, pal = (e >> 10) & 1, (e >> 11) & 1, (e >> 12) & 15
            for y in range(8):
                for x in range(8):
                    if bpp8:
                        c = vram[char + tile*64 + y*8 + x]
                    else:
                        b = vram[char + tile*32 + y*4 + x//2]
                        c = (b >> (4*(x % 2))) & 15
                        if c:
                            c += pal*16
                    xx = sx*8 + (7-x if hf else x)
                    yy = sy*8 + (7-y if vf else y)
                    px[xx, yy] = (*col(c), 0 if c == 0 else 255)
    return img


layers = []
for n in range(4):
    if (dispcnt >> (8+n)) & 1:
        im = render_bg(n)
        im.save(os.path.join(paths.BUILD, f"scr_{tag}_bg{n}.png"))
        prio = struct.unpack_from("<H", io, 8+n*2)[0] & 3
        layers.append((prio, n, im))
        print("saved bg", n, "prio", prio)

# 합성 (우선순위 큰 것부터 아래에)
layers.sort(key=lambda t: -t[0])
comp = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
for _, n, im in layers:
    comp.alpha_composite(im.crop((0, 0, 256, 256)))
comp.crop((0, 0, 240, 160)).resize((720, 480), Image.NEAREST)\
    .save(os.path.join(paths.BUILD, f"scr_{tag}.png"))
print("saved", f"scr_{tag}.png")
