# -*- coding: utf-8 -*-
"""커맨드 버튼 스프라이트(32x16, 1D 8타일)의 색 인덱스를 ROM에서 직접 읽는다"""
import sys, os
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths

BASE, STRIDE = 0x233A24, 0x120


def btn_px(rom, k):
    """버튼 k -> (16,32) 팔레트 인덱스 배열"""
    a = np.zeros((16, 32), dtype=np.uint8)
    b0 = BASE + k*STRIDE
    for t in range(8):
        tx, ty = (t % 4)*8, (t//4)*8
        b = b0 + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                a[ty+y, tx+x] = v & 15
                a[ty+y, tx+x+1] = v >> 4
    return a


def btn_write(rom, k, a):
    """(16,32) 인덱스 배열을 버튼 k 자리에 다시 써 넣는다"""
    b0 = BASE + k*STRIDE
    for t in range(8):
        tx, ty = (t % 4)*8, (t//4)*8
        b = b0 + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                rom[b + y*4 + x//2] = (int(a[ty+y, tx+x]) & 15) | ((int(a[ty+y, tx+x+1]) & 15) << 4)


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    for k in (20, 21, 26, 3):
        a = btn_px(rom, k)
        c = Counter(a.reshape(-1).tolist())
        print(f"\n버튼 {k} (ROM {BASE+k*STRIDE:#08x}) : " +
              " ".join(f"{i}={n}" for i, n in c.most_common()))
        for y in range(16):
            print("   " + "".join(f"{v:X}" for v in a[y]))
