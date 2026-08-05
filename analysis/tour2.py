# -*- coding: utf-8 -*-
"""한 세션에서 주요 화면을 순회 덤프 (실패해도 반드시 detach)"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drive import Drv, BP

d = None
try:
    d = Drv()
    z = d.r.cmd(f"Z0,{BP:x},2", timeout=5)
    print("Z0 ->", z)
    ok = (z == b"OK")
    if not ok:
        print("소프트 브레이크포인트 미지원 -> Z1 시도")
        print("Z1 ->", d.r.cmd(f"Z1,{BP:x},2", timeout=5))

    d.frames(90)                      # 타이틀
    d.dump("s01_title")
    d.tap("START", 4, 50); d.dump("s02_mode")
    d.tap("A", 4, 50);     d.dump("s03")
    d.tap("A", 4, 50);     d.dump("s04")
    d.tap("A", 4, 70);     d.dump("s05")
    d.tap("A", 4, 90);     d.dump("s06")
    d.tap("A", 4, 90);     d.dump("s07")
    d.tap("A", 4, 120);    d.dump("s08")
    print("done")
except Exception:
    traceback.print_exc()
finally:
    if d:
        try:
            d.close()
        except Exception:
            try:
                d.r.detach()
            except Exception:
                pass
    print("detached")
