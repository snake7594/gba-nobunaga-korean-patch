# -*- coding: utf-8 -*-
"""4bpp 타일 그래픽의 자연스러운 폭(타일 수)을 세로 연속성으로 추정"""
import sys
import numpy as np
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = np.frombuffer(paths.read_rom_jp(), dtype=np.uint8)


def tiles_to_rows(off, ntiles):
    """타일 목록 -> (ntiles, 8, 8) 픽셀"""
    d = rom[off:off+ntiles*32].reshape(ntiles, 8, 4)
    lo = d & 0x0F
    hi = d >> 4
    out = np.empty((ntiles, 8, 8), dtype=np.uint8)
    out[:, :, 0::2] = lo
    out[:, :, 1::2] = hi
    return out


def score(off, ntiles, w):
    t = tiles_to_rows(off, ntiles)
    rows = ntiles // w
    if rows < 3:
        return -1
    img = t[:rows*w].reshape(rows, w, 8, 8).transpose(0, 2, 1, 3).reshape(rows*8, w*8)
    # 세로 인접 픽셀 일치율 (자연스러운 이미지일수록 높음)
    return float((img[1:] == img[:-1]).mean())


if __name__ == "__main__":
    off = int(sys.argv[1], 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    best = []
    for w in range(4, 65):
        s = score(off, n, w)
        best.append((s, w))
    best.sort(reverse=True)
    print(f"{off:#x} ({n}타일) 폭 후보:")
    for s, w in best[:10]:
        print(f"   폭 {w:3d} 타일 ({w*8:4d}px)  세로연속 {s:.4f}")
