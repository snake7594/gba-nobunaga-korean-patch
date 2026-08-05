# -*- coding: utf-8 -*-
"""ROM 내 0x08xxxxxx 포인터 중 SJIS 문자열 시작을 가리키는 것 전수 조사"""
import struct, json
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
LIMIT = 0x33a200

TB2 = 0x30d6ce; N2 = 1869
valid2 = set(struct.unpack_from("<H", rom, TB2+i*2)[0] for i in range(N2))

def read_str(off, maxlen=2048):
    """null 종단 SJIS 문자열 읽기. (text, bytelen) 또는 None"""
    out = []
    i = off
    while i < LIMIT:
        b = rom[i]
        if b == 0:
            break
        if b < 0x80:
            # ASCII / 제어코드(%s 등)
            if 0x20 <= b < 0x7F or b in (0x0A, 0x0D):
                out.append(chr(b)); i += 1; continue
            return None
        if 0xA1 <= b <= 0xDF:
            # 반각 가나
            out.append(bytes([b]).decode("cp932")); i += 1; continue
        v = (b << 8) | rom[i+1]
        if v in valid2:
            try:
                out.append(bytes(rom[i:i+2]).decode("cp932"))
            except Exception:
                return None
            i += 2; continue
        return None
    if i - off < 2 or i - off > maxlen:
        return None
    txt = "".join(out)
    # 실제 텍스트다운지: 2바이트 문자 1개 이상
    if not any(ord(c) > 0x3000 for c in txt):
        return None
    return txt, i - off

# 모든 4바이트 정렬 포인터 후보
ptr_hits = {}
for off in range(0, LIMIT-3, 4):
    v = struct.unpack_from("<I", rom, off)[0]
    if 0x08000000 <= v < 0x08000000 + LIMIT:
        tgt = v - 0x08000000
        r = read_str(tgt)
        if r:
            ptr_hits.setdefault(tgt, []).append(off)

print("unique string targets referenced by pointers:", len(ptr_hits))
tot = 0
out = []
for tgt in sorted(ptr_hits):
    r = read_str(tgt)
    txt, blen = r
    out.append({"off": tgt, "len": blen, "refs": ptr_hits[tgt], "text": txt})
    tot += blen
print("total pointer-referenced text bytes:", tot)

from collections import Counter
c = Counter(o["off"] >> 16 for o in out)
for k in sorted(c):
    print(f"  0x{k:03x}xxxx: {c[k]} strings")

json.dump(out, open(S+r"\ptr_strings.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved ptr_strings.json")
for o in out[:10]:
    print(hex(o["off"]), o["len"], len(o["refs"]), repr(o["text"][:30]))
