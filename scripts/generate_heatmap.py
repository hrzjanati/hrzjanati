#!/usr/bin/env python3
"""Generate an animated, Apple-style contribution heatmap as an SVG.

Usage:  python3 scripts/generate_heatmap.py [username] [output.svg]
No token needed: it reads the public contributions calendar.
"""
import re, sys, html, urllib.request
from datetime import date

user = sys.argv[1] if len(sys.argv) > 1 else "hrzjanati"
out = sys.argv[2] if len(sys.argv) > 2 else "assets/heatmap.svg"

req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                             headers={"User-Agent": "Mozilla/5.0"})
page = urllib.request.urlopen(req, timeout=30).read().decode()

counts = {}
for cid, n in re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>(No|\d+) contributions?', page):
    counts[cid] = 0 if n == "No" else int(n)

days = []
for m in re.finditer(r'<td[^>]*data-date="([\d-]+)"[^>]*id="(contribution-day-component-(\d+)-(\d+))"[^>]*data-level="(\d)"', page):
    d, cid, row, col, lvl = m.groups()
    days.append((int(col), int(row), date.fromisoformat(d), int(lvl), counts.get(cid, 0)))
if not days:
    sys.exit("Could not read the contributions calendar.")

days.sort(key=lambda x: (x[0], x[1]))
total = sum(d[4] for d in days)
cols = max(d[0] for d in days) + 1

# streaks and best day
by_date = sorted(days, key=lambda x: x[2])
best = max(by_date, key=lambda x: x[4])
longest = cur = 0
for d in by_date:
    cur = cur + 1 if d[4] > 0 else 0
    longest = max(longest, cur)

COLORS = ["#1c1c1e", "#12345c", "#0a6ad6", "#5e5ce6", "#bf5af2"]
CELL, GAP, X0, Y0 = 14, 4, 60, 118
PITCH = CELL + GAP
W = X0 + cols * PITCH + 36
H = Y0 + 7 * PITCH + 56

p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{total} contributions in the last year">')
p.append('<defs><linearGradient id="tg" x1="0" x2="1"><stop offset="0" stop-color="#64d2ff"/><stop offset=".5" stop-color="#5e5ce6"/><stop offset="1" stop-color="#bf5af2"/></linearGradient>'
         '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
p.append('<style>text{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif}'
         '.c{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .6s cubic-bezier(.2,.8,.2,1) forwards}'
         '@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:scale(1)}}'
         '.a{animation:pop .6s cubic-bezier(.2,.8,.2,1) forwards,wave 7s ease-in-out infinite}'
         '@keyframes wave{0%,16%,100%{transform:scale(1);stroke-opacity:0}8%{transform:scale(1.28);stroke-opacity:.9}}'
         '.hd{opacity:0;animation:fade 1s ease forwards}@keyframes fade{to{opacity:1}}</style>')
p.append(f'<rect width="{W}" height="{H}" rx="28" fill="#000"/><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="28" fill="none" stroke="#2c2c2e"/>')

p.append(f'<g class="hd"><text x="40" y="64" font-size="34" font-weight="700" letter-spacing="-1" fill="url(#tg)">{total:,} contributions</text>'
         f'<text x="40" y="90" font-size="14" fill="#8e8e93">in the last year</text>'
         f'<text x="{W-40}" y="56" font-size="13" fill="#8e8e93" text-anchor="end">Longest streak  <tspan fill="#f5f5f7" font-weight="600">{longest} days</tspan></text>'
         f'<text x="{W-40}" y="78" font-size="13" fill="#8e8e93" text-anchor="end">Best day  <tspan fill="#f5f5f7" font-weight="600">{best[4]} contributions</tspan></text></g>')

# month labels
last_m = None
for col in range(cols):
    first = next((d for d in days if d[0] == col), None)
    if first and first[2].month != last_m:
        if col == 0 or first[2].day <= 7 or last_m is None:
            p.append(f'<text class="hd" x="{X0 + col*PITCH}" y="{Y0-10}" font-size="12" fill="#8e8e93">{first[2].strftime("%b")}</text>')
        last_m = first[2].month
for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    p.append(f'<text class="hd" x="{X0-12}" y="{Y0 + r*PITCH + 11}" font-size="11" fill="#8e8e93" text-anchor="end">{name}</text>')

for col, row, d, lvl, n in days:
    x, y = X0 + col * PITCH, Y0 + row * PITCH
    delay = col * 0.035 + row * 0.01
    tip = f'<title>{n} contributions on {d.isoformat()}</title>'
    if lvl:
        wd = (col * 0.09) % 7
        p.append(f'<rect class="a" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{COLORS[lvl]}" stroke="#fff" style="animation-delay:{delay:.2f}s,{2+wd:.2f}s">{tip}</rect>')
    else:
        p.append(f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{COLORS[0]}" style="animation-delay:{delay:.2f}s">{tip}</rect>')

ly = H - 30
lx = W - 40 - 5 * PITCH - 70
p.append(f'<g class="hd"><text x="{lx}" y="{ly+11}" font-size="12" fill="#8e8e93" text-anchor="end">Less</text>')
for i, c in enumerate(COLORS):
    p.append(f'<rect x="{lx+10+i*PITCH}" y="{ly}" width="{CELL}" height="{CELL}" rx="4" fill="{c}"/>')
p.append(f'<text x="{lx+16+5*PITCH}" y="{ly+11}" font-size="12" fill="#8e8e93">More</text></g></svg>')

open(out, "w").write("".join(p))
print(f"{out}: {total} contributions, {len(days)} days, longest streak {longest}")
