# -*- coding: utf-8 -*-
"""타이틀 로고를 추출한다.

BG0 = 8bpp, char base 0x4000 (ROM 0x08002C), screen base 0xE000.
타일맵을 읽어 화면상의 각 칸이 어떤 타일인지 알아내고,
로고 영역의 타일 목록과 ROM 오프셋을 구한다.
"""
import sys, os, struct, json
from PIL import Image
sys.path.insert(0, r"D:\gba\NOBU2\gba-nobunaga-korean-patch\tools")
import paths

S = os.path.dirname(os.path.abspath(__file__))
tag = sys.argv[1] if len(sys.argv) > 1 else "s01_title"
vram = open(os.path.join(S, f"vram_{tag}.bin"), "rb").read()
pram = open(os.path.join(S, f"pram_{tag}.bin"), "rb").read()
rom = paths.read_rom_jp()

CHAR, SCR = 0x4000, 0xE000
ROM_CHAR = 0x08002C          # VRAM 0x4000 의 ROM 원본


def col(i):
    v = struct.unpack_from("<H", pram, i*2)[0]
    return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)


# 화면 30x20 칸의 타일 인덱스
grid = []
for sy in range(20):
    row = []
    for sx in range(30):
        e = struct.unpack_from("<H", vram, SCR + (sy*32+sx)*2)[0]
        row.append(e & 0x3FF)
    grid.append(row)

# 로고 영역(대략 y=3..13, x=1..29) 렌더
img = Image.new("RGB", (240, 160))
px = img.load()
for sy in range(20):
    for sx in range(30):
        t = grid[sy][sx]
        for y in range(8):
            for x in range(8):
                c = vram[CHAR + t*64 + y*8 + x]
                px[sx*8+x, sy*8+y] = col(c)
img.resize((720, 480), Image.NEAREST).save(os.path.join(paths.BUILD, "logo_full.png"))

# 타일 사용 통계
used = {}
for sy in range(20):
    for sx in range(30):
        used.setdefault(grid[sy][sx], []).append((sx, sy))
print(f"화면에 쓰인 고유 타일 {len(used)}개, 최대 인덱스 {max(used)}")
print(f"ROM 범위: {ROM_CHAR:#x} ~ {ROM_CHAR + (max(used)+1)*64:#x}")

# 중복 사용(여러 칸에서 쓰는) 타일 = 배경 패턴, 단독 사용 = 로고 획
multi = {t: v for t, v in used.items() if len(v) > 1}
print(f"여러 칸에서 재사용되는 타일 {len(multi)}개")

json.dump({"grid": grid, "rom_char": ROM_CHAR}, open(os.path.join(paths.BUILD, "logo_map.json"), "w"))
print("saved build/logo_full.png, build/logo_map.json")
