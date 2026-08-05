import numpy as np
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
rom = np.frombuffer(data, dtype=np.uint8)
LIM = 0x33a200

def best_lags(sig, lo=6, hi=96, k=4):
    n = len(sig)
    x = sig - sig.mean()
    if x.std() == 0: return []
    f = np.fft.rfft(x, 2*n)
    ac = np.fft.irfft(f*np.conj(f))[:hi+1].real
    if ac[0] == 0: return []
    ac = ac/ac[0]
    cand = [(ac[l], l) for l in range(lo, hi+1)]
    cand.sort(reverse=True)
    return cand[:k]

BS = 0x10000
print(f"{'offset':>9} {'dens':>5} {'zfrac':>5}  top periodicities (lag:corr)")
for off in range(0, LIM, BS):
    blk = rom[off:off+BS]
    if len(blk) < 1024: break
    dens = np.unpackbits(blk).mean()
    z = (blk == 0).astype(np.float64)
    zf = z.mean()
    if zf > 0.97 or zf < 0.02:
        continue
    bl = best_lags(z)
    if not bl: continue
    s = "  ".join(f"{l:2d}:{c:.2f}" for c,l in bl)
    flag = ""
    tops = [l for c,l in bl if c > 0.15]
    if any(t in (16,18,24,32,36,48,72) for t in tops): flag = "  <== FONT?"
    print(f"{off:#09x} {dens:5.3f} {zf:5.3f}  {s}{flag}")
