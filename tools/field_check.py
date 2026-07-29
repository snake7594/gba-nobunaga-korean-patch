# -*- coding: utf-8 -*-
"""DB 고정 필드에 쓴 한글이 원문보다 길어 다음 필드를 침범할 위험이 없는지 점검"""
import json, os, sys, struct
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hangul_codec import Codec, enc_len

S = os.path.dirname(os.path.abspath(__file__))
OLD = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba", "rb").read()
NEW = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba", "rb").read()
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))
by_off = {e["off"]: e for e in es}

# 실제로 새 바이트가 원문 문자열 길이를 넘어선 필드 찾기
grew = []
for e in es:
    if e["kind"] not in ("field", "inline"): continue
    off, blen = e["off"], e["blen"]
    # 새 ROM 에서 이 위치의 문자열 길이
    i = off
    while i < len(NEW) and NEW[i] != 0: i += 1
    nlen = i - off
    if nlen > blen:
        grew.append((off, blen, nlen, e["slack"], e["jp"][:16]))
print("field/inline entries that grew past original length:", len(grew))
print(Counter(n - b for _, b, n, _, _ in grew).most_common(10))

# 레코드 경계 추정: 같은 종류 필드들의 오프셋 간격
field_offs = sorted(e["off"] for e in es if e["kind"] == "field")
gaps = Counter(b - a for a, b in zip(field_offs, field_offs[1:]) if 0 < b - a < 200)
print("\ncommon field offset gaps:", gaps.most_common(12))

# 침범 검사: 성장한 필드의 새 끝이 '다음 엔트리 시작'을 넘었는가
viol = []
for off, blen, nlen, slack, jp in grew:
    nxt = None
    for e in es:
        if e["off"] > off:
            if nxt is None or e["off"] < nxt: nxt = e["off"]
    if nxt is not None and off + nlen >= nxt:
        viol.append((hex(off), blen, nlen, hex(nxt), jp))
print("\nentries whose new text reaches the next entry:", len(viol))
for v in viol[:15]: print("  ", v)

# 성장분이 원본에서 모두 0 이었는지(=패딩만 사용) 최종 확인
bad = []
for off, blen, nlen, slack, jp in grew:
    if any(OLD[off+blen:off+nlen]):
        bad.append((hex(off), blen, nlen, jp, OLD[off+blen:off+nlen].hex()))
print("\ngrew into NON-zero original bytes:", len(bad))
for b in bad[:15]: print("  ", b)
