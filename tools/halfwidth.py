# -*- coding: utf-8 -*-
"""반각(1바이트) 한글 — 고정 길이 이름 필드에 일본어 읽기를 넣기 위한 장치.

왜 필요한가
    무장 레코드(스트라이드 44)의 성·이름 필드는 각 7바이트로, NUL 을 빼면
    전각 3음절이 한계다. `노부나가`(4음절=8바이트)가 들어가지 않는다.
    레코드를 넓히려면 ×44 계산 298곳을 모두 고쳐야 해 위험하다.

어떻게 푸는가
    게임에는 1바이트 문자를 8px 전진으로 그리는 반각 경로가 이미 있다
    (드로잉 루프 0x08003E6C 의 else 가지, 폰트 0x304DF4, 글리프 12바이트=8×12).
    실제 텍스트가 쓰지 않는 ASCII 코드 50칸에 한글 음절을 넣으면
    1음절=1바이트가 되어 `노부나가`가 4바이트로 들어간다.
    전각 전진폭도 이미 8px 이므로 시각적으로 이어 붙어도 어색하지 않다.

주의
    여기 배정하는 코드는 '실제 게임 텍스트에 등장하지 않는' 것만 골라야 한다.
    (tools/halfwidth.py 의 FREE_CODES 는 ascii 사용 실측 결과)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

ASCII_FONT = 0x304DF4      # 8×12, 글리프 12바이트 (1바이트=1행, MSB=왼쪽)
ASCII_GLYPHS = 96          # 코드 0x20~0x7F
GLYPH_BYTES = 12


def glyph_off(code):
    if not (0x20 <= code <= 0x7F):
        raise ValueError(f"반각 폰트 범위 밖: {code:#x}")
    return ASCII_FONT + (code - 0x20) * GLYPH_BYTES


# 실제 게임 텍스트(원문+번역)가 쓰지 않는 1바이트 코드.
# tools/ 의 조사 스크립트로 실측한 값이며, 번역을 크게 고치면 다시 확인해야 한다.
FREE_CODES = [
    0x23, 0x24, 0x26, 0x2A, 0x3B, 0x3C, 0x3D, 0x3E, 0x42, 0x46,
    0x47, 0x48, 0x49, 0x4A, 0x4D, 0x4F, 0x51, 0x56, 0x57, 0x58,
    0x59, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63,
    0x65, 0x67, 0x68, 0x69, 0x6C, 0x6D, 0x6F, 0x70, 0x71, 0x72,
    0x74, 0x75, 0x76, 0x78, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7F,
]


def build_map(syllables):
    """음절 목록(빈도순) -> {음절: 1바이트 코드}"""
    if len(syllables) > len(FREE_CODES):
        syllables = syllables[:len(FREE_CODES)]
    return {s: c for s, c in zip(syllables, FREE_CODES)}


def to_ascii_glyph(rows12):
    """12비트 폭 글리프 행 -> 반각 폰트용 1바이트/행 (왼쪽 8비트)"""
    out = bytearray()
    for v in rows12:
        out.append((v >> 4) & 0xFF)     # 12비트 중 상위 8비트 = 왼쪽 8px
    return bytes(out)


def write_font(rom, halfmap, glyphmaker):
    """반각 슬롯에 한글 글리프를 기록. 잉크가 8px 를 넘으면 예외."""
    n = 0
    for syl, code in halfmap.items():
        rows = glyphmaker.hangul(syl)          # Condensed, 왼쪽 정렬, 잉크 7px
        l, r = glyphmaker.ink(rows)
        if r >= 8:
            raise ValueError(f"음절 {syl} 잉크 폭 {r+1}px > 8px (반각 불가)")
        off = glyph_off(code)
        rom[off:off + GLYPH_BYTES] = to_ascii_glyph(rows)
        n += 1
    return n
