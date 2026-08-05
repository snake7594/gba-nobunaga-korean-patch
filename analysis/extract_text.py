# -*- coding: utf-8 -*-
"""ROM 전체 SJIS 문자열 스캔.
게임 폰트가 지원하는 문자(테이블 0x30D6CE의 1869자 + ASCII)만 유효 문자로 간주."""
import struct, json
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

TB2 = 0x30d6ce; N2 = 1869
valid2 = set()
for i in range(N2):
    valid2.add(struct.unpack_from("<H", rom, TB2+i*2)[0])

LIMIT = 0x33a200

strings = []
i = 0
while i < LIMIT - 1:
    v = (rom[i] << 8) | rom[i+1]
    if v in valid2:
        # start of a candidate run of 2-byte chars
        j = i; chars = 0
        while j < LIMIT-1:
            w = (rom[j] << 8) | rom[j+1]
            if w in valid2:
                j += 2; chars += 1
            else:
                break
        if chars >= 2:  # at least 2 full-width chars
            raw = rom[i:j]
            try:
                txt = raw.decode("cp932")
            except Exception:
                txt = None
            if txt:
                strings.append({"off": i, "len": j-i, "text": txt})
            i = j
            continue
    i += 1

print("runs >=2 chars:", len(strings))
tot = sum(s["len"] for s in strings)
print("total bytes:", tot)

# 분포 확인: 어느 영역에 몰려있나
from collections import Counter
c = Counter(s["off"] >> 16 for s in strings)
for k in sorted(c):
    print(f"  0x{k:03x}xxxx: {c[k]} strings")

json.dump(strings, open(S+r"\sjis_runs.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved sjis_runs.json")

# 샘플 출력
for s in strings[:20]:
    print(hex(s["off"]), s["len"], repr(s["text"][:24]))
