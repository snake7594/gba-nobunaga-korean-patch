# -*- coding: utf-8 -*-
import sys, os
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths
rom = paths.read_rom_jp()
GRAY = [255, 210, 170, 130, 100, 75, 55, 35, 20, 8, 0, 45, 65, 85, 115, 150]

off = int(sys.argv[1], 16); n = int(sys.argv[2]); cols = int(sys.argv[3])
sc = int(sys.argv[4]) if len(sys.argv) > 4 else 6
nm = sys.argv[5] if len(sys.argv) > 5 else "zoom.png"
rows = (n+cols-1)//cols
img = Image.new("L", (cols*8, rows*8), 128); px = img.load()
for t in range(n):
    b = off+t*32
    if b+32 > len(rom): break
    tx, ty = (t % cols)*8, (t//cols)*8
    for y in range(8):
        for x in range(0, 8, 2):
            v = rom[b+y*4+x//2]
            px[tx+x, ty+y] = GRAY[v & 15]; px[tx+x+1, ty+y] = GRAY[v >> 4]
img = img.resize((img.width*sc, img.height*sc), Image.NEAREST)
img.save(os.path.join(paths.BUILD, nm)); print(os.path.join(paths.BUILD, nm))
