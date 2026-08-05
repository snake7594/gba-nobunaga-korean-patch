# -*- coding: utf-8 -*-
"""이름·지명 대조표 생성 (검수·수정용)"""
import sys, json
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\data")
import paths
from yomi_place import PLACE, TITLE
from yomi_surname import SURNAME
from yomi_given import GIVEN
import names as N

inv = N._inventory() or {}
real = N._real_pairs()

L = []
L.append("# 노부나가의 야망 (GBA) 한글패치 — 이름·지명 대조표")
L.append("")
L.append("일본어 읽기는 외래어 표기법을 따랐습니다(어두 평음, 장음 미표기).")
L.append("고칠 곳이 있으면 data/yomi_*.py 의 해당 줄을 수정하고 다시 빌드하세요.")
L.append("")

L.append("## 구니·지역 (%d)" % len(PLACE))
row = []
for k in sorted(PLACE, key=lambda x: PLACE[x]):
    row.append(f"{k}={PLACE[k]}")
    if len(row) == 6:
        L.append("  " + "  ".join(row)); row = []
if row: L.append("  " + "  ".join(row))
L.append("")

L.append("## 성씨 (%d)  ※게임 등장 수" % len(SURNAME))
row = []
for k in sorted(SURNAME, key=lambda x: -inv.get(x, 0)):
    n = inv.get(k, 0)
    row.append(f"{k}={SURNAME[k]}({n})")
    if len(row) == 5:
        L.append("  " + "  ".join(row)); row = []
if row: L.append("  " + "  ".join(row))
L.append("")

L.append("## 이름 (%d)" % len(GIVEN))
row = []
for k in sorted(GIVEN, key=lambda x: -inv.get(x, 0)):
    n = inv.get(k, 0)
    row.append(f"{k}={GIVEN[k]}({n})")
    if len(row) == 5:
        L.append("  " + "  ".join(row)); row = []
if row: L.append("  " + "  ".join(row))
L.append("")

L.append("## 게임에 실제로 있는 성+이름 조합 (%d)" % len(real))
pairs = sorted(real, key=lambda p: (p[0], p[1]))
row = []
for s, g in pairs:
    full = f"{s}{g}={SURNAME.get(s,'?')} {GIVEN.get(g,'?')}"
    row.append(full)
    if len(row) == 3:
        L.append("  " + "   ".join(row)); row = []
if row: L.append("  " + "   ".join(row))
L.append("")

L.append("## 단독 치환에서 제외한 항목 (한국어 낱말과 겹침)")
L.append("  " + " ".join(sorted(N.AMBIGUOUS_SOLO)))
L.append("  → 성+이름 결합형에서는 정상 치환됩니다 (예: 伊東祐兵 = 이토 스케타케)")

open(r"D:\gba\NOBU2\gba-nobunaga-korean-patch\data\이름대조표.txt", "w",
     encoding="utf-8").write("\n".join(L))
print("saved data/이름대조표.txt  (%d줄)" % len(L))
