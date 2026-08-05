# -*- coding: utf-8 -*-
"""패치 안전성 점검: 어떤 영역이 변경됐는가 / 재배치 포인터의 신뢰도"""
import struct, json, os, sys
from collections import Counter

S = os.path.dirname(os.path.abspath(__file__))
NEW = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba", "rb").read()
OLD = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba", "rb").read()
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))

# 1) 변경 구간 요약
runs = []
i = 0; N = len(OLD)
while i < N:
    if NEW[i] != OLD[i]:
        j = i
        while j < N and NEW[j] != OLD[j]: j += 1
        runs.append((i, j)); i = j
    else:
        i += 1
print(f"changed runs: {len(runs)}, total bytes: {sum(b-a for a,b in runs)}")
buckets = Counter()
for a, b in runs:
    if a < 0x62000: buckets["code/data <0x62000"] += b-a
    elif 0x220000 <= a < 0x260000: buckets["text 0x220000-0x260000"] += b-a
    elif 0x304df4 <= a < 0x30d604: buckets["FONT"] += b-a
    elif 0x30d604 <= a < 0x30e56a: buckets["charmap table"] += b-a
    elif 0x300000 <= a < 0x33a200: buckets["db 0x300000-0x33a200"] += b-a
    elif a >= 0x33a1a0: buckets["appended free space"] += b-a
    else: buckets[f"other {a>>16:#x}xxxx"] += b-a
for k, v in buckets.most_common(): print(f"  {k}: {v} bytes")

# 폰트 테이블(매핑)은 절대 바뀌면 안 됨
assert NEW[0x30d604:0x30e56a] == OLD[0x30d604:0x30e56a], "charmap table modified!"
print("charmap table: unchanged OK")

# 2) 재배치된 문자열의 ref 위치 분포 + 신뢰도
reloc = []
for e in es:
    if not e["refs"]: continue
    v = struct.unpack_from("<I", NEW, e["refs"][0])[0]
    if v - 0x08000000 != e["off"]:
        reloc.append(e)
print(f"\nrelocated strings: {len(reloc)}")
rc = Counter()
for e in reloc:
    for r in e["refs"]:
        rc["code <0x62000" if r < 0x62000 else f"{r>>16:#x}xxxx"] += 1
print("  ref locations:", dict(rc.most_common(8)))
print("  refs per string:", Counter(len(e["refs"]) for e in reloc).most_common(5))

# 3) 각 ref 가 진짜 포인터인지: 원본에서 그 값이 문자열 시작을 정확히 가리켰는가 (이미 보장)
#    추가로 ref 주소가 4정렬인지, 그리고 ref 주변이 포인터 배열인지 확인
solo_ref_code = [e for e in reloc if all(r < 0x62000 for r in e["refs"])]
print(f"  relocated w/ refs only in code region: {len(solo_ref_code)}")
neigh_ok = 0
for e in solo_ref_code:
    r = e["refs"][0]
    around = [struct.unpack_from("<I", OLD, r+d)[0] for d in (-8,-4,4,8) if 0 <= r+d < len(OLD)-3]
    if sum(1 for v in around if 0x08000000 <= v < 0x08400000) >= 1:
        neigh_ok += 1
print(f"  of those, refs adjacent to another 0x08xxxxxx word (literal-pool-like): {neigh_ok}")

# 4) 빈 공간 사용 범위 확인
last = max(b for a, b in runs)
print(f"\nlast changed byte: {last:#x} (ROM end {len(NEW):#x})")
print("original data ended at 0x33a198; free-space writes start at 0x33a1a0")
print("free-space region was all-zero in original:",
      set(OLD[0x33a1a0:0x356a8a]) == {0})
