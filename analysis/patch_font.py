# -*- coding: utf-8 -*-
"""노부나가의 야망 GBA — 한자/가타카나 글리프를 한글(갈무리11)로 교체"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdf import load_bdf, render12
from eumdok import KANJI_READ, KANJI_SKIP, KATA_READ

S = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba"
DST = r"D:\gba\NOBU2\Nobunaga no Yabou (Korean-Reading).gba"

FONT2 = 0x305274
TB2 = 0x30d6ce

rom = bytearray(open(SRC, "rb").read())
charset = json.load(open(os.path.join(S, "charset.json"), encoding="utf-8"))

glyphs, fbbx, ascent, descent = load_bdf(os.path.join(S, "Galmuri11.bdf"))
YSHIFT = 3  # render12(baseline=ascent) puts 12px hangul at rows 3..14 -> shift up 3

def hangul_rows(ch):
    r = render12(glyphs, ascent, ord(ch), W=12, H=16)
    if r is None:
        return None
    rows = r[YSHIFT:YSHIFT+12]
    # ink bbox 기준 수평 중앙 정렬 (자모 등 좁은 글리프 대비)
    l, rgt = 12, -1
    for v in rows:
        for x in range(12):
            if (v >> (11-x)) & 1:
                l = min(l, x); rgt = max(rgt, x)
    if rgt >= 0:
        w = rgt - l + 1
        shift = (12 - w)//2 - l
        if shift > 0:
            rows = [ (v >> shift) for v in rows ]
        elif shift < 0:
            rows = [ (v << (-shift)) & 0xFFF for v in rows ]
    return rows

def pack18(rows):
    bits = 0
    for v in rows:
        bits = (bits << 12) | (v & 0xFFF)
    return bits.to_bytes(18, "big")

replaced_kanji = 0
replaced_kata = 0
skipped = []
missing_font = []

for e in charset:
    idx, ch, cls = e["idx"], e["ch"], e["cls"]
    if ch is None:
        continue
    tgt = None
    if cls == "kanji":
        if ch in KANJI_SKIP:
            skipped.append(ch); continue
        tgt = KANJI_READ.get(ch)
        if tgt is None: continue
        kind = "kanji"
    elif cls == "kata":
        tgt = KATA_READ.get(ch)
        if tgt is None: continue  # ー ・ 유지
        kind = "kata"
    else:
        continue
    rows = hangul_rows(tgt)
    if rows is None:
        missing_font.append((ch, tgt)); continue
    off = FONT2 + idx * 18
    rom[off:off+18] = pack18(rows)
    if kind == "kanji": replaced_kanji += 1
    else: replaced_kata += 1

open(DST, "wb").write(rom)
print(f"kanji replaced: {replaced_kanji}")
print(f"kata replaced:  {replaced_kata}")
print(f"kokuji kept:    {len(skipped)} {''.join(skipped)}")
print(f"missing in Galmuri: {missing_font}")
print("written:", DST, len(rom), "bytes")
