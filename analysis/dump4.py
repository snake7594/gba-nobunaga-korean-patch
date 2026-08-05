from PIL import Image
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
OUT = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"

def strip(off, wbytes, height, name, scale=2):
    """render as one continuous 1bpp bitmap, wbytes per row"""
    W = wbytes*8; H = height
    img = Image.new("L",(W,H),255)
    for y in range(H):
        for xb in range(wbytes):
            i = off + y*wbytes + xb
            if i >= len(data): break
            b = data[i]
            for bit in range(8):
                img.putpixel((xb*8+bit,y), 0 if (b>>(7-bit))&1 else 255)
    img = img.resize((W*scale,H*scale),Image.NEAREST)
    img.save(OUT+"\\"+name); print("saved",name, img.size)

# treat region as continuous bitmap at several widths
strip(0x2dc000, 16, 512, "m_2dc000_w16.png")
strip(0x2dc000, 24, 512, "n_2dc000_w24.png")
strip(0x2dc000, 32, 512, "o_2dc000_w32.png")
strip(0x2dc000, 30, 512, "p_2dc000_w30.png")
