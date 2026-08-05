# -*- coding: utf-8 -*-
"""타이틀 로고를 한글로 교체한다.

1) 원본에서 글자 픽셀(크림+빨강외곽+그림자)을 지우고 배경을 메운다
2) '노부나가의 야망' 을 같은 스타일(크림 면 + 빨강 외곽 + 어두운 그림자)로 그린다
3) 원본 팔레트로 8bpp 인덱스화 -> 타일로 재인코딩
"""
import sys, os, struct, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
vram = open(os.path.join(S, "vram_s01_title.bin"), "rb").read()
pram = open(os.path.join(S, "pram_s01_title.bin"), "rb").read()
CHAR, SCR = 0x4000, 0xE000
PAL = []
for i in range(256):
    v = struct.unpack_from("<H", pram, i*2)[0]
    PAL.append(((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3))
PALA = np.array(PAL, dtype=np.int16)

# ---- 원본 인덱스 맵
idx = np.zeros((160, 240), dtype=np.uint8)
grid = np.zeros((20, 30), dtype=np.int16)
for sy in range(20):
    for sx in range(30):
        e = struct.unpack_from("<H", vram, SCR + (sy*32+sx)*2)[0]
        t = e & 0x3FF
        grid[sy, sx] = t
        blk = np.frombuffer(vram[CHAR+t*64:CHAR+t*64+64], dtype=np.uint8).reshape(8, 8)
        idx[sy*8:sy*8+8, sx*8:sx*8+8] = blk

CREAM = [45, 65, 64, 89, 88, 92, 90, 93, 86, 94, 87, 85, 91]
RED = 10
# 글자 = 밝은 크림 면 + 채도 높은 빨강 외곽.
# 팔레트 인덱스만으로는 어두운 외곽선을 놓쳐 획이 남으므로 RGB 조건도 함께 쓴다.
pr = PALA[idx]
saturated_red = (pr[:, :, 0] >= 150) & (pr[:, :, 1] <= 80) & (pr[:, :, 2] <= 80)
bright = pr.sum(2) >= 470
mask = np.isin(idx, CREAM) | (idx == RED) | saturated_red | bright
# 글자 영역 밖(불꽃 배경)은 건드리지 않도록 bbox 로 제한
BB = (10, 28, 232, 102)
lim = np.zeros_like(mask)
lim[BB[1]:BB[3], BB[0]:BB[2]] = True
mask &= lim
# 외곽 그림자까지 포함하도록 팽창
m = Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
mask2 = (np.array(m) > 0) & lim

# ---- 배경 복원: 마스크 영역을 주변 배경에서 채워 넣기(반복 확산)
rgb = PALA[idx].astype(np.float32)
fill = rgb.copy()
mk = mask2.copy()
for _ in range(60):
    if not mk.any():
        break
    src = fill.copy()
    src[mk] = np.nan
    acc = np.zeros_like(fill)
    cnt = np.zeros(fill.shape[:2], dtype=np.float32)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        sh = np.roll(np.roll(src, dy, 0), dx, 1)
        ok = ~np.isnan(sh[:, :, 0])
        acc[ok] += sh[ok]
        cnt += ok
    newpx = np.zeros_like(fill)
    good = (cnt > 0) & mk
    newpx[good] = acc[good] / cnt[good, None]
    fill[good] = newpx[good]
    mk = mk & ~good
bg = Image.fromarray(fill.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
bg.resize((720, 480), Image.NEAREST).save(os.path.join(paths.BUILD, "logo_bg.png"))

# ---- 한글 로고 렌더
# 원문 信長の野望 은 5자 205px = 자당 약 41px.
# 한글 7자를 한 줄에 넣으면 자당 29px 로 작아지므로, 두 줄로 나눠 글자 크기를 지킨다.
LINES = ["노부나가의", "야망"]
BOX = (17, 35, 221, 93)          # 원본 글자 bbox
bw, bh = BOX[2]-BOX[0]+1, BOX[3]-BOX[1]+1
FONTS = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\HMKMMAG.TTF",
         r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\batang.ttc"]
fp = next(f for f in FONTS if os.path.exists(f))
print("font:", fp)

SS = 4
GAP = 2                              # 줄 간격(원본 해상도 기준)
best = None
for size in range(12, 60):
    f = ImageFont.truetype(fp, size*SS)
    bbs = [f.getbbox(s) for s in LINES]
    wmax = max(b[2]-b[0] for b in bbs)
    htot = sum(b[3]-b[1] for b in bbs) + GAP*SS*(len(LINES)-1)
    if wmax <= bw*SS and htot <= bh*SS:
        best = (size, f, bbs, wmax, htot)
    else:
        break
size, font, bbs, wmax, htot = best
print(f"글자 크기 {size}px -> {wmax//SS}x{htot//SS} (박스 {bw}x{bh})")

lay = Image.new("L", (bw*SS, bh*SS), 0)
d = ImageDraw.Draw(lay)
y = (bh*SS - htot)//2
for s, b in zip(LINES, bbs):
    w = b[2]-b[0]
    d.text(((bw*SS-w)//2 - b[0], y - b[1]), s, font=font, fill=255)
    y += (b[3]-b[1]) + GAP*SS
core = lay.resize((bw, bh), Image.LANCZOS)
core_a = np.array(core).astype(np.float32)/255.0

def grow(a, px):
    im = Image.fromarray((a*255).astype(np.uint8))
    for _ in range(px):
        im = im.filter(ImageFilter.MaxFilter(3))
    return np.array(im).astype(np.float32)/255.0

outline = grow(core_a, 2)
shadow = grow(core_a, 3)

out = np.array(bg).astype(np.float32)
sub = out[BOX[1]:BOX[1]+bh, BOX[0]:BOX[0]+bw]
SHADOW_C = np.array([24, 8, 0], dtype=np.float32)
RED_C = np.array(PAL[RED], dtype=np.float32)
CREAM_C = np.array([248, 248, 192], dtype=np.float32)

# 그림자(우하 오프셋) -> 빨강 외곽 -> 크림 면
sh = np.zeros_like(shadow)
sh[3:, 3:] = shadow[:-3, :-3]
sub = sub*(1-sh[..., None]) + SHADOW_C*sh[..., None]
sub = sub*(1-outline[..., None]) + RED_C*outline[..., None]
sub = sub*(1-core_a[..., None]) + CREAM_C*core_a[..., None]
out[BOX[1]:BOX[1]+bh, BOX[0]:BOX[0]+bw] = sub

newimg = Image.fromarray(out.astype(np.uint8))
newimg.resize((720, 480), Image.NEAREST).save(os.path.join(paths.BUILD, "logo_ko.png"))
print("saved build/logo_bg.png, build/logo_ko.png")

# ---- 팔레트 인덱스화
flat = np.array(newimg).reshape(-1, 3).astype(np.int32)
palm = PALA.astype(np.int32)
dist = ((flat[:, None, :] - palm[None, :, :])**2).sum(2)
newidx = dist.argmin(1).astype(np.uint8).reshape(160, 240)
json.dump({"idx": newidx.tolist(), "grid": grid.tolist()},
          open(os.path.join(paths.BUILD, "logo_new.json"), "w"))
print("saved build/logo_new.json")
