import sys, hashlib
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()
print("size", len(rom), hex(len(rom)))
print("md5", hashlib.md5(rom).hexdigest())
print("title", rom[0xA0:0xAC])
print("gamecode", rom[0xAC:0xB0])
print("maker", rom[0xB0:0xB2])
print("ver", rom[0xBC])
# find trailing padding
i = len(rom)
while i>0 and rom[i-1] in (0x00,0xFF):
    i -= 1
print("last non-pad byte at", hex(i))
