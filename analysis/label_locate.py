# -*- coding: utf-8 -*-
"""화면 캡처의 32×16 라벨이 롬 어디에서 왔는지 찾는다

팔레트를 모르므로 '획색 하나로 칠해진 글자 픽셀 배치'만 비교한다.
후보 오프셋마다 인덱스별 마스크를 만들어 화면 마스크와 가장 많이 겹치는 곳을 고른다.

사용: python analysis/label_locate.py <캡처> <화면x> <화면y> [lo16] [hi16]
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths

W, H = 32, 16


def rel_index():
    """32×16 1D 매핑 스프라이트의 픽셀 -> 스프라이트 시작 기준 니블 위치"""
    r = np.zeros(W*H, dtype=np.int64)
    for y in range(H):
        for x in range(W):
            t = (y//8)*(W//8) + x//8
            r[y*W + x] = t*64 + (y % 8)*8 + (x % 8)
    return r


def locate(rom, mask, lo, hi, step=4, topn=5):
    a = np.frombuffer(rom, dtype=np.uint8)
    nib = np.empty(len(a)*2, dtype=np.uint8)
    nib[0::2] = a & 15
    nib[1::2] = a >> 4
    base = np.arange(lo, hi, step)
    T = nib[base[:, None]*2 + rel_index()[None, :]]
    m = mask.reshape(-1)
    best = np.zeros(len(base), dtype=np.int32)
    bestv = np.zeros(len(base), dtype=np.uint8)
    for v in range(16):
        sc = ((T == v) == m[None, :]).sum(axis=1).astype(np.int32)
        up = sc > best
        best[up] = sc[up]
        bestv[up] = v
    order = np.argsort(-best)[:topn]
    return [(int(base[i]), int(best[i]), int(bestv[i])) for i in order]


if __name__ == "__main__":
    cap, sx, sy = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    lo = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x100000
    hi = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x300000
    a = np.array(Image.open(cap).convert("RGB")).astype(int)
    mask = (np.abs(a[sy:sy+H, sx:sx+W] - 248).max(axis=2) <= 24)
    print(f"화면({sx},{sy}) 글자 픽셀 {mask.sum()}칸")
    for r in mask:
        print("   " + "".join("#" if v else "." for v in r))
    for off, sc, v in locate(paths.read_rom_jp(), mask, lo, hi):
        print(f"  {off:#08x}  일치 {sc}/512  획색 인덱스 {v}")
