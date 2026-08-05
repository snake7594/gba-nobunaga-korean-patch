# -*- coding: utf-8 -*-
"""번역 단위 v2: 포인터 배열 -> 시퀀스 재구성, 필드 노이즈 제거"""
import os, sys
import paths
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eumdok import KANJI_READ, KANJI_SKIP
from hangul_codec import enc_len

S = os.path.dirname(os.path.abspath(__file__))
es = json.load(open(paths.inp('master_strings.json'), encoding="utf-8"))
by_off = {e["off"]: e for e in es}

GA = re.compile(r"\{G\d\d\}")
def strip_g(t): return GA.sub("", t)
def has_jp(t):
    t = strip_g(t)
    return any(0x3041 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF for c in t)
def all_2byte(t):
    t = strip_g(t)
    return all(ord(c) >= 0x3000 or c in "\n" for c in t) and len(t) > 0

# --- 필드 정리: ASCII 섞인 field 는 노이즈 -> 제외
clean = []
dropped = 0
for e in es:
    if e["kind"] == "field" and not all_2byte(e["jp"]):
        dropped += 1; continue
    clean.append(e)
print("field noise dropped:", dropped)
es = clean
by_off = {e["off"]: e for e in es}

# --- 시퀀스 감지: ref 주소 연속 런
ref_pairs = []  # (ref_addr, target_off)
for e in es:
    for r in e["refs"]:
        ref_pairs.append((r, e["off"]))
ref_pairs.sort()
seqs = []
cur = []
prev_addr = None
for addr, tgt in ref_pairs:
    if prev_addr is not None and addr == prev_addr + 4:
        cur.append((addr, tgt))
    else:
        if len(cur) >= 2: seqs.append(cur)
        cur = [(addr, tgt)]
    prev_addr = addr
if len(cur) >= 2: seqs.append(cur)

in_seq = set()
seq_units = []
for sq in seqs:
    members = [t for _, t in sq]
    # 일본어 없는 멤버만 있으면 스킵
    if not any(has_jp(by_off[t]["jp"]) for t in members):
        continue
    seq_units.append({"kind": "seq", "table": sq[0][0], "offs": members,
                      "jps": [by_off[t]["jp"] for t in members]})
    in_seq.update(members)
print("sequences:", len(seq_units), " member strings:", len(in_seq))

# --- 두음법칙
DUEUM = {
 "라":"나","락":"낙","란":"난","랄":"날","람":"남","랍":"납","랑":"낭","래":"내","랭":"냉",
 "량":"양","려":"여","력":"역","련":"연","렬":"열","렴":"염","렵":"엽","령":"영","례":"예",
 "로":"노","록":"녹","론":"논","롱":"농","뢰":"뇌","료":"요","룡":"용","루":"누","류":"유",
 "륙":"육","륜":"윤","률":"율","륭":"융","륵":"늑","름":"늠","릉":"능","리":"이","린":"인",
 "림":"임","립":"입","녀":"여","년":"연","념":"염","녕":"영","뇨":"요","뉴":"유","니":"이",
 "닉":"익","님":"임",
}
def eumdok_name(txt):
    out = []
    for ch in txt:
        if ch in KANJI_SKIP: return None
        r = KANJI_READ.get(ch)
        if r is None: return None
        out.append(r)
    if out: out[0] = DUEUM.get(out[0], out[0])
    return "".join(out)
def is_all_kanji(txt):
    return len(txt) > 0 and all(0x4E00 <= ord(c) <= 0x9FFF for c in txt)
def is_kana1(t):
    return len(t) == 1 and 0x3041 <= ord(t) <= 0x30FF

# --- 솔로 유닛 분류
auto = {}      # off -> ko  (독음 자동)
keep_offs = []
solo_units = {}  # jp -> {jp, offs, limit}
for e in es:
    if e["off"] in in_seq: continue
    jp = e["jp"]
    if not has_jp(jp):
        keep_offs.append(e["off"]); continue
    if is_kana1(strip_g(jp)) and strip_g(jp) == jp:
        keep_offs.append(e["off"]); continue
    lim = e["blen"] + e["slack"] - 1 if e["kind"] in ("field", "inline") else None
    if is_all_kanji(jp):
        ko = eumdok_name(jp)
        if ko is not None and (e["kind"] == "field" or len(jp) == 1):
            if lim is None or enc_len(ko) <= lim:
                auto[e["off"]] = ko
                continue
    u = solo_units.setdefault(jp, {"kind": "solo", "jp": jp, "offs": [], "limit": None})
    u["offs"].append(e["off"])
    if lim is not None:
        u["limit"] = lim if u["limit"] is None else min(u["limit"], lim)

print("auto:", len(auto), " keep:", len(keep_offs), " solo units:", len(solo_units))
print("agent chars:", sum(len(u['jp']) for u in solo_units.values()) + sum(len(j) for sq in seq_units for j in sq["jps"]))

json.dump({"auto": {str(k): v for k, v in auto.items()},
           "keep": keep_offs,
           "solo": list(solo_units.values()),
           "seq": seq_units},
          open(paths.out('units2.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved units2.json")

# 시퀀스 샘플
for sq in seq_units[:6]:
    print("SEQ @tbl", hex(sq["table"]), "->", [j[:14] for j in sq["jps"][:6]])
