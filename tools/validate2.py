# -*- coding: utf-8 -*-
"""번역 검증 v2 — 실제 주입 실패 요인만 검사"""
import json, os, sys, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_codec import SYM_CODE, enc_len, TABLE

S = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(S+r"\units2.json", encoding="utf-8"))
tr = json.load(open(S+r"\tr_merged.json", encoding="utf-8"))
TSET = set(TABLE)

FMT = re.compile(r"%[-0-9]*[sd]")
GA = re.compile(r"\{G\d\d\}")

def badchars(t):
    bad = []
    for ch in GA.sub("", t):
        o = ord(ch)
        if ch == "\n" or o < 0x80: continue
        if 0xAC00 <= o <= 0xD7A3: continue
        if ch in SYM_CODE: continue
        try:
            b = ch.encode("cp932")
            if len(b) == 2 and ((b[0]<<8)|b[1]) in TSET: continue
        except Exception: pass
        bad.append(ch)
    return bad

def jp_left(t):
    return [c for c in GA.sub("", t) if 0x3041 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF]

issues = []
def check(tag, jp, ko, limit=None):
    if ko is None:
        issues.append({"tag":tag,"type":"missing","jp":jp,"ko":""}); return
    b = badchars(ko)
    if b: issues.append({"tag":tag,"type":"badchar","chars":"".join(sorted(set(b))),"jp":jp,"ko":ko})
    j = jp_left(ko)
    if j: issues.append({"tag":tag,"type":"jp-remains","chars":"".join(sorted(set(j))),"jp":jp,"ko":ko})
    if sorted(FMT.findall(jp)) != sorted(FMT.findall(ko)):
        issues.append({"tag":tag,"type":"fmt","jp":jp,"ko":ko})
    if GA.findall(jp) != GA.findall(ko):
        issues.append({"tag":tag,"type":"gaiji","jp":jp,"ko":ko})
    if limit is not None and enc_len(ko) > limit:
        issues.append({"tag":tag,"type":"limit","limit":limit,"need":enc_len(ko),"jp":jp,"ko":ko})

for u in U["solo"]:
    r = tr.get(u["jp"])
    check("solo", u["jp"], r.get("ko") if r else None, u["limit"])

for k, sq in enumerate(U["seq"]):
    r = tr.get(f"seq{k}")
    if not r or "kos" not in r:
        issues.append({"tag":f"seq{k}","type":"missing","jp":sq["jps"][0],"ko":""}); continue
    if len(r["kos"]) != len(sq["jps"]):
        issues.append({"tag":f"seq{k}","type":"count","jp":f"{len(sq['jps'])} -> {len(r['kos'])}","ko":""}); continue
    jp_all = "\n".join(sq["jps"]); ko_all = "\n".join(r["kos"])
    if sorted(FMT.findall(jp_all)) != sorted(FMT.findall(ko_all)):
        issues.append({"tag":f"seq{k}","type":"fmt","jp":jp_all[:60],"ko":ko_all[:60]})
    if GA.findall(jp_all) != GA.findall(ko_all):
        issues.append({"tag":f"seq{k}","type":"gaiji","jp":jp_all[:60],"ko":ko_all[:60]})
    for m, (jm, km) in enumerate(zip(sq["jps"], r["kos"])):
        b = badchars(km)
        if b: issues.append({"tag":f"seq{k}.{m}","type":"badchar","chars":"".join(sorted(set(b))),"jp":jm,"ko":km})
        j = jp_left(km)
        if j: issues.append({"tag":f"seq{k}.{m}","type":"jp-remains","chars":"".join(sorted(set(j))),"jp":jm,"ko":km})

print("issues:", len(issues))
print(Counter(i["type"] for i in issues))
allbad = Counter()
for i in issues:
    if i["type"] in ("badchar","jp-remains"):
        allbad.update(i["chars"])
print("chars:", dict(allbad))
json.dump(issues, open(S+r"\issues.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
for i in issues[:25]:
    print(" ", i["type"], i.get("chars",""), repr(i["jp"][:26]), "->", repr(i["ko"][:36]))
