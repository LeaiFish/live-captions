"""Generate Live Captions app icon at all macOS iconset sizes."""
import os
from PIL import Image, ImageDraw


def hex_rgba(h, a=255):
    h = h.lstrip('#')
    return (int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def make_icon(size):
    # Draw at 86% of canvas with transparent border to match system icon visual size
    pad = int(round(size * 0.07))
    inner = size - 2 * pad
    sc = inner / 128

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def S(v): return pad + int(round(v * sc))
    def SW(v): return int(round(v * sc))  # width/size only, no offset
    def W(v): return max(1, int(round(v * sc)))

    BG   = hex_rgba('#0f0f1a')
    BLUE = hex_rgba('#6c8eff')
    BLU6 = hex_rgba('#6c8eff', int(0.6 * 255))
    W92  = hex_rgba('#ffffff', int(0.92 * 255))
    W65  = hex_rgba('#ffffff', int(0.65 * 255))
    FILL = hex_rgba('#1a1a2e')

    # Squircle background at Apple standard corner radius (~22% of inner width)
    r = int(round(inner * 0.22))
    d.rounded_rectangle([pad, pad, pad + inner - 1, pad + inner - 1], radius=r, fill=BG)

    # Speech bubble fill
    d.rounded_rectangle([S(10), S(26), S(10) + SW(94), S(26) + SW(66)],
                        radius=SW(14), fill=FILL)

    # Tail fill
    tail = [(S(22), S(92)), (S(14), S(112)), (S(46), S(92))]
    d.polygon(tail, fill=FILL)

    # Speech bubble stroke
    d.rounded_rectangle([S(10), S(26), S(10) + SW(94), S(26) + SW(66)],
                        radius=SW(14), fill=None, outline=BLUE, width=W(2.5))

    # Tail stroke
    d.line([(S(22), S(92)), (S(14), S(112))], fill=BLUE, width=W(2.5))
    d.line([(S(14), S(112)), (S(46), S(92))], fill=BLUE, width=W(2.5))

    # Text line 1 — bright white
    d.rounded_rectangle([S(22), S(40), S(22) + SW(68), S(40) + SW(6)],
                        radius=SW(3), fill=W92)
    # Text line 2 — dim white
    d.rounded_rectangle([S(22), S(54), S(22) + SW(54), S(54) + SW(6)],
                        radius=SW(3), fill=W65)
    # Text line 3 — blue accent
    d.rounded_rectangle([S(22), S(68), S(22) + SW(40), S(68) + SW(6)],
                        radius=SW(3), fill=BLUE)

    # Mic badge
    d.rounded_rectangle([S(84), S(10), S(84) + SW(34), S(10) + SW(44)],
                        radius=SW(17), fill=FILL)
    d.rounded_rectangle([S(84), S(10), S(84) + SW(34), S(10) + SW(44)],
                        radius=SW(17), fill=None, outline=BLU6, width=W(2))

    # Mic capsule body
    d.rounded_rectangle([S(94), S(16), S(94) + SW(14), S(16) + SW(22)],
                        radius=SW(7), fill=BLUE)

    # Mic arc
    d.arc([S(88), S(28), S(88) + SW(26), S(28) + SW(14)], start=0, end=180,
          fill=BLUE, width=W(2.5))

    # Mic stand
    d.line([(S(101), S(42)), (S(101), S(48))], fill=BLUE, width=W(2.5))

    return img


ICONSET = {
    'icon_16x16.png':      16,
    'icon_16x16@2x.png':   32,
    'icon_32x32.png':      32,
    'icon_32x32@2x.png':   64,
    'icon_128x128.png':    128,
    'icon_128x128@2x.png': 256,
    'icon_256x256.png':    256,
    'icon_256x256@2x.png': 512,
    'icon_512x512.png':    512,
    'icon_512x512@2x.png': 1024,
}

out_dir = os.path.join(os.path.dirname(__file__), 'assets', 'AppIcon.iconset')
os.makedirs(out_dir, exist_ok=True)

for filename, size in ICONSET.items():
    icon = make_icon(size)
    path = os.path.join(out_dir, filename)
    icon.save(path)
    print(f"  {filename} ({size}x{size})")

print("Done.")
