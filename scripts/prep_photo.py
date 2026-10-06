"""
Prepare a portrait photo for clean ASCII conversion:
  1. remove the background (OpenCV GrabCut) so the subject is isolated
  2. bilateral-smooth skin texture while keeping edges (eyes, beard, collar)
  3. CLAHE + tone stretch over the subject only, so the face lands in sparse
     characters and hair / beard / sweater stay dense
  4. darken thin dark strokes (difference-of-gaussians) so eyelids, brows and
     the smile survive the downsample
  5. composite onto white and crop square around the subject

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py <input.png> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = float(os.environ.get("LINE_WEIGHT", 0.5))
UPSCALE = 3  # the GitHub avatar is 460px; work at ~1400px so the grid has detail

# 1. cut out the subject. GrabCut seeded with "the top corners and side strips
#    are backdrop" handles a plain studio background in a second; rembg (a
#    176 MB model, minutes on a loaded CPU) is not needed for a headshot.
#    Side strips stop at SIDE_SEED of the height: shoulders touch the frame
#    edges lower down.
src = Image.open(INP).convert("RGB")
src = src.resize((src.width * UPSCALE, src.height * UPSCALE), Image.LANCZOS)
rgb = np.array(src)
h, w = rgb.shape[:2]
gc = np.full((h, w), cv2.GC_PR_FGD, np.uint8)
edge = int(w * 0.04)
seed_h = int(h * float(os.environ.get("SIDE_SEED", 0.5)))
gc[:seed_h, :edge] = gc[:seed_h, -edge:] = cv2.GC_BGD
gc[:edge, :] = cv2.GC_BGD
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
small = cv2.resize(rgb, (w // UPSCALE, h // UPSCALE))
gc_small = cv2.resize(gc, (w // UPSCALE, h // UPSCALE), interpolation=cv2.INTER_NEAREST)
cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), gc_small, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
fg = np.where((gc_small == cv2.GC_FGD) | (gc_small == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, labels, stats, _ = cv2.connectedComponentsWithStats(fg)  # keep the largest blob
if n > 1:
    fg = np.where(labels == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
alpha = cv2.resize(fg, (w, h), interpolation=cv2.INTER_LINEAR)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. smooth texture, keep edges
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. local contrast, then stretch tones over the subject only
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
smooth = clahe.apply(smooth)
lo, hi = np.percentile(smooth[alpha > 128], [2, float(os.environ.get("HI_PCT", 96))])
tone = np.clip((smooth.astype(np.float32) - lo) / max(hi - lo, 1), 0, 1)

# 4. dark-on-light ridges -> darken
fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

# 5. paste onto white (feathered to avoid a halo), square crop
mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = out * mask + 255.0 * (1.0 - mask)

ys, xs = np.where(alpha > 20)
side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
canvas = np.full((side, side), 255, np.uint8)
x0, y0 = cx - side // 2, cy - side // 2
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

# keep the subject mask as alpha so make_ascii_svg.py can blank the background
# in positive mode (where white skin and the white backdrop would both be dense)
amask = np.zeros((side, side), np.uint8)
amask[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = (mask[sy0:sy1, sx0:sx1] * 255).astype(np.uint8)
Image.merge("LA", (Image.fromarray(canvas, mode="L"), Image.fromarray(amask, mode="L"))).save(OUT)
print("wrote", OUT, canvas.shape)
