from PIL import Image
import numpy as np
S = r"C:\Users\Jay\AppData\Local\Temp\claude\D--gba-NOBU2\880e59fe-50f8-4f05-9587-2cbaf5132883\scratchpad"
img = Image.open(S+r"\bg3_menu.png").convert("L")
a = np.array(img)
on = a > 100

ys, xs = np.where(on)
print("text bbox: y", ys.min(), ys.max(), " x", xs.min(), xs.max())

# column occupancy for the first text line region
line1 = on[ys.min():ys.min()+16, :]
cols = line1.any(0)
xs1 = np.where(cols)[0]
print("line1 x range:", xs1.min(), xs1.max())
# find gaps -> character boundaries
gaps = []
prev = None
for x in range(xs1.min(), xs1.max()+2):
    if not cols[x]:
        if prev is None: prev = x
    else:
        if prev is not None:
            gaps.append((prev, x-1)); prev = None
print("gaps in line1:", gaps)

rows = line1.any(1)
print("line1 row occupancy:", [int(r) for r in rows])

# dump ascii art of first line
y0 = ys.min()
for y in range(y0-2, y0+14):
    print("".join("#" if on[y,x] else "." for x in range(xs1.min()-2, xs1.min()+62)))
