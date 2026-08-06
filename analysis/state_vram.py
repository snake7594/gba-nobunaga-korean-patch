# -*- coding: utf-8 -*-
"""mGBA 세이브스테이트에서 VRAM 을 꺼내 화면 라벨의 원본 위치를 찾는다

에뮬레이터를 조작하지 않고 파일만으로 처리하기 위한 경로다.
(GDB 서버를 켜 두었다면 analysis/grab.py 로도 같은 덤프를 얻을 수 있다)

세이브스테이트 구조는 mGBA 판올림마다 조금씩 달라 오프셋을 박아 두지 않는다.
대신 'VRAM 은 롬에서 그대로 복사돼 온다'는 성질을 써서 위치를 찾는다.
64바이트씩 떠서 롬에 그대로 있는 비율이 가장 높은 구간이 VRAM 이다.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths

VRAM_SIZE = 0x18000


def find_vram(state, rom, probe=0x400):
    """세이브스테이트 안에서 VRAM 시작 위치를 찾는다"""
    hits = []
    for off in range(0, len(state)-64, probe):
        c = state[off:off+64]
        if c.count(c[0:1]) > 56:            # 단색 덩어리는 판단 근거가 못 된다
            hits.append((off, None))
            continue
        hits.append((off, rom.find(c) >= 0))
    # 롬에 있는 조각이 연달아 나오는 구간
    best, run, start = (0, None), 0, None
    for off, ok in hits:
        if ok:
            if start is None:
                start = off
            run += 1
            if run > best[0]:
                best = (run, start)
        elif ok is False:
            run, start = 0, None
    return best[1]


def tiles(vram, bpp=4):
    n = 32 if bpp == 4 else 64
    return len(vram)//n


def tile_px(vram, idx, bpp=4):
    """VRAM 타일 하나 -> 8×8 인덱스 배열"""
    if bpp == 4:
        b = vram[idx*32: idx*32+32]
        a = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(0, 8, 2):
                v = b[y*4 + x//2]
                a[y, x] = v & 15
                a[y, x+1] = v >> 4
        return a
    b = vram[idx*64: idx*64+64]
    return np.frombuffer(b, np.uint8).reshape(8, 8).copy()


def screen_ids(img, x0, y0, w, h):
    """화면 조각을 '같은 색끼리 같은 번호'로 바꾼다 (팔레트를 몰라도 비교 가능)"""
    a = np.array(img.convert("RGB")).astype(int)[y0:y0+h, x0:x0+w]
    uniq, out = {}, np.zeros((h, w), int)
    for y in range(h):
        for x in range(w):
            out[y, x] = uniq.setdefault(tuple(a[y, x]), len(uniq))
    return out


def bijective(S, R):
    """색 번호 <-> 인덱스가 일대일로 대응하면 같은 그림이다"""
    f, g = {}, {}
    for s, r in zip(np.ravel(S), np.ravel(R)):
        s, r = int(s), int(r)
        if f.setdefault(s, r) != r or g.setdefault(r, s) != s:
            return False
    return True


def match_screen(vram, img, x0, y0, bpp=4):
    """화면 8×8 조각과 같은 VRAM 타일 번호들"""
    S = screen_ids(img, x0, y0, 8, 8)
    out = []
    for t in range(tiles(vram, bpp)):
        if bijective(S, tile_px(vram, t, bpp)):
            out.append(t)
    return out


if __name__ == "__main__":
    from PIL import Image
    st = open(sys.argv[1], "rb").read()
    rom = paths.read_rom_jp()
    base = find_vram(st, rom)
    if base is None:
        sys.exit("VRAM 을 찾지 못했습니다")
    print(f"세이브스테이트 {len(st):#x} 바이트 · VRAM 추정 시작 {base:#x}")
    vram = st[base: base+VRAM_SIZE]
    if len(sys.argv) > 4:
        img = Image.open(sys.argv[2])
        x0, y0 = int(sys.argv[3]), int(sys.argv[4])
        for bpp in (4, 8):
            ts = match_screen(vram, img, x0, y0, bpp)
            for t in ts:
                n = 32 if bpp == 4 else 64
                chunk = vram[t*n:(t+1)*n]
                r = rom.find(chunk)
                print(f"  {bpp}bpp VRAM 타일 {t}({t*n:#x}) -> ROM "
                      f"{'없음' if r < 0 else hex(r)}")
