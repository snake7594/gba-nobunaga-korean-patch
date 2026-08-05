# -*- coding: utf-8 -*-
"""라벨 스프라이트(32×16, 위·아래 테두리가 한 색, 오른쪽 4px 투명) 자동 탐색"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spr_grid import grid


def row_px(rom, base, ty, y):
    """32px 가로줄 하나 -> 인덱스 16개(2px 씩)"""
    out = []
    for t in range(4):
        b = base + (ty*4+t)*32 + y*4
        for i in range(4):
            v = rom[b+i]
            out.append(v & 15)
            out.append(v >> 4)
    return out


def is_label(rom, base):
    if base + 8*32 > len(rom):
        return False
    top = row_px(rom, base, 0, 0)
    bot = row_px(rom, base, 1, 7)
    if any(v != 0 for v in top[28:]) or any(v != 0 for v in bot[28:]):
        return False
    c = top[0]
    if c == 0 or any(v != c for v in top[1:26]):
        return False
    d = bot[1]
    if d == 0 or any(v != d for v in bot[2:27]):
        return False
    # 속이 비어 있으면(전부 같은 색) 라벨이 아니다
    mid = row_px(rom, base, 0, 6) + row_px(rom, base, 1, 3)
    return len(set(mid[:28])) >= 3


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x220000
    hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x260000
    hits = [b for b in range(lo, hi, 4) if is_label(rom, b)]
    print(f"{len(hits)}개 후보")
    runs, prev = [], None
    for b in hits:
        if prev is None or b - prev > 0x400:
            runs.append([b, b])
        else:
            runs[-1][1] = b
        prev = b
    for s, e in runs:
        print(f"  {s:#08x} ~ {e:#08x}  ({(e-s)//32+8}타일)")
    with open(os.path.join(paths.BUILD, "spr_hits.txt"), "w") as f:
        f.write("\n".join(f"{b:#08x}" for b in hits))
    grid(rom, 0, 0, 1, 8, 8, name="_dummy.png") if False else None
