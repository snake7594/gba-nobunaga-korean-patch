# -*- coding: utf-8 -*-
"""최종 샘플 시트: 원문 일본어를 키로 찾아 현재 유효 주소를 추적해 렌더"""
import struct, json, os, sys
from PIL import Image, ImageDraw

S = os.path.dirname(os.path.abspath(__file__))
NEW = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Korean).gba", "rb").read()
FONT2 = 0x305274; ASCII_F = 0x304df4
TB2 = 0x30d6ce; N2 = 1869
table = [struct.unpack_from("<H", NEW, TB2+i*2)[0] for i in range(N2)]
idx_of = {v: i for i, v in enumerate(table)}
es = json.load(open(S+r"\master_strings.json", encoding="utf-8"))
by_jp = {}
for e in es:
    by_jp.setdefault(e["jp"], e)

def cur_addr(e):
    if e["refs"]:
        v = struct.unpack_from("<I", NEW, e["refs"][0])[0]
        if 0x08000000 <= v < 0x08400000: return v - 0x08000000
    return e["off"]

def tokens(off, maxb=4096):
    lines = [[]]; i = off
    while i < len(NEW) and NEW[i] != 0 and i - off < maxb:
        b = NEW[i]
        if b == 0x0A: lines.append([]); i += 1; continue
        if b < 0x80: lines[-1].append(("a", b)); i += 1; continue
        if 0xA1 <= b <= 0xDF: lines[-1].append(("a", 0x3F)); i += 1; continue
        v = (b << 8) | NEW[i+1]
        lines[-1].append(("g", idx_of.get(v))); i += 2
    return lines

WANT = [
 "入門モード", "実力モード", "デモモード", "どのモードにしますか？",
 "どの大名を担当しますか", "本能寺の変", "信長包囲網", "戦国の動乱",
 "何を行いますか", "何をご覧になりますか", "兵糧", "武将", "調略", "外交",
 "上書きします", "ロードします", "データがありません",
 "%s%sが%s領%sへ攻め込みました", "%s%sが寝返りました",
 "%s%sが持っていた茶器を手に入れました",
 "余勢を駆って撃ていっ！！", "はずしましたぞ", "むう…  不覚",
 "御意", "兵に施しますか？", "国一番の果報者にござる",
]

rows = []
for jp in WANT:
    e = by_jp.get(jp)
    if not e: rows.append(None); continue
    rows.extend(tokens(cur_addr(e)))

W = max((sum(7 if k == "a" else 13 for k, _ in ln) for ln in rows if ln), default=40) + 8
H = len(rows)*15 + 8
img = Image.new("L", (W, H), 255)
y = 4
for ln in rows:
    if ln is None: y += 15; continue
    x = 4
    for kind, v in ln:
        if kind == "a":
            if 0x20 <= v < 0x80:
                ao = ASCII_F + (v - 0x20)*12
                for yy in range(12):
                    bb = NEW[ao+yy]
                    for xx in range(8):
                        if (bb >> (7-xx)) & 1: img.putpixel((x+xx, y+yy), 0)
            x += 7; continue
        if v is None: x += 13; continue
        o = FONT2 + v*18
        bits = int.from_bytes(NEW[o:o+18], "big")
        for yy in range(12):
            r = (bits >> (144-12*(yy+1))) & 0xFFF
            for xx in range(12):
                if (r >> (11-xx)) & 1: img.putpixel((x+xx, y+yy), 0)
        x += 13
    y += 15
img = img.resize((W*3, H*3), Image.NEAREST)
img.save(S+r"\sample_korean.png")
print("saved sample_korean.png", img.size)
