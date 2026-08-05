# -*- coding: utf-8 -*-
"""본편 화면까지 진입해 덤프"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drive import Drv, BP

d = None
try:
    d = Drv()
    print("Z0 ->", d.r.cmd(f"Z0,{BP:x},2", timeout=5))
    d.frames(90)
    d.tap("START", 4, 50)      # 타이틀 -> 모드
    d.tap("A", 4, 50)          # 입문 모드
    d.tap("A", 4, 50)          # 레벨
    d.tap("A", 4, 70)          # 시나리오
    d.tap("A", 4, 90)          # 확인
    d.tap("A", 4, 90)          # 다이묘 선택 진입
    for i in range(3):
        d.tap("A", 4, 90)
        d.dump(f"g{i:02d}")
    # 커서 이동 후 결정
    for i in range(3):
        d.tap("R", 3, 20)
    d.tap("A", 4, 120); d.dump("g10")
    d.tap("A", 4, 120); d.dump("g11")
    d.tap("A", 4, 150); d.dump("g12")
    d.tap("A", 4, 150); d.dump("g13")
    d.tap("B", 4, 90);  d.dump("g14")
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
