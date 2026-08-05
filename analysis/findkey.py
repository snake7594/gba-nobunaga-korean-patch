# -*- coding: utf-8 -*-
"""KEYINPUT(0x04000130)을 읽어 저장하는 코드/변수 찾기"""
import sys, struct
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

rom = paths.read_rom_jp()
CODE_END = 0x62000

# 리터럴 풀에서 0x04000130 / 0x04000000 찾기
lits = []
for a in range(0, CODE_END, 4):
    v = struct.unpack_from("<I", rom, a)[0]
    if v in (0x04000130, 0x04000000):
        lits.append((a, v))
print(f"리터럴 {len(lits)}개")
for a, v in lits[:20]:
    print(f"  {0x08000000+a:#010x} = {v:#010x}")

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
# 리터럴을 참조하는 ldr 을 찾아 주변 디스어셈블
for a, v in lits[:6]:
    print(f"\n=== 리터럴 {0x08000000+a:#x} ({v:#x}) 참조 코드 ===")
    for c in range(max(0, a-1024), a, 2):
        hw = rom[c] | (rom[c+1] << 8)
        if 0x4800 <= hw <= 0x4FFF:
            tgt = ((c + 4) & ~3) + (hw & 0xFF) * 4
            if tgt == a:
                lo = max(0, c-8)
                code = rom[lo:c+56]
                for ins in md.disasm(code, 0x08000000+lo):
                    print(f"   {ins.address:08x}: {ins.mnemonic:8}{ins.op_str}")
                break
