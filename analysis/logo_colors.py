# -*- coding: utf-8 -*-
"""타이틀 로고의 색 구조 분석 — 글자(크림/빨강/그림자)와 배경 분리"""
import sys, os, struct
from collections import Counter
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
vram = open(os.path.join(S, "vram_s01_title.bin"), "rb").read()
pram = open(os.path.join(S, "pram_s01_title.bin"), "rb").read()
CHAR, SCR = 0x4000, 0xE000


def col(i):
    v = struct.unpack_from("<H", pram, i*2)[0]
    return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)


# 화면 인덱스맵 (240x160, 8bpp 팔레트 인덱스)
idx = [[0]*240 for _ in range(160)]
for sy in range(20):
    for sx in range(30):
        e = struct.unpack_from("<H", vram, SCR + (sy*32+sx)*2)[0]
        t = e & 0x3FF
        for y in range(8):
            for x in range(8):
                idx[sy*8+y][sx*8+x] = vram[CHAR + t*64 + y*8 + x]

cnt = Counter()
for r in idx:
    cnt.update(r)
print("색 사용 상위 24 (인덱스, 횟수, RGB):")
for i, n in cnt.most_common(24):
    print(f"   {i:3d} {n:6d}  {col(i)}")

# 글자 영역 추정: 밝은 크림색(높은 R,G,B) 위주
bright = [i for i in cnt if sum(col(i)) > 480]
print("\n밝은 색(크림) 인덱스:", bright)
rows = [y for y in range(160) if any(idx[y][x] in bright for x in range(240))]
cols = [x for x in range(240) if any(idx[y][x] in bright for y in range(160))]
print(f"밝은 글자 bbox: x {min(cols)}~{max(cols)}, y {min(rows)}~{max(rows)}")

import json
json.dump({"idx": idx, "bright": bright,
           "pal": [col(i) for i in range(256)]},
          open(os.path.join(paths.BUILD, "logo_px.json"), "w"))
print("saved build/logo_px.json")
