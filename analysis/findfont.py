import numpy as np
rom = np.frombuffer(open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read(), dtype=np.uint8)
N = len(rom)
LIMIT = 0x33a200
z = (rom[:LIMIT] == 0).astype(np.float32)     # zero-byte indicator
pop = np.unpackbits(rom[:LIMIT]).reshape(-1,8).sum(1).astype(np.float32)

WIN = 32768          # window bytes
STEP = 8192

results = []
for S in (16,18,22,24,26,28,32,36,40,48,64,72):
    nrow = LIMIT//S
    zz = z[:nrow*S].reshape(nrow, S)
    pp = pop[:nrow*S].reshape(nrow, S)
    rows_per_win = WIN//S
    step_rows = max(1, STEP//S)
    for start in range(0, nrow-rows_per_win, step_rows):
        blk = zz[start:start+rows_per_win]
        pb  = pp[start:start+rows_per_win]
        colz = blk.mean(0)                 # zero-fraction per position-in-cell
        dens = pb.mean()/8.0
        if not (0.04 < dens < 0.45):
            continue
        # structure: spread between most-blank and least-blank positions
        spread = colz.max() - colz.min()
        # font signal: some positions nearly always blank (edges), overall not all blank
        nblank = (colz > 0.90).sum()
        if spread > 0.55 and nblank >= 1 and colz.mean() < 0.75:
            results.append((spread, S, start*S, dens, nblank, colz))

results.sort(reverse=True, key=lambda r: r[0])
seen = []
print(f"{'spread':>6} {'stride':>6} {'offset':>10} {'dens':>5} {'nblank':>6}")
for spread, S, off, dens, nblank, colz in results:
    if any(abs(off-o) < 0x8000 and S==s for o,s in seen): continue
    seen.append((off,S))
    print(f"{spread:6.3f} {S:6d} {off:#10x} {dens:5.3f} {nblank:6d}   blankpos={[i for i,v in enumerate(colz) if v>0.9]}")
    if len(seen) >= 25: break
