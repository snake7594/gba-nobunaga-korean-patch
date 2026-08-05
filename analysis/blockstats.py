import numpy as np
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
LIM = 0x33a200
rom = np.frombuffer(data[:LIM], dtype=np.uint8)

# decode the SJIS we found
print("=== SJIS check @0x320000 ===")
for off in (0x32000E, 0x320016, 0x32002A, 0x330014, 0x330034, 0x330048):
    raw = data[off:off+16]
    end = raw.find(b'\x00')
    if end > 0: raw = raw[:end]
    try:
        print(f"  {off:#x}: {raw.hex(' ')} -> {raw.decode('shift_jis')!r}")
    except Exception as e:
        print(f"  {off:#x}: {raw.hex(' ')} -> ERR {e}")

# longest-bit-run table
def maxrun(b):
    best=cur=0
    for i in range(8):
        if (b>>(7-i))&1: cur+=1; best=max(best,cur)
        else: cur=0
    return best
RUN = np.array([maxrun(i) for i in range(256)], dtype=np.uint8)

BS = 0x1000
print("\n=== per-16KB block stats (z=zero frac, ff=0xFF frac, r6=frac bytes with >=6bit run, d=density) ===")
BS = 0x4000
for off in range(0, LIM, BS):
    blk = rom[off:off+BS]
    if len(blk) < 256: break
    z = float((blk==0).mean())
    ff = float((blk==0xFF).mean())
    r6 = float((RUN[blk]>=6).mean())
    d = float(np.unpackbits(blk).mean())
    # font score: needs blanks AND horizontal strokes
    score = 0.0
    if 0.15 < z < 0.80 and r6 > 0.05:
        score = r6 * (1-abs(z-0.45))
    mark = " *" if score > 0.05 else ""
    if score > 0.03 or off % 0x40000 == 0:
        print(f"{off:#09x} z={z:.3f} ff={ff:.3f} r6={r6:.3f} d={d:.3f} score={score:.3f}{mark}")
