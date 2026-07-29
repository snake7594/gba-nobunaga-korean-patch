# -*- coding: utf-8 -*-
"""코드 영역(0..0x62000) 변경분이 전부 '의도한 포인터 갱신'인지 확인"""
import struct, json, os
S = os.path.dirname(os.path.abspath(__file__))
OLD = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba", "rb").read()
NEW = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba", "rb").read()
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))

intended = set()          # 포인터 슬롯 주소 (4바이트)
str_span = set()          # 문자열 본문이 차지하는 바이트
for e in es:
    for r in e["refs"]:
        intended.add(r)
    str_span.update(range(e["off"], e["off"] + e["blen"] + e["slack"]))

CODE_END = 0x62000
changed_words = []
for a in range(0, CODE_END, 4):
    if NEW[a:a+4] != OLD[a:a+4]:
        changed_words.append(a)
print("changed 4-byte words in code region:", len(changed_words))

unexpected = [a for a in changed_words
              if a not in intended and not any((a+d) in str_span for d in range(4))]
print("unexpected (neither pointer slot nor inside a string):", len(unexpected))
for a in unexpected[:20]:
    print(f"  {a:#08x}: {OLD[a:a+4].hex()} -> {NEW[a:a+4].hex()}")

# 갱신된 '포인터'가 모두 유효한 문자열 시작을 가리키는가
bad = 0
for a in sorted(intended):
    if a >= CODE_END or NEW[a:a+4] == OLD[a:a+4]: continue
    v = struct.unpack_from("<I", NEW, a)[0]
    if not (0x08000000 <= v < 0x08400000):
        bad += 1; print(f"  BAD PTR {a:#x} -> {v:#x}")
    else:
        t = v - 0x08000000
        if t > 0 and NEW[t-1] != 0:
            bad += 1; print(f"  ptr {a:#x} -> {t:#x} not preceded by NUL")
print("invalid updated pointers:", bad)

# 코드 영역 전체에서 '포인터도 문자열도 아닌' 변경 바이트
partial = [a for a in range(CODE_END)
           if NEW[a] != OLD[a] and (a & ~3) not in intended and a not in str_span]
print("changed bytes that are neither pointer nor string:", len(partial))
for a in partial[:20]: print(f"   {a:#08x}: {OLD[a]:02x} -> {NEW[a]:02x}")

# ROM 전체에 대해서도 동일 검사 (폰트/여유공간 제외)
FONT_LO, FONT_HI = 0x304df4, 0x30d604
FREE_LO = 0x33a1a0
glob = [a for a in range(len(OLD))
        if NEW[a] != OLD[a] and (a & ~3) not in intended and a not in str_span
        and not (FONT_LO <= a < FONT_HI) and a < FREE_LO]
print("global unexplained changed bytes:", len(glob))
for a in glob[:20]: print(f"   {a:#08x}: {OLD[a]:02x} -> {NEW[a]:02x}")
