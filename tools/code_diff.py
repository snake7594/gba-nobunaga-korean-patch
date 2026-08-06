# -*- coding: utf-8 -*-
"""코드 영역(0..0x62000) 변경분이 전부 '의도한 포인터 갱신'인지 확인"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import struct, json, os
from glyphs import ADV_SITES_FULL, ADV_SITES_HALF
import logo_patch
import imgtext
S = os.path.dirname(os.path.abspath(__file__))
OLD = open(paths.rom_jp(), "rb").read()
NEW = open(paths.rom_kr(), "rb").read()
es = json.load(open(paths.inp('master_strings.json'), encoding="utf-8"))

# 의도한 코드 패치: 전각·반각 전진폭 6곳 (glyphs.patch_advance)
CODE_PATCH = set(ADV_SITES_FULL) | set(ADV_SITES_HALF)

# 의도한 그림 패치: 타이틀 로고 타일 + 이미지 라벨(버튼·상태창·합전 명령)
GFX = set()
for _s, _e, _base in logo_patch.SEGMENTS:
    GFX.update(range(_base, _base + (_e - _s)*64))
for _s, _e in imgtext.ranges():
    GFX.update(range(_s, _e))

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
              if a not in intended and not any((a+d) in str_span for d in range(4))
              and not any((a+d) in CODE_PATCH for d in range(4))
              and not any((a+d) in GFX for d in range(4))]
print("설명 안 되는 4바이트 워드(포인터·의도한 코드/그림 패치·문자열 제외):",
      len(unexpected))
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
           if NEW[a] != OLD[a] and (a & ~3) not in intended and a not in str_span
           and a not in CODE_PATCH and a not in GFX]
print("설명 안 되는 변경 바이트(코드 영역):", len(partial))
for a in partial[:20]: print(f"   {a:#08x}: {OLD[a]:02x} -> {NEW[a]:02x}")
for a in sorted(CODE_PATCH):
    if NEW[a] != OLD[a]:
        kind = "전각" if a in ADV_SITES_FULL else "반각"
        print(f"   [의도한 코드 패치] {a:#08x}: {OLD[a]:02x} -> {NEW[a]:02x} ({kind} 전진폭)")

# ROM 전체에 대해서도 동일 검사 (폰트/여유공간 제외)
FONT_LO, FONT_HI = 0x304df4, 0x30d604
FREE_LO = 0x33a1a0
glob = [a for a in range(len(OLD))
        if NEW[a] != OLD[a] and (a & ~3) not in intended and a not in str_span
        and not (FONT_LO <= a < FONT_HI) and a < FREE_LO
        and a not in CODE_PATCH and a not in GFX]
print("설명 안 되는 변경 바이트(롬 전체):", len(glob))
for a in glob[:20]: print(f"   {a:#08x}: {OLD[a]:02x} -> {NEW[a]:02x}")
