"""Shared palette + terminal-window chrome for every SVG on the profile.

GitHub renders SVGs embedded via <img> and runs their SMIL / CSS keyframe
animations, but strips <script>, so every panel is a self-contained SVG.
"""

USER = "a1"
HOST = "github"
PROMPT = f"{USER}@{HOST}:~$"

BG = "#0d1117"
BG2 = "#131a26"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
TEXT = "#e6edf3"

PURPLE = "#9d4edd"
CYAN = "#00d9ff"
PINK = "#ff006e"
GOLD = "#f2cc60"

# contribution ramp, empty -> brightest (purple so it matches the profile)
RAMP = ["#161b22", "#3d2a6b", "#5e3aa6", "#8048d4", "#a865f0", "#dcb8ff"]

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]


def window(w, h, title, pad=20, titlebar=30, grad_id="bg"):
    """Rounded dark window with traffic-light dots and a centered title."""
    return [
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#{grad_id})"/>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{titlebar}" x2="{w}" y2="{titlebar}" stroke="{FRAME}"/>',
        *[f'<circle cx="{pad + i*16}" cy="{titlebar/2}" r="5" fill="{c}"/>' for i, c in enumerate(DOTS)],
        f'<text x="{w/2}" y="{titlebar/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">{title}</text>',
    ]


def svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}">')
