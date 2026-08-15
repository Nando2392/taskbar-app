"""Genera icon.ico (cuadro oscuro + check acuamarina) para TaskBar."""
from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]
FRAMES = []
for s in SIZES:
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = max(2, s // 8)
    d.rounded_rectangle([1, 1, s - 2, s - 2], radius=r, fill=(20, 22, 28, 255))
    m = s * 0.20
    t = max(2, s // 9)
    d.line([(m, s * 0.54), (s * 0.45, s * 0.68), (s - m, s * 0.33)],
           fill=(94, 234, 212, 255), width=t, joint="curve")
    FRAMES.append(im)

FRAMES[0].save("icon.ico", format="ICO",
               sizes=[(s, s) for s in SIZES], append_images=FRAMES[1:])
print("icon.ico generado")
