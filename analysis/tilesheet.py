# -*- coding: utf-8 -*-
"""ROM 구간을 4bpp 타일 시트로 렌더 (팔레트 미상 -> 인덱스 그레이)"""
import sys, os
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = paths.read_rom_jp()
OUT = paths.BUILD
os.makedirs(OUT, exist_ok=True)

GRAY = [0, 17, 34, 51, 68, 102, 119, 136, 153, 170, 187, 204, 221, 238, 247, 255]


def sheet(off, ntiles, cols, name, scale=2, pal=None):
    rows = (ntiles + cols - 1) // cols
    W, H = cols*8, rows*8
    img = Image.new("L", (W, H), 0)
    px = img.load()
    for t in range(ntiles):
        base = off + t*32
        if base + 32 > len(rom):
            break
        tx, ty = (t % cols)*8, (t//cols)*8
        for y in range(8):
            for x in range(0, 8, 2):
                b = rom[base + y*4 + x//2]
                px[tx+x, ty+y] = GRAY[b & 0x0F]
                px[tx+x+1, ty+y] = GRAY[b >> 4]
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    p = os.path.join(OUT, name)
    img.save(p)
    return p


if __name__ == "__main__":
    off = int(sys.argv[1], 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    nm = sys.argv[4] if len(sys.argv) > 4 else f"ts_{off:06x}.png"
    print(sheet(off, n, cols, nm))
