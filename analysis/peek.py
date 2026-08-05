# -*- coding: utf-8 -*-
import sys
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

def dump(off, n=256, w=16):
    for r in range(0, n, w):
        c = rom[off+r:off+r+w]
        hx = " ".join(f"{b:02x}" for b in c)
        try_txt = []
        k = 0
        while k < len(c):
            b = c[k]
            if 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEB:
                try:
                    try_txt.append(bytes(c[k:k+2]).decode("cp932")); k += 2; continue
                except Exception:
                    pass
            try_txt.append(chr(b) if 32 <= b < 127 else "."); k += 1
        print(f"{off+r:07x}  {hx}  {''.join(try_txt)}")

for a in [int(x,16) for x in sys.argv[1:]]:
    print(f"===== {a:#x} =====")
    dump(a)
    print()
