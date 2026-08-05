# -*- coding: utf-8 -*-
"""저장소 경로 해석 — 모든 도구가 이 모듈을 통해 파일 위치를 얻는다.

디렉터리 규약
    <repo>/rom/     원본 롬을 두는 곳 (저장소에는 포함되지 않음)
    <repo>/data/    저장소에 커밋된 기준 데이터 (번역·문자열DB·용어집 등)
    <repo>/font/    갈무리11 BDF
    <repo>/build/   실행 중 생성되는 산출물 (패치 롬 포함)

읽기 규칙
    inp(name) 은 build/ 에 같은 이름이 있으면 그것을, 없으면 data/ 를 읽는다.
    → 파이프라인을 처음부터 다시 돌리면 build/ 의 새 산출물이 자동으로 쓰이고,
      inject.py 만 돌리면 커밋된 data/ 가 그대로 쓰인다.

원본 롬 위치 (아래 순서로 탐색)
    1. 환경변수 NOBU2_ROM
    2. <repo>/rom/ 안의 .gba 파일 중 MD5가 일치하는 것
    3. <repo>/rom/ 안의 .gba 파일이 하나뿐이면 그것 (MD5 경고만 출력)
"""
import os, sys, glob, hashlib

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "data")
FONT_DIR = os.path.join(ROOT, "font")
BUILD = os.path.join(ROOT, "build")
PATCH_DIR = os.path.join(ROOT, "patch")
ROM_DIR = os.path.join(ROOT, "rom")

MD5_JP = "2d1ceffbc8c34e3101ab91ea49f43a44"
MD5_KR = "210ff917c0a5ae3b249e0adb2be24bad"

# 롬 내부 주소 (docs/ROM구조.md 참고)
FONT_BASE = 0x305274      # 12x12 폰트, 글리프당 18바이트
TABLE_BASE = 0x30D6CE     # u16 LE SJIS 오름차순 매핑 테이블
TABLE_N = 1869            # 테이블 엔트리 수
GAIJI0 = 1851             # 가이지 시작 인덱스
DATA_END = 0x33A200       # 원본 유효 데이터 끝
FREE_BASE = 0x33A1A0      # 재배치용 여유 공간 시작
ROM_SIZE = 0x400000


def _ensure(d):
    os.makedirs(d, exist_ok=True)
    return d


def data(name):
    """커밋된 기준 데이터 경로"""
    return os.path.join(DATA, name)


def out(name):
    """생성 산출물 경로 (build/)"""
    _ensure(BUILD)
    return os.path.join(BUILD, name)


def inp(name):
    """읽기 경로 — build/ 우선, 없으면 data/"""
    b = os.path.join(BUILD, name)
    return b if os.path.exists(b) else os.path.join(DATA, name)


def font(name="Galmuri11.bdf"):
    return os.path.join(FONT_DIR, name)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _die(msg):
    sys.stderr.write("\n[오류] " + msg + "\n")
    sys.exit(1)


def rom_jp():
    """원본 일본판 롬 경로를 찾아 반환"""
    env = os.environ.get("NOBU2_ROM")
    if env:
        if not os.path.exists(env):
            _die(f"환경변수 NOBU2_ROM 이 가리키는 파일이 없습니다: {env}")
        return env

    cands = sorted(glob.glob(os.path.join(ROM_DIR, "*.gba")))
    if not cands:
        _die(
            "원본 롬을 찾을 수 없습니다.\n"
            f"  방법 1) 원본 롬을 이 폴더에 두세요: {ROM_DIR}\n"
            "  방법 2) 환경변수로 지정하세요:\n"
            '           Windows : set NOBU2_ROM=C:\\path\\to\\Nobunaga no Yabou (Japan).gba\n'
            '           mac/Linux: export NOBU2_ROM="/path/to/Nobunaga no Yabou (Japan).gba"\n'
            f"  필요한 롬 MD5 = {MD5_JP}"
        )
    for c in cands:
        if md5(c) == MD5_JP:
            return c
    if len(cands) == 1:
        sys.stderr.write(
            f"[경고] {os.path.basename(cands[0])} 의 MD5가 기대값과 다릅니다.\n"
            f"        기대 {MD5_JP}\n        실제 {md5(cands[0])}\n"
            "        다른 리비전이면 주소가 어긋나 패치가 깨질 수 있습니다.\n"
        )
        return cands[0]
    _die(f"{ROM_DIR} 안에 MD5가 일치하는 롬이 없습니다 (기대 {MD5_JP}).")


def rom_kr():
    """패치 결과 롬 경로 (build/)"""
    return out("Nobunaga no Yabou (Korean).gba")


def read_rom_jp():
    return open(rom_jp(), "rb").read()


def read_rom_kr():
    p = rom_kr()
    if not os.path.exists(p):
        _die(f"패치 롬이 없습니다: {p}\n  먼저 `python tools/inject.py` 를 실행하세요.")
    return open(p, "rb").read()


if __name__ == "__main__":
    print("repo root :", ROOT)
    print("data      :", DATA)
    print("build     :", BUILD)
    print("font      :", font())
    try:
        p = rom_jp()
        print("rom (JP)  :", p, "md5", md5(p))
    except SystemExit:
        pass
