# -*- coding: utf-8 -*-
"""ROM 전역에서 4bpp 타일 그래픽 후보 영역을 찾는다.

GBA 4bpp: 8x8 타일 = 32바이트, 픽셀 2개당 1바이트(하위 니블이 왼쪽).
글자가 들어간 그래픽은 색 수가 적고(외곽선+면+그림자+투명) 0 니블이 많다.
"""
import sys
from collections import Counter
import numpy as np
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

rom = np.frombuffer(paths.read_rom_jp(), dtype=np.uint8)
LIMIT = 0x33A200

lo = rom[:LIMIT] & 0x0F
hi = rom[:LIMIT] >> 4

BS = 0x2000     # 8KB = 256 타일
print(f"{'offset':>10} {'zero%':>6} {'ncol':>5} {'edge':>6}  판정")
cands = []
for off in range(0, LIMIT, BS):
    a, b = lo[off:off+BS], hi[off:off+BS]
    if len(a) < BS:
        break
    nib = np.concatenate([a, b])
    zero = float((nib == 0).mean())
    cnt = np.bincount(nib, minlength=16)
    ncol = int((cnt > len(nib) * 0.002).sum())      # 유의미하게 쓰인 색 수
    # 가로 인접 픽셀 변화율 (그래픽은 완만, 코드/데이터는 난잡)
    edge = float((a != b).mean())
    tag = ""
    if 0.05 < zero < 0.92 and 2 <= ncol <= 16 and edge < 0.75:
        tag = "GFX?"
        cands.append(off)
    if tag or off % 0x40000 == 0:
        print(f"{off:#010x} {zero:6.3f} {ncol:5d} {edge:6.3f}  {tag}")

# 연속 구간으로 묶기
runs = []
cur = None
for o in cands:
    if cur and o == cur[1] + BS:
        cur[1] = o
    else:
        if cur:
            runs.append(cur)
        cur = [o, o]
if cur:
    runs.append(cur)
print(f"\n후보 구간 {len(runs)}개 (>=16KB 만):")
for a, b in runs:
    if b - a >= 0x4000:
        print(f"  {a:#08x}-{b+BS:#08x}  {(b+BS-a)/1024:.0f}KB")
