"""
Convert the prepped portrait into a monochrome ASCII-art SVG that "types"
itself in like a terminal (one cursor rasters top -> bottom, then a blinking
cursor holds on the status line).

One fill colour + a good density ramp is what keeps ASCII portraits legible;
per-character colour is what makes them look like noise.

    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

from theme import BG, FRAME, INK, MUTED, PROMPT, svg_open, window

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait.svg")

COLS = int(os.environ.get("COLS", 180))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense)

CONTRAST = float(os.environ.get("CONTRAST", 1.05))
GAMMA = float(os.environ.get("GAMMA", 1.0))
WHITE_FLOOR = float(os.environ.get("WHITE_FLOOR", 0.80))

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

ROW_DUR = 5.8 / ROWS   # whole portrait prints in ~6s
STAGGER = ROW_DUR

NAME = os.environ.get("PORTRAIT_NAME", "Abdulhadi Alturafi")
STATIC = bool(os.environ.get("STATIC"))

# POSITIVE (default): bright pixels print as dense ink, which reads as a photo
# on a dark terminal. Needs the alpha mask prep_photo.py saves, since the
# backdrop and the skin highlights are both near white. POSITIVE=0 gives the
# original negative mapping (dark = dense), better for light line-art sources.
POSITIVE = os.environ.get("POSITIVE", "1") != "0"
SUBJECT_FLOOR = 1  # min ramp index inside the subject, keeps the silhouette

src = Image.open(SRC)
alpha = src.getchannel("A") if "A" in src.getbands() else None
im = ImageEnhance.Contrast(src.convert("L")).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()
apx = alpha.resize((COLS, ROWS), Image.LANCZOS).load() if alpha else None

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = pow(px[x, y] / 255.0, GAMMA)
        if POSITIVE and apx is not None:
            if apx[x, y] < 128:
                chars.append(" ")
                continue
            idx = max(SUBJECT_FLOOR, int(lum * (len(RAMP) - 1) + 0.5))
        else:
            if lum >= WHITE_FLOOR:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        chars.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

parts = [svg_open(CANVAS_W, CANVAS_H)]
parts += window(CANVAS_W, CANVAS_H, f"{PROMPT} ./portrait.sh", pad=PAD, titlebar=TITLEBAR_H)

font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">'
            f'{html.escape(line)}</text>')
    if STATIC:
        parts.append(text)
        continue
    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#r{ry})">{text}</g>'
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{INK}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="13">'
             f'{PROMPT} whoami <tspan fill="{INK}">{html.escape(NAME)}</tspan></text>')
status_chars = len(f"{PROMPT} whoami {NAME} ")
parts.append(f'<rect x="{PAD + status_chars * 13 * 0.6:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')
parts.append("</svg>")

svg = "".join(parts)
open(OUT, "w").write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
