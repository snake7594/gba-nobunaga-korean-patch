import struct, os
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
N = len(data)

def lz77(src, pos):
    """GBA BIOS LZ77 (type 0x10). Returns bytes or None."""
    hdr = src[pos]
    if hdr != 0x10: return None
    size = src[pos+1] | (src[pos+2]<<8) | (src[pos+3]<<16)
    if size < 256 or size > 0x200000: return None
    out = bytearray()
    p = pos+4
    try:
        while len(out) < size:
            flags = src[p]; p += 1
            for i in range(8):
                if len(out) >= size: break
                if flags & (0x80>>i):
                    b0 = src[p]; b1 = src[p+1]; p += 2
                    ln = (b0>>4)+3
                    disp = (((b0&0x0F)<<8)|b1)+1
                    if disp > len(out): return None
                    st = len(out)-disp
                    for k in range(ln):
                        out.append(out[st+k])
                else:
                    out.append(src[p]); p += 1
    except IndexError:
        return None
    return bytes(out[:size]), p-pos

hits = []
for off in range(0, min(N,0x33a200), 4):
    if data[off] != 0x10: continue
    r = lz77(data, off)
    if r:
        blob, clen = r
        if len(blob) >= 2048 and clen > 64:
            hits.append((off, clen, len(blob)))

print(f"LZ77 candidate blocks: {len(hits)}")
# merge/overlap filter: keep non-overlapping greedy by size
hits.sort(key=lambda h: -h[2])
kept, used = [], []
for off, clen, ulen in hits:
    if any(not (off+clen <= a or off >= a+c) for a,c,_ in kept): continue
    kept.append((off,clen,ulen))
kept.sort()
print(f"non-overlapping: {len(kept)}")
tot=0
for off, clen, ulen in kept:
    print(f"  src={off:#08x} clen={clen:#7x} -> ulen={ulen:#7x} ({ulen/1024:.1f}KB) ratio={clen/ulen:.2f}")
    tot += ulen
print("total decompressed:", tot, f"{tot/1024:.0f}KB")

OUT = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad\lz"
os.makedirs(OUT, exist_ok=True)
for off, clen, ulen in kept:
    blob, _ = lz77(data, off)
    open(os.path.join(OUT, f"{off:08x}.bin"),"wb").write(blob)
