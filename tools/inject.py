# -*- coding: utf-8 -*-
"""한글패치 주입기:
1) 번역 취합 (auto + keep + agent)
2) 음절 수집 -> charmap (빈도순, 히라가나 슬롯에 고빈도 가나다순 배치)
3) 폰트 슬롯에 갈무리11 글리프 기록
4) 텍스트 인코딩 & 기록 (제자리 or 재배치+포인터 갱신)
"""
import json, os, sys, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_codec import Codec, TABLE, CLS, SYM_CODE, FREE_SLOTS, GAIJI0, enc_len
from bdf import load_bdf, render12
from collections import Counter

S = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba"
DST = r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba"
FONT2 = 0x305274
FREE_BASE = 0x33a1a0   # 여유 공간 시작
ROM_END = 0x400000

U = json.load(open(S+r"\units2.json", encoding="utf-8"))
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))
by_off = {e["off"]: e for e in es}
tr = json.load(open(S+r"\tr_merged.json", encoding="utf-8"))

# ---- 오프셋별 최종 텍스트 결정
final = {}   # off -> ko text (None = 원본 유지)
problems = []

for off_s, ko in U["auto"].items():
    final[int(off_s)] = ko
for off in U["keep"]:
    final[off] = None

for u in U["solo"]:
    r = tr.get(u["jp"])
    if r is None or "ko" not in r:
        problems.append(("missing", u["jp"][:30])); continue
    for off in u["offs"]:
        final[off] = r["ko"]

for k, sq in enumerate(U["seq"]):
    r = tr.get(f"seq{k}")
    if r is None or "kos" not in r or len(r["kos"]) != len(sq["offs"]):
        problems.append(("seq-bad", f"seq{k}")); continue
    for off, ko in zip(sq["offs"], r["kos"]):
        final[off] = ko

# ---- 안전 처리
# (a) 리터럴풀/포인터배열로 확인되지 않은 참조 -> 포인터를 고쳐선 안 됨(재배치 금지).
#     단 제자리 기록은 포인터를 건드리지 않으므로 안전하다.
try:
    NO_RELOC = set(json.load(open(S+r"\unsafe_offsets.json")))
except FileNotFoundError:
    NO_RELOC = set()

# (b) 겹치는 엔트리: 검증된 포인터 참조 > 참조 없음 > 미검증 참조, 동급이면 긴 쪽
def rank(e):
    unverified = e["off"] in NO_RELOC
    if unverified:      tier = 2
    elif e["refs"]:     tier = 0    # 진짜 포인터가 가리키는 문자열
    else:               tier = 1
    return (tier, -e["blen"], e["off"])
ranked = sorted(es, key=rank)
taken, drop_overlap = [], set()
occupied = []
for e in ranked:
    a, b = e["off"], e["off"] + e["blen"]
    if any(a < ob and oa < b for oa, ob in occupied):
        drop_overlap.add(e["off"])
    else:
        occupied.append((a, b))
for o in drop_overlap:
    final.pop(o, None)
print(f"overlap drops: {len(drop_overlap)}, no-reloc entries: {len(NO_RELOC)}")

print("final offsets:", len(final), " problems:", len(problems))
for p in problems[:20]: print("  !", p)
if problems:
    json.dump(problems, open(S+r"\inject_problems.json","w",encoding="utf-8"), ensure_ascii=False)

# ---- 번역문에 남은 일본 문자 / 인코딩 불가 문자가 있으면 원문 유지
# (해당 한자·가나 슬롯은 한글로 재활용되므로 그대로 두면 엉뚱한 글자로 표시됨)
from hangul_codec import normalize as _norm
_TSET = set(TABLE)
def encodable(t):
    for ch in re.sub(r"\{G\d\d\}", "", _norm(t)):
        o = ord(ch)
        if ch == "\n" or o < 0x80: continue
        if 0xAC00 <= o <= 0xD7A3: continue
        if ch in SYM_CODE: continue           # 유지 기호(・ー 포함)
        if 0xFF61 <= o <= 0xFF9F: continue    # 반각 가나(원본 바이트 보존)
        if 0x3041 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            return False                      # 재활용된 슬롯 -> 사용 불가
        try:
            b = ch.encode("cp932")
            if len(b) == 2 and ((b[0] << 8) | b[1]) in _TSET: continue
        except Exception: pass
        return False
    return True

unencodable = []
for off in list(final):
    ko = final[off]
    if ko and not encodable(ko):
        unencodable.append((hex(off), by_off[off]["jp"][:30], ko[:30]))
        final[off] = None
print("unencodable -> kept original:", len(unencodable))
for u in unencodable[:10]: print("   ", u)

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
json.dump(charmap, open(S+r"\charmap.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
codec = Codec(charmap)

# ---- ROM 준비 + 폰트 기록
rom = bytearray(open(SRC, "rb").read())
glyphs, fbbx, ascent, descent = load_bdf(S+r"\Galmuri11.bdf")
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
    json.dump(truncated, open(S+r"\truncated.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    for t in truncated[:12]: print("   TRUNC", t["off"], repr(t["ko"][:28]), "->", repr(t["cut"][:28]))
print(f"free space used: {free_ptr - FREE_BASE} bytes ({free_ptr:#x})")
if overflow:
    json.dump(overflow, open(S+r"\overflow.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("overflow saved -> overflow.json")

open(DST, "wb").write(rom)
print("written:", DST)
