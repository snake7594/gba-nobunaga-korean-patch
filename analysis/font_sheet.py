from PIL import Image
import sys
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

def glyph(off):
    """decode 18-byte packed 12x12"""
    bits = int.from_bytes(rom[off:off+18], "big")
    rows = []
    for y in range(12):
        rows.append((bits >> (144-12*(y+1))) & 0xFFF)
    return rows

def sheet(base, count, cols, name, scale=2, number_every=None):
    rows_n = (count+cols-1)//cols
    W = cols*13+1; H = rows_n*13+1
    img = Image.new("L", (W,H), 160)
    for i in range(count):
        off = base + i*18
        if off+18 > len(rom): break
        g = glyph(off)
        gx = (i%cols)*13+1; gy = (i//cols)*13+1
        for y in range(12):
            r = g[y]
            for x in range(12):
                img.putpixel((gx+x, gy+y), 0 if (r>>(11-x))&1 else 255)
    img = img.resize((W*scale,H*scale), Image.NEAREST)
    img.save(S+"\\"+name)
    print("saved", name, img.size)

if __name__ == "__main__":
    base = int(sys.argv[1], 16)
    count = int(sys.argv[2])
    name = sys.argv[3]
    cols = int(sys.argv[4]) if len(sys.argv)>4 else 47
    sheet(base, count, cols, name)
