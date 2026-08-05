import struct, json
rom = open(r"D:\gba\NOBU2\Nobunaga no Yabou (Japan).gba","rb").read()

TB2 = 0x30d6ce
N2 = 0x74D + 1  # 1870
FONT2 = 0x305274

chars = []
for i in range(N2):
    v = struct.unpack_from("<H", rom, TB2 + i*2)[0]
    b = bytes([v >> 8, v & 0xFF])
    try:
        ch = b.decode("shift_jis")
    except Exception:
        ch = None
    chars.append((i, v, ch))

bad = [c for c in chars if c[2] is None]
print("total", len(chars), "undecodable", len(bad))
# verify ascending
asc = all(chars[i][1] < chars[i+1][1] for i in range(len(chars)-1))
print("ascending:", asc)

def cls(ch):
    if ch is None: return "?"
    o = ord(ch)
    if 0x3041 <= o <= 0x309F: return "hira"
    if 0x30A0 <= o <= 0x30FF: return "kata"
    if 0x4E00 <= o <= 0x9FFF: return "kanji"
    return "sym"

from collections import Counter
cnt = Counter(cls(c[2]) for c in chars)
print(cnt)

kata = [c for c in chars if cls(c[2])=="kata"]
kanji = [c for c in chars if cls(c[2])=="kanji"]
print("kata range: idx", kata[0][0], "-", kata[-1][0])
print("kanji range: idx", kanji[0][0], "-", kanji[-1][0])
print("kata:", "".join(c[2] for c in kata))
print("first kanji:", "".join(c[2] for c in kanji[:80]))
print("last kanji:", "".join(c[2] for c in kanji[-40:]))

with open(r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad\charset.json","w",encoding="utf-8") as f:
    json.dump([{"idx":i,"sjis":v,"ch":ch,"cls":cls(ch)} for i,v,ch in chars], f, ensure_ascii=False, indent=0)
print("charset.json written")

# all kanji as one string for mapping work
with open(r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad\kanji_list.txt","w",encoding="utf-8") as f:
    f.write("".join(c[2] for c in kanji))
print("kanji count:", len(kanji))
