# -*- coding: utf-8 -*-
"""GDB 브레이크포인트로 키 입력을 주입해 게임을 조작하고 화면을 덤프한다.

키 처리 루틴 0x08002480:
    [0x03001478] = 이번 프레임에 새로 눌린 키
    [0x03001470] = 현재 눌린 키
루틴이 끝나는 지점(0x0800249A)에서 멈춰 두 변수를 덮어쓰면
게임은 그 프레임에 그 키가 눌린 것으로 본다.
"""
import sys, os, time, struct, binascii
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdbrsp import RSP

S = os.path.dirname(os.path.abspath(__file__))
BP = 0x0800249A
V_NEW, V_CUR = 0x03001478, 0x03001470

KEY = {"A": 0x001, "B": 0x002, "SEL": 0x004, "START": 0x008,
       "R": 0x010, "L": 0x020, "UP": 0x040, "DOWN": 0x080,
       "RB": 0x100, "LB": 0x200, "": 0}


class Drv:
    def __init__(self):
        self.r = RSP()
        self.r.flush_packets()
        self.r.cmd("?", timeout=8)
        self.r.cmd(f"Z0,{BP:x},2", timeout=5)

    def frames(self, n, key=""):
        """n 프레임 진행. key 를 매 프레임 주입"""
        k = KEY[key] if isinstance(key, str) else key
        for _ in range(n):
            self.r.send(b"c")
            p = self.r.recv_packet(timeout=10)
            if p is None:
                # 브레이크포인트가 안 걸리면 그냥 시간으로 진행
                self.r.halt()
                continue
            if k:
                self.r.cmd("M%x,2:%s" % (V_NEW, binascii.hexlify(struct.pack("<H", k)).decode()))
                self.r.cmd("M%x,2:%s" % (V_CUR, binascii.hexlify(struct.pack("<H", k)).decode()))

    def tap(self, key, hold=2, gap=8):
        self.frames(hold, key)
        self.frames(gap, "")

    def dump(self, tag):
        R = self.r
        for n, a, ln in (("vram", 0x06000000, 0x18000), ("pram", 0x05000000, 0x400),
                         ("oam", 0x07000000, 0x400), ("io", 0x04000000, 0x60)):
            open(os.path.join(S, f"{n}_{tag}.bin"), "wb").write(R.read_mem(a, ln))
        io = open(os.path.join(S, f"io_{tag}.bin"), "rb").read()
        dc = struct.unpack_from("<H", io, 0)[0]
        print(f"[{tag}] DISPCNT={dc:04x}", end=" ")
        for i in range(4):
            if (dc >> (8+i)) & 1:
                bg = struct.unpack_from("<H", io, 8+i*2)[0]
                print(f"BG{i}(c={((bg>>2)&3)*0x4000:#x},s={((bg>>8)&31)*0x800:#x},8b={(bg>>7)&1})", end=" ")
        print()

    def close(self):
        self.r.cmd(f"z0,{BP:x},2", timeout=5)
        self.r.detach()
