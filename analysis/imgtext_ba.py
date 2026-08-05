# -*- coding: utf-8 -*-
"""이미지 라벨 한글화 전/후 비교 그림 생성 (릴리스 노트용)

팔레트는 화면마다 달라 인덱스 명암으로 그린다. 원본과 결과에 같은 규칙을
쓰므로 무엇이 어떻게 바뀌었는지 비교하기에는 충분하다.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont


def kfont(size=14):
    """제목용 한글 글꼴 — 없으면 기본 글꼴(한글이 깨짐)로 물러난다"""
    for p in (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\gulim.ttc",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths
import imgtext

GRAY = [0, 17, 34, 51, 68, 102, 119, 136, 153, 170, 187, 204, 221, 238, 247, 255]
BG = (28, 28, 44)


def draw(rom, img, off, ox, oy, w):
    tw = w//8
    for t in range(tw*2):
        tx, ty = (t % tw)*8, (t//tw)*8
        b = off + t*32
        for y in range(8):
            for x in range(0, 8, 2):
                v = rom[b + y*4 + x//2]
                for k, idx in ((0, v & 15), (1, v >> 4)):
                    if idx:
                        img.putpixel((ox+tx+x+k, oy+ty+y), (GRAY[idx],)*3)


def sheet(jp, kr, arr, cols, scale=3):
    offs = arr.get("offs") or [arr["base"] + k*arr["stride"] for k in range(arr["n"])]
    ks = sorted(arr["items"])
    w = arr["w"]
    rows = (len(ks)+cols-1)//cols
    cw, ch = w+4, 16*2+8
    img = Image.new("RGB", (cols*cw+4, rows*ch+4), BG)
    for i, k in enumerate(ks):
        ox, oy = 4+(i % cols)*cw, 4+(i//cols)*ch
        draw(jp, img, offs[k], ox, oy, w)
        draw(kr, img, offs[k], ox, oy+18, w)
    return img.resize((img.width*scale, img.height*scale), Image.NEAREST)


TITLES = {
    "cmd": ("커맨드 버튼 39개", 8),
    "stA": ("상태창 항목명 (1)", 6),
    "stB": ("상태창 항목명 (2)", 5),
    "war": ("합전 명령 16개", 8),
    "stat": ("무장 능력치 이름", 5),
    "wide": ("제목 라벨", 3),
}


def main():
    jp = paths.read_rom_jp()
    kr = open(paths.rom_kr(), "rb").read()
    parts = []
    for arr in imgtext.ARRAYS:
        t = TITLES.get(arr["key"])
        if not t:
            continue
        parts.append((t[0], sheet(jp, kr, arr, t[1])))
    pad, head = 12, 26
    f = kfont(15)
    W = max(p[1].width for p in parts) + pad*2
    Hh = sum(p[1].height + head + pad for p in parts) + pad
    out = Image.new("RGB", (W, Hh), BG)
    d = ImageDraw.Draw(out)
    y = pad
    for name, im in parts:
        d.text((pad, y), f"{name}   (위 = 원본 / 아래 = 한글)", fill=(255, 214, 110), font=f)
        y += head
        out.paste(im, (pad, y))
        y += im.height + pad
    p = os.path.join(paths.ROOT, "images", "imgtext_ba.png")
    out.save(p)
    print("saved", p, out.size)


if __name__ == "__main__":
    main()
