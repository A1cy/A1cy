#!/usr/bin/env python3
"""
neofetch-style info card: key / value rows that fade + slide in one line at a
time, then a blinking cursor. Static content lives in ROWS below; edit and
re-run. Same canvas as portrait.svg (840 x 880) so they pair side by side.

    STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import html
import os
import sys

from theme import CYAN, FRAME, INK, MUTED, PINK, PROMPT, PURPLE, TEXT, svg_open, window

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

W, H = 840, 880
PAD, TITLEBAR_H = 20, 30
LINE_H = 38
FONT = 23
STATIC = bool(os.environ.get("STATIC"))

# (key, value, value colour). key None = blank line, key "" = section rule
ROWS = [
    ("", "Abdulhadi Alturafi", TEXT),
    (None, "", None),
    ("Role", "Digital Transformation Manager", CYAN),
    ("Company", "MHG Trading CJSC, Riyadh", INK),
    ("Path", "Web Dev > Full-Stack > DX Manager", INK),
    (None, "", None),
    ("Leading", "Enterprise CRM, 40+ branches, 3 countries", INK),
    ("Building", "AI agents, voice AI, AI recruiting", INK),
    ("Platform", "Dynamics 365, Dataverse, Entra ID SSO", INK),
    ("AI", "Claude, Bedrock, ElevenLabs, Gemini", INK),
    ("Stack", "TypeScript, Next.js, Python, Supabase", INK),
    ("Cloud", "Vercel, AWS, Azure, n8n, Docker", INK),
    (None, "", None),
    ("Uptime", "99.9% SLA, 40% faster p95 on AI", PURPLE),
    ("Shipped", "8 major releases in 7 months", INK),
    ("Langs", "Arabic, English, German (learning)", INK),
    (None, "", None),
    ("Web", "a1xai.vercel.app", PINK),
    ("Mail", "a1hvdy@gmail.com", INK),
]

parts = [svg_open(W, H),
         '<style>.l{opacity:0;animation:in .4s ease-out both}'
         '@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}'
         '@media (prefers-reduced-motion: reduce){.l{opacity:1!important;animation:none!important}}</style>']
parts += window(W, H, f"{PROMPT} neofetch", pad=PAD, titlebar=TITLEBAR_H, grad_id="ibg")

y = TITLEBAR_H + PAD + 36
KEY_W = 165
delay = 0.3
for key, value, colour in ROWS:
    if key is None:
        y += LINE_H * 0.5
        continue
    cls = "" if STATIC else f' class="l" style="animation-delay:{delay:.2f}s"'
    if key == "":
        parts.append(f'<text{cls} x="{PAD+24}" y="{y}" font-size="30" font-weight="700" fill="{colour}">{html.escape(value)}</text>')
        y += 10
        parts.append(f'<line{cls} x1="{PAD+24}" y1="{y+6}" x2="{W-PAD-24}" y2="{y+6}" stroke="{FRAME}"/>')
        y += LINE_H
    else:
        parts.append(f'<text{cls} x="{PAD+24}" y="{y}" font-size="{FONT}">'
                     f'<tspan fill="{PURPLE}" font-weight="700">{html.escape(key)}</tspan>'
                     f'<tspan fill="{MUTED}" x="{PAD+24+KEY_W-18}">:</tspan>'
                     f'<tspan fill="{colour}" x="{PAD+24+KEY_W}">{html.escape(value)}</tspan></text>')
        y += LINE_H
    delay += 0.12

# colour swatches, neofetch style
y += LINE_H * 0.5
cls = "" if STATIC else f' class="l" style="animation-delay:{delay:.2f}s"'
parts.append(f'<g{cls}>')
for i, c in enumerate(["#0d1117", "#30363d", PURPLE, CYAN, PINK, "#f2cc60", "#39d353", TEXT]):
    parts.append(f'<rect x="{PAD+24+i*44}" y="{y}" width="40" height="22" rx="3" fill="{c}"/>')
parts.append('</g>')
y += 22 + LINE_H

parts.append(f'<text x="{PAD+24}" y="{y}" fill="{MUTED}" font-size="{FONT}">{PROMPT} </text>')
cx = PAD + 24 + len(f"{PROMPT} ") * FONT * 0.6
parts.append(f'<rect x="{cx:.1f}" y="{y-16}" width="11" height="20" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>')
parts.append('</svg>')

svg = "".join(parts)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)} bytes")
