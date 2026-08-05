import struct
from PIL import Image
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
vram = open(S+r"\vram_menu.bin","rb").read()
pram = open(S+r"\pram_menu.bin","rb").read()
io   = open(S+r"\io_menu.bin","rb").read()

dispcnt = struct.unpack_from("<H", io, 0)[0]
print(f"DISPCNT={dispcnt:04x} mode={dispcnt&7} OBJ={(dispcnt>>12)&1} win0={(dispcnt>>13)&1}")
for i in range(4):
    bgcnt = struct.unpack_from("<H", io, 8+i*2)[0]
    print(f"BG{i}CNT={bgcnt:04x} prio={bgcnt&3} char={((bgcnt>>2)&3)*0x4000:#07x} scr={((bgcnt>>8)&31)*0x800:#07x} 8bpp={(bgcnt>>7)&1} size={(bgcnt>>14)&3} on={(dispcnt>>(8+i))&1}")

def pal(idx):
    v = struct.unpack_from("<H", pram, idx*2)[0]
    return ((v&31)<<3, ((v>>5)&31)<<3, ((v>>10)&31)<<3)

def render_bg(charbase, scrbase, bpp8, size, name):
    W = 256 if size in (0,2) else 512
    H = 256 if size in (0,1) else 512
    img = Image.new("RGB", (W, H))
    px = img.load()
    for sy in range(H//8):
        for sx in range(W//8):
            # screenblock addressing
            sbx, sby = sx//32, sy//32
            sbi = (sy%32)*32 + (sx%32)
            sboff = scrbase + (sby*(W//256)+sbx)*0x800 + sbi*2
            e = struct.unpack_from("<H", vram, sboff)[0]
            tile = e & 0x3FF
            hf, vf = (e>>10)&1, (e>>11)&1
            palno = (e>>12)&15
            for y in range(8):
                for x in range(8):
                    if bpp8:
                        c = vram[charbase + tile*64 + y*8 + x]
                    else:
                        b = vram[charbase + tile*32 + y*4 + x//2]
                        c = (b >> (4*(x%2))) & 15
                        if c: c = palno*16 + c
                    xx = sx*8 + (7-x if hf else x)
                    yy = sy*8 + (7-y if vf else y)
                    px[xx, yy] = pal(c)
    img.save(S+f"\\{name}")
    print("saved", name)

for i in range(4):
    bgcnt = struct.unpack_from("<H", io, 8+i*2)[0]
    if (dispcnt>>(8+i))&1:
        render_bg(((bgcnt>>2)&3)*0x4000, ((bgcnt>>8)&31)*0x800, (bgcnt>>7)&1, (bgcnt>>14)&3, f"bg{i}_menu.png")
