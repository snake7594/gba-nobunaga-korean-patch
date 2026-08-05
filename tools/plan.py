# -*- coding: utf-8 -*-
"""주입 계획 수립 — inject.py 와 verify_all.py 가 공유한다.

두 도구가 같은 판단을 쓰도록 한 곳에 모았다.
검증기가 주입기와 다른 기준을 쓰면 '실제로는 정상인데 불일치로 잡히는' 착시가 생긴다.

build_plan() 반환값
    final       {off: 한국어 문자열 또는 None}   None = 원본 바이트 유지
    skipped     {off: 사유}                      의도적으로 제외한 항목
    no_reloc    {off}                            포인터를 고쳐선 안 되는 항목
    problems    [(사유, 설명)]                   번역 누락 등 진짜 문제
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from hangul_codec import TABLE, SYM_CODE, normalize

_TSET = set(TABLE)
_GA = re.compile(r"\{G\d\d\}")


def encodable(t):
    """번역문이 게임 폰트로 표현 가능한가.

    한자·가나 슬롯은 한글로 재활용되므로, 번역문에 일본 문자가 남아 있으면
    엉뚱한 글자로 출력된다. 그런 문자열은 주입하지 않고 원본을 남긴다.
    """
    for ch in _GA.sub("", normalize(t)):
        o = ord(ch)
        if ch == "\n" or o < 0x80:
            continue
        if 0xAC00 <= o <= 0xD7A3:          # 한글 음절
            continue
        if ch in SYM_CODE:                 # 유지 기호 (・ ー 「 」 등)
            continue
        if 0xFF61 <= o <= 0xFF9F:          # 반각 가나 (원본 조각 보존용)
            continue
        if 0x3041 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            return False                   # 재활용된 슬롯 -> 사용 불가
        try:
            b = ch.encode("cp932")
            if len(b) == 2 and ((b[0] << 8) | b[1]) in _TSET:
                continue
        except Exception:
            pass
        return False
    return True


def load():
    U = json.load(open(paths.inp('units2.json'), encoding="utf-8"))
    es = json.load(open(paths.inp('master_strings.json'), encoding="utf-8"))
    tr = json.load(open(paths.inp('tr_merged.json'), encoding="utf-8"))
    return U, es, tr


def build_plan():
    U, es, tr = load()
    by_off = {e["off"]: e for e in es}

    final, problems, skipped = {}, [], {}

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

    # (a) 리터럴풀/포인터배열로 확인되지 않은 참조 -> 포인터를 고쳐선 안 됨(재배치 금지).
    #     단 제자리 기록은 포인터를 건드리지 않으므로 안전하다.
    try:
        no_reloc = set(json.load(open(paths.inp('unsafe_offsets.json'))))
    except FileNotFoundError:
        no_reloc = set()

    # (b) 겹치는 엔트리 정리.
    #     추출기가 진짜 문자열 '안쪽'을 새 문자열로 오인하는 경우가 있다.
    #     둘 다 쓰면 서로 덮어쓰므로 하나만 남긴다:
    #        검증된 포인터 참조 > 참조 없음 > 미검증 참조, 동급이면 긴 쪽
    def rank(e):
        if e["off"] in no_reloc:  tier = 2      # 미검증 참조(오검출 가능성 높음)
        elif e["refs"]:           tier = 0      # 진짜 포인터가 가리키는 문자열
        else:                     tier = 1
        return (tier, -e["blen"], e["off"])

    occupied = []
    for e in sorted(es, key=rank):
        a, b = e["off"], e["off"] + e["blen"]
        if any(a < ob and oa < b for oa, ob in occupied):
            if e["off"] in final:
                skipped[e["off"]] = "overlap"
                final.pop(e["off"], None)
        else:
            occupied.append((a, b))

    # (c) 표현 불가 문자열 -> 원본 유지
    for off in list(final):
        ko = final[off]
        if ko and not encodable(ko):
            skipped[off] = "unencodable"
            final[off] = None

    return final, skipped, no_reloc, problems, by_off, es


if __name__ == "__main__":
    final, skipped, no_reloc, problems, by_off, es = build_plan()
    from collections import Counter
    print("주입 대상 :", sum(1 for v in final.values() if v is not None))
    print("원본 유지 :", sum(1 for v in final.values() if v is None))
    print("의도적 제외:", len(skipped), Counter(skipped.values()))
    print("재배치 금지:", len(no_reloc))
    print("문제       :", len(problems))
    for p in problems[:10]:
        print("  !", p)
