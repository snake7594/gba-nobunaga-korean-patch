# -*- coding: utf-8 -*-
"""테두리가 있는 라벨 스프라이트를 폭 16/24/32 로 전부 찾아 목록화

라벨 양식
    위·왼쪽 테두리가 한 색, 아래·오른쪽 테두리가 다른 한 색인 액자 모양.
    안쪽은 세로 그라데이션 디더 + 글자. OBJ 1D 매핑이라 타일이 순서대로 이어진다.
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths


def block(rom, base, w, h=16):
    tw = w//8
    a = np.zeros((h, w), dtype=np.uint8)
    for t in range((w*h)//64):
        tx, ty = (t % tw)*8, (t//tw)*8
        b = base + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                a[ty+y, tx+x] = v & 15
                a[ty+y, tx+x+1] = v >> 4
    return a


def framed(a):
    """액자 조건을 만족하면 (위색, 아래색) 반환"""
    h, w = a.shape
    top, bot = a[0, :-1], a[-1, 1:]
    lft, rgt = a[:-1, 0], a[1:, -1]
    if len(set(top.tolist())) != 1 or len(set(bot.tolist())) != 1:
        return None
    if len(set(lft.tolist())) != 1 or len(set(rgt.tolist())) != 1:
        return None
    ct, cb = int(top[0]), int(bot[0])
    if ct == 0 or cb == 0 or ct == cb:
        return None
    if int(lft[0]) != ct or int(rgt[0]) != cb:
        return None
    inner = a[2:h-2, 2:w-2]
    return (ct, cb) if len(set(inner.reshape(-1).tolist())) >= 3 else None


def scan(rom, lo, hi, widths=(32, 24, 16)):
    hits = []
    for w in widths:
        need = (w*16)//64*32
        for b in range(lo, hi-need, 4):
            a = block(rom, b, w)
            f = framed(a)
            if f:
                hits.append({"off": b, "w": w, "end": b+need, "frame": f})
    # 겹치면 폭이 큰 쪽을 남긴다
    hits.sort(key=lambda d: (d["off"], -d["w"]))
    out = []
    for h in hits:
        if out and h["off"] < out[-1]["end"]:
            if h["w"] > out[-1]["w"]:
                out[-1] = h
            continue
        out.append(h)
    return out


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    lo = int(sys.argv[1], 16)
    hi = int(sys.argv[2], 16)
    hs = scan(rom, lo, hi)
    print(f"라벨 {len(hs)}개")
    for h in hs:
        print(f"  {h['off']:#08x} w={h['w']} frame={h['frame']}")
    json.dump(hs, open(os.path.join(paths.BUILD, "labels.json"), "w"))
