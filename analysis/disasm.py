import sys, struct
from capstone import *
data = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = False

def dis(off, n=120, base=0x08000000):
    code = data[off:off+n]
    for ins in md.disasm(code, base+off):
        print(f"{ins.address:08x}: {ins.bytes.hex()}  {ins.mnemonic}\t{ins.op_str}")

start = int(sys.argv[1], 16) if len(sys.argv)>1 else 0x7b60
n = int(sys.argv[2], 16) if len(sys.argv)>2 else 0x100
dis(start, n)
