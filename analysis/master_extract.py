# -*- coding: utf-8 -*-
"""마스터 문자열 DB 구축
- ptr: 포인터 참조 문자열(재배치 가능) — 0x220000-0x25ffff 등
- inline: 같은 영역의 비참조 널종단 문자열 — 제자리+슬랙
- field: DB 고정 필드(0x310000-0x33a200) — 제자리+슬랙
"""
import struct, json
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
LIMIT = 0x33a200

TB2 = 0x30d6ce; N2 = 1869
valid2 = set(struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2))

def parse_str(off, maxlen=4096):
    """off에서 널 종단 문자열 파싱. (text, bytelen) or None. 제어문자 %s 유지."""
    out = []; i = off
    while i < LIMIT:
        b = rom[i]
        if b == 0: break
        if b < 0x80:
            if 0x20 <= b < 0x7F or b in (0x0A,):
                out.append(chr(b)); i += 1; continue
            return None
        if 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode("cp932")); i += 1; continue
        if i+1 >= LIMIT: return None
        v = (b << 8) | rom[i+1]
        if v not in valid2: return None
        try: out.append(bytes(rom[i:i+2]).decode("cp932"))
        except Exception: return None
        i += 2
    n = i - off
    if n < 2 or n > maxlen: return None
    txt = "".join(out)
    if not any(ord(c) > 0x3000 for c in txt): return None
    return txt, n

def slack_after(off, blen):
    """문자열 뒤 0x00 연속 개수(다음 데이터 전까지)"""
    i = off + blen
    z = 0
    while i < LIMIT and rom[i] == 0:
        z += 1; i += 1
    return z

ptr_strings = json.load(open(S+r"\ptr_strings.json", encoding="utf-8"))
ptr_targets = {}
for o in ptr_strings:
    r = parse_str(o["off"])
    if r and r[1] >= 4:
        ptr_targets[o["off"]] = o["refs"]

entries = []
covered = set()

# 1) ptr 문자열 (텍스트 영역 위주 필터)
for tgt in sorted(ptr_targets):
    r = parse_str(tgt)
    if not r: continue
    txt, blen = r
    if not (0x220000 <= tgt < 0x260000 or 0x2e0000 <= tgt < 0x310000 or tgt < 0x60000 or 0x300000 <= tgt < 0x33a200):
        continue
    entries.append({"id": len(entries), "kind": "ptr", "off": tgt, "blen": blen,
                    "slack": slack_after(tgt, blen), "refs": ptr_targets[tgt], "jp": txt})
    covered.update(range(tgt, tgt+blen))

# 2) 텍스트 영역 내 비참조 문자열 (0x220000-0x260000)
i = 0x220000
while i < 0x260000:
    if i in covered or rom[i] == 0:
        i += 1; continue
    r = parse_str(i)
    if r:
        txt, blen = r
        if blen >= 4:
            entries.append({"id": len(entries), "kind": "inline", "off": i, "blen": blen,
                            "slack": slack_after(i, blen), "refs": [], "jp": txt})
            covered.update(range(i, i+blen))
            i += blen
            continue
    i += 1

# 3) DB 고정 필드 (0x310000-0x33a200), ptr 대상 제외
i = 0x310000
while i < LIMIT:
    if i in covered or rom[i] == 0:
        i += 1; continue
    # 폰트/테이블 영역 제외
    if 0x304df4 <= i < 0x30e56a:
        i = 0x30e56a; continue
    r = parse_str(i, maxlen=64)
    if r:
        txt, blen = r
        # 필드다운지: 2바이트 문자 위주 짧은 문자열
        if 2 <= blen <= 40 and any(ord(c) >= 0x3000 for c in txt):
            entries.append({"id": len(entries), "kind": "field", "off": i, "blen": blen,
                            "slack": slack_after(i, blen), "refs": [], "jp": txt})
            covered.update(range(i, i+blen))
            i += blen
            continue
    i += 1

print("entries:", len(entries))
from collections import Counter
print(Counter(e["kind"] for e in entries))
print("total jp bytes:", sum(e["blen"] for e in entries))

json.dump(entries, open(S+r"\master_strings.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved master_strings.json")

# 통계: 종류별 샘플
for kind in ("ptr","inline","field"):
    ss = [e for e in entries if e["kind"]==kind]
    print(f"--- {kind} ({len(ss)}) ---")
    for e in ss[:6]:
        print(" ", hex(e["off"]), f"len={e['blen']} slack={e['slack']} refs={len(e['refs'])}", repr(e["jp"][:36]))
