import numpy as np
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
rom = np.frombuffer(data, dtype=np.uint8)

def hx(off, n=256, w=32):
    for r in range(0, n, w):
        chunk = data[off+r:off+r+w]
        print(f"{off+r:08x}  " + " ".join(f"{b:02x}" for b in chunk))

print("=== 0x10bf00 ===");  hx(0x10bf00, 128)
print("=== 0x10c000 ===");  hx(0x10c000, 128)

# map extent of "odd bytes are zero"
LIM = 0x33a200
ev = rom[0:LIM:2]; od = rom[1:LIM:2]
BS = 2048
print("\n=== regions where >95% of odd bytes are zero (block=2KB) ===")
runs=[]; cur=None
for i in range(0, LIM//2 - BS, BS):
    frac = float((od[i:i+BS]==0).mean())
    if frac > 0.95:
        if cur is None: cur=[i*2,(i+BS)*2]
        else: cur[1]=(i+BS)*2
    else:
        if cur: runs.append(tuple(cur)); cur=None
if cur: runs.append(tuple(cur))
for a,b in runs:
    if b-a >= 0x2000: print(f"  {a:#08x}-{b:#08x} len={b-a:#x}")
