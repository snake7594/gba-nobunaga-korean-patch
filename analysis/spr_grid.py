# -*- coding: utf-8 -*-
"""OBJ 1D 매핑 스프라이트를 격자로 렌더 (base/stride/크기 지정)

사용: python analysis/spr_grid.py <base16> <n> <stride16> <w> <h> [출력명]
"""
import sys, os
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths

GRAY = [0, 17, 34, 51, 68, 102, 119, 136, 153, 170, 187, 204, 221, 238, 247, 255]


def draw(rom, img, base, ox, oy, w, h):
    tw = w//8
    for t in range((w*h)//64):
        tx, ty = (t % tw)*8, (t//tw)*8
        b = base + t*32
        if b+32 > len(rom):
            return
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                img.putpixel((ox+tx+x, oy+ty+y), (255, 0, 255) if (v & 15) == 0 else (GRAY[v & 15],)*3)
                img.putpixel((ox+tx+x+1, oy+ty+y), (255, 0, 255) if (v >> 4) == 0 else (GRAY[v >> 4],)*3)


def grid(rom, base, n, stride, w, h, cols=8, scale=3, name="spr.png"):
    rows = (n+cols-1)//cols
    W, Hh = cols*(w+2)+2, rows*(h+4)+2
    img = Image.new("RGB", (W, Hh), (30, 30, 50))
    for k in range(n):
        draw(rom, img, base + k*stride, 2+(k % cols)*(w+2), 2+(k//cols)*(h+4), w, h)
    p = os.path.join(paths.BUILD, name)
    img.resize((W*scale, Hh*scale), Image.NEAREST).save(p)
    print("saved", p)


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    a = sys.argv
    grid(rom, int(a[1], 16), int(a[2]), int(a[3], 16), int(a[4]), int(a[5]),
         name=a[6] if len(a) > 6 else "spr.png")
