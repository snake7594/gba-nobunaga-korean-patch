# -*- coding: utf-8 -*-
"""타이틀 로고(信長の野望)를 한글로 교체해 ROM 에 기록.

이 게임은 거의 모든 문자를 폰트로 그린다. 이미지에 일본어가 박혀 있는 곳은
타이틀 로고뿐이며, 그 로고는 BG0(8bpp) 배경 그림에 통째로 그려져 있다.

    VRAM char 0x4000 <- ROM 0x08002C  (타일 0~203)
    VRAM 0x7400      <- ROM 0x0596F0  (타일 208~)
    화면 맵          <- VRAM 0xE000   (30x20)

로고 픽셀을 지우고 배경을 메운 뒤 한글을 그려 넣고, 같은 팔레트로
8bpp 인덱스화해 해당 타일만 덮어쓴다. 타일맵과 팔레트는 건드리지 않는다.
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

# VRAM 타일 -> ROM 오프셋 (VRAM 덤프를 ROM 에서 역검색해 확인한 값)
SEGMENTS = [(0, 204, 0x08002C), (204, 640, 0x0595F0)]


def rom_off(tile):
    for lo, hi, base in SEGMENTS:
        if lo <= tile < hi:
            return base + (tile - lo) * 64
    return None


def patch(rom, newidx, grid, report=None):
    """newidx: (160,240) 팔레트 인덱스, grid: (20,30) 타일 인덱스

    같은 타일을 여러 칸이 공유할 수 있다. 그럴 때 '글자를 지운 새 내용'과
    '원래 그대로'가 충돌하는데, 그냥 건너뛰면 지워야 할 획이 남는다.
    충돌 시에는 원본과 가장 많이 다른 쪽(=글자를 지운 결과)을 채택한다.
    배경 무늬는 어디서 쓰이든 같은 그림이라 이렇게 해도 안전하다.
    """
    newidx = np.asarray(newidx, dtype=np.uint8)
    cells = {}
    for sy in range(20):
        for sx in range(30):
            t = int(grid[sy][sx])
            blk = bytes(newidx[sy*8:sy*8+8, sx*8:sx*8+8].reshape(-1))
            cells.setdefault(t, []).append(blk)

    written = resolved = skipped = 0
    for t, blks in cells.items():
        off = rom_off(t)
        if off is None:
            skipped += 1
            continue
        orig = bytes(rom[off:off+64])
        uniq = sorted(set(blks))          # set 순회는 비결정적 -> 정렬해 재현성 확보
        if len(uniq) == 1:
            blk = uniq[0]
        else:
            blk = max(uniq, key=lambda b: sum(1 for a, c in zip(b, orig) if a != c))
            resolved += 1
        if orig != blk:
            rom[off:off+64] = blk
            written += 1
    if report is not None:
        report.update(tiles=len(cells), written=written,
                      resolved=resolved, skipped=skipped)
    return rom


def main():
    data = json.load(open(paths.inp("logo_new.json"), encoding="utf-8"))
    newidx = np.array(data["idx"], dtype=np.uint8)
    grid = data["grid"]
    src = paths.rom_kr() if os.path.exists(paths.rom_kr()) else paths.rom_jp()
    rom = bytearray(open(src, "rb").read())
    rep = {}
    patch(rom, newidx, grid, rep)
    open(paths.rom_kr(), "wb").write(rom)
    print(f"타이틀 로고: 타일 {rep['tiles']}개 중 {rep['written']}개 기록 "
          f"(공유타일 해소 {rep['resolved']}, 범위밖 {rep['skipped']})")
    print("written:", paths.rom_kr())


if __name__ == "__main__":
    main()
