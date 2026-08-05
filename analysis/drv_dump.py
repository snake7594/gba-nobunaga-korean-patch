import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rsp_cmd import do
tag = sys.argv[1] if len(sys.argv)>1 else "menu"
print(do({"op":"read","addr":0x06000000,"len":0x18000,"out":f"vram_{tag}.bin"}, 300))
print(do({"op":"read","addr":0x05000000,"len":0x400,"out":f"pram_{tag}.bin"}, 60))
print(do({"op":"read","addr":0x07000000,"len":0x400,"out":f"oam_{tag}.bin"}, 60))
print(do({"op":"read","addr":0x04000000,"len":0x60,"out":f"io_{tag}.bin"}, 60))
