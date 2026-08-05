rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

# SJIS codes for あいうえお
seqs = {
 "LE hira": bytes.fromhex("a082a282a482a682a882"),
 "BE hira": bytes.fromhex("82a082a282a482a682a8"),
 "LE kata": bytes.fromhex("a183a283a383a483a583"),  # ァアィイゥ
 "BE kata": bytes.fromhex("83a183a283a383a483a5"),
}
for label, s in seqs.items():
    hits = []
    i = rom.find(s)
    while i >= 0 and len(hits) < 10:
        hits.append(hex(i)); i = rom.find(s, i+1)
    print(label, hits)

# pointers to the font region (0x08300000-0x08310000)
import struct
cnt = {}
for off in range(0, 0x33a200, 4):
    v = struct.unpack_from("<I", rom, off)[0]
    if 0x08300000 <= v <= 0x08310000:
        cnt.setdefault(v, []).append(off)
print("\npointers into 0x0830xxxx:")
for v in sorted(cnt):
    if len(cnt[v]) >= 1:
        print(f"  {v:#x} <- {[hex(o) for o in cnt[v][:6]]}")
