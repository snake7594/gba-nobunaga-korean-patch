# -*- coding: utf-8 -*-
"""갈무리11 12px 한글 렌더 미리보기 (주입 전 품질 확인)"""
import os, sys
import paths
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdf import load_bdf, render12
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
glyphs, fbbx, ascent, descent = load_bdf(paths.font())
YSHIFT = 3

def rows_for(ch):
    r = render12(glyphs, ascent, ord(ch), W=12, H=16)
    if r is None: return None
    rows = r[YSHIFT:YSHIFT+12]
    l, rgt = 12, -1
    for v in rows:
        for x in range(12):
            if (v >> (11-x)) & 1:
                l = min(l, x); rgt = max(rgt, x)
    if rgt >= 0:
        w = rgt - l + 1
        shift = (12 - w)//2 - l
        if shift > 0: rows = [v >> shift for v in rows]
        elif shift < 0: rows = [(v << (-shift)) & 0xFFF for v in rows]
    return rows

lines = [
 "직전신장의 야망",
 "천하통일을 노려라",
 "무장 병량 다이묘 합전",
 "덕천가강 무전신현 상삼겸신",
 "어느 다이묘를 맡으시겠습니까?",
 "훈  련  병력을 단련합니다",
 "몇 명을 출진시키겠습니까?",
 "쌓 짧 꿇 꽃 훑 뷁 웩 쭉 뀨 픽",
]
W = max(len(l) for l in lines)*13+4
H = len(lines)*15+4
img = Image.new("L", (W,H), 255)
missing = []
for li, line in enumerate(lines):
    for ci, ch in enumerate(line):
        if ch == " ": continue
        rows = rows_for(ch)
        if rows is None: missing.append(ch); continue
        for y in range(12):
            for x in range(12):
                if (rows[y] >> (11-x)) & 1:
                    img.putpixel((2+ci*13+x, 2+li*15+y), 0)
img = img.resize((W*3, H*3), Image.NEAREST)
img.save(paths.out('font_preview.png'))
print("saved font_preview.png; missing:", missing)

# 전체 한글 음절 커버리지 확인
miss = [chr(c) for c in range(0xAC00, 0xD7A4) if c not in glyphs]
print("KS 완성형 11172 음절 중 갈무리 미보유:", len(miss))
