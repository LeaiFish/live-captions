"""Generate Live Captions app icon at all macOS iconset sizes."""
import os
from PIL import Image, ImageDraw


def hex_rgba(h, a=255):
    h = h.lstrip('#')
    return (int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def make_icon(size):
    sc = size / 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def S(v): return int(round(v * sc))
    def W(v): return max(1, int(round(v * sc)))

    BG   = hex_rgba('#c0b8b0')   # match macOS generic-app-template frame colour
    BLUE = hex_rgba('#6c8eff')
    BLU6 = hex_rgba('#6c8eff', int(0.6 * 255))
    W92  = hex_rgba('#ffffff', int(0.92 * 255))
    W65  = hex_rgba('#ffffff', int(0.65 * 255))
    FILL = hex_rgba('#1a1a2e')   # bubble fill: dark navy

    # Full-bleed background — same warm grey as the macOS unsigned-app frame
    d.rectangle([0, 0, size - 1, size - 1], fill=BG)

    # Speech bubble fill
    d.rounded_rectangle([S(10), S(26), S(10) + S(94), S(26) + S(66)],
                        radius=S(14), fill=FILL)

    # Tail fill (extends bubble downward)
    tail = [(S(22), S(92)), (S(14), S(112)), (S(46), S(92))]
    d.polygon(tail, fill=FILL)

    # Speech bubble stroke (drawn after tail fill so it sits on top cleanly)
    d.rounded_rectangle([S(10), S(26), S(10) + S(94), S(26) + S(66)],
                        radius=S(14), fill=None, outline=BLUE, width=W(2.5))

    # Tail stroke
    d.line([(S(22), S(92)), (S(14), S(112))], fill=BLUE, width=W(2.5))
    d.line([(S(14), S(112)), (S(46), S(92))], fill=BLUE, width=W(2.5))

    # Text line 1 — bright white
    d.rounded_rectangle([S(22), S(40), S(22) + S(68), S(40) + S(6)],
                        radius=S(3), fill=W92)
    # Text line 2 — dim white
    d.rounded_rectangle([S(22), S(54), S(22) + S(54), S(54) + S(6)],
                        radius=S(3), fill=W65)
    # Text line 3 — blue accent
    d.rounded_rectangle([S(22), S(68), S(22) + S(40), S(68) + S(6)],
                        radius=S(3), fill=BLUE)

    # Mic badge — drawn last so it sits on top of the bubble
    d.rounded_rectangle([S(84), S(10), S(84) + S(34), S(10) + S(44)],
                        radius=S(17), fill=FILL)
    d.rounded_rectangle([S(84), S(10), S(84) + S(34), S(10) + S(44)],
                        radius=S(17), fill=None, outline=BLU6, width=W(2))

    # Mic capsule body
    d.rounded_rectangle([S(94), S(16), S(94) + S(14), S(16) + S(22)],
                        radius=S(7), fill=BLUE)

    # Mic arc (bottom half of ellipse beneath the capsule)
    d.arc([S(88), S(28), S(114), S(42)], start=0, end=180,
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
