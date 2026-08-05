# -*- coding: utf-8 -*-
"""4bpp 타일을 NxN 블록 단위로 묶어 렌더 (16x16 글자 = 2x2 타일 등)"""
import sys, os
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = paths.read_rom_jp()
GRAY = [255, 200, 160, 120, 90, 70, 50, 30, 20, 10, 0, 40, 60, 80, 100, 140]


def tile_px(base, px, ox, oy):
    for y in range(8):
        for x in range(0, 8, 2):
            b = rom[base + y*4 + x//2]
            px[ox+x, oy+y] = GRAY[b & 0x0F]
            px[ox+x+1, oy+y] = GRAY[b >> 4]


def sheet(off, nblk, bw, bh, cols, name, scale=3, gap=1):
    """bw x bh 타일을 한 블록으로 (블록 안은 타일 순서대로 좌->우, 위->아래)"""
    W = cols*(bw*8+gap)+gap
    H = ((nblk+cols-1)//cols)*(bh*8+gap)+gap
    img = Image.new("L", (W, H), 128)
    px = img.load()
    tpb = bw*bh
    for k in range(nblk):
        base = off + k*tpb*32
        if base + tpb*32 > len(rom):
            break
        bx = (k % cols)*(bw*8+gap)+gap
        by = (k//cols)*(bh*8+gap)+gap
        for t in range(tpb):
            tile_px(base + t*32, px, bx + (t % bw)*8, by + (t//bw)*8)
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    p = os.path.join(paths.BUILD, name)
    img.save(p)
    return p


if __name__ == "__main__":
    off = int(sys.argv[1], 16)
    nblk = int(sys.argv[2])
    bw = int(sys.argv[3]); bh = int(sys.argv[4])
    cols = int(sys.argv[5]); nm = sys.argv[6]
    print(sheet(off, nblk, bw, bh, cols, nm))
