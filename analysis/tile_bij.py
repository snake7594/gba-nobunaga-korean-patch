# -*- coding: utf-8 -*-
"""화면 8×8 조각을 롬에서 찾는다 — 팔레트 없이 '색 ↔ 인덱스 일대일 대응'으로 판정

잉크 픽셀 배치만 비교하면 배경이 전부 '잉크 아님'으로 뭉뚱그려져 엉뚱한 곳이 걸린다.
여기서는 같은 색인 자리는 반드시 같은 인덱스, 다른 색인 자리는 반드시 다른 인덱스여야
통과시킨다. 조건은 두 가지뿐이라 벡터 연산으로 롬 전체를 몇 초에 훑는다.

    (a) 모든 자리 i 에서  T[i] == T[대표자리(색_i)]
    (b) 색마다의 대표 인덱스가 서로 전부 다르다
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths


def screen_ids(img, x0, y0, w=8, h=8):
    a = np.array(img.convert("RGB")).astype(int)[y0:y0+h, x0:x0+w]
    uniq, out = {}, np.zeros(w*h, int)
    for i, c in enumerate(map(tuple, a.reshape(-1, 3))):
        out[i] = uniq.setdefault(c, len(uniq))
    return out


class RomTiles:
    """롬을 4bpp/8bpp 타일 후보로 펼쳐 둔다"""

    def __init__(self, rom, step=4):
        a = np.frombuffer(rom, dtype=np.uint8)
        nib = np.empty(len(a)*2, dtype=np.uint8)
        nib[0::2] = a & 15
        nib[1::2] = a >> 4
        self.b4 = np.arange(0, len(a)-64, step)
        self.T4 = nib[self.b4[:, None]*2 + np.arange(64)[None, :]]
        self.b8 = np.arange(0, len(a)-128, step)
        self.T8 = a[self.b8[:, None] + np.arange(64)[None, :]]

    @staticmethod
    def _find(T, base, ids):
        k = ids.max()+1
        if k > 16:
            return np.array([], dtype=np.int64)
        rep = np.zeros(k, dtype=np.int64)
        for c in range(k):
            rep[c] = int(np.argmax(ids == c))
        R = T[:, rep]                                   # 색마다의 대표 인덱스
        ok = np.all(T == R[:, ids], axis=1)             # (a)
        for i in range(k):                              # (b)
            for j in range(i+1, k):
                ok &= R[:, i] != R[:, j]
        return base[ok]

    def find4(self, ids):
        return self._find(self.T4, self.b4, ids)

    def find8(self, ids):
        return self._find(self.T8, self.b8, ids)


if __name__ == "__main__":
    from PIL import Image
    img = Image.open(sys.argv[1])
    cx, cy = int(sys.argv[2]), int(sys.argv[3])
    span = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    R = RomTiles(paths.read_rom_jp())
    for dy in range(span):
        for dx in range(span):
            ids = screen_ids(img, cx+dx, cy+dy)
            k = ids.max()+1
            if k < 3 or k > 16:
                continue
            h4, h8 = R.find4(ids), R.find8(ids)
            if len(h4) or len(h8):
                print(f"화면({cx+dx},{cy+dy}) 색 {k}종  "
                      f"4bpp={[hex(v) for v in h4[:6]]}  8bpp={[hex(v) for v in h8[:6]]}")
