# -*- coding: utf-8 -*-
"""마스터 문자열 DB v2 — 가이지 {Gnn} 토큰화, 유효성 강화"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import struct, json
rom = open(paths.rom_jp(), "rb").read()
S = paths.BUILD
LIMIT = 0x33a200

TB2 = 0x30d6ce; N2 = 1869
table = [struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2)]
valid2 = set(table)
GAIJI0 = 1851  # 테이블 인덱스 1851..1868 = 가이지
gaiji_codes = {table[i]: i-GAIJI0 for i in range(GAIJI0, N2)}

FMT_OK = set("0123456789%sd. ()/:+-")

def parse_str(off, maxlen=4096, min2=2):
    out = []; i = off; n2 = 0
    while i < LIMIT:
        b = rom[i]
        if b == 0: break
        if b == 0x0A:
            out.append("\n"); i += 1; continue
        if b < 0x20: return None
        if b < 0x80:
            if b < 0x7F: out.append(chr(b)); i += 1; continue
            return None
        if 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode("cp932")); i += 1; continue
        if i+1 >= LIMIT: return None
        v = (b << 8) | rom[i+1]
        if v not in valid2: return None
        if v in gaiji_codes:
            out.append("{G%02d}" % gaiji_codes[v]); n2 += 1; i += 2; continue
        try: out.append(bytes(rom[i:i+2]).decode("cp932"))
        except Exception: return None
        n2 += 1; i += 2
    n = i - off
    if n < 2 or n > maxlen: return None
    txt = "".join(out)
    # 유효성: 2바이트 문자 2개 이상, 또는 1개 이상이면서 나머지가 포맷/숫자류
    others = [c for c in txt if ord(c) < 0x100 and c != "\n"]
    if n2 >= min2: pass
    elif n2 >= 1 and all(c in FMT_OK for c in others): pass
    else: return None
    return txt, n

def slack_after(off, blen):
    i = off + blen; z = 0
    while i < LIMIT and rom[i] == 0: z += 1; i += 1
    return z

# 포인터 전수 스캔 (v2 파서로 재검증)
ptr_targets = {}
for off in range(0, LIMIT-3, 4):
    v = struct.unpack_from("<I", rom, off)[0]
    if 0x08000000 <= v < 0x08000000 + LIMIT:
        tgt = v - 0x08000000
        if tgt in ptr_targets:
            ptr_targets[tgt].append(off); continue
        r = parse_str(tgt)
        if r:
            ptr_targets[tgt] = [off]

entries = []; covered = set()
def add(kind, off, refs, min2=2):
    r = parse_str(off, min2=min2)
    if not r: return False
    txt, blen = r
    entries.append({"id": 0, "kind": kind, "off": off, "blen": blen,
                    "slack": slack_after(off, blen), "refs": refs, "jp": txt})
    covered.update(range(off, off+blen))
    return True

# 1) ptr 문자열
for tgt in sorted(ptr_targets):
    if tgt < 0x60000:
        add("ptr", tgt, ptr_targets[tgt], min2=2)
    elif 0x220000 <= tgt < 0x260000 or 0x300000 <= tgt < LIMIT:
        add("ptr", tgt, ptr_targets[tgt], min2=1)

# 2) 텍스트 영역 비참조 문자열
i = 0x220000
while i < 0x260000:
    if i in covered or rom[i] == 0: i += 1; continue
    r = parse_str(i, min2=1)
    if r and r[1] >= 2:
        add("inline", i, [], min2=1); i += r[1]; continue
    i += 1

# 3) DB 고정 필드
i = 0x30e56a
while i < LIMIT:
    if i in covered or rom[i] == 0: i += 1; continue
    r = parse_str(i, maxlen=64, min2=1)
    if r and 2 <= r[1] <= 40:
        add("field", i, [], min2=1); i += r[1]; continue
    i += 1

for k, e in enumerate(entries): e["id"] = k
print("entries:", len(entries))
from collections import Counter
print(Counter(e["kind"] for e in entries))
print("total jp bytes:", sum(e["blen"] for e in entries))
gaiji_strs = [e for e in entries if "{G" in e["jp"]]
print("strings with gaiji:", len(gaiji_strs))
nl = [e for e in entries if "\n" in e["jp"]]
print("strings with newline:", len(nl))
fmt = [e for e in entries if "%" in e["jp"]]
print("strings with %fmt:", len(fmt))
json.dump(entries, open(paths.out('master_strings.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved")
for e in gaiji_strs[:5]: print("G:", hex(e["off"]), repr(e["jp"][:40]))
