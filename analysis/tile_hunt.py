# -*- coding: utf-8 -*-
"""화면에 보이는 8×8 타일 그림을 ROM 에서 역검색한다

VRAM 덤프 없이 '화면 캡처 → 원본 위치' 를 찾기 위한 도구.
잉크 픽셀의 배치만 비교하므로 팔레트를 몰라도 된다.

원리
    한 타일 안에서 글자(잉크)는 팔레트 인덱스 하나로 칠해져 있다.
    그래서 후보 타일에서 '첫 잉크 자리의 값'을 잉크색으로 잡고,
    그 값의 마스크가 화면에서 뜬 마스크와 정확히 같은지만 보면 된다.
    (인덱스 16가지를 다 돌 필요가 없어 롬 전체를 몇 초에 훑는다)

    타일 정렬을 모르므로 화면 쪽 8×8 창을 x·y 로 밀어 가며 전부 시도한다.
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths


def screen_ink(path, ink=(248, 248, 248), tol=8):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    return (np.abs(a - np.array(ink)).max(axis=2) <= tol)


class Rom:
    """롬을 4bpp/8bpp 타일 후보 배열로 펼쳐 둔다 (한 번만 만들면 재사용)"""

    def __init__(self, rom, step=4):
        a = np.frombuffer(rom, dtype=np.uint8)
        self.step = step
        nib = np.empty(len(a)*2, dtype=np.uint8)
        nib[0::2] = a & 15
        nib[1::2] = a >> 4
        b4 = np.arange(0, len(a)-64, step)
        self.b4 = b4
        self.T4 = nib[b4[:, None]*2 + np.arange(64)[None, :]]
        b8 = np.arange(0, len(a)-128, step)
        self.b8 = b8
        self.T8 = a[b8[:, None] + np.arange(64)[None, :]]

    @staticmethod
    def _match(T, base, mask):
        first = int(np.argmax(mask))
        v = T[:, first]
        hit = np.all((T == v[:, None]) == mask[None, :], axis=1)
        return base[hit]

    def find(self, mask):
        return (self._match(self.T4, self.b4, mask),
                self._match(self.T8, self.b8, mask))


def sweep(rom_idx, ink, x0, y0, span=8):
    """(x0,y0) 근처에서 타일 정렬을 밀어 가며 찾는다 -> [(dx, dy, 4bpp후보, 8bpp후보)]"""
    out = []
    for dy in range(span):
        for dx in range(span):
            m = ink[y0+dy:y0+dy+8, x0+dx:x0+dx+8].reshape(-1)
            if m.shape[0] != 64 or m.sum() < 8:
                continue
            h4, h8 = rom_idx.find(m)
            if len(h4) or len(h8):
                out.append((x0+dx, y0+dy, h4, h8))
    return out


if __name__ == "__main__":
    cap = sys.argv[1]
    x0, y0 = int(sys.argv[2]), int(sys.argv[3])
    ink = screen_ink(cap)
    R = Rom(paths.read_rom_jp())
    for x, y, h4, h8 in sweep(R, ink, x0, y0):
        print(f"화면({x},{y})  4bpp={[hex(v) for v in h4[:6]]}  8bpp={[hex(v) for v in h8[:6]]}")
