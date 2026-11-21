"""Generate the SVG assets for the GitHub profile README.

Styled after https://matthewmacraebovell.com (Geist, vortex rings).

    pip install fonttools brotli
    python scripts/generate.py

Writes light + dark variants of every asset into ./assets.
"""

import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"

SITE = "https://matthewmacraebovell.com"

THEMES = {
    "light": dict(
        bg="#f9fafb",
        card="#ffffff",
        text="#0f172a",
        muted="#64748b",
        faint="#94a3b8",
        border="rgba(15,23,42,0.12)",
        glow=1.0,
        ring=1.0,
    ),
    "dark": dict(
        bg="#0b0f19",
        card="#111726",
        text="#e2e8f0",
        muted="#94a3b8",
        faint="#64748b",
        border="rgba(226,232,240,0.12)",
        glow=1.6,
        ring=1.4,
    ),
}

ROLES = [
    "Software Engineer",
    "Writer",
    "Speaker",
    "Researcher",
    "Community Builder",
    "Game Designer",
    "Adventurer",
]

BUTTONS = [
    ("website", "matthewmacraebovell.com", True),
    ("blog", "Blog", False),
    ("talks", "Talks", False),
    ("linkedin", "LinkedIn", False),
    ("coffee", "Coffee chat ☕", False),
]


# ── fonts ────────────────────────────────────────────────────────────────


def all_text():
    parts = ["Matthew MacRae-Bovell", "Ottawa, Canada", "OTTAWA, CANADA", "→"]
    parts += ROLES
    parts.append("Building things, sharing ideas, and exploring what's next.")
    parts += [b[1] for b in BUTTONS]
    return "".join(parts)


def subset_font(name, text):
    font = TTFont(FONTS / name)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    sub = subset.Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


class Measure:
    def __init__(self, name):
        self.path = FONTS / name
        self.cache = {}

    def width(self, text, size, weight=400):
        if weight not in self.cache:
            inst = instancer.instantiateVariableFont(
                TTFont(self.path), {"wght": weight}
            )
            self.cache[weight] = (inst.getBestCmap(), inst["hmtx"], inst["head"].unitsPerEm)
        cmap, hmtx, upm = self.cache[weight]
        return sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in text) * size / upm


TEXT = all_text()
SANS = subset_font("GeistVF.woff", TEXT)
MONO = subset_font("GeistMonoVF.woff", TEXT)
sans_m = Measure("GeistVF.woff")

FONT_CSS = f"""
@font-face{{font-family:G;font-weight:100 900;src:url(data:font/woff2;base64,{SANS}) format('woff2')}}
@font-face{{font-family:GM;font-weight:100 900;src:url(data:font/woff2;base64,{MONO}) format('woff2')}}
.s{{font-family:G,'Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}}
.m{{font-family:GM,'Geist Mono',ui-monospace,SFMono-Regular,Menlo,monospace}}
"""

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rgba(rgb, a):
    return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{min(a, 1):.3f})"


# ── hero ─────────────────────────────────────────────────────────────────

# (rx, ry, rgb, alpha, faint-side angle, seconds, direction)
RINGS = [
    (90, 90, (81, 122, 255), 0.50, 270, 5, 1),
    (170, 150, (81, 122, 255), 0.36, 0, 9, -1),
    (260, 230, (100, 130, 255), 0.28, 90, 15, 1),
    (360, 315, (120, 100, 255), 0.21, 180, 23, -1),
    (470, 410, (140, 90, 255), 0.15, 270, 34, 1),
    (580, 500, (150, 80, 255), 0.10, 0, 47, -1),
]


def hero(t):
    W, H = 1200, 500
    cx, cy = 790, 230
    defs, rings, css = [], [], []

    for i, (rx, ry, rgb, a, ang, secs, d) in enumerate(RINGS):
        a = a * t["ring"]
        # Gradient stroke: strong on one side, faint on the other (like a
        # single translucent CSS border side).
        defs.append(
            f'<linearGradient id="r{i}" gradientTransform="rotate({ang} .5 .5)">'
            f'<stop offset="0" stop-color="{rgba(rgb, a * 0.12)}"/>'
            f'<stop offset=".55" stop-color="{rgba(rgb, a)}"/>'
            f'<stop offset="1" stop-color="{rgba(rgb, a)}"/></linearGradient>'
        )
        sw = 1.5 if i < 2 else 1
        rings.append(
            f'<ellipse class="ring" style="animation:{"cw" if d > 0 else "ccw"} {secs}s linear infinite" '
            f'rx="{rx}" ry="{ry}" fill="none" stroke="url(#r{i})" stroke-width="{sw}"/>'
        )

    g = t["glow"]
    glows = [
        ("ga", 350, 250, 820, 170, (80, 120, 230), 0.18 * g, "da 8s"),
        ("gb", 300, 240, 300, 150, (110, 160, 255), 0.14 * g, "db 11s"),
        ("gc", 210, 210, 640, 330, (140, 90, 255), 0.10 * g, "dc 7s"),
    ]
    glow_svg = []
    for gid, rx, ry, x, y, rgb, a, anim in glows:
        defs.append(
            f'<radialGradient id="{gid}"><stop offset="0" stop-color="{rgba(rgb, a)}"/>'
            f'<stop offset=".65" stop-color="{rgba(rgb, 0)}"/></radialGradient>'
        )
        glow_svg.append(
            f'<g transform="translate({x} {y})"><ellipse style="animation:{anim} ease-in-out infinite" '
            f'rx="{rx}" ry="{ry}" fill="url(#{gid})"/></g>'
        )

    n = len(ROLES)
    period = 2.5 * n
    role_svg = "".join(
        f'<text class="m role" x="0" y="0" style="animation-delay:{0.6 + i * 2.5:.1f}s">{esc(r)}</text>'
        for i, r in enumerate(ROLES)
    )

    css.append(
        f"""
{FONT_CSS}
.ring{{transform-origin:0 0}}
@keyframes cw{{to{{transform:rotate(360deg)}}}}
@keyframes ccw{{to{{transform:rotate(-360deg)}}}}
@keyframes da{{0%,100%{{transform:translate(0,0) scale(1);opacity:.8}}25%{{transform:translate(90px,-50px) scale(1.18);opacity:.5}}50%{{transform:translate(45px,40px) scale(.88);opacity:.75}}75%{{transform:translate(-60px,-30px) scale(1.1);opacity:.55}}}}
@keyframes db{{0%,100%{{transform:translate(0,0) scale(1);opacity:.6}}30%{{transform:translate(-80px,50px) scale(.85);opacity:.85}}60%{{transform:translate(60px,30px) scale(1.15);opacity:.5}}}}
@keyframes dc{{0%,100%{{transform:translate(0,0) scale(1);opacity:.5}}25%{{transform:translate(70px,-40px) scale(1.2);opacity:.75}}50%{{transform:translate(-50px,50px) scale(.82);opacity:.4}}75%{{transform:translate(-70px,-30px) scale(1.1);opacity:.65}}}}
@keyframes role{{0%{{opacity:0;transform:translateY(14px)}}2%,12%{{opacity:1;transform:none}}14%{{opacity:0;transform:translateY(-10px)}}15%,100%{{opacity:0;transform:translateY(14px)}}}}
.role{{font-size:34px;fill:{t["muted"]};opacity:0;animation:role {period}s ease-in-out infinite backwards}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.role{{opacity:0}}.role:first-child{{opacity:1}}}}
"""
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Matthew MacRae-Bovell — {esc(', '.join(ROLES))}">
<title>Matthew MacRae-Bovell</title>
<style>{css[0]}</style>
<defs>{''.join(defs)}<clipPath id="clip"><rect width="{W}" height="{H}" rx="24"/></clipPath></defs>
<g clip-path="url(#clip)">
<rect width="{W}" height="{H}" fill="{t["bg"]}"/>
{''.join(glow_svg)}
<g transform="translate({cx} {cy})">{''.join(rings)}</g>
<g transform="translate(72 0)">
<text class="m" y="120" font-size="14" letter-spacing="1.1" fill="{t["muted"]}" opacity=".75">🇨🇦 OTTAWA, CANADA</text>
<g><text class="s" y="215" font-size="96" font-weight="700" letter-spacing="-3.8" fill="{t["text"]}">Matthew</text>
<text class="s" y="310" font-size="96" font-weight="700" letter-spacing="-3.8" fill="{t["text"]}">MacRae-Bovell</text></g>
<g transform="translate(2 378)">{role_svg}</g>
<text class="s" x="2" y="432" font-size="20" fill="{t["muted"]}">Building things, sharing ideas, and exploring what's next.</text>
</g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{t["border"]}"/>
</svg>"""


# ── buttons ──────────────────────────────────────────────────────────────


def button(t, label, primary):
    size, h, padx = 15, 40, 20
    w = round(sans_m.width(label, size, 500) + padx * 2)
    if primary:
        fill, stroke, color = "#517aff", "#517aff", "#ffffff"
    else:
        fill, stroke, color = t["card"], t["border"], t["text"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2}" height="{h + 2}" viewBox="-1 -1 {w + 2} {h + 2}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<style>{FONT_CSS}</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{(h - 1) / 2}" fill="{fill}" stroke="{stroke}"/>
<text class="s" x="{w / 2}" y="{h / 2 + 5.2}" text-anchor="middle" font-size="{size}" font-weight="500" fill="{color}">{esc(label)}</text>
</svg>"""


def main():
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"hero-{name}.svg").write_text(hero(t))
        for key, label, primary in BUTTONS:
            (OUT / f"btn-{key}-{name}.svg").write_text(button(t, label, primary))
    print("wrote", len(list(OUT.glob("*.svg"))), "files to", OUT)


if __name__ == "__main__":
    main()
