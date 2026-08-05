# -*- coding: utf-8 -*-
"""LZ77(GBA BIOS 형식)로 압축된 그래픽 안에서 화면 타일을 찾는다

압축되지 않은 구간을 다 훑어도 안 나오는 그림이 있어, 압축 블록까지 열어 본다.
헤더는 `10 ss ss ss` (0x10 = LZ77, 24비트 원본 크기).
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths


def lz77(data, pos, out_size, limit=None):
    """BIOS LZ77 풀기. 실패하면 None"""
    out = bytearray()
    n = len(data)
    while len(out) < out_size:
        if pos >= n:
            return None
        flags = data[pos]; pos += 1
        for b in range(8):
            if len(out) >= out_size:
                break
            if flags & (0x80 >> b):
                if pos+1 >= n:
                    return None
                d = (data[pos] << 8) | data[pos+1]; pos += 2
                ln = (d >> 12) + 3
                disp = (d & 0xFFF) + 1
                if disp > len(out):
                    return None
                s = len(out) - disp
                for k in range(ln):
                    out.append(out[s+k])
            else:
                out.append(data[pos]); pos += 1
        if limit and len(out) > limit:
            return None
    return bytes(out)


def blocks(rom, lo=0, hi=None, min_size=0x200, max_size=0x20000):
    """그럴듯한 LZ77 블록 [(오프셋, 원본크기, 푼 데이터)]"""
    hi = hi or len(rom)
    out = []
    i = lo
    while i < hi-4:
        if rom[i] == 0x10:
            size = rom[i+1] | (rom[i+2] << 8) | (rom[i+3] << 16)
            if min_size <= size <= max_size:
                d = lz77(rom, i+4, size, max_size)
                if d is not None and len(d) == size:
                    out.append((i, size, d))
                    i += 4
                    continue
        i += 4
    return out


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    lo = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0
    hi = int(sys.argv[2], 16) if len(sys.argv) > 2 else len(rom)
    bs = blocks(rom, lo, hi)
    print(f"LZ77 블록 {len(bs)}개")
    tot = 0
    for off, size, _ in bs[:40]:
        print(f"  {off:#08x}  원본 {size:#x}")
    for _, s, _ in bs:
        tot += s
    print(f"합계 원본 {tot:#x} 바이트")
