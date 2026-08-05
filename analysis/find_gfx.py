# -*- coding: utf-8 -*-
"""VRAM 타일 데이터를 ROM에서 역검색해 원본 위치를 찾는다"""
import sys, os
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1] if len(sys.argv) > 1 else "title"
vram = open(os.path.join(S, f"vram_{tag}.bin"), "rb").read()
rom = paths.read_rom_jp()

# 여러 지점에서 표본을 뽑아 검색 (0 아닌 구간 위주)
print("VRAM char base 0x4000 (BG0, 8bpp) 에서 표본 검색")
found = {}
for probe_off in range(0x4000, 0xE000, 0x400):
    chunk = vram[probe_off:probe_off+64]
    if chunk.count(0) > 50:
        continue
    idx = rom.find(chunk)
    if idx >= 0:
        # 정합 길이 확인
        n = 0
        while (probe_off+n < len(vram) and idx+n < len(rom)
               and vram[probe_off+n] == rom[idx+n]):
            n += 1
        found[probe_off] = (idx, n)
        print(f"  VRAM {probe_off:#07x} -> ROM {idx:#08x}  일치 {n}바이트")
if not found:
    print("  직접 일치 없음 (압축 가능성)")

# 팔레트도 검색
pram = open(os.path.join(S, f"pram_{tag}.bin"), "rb").read()
for p in range(0, 0x400, 0x20):
    c = pram[p:p+32]
    if c.count(0) > 28:
        continue
    i = rom.find(c)
    if i >= 0:
        print(f"  PAL {p//32:2d} -> ROM {i:#08x}")
