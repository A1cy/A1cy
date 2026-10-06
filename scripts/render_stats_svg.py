#!/usr/bin/env python3
"""
Render the streak / numbers card from data/contributions.json as a terminal
window the same size as portrait.svg (840 x 880) so the two line up side by
side. Six stat tiles slide in and count up to the real value (a stack of
pre-rendered frames toggled with SMIL <set>, since GitHub runs no JS), then a
monthly bar chart grows in underneath.

    python scripts/render_stats_svg.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

from theme import CYAN, FRAME, INK, MUTED, PROMPT, PURPLE, TILE, svg_open, window

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "stats.svg")

W, H = 840, 880
PAD, TITLEBAR_H = 20, 30
COLS, ROWS, GAP = 2, 3, 16
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILE_H = 150
TILES_TOP = TITLEBAR_H + PAD + 4
CHART_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + GAP

TILE_STAGGER, SLIDE_DUR, COUNT_DUR, FRAMES = 0.15, 0.45, 1.2, 16
BAR_START = TILE_STAGGER * COLS * ROWS + 0.4
BAR_STAGGER, BAR_DUR = 0.06, 0.6


def short(d):
    return datetime.date.fromisoformat(d).strftime("%b %-d")


def span(s):
    return f'{short(s["start"])} to {short(s["end"])}' if s["length"] else "none yet"


def fmt(v, like):
    return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"


data = json.load(open(SRC))
cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
n_days = len(data["days"])

tiles = [
    ("current streak", cur["length"], " days", span(cur), CYAN),
    ("longest streak", lng["length"], " days", span(lng), INK),
    ("contributions", data["total_contributions"], "", "in the last year", PURPLE),
    ("active days", data["active_days"], f" / {n_days}", f'{data["active_days"] / n_days:.0%} of the year', INK),
    ("best day", best["count"], "", short(best["date"]), INK),
    ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
]

parts = [
    svg_open(W, H),
    '<style>'
    f'.t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}'
    '@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}'
    f'.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}'
    '@keyframes grow{to{transform:scaleY(1)}}'
    '@media (prefers-reduced-motion: reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}'
    '</style>',
]
parts += window(W, H, f"{PROMPT} ./stats.sh", pad=PAD, titlebar=TITLEBAR_H, grad_id="sbg")

for i, (label, value, suffix, caption, accent) in enumerate(tiles):
    col, row = i % COLS, i // COLS
    x = PAD + col * (TILE_W + GAP)
    y = TILES_TOP + row * (TILE_H + GAP)
    start = i * TILE_STAGGER
    count_start = start + SLIDE_DUR * 0.6

    parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
    parts.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{x+24:.1f}" y="{y+40}" fill="{MUTED}" font-size="22">$ {label}</text>')
    for k in range(1, FRAMES + 1):
        p = k / FRAMES
        v = value * (1 - (1 - p) ** 3)
        t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
        t_off = count_start + COUNT_DUR * k / FRAMES
        anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
        if k < FRAMES:
            anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
        parts.append(
            f'<text x="{x+24:.1f}" y="{y+100}" opacity="0" font-size="54" font-weight="700" fill="{accent}">'
            f'{fmt(v, value)}<tspan font-size="24" font-weight="400" fill="{MUTED}">{suffix}</tspan>{anim}</text>')
    parts.append(f'<text x="{x+24:.1f}" y="{y+132}" fill="{MUTED}" font-size="20">{caption}</text>')
    parts.append('</g>')

monthly = data["monthly"]
chart_x, chart_w = PAD, W - PAD * 2
chart_h = H - PAD - CHART_TOP
parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">'
             f'<rect x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{chart_h}" rx="10" fill="{TILE}" stroke="{FRAME}"/>'
             f'<text x="{chart_x+24}" y="{CHART_TOP+40}" fill="{MUTED}" font-size="22">$ contributions / month</text></g>')

plot_top, plot_bot = CHART_TOP + 64, CHART_TOP + chart_h - 40
plot_l, plot_r = chart_x + 24, chart_x + chart_w - 24
slot = (plot_r - plot_l) / len(monthly)
bar_w = slot * 0.62
peak = max(m["total"] for m in monthly) or 1
for i, m in enumerate(monthly):
    h = max(2, (plot_bot - plot_top) * m["total"] / peak)
    bx = plot_l + i * slot + (slot - bar_w) / 2
    fill = CYAN if m["total"] == peak else PURPLE
    delay = BAR_START + i * BAR_STAGGER
    parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                 f'rx="3" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
    mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 28}" fill="{MUTED}" font-size="18" text-anchor="middle">{mon}</text>')
    if m["total"] == peak:
        parts.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w/2:.1f}" '
                     f'y="{plot_bot - h - 10:.1f}" fill="{INK}" font-size="18" text-anchor="middle">{peak:,}</text>')

parts.append('</svg>')
svg = "".join(parts)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
