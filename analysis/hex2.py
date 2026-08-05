data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
def hx(off, n=192, w=24):
    for r in range(0,n,w):
        c = data[off+r:off+r+w]
        asc = "".join(chr(b) if 32<=b<127 else "." for b in c)
        print(f"{off+r:08x}  " + " ".join(f"{b:02x}" for b in c) + "  " + asc)
for o in (0x300000, 0x2f8000, 0x310000, 0x320000, 0x330000, 0x103800, 0x223000, 0x23ac00, 0x250000):
    print(f"===== {o:#x} =====")
    hx(o, 144)
    print()
