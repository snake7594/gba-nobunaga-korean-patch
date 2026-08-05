import sys
from PIL import Image
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
OUT = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

def dump(off, w, h, cols, rows, name, scale=2):
    """1bpp linear, w bits wide (padded to byte rows), h rows per glyph."""
    bpr = (w+7)//8
    gsz = bpr*h
    W = cols*(w+1)+1
    H = rows*(h+1)+1
    img = Image.new("L", (W,H), 128)
    for gi in range(cols*rows):
        base = off + gi*gsz
        if base+gsz > len(rom): break
        gx = (gi % cols)*(w+1)+1
        gy = (gi//cols)*(h+1)+1
        for y in range(h):
            for xb in range(bpr):
                b = rom[base+y*bpr+xb]
                for bit in range(8):
                    x = xb*8+bit
                    if x >= w: break
                    img.putpixel((gx+x, gy+y), 0 if (b>>(7-bit))&1 else 255)
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    p = OUT+"\\"+name
    img.save(p)
    print("saved", p, img.size)

if __name__ == "__main__":
    dump(0x2f8000, 16,16, 32, 24, "a_2f8000_16x16.png")
    dump(0x2f8000, 12,12, 32, 24, "b_2f8000_12x12.png")
    dump(0x32fc00, 16,16, 32, 24, "c_32fc00_16x16.png")
    dump(0x310000, 16,16, 32, 24, "d_310000_16x16.png")
