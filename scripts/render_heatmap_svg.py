#!/usr/bin/env python3
"""
Render data/contributions.json as a GitHub-style contribution heatmap SVG:
53 weeks x 7 days of rounded boxes, revealed once with a diagonal cascade
(CSS keyframes, plays on load then freezes), a Less -> More legend and a
stats footer. Colour levels come from GitHub's own data-level (0..4) plus a
fifth tier for the top 5% of days, so the ramp stays readable on a profile
with a few 1000+ commit days.

Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os

from theme import CYAN, FRAME, GOLD, MUTED, PROMPT, PURPLE, RAMP, svg_open, window

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42


def build_grid(days, top_cut):
    first = datetime.date.fromisoformat(days[0]["date"])
    grid, col = [], [None] * ((first.weekday() + 1) % 7)
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        lvl = int(d.get("level", 0))
        if lvl == 4 and d["count"] >= top_cut:
            lvl = 5
        col.append((d["date"], d["count"], lvl))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        col += [None] * (7 - len(col))
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    top_cut = counts[int(len(counts) * 0.95)] if counts else 1
    grid = build_grid(days, top_cut)
    art_w, art_h = len(grid) * STEP, 7 * STEP

    month_labels, seen = [], set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            if (date.year, date.month) not in seen and date.day <= 7:
                seen.add((date.year, date.month))
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + 88 + PAD

    parts = [svg_open(canvas_w, canvas_h),
             '<style>@keyframes cell{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}'
             f'.c{{opacity:0;animation:cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both}}'
             '@media (prefers-reduced-motion: reduce){.c{opacity:1!important;animation:none!important}}</style>']
    parts += window(canvas_w, canvas_h, f"{PROMPT} ./contributions.sh --graph", pad=PAD, titlebar=TITLEBAR_H, grad_id="hbg")

    grid_top, grid_left = TITLEBAR_H + TOP_LABEL_H, PAD + LEFT_LABEL_W
    for ci, label in month_labels:
        parts.append(f'<text x="{grid_left + ci * STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="{PAD}" y="{grid_top + wi * STEP + CELL * 0.78:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{gx}" y="{grid_top + ri * STEP}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{RAMP[lvl]}" style="animation-delay:{ci * COL_T + ri * ROW_T:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>')

    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(RAMP) * (CELL - 1) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in RAMP:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.6"/>')

    cs, ls = data["current_streak"]["length"], data["longest_streak"]["length"]
    total, best, rng = data["total_contributions"], data["best_day"], data["range"]
    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{PURPLE}"><tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
                 f'<tspan fill="{CYAN}" font-weight="700">{cs} days</tspan>'
                 f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
                 f'<tspan fill="{CYAN}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]:,}</tspan> on {best["date"]}</text>')
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    svg = render(json.load(open(IN_PATH)))
    open(OUT_PATH, "w").write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
