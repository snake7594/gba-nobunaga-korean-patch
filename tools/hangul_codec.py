# -*- coding: utf-8 -*-
"""한글 코덱: 폰트 슬롯 재활용 인코딩
- 유지 문자(기호·전각 숫자·영문·가이지): 원래 SJIS 코드 그대로
- 한글 음절: 한자/히라가나/가타카나 슬롯에 배정 (charmap.json)
- ASCII(반각)·개행: 1바이트 그대로
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import struct, json, os, re

S = os.path.dirname(os.path.abspath(__file__))
ROM_SRC = paths.rom_jp()

TB2 = 0x30d6ce
N2 = 1869
GAIJI0 = 1851

_rom = open(ROM_SRC, "rb").read()
TABLE = [struct.unpack_from("<H", _rom, TB2+i*2)[0] for i in range(N2)]

def classify(i):
    v = TABLE[i]
    if i >= GAIJI0: return "gaiji"
    b = bytes([v >> 8, v & 0xFF])
    try: ch = b.decode("cp932")
    except Exception: return "gaiji"
    o = ord(ch)
    if o in (0x30FB, 0x30FC): return "sym"   # ・ ー 는 유지(구분자 용도)
    if 0x3041 <= o <= 0x309F: return "hira"
    if 0x30A0 <= o <= 0x30FF: return "kata"
    if 0x4E00 <= o <= 0x9FFF: return "kanji"
    return "sym"

CLS = [classify(i) for i in range(N2)]
SYM_CODE = {}   # 유지 문자 -> sjis code
for i in range(N2):
    if CLS[i] == "sym":
        v = TABLE[i]
        ch = bytes([v >> 8, v & 0xFF]).decode("cp932")
        SYM_CODE[ch] = v

# 한글 배정 가능 슬롯 (한자 -> 히라 -> 가타 순)
FREE_SLOTS = [i for i in range(N2) if CLS[i] == "kanji"] + \
             [i for i in range(N2) if CLS[i] == "hira"] + \
             [i for i in range(N2) if CLS[i] == "kata"]

GAIJI_RE = re.compile(r"\{G(\d\d)\}")

# 번역가가 쓰기 쉬운 문자 -> 게임 폰트에 있는 문자로 정규화
NORMALIZE = {
    "·": "・",   # · -> ・  가운뎃점
    "‧": "・",   # ‧ -> ・
    "･": "・",   # ･ -> ・
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "–": "－", "—": "－",   # – — -> －
    "、": "、",
    " ": " ",
    "→": "→",
}

def normalize(text):
    return "".join(NORMALIZE.get(c, c) for c in text)

def build_charmap(syllables):
    """음절 목록(정렬됨) -> {syllable: slot_index}"""
    syl = sorted(set(syllables))
    if len(syl) > len(FREE_SLOTS):
        raise ValueError(f"음절 {len(syl)}개 > 슬롯 {len(FREE_SLOTS)}개")
    return {s: FREE_SLOTS[k] for k, s in enumerate(syl)}

class Codec:
    def __init__(self, charmap, halfmap=None):
        self.charmap = charmap          # syllable -> slot idx (전각)
        self.enc2 = {s: TABLE[i] for s, i in charmap.items()}
        # 반각 1바이트 음절 (고정 길이 이름 필드용). halfwidth.py 참고
        self.half = dict(halfmap or {})

    def encode(self, text):
        out = bytearray()
        text = normalize(text)
        i = 0
        while i < len(text):
            m = GAIJI_RE.match(text, i)
            if m:
                v = TABLE[GAIJI0 + int(m.group(1))]
                out += bytes([v >> 8, v & 0xFF])
                i = m.end(); continue
            ch = text[i]; i += 1
            if ch == "\n":
                out.append(0x0A); continue
            o = ord(ch)
            if o < 0x80:
                out.append(o); continue
            if ch in self.half:
                out.append(self.half[ch]); continue
            if ch in self.enc2:
                v = self.enc2[ch]
                out += bytes([v >> 8, v & 0xFF]); continue
            if ch in SYM_CODE:
                v = SYM_CODE[ch]
                out += bytes([v >> 8, v & 0xFF]); continue
            if 0xFF61 <= o <= 0xFF9F:      # 반각 가나(원본 바이너리 조각 보존용)
                out += ch.encode("cp932"); continue
            # 전각 -> 대응 시도 (cp932 인코딩 가능한 유지문자)
            try:
                b = ch.encode("cp932")
                if len(b) == 2 and ((b[0] << 8) | b[1]) in set(TABLE):
                    out += b; continue
            except Exception:
                pass
            raise KeyError(f"인코딩 불가 문자: {ch!r} in {text[:30]!r}")
        return bytes(out)

def enc_len(text, charmap_keys=None):
    """인코딩 후 바이트 길이 (charmap 없이 추정: 2바이트/전각, 1바이트/ASCII·개행)"""
    n = 0; i = 0
    while i < len(text):
        m = GAIJI_RE.match(text, i)
        if m: n += 2; i = m.end(); continue
        ch = text[i]; i += 1
        n += 1 if ord(ch) < 0x80 else 2
    return n

if __name__ == "__main__":
    from collections import Counter
    print("slots:", Counter(CLS))
    print("free slots:", len(FREE_SLOTS))
    print("sym chars:", "".join(sorted(SYM_CODE)))
