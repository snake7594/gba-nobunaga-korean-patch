# -*- coding: utf-8 -*-
"""이름·지명을 일본어 읽기로 치환한다.

두 곳을 고쳐야 한다.
  1) DB 고정 필드 — 원문이 한자 그 자체(織田 / 信長)이므로 읽기표로 바로 치환
  2) 본문(대사·열전) — 이미 한자 독음으로 번역돼 있으므로(직전신장)
     '독음 → 일본어 읽기' 로 다시 치환

2)는 오치환 위험이 있어, 한국어 일반 낱말과 겹치는 독음은 제외한다.
"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
import paths
from eumdok import KANJI_READ, KANJI_SKIP
from yomi_place import PLACE, TITLE
from yomi_surname import SURNAME
from yomi_given import GIVEN

DUEUM = {
    "라": "나", "락": "낙", "란": "난", "랄": "날", "람": "남", "랍": "납",
    "랑": "낭", "래": "내", "랭": "냉", "량": "양", "려": "여", "력": "역",
    "련": "연", "렬": "열", "렴": "염", "렵": "엽", "령": "영", "례": "예",
    "로": "노", "록": "녹", "론": "논", "롱": "농", "뢰": "뇌", "료": "요",
    "룡": "용", "루": "누", "류": "유", "륙": "육", "륜": "윤", "률": "율",
    "륭": "융", "륵": "늑", "름": "늠", "릉": "능", "리": "이", "린": "인",
    "림": "임", "립": "입", "녀": "여", "년": "연", "념": "염", "녕": "영",
    "뇨": "요", "뉴": "유", "니": "이", "닉": "익", "님": "임",
}

# 읽기표 통합 (지명 > 성 > 이름 순으로 우선)
YOMI = {}
YOMI.update(GIVEN)
YOMI.update(SURNAME)
YOMI.update(TITLE)
YOMI.update(PLACE)

SURNAME_SET = set(SURNAME)

# 독음이 한국어 일반 낱말과 겹치는 항목.
#   SOLO  = 단독으로는 치환하지 않지만 '성+이름' 결합형에서는 허용
#           (본다=sees 이지만 '본다충승'은 本多忠勝 이 확실하다)
#   NEVER = 결합형에서도 쓰지 않음
AMBIGUOUS_SOLO = {
    "本多", "大和", "中国", "田原", "青山", "山川", "山中", "一色",
    "土岐", "大内", "国司", "伊藤", "江戸", "清水", "長政", "正則",
    "義元", "成実", "家次", "三成", "武蔵", "信濃", "近江", "出羽",
    "日向",   # 일향 = 一向宗(일향종)
    "伊東",   # 이동 = 移動
    "相模", "上総", "下総", "安房", "伊豆", "志摩", "和泉",
}
AMBIGUOUS_NEVER = {"森", "島", "岡", "堀", "林", "原", "関", "長", "陶", "桂", "京"}
AMBIGUOUS = AMBIGUOUS_SOLO | AMBIGUOUS_NEVER

# 성 없이 단독으로 나와도 그 인물이 확실한 이름
FAMOUS_GIVEN = {
    "信長", "秀吉", "家康", "信玄", "謙信", "政宗", "元就", "氏康", "元親",
    "宗麟", "隆信", "義弘", "光秀", "勝家", "利家", "三成", "清正", "幸村",
    "昌幸", "勝頼", "信忠", "秀長", "秀頼", "輝元", "隆景", "元春", "道三",
    "久秀", "長慶", "義輝", "義昭", "氏政", "輝宗", "信繁", "景勝", "兼続",
}


def _inventory():
    """게임에 실제로 존재하는 한자어 집합 (없는 이름으로 규칙을 만들지 않기 위함)"""
    import json
    try:
        items = json.load(open(paths.inp("namelist.json"), encoding="utf-8"))
    except FileNotFoundError:
        return None
    return {it["jp"]: it.get("count", 1) for it in items}


def _real_pairs():
    """실제 게임에 존재하는 (성, 이름) 조합.

    무장 레코드는 성(7바이트) 바로 뒤에 이름(7바이트)이 온다. 테이블이 여러 곳에
    흩어져 있고 스트라이드도 달라서, 레이아웃을 가정하지 않고
    '추출된 필드 문자열 중 주소가 정확히 7 차이 나는 이웃'을 조합으로 본다.
    """
    import json
    try:
        es = json.load(open(paths.inp("master_strings.json"), encoding="utf-8"))
    except FileNotFoundError:
        return set()
    fields = sorted((e["off"], e["jp"]) for e in es if e["kind"] == "field")
    by = dict(fields)
    out = set()
    for off, jp in fields:
        nxt = by.get(off + 7)
        if nxt and jp in SURNAME and nxt in GIVEN:
            out.add((jp, nxt))
    return out


def eumdok(word, dueum=True):
    """한자어 -> 한자 독음. 번역문에 쓰인 형태를 재현한다.

    dueum=False 는 낱말 중간에 오는 경우(성+이름의 이름 부분)로,
    두음법칙이 적용되지 않는다. 예: 隆景 단독 '융경' / 小早川隆景 안에서는 '륭경'
    """
    out = []
    for ch in word:
        if ch in KANJI_SKIP:
            return None
        r = KANJI_READ.get(ch)
        if r is None:
            return None
        out.append(r)
    if out and dueum:
        out[0] = DUEUM.get(out[0], out[0])
    return "".join(out)


def reading(word, with_space=False):
    """한자어 -> 일본어 읽기(한글). 없으면 None"""
    r = YOMI.get(word)
    if r is None:
        return None
    if with_space and word in SURNAME_SET:
        return r + " "
    return r


def field_text(word, cap, cost_fn):
    """DB 필드용: 용량에 맞으면 성 뒤 공백을 붙이고, 넘치면 뺀다."""
    r = YOMI.get(word)
    if r is None:
        return None
    if word in SURNAME_SET:
        withsp = r + " "
        if cost_fn(withsp) <= cap - 1:
            return withsp
    return r if cost_fn(r) <= cap - 1 else None


def has_batchim(syl):
    o = ord(syl)
    if not (0xAC00 <= o <= 0xD7A3):
        return False
    return (o - 0xAC00) % 28 != 0


# 앞말 받침 유무에 따라 갈리는 조사 (받침있음, 받침없음)
PARTICLES = [("은", "는"), ("이", "가"), ("을", "를"), ("과", "와"),
             ("아", "야"), ("으로", "로"), ("이나", "나"), ("이란", "란"),
             ("이라", "라"), ("이여", "여"), ("이며", "며"), ("이고", "고")]


def fix_particle(new_word, rest):
    """치환된 이름 뒤의 조사를 새 이름의 받침에 맞게 고친다"""
    if not new_word or not rest:
        return rest
    last = new_word.rstrip()[-1:] if new_word.rstrip() else ""
    if not last:
        return rest
    bat = has_batchim(last)
    for a, b in PARTICLES:
        if rest.startswith(a) and not bat:
            return b + rest[len(a):]
        if rest.startswith(b) and bat:
            # '로'는 ㄹ 받침 뒤에서 그대로
            if b == "로" and last and (ord(last) - 0xAC00) % 28 == 8:
                return rest
            return a + rest[len(b):]
    return rest


def body_rules():
    """본문 치환 규칙 {독음: 일본어읽기} — 성+이름 결합형과 단독형

    게임에 실제로 존재하는 이름만 대상으로 한다. 그렇지 않으면 실제로는
    쓰이지 않는 동음이의 이름(예: 信賢) 때문에 정작 필요한 규칙(信玄)이
    '모호'로 판정돼 사라진다.
    """
    inv = _inventory()
    real = _real_pairs()          # DB에 실제로 있는 (성, 이름) 조합
    rules = {}
    prio = {}

    def add(e, r, p=0):
        """같은 독음이 겹치면 우선순위가 높은 쪽을 남긴다.
        우선순위: 실제 존재하는 조합 > 등장 빈도 > 동점이면 폐기(모호)"""
        if e not in rules:
            rules[e] = r; prio[e] = p
        elif rules[e] == r:
            prio[e] = max(prio[e], p)
        elif p > prio[e]:
            rules[e] = r; prio[e] = p
        elif p == prio[e]:
            rules[e] = None       # 동점 모호 -> 폐기

    # 이름(名)만 인벤토리로 거른다. 게임에 없는 동음이의 이름이 끼어들면
    # 정작 필요한 규칙이 '모호'로 판정돼 사라지기 때문이다 (信玄 vs 信賢).
    # 성(姓)은 DB 필드에 없고 본문에만 나오는 것도 있어 거르지 않는다 (長宗我部).
    sur = {s: v for s, v in SURNAME.items() if s not in AMBIGUOUS_NEVER}
    giv = {g: v for g, v in GIVEN.items()
           if g not in AMBIGUOUS_NEVER and (inv is None or g in inv)}

    # 성+이름 결합형 (직전신장 -> 오다 노부나가)
    # 이름 부분은 낱말 중간이므로 두음법칙을 적용하지 않는다 (小早川隆景 = 소조천'륭'경)
    for s, sr in sur.items():
        se = eumdok(s)
        if not se or len(se) < 2:
            continue
        for g, gr in giv.items():
            ge = eumdok(g, dueum=False)
            if not ge or len(ge) < 2:
                continue
            # 실제 게임에 있는 조합이면 가중치를 크게 (明智光秀 > 明智光寿)
            p = 1000 + (inv.get(g, 0) if inv else 0) if (s, g) in real else (inv.get(g, 0) if inv else 0)
            add(se + ge, sr + " " + gr, p)

    # 지명 + '국/성' 접미형 (대화국 -> 야마토국)
    for w, r in PLACE.items():
        e = eumdok(w)
        if not e or len(e) < 2:
            continue
        for suf in ("국", "성", "군", "가"):
            add(e + suf, r + suf)

    # 단독 낱말 — 성·지명·관직만. 이름(名)은 단독으로 쓰면 오치환이 잦다
    # (예: 綱成=강성 이 '岡城(강성)' 을 잡아먹는다). 이름은 성과 함께 올 때만 바꾼다.
    for w, r in list(PLACE.items()) + list(TITLE.items()) + list(SURNAME.items()):
        if w in AMBIGUOUS:
            continue
        e = eumdok(w)
        if e and len(e) >= 2:
            add(e, r)
    # 단독으로 써도 안전한 유명 인물 이름만 예외로 허용
    for w in FAMOUS_GIVEN:
        r = GIVEN.get(w)
        if not r:
            continue
        e = eumdok(w)
        if e and len(e) >= 2:
            add(e, r)

    return {e: r for e, r in rules.items() if r}


_RULES = None
_RE = None


def _prepare():
    global _RULES, _RE
    if _RULES is None:
        _RULES = body_rules()
        keys = sorted(_RULES, key=len, reverse=True)
        _RE = re.compile("|".join(re.escape(k) for k in keys))


def _is_hangul(ch):
    return "가" <= ch <= "힣"


# 짧은 이름 뒤에 올 수 있는 것 — 조사·구두점·공백. 그 밖의 한글이 이어지면
# 낱말의 일부일 가능성이 커서 치환하지 않는다.
#   移動시킵니다 / 加하거나 / 前轉하였다 / 結成되었다 …
_OK_AFTER = set("은는이가을를와과의에도만로으께야여랑나든지"
                " 　\n,.，。、·…~-/:;!?()（）「」『』[]0123456789")


def _ok_after(text, end):
    if end >= len(text):
        return True
    ch = text[end]
    if ch in _OK_AFTER:
        return True
    return not _is_hangul(ch)


def apply_body(text):
    """번역문 속 한자 독음 이름을 일본어 읽기로 치환 (뒤 조사 보정 포함)

    앞이 한글로 이어지는 자리는 건너뛴다. 이름이 아닌 낱말의 일부를 잘라
    치환하는 사고를 막기 위함이다 (예: '藤岡城'의 '강성'을 綱成 으로 오인).
    단, 바로 앞이 방금 치환된 자리면 허용한다 (徳川四天王 처럼 이어지는 경우).
    """
    _prepare()
    pos = 0
    just_replaced_end = -1
    while True:
        m = _RE.search(text, pos)
        if not m:
            return text
        i = m.start()
        ok = (i == 0 or not _is_hangul(text[i-1]) or i == just_replaced_end)
        # 짧은 이름(3음절 이하)은 뒤에 조사·구두점이 와야 이름으로 인정한다.
        # 결합형(4음절 이상)은 그 자체로 고유하므로 검사하지 않는다.
        if ok and len(m.group(0)) <= 3 and not _ok_after(text, m.end()):
            ok = False
        if not ok:
            pos = i + 1
            continue
        new = _RULES[m.group(0)]
        rest = fix_particle(new, text[m.end():])
        # 성 뒤에 낱말이 바로 붙으면 띄어 준다 (오다가신 -> 오다 가신)
        if (rest and _is_hangul(rest[0]) and not new.endswith(" ")
                and rest[:1] not in ("의", "은", "는", "이", "가", "을", "를",
                                     "와", "과", "에", "도", "만", "께", "로")):
            rest = " " + rest
        text = text[:i] + new + rest
        pos = i + len(new)
        just_replaced_end = pos


if __name__ == "__main__":
    print("읽기표:", len(YOMI))
    rules = body_rules()
    print("본문 치환 규칙:", len(rules))
    for t in ["직전신장의 적남이다.", "덕천가강과 상삼겸신",
              "풍신수길이 구주를 정벌했다", "무전신현의 가신 산현창경"]:
        print(f"  {t}  ->  {apply_body(t)}")
