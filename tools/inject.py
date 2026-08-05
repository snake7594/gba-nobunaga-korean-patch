# -*- coding: utf-8 -*-
"""한글패치 주입기:
1) 번역 취합 (auto + keep + agent)
2) 음절 수집 -> charmap (빈도순, 히라가나 슬롯에 고빈도 가나다순 배치)
3) 폰트 슬롯에 갈무리11 글리프 기록
4) 텍스트 인코딩 & 기록 (제자리 or 재배치+포인터 갱신)
"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from hangul_codec import Codec, TABLE, CLS, SYM_CODE, FREE_SLOTS, GAIJI0, enc_len
from bdf import load_bdf, render12
from plan import build_plan
from collections import Counter

SRC = paths.rom_jp()
DST = paths.rom_kr()
FONT2 = paths.FONT_BASE
FREE_BASE = paths.FREE_BASE
ROM_END = paths.ROM_SIZE

# ---- 주입 계획 (verify_all.py 와 동일한 판단을 쓰기 위해 plan.py 로 분리)
final, skipped, NO_RELOC, problems, by_off, es = build_plan()

nskip = Counter(skipped.values())
print(f"overlap drops: {nskip.get('overlap', 0)}, unencodable(원본 유지): {nskip.get('unencodable', 0)}, "
      f"no-reloc entries: {len(NO_RELOC)}")
print("final offsets:", len(final), " problems:", len(problems))
for p in problems[:20]: print("  !", p)
if problems:
    json.dump(problems, open(paths.out('inject_problems.json'), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({hex(k): v for k, v in sorted(skipped.items())},
          open(paths.out('skipped.json'), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- 음절 수집
syls = Counter()
HG = re.compile(r"[가-힣]")
for off, ko in final.items():
    if ko:
        for c in HG.findall(ko):
            syls[c] += 1
print("distinct syllables:", len(syls))
nslots = len(FREE_SLOTS)
if len(syls) > nslots:
    raise SystemExit(f"음절 {len(syls)} > 슬롯 {nslots}")

# ---- charmap: 히라 슬롯(그리드)에 고빈도 음절을 가나다순으로, 나머지는 한자/가타 슬롯
hira_slots = [i for i in FREE_SLOTS if CLS[i] == "hira"]
other_slots = [i for i in FREE_SLOTS if CLS[i] != "hira"]
top = sorted([s for s, _ in syls.most_common(len(hira_slots))])
rest = sorted([s for s in syls if s not in set(top)])
charmap = {}
for s, slot in zip(top, hira_slots): charmap[s] = slot
for s, slot in zip(rest, other_slots): charmap[s] = slot
json.dump(charmap, open(paths.out('charmap.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=0)
codec = Codec(charmap)

# ---- ROM 준비 + 폰트 기록
rom = bytearray(open(SRC, "rb").read())
glyphs, fbbx, ascent, descent = load_bdf(paths.font())
YSHIFT = 3

def hangul_rows(ch):
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

def pack18(rows):
    bits = 0
    for v in rows: bits = (bits << 12) | (v & 0xFFF)
    return bits.to_bytes(18, "big")

nfont = 0
for s, slot in charmap.items():
    rows = hangul_rows(s)
    if rows is None:
        raise SystemExit(f"갈무리에 없는 음절: {s}")
    off = FONT2 + slot*18
    rom[off:off+18] = pack18(rows)
    nfont += 1
print("font glyphs written:", nfont)

# ---- 텍스트 기록
free_ptr = FREE_BASE
overflow = []
truncated = []
encoded_cache = {}
relocated = 0
inplace = 0

def enc(ko):
    if ko not in encoded_cache:
        encoded_cache[ko] = codec.encode(ko)
    return encoded_cache[ko]

for off, ko in sorted(final.items()):
    if ko is None: continue
    e = by_off[off]
    data = enc(ko)
    cap = e["blen"] + e["slack"] - 1   # NUL 1바이트 확보
    if len(data) <= cap:
        rom[off:off+len(data)] = data
        for z in range(off+len(data), off+e["blen"]+e["slack"]):
            rom[z] = 0
        inplace += 1
    elif e["kind"] == "ptr" and off not in NO_RELOC:
        # 재배치
        newoff = free_ptr
        if newoff + len(data) + 1 >= ROM_END:
            raise SystemExit("여유 공간 부족")
        rom[newoff:newoff+len(data)] = data
        rom[newoff+len(data)] = 0
        free_ptr = newoff + len(data) + 1
        newptr = 0x08000000 + newoff
        for r in e["refs"]:
            struct.pack_into("<I", rom, r, newptr)
        relocated += 1
    else:
        # 제자리 초과 + 재배치 불가 -> 용량에 맞게 축약해서라도 한글로 기록
        cut = ko
        while cut and len(enc(cut)) > cap:
            cut = cut[:-1]
        cut = cut.rstrip()
        while cut and len(enc(cut)) > cap:
            cut = cut[:-1]
        if cut:
            d2 = enc(cut)
            rom[off:off+len(d2)] = d2
            for z in range(off+len(d2), off+e["blen"]+e["slack"]):
                rom[z] = 0
            truncated.append({"off": hex(off), "jp": e["jp"][:40], "ko": ko[:40],
                              "cut": cut[:40], "cap": cap, "need": len(data)})
        else:
            overflow.append({"off": off, "jp": e["jp"], "ko": ko, "cap": cap, "need": len(data)})

print(f"inplace: {inplace}, relocated: {relocated}, truncated: {len(truncated)}, overflow: {len(overflow)}")
if truncated:
    json.dump(truncated, open(paths.out('truncated.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=1)
    for t in truncated[:12]: print("   TRUNC", t["off"], repr(t["ko"][:28]), "->", repr(t["cut"][:28]))
print(f"free space used: {free_ptr - FREE_BASE} bytes ({free_ptr:#x})")
if overflow:
    json.dump(overflow, open(paths.out('overflow.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("overflow saved -> overflow.json")

open(DST, "wb").write(rom)
print("written:", DST)
