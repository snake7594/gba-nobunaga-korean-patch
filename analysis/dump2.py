from PIL import Image
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
OUT = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

def dump(off, w, h, bpr, cols, rows, name, scale=3):
    gsz = bpr*h
    W = cols*(w+1)+1; H = rows*(h+1)+1
    img = Image.new("L",(W,H),160)
    for gi in range(cols*rows):
        base = off+gi*gsz
        if base+gsz > len(data): break
        gx=(gi%cols)*(w+1)+1; gy=(gi//cols)*(h+1)+1
        for y in range(h):
            for xb in range(bpr):
                b = data[base+y*bpr+xb]
                for bit in range(8):
                    x = xb*8+bit
                    if x>=w: break
                    img.putpixel((gx+x,gy+y), 0 if (b>>(7-bit))&1 else 255)
    img = img.resize((W*scale,H*scale), Image.NEAREST)
    img.save(OUT+"\\"+name); print("saved",name,img.size)

dump(0x300000, 12,12,2, 24,16, "e_300000_12x12.png")
dump(0x2f8000, 12,12,2, 24,16, "f_2f8000_12x12.png")
dump(0x330000, 12,12,2, 24,16, "g_330000_12x12.png")
