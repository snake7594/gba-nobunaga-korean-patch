from PIL import Image
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
OUT = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

def dump1(off, w, h, bpr, cols, rows, name, scale=3):
    gsz = bpr*h
    W=cols*(w+1)+1; H=rows*(h+1)+1
    img=Image.new("L",(W,H),160)
    for gi in range(cols*rows):
        base=off+gi*gsz
        if base+gsz>len(data): break
        gx=(gi%cols)*(w+1)+1; gy=(gi//cols)*(h+1)+1
        for y in range(h):
            for xb in range(bpr):
                b=data[base+y*bpr+xb]
                for bit in range(8):
                    x=xb*8+bit
                    if x>=w: break
                    img.putpixel((gx+x,gy+y),0 if (b>>(7-bit))&1 else 255)
    img=img.resize((W*scale,H*scale),Image.NEAREST)
    img.save(OUT+"\\"+name); print("saved",name)

def dump2bpp(off, w, h, cols, rows, name, scale=3):
    # GBA 4bpp tile? try 2bpp packed rows
    bpr = w//4  # 2 bits per px
    gsz = bpr*h
    W=cols*(w+1)+1; H=rows*(h+1)+1
    img=Image.new("L",(W,H),160)
    pal=[255,170,85,0]
    for gi in range(cols*rows):
        base=off+gi*gsz
        if base+gsz>len(data): break
        gx=(gi%cols)*(w+1)+1; gy=(gi//cols)*(h+1)+1
        for y in range(h):
            for x in range(w):
                b=data[base+y*bpr+x//4]
                v=(b>>(6-2*(x%4)))&3
                img.putpixel((gx+x,gy+y),pal[v])
    img=img.resize((W*scale,H*scale),Image.NEAREST)
    img.save(OUT+"\\"+name); print("saved",name)

dump1(0x2dc000, 16,16,2, 24,16, "h_2dc000_16x16.png")
dump1(0x2dc000, 12,12,2, 24,16, "i_2dc000_12x12.png")
dump2bpp(0x2dc000, 16,16, 24,16, "j_2dc000_2bpp16.png")
dump2bpp(0x2dc000, 12,12, 24,16, "k_2dc000_2bpp12.png")
