# -*- coding: utf-8 -*-
"""전수 검증: 모든 엔트리에 대해 (포인터 추적 후) 실제 ROM 바이트를 디코드해
   의도한 한국어와 일치하는지 확인"""
import struct, json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_codec import normalize

S = os.path.dirname(os.path.abspath(__file__))
NEW = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba", "rb").read()
OLD = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba", "rb").read()
FONT2 = 0x305274; TB2 = 0x30d6ce; N2 = 1869; GAIJI0 = 1851
table = [struct.unpack_from("<H", NEW, TB2+i*2)[0] for i in range(N2)]
idx_of = {v: i for i, v in enumerate(table)}
charmap = json.load(open(S+r"\charmap.json", encoding="utf-8"))
slot2syl = {v: k for k, v in charmap.items()}

def decode(off, maxb=4096):
    out = []; i = off
    while i < len(NEW) and NEW[i] != 0 and i - off < maxb:
        b = NEW[i]
        if b == 0x0A: out.append("\n"); i += 1; continue
        if b < 0x80: out.append(chr(b)); i += 1; continue
        if 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode("cp932")); i += 1; continue
        v = (b << 8) | NEW[i+1]
        gi = idx_of.get(v)
        if gi is None: out.append("\uFFFD")
        elif gi in slot2syl: out.append(slot2syl[gi])
        elif gi >= GAIJI0: out.append("{G%02d}" % (gi - GAIJI0))
        else:
            try: out.append(bytes([b, NEW[i+1]]).decode("cp932"))
            except Exception: out.append("\uFFFD")
        i += 2
    return "".join(out), i - off

U = json.load(open(S+r"\units2.json", encoding="utf-8"))
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))
by_off = {e["off"]: e for e in es}
tr = json.load(open(S+r"\tr_merged.json", encoding="utf-8"))

expected = {}
for k, v in U["auto"].items(): expected[int(k)] = v
for u in U["solo"]:
    r = tr.get(u["jp"])
    if r and "ko" in r:
        for off in u["offs"]: expected[off] = r["ko"]
for k, sq in enumerate(U["seq"]):
    r = tr.get(f"seq{k}")
    if r and "kos" in r and len(r["kos"]) == len(sq["offs"]):
        for off, ko in zip(sq["offs"], r["kos"]): expected[off] = ko

ok = bad = 0
mismatches = []
for off, ko in expected.items():
    e = by_off[off]
    # 현재 유효 주소: refs 가 있으면 첫 ref 의 포인터를 따라감
    cur = off
    if e["refs"]:
        v = struct.unpack_from("<I", NEW, e["refs"][0])[0]
        if 0x08000000 <= v < 0x08400000: cur = v - 0x08000000
    got, _ = decode(cur)
    if got == normalize(ko):
        ok += 1
    else:
        bad += 1
        if len(mismatches) < 30:
            mismatches.append({"off": hex(off), "cur": hex(cur), "want": ko[:50], "got": got[:50]})

print(f"verified OK: {ok}, mismatch: {bad}")
for m in mismatches: print(" ", m["off"], "->", m["cur"], "| want", repr(m["want"]), "| got", repr(m["got"]))
json.dump(mismatches, open(S+r"\verify_mismatch.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

# 포인터 무결성: 모든 refs 가 유효 문자열을 가리키는가
badptr = 0
for e in es:
    for r in e["refs"]:
        v = struct.unpack_from("<I", NEW, r)[0]
        if not (0x08000000 <= v < 0x08400000): badptr += 1
print("invalid pointers:", badptr)

# ROM 크기/헤더 무결성
print("size:", len(NEW), "header intact:", NEW[0xA0:0xB0] == OLD[0xA0:0xB0])
