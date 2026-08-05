# -*- coding: utf-8 -*-
"""글리프 생성 — 전진폭(advance)에 맞춰 12×12 셀 비트맵을 만든다.

배경
    게임의 전각 전진폭은 코드에 12px 로 박혀 있다 (0x08003EAC: adds r6,#0xc).
    한자 독음은 1자=1음절이라 이름 폭은 그대로지만, 문장은 한국어가 길어져
    인물 열전(18칸×4줄 창)이 5~6줄로 넘쳐 잘렸다.

대책
    전진폭을 8px 로 바꾸고(1바이트 패치), 글리프를 8px 칸에 맞춘다.
    갈무리11 Condensed 는 한글 787자가 전부 잉크 폭 7px 라 8px 칸에 정확히 맞는다.

겹침이 안전한 이유
    그리기 루틴(0x08003900)은 12×12 를 불투명하게 쓴다. 8px 전진이면 각 글자의
    오른쪽 4px(여백)를 다음 글자가 덮는다. 잉크가 7px 이내면 덮이는 부분은
    항상 여백이므로 획이 지워지지 않는다. 왼쪽 정렬이 전제다.
"""
import os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from bdf import load_bdf, render12

CELL = 12                 # 글리프 셀 폭(비트)
YSHIFT = 3                # BDF baseline(ascent=14) -> 12칸에 맞추는 세로 오프셋


class GlyphMaker:
    def __init__(self, advance=8, font_name=None, rom=None):
        self.advance = advance
        if font_name is None:
            font_name = "Galmuri11-Condensed.bdf" if advance <= 8 else "Galmuri11.bdf"
        self.font_name = font_name
        self.bdf = load_bdf(paths.font(font_name))
        self.glyphs, self.fbbx, self.ascent, self.descent = self.bdf
        self.rom = rom if rom is not None else paths.read_rom_jp()
        self.align = "left" if advance < CELL else "center"

    # ---------- 기본 도구 ----------
    @staticmethod
    def ink(rows):
        l, r = CELL, -1
        for v in rows:
            for x in range(CELL):
                if (v >> (CELL-1-x)) & 1:
                    l = min(l, x); r = max(r, x)
        return l, r

    def align_rows(self, rows):
        l, r = self.ink(rows)
        if r < 0:
            return rows
        w = r - l + 1
        shift = (0 if self.align == "left" else (CELL - w)//2) - l
        if shift > 0:
            return [v >> shift for v in rows]
        if shift < 0:
            return [(v << (-shift)) & 0xFFF for v in rows]
        return rows

    def orig_rows(self, slot):
        """롬 원본 글리프"""
        off = paths.FONT_BASE + slot*18
        bits = int.from_bytes(self.rom[off:off+18], "big")
        return [(bits >> (144 - 12*(y+1))) & 0xFFF for y in range(12)]

    @staticmethod
    def squeeze8(rows):
        """12px -> 8px 가로 압축. 3열을 2열로 접되 OR 로 획을 보존한다."""
        out = []
        for v in rows:
            bits = [(v >> (CELL-1-x)) & 1 for x in range(CELL)]
            nb = []
            for g in range(4):
                a, b, c = bits[g*3], bits[g*3+1], bits[g*3+2]
                nb.append(a | b)
                nb.append(b | c)
            nv = 0
            for x in range(8):
                nv = (nv << 1) | nb[x]
            out.append(nv << 4)      # 12비트 필드 좌측에 배치
        return out

    def from_font(self, ch):
        r = render12(self.glyphs, self.ascent, ord(ch), W=CELL, H=16)
        return r[YSHIFT:YSHIFT+CELL] if r else None

    # ---------- 용도별 ----------
    def hangul(self, syl):
        rows = self.from_font(syl)
        if rows is None:
            raise KeyError(f"갈무리({self.font_name})에 없는 음절: {syl}")
        rows = self.align_rows(rows)
        l, r = self.ink(rows)
        if r >= self.advance:
            raise ValueError(f"음절 {syl} 잉크 폭 {r+1}px > 전진 {self.advance}px")
        return rows

    def symbol(self, ch, slot):
        """유지 기호·전각 숫자/영문 — 폰트에 있으면 쓰고, 없으면 원본을 압축"""
        if ch == "　":
            return [0]*CELL
        rows = self.from_font(ch)
        if rows is None:
            alt = unicodedata.normalize("NFKC", ch)     # 전각 -> 반각 대응
            if len(alt) == 1:
                rows = self.from_font(alt)
        if rows is not None:
            rows = self.align_rows(rows)
            if self.ink(rows)[1] < self.advance:
                return rows
        rows = self.squeeze8(self.orig_rows(slot))
        return rows if self.advance >= 8 else self.align_rows(rows)

    def gaiji(self, slot):
        """게임 전용 외자 — 어떤 한자인지 확정할 수 없으므로 원본을 압축해 보존"""
        if self.advance >= CELL:
            return self.orig_rows(slot)
        return self.squeeze8(self.orig_rows(slot))


def pack18(rows):
    bits = 0
    for v in rows:
        bits = (bits << 12) | (v & 0xFFF)
    return bits.to_bytes(18, "big")


# ---- 전진폭 코드 패치 ----
# 0x08003EAC: adds r6,#0xc   (전각 전진 12px)   halfword = 0x360C, imm 은 하위 바이트
ADV_PATCH_OFF = 0x3EAC
ADV_PATCH_ORIG = 0x0C


def patch_advance(rom, advance):
    """전각 전진폭을 바꾼다. rom 은 bytearray."""
    if rom[ADV_PATCH_OFF] != ADV_PATCH_ORIG:
        raise ValueError(f"{ADV_PATCH_OFF:#x} 가 예상과 다릅니다: {rom[ADV_PATCH_OFF]:#04x}")
    if not (1 <= advance <= 255):
        raise ValueError("advance 범위 오류")
    rom[ADV_PATCH_OFF] = advance
    return rom
