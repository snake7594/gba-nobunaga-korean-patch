# -*- coding: utf-8 -*-
"""이름 폭 전/후 비교 그림 — 명판 안쪽 64px 에 이름이 들어가는지 보여준다

예전 규칙(성 뒤 공백을 늘 유지)과 새 규칙(64px 를 넘으면 공백 제거)을 같은
전진폭 8px 로 그려 비교한다. 전진 7px 는 갈무리 Condensed 잉크가 7px 라
글자 사이 여백이 0이 되어 붙어 보이므로 쓰지 않는다.
"""
import os, sys, json, io
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths
from bdf import load_bdf, render12

PLATE = 64                      # 명판 안쪽 폭(px)
ADV = 8                         # 문자 전진폭(px)
SAMPLES = ["오다 노부나가", "다케다 신겐", "우에스기 겐신", "도쿠가와 이에야스",
           "이나와시로 모리쿠니", "사이토 도산", "모리 모토나리"]


def kfont(size=14):
    for p in (r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\gulim.ttc",
              "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def rows_of(glyphs, ascent, ch):
    r = render12(glyphs, ascent, ord(ch), W=12, H=16)
    return r[3:15] if r else [0]*12


def strip(text, adv, glyphs, ascent, scale=3):
    """전진폭 adv 로 이어 그린 이름 띠 + 명판 경계선"""
    w = max(PLATE + 24, len(text)*adv + 8)
    img = Image.new("RGB", (w, 16), (26, 26, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, PLATE-1, 15], fill=(40, 40, 130))
    x = 0
    for ch in text:
        if ch != " ":
            for y, v in enumerate(rows_of(glyphs, ascent, ch)):
                for k in range(12):
                    if (v >> (11-k)) & 1 and 0 <= x+k < w:
                        img.putpixel((x+k, y+2),
                                     (255, 255, 255) if x+k < PLATE else (255, 120, 120))
        x += adv
    return img.resize((w*scale, 16*scale), Image.NEAREST)


def main():
    reg = load_bdf(paths.font("Galmuri11.bdf"))
    con = load_bdf(paths.font("Galmuri11-Condensed.bdf"))
    f = kfont(14)
    rowh = 16*3 + 6
    out = Image.new("RGB", (760, 40 + len(SAMPLES)*(rowh*2 + 18)), (28, 28, 44))
    d = ImageDraw.Draw(out)
    d.text((12, 10), "파란 칸 = 명판 안쪽 64px · 빨간 획 = 잘려서 안 보이는 부분",
           fill=(255, 214, 110), font=f)
    y = 38
    for t in SAMPLES:
        short = t if len(t)*ADV <= PLATE else t.replace(" ", "")
        a = strip(t, ADV, con[0], con[2])
        b = strip(short, ADV, con[0], con[2])
        d.text((12, y), f"이전 : {t}", fill=(220, 220, 220), font=f)
        out.paste(a, (300, y-2))
        y += rowh
        d.text((12, y), f"이후 : {short}", fill=(150, 230, 150), font=f)
        out.paste(b, (300, y-2))
        y += rowh + 18
    p = os.path.join(paths.ROOT, "images", "name_ba.png")
    out.save(p)
    print("saved", p, out.size)


if __name__ == "__main__":
    main()
