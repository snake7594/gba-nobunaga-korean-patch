# -*- coding: utf-8 -*-
"""4타일(32px) 폭 스트립으로 잘라 나란히 배치 — 1D 매핑 32px 스프라이트를 그대로 읽는다

사용: python analysis/strips.py <base16> <바이트수16> <스트립높이(줄)> [출력명]
"""
import sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths

GRAY = [0, 17, 34, 51, 68, 102, 119, 136, 153, 170, 187, 204, 221, 238, 247, 255]


def run(rom, base, nbytes, rows_per_strip=24, scale=2, name="strips.png", label=True):
    ntiles = nbytes//32
    nrows = ntiles//4
    nstrips = (nrows + rows_per_strip - 1)//rows_per_strip
    lw = 46 if label else 0                       # 주소 적을 자리
    cell = 32 + lw + 4
    W = nstrips*cell+4
    Hh = rows_per_strip*8+4
    img = Image.new("RGB", (W*scale, Hh*scale), (25, 25, 45))
    raw = Image.new("RGB", (W, Hh), (25, 25, 45))
    for t in range(ntiles):
        r, c = t//4, t % 4
        s, rr = r//rows_per_strip, r % rows_per_strip
        ox, oy = 4+s*cell+lw+c*8, 2+rr*8
        b = base + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                raw.putpixel((ox+x, oy+y), (255, 0, 255) if (v & 15) == 0 else (GRAY[v & 15],)*3)
                raw.putpixel((ox+x+1, oy+y), (255, 0, 255) if (v >> 4) == 0 else (GRAY[v >> 4],)*3)
    img.paste(raw.resize((W*scale, Hh*scale), Image.NEAREST), (0, 0))
    if label:
        d = ImageDraw.Draw(img)
        for s in range(nstrips):
            for rr in range(0, rows_per_strip, 2):
                off = base + ((s*rows_per_strip+rr)*4)*32
                d.text(((4+s*cell)*scale, (2+rr*8)*scale+2), f"{off & 0xFFFFF:05x}",
                       fill=(255, 220, 120))
    p = os.path.join(paths.BUILD, name)
    img.save(p)
    print("saved", p, f"base={base:#x} {nbytes:#x}바이트 스트립{nstrips}개 (주소는 하위 5자리)")


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    a = sys.argv
    run(rom, int(a[1], 16), int(a[2], 16), int(a[3]) if len(a) > 3 else 24,
        name=a[4] if len(a) > 4 else "strips.png")
