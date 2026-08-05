# -*- coding: utf-8 -*-
"""팔레트 없이 인덱스 명암만으로 버튼을 렌더 (PRAM 덤프 없이 글자 확인용)"""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from btn_px import btn_px, BASE, STRIDE


def render(rom, ks, cols=8, scale=3, path="build/btn_gray.png"):
    rows = (len(ks)+cols-1)//cols
    W, H = cols*34+2, rows*22+2
    img = Image.new("RGB", (W, H), (40, 40, 60))
    for n, k in enumerate(ks):
        a = btn_px(rom, k)
        ox, oy = 2+(n % cols)*34, 2+(n//cols)*22
        for y in range(16):
            for x in range(32):
                v = int(a[y, x])
                img.putpixel((ox+x, oy+y), (255, 0, 255) if v == 0 else (v*17,)*3)
    img = img.resize((W*scale, H*scale), Image.NEAREST)
    p = os.path.join(paths.BUILD, os.path.basename(path))
    img.save(p)
    print("saved", p)


if __name__ == "__main__":
    rom = paths.read_rom_jp()
    a, b = int(sys.argv[1]), int(sys.argv[2])
    render(rom, list(range(a, b)), path=sys.argv[3] if len(sys.argv) > 3 else "btn_gray.png")
