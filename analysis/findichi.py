import numpy as np
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
N = 0x33a200

def runlen_bits(v, nbits):
    """longest run of consecutive 1 bits in integer v (nbits wide)"""
    best = cur = 0
    for i in range(nbits):
        if (v >> (nbits-1-i)) & 1:
            cur += 1; best = max(best,cur)
        else:
            cur = 0
    return best

# zero-run map
z = np.frombuffer(data[:N], dtype=np.uint8) == 0
# prefix count of zeros ending at i (inclusive)
zr = np.zeros(N, dtype=np.int32)
c = 0
zl = z.tolist()
for i in range(N):
    c = c+1 if zl[i] else 0
    zr[i] = c
# zeros starting at i
zf = np.zeros(N+1, dtype=np.int32)
c = 0
for i in range(N-1, -1, -1):
    c = c+1 if zl[i] else 0
    zf[i] = c

hits = []
for i in range(1, N-4):
    if zl[i] or zl[i+1]:
        continue
    # candidate 2-byte "bar" row at i..i+1
    v = (data[i] << 8) | data[i+1]
    if runlen_bits(v, 16) < 9:
        continue
    before = zr[i-1]
    after = zf[i+2]
    if before >= 8 and after >= 8:
        hits.append((i, before, after, v))

print("bar-glyph candidates:", len(hits))
# cluster
clusters = []
cur = None
for i, b, a, v in hits:
    if cur and i - cur[1] < 0x800:
        cur[1] = i; cur[2] += 1
    else:
        if cur: clusters.append(cur)
        cur = [i, i, 1]
if cur: clusters.append(cur)
clusters.sort(key=lambda c: -c[2])
print("\ntop clusters (start, end, count):")
for s, e, n in clusters[:20]:
    print(f"  {s:#08x}-{e:#08x}  n={n}")
