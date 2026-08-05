# -*- coding: utf-8 -*-
"""한 번에 패치 롬을 만든다.

    python build_patch.py            # 커밋된 번역으로 패치 롬 생성 + 검증
    python build_patch.py --full     # 문자열 추출부터 전 과정 재실행
    python build_patch.py --patch    # xdelta 패치까지 생성

원본 롬은 rom/ 폴더에 두거나 환경변수 NOBU2_ROM 으로 지정하세요.
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import paths

PY = sys.executable


def run(script, optional=False):
    print(f"\n{'='*60}\n▶ {script}\n{'='*60}")
    r = subprocess.run([PY, os.path.join(TOOLS, script)], cwd=ROOT)
    if r.returncode != 0:
        if optional:
            print(f"[경고] {script} 가 0이 아닌 코드로 종료했습니다 (계속 진행)")
        else:
            sys.exit(f"[중단] {script} 실패")


def main():
    full = "--full" in sys.argv
    make_patch = "--patch" in sys.argv

    rom = paths.rom_jp()          # 없으면 여기서 안내 후 종료
    print("원본 롬 :", rom)
    print("MD5     :", paths.md5(rom))
    if paths.md5(rom) != paths.MD5_JP:
        print("[경고] 기대 MD5와 다릅니다:", paths.MD5_JP)

    if full:
        # 롬에서 문자열을 다시 추출하고 번역 단위·포인터 안전성까지 재계산
        run("master_extract2.py")
        run("build_units2.py")
        run("build_batches.py")
        run("ptr_confirm.py")
        run("merge_tr.py")
        run("validate2.py", optional=True)   # 경고성 리포트

    run("inject.py")
    run("logo_patch.py")        # 타이틀 로고 이미지 한글화
    run("verify_all.py")
    run("code_diff.py")
    run("field_check.py")

    if make_patch:
        run("make_patch.py")

    print("\n" + "="*60)
    print("완료")
    print("  패치 롬 :", paths.rom_kr())
    print("  MD5     :", paths.md5(paths.rom_kr()))
    print("  기대값  :", paths.MD5_KR)
    if paths.md5(paths.rom_kr()) == paths.MD5_KR:
        print("  >>> 공식 배포본과 바이트 단위로 동일합니다")
    print("="*60)


if __name__ == "__main__":
    main()
