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
from plan import build_plan
from glyphs import GlyphMaker, pack18, patch_advance, ADV_PATCH_OFF, ADV_PATCH_ORIG
import halfwidth
import names as NAMES
from collections import Counter

# 이름·지명을 일본어 읽기로 표기할지 (0 이면 한자 독음 유지)
JP_NAMES = os.environ.get("NOBU2_JPNAMES", "1") != "0"

SRC = paths.rom_jp()
DST = paths.rom_kr()
FONT2 = paths.FONT_BASE
FREE_BASE = paths.FREE_BASE
ROM_END = paths.ROM_SIZE

# 전각 전진폭(px). 12 = 원본, 8 = 좁은 글꼴로 창 넘침 해소.
# 환경변수 NOBU2_ADVANCE 로 덮어쓸 수 있다.
ADVANCE = int(os.environ.get("NOBU2_ADVANCE", "8"))

# ---- 주입 계획 (verify_all.py 와 동일한 판단을 쓰기 위해 plan.py 로 분리)
#      이름의 일본어 읽기 치환과 반각 배정도 plan 이 결정한다.
final, skipped, NO_RELOC, problems, by_off, es, halfmap = build_plan()

nskip = Counter(skipped.values())
print(f"overlap drops: {nskip.get('overlap', 0)}, unencodable(원본 유지): {nskip.get('unencodable', 0)}, "
      f"no-reloc entries: {len(NO_RELOC)}")
print("final offsets:", len(final), " problems:", len(problems))
for p in problems[:20]: print("  !", p)
if problems:
    json.dump(problems, open(paths.out('inject_problems.json'), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({hex(k): v for k, v in sorted(skipped.items())},
          open(paths.out('skipped.json'), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if halfmap:
    print(f"일본어 읽기 적용 · 반각 음절 {len(halfmap)}종")

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
json.dump({k: hex(v) for k, v in halfmap.items()},
          open(paths.out('halfmap.json'), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
codec = Codec(charmap, halfmap)

# ---- ROM 준비 + 폰트 기록
rom = bytearray(open(SRC, "rb").read())

gm = GlyphMaker(advance=ADVANCE, rom=rom)
print(f"전각 전진폭 {ADVANCE}px · 폰트 {gm.font_name} · 정렬 {gm.align}")

nfont = nsym = ngai = 0

# 한글 음절
for s, slot in charmap.items():
    rom[FONT2+slot*18: FONT2+slot*18+18] = pack18(gm.hangul(s))
    nfont += 1

if ADVANCE < 12:
    # 전진폭을 줄이면 원본 12px 글리프(기호·전각숫자·영문·외자)가 다음 글자에
    # 덮여 오른쪽이 잘린다. 그래서 이들도 전진폭 안에 들어오도록 다시 그린다.
    for slot in range(len(TABLE)):
        if slot in charmap.values():
            continue
        if CLS[slot] == "sym":
            v = TABLE[slot]
            ch = bytes([v >> 8, v & 0xFF]).decode("cp932")
            rom[FONT2+slot*18: FONT2+slot*18+18] = pack18(gm.symbol(ch, slot))
            nsym += 1
        elif CLS[slot] == "gaiji":
            rom[FONT2+slot*18: FONT2+slot*18+18] = pack18(gm.gaiji(slot))
            ngai += 1

    # 전각 전진폭 코드 패치 (1바이트)
    patch_advance(rom, ADVANCE)
    print(f"code patch: {ADV_PATCH_OFF:#x} {ADV_PATCH_ORIG} -> {ADVANCE}")

# 반각 슬롯에 한글 글리프 기록 (1바이트 이름용)
nhalf = halfwidth.write_font(rom, halfmap, gm) if halfmap else 0

print(f"font glyphs written: 한글 {nfont}, 기호 {nsym}, 외자 {ngai}, 반각한글 {nhalf}")

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
