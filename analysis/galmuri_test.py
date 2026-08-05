from PIL import Image, ImageFont, ImageDraw
FT = r"D:\nds\files (1)\Galmuri11.ttf"
font = ImageFont.truetype(FT, 12)

for ch in "신장왕카ㄴ군베":
    img = Image.new("L", (16, 16), 0)
    d = ImageDraw.Draw(img)
    d.text((0, 0), ch, font=font, fill=255)
    import numpy as np
    a = np.array(img) > 128
    ys, xs = np.where(a)
    print(f"--- {ch} bbox x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()} ---")
    for y in range(16):
        print("".join("#" if a[y,x] else "." for x in range(16)))
