# -*- coding: utf-8 -*-
"""번역 단위 생성:
- auto: DB 필드 중 한자 전용 문자열 -> 독음(두음법칙 word-initial 적용)
- agent: 나머지 -> 배치 파일로 분할
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eumdok import KANJI_READ, KANJI_SKIP
from hangul_codec import enc_len

S = os.path.dirname(os.path.abspath(__file__))
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))

# 두음법칙 (어두)
DUEUM = {
 "라":"나","락":"낙","란":"난","랄":"날","람":"남","랍":"납","랑":"낭","래":"내","랭":"냉",
 "량":"양","려":"여","력":"역","련":"연","렬":"열","렴":"염","렵":"엽","령":"영","례":"예",
 "로":"노","록":"녹","론":"논","롱":"농","뢰":"뇌","료":"요","룡":"용","루":"누","류":"유",
 "륙":"육","륜":"윤","률":"율","륭":"융","륵":"늑","름":"늠","릉":"능","리":"이","린":"인",
 "림":"임","립":"입","녀":"여","년":"연","념":"염","녕":"영","뇨":"요","뉴":"유","니":"이",
 "닉":"익","님":"임",
}

def eumdok_name(txt):
    """한자 전용 문자열 -> 독음 (첫 글자 두음법칙)"""
    out = []
    for ch in txt:
        if ch in KANJI_SKIP:
            return None
        r = KANJI_READ.get(ch)
        if r is None:
            return None
        out.append(r)
    if out:
        out[0] = DUEUM.get(out[0], out[0])
    return "".join(out)

def is_all_kanji(txt):
    return all(0x4E00 <= ord(c) <= 0x9FFF for c in txt)

units = {}
for e in es:
    u = units.setdefault(e["jp"], {"jp": e["jp"], "ids": [], "kinds": set(), "limit": None})
    u["ids"].append(e["id"])
    u["kinds"].add(e["kind"])
    if e["kind"] in ("field", "inline"):
        lim = e["blen"] + e["slack"] - 1
        u["limit"] = lim if u["limit"] is None else min(u["limit"], lim)

import re
GA = re.compile(r"\{G\d\d\}")
def strip_g(t): return GA.sub("", t)

def is_kana(c):
    return 0x3041 <= ord(c) <= 0x30FF

auto = {}
keep = []
agent = []
for jp, u in units.items():
    u["kinds"] = sorted(u["kinds"])
    core = strip_g(jp)
    # 번역할 일본어(가나/한자)가 없는 문자열 -> 원본 유지
    if not any(0x3041 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF for c in core):
        keep.append(jp); continue
    # 단일 가나 문자 (이름 입력 그리드) -> 원본 유지
    if len(core) == 1 and is_kana(core):
        keep.append(jp); continue
    # 한자 전용 -> 독음 자동 (필드 여부 무관하게 이름/단어가 확실한 DB필드만, 그 외 한자단어는 agent)
    if is_all_kanji(core) and core == jp:
        ko = eumdok_name(jp)
        if ko is not None and enc_len(ko) <= (u["limit"] if u["limit"] is not None else 999):
            if "field" in u["kinds"] or len(jp) == 1:
                auto[jp] = ko
                continue
    agent.append(u)

print("unique units:", len(units))
print("auto (eumdok names):", len(auto))
print("keep (as-is):", len(keep))
print("agent units:", len(agent))
print("agent chars:", sum(len(u['jp']) for u in agent))

json.dump(auto, open(S+r"\tr_auto.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(keep, open(S+r"\tr_keep.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)

# agent 단위: 짧은 것(라벨/이름)과 긴 것(대사/열전) 구분해 배치
agent.sort(key=lambda u: (len(u["jp"]), u["jp"]))
batches = []
cur, cur_chars = [], 0
for u in agent:
    cur.append({"jp": u["jp"], "limit": u["limit"], "kinds": u["kinds"]})
    cur_chars += max(len(u["jp"]), 8)
    if cur_chars >= 2600:
        batches.append(cur); cur, cur_chars = [], 0
if cur: batches.append(cur)
os.makedirs(S+r"\tr_batches", exist_ok=True)
import glob
for f in glob.glob(S+r"\tr_batches\*.json"): os.remove(f)
for k, b in enumerate(batches):
    json.dump(b, open(S+rf"\tr_batches\batch_{k:03d}.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("batches:", len(batches))

# 샘플
items = list(auto.items())
print("auto sample:", items[:8])
print("agent sample short:", [a["jp"] for a in batches[0][:10]])
