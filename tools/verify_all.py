# -*- coding: utf-8 -*-
"""전수 검증: 모든 엔트리에 대해 (포인터 추적 후) 실제 ROM 바이트를 디코드해
   의도한 한국어와 일치하는지 확인.

주입기(inject.py)와 같은 계획(plan.py)을 쓴다. 검증기가 다른 기준을 쓰면
'의도적으로 제외한 항목'이 불일치로 잡혀 실제 결함과 구분되지 않는다.
"""
import os, sys, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from hangul_codec import normalize
from plan import build_plan
from collections import Counter

NEW = paths.read_rom_kr()
OLD = paths.read_rom_jp()
FONT2 = paths.FONT_BASE
TB2 = paths.TABLE_BASE
N2 = paths.TABLE_N
GAIJI0 = paths.GAIJI0
table = [struct.unpack_from("<H", NEW, TB2 + i*2)[0] for i in range(N2)]
idx_of = {v: i for i, v in enumerate(table)}
charmap = json.load(open(paths.inp('charmap.json'), encoding="utf-8"))
slot2syl = {v: k for k, v in charmap.items()}

final, skipped, no_reloc, problems, by_off, es, halfmap = build_plan()
# 반각 1바이트 코드 -> 음절 (이름 필드용)
code2syl = {c: s for s, c in halfmap.items()}


def decode(off, maxb=4096):
    """게임과 동일한 조회 로직으로 ROM 바이트를 문자열로 되돌린다"""
    out = []; i = off
    while i < len(NEW) and NEW[i] != 0 and i - off < maxb:
        b = NEW[i]
        if b == 0x0A: out.append("\n"); i += 1; continue
        if b in code2syl: out.append(code2syl[b]); i += 1; continue
        if b < 0x80: out.append(chr(b)); i += 1; continue
        if 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode("cp932")); i += 1; continue
        v = (b << 8) | NEW[i+1]
        gi = idx_of.get(v)
        if gi is None: out.append("�")
        elif gi in slot2syl: out.append(slot2syl[gi])
        elif gi >= GAIJI0: out.append("{G%02d}" % (gi - GAIJI0))
        else:
            try: out.append(bytes([b, NEW[i+1]]).decode("cp932"))
            except Exception: out.append("�")
        i += 2
    return "".join(out), i - off


ok = bad = 0
mismatches = []
for off, ko in final.items():
    if ko is None:          # 원본 유지 대상 -> 대조하지 않음
        continue
    e = by_off[off]
    # 현재 유효 주소: refs 가 있으면 첫 ref 의 포인터를 따라감
    cur = off
    if e["refs"]:
        v = struct.unpack_from("<I", NEW, e["refs"][0])[0]
        if 0x08000000 <= v < 0x08400000:
            cur = v - 0x08000000
    got, _ = decode(cur)
    if got == normalize(ko):
        ok += 1
    else:
        bad += 1
        if len(mismatches) < 30:
            mismatches.append({"off": hex(off), "cur": hex(cur),
                               "want": ko[:60], "got": got[:60]})

print(f"주입 대조 : OK {ok} / 불일치 {bad}")
for m in mismatches:
    # 콘솔 인코딩이 cp949 라 일부 문자에서 죽는다. 못 찍는 글자는 이스케이프한다.
    line = f"   {m['off']} -> {m['cur']} | want {m['want']!r} | got {m['got']!r}"
    print(line.encode(sys.stdout.encoding or "utf-8", "backslashreplace")
              .decode(sys.stdout.encoding or "utf-8", "replace"))
json.dump(mismatches, open(paths.out('verify_mismatch.json'), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

nskip = Counter(skipped.values())
print(f"의도적 제외: {len(skipped)} (겹침 오검출 {nskip.get('overlap',0)}, "
      f"표현불가 {nskip.get('unencodable',0)}) — 원본 바이트 유지")
print(f"번역 누락  : {len(problems)}")

# 포인터 무결성: 모든 refs 가 ROM 범위 안을 가리키는가
badptr = 0
for e in es:
    for r in e["refs"]:
        v = struct.unpack_from("<I", NEW, r)[0]
        if not (0x08000000 <= v < 0x08400000):
            badptr += 1
print("포인터 이상:", badptr)

# ROM 크기/헤더 무결성
print("크기:", len(NEW), "(원본과 동일:", len(NEW) == len(OLD), ")",
      "헤더 보존:", NEW[0xA0:0xB0] == OLD[0xA0:0xB0])

if bad == 0 and badptr == 0 and not problems:
    print("\n>>> 검증 통과")
else:
    print("\n>>> 확인 필요")
    sys.exit(1)
