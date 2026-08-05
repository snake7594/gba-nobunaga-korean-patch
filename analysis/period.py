rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

def period_scan(a, b, maxp=80, label=""):
    seg = rom[a:b]
    n = len(seg)
    # signal: 1 if byte==0 else 0  (glyph edges/blank rows)
    sig = [1 if x == 0 else 0 for x in seg]
    mean = sum(sig)/n
    var = sum((s-mean)**2 for s in sig)
    scores = []
    for p in range(2, maxp+1):
        # correlation at lag p
        s = 0.0
        m = n - p
        for i in range(m):
            s += (sig[i]-mean)*(sig[i+p]-mean)
        scores.append((s/ (var if var else 1), p))
    scores.sort(reverse=True)
    print(f"--- {label} {a:#x}-{b:#x} zero-frac={mean:.3f} top lags:")
    for sc, p in scores[:10]:
        print(f"    lag={p:3d} corr={sc:.4f}")

period_scan(0x103800, 0x103800+0x8000, label="bigfont")
period_scan(0x2f8000, 0x2f8000+0x8000, label="r2f8000")
period_scan(0x32fc00, 0x32fc00+0x8000, label="r32fc00")
period_scan(0x310000, 0x310000+0x5000, label="r310000")
