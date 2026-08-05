import sys
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
N = len(rom)
POP = bytes(bin(i).count('1') for i in range(256))

BS = 1024
dens = []
for off in range(0, 0x340000, BS):
    blk = rom[off:off+BS]
    d = sum(POP[b] for b in blk)/(len(blk)*8)
    dens.append((off, d))

# report contiguous runs where density in a font-plausible band
runs = []
cur = None
for off, d in dens:
    ok = 0.08 <= d <= 0.45
    if ok:
        if cur is None: cur = [off, off+BS]
        else: cur[1] = off+BS
    else:
        if cur: runs.append(tuple(cur)); cur=None
if cur: runs.append(tuple(cur))

print("=== plausible-density runs >= 16KB ===")
for a,b in runs:
    if b-a >= 16*1024:
        blk = rom[a:b]
        d = sum(POP[x] for x in blk)/(len(blk)*8)
        print(f"{a:#08x}-{b:#08x}  len={b-a:#x} ({(b-a)/1024:.0f}KB) dens={d:.3f}")
