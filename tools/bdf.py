"""Minimal BDF parser -> dict[codepoint] = (bbx_w,bbx_h,xoff,yoff,dwidth,rows[list of int])"""
def load_bdf(path):
    glyphs = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        enc = None; bbx = None; dw = None; rows = None; inbm = False
        fbbx = None; ascent = None; descent = None
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("FONTBOUNDINGBOX"):
                p = line.split(); fbbx = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
            elif line.startswith("FONT_ASCENT"):
                ascent = int(line.split()[1])
            elif line.startswith("FONT_DESCENT"):
                descent = int(line.split()[1])
            elif line.startswith("ENCODING"):
                enc = int(line.split()[1])
            elif line.startswith("DWIDTH"):
                dw = int(line.split()[1])
            elif line.startswith("BBX"):
                p = line.split(); bbx = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
            elif line.startswith("BITMAP"):
                inbm = True; rows = []
            elif line.startswith("ENDCHAR"):
                if enc is not None and enc >= 0:
                    glyphs[enc] = (bbx, dw, rows)
                enc=None; bbx=None; dw=None; rows=None; inbm=False
            elif inbm:
                rows.append(int(line, 16))
    return glyphs, fbbx, ascent, descent

def render12(glyphs, ascent, cp, W=12, H=12, baseline=None):
    """render codepoint into WxH cell (list of W-bit ints)."""
    if cp not in glyphs: return None
    (bw, bh, xo, yo), dw, rows = glyphs[cp]
    if baseline is None: baseline = ascent  # y of baseline from top = ascent
    out = [0]*H
    hexw = ((bw+7)//8)*8
    for i, rv in enumerate(rows):
        # top row of bitmap is at y = baseline - (yo + bh) + i
        y = baseline - (yo + bh) + i
        if not (0 <= y < H): continue
        # bits: MSB-first across hexw
        rowbits = 0
        for x in range(bw):
            bit = (rv >> (hexw-1-x)) & 1
            xx = x + xo
            if 0 <= xx < W and bit:
                rowbits |= 1 << (W-1-xx)
        out[y] |= rowbits
    return out

if __name__ == "__main__":
    import sys
    g, fb, asc, dsc = load_bdf(r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad\Galmuri11.bdf")
    print("glyphs:", len(g), "fbbx:", fb, "ascent:", asc, "descent:", dsc)
    for ch in "신장왕카건베ㄴㅅ가":
        r = render12(g, asc, ord(ch))
        print("---", ch)
        if r is None: print("MISSING"); continue
        for v in r:
            print("".join("#" if (v>>(11-x))&1 else "." for x in range(12)))
