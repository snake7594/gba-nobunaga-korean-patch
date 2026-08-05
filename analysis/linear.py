# -*- coding: utf-8 -*-
"""선형 4bpp/8bpp 비트맵으로 렌더 + 최적 폭 탐색"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = np.frombuffer(paths.read_rom_jp(), dtype=np.uint8)


def px4(off, n):
    d = rom[off:off+n]
    out = np.empty(n*2, dtype=np.uint8)
    out[0::2] = d & 0x0F
    out[1::2] = d >> 4
    return out


def px8(off, n):
    return rom[off:off+n].astype(np.uint8)


def best_width(off, nbytes, mode="4"):
    p = px4(off, nbytes) if mode == "4" else px8(off, nbytes)
    res = []
    for w in range(32, 513, 8):
        rows = len(p)//w
        if rows < 8:
            continue
        img = p[:rows*w].reshape(rows, w)
        s = float((img[1:] == img[:-1]).mean())
        res.append((s, w))
    res.sort(reverse=True)
    return res[:6]


def render(off, nbytes, w, name, mode="4", scale=2):
    p = px4(off, nbytes) if mode == "4" else px8(off, nbytes)
    rows = len(p)//w
    a = p[:rows*w].reshape(rows, w)
    if mode == "4":
        a = (a * 17).astype(np.uint8)
    img = Image.fromarray(255 - a, "L")
    img = img.resize((w*scale, rows*scale), Image.NEAREST)
    pth = os.path.join(paths.BUILD, name)
    img.save(pth)
    return pth


if __name__ == "__main__":
    off = int(sys.argv[1], 16)
    n = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x4000
    print("4bpp 폭 후보:", best_width(off, n, "4"))
    print("8bpp 폭 후보:", best_width(off, n, "8"))
