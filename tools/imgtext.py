# -*- coding: utf-8 -*-
"""이미지로 그려진 일본어 UI 라벨을 한글로 교체한다

대상
    커맨드 버튼, 상태창 항목명, 합전 명령 — 전부 32×16 4bpp OBJ 스프라이트다.
    OBJ 1D 매핑이라 타일 8개(가로4×세로2)가 순서대로 나열되고, 배열마다
    일정한 stride 로 이어진다.

색 구조
    배경  : 세로 그라데이션을 2색 체커 디더로 표현. 색은 y 와 (x+y)&1 로 정해진다.
    글자  : 어두운 획색 A + 오른쪽아래 1px 하이라이트 B (음각 효과).
    A/B 와 배경색은 계열(내정/군사/외교/상태창…)마다 달라 자동으로 판별한다.

빈 판 복원
    한 라벨 안에서는 획 픽셀이 배경보다 많을 수 있어 단순 최빈값으로는 글자가
    안 지워진다. 그래서 (1) 테두리 쪽에 쓰인 색만 배경 후보로 두고,
    (2) 라벨마다 그 줄의 최빈 후보색을 뽑은 뒤 라벨 전체로 다시 다수결하고,
    (3) 여러 줄에 걸쳐 나오는 '색 사다리'에서 벗어난 칸은 사다리 안에서 다시 뽑는다.
    폭이 다른 라벨(24/32/64px)도 x 원점과 디더 위상이 같아 한 계열로 묶는다.
"""
import os, sys
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from bdf import load_bdf, render12

H = 16

# ---------------- 배열 정의 ----------------
CMD = {
    3: "개간", 4: "치수", 5: "상업", 6: "기술", 7: "축성",
    8: "금산", 9: "교역", 10: "조략", 11: "외교", 12: "첩보",
    13: "위임", 14: "직할", 15: "교육", 16: "추방", 17: "포상",
    18: "몰수", 19: "다회", 20: "이동", 21: "수송", 22: "전투",
    23: "공동", 24: "고용", 25: "훈련", 26: "시혜", 27: "제조",
    28: "매입", 29: "매각", 30: "철포", 31: "다기", 32: "철포",
    33: "철갑", 34: "매수", 35: "유언", 36: "적대", 37: "공물",
    38: "동맹", 39: "혼인", 40: "협박", 41: "단교",
}
ST_A = ["동맹", "가문", "혼인", "우호", "문화", "무장",
        "치수", "기술", "병충", "병수", "병량"]
ST_B = ["위임", "금", "국", "훈련", "민충", "성방", "석고", "상업", "철포"]
WAR = ["이동", "통상", "돌격", "철포", "파괴", "대포", "진언", "지형",
       "부대", "이웃", "성내", "권고", "개문", "출진", "위임", "대기"]

# 무장 능력치 라벨 (그려지는 폭 24px)
STAT24 = [(0x237704, "충성"), (0x237824, "다기"), (0x237A64, "교양"),
          (0x237FA4, "매력"), (0x2380C4, "연령"), (0x2381E4, "정치"),
          (0x2383A4, "전투"), (0x2384C4, "철갑"), (0x2385E4, "야망")]
# 64px 폭 제목 라벨
WIDE64 = [(0x2372E4, "무장명"), (0x238E44, "다이묘"), (0x239EC4, "성주")]

ARRAYS = [
    # 커맨드 버튼 — 오른쪽 4px 가 투명이라 실제 폭 28px
    dict(key="cmd", base=0x233A24, stride=0x120, n=42, w=32, lo=0, hi=27,
         inset=(2, 25, 2, 13), items=CMD),
    # 상태창 항목명 (액자형, 폭 32px)
    dict(key="stA", base=0x239264, stride=0x120, n=11, w=32, lo=0, hi=31,
         inset=(2, 29, 2, 13), items=dict(enumerate(ST_A))),
    dict(key="stB", base=0x23A2E4, stride=0x120, n=9, w=32, lo=0, hi=31,
         inset=(2, 29, 2, 13), items=dict(enumerate(ST_B))),
    # 합전 명령
    dict(key="war", base=0x153400, stride=0x100, n=16, w=32, lo=0, hi=31,
         inset=(2, 29, 2, 13), items=dict(enumerate(WAR))),
    dict(key="war2", base=0x154420, stride=0x100, n=1, w=32, lo=0, hi=31,
         inset=(2, 29, 2, 13), items={0: "이동"}),
    # 무장 능력치 이름
    # 이 판은 글자가 x=1 까지 닿는다. 배경 후보색을 모을 때 획이 섞이지 않도록
    # 글자칸을 1~22 로 잡아 테두리(0, 23)만 후보 수집에 쓰이게 한다.
    dict(key="stat", offs=[o for o, _ in STAT24], w=32, lo=0, hi=23,
         inset=(1, 22, 2, 13), items={i: t for i, (_, t) in enumerate(STAT24)}),
    # 선택 강조된 '決定' (왼쪽 4px 여백, 배색이 반전돼 있다)
    dict(key="ok", offs=[0x237944], w=32, lo=4, hi=27,
         inset=(6, 25, 2, 13), items={0: "결정"}),
    # 64px 폭 제목
    dict(key="wide", offs=[o for o, _ in WIDE64], w=64, lo=0, hi=63,
         inset=(2, 61, 2, 13), items={i: t for i, (_, t) in enumerate(WIDE64)}),
]


# ---------------- 타일 <-> 배열 ----------------
def read(rom, off, w=32):
    """스프라이트 폭 w(=32/64) 의 16줄을 인덱스 배열로 읽는다 (OBJ 1D 매핑)"""
    tw = w//8
    a = np.zeros((H, w), dtype=np.uint8)
    for t in range(tw*2):
        tx, ty = (t % tw)*8, (t//tw)*8
        b = off + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                a[ty+y, tx+x] = v & 15
                a[ty+y, tx+x+1] = v >> 4
    return a


def write(rom, off, a):
    w = a.shape[1]
    tw = w//8
    for t in range(tw*2):
        tx, ty = (t % tw)*8, (t//tw)*8
        b = off + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                rom[b + y*4 + x//2] = ((int(a[ty+y, tx+x]) & 15) |
                                       ((int(a[ty+y, tx+x+1]) & 15) << 4))


# ---------------- 빈 판 복원 ----------------
def _mode(vals, fallback=0):
    c = Counter(vals)
    return c.most_common(1)[0][0] if c else fallback


def sig(a, lo, hi):
    """테두리 색 지문 — 같은 계열끼리 묶는 열쇠"""
    return (int(a[0, lo+1]), int(a[1, lo+1]), int(a[14, lo+1]), int(a[15, lo+1]),
            int(a[5, lo]), int(a[5, hi]))


def fill_box(arr):
    """빈 판을 다시 그려야 할 안쪽 영역 — 테두리 1px 을 뺀 전부"""
    return (arr["lo"]+1, arr["hi"]-1, 1, H-2)


def dither(members, ladder=None):
    """배경 디더표 {(y, (x+y)&1): 색}

    두 단계로 획을 걸러낸다.
      1. 테두리와 글자칸 바깥 줄에 한 번이라도 쓰인 색만 배경 후보로 둔다.
      2. 라벨마다 그 줄의 최빈 후보색을 뽑고(1차), 라벨 전체로 다시 다수결한다(2차).
    글자가 x=1 까지 닿는 라벨 때문에 1 만으로는 획색이 후보에 섞이지만,
    2차 투표에서 밀려 배경만 남는다. 폭이 다른 라벨(24/32/64px)도 x 원점과
    디더 위상이 같아 한 계열로 묶어 쓸 수 있다."""
    edge = set()
    for a, lo, hi, (x0, x1, y0, y1) in members:
        for y in list(range(0, y0)) + list(range(y1+2, H)):
            edge |= set(a[y, lo:hi+1].tolist())
        for x in list(range(lo, x0)) + list(range(x1+2, hi+1)):
            edge |= set(a[:, x].tolist())
    pools = {}
    for a, lo, hi, (x0, x1, y0, y1) in members:
        for y in range(1, H-1):
            for p in (0, 1):
                xs = [x for x in range(lo+1, hi) if (x+y) & 1 == p]
                vals = [int(a[y, x]) for x in xs if int(a[y, x]) in edge]
                if vals:
                    pools.setdefault((y, p), []).append(vals)

    def vote(k, allow=None):
        ms = [_mode([v for v in vals if allow is None or v in allow])
              for vals in pools[k] if allow is None or any(v in allow for v in vals)]
        return _mode(ms) if ms else None

    tab = {k: vote(k) for k in pools}
    # 배경은 위에서 아래로 이어지는 색 사다리다. 여러 줄에 걸쳐 나오는 색만
    # 사다리로 인정하고, 한두 칸에서만 튀는 색(대개 하이라이트)은 다시 뽑는다.
    # 라벨이 두세 장뿐인 계열은 스스로 사다리를 못 찾으므로 밖에서 받아 쓴다.
    if ladder is None:
        ladder = {v for v, k in Counter(tab.values()).items() if k >= 3}
    for k, v in list(tab.items()):
        if v not in ladder:
            tab[k] = vote(k, ladder) or v
    return tab


def blank(arrs, inset, tab):
    """디더표를 써서 글자 없는 판을 만든다 (테두리는 픽셀별 최빈값)"""
    x0, x1, y0, y1 = inset
    st = np.stack(arrs)
    w = st.shape[2]
    t = np.zeros((H, w), dtype=np.uint8)
    for y in range(H):
        for x in range(w):
            t[y, x] = _mode(st[:, y, x].tolist())
    for y in range(y0, y1+1):
        for x in range(x0, x1+1):
            v = tab.get((y, (x+y) & 1))
            if v is not None:
                t[y, x] = v
    return t


def ink_colors(a, t, inset):
    """(획색 A, 하이라이트색 B) — 글자 픽셀 중 맨 윗줄 색이 획이다"""
    x0, x1, y0, y1 = inset
    diff = [(y, int(a[y, x])) for y in range(y0, y1+1)
            for x in range(x0, x1+1) if a[y, x] != t[y, x]]
    if not diff:
        return None, None
    top = min(y for y, _ in diff)
    ca = _mode([c for y, c in diff if y == top])
    rest = [c for _, c in diff if c != ca]
    return ca, (_mode(rest, ca) if rest else ca)


def ink_box(a, t, inset):
    x0, x1, y0, y1 = inset
    pts = [(y, x) for y in range(y0, y1+1) for x in range(x0, x1+1)
           if a[y, x] != t[y, x]]
    if not pts:
        return None
    ys = [p[0] for p in pts]
    xs = [p[1] for p in pts]
    return min(ys), max(ys), min(xs), max(xs)


# ---------------- 한글 렌더 ----------------
class Painter:
    """갈무리11(보통)과 Condensed 를 함께 들고, 칸 폭에 맞는 쪽을 골라 쓴다"""

    FONTS = ("Galmuri11.bdf", "Galmuri11-Condensed.bdf")

    def __init__(self):
        self.f = [load_bdf(paths.font(n))[0:3] for n in self.FONTS]

    def _glyph(self, fi, ch):
        glyphs, _fbbx, ascent = self.f[fi]
        r = render12(glyphs, ascent, ord(ch), W=12, H=16)
        if r is None:
            raise KeyError(f"{self.FONTS[fi]} 에 없는 글자: {ch}")
        bm = np.zeros((12, 12), dtype=bool)
        for y in range(12):
            v = r[3+y]
            for x in range(12):
                if (v >> (11-x)) & 1:
                    bm[y, x] = True
        cs = np.where(bm.any(axis=0))[0]
        return bm[:, cs.min():cs.max()+1] if len(cs) else bm[:, :1]

    def body(self, text, fi=0, gap=1):
        """글자마다 좌우 여백을 떼고 gap 칸씩 띄워 이어 붙인다"""
        gs = [self._glyph(fi, ch) for ch in text]
        w = sum(g.shape[1] for g in gs) + gap*(len(gs)-1)
        bm = np.zeros((12, w), dtype=bool)
        x = 0
        for g in gs:
            bm[:, x:x+g.shape[1]] = g
            x += g.shape[1] + gap
        rs = np.where(bm.any(axis=1))[0]
        return bm[rs.min():rs.max()+1]

    def fit(self, text, avail):
        """avail 픽셀 안에 들어가는 가장 큰 조합을 고른다"""
        for fi, gap in ((0, 1), (0, 0), (1, 1), (1, 0)):
            b = self.body(text, fi, gap)
            if b.shape[1] <= avail:
                return b
        return self.body(text, 1, 0)


def paint(a, t, text, painter, inset, cell=12):
    x0, x1, y0, y1 = inset
    ca, cb = ink_colors(a, t, inset)
    if ca is None:
        return None
    by0, by1, bx0, bx1 = ink_box(a, t, inset)
    body = painter.fit(text, x1 - x0)        # 오른쪽 하이라이트 1px 자리를 남긴다
    gh, gw = body.shape

    ow, oh = (bx1-bx0+1) - 1, (by1-by0+1) - 1     # 하이라이트 1px 제외한 원본 크기
    ox = max(x0, min(bx0 + max(0, (ow-gw)//2), x1 - gw))
    oy = max(y0, min(by0 + max(0, (oh-gh)//2), y1 - gh))

    out = t.copy()
    for y in range(gh):                            # 하이라이트 먼저
        for x in range(gw):
            if body[y, x] and y0 <= oy+y+1 <= y1+1 and x0 <= ox+x+1 <= x1+1:
                out[oy+y+1, ox+x+1] = cb
    for y in range(gh):                            # 획을 위에 덮어쓴다
        for x in range(gw):
            if body[y, x]:
                out[oy+y, ox+x] = ca
    return out


# ---------------- 진입점 ----------------
def patch(rom, cell=12, arrays=None):
    """rom(bytearray)의 이미지 라벨을 한글로 교체. 바꾼 개수를 돌려준다."""
    arrays = ARRAYS if arrays is None else arrays
    p = Painter()
    done = 0

    # 1) 전부 읽어 테두리 지문으로 계열을 나눈다 (배열 경계를 넘어 묶인다)
    loaded = []
    for arr in arrays:
        offs = arr.get("offs") or [arr["base"] + k*arr["stride"]
                                   for k in range(arr["n"])]
        blocks = [read(rom, o, arr["w"]) for o in offs]
        loaded.append((arr, offs, blocks, fill_box(arr)))
    fam = {}
    for arr, _offs, blocks, fl in loaded:
        for b in blocks:
            fam.setdefault(sig(b, arr["lo"], arr["hi"]), []).append(
                (b, arr["lo"], arr["hi"], arr["inset"]))

    # 2) 계열마다 배경 디더표를 만든다.
    #    라벨이 3장 미만인 계열은 같은 배열의 최대 계열이 찾아낸 색 사다리를 빌려 쓴다.
    tabs = {s: dither(ms) for s, ms in fam.items()}
    for arr, _offs, blocks, _fl in loaded:
        sigs = [sig(b, arr["lo"], arr["hi"]) for b in blocks]
        big = max(set(sigs), key=lambda s: len(fam[s]))
        ladder = {v for v, k in Counter(tabs[big].values()).items() if k >= 3}
        if not ladder:
            continue
        for s in set(sigs):
            if len(fam[s]) < 3:
                tabs[s] = dither(fam[s], ladder)

    # 3) 배열별로 빈 판을 만들고 한글을 그려 넣는다
    for arr, offs, blocks, fl in loaded:
        lo, hi = arr["lo"], arr["hi"]
        groups = {}
        for i, b in enumerate(blocks):
            groups.setdefault(sig(b, lo, hi), []).append(i)
        tpl = {s: blank([blocks[i] for i in ix], fl, tabs[s])
               for s, ix in groups.items()}
        for k, text in sorted(arr["items"].items()):
            a = blocks[k]
            out = paint(a, tpl[sig(a, lo, hi)], text, p, arr["inset"], cell)
            if out is None:
                continue
            write(rom, offs[k], out)
            done += 1
    return done


def main():
    src = paths.rom_kr() if os.path.exists(paths.rom_kr()) else paths.rom_jp()
    rom = bytearray(open(src, "rb").read())
    n = patch(rom)
    open(paths.rom_kr(), "wb").write(rom)
    total = sum(len(a["items"]) for a in ARRAYS)
    print(f"이미지 라벨 한글화: {n}/{total}개")
    print("written:", paths.rom_kr())


if __name__ == "__main__":
    main()
