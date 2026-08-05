# -*- coding: utf-8 -*-
"""build/ 의 패치 롬으로 xdelta 패치를 만든다.

xdelta3 실행파일이 있으면 그것을 쓰고, 없으면 순수 파이썬으로
VCDIFF(RFC 3284) 패치를 직접 생성한다. 두 경우 모두 xdelta3 / xdeltaUI 로 적용 가능하다.
"""
import os, sys, shutil, subprocess, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths

OUT = os.path.join(paths.PATCH_DIR, "Nobunaga_Korean.xdelta")


def with_xdelta3(exe, src, dst, out):
    cmd = [exe, "-e", "-9", "-f", "-s", src, dst, out]
    subprocess.run(cmd, check=True)
    return True


# ---------------- 순수 파이썬 VCDIFF 인코더 ----------------
# xdelta3 가 없는 환경에서도 패치를 만들 수 있도록 최소 구현.
# 소스 전체를 하나의 윈도우로 두고 COPY/ADD 명령만 사용한다.

def _varint(n):
    """VCDIFF integer (big-endian base-128, 마지막 바이트만 최상위 비트 0)"""
    if n == 0:
        return b"\x00"
    parts = []
    while n:
        parts.append(n & 0x7F)
        n >>= 7
    parts.reverse()
    return bytes([p | 0x80 for p in parts[:-1]] + [parts[-1]])


def _diff_runs(src, dst, minmatch=16):
    """dst 를 (COPY from src) / (ADD literal) 구간으로 쪼갠다."""
    index = {}
    B = minmatch
    for i in range(0, len(src) - B + 1):
        index.setdefault(src[i:i+B], i)

    ops = []            # ("copy", src_off, size) | ("add", bytes)
    lit = bytearray()
    i = 0
    n = len(dst)
    while i < n:
        key = bytes(dst[i:i+B])
        j = index.get(key) if len(key) == B else None
        if j is None:
            lit.append(dst[i]); i += 1; continue
        # 최대한 늘린다
        ln = B
        while (i + ln < n and j + ln < len(src) and dst[i+ln] == src[j+ln]):
            ln += 1
        if lit:
            ops.append(("add", bytes(lit))); lit = bytearray()
        ops.append(("copy", j, ln))
        i += ln
    if lit:
        ops.append(("add", bytes(lit)))
    return ops


def pure_python_vcdiff(src_path, dst_path, out_path):
    src = open(src_path, "rb").read()
    dst = open(dst_path, "rb").read()
    ops = _diff_runs(src, dst)

    inst = bytearray()
    data = bytearray()
    addr = bytearray()
    # 코드 테이블: 기본 테이블에서 ADD(size 0 -> 가변) = 1, COPY(mode 0, size 0) = 19
    for op in ops:
        if op[0] == "add":
            payload = op[1]
            inst.append(1); inst += _varint(len(payload))
            data += payload
        else:
            _, soff, size = op
            inst.append(19); inst += _varint(size)
            addr += _varint(soff)          # mode 0 = VCD_SELF, 절대 주소

    win = bytearray()
    win.append(0x01)                        # Win_Indicator = VCD_SOURCE
    win += _varint(len(src))                # 소스 세그먼트 길이
    win += _varint(0)                       # 소스 세그먼트 시작
    delta_body = _varint(len(dst)) + b"\x00" + _varint(len(data)) + _varint(len(inst)) + _varint(len(addr))
    delta = delta_body + bytes(data) + bytes(inst) + bytes(addr)
    win += _varint(len(delta))
    win += delta

    hdr = b"\xD6\xC3\xC4\x00\x00"           # VCDIFF magic + version + no hdr indicator
    open(out_path, "wb").write(hdr + bytes(win))


def main():
    src = paths.rom_jp()
    dst = paths.rom_kr()
    if not os.path.exists(dst):
        paths._die(f"패치 롬이 없습니다: {dst}\n  먼저 `python tools/inject.py` 를 실행하세요.")
    os.makedirs(paths.PATCH_DIR, exist_ok=True)

    exe = shutil.which("xdelta3") or shutil.which("xdelta")
    if exe:
        print("xdelta3 사용:", exe)
        with_xdelta3(exe, src, dst, OUT)
    else:
        print("xdelta3 를 찾지 못해 내장 인코더로 생성합니다 (적용 호환됨)")
        pure_python_vcdiff(src, dst, OUT)

    print("생성:", OUT, os.path.getsize(OUT), "bytes")
    print("원본 MD5 :", paths.md5(src))
    print("패치본 MD5:", paths.md5(dst))


if __name__ == "__main__":
    main()
