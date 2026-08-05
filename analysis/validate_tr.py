# -*- coding: utf-8 -*-
"""번역 결과 기계 검증"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_codec import SYM_CODE, enc_len

S = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(S+r"\units2.json", encoding="utf-8"))
tr = json.load(open(S+r"\tr_merged.json", encoding="utf-8"))

FMT = re.compile(r"%[-0-9]*[sd]")
GA = re.compile(r"\{G\d\d\}")

def encodable(t):
    bad = []
    for ch in GA.sub("", t):
        o = ord(ch)
        if ch == "\n" or o < 0x80: continue
        if 0xAC00 <= o <= 0xD7A3: continue
        if ch in SYM_CODE: continue
        try:
            b = ch.encode("cp932")
            if len(b) == 2: continue   # 유지문자 시도 (인코더에서 재확인)
        except Exception: pass
        bad.append(ch)
    return bad

def check_one(jp, ko, tag, errs):
    if ko is None:
        errs.append((tag, "missing", jp[:30], "")); return
    if sorted(FMT.findall(jp)) != sorted(FMT.findall(ko)):
        errs.append((tag, "fmt", jp[:30], ko[:30]))
    if GA.findall(jp) != GA.findall(ko):
        errs.append((tag, "gaiji", jp[:30], ko[:30]))
    for line in ko.split("\n"):
        if enc_len(line) > 40:
            errs.append((tag, "linelen", jp[:30], line[:30])); break
    bad = encodable(ko)
    if bad:
        errs.append((tag, "badchar:" + "".join(set(bad)), jp[:30], ko[:30]))
    if any(0x3041 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF for c in GA.sub("", ko)):
        errs.append((tag, "jp-remains", jp[:30], ko[:30]))

errs = []
for u in U["solo"]:
    r = tr.get(u["jp"])
    ko = r.get("ko") if r else None
    check_one(u["jp"], ko, "solo:"+u["jp"][:16], errs)
    if ko is not None and u["limit"] is not None and enc_len(ko) > u["limit"]:
        errs.append(("solo:"+u["jp"][:16], f"limit({u['limit']})", u["jp"][:30], ko[:30]))

for k, sq in enumerate(U["seq"]):
    r = tr.get(f"seq{k}")
    if not r or "kos" not in r:
        errs.append((f"seq{k}", "missing", sq["jps"][0][:30], "")); continue
    if len(r["kos"]) != len(sq["jps"]):
        errs.append((f"seq{k}", f"count {len(sq['jps'])}->{len(r['kos'])}", sq["jps"][0][:30], "")); continue
    # 포맷코드는 시퀀스 전체 단위로 비교(재분할 시 이동 가능)
    jp_all = "\n".join(sq["jps"]); ko_all = "\n".join(r["kos"])
    if sorted(FMT.findall(jp_all)) != sorted(FMT.findall(ko_all)):
        errs.append((f"seq{k}", "fmt", jp_all[:30], ko_all[:30]))
    if GA.findall(jp_all) != GA.findall(ko_all):
        errs.append((f"seq{k}", "gaiji", jp_all[:30], ko_all[:30]))
    for m, (jm, km) in enumerate(zip(sq["jps"], r["kos"])):
        for line in km.split("\n"):
            if enc_len(line) > 40:
                errs.append((f"seq{k}.{m}", "linelen", jm[:30], line[:30])); break
        bad = encodable(km)
        if bad: errs.append((f"seq{k}.{m}", "badchar:"+"".join(set(bad)), jm[:30], km[:30]))
        if any(0x3041 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF for c in GA.sub("", km)):
            errs.append((f"seq{k}.{m}", "jp-remains", jm[:30], km[:30]))

print("errors:", len(errs))
from collections import Counter
print(Counter(e[1].split("(")[0].split(":")[0] for e in errs))
json.dump(errs, open(S+r"\tr_errors.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
for e in errs[:30]: print(" ", e)
