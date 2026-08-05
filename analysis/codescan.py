import struct
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
CODE_END = 0x62000

# Thumb: movs rX,#imm = 0b00100xxx iiiiiiii -> byte0=imm byte1=0x20|reg
# muls  = 0x4340 | (rm<<3) | rd  -> byte1=0x43, byte0=0x40..0x7F
def scan_mul_const(consts):
    hits = []
    for i in range(0, CODE_END-2, 2):
        b0, b1 = data[i], data[i+1]
        if b0 in consts and 0x20 <= b1 <= 0x27:  # movs r0-r7,#const
            # look for muls within next 12 bytes
            for j in range(i+2, min(i+14, CODE_END), 2):
                c0, c1 = data[j], data[j+1]
                if c1 == 0x43 and 0x40 <= c0 <= 0x7F:
                    hits.append((i, b0, b1&7, j))
                    break
    return hits

for label, consts in [("x94/x188", {0x5E, 0xBC}), ("x0xC0", {0xC0}), ("x18/x24/x32/x36 glyphsize", {0x12,0x18,0x20,0x24,0x1A})]:
    hits = scan_mul_const(consts)
    print(f"=== {label}: {len(hits)} hits ===")
    for i, c, r, j in hits[:20]:
        print(f"  {i:#07x}: movs r{r},#{c:#x} ... muls @{j:#x}")

# Also: SJIS lead-byte range checks: cmp rX,#0x81 (0x2881|reg<<8): byte0=0x81 byte1=0x28..0x2f
print("\n=== cmp rX,#0x81 / #0x9F / #0xE0 clusters ===")
marks = []
for i in range(0, CODE_END-2, 2):
    b0, b1 = data[i], data[i+1]
    if 0x28 <= b1 <= 0x2F and b0 in (0x81, 0x9F, 0xA0, 0xE0, 0xFC, 0x7F, 0x40):
        marks.append((i, b0, b1&7))
# cluster: >=3 marks within 64 bytes
cl = []
for k in range(len(marks)):
    near = [m for m in marks if abs(m[0]-marks[k][0]) <= 64]
    vals = {m[1] for m in near}
    if len(near) >= 3 and 0x81 in vals and (0x40 in vals or 0x7F in vals or 0xFC in vals or 0x9F in vals):
        cl.append(marks[k][0])
# dedupe clusters
out=[]
for a in cl:
    if not out or a-out[-1] > 64: out.append(a)
for a in out:
    print(f"  cluster near {a:#07x}")
