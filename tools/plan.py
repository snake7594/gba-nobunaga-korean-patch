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
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from hangul_codec import TABLE, SYM_CODE, normalize
import halfwidth

_TSET = set(TABLE)
_GA = re.compile(r"\{G\d\d\}")

# 이름·지명을 일본어 읽기로 표기할지 (0 이면 한자 독음 유지)
JP_NAMES = os.environ.get("NOBU2_JPNAMES", "1") != "0"

# 문자 전진폭(px) — inject.py 와 같은 값을 써야 줄 수 계산이 맞는다
ADVANCE = int(os.environ.get("NOBU2_ADVANCE", "7"))

# 성+이름 명판의 안쪽 폭(px). 이보다 길어지는 이름은 성 뒤 공백을 빼서 줄인다.
NAME_PLATE_PX = 64


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

    # (b-2) 이미지 라벨(스프라이트 타일) 안을 문자열로 오인한 항목 제외.
    #       그림 데이터라 텍스트를 써 넣으면 버튼·상태창 그림이 깨진다.
    import imgtext
    gfx = []
    for arr in imgtext.ARRAYS:
        offs = arr.get("offs") or [arr["base"] + k*arr["stride"]
                                   for k in range(arr["n"])]
        nb = (arr["w"]*16)//64*32
        gfx += [(offs[k], offs[k]+nb) for k in arr["items"]]
    for off in list(final):
        e = by_off[off]
        a, b = off, off + e["blen"] + e["slack"]
        if any(a < gb and ga < b for ga, gb in gfx):
            skipped[off] = "image"
            final.pop(off)

    # (c) 표현 불가 문자열 -> 원본 유지
    for off in list(final):
        ko = final[off]
        if ko and not encodable(ko):
            skipped[off] = "unencodable"
            final[off] = None

    # (d) 이름·지명을 일본어 읽기로 (반각 1바이트 인코딩 포함)
    halfmap = apply_jp_names(final, by_off) if JP_NAMES else {}

    return final, skipped, no_reloc, problems, by_off, es, halfmap


def apply_jp_names(final, by_off):
    """한자 독음으로 되어 있던 이름·지명을 일본어 읽기로 바꾸고
       반각 1바이트 음절 배정표를 만든다.

    고정 길이 필드(성 7바이트)에 `노부나가`(전각 8바이트)가 안 들어가므로
    자주 쓰이는 음절을 1바이트 코드로 배정한다 (halfwidth.py 참고).
    """
    import names as NAMES

    # 1) DB 필드 후보 읽기 (성은 뒤에 공백)
    cand = {}
    for off in final:
        e = by_off[off]
        if e["kind"] not in ("field", "inline"):
            continue
        r = NAMES.YOMI.get(e["jp"])
        if r:
            cand[off] = r + (" " if e["jp"] in NAMES.SURNAME_SET else "")

    # 2) 본문(대사·열전) 속 독음 이름 치환
    body_new = {}
    for off, ko in final.items():
        if ko is None or by_off[off]["kind"] == "field":
            continue
        nk = NAMES.apply_body(ko)
        if nk != ko:
            body_new[off] = nk

    # 3) 음절 빈도 -> 반각 슬롯 배정
    freq = Counter()
    for t in list(cand.values()) + list(body_new.values()):
        for ch in t:
            if "가" <= ch <= "힣":
                freq[ch] += 1
    halfmap = halfwidth.build_map([s for s, _ in freq.most_common(len(halfwidth.FREE_CODES))])

    def hcost(t):
        return sum(1 if (ord(c) < 0x80 or c in halfmap) else 2 for c in t)

    # 4) 용량에 맞으면 적용
    #    성 뒤 공백은 바이트가 아니라 '화면 폭' 때문에도 뺀다. 명판 안쪽은 64px 라
    #    전진폭 7px 기준 9글자까지만 들어간다. 성+이름이 그보다 길면 공백을 뺀다.
    #    (`이나와시로 모리쿠니` 10글자 → 70px 로 잘리던 것이 `이나와시로모리쿠니` 63px)
    given_len = {}
    for off, t in cand.items():
        e = by_off[off]
        if e["jp"] not in NAMES.SURNAME_SET:
            given_len[off] = len(t)
    for off, t in cand.items():
        e = by_off[off]
        capn = e["blen"] + e["slack"] - 1
        use = t
        if e["jp"] in NAMES.SURNAME_SET:
            pair = given_len.get(off + 7, 4)          # 같은 레코드의 이름 필드
            if hcost(use) > capn or (len(t) + pair) * ADVANCE > NAME_PLATE_PX:
                use = t.rstrip()
        if hcost(use) <= capn:
            final[off] = use
    for off, nk in body_new.items():
        final[off] = nk

    # 5) 창 넘침 정리 — 일본어 읽기는 한자 독음보다 길어 줄이 늘 수 있다.
    #    원문 자체가 창 크기에 맞춰 문장 도중에 잘려 있으므로, 같은 방식으로 줄인다.
    trim_to_window(final, by_off, halfmap)
    return halfmap


_FMT = re.compile(r"%[-0-9]*[sd]")


def _lines(t, limit, adv_full, halfmap=None, adv_half=8):
    """게임의 자동 줄바꿈 규칙으로 줄 수 계산"""
    t = _GA.sub("　", t)
    t = _FMT.sub("　　　", t)
    n, x = 1, 0
    for ch in t:
        if ch == "\n":
            n += 1; x = 0; continue
        w = adv_half if ord(ch) < 0x80 else adv_full
        if x + w > limit:
            n += 1; x = 0
        x += w
    return n


def trim_to_window(final, by_off, halfmap, advance=ADVANCE):
    """번역이 원문보다 줄이 늘어난 경우 원문 줄 수에 맞게 잘라낸다.

    포맷 코드(%s·%d)가 있는 문자열은 인자 개수가 달라지면 위험하므로 건드리지 않는다.
    """
    trimmed = 0
    for off, ko in list(final.items()):
        if ko is None or _FMT.search(ko):
            continue
        jp = by_off[off]["jp"]
        for limit in (216, 240):
            lj = _lines(jp, limit, 12)                       # 원문은 전각 12·반각 8px
            if _lines(ko, limit, advance, halfmap, advance) <= lj:
                continue
            cut = ko
            while cut and _lines(cut, limit, advance, halfmap, advance) > lj:
                # 낱말 경계에서 자르되, 안 되면 한 글자씩
                sp = cut.rstrip().rfind(" ")
                cut = cut[:sp] if sp > len(cut) * 0.5 else cut[:-1]
            cut = cut.rstrip(" ,.、。")
            if cut and cut != ko:
                final[off] = cut
                trimmed += 1
            break
    if trimmed:
        print(f"창 넘침 정리(원문 줄 수에 맞춰 절단): {trimmed}건")


if __name__ == "__main__":
    final, skipped, no_reloc, problems, by_off, es, halfmap = build_plan()
    print("반각 음절 :", len(halfmap))
    print("주입 대상 :", sum(1 for v in final.values() if v is not None))
    print("원본 유지 :", sum(1 for v in final.values() if v is None))
    print("의도적 제외:", len(skipped), Counter(skipped.values()))
    print("재배치 금지:", len(no_reloc))
    print("문제       :", len(problems))
    for p in problems[:10]:
        print("  !", p)
