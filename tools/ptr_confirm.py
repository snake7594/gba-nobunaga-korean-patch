# -*- coding: utf-8 -*-
"""재배치 대상 포인터가 '진짜 포인터'인지 확인.
 (a) Thumb  LDR Rd,[PC,#imm8*4]  가 그 주소를 가리키는가
 (b) ARM    LDR Rd,[PC,#imm12]   가 그 주소를 가리키는가
 (c) 포인터 배열의 일원인가 (이웃 워드도 0x08xxxxxx 유효 포인터)
"""
import struct, json, os
S = os.path.dirname(os.path.abspath(__file__))
OLD = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba", "rb").read()
LIMIT = 0x33a200
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))

def thumb_pool(ref, back=1200):
    lo = max(0, ref - back)
    for a in range(lo, ref, 2):
        hw = OLD[a] | (OLD[a+1] << 8)
        if 0x4800 <= hw <= 0x4FFF:              # LDR Rd,[PC,#imm8*4]
            tgt = ((a + 4) & ~3) + (hw & 0xFF) * 4
            if tgt == ref: return True
    return False

def arm_pool(ref, back=4200):
    lo = max(0, ref - back)
    for a in range(lo & ~3, ref, 4):
        w = struct.unpack_from("<I", OLD, a)[0]
        if (w & 0x0F7F0000) == 0x051F0000:      # LDR Rd,[PC,#-imm12] / +imm12
            imm = w & 0xFFF
            up = (w >> 23) & 1
            tgt = a + 8 + (imm if up else -imm)
            if tgt == ref: return True
    return False

def in_ptr_array(ref):
    good = 0
    for d in (-12, -8, -4, 4, 8, 12):
        a = ref + d
        if not (0 <= a < len(OLD) - 3): continue
        v = struct.unpack_from("<I", OLD, a)[0]
        if 0x08000000 <= v < 0x08000000 + LIMIT: good += 1
    return good >= 2

# 재배치가 필요했던 항목(= 한국어가 제자리 용량 초과) 판정용으로 전체 ptr 엔트리 검사
targets = [e for e in es if e["kind"] == "ptr" and e["refs"]]
print("ptr entries:", len(targets), " total refs:", sum(len(e["refs"]) for e in targets))

unsafe = []
stats = {"thumb": 0, "arm": 0, "array": 0, "unsafe": 0}
for e in targets:
    bad_refs = []
    for r in e["refs"]:
        if in_ptr_array(r): stats["array"] += 1; continue
        if thumb_pool(r):   stats["thumb"] += 1; continue
        if arm_pool(r):     stats["arm"] += 1;   continue
        stats["unsafe"] += 1; bad_refs.append(r)
    if bad_refs:
        unsafe.append({"off": e["off"], "jp": e["jp"][:40], "bad_refs": [hex(x) for x in bad_refs]})

print("ref classification:", stats)
print("entries with unverified refs:", len(unsafe))
json.dump([u["off"] for u in unsafe], open(S+r"\unsafe_offsets.json","w"), indent=0)
for u in unsafe[:20]: print("  ", hex(u["off"]), u["bad_refs"], repr(u["jp"][:30]))
