"""
Builds every image used by the profile README, in the "Editorial Ink" system of the
v2027 portfolio: ink / bone / one rust accent, Geist + Instrument Serif Italic + Geist Mono.

Static text is drawn as real glyph outlines (shaped with HarfBuzz), so typography is
identical in every browser. The only live text is the numbers in dark_mode.svg /
light_mode.svg, which today.py rewrites daily; those use an embedded font subset.

    pip install -r scripts/readme/requirements.txt
    python scripts/readme/build.py
"""
from __future__ import annotations

import base64
import io
import math
import re
from pathlib import Path

import uharfbuzz as hb
from xml.sax.saxutils import escape
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image

from content import ABOUT, CONTACT, MILESTONES, PROFILE, PROJECTS, STATS_SEED

HERE = Path(__file__).parent
REPO = HERE.parent.parent
OUT = REPO / "assets"
FONTS = HERE / "fonts"
SHOTS = HERE / "shots"

W = 1200          # canvas width of full-width panels
M = 12            # transparent side margin, so panels line up with the 2-up cards
X0, X1 = 56, W - 56  # content edges inside a panel


# ----------------------------------------------------------------------------- colour
def oklch(L, C, h, a=1.0):
    h = math.radians(h)
    la, lb = C * math.cos(h), C * math.sin(h)
    l_ = (L + 0.3963377774 * la + 0.2158037573 * lb) ** 3
    m_ = (L - 0.1055613458 * la - 0.0638541728 * lb) ** 3
    s_ = (L - 0.0894841775 * la - 1.2914855480 * lb) ** 3
    rgb = (
        +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def enc(c):
        c = max(0.0, min(1.0, c))
        c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return round(c * 255)

    return "#" + "".join(f"{enc(c):02x}" for c in rgb)


INK, INK2 = oklch(0.145, 0.006, 270), oklch(0.19, 0.007, 270)
BONE = oklch(0.94, 0.012, 85)
RUST, RUST_DEEP = oklch(0.68, 0.19, 40), oklch(0.58, 0.17, 38)
ON_ACCENT = oklch(0.15, 0, 0)
FG, FG_MUTED = oklch(0.95, 0.008, 85), oklch(0.72, 0.010, 85)
ON_PANEL, ON_PANEL_MUTED = oklch(0.20, 0.010, 60), oklch(0.45, 0.010, 60)

THEMES = {
    # rust_text: rust may be used as text colour on `page`/`card`/`tile` (fails on bone).
    "dark": dict(
        page=INK, card=INK2, tile=INK2, text=FG, muted=FG_MUTED, line="#ffffff", line_op=0.09,
        alt=BONE, alt_text=ON_PANEL, alt_muted=ON_PANEL_MUTED, alt_dark=False,
        rust_text=True, grain=0.07, wordmark=oklch(0.225, 0.008, 270),
    ),
    "light": dict(
        page=oklch(0.965, 0.010, 85), card=oklch(0.955, 0.012, 85), tile=oklch(0.995, 0.003, 85),
        text=ON_PANEL, muted=ON_PANEL_MUTED, line=INK, line_op=0.11,
        alt=INK, alt_text=FG, alt_muted=FG_MUTED, alt_dark=True,
        rust_text=False, grain=0.09, wordmark=oklch(0.91, 0.014, 85),
    ),
}


# ----------------------------------------------------------------------------- fonts
class Font:
    def __init__(self, key, path, wght=None):
        tt = TTFont(path)
        if wght and "fvar" in tt:
            tt = instancer.instantiateVariableFont(tt, {"wght": wght})
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        self.data = buf.getvalue()
        self.key = key
        self.tt = TTFont(io.BytesIO(self.data))
        self.upm = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.hb = hb.Font(hb.Face(self.data))
        self.cmap = self.tt.getBestCmap()
        self._paths = {}

    def shape(self, text):
        missing = [c for c in text if ord(c) not in self.cmap]
        if missing:
            raise ValueError(f"{self.key}: no glyph for {missing!r} in {text!r}")
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text, size, track=0.0):
        g = self.shape(text)
        return (sum(a for _, a, _, _ in g) + track * self.upm * (len(g) - 1)) * size / self.upm

    def path(self, gid):
        if gid not in self._paths:
            pen = SVGPathPen(self.gs, ntos=lambda v: f"{round(v)}")
            self.gs[self.order[gid]].draw(pen)
            self._paths[gid] = pen.getCommands()
        return self._paths[gid]

    def woff2_subset(self, chars):
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "tnum"]
        opts.name_IDs = []
        f = TTFont(io.BytesIO(self.data))
        s = Subsetter(opts)
        s.populate(text=chars)
        s.subset(f)
        out = io.BytesIO()
        f.flavor = "woff2"
        f.save(out)
        return base64.b64encode(out.getvalue()).decode()


SANS = Font("sans", FONTS / "Geist[wght].woff2", 400)
SANS_MED = Font("sansm", FONTS / "Geist[wght].woff2", 500)
DISPLAY = Font("disp", FONTS / "Geist[wght].woff2", 600)
MONO = Font("mono", FONTS / "GeistMono[wght].woff2", 400)
MONO_MED = Font("monom", FONTS / "GeistMono[wght].woff2", 500)
SERIF = Font("serif", FONTS / "InstrumentSerif-Italic.woff2")

DISPLAY_TRACK = -0.045
LABEL_TRACK = 0.12


def wrap(text, font, size, max_w, track=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and font.width(trial, size, track) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------------------- document
class Doc:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs, self.body, self.css = [], [], []
        self.glyphs = {}
        self._ids = 0

    def uid(self, p="e"):
        self._ids += 1
        return f"{p}{self._ids}"

    def add(self, s):
        self.body.append(s)

    def text(self, s, font, size, x, y, fill, track=0.0, anchor="start", opacity=None, cls=None, into=None):
        """Draws `s` as glyph outlines. Returns (x_start, width)."""
        w = font.width(s, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        k = size / font.upm
        pen_x, parts = 0, []
        for gid, adv, xo, yo in font.shape(s):
            if font.path(gid):
                ref = f"{font.key}{gid}"
                self.glyphs[ref] = (font, gid)
                gx, gy = x + (pen_x + xo) * k, y - yo * k
                parts.append(f'<use href="#{ref}" transform="translate({gx:.2f} {gy:.2f}) scale({k:.5f} {-k:.5f})"/>')
            pen_x += adv + track * font.upm
        attrs = f'fill="{fill}"' + (f' fill-opacity="{opacity}"' if opacity is not None else "") + (f' class="{cls}"' if cls else "")
        el = f"<g {attrs}>{''.join(parts)}</g>"
        (into if into is not None else self.body).append(el)
        return x, w

    def clip_text(self, s, font, size, x, y, track=0.0):
        """Glyph outlines as bare <use> elements, for use inside a <clipPath>."""
        k = size / font.upm
        pen_x, parts = 0, []
        for gid, adv, xo, yo in font.shape(s):
            if font.path(gid):
                ref = f"{font.key}{gid}"
                self.glyphs[ref] = (font, gid)
                parts.append(f'<use href="#{ref}" transform="translate({x + (pen_x + xo) * k:.2f} {y - yo * k:.2f}) scale({k:.5f} {-k:.5f})"/>')
            pen_x += adv + track * font.upm
        return "".join(parts)

    def render(self):
        glyph_defs = "".join(f'<path id="{ref}" d="{f.path(g)}"/>' for ref, (f, g) in sorted(self.glyphs.items()))
        css = "\n".join(self.css)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(self.title)}</title>\n<desc id="desc">{escape(self.desc)}</desc>\n'
            f"<style>{css}</style>\n"
            f"<defs>{glyph_defs}{''.join(self.defs)}</defs>\n" + "\n".join(self.body) + "\n</svg>\n"
        )


# ----------------------------------------------------------------------------- shared pieces
EASE = "cubic-bezier(.22,1,.36,1)"
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def panel(d, t, y, h, fill=None, rx=28, grain=True, border=True):
    fill = fill or t["page"]
    cid = d.uid("clip")
    d.defs.append(f'<clipPath id="{cid}"><rect x="{M}" y="{y}" width="{W - 2 * M}" height="{h}" rx="{rx}"/></clipPath>')
    d.add(f'<rect x="{M}" y="{y}" width="{W - 2 * M}" height="{h}" rx="{rx}" fill="{fill}"/>')
    if grain:
        add_grain(d, t, cid, y, h)
    if border:
        d.add(f'<rect x="{M + .5}" y="{y + .5}" width="{W - 2 * M - 1}" height="{h - 1}" rx="{rx}" fill="none" '
              f'stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>')
    return cid


def add_grain(d, t, clip_id, y, h, x=M, w=W - 2 * M, op=None):
    if "grain" not in {s.split('"')[1] for s in d.defs if s.startswith('<filter id="')}:
        d.defs.append(
            '<filter id="grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB">'
            '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1.6 -.55"/></filter>'
        )
    d.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" filter="url(#grain)" opacity="{op or t["grain"]}" '
          f'clip-path="url(#{clip_id})"/>')


def label(d, s, x, y, fill, size=17, anchor="start", font=MONO, opacity=None):
    return d.text(s.upper(), font, size, x, y, fill, LABEL_TRACK, anchor, opacity)


def arrow(d, x, y, size, color, direction="ne", width=None):
    """A drawn arrow (the fonts' latin subset has no → or ↗). (x, y) is the centre."""
    s = size / 2
    sw = width or max(1.6, size / 9)
    if direction == "e":
        p = f"M{x - s} {y} H{x + s} M{x + s * .2} {y - s * .8} L{x + s} {y} L{x + s * .2} {y + s * .8}"
    else:
        p = f"M{x - s * .8} {y + s * .8} L{x + s * .8} {y - s * .8} M{x - s * .45} {y - s * .8} H{x + s * .8} V{y + s * .45}"
    d.add(f'<path d="{p}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


def heading(d, t, parts, x, y, size, on="page", anchor_end=None):
    """Display heading in Geist with exactly one Instrument Serif Italic word.
    The serif word is rust text on dark surfaces, and a rust highlight with dark text
    on light ones (rust text fails contrast on bone)."""
    dark_surface = (on == "page" and t["rust_text"]) or (on == "alt" and t["alt_dark"])
    base = t["text"] if on == "page" else t["alt_text"]
    cx = x
    for s, kind in parts:
        if kind == "serif":
            ss = size * 1.12
            w = SERIF.width(s, ss)
            if dark_surface:
                d.text(s, SERIF, ss, cx, y, RUST)
            else:
                pad = size * 0.10
                d.add(f'<rect x="{cx - pad:.1f}" y="{y - size * .78:.1f}" width="{w + 2 * pad:.1f}" height="{size * 1.0:.1f}" '
                      f'rx="{size * .12:.1f}" fill="{RUST}"/>')
                d.text(s, SERIF, ss, cx, y, ON_ACCENT)
            cx += w
        else:
            _, w = d.text(s, DISPLAY, size, cx, y, base, DISPLAY_TRACK)
            cx += w
    return cx - x


def section_head(d, t, num, name, parts, y, right=None, on="page", size=64):
    fg = t["muted"] if on == "page" else t["alt_muted"]
    label(d, f"{num} / {name}", X0, y, fg)
    heading(d, t, parts, X0, y + 22 + size * 0.95, size, on)
    if right:
        for i, line in enumerate(right):
            label(d, line, X1, y + i * 28, fg, anchor="end")


def pulse_dot(d, x, y, r=6):
    d.css.append(f"@keyframes ping{{0%{{transform:scale(1);opacity:.8}}100%{{transform:scale(3.4);opacity:0}}}}"
                 f".ping{{animation:ping 2.2s {EASE} infinite;transform-box:fill-box;transform-origin:center}}")
    d.add(f'<circle class="ping" cx="{x}" cy="{y}" r="{r}" fill="{RUST}"/><circle cx="{x}" cy="{y}" r="{r}" fill="{RUST}"/>')


def column_lines(d, t, y0, y1, cols=12):
    gid = d.uid("fade")
    d.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["line"]}" stop-opacity="{t["line_op"]}"/>'
                  f'<stop offset="1" stop-color="{t["line"]}" stop-opacity="0"/></linearGradient>')
    step = (X1 - X0) / cols
    for i in range(cols + 1):
        x = X0 + i * step
        d.add(f'<rect x="{x - .5:.1f}" y="{y0}" width="1" height="{y1 - y0}" fill="url(#{gid})"/>')


def embed_image(path, w, h):
    im = Image.open(path).convert("RGB")
    sc = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    l, tp = (im.width - w) // 2, (im.height - h) // 2
    buf = io.BytesIO()
    im.crop((l, tp, l + w, tp + h)).save(buf, "WEBP", quality=76, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


# ----------------------------------------------------------------------------- 1. hero
def hero(t):
    H = 720
    d = Doc(W, H, PROFILE["name"], PROFILE["alt"])
    d.css += [
        f"@keyframes rise{{from{{transform:translateY(240px)}}to{{transform:none}}}}",
        f".w1{{animation:rise 1.1s {EASE} .15s both}}.w2{{animation:rise 1.1s {EASE} .24s both}}",
        f"@keyframes fade{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}",
        f".f1{{animation:fade .9s {EASE} .7s both}}.f2{{animation:fade .9s {EASE} .8s both}}.f3{{animation:fade .9s {EASE} .95s both}}",
        f"@keyframes breathe{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.035)}}}}",
        ".orb{animation:breathe 7s ease-in-out infinite;transform-box:fill-box;transform-origin:center}",
        f"@keyframes orbIn{{from{{opacity:0;transform:scale(.85)}}to{{opacity:1;transform:none}}}}",
        f".orbin{{animation:orbIn 1.2s {EASE} .3s both;transform-box:fill-box;transform-origin:center}}",
        REDUCED,
    ]
    clip = panel(d, t, 0, H, border=True)
    column_lines(d, t, 0, H * 0.8)

    ox, oy, r = 972, 312, 138
    g = d.uid("glow")
    d.defs.append(f'<radialGradient id="{g}"><stop offset="0" stop-color="{RUST}" stop-opacity=".16"/><stop offset="1" stop-color="{RUST}" stop-opacity="0"/></radialGradient>')
    d.add(f'<circle cx="{ox}" cy="{oy}" r="420" fill="url(#{g})" clip-path="url(#{clip})"/>')

    # top bar
    label(d, "Kwik Andreas — GitHub", X0, 70, t["muted"])
    label(d, PROFILE["where"], X1, 70, t["muted"], anchor="end")
    d.add(f'<rect x="{X0}" y="92" width="{X1 - X0}" height="1" fill="{t["line"]}" fill-opacity="{t["line_op"]}"/>')

    # orb + orbit (behind name in z-order so the name never gets covered)
    ring_back, ring_front = [], []
    for i, (rx, ry, rot, dur, dot) in enumerate([(206, 58, -16, 14, 7), (184, 86, 22, 22, 5)]):
        pid = d.uid("orbit")
        a = math.radians(rot)
        # Ellipse starting at its left extreme and passing through the front (lower) half
        # first, so the travelling dot can be hidden while it is "behind" the orb.
        pts = []
        for k in range(0, 361, 4):
            th = math.radians(180 - k)
            ex, ey = rx * math.cos(th), ry * math.sin(th)
            pts.append((ox + ex * math.cos(a) - ey * math.sin(a), oy + ex * math.sin(a) + ey * math.cos(a)))
        dpath = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        d.defs.append(f'<path id="{pid}" d="{dpath}"/>')
        half = len(pts) // 2
        front = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts[: half + 1])
        ring_back.append(f'<use href="#{pid}" fill="none" stroke="{t["text"]}" stroke-opacity=".14"/>')
        ring_front.append(f'<path d="{front}" fill="none" stroke="{t["text"]}" stroke-opacity=".38"/>')
        ring_front.append(
            f'<circle r="{dot}" fill="{t["text"]}"><animateMotion dur="{dur}s" repeatCount="indefinite" rotate="0">'
            f'<mpath href="#{pid}"/></animateMotion>'
            f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" values="1;1;0;0;1" keyTimes="0;.5;.56;.96;1"/></circle>'
        )
    gid = d.uid("orbshade")
    d.defs.append(f'<radialGradient id="{gid}" cx=".36" cy=".32" r=".8"><stop offset=".55" stop-color="{RUST}"/><stop offset="1" stop-color="{RUST_DEEP}"/></radialGradient>')
    oc = d.uid("orbclip")
    d.defs.append(f'<clipPath id="{oc}"><circle cx="{ox}" cy="{oy}" r="{r}"/></clipPath>')
    d.add('<g class="orbin">' + "".join(ring_back))
    d.add(f'<g class="orb"><circle cx="{ox}" cy="{oy}" r="{r}" fill="url(#{gid})"/>')
    add_grain(d, t, oc, oy - r, 2 * r, ox - r, 2 * r, op=.12)
    d.text("KA", DISPLAY, 104, ox, oy + 37, ON_ACCENT, DISPLAY_TRACK, "middle")
    d.add("</g>" + "".join(ring_front) + "</g>")

    # name: mask reveal per word
    size, lead = 184, 0.87
    for i, (word, y) in enumerate([("Kwik", 300), ("Andreas", 300 + size * lead)]):
        cid = d.uid("wclip")
        d.defs.append(f'<clipPath id="{cid}"><rect x="0" y="{y - size * .82:.0f}" width="{W}" height="{size * 1.02:.0f}"/></clipPath>')
        grp = []
        d.text(word, DISPLAY, size, X0 - 8, y, t["text"], DISPLAY_TRACK, into=grp)
        d.add(f'<g clip-path="url(#{cid})"><g class="w{i + 1}">{"".join(grp)}</g></g>')

    # tagline
    d.add('<g class="f1">')
    y = 556
    d.text("I build full-stack web apps and 3D games,", SANS, 31, X0, y, t["muted"])
    _, w = d.text("and I care about making both feel ", SANS, 31, X0, y + 42, t["muted"])
    if t["rust_text"]:
        d.text("fast.", SERIF, 36, X0 + w, y + 42, RUST)
    else:
        sw = SERIF.width("fast.", 36)
        d.add(f'<rect x="{X0 + w - 3:.1f}" y="{y + 42 - 29}" width="{sw + 8:.1f}" height="38" rx="5" fill="{RUST}"/>')
        d.text("fast.", SERIF, 36, X0 + w + 1, y + 42, ON_ACCENT)
    d.add("</g>")

    # bottom strip
    d.add(f'<rect class="f2" x="{X0}" y="{H - 82}" width="{X1 - X0}" height="1" fill="{t["line"]}" fill-opacity="{t["line_op"]}"/>')
    d.add('<g class="f3">')
    by = H - 42
    pulse_dot(d, X0 + 6, by - 6, 5)
    items = PROFILE["strip"]
    widths = [MONO.width(s.upper(), 16, LABEL_TRACK) for s in items]
    widths[0] += 22
    gap = (X1 - X0 - sum(widths)) / (len(items) - 1)
    x = X0
    for s, wd in zip(items, widths):
        label(d, s, x + (22 if s is items[0] else 0), by, t["text"] if s is items[0] else t["muted"], 16)
        x += wd + gap
    d.add("</g>")
    return d


# ----------------------------------------------------------------------------- 2. work
def work_head(t):
    d = Doc(W, 190, "Selected work", "Selected work: eight projects across web, AI, games and tools, newest first.")
    section_head(d, t, "01", "Work", [("Selected ", "sans"), ("work", "serif")], 52,
                 right=[f"{len(PROJECTS):02d} projects", "Newest first", "Click a card to open"])
    return d


CW = 600        # card canvas
CI = 12         # card inset (matches panel margin M at the same scale)


def card(t, n, p, summary_lines_max):
    x0, x1 = CI, CW - CI
    pad = 22
    img_w, img_h = x1 - x0 - 2 * pad, round((x1 - x0 - 2 * pad) * 10 / 16)
    lines = wrap(p["summary"], SANS, 22, x1 - x0 - 2 * pad)
    y_meta = pad + img_h + 46
    y_title = y_meta + 56
    y_sum = y_title + 42
    y_rule = y_sum + (summary_lines_max - 1) * 32 + 34
    H = y_rule + 58
    d = Doc(CW, H, p["title"], f'{p["title"]}: {p["summary"]} Built with {", ".join(p["stack"])}.')
    clip = d.uid("card")
    d.defs.append(f'<clipPath id="{clip}"><rect x="{x0}" y="0" width="{x1 - x0}" height="{H}" rx="26"/></clipPath>')
    d.add(f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{H}" rx="26" fill="{t["card"]}"/>')
    add_grain(d, t, clip, 0, H, x0, x1 - x0)
    d.add(f'<rect x="{x0 + .5}" y=".5" width="{x1 - x0 - 1}" height="{H - 1}" rx="26" fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>')

    ic = d.uid("img")
    ix, iy = x0 + pad, pad
    d.defs.append(f'<clipPath id="{ic}"><rect x="{ix}" y="{iy}" width="{img_w}" height="{img_h}" rx="16"/></clipPath>')
    ew = round(img_w * 1.4)  # cards display at ~0.7x, so this is ~2x on retina screens
    d.add(f'<image href="{embed_image(SHOTS / p["shot"], ew, round(ew * 10 / 16))}" x="{ix}" y="{iy}" '
          f'width="{img_w}" height="{img_h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{ic})"/>')
    d.add(f'<rect x="{ix + .5}" y="{iy + .5}" width="{img_w - 1}" height="{img_h - 1}" rx="16" fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>')

    # meta row: number chip, categories, link hint
    num = f"{n:02d}"
    nw = MONO_MED.width(num, 17, LABEL_TRACK)
    d.add(f'<rect x="{ix}" y="{y_meta - 23}" width="{nw + 24:.1f}" height="32" rx="16" fill="{RUST}"/>')
    d.text(num, MONO_MED, 17, ix + 12, y_meta - 1, ON_ACCENT, LABEL_TRACK)
    label(d, " · ".join(p["categories"]), ix + nw + 40, y_meta - 1, t["muted"])
    hint = p["hint"]
    _, hw = label(d, hint, x1 - pad - 24, y_meta - 1, t["text"], anchor="end")
    arrow(d, x1 - pad - 8, y_meta - 7, 15, t["text"])

    d.text(p["title"], DISPLAY, 40, ix, y_title, t["text"], -0.03)
    for i, ln in enumerate(lines):
        d.text(ln, SANS, 22, ix, y_sum + i * 32, t["muted"])
    d.add(f'<rect x="{ix}" y="{y_rule}" width="{img_w}" height="1" fill="{t["line"]}" fill-opacity="{t["line_op"]}"/>')
    label(d, " / ".join(p["stack"]), ix, y_rule + 36, t["muted"], 15)
    # transparent top/bottom inset, so the vertical gap between card rows matches the horizontal one
    d.body = [f'<g transform="translate(0 {CI})">'] + d.body + ["</g>"]
    d.h += 2 * CI
    return d


def work_more(t):
    H = 150
    d = Doc(W, H, "More on GitHub", "More experiments live on my GitHub repositories page.")
    panel(d, t, 0, H, fill=t["alt"], grain=True, border=False)
    label(d, "And the rest", X0, 58, t["alt_muted"])
    d.text("More experiments live on GitHub", DISPLAY, 42, X0, 108, t["alt_text"], DISPLAY_TRACK)
    d.add(f'<circle cx="{X1 - 40}" cy="{H / 2}" r="40" fill="{RUST}"/>')
    arrow(d, X1 - 40, H / 2, 24, ON_ACCENT, "e", 3)
    return d


# ----------------------------------------------------------------------------- 3. about (bento)
def about(t):
    gap, top = 16, 200
    cw = (X1 - X0 - gap) / 3
    wide, narrow = 2 * cw, cw
    pad = 34
    bio = wrap(ABOUT["bio"], SANS, 30, wide - 2 * pad)
    r1 = max(110 + len(bio) * 42, 300)
    r2 = 290
    H = top + r1 + gap + r2 + 56
    d = Doc(W, H, "About Kwik Andreas", "About: " + ABOUT["bio"])
    panel(d, t, 0, H)
    section_head(d, t, "02", "About", [("Built in ", "sans"), ("Jakarta", "serif"), (".", "sans")], 52,
                 right=["Informatics student", "Web · Game · ML"])

    def tile(x, y, w, h, alt=False):
        d.add(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="22" fill="{t["alt"] if alt else t["tile"]}"/>')
        if not alt:
            d.add(f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{w - 1:.1f}" height="{h - 1}" rx="22" fill="none" stroke="{t["line"]}" stroke-opacity="{t["line_op"]}"/>')

    xa, xb, y1, y2 = X0, X0 + wide + gap, top, top + r1 + gap
    # bio
    tile(xa, y1, wide, r1)
    label(d, "Bio", xa + pad, y1 + 50, t["muted"])
    for i, ln in enumerate(bio):
        d.text(ln, SANS, 30, xa + pad, y1 + 108 + i * 42, t["text"], -0.01)
    # education
    tile(xb, y1, narrow, r1, alt=True)
    label(d, "Education", xb + pad, y1 + 50, t["alt_muted"])
    d.text(ABOUT["edu_title"], DISPLAY, 46, xb + pad, y1 + r1 - 92, t["alt_text"], DISPLAY_TRACK)
    d.text(ABOUT["edu_school"], SANS, 22, xb + pad, y1 + r1 - 52, t["alt_muted"])
    # stack
    tile(xa, y2, wide, r2)
    label(d, "Stack", xa + pad, y2 + 50, t["muted"])
    colw = (wide - 2 * pad) / 3
    for i, (grp, items) in enumerate(ABOUT["stack"]):
        cx = xa + pad + i * colw
        label(d, grp, cx, y2 + 104, t["muted"], 14)
        d.add(f'<rect x="{cx:.1f}" y="{y2 + 118}" width="{colw - 26:.1f}" height="1" fill="{t["line"]}" fill-opacity="{t["line_op"]}"/>')
        for j, it in enumerate(items):
            d.text(it, SANS_MED, 25, cx, y2 + 160 + j * 36, t["text"], -0.01)
    # projects shipped
    tile(xb, y2, narrow, r2, alt=True)
    label(d, "Projects shipped", xb + pad, y2 + 50, t["alt_muted"])
    d.text(f"{len(PROJECTS):02d}", DISPLAY, 150, xb + pad - 6, y2 + r2 - 76, t["alt_text"], -0.06)
    d.text("and counting", SERIF, 32, xb + pad, y2 + r2 - 32, RUST if t["alt_dark"] else t["alt_muted"])
    return d


# ----------------------------------------------------------------------------- 4. milestones
def milestones(t):
    top, pad = 200, 40
    left_w = 430
    lx, rx = X0, X0 + left_w + 48
    title_x = rx + 120
    rows = []
    for m in MILESTONES["timeline"]:
        sub = wrap(m["issuer"], SANS, 20, X1 - title_x)
        rows.append((m, sub, 74 + (len(sub) - 1) * 28))
    tl_h = sum(h for *_, h in rows)
    H = top + max(tl_h, 470) + 56
    d = Doc(W, H, "Milestones", "Milestones: " + "; ".join(f'{m["year"]} {m["title"]}, {m["issuer"]}' for m in [MILESTONES["highlight"]] + MILESTONES["timeline"]))
    panel(d, t, 0, H)
    section_head(d, t, "03", "Milestones", [("Proof, not ", "sans"), ("promises", "serif"), (".", "sans")], 52,
                 right=["Awards & certificates", "2023 — 2026"])

    # highlight card
    hl = MILESTONES["highlight"]
    ch = H - top - 56
    d.add(f'<rect x="{lx}" y="{top}" width="{left_w}" height="{ch}" rx="24" fill="{t["alt"]}"/>')
    tag = f"Highlight · {hl['year']}"
    tw = MONO_MED.width(tag.upper(), 15, LABEL_TRACK)
    d.add(f'<rect x="{lx + pad}" y="{top + pad}" width="{tw + 26:.1f}" height="32" rx="16" fill="{RUST}"/>')
    label(d, tag, lx + pad + 13, top + pad + 21, ON_ACCENT, 15, font=MONO_MED)
    big = 132
    while DISPLAY.width(hl["big"], big, -0.055) > left_w - 2 * pad:
        big -= 2
    d.text(hl["big"], DISPLAY, big, lx + pad - 4, top + pad + 200, t["alt_text"], -0.055)
    d.text(hl["sub"], DISPLAY, 30, lx + pad, top + pad + 250, t["alt_text"], -0.02)
    for i, ln in enumerate(wrap(hl["body"], SANS, 21, left_w - 2 * pad)):
        d.text(ln, SANS, 21, lx + pad, top + ch - pad - 70 + i * 30, t["alt_muted"])

    # timeline
    line_x = rx + 10
    y = top + 30
    first_y, last_y = y - 8, y - 8 + tl_h - rows[-1][2]
    d.add(f'<rect x="{line_x - .5}" y="{first_y}" width="1" height="{last_y - first_y}" fill="{t["line"]}" fill-opacity="{t["line_op"] * 2.2}"/>')
    # travelling rust segment
    tid = d.uid("trail")
    d.defs.append(f'<linearGradient id="{tid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RUST}" stop-opacity="0"/><stop offset="1" stop-color="{RUST}"/></linearGradient>')
    d.add(f'<rect x="{line_x - 1}" y="{first_y}" width="2" height="70" fill="url(#{tid})">'
          f'<animate attributeName="y" values="{first_y - 70};{last_y}" dur="5s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="5s" repeatCount="indefinite"/></rect>')
    for i, (m, sub, h) in enumerate(rows):
        cy = y - 8
        if i == 0:
            pulse_dot(d, line_x, cy, 6)
        else:
            d.add(f'<circle cx="{line_x}" cy="{cy}" r="5.5" fill="{t["page"]}" stroke="{t["text"]}" stroke-opacity=".55" stroke-width="1.5"/>')
        label(d, str(m["year"]), rx + 38, y, t["muted"], 16)
        d.text(m["title"], DISPLAY, 25, title_x, y, t["text"], -0.02)
        for j, ln in enumerate(sub):
            d.text(ln, SANS, 20, title_x, y + 30 + j * 28, t["muted"])
        y += h
    return d


# ----------------------------------------------------------------------------- 5. stats (rewritten daily by today.py)
def stats(t, file_name):
    H = 350
    d = Doc(W, H, "GitHub stats", "GitHub stats for KwikAndreas: repositories, commits, stars, followers and lines of code. Updated daily.")
    panel(d, t, 0, H)
    section_head(d, t, "04", "GitHub", [("By the ", "sans"), ("numbers", "serif"), (".", "sans")], 52,
                 right=["Updated daily", "via GitHub Actions"])
    s = STATS_SEED
    cells = [  # (label, id, value, sub-line parts, width)
        ("Repositories", "repo_data", s["repo"], [("+", None), (s["contrib"], "contrib_data"), (" contributed", None)], 220),
        ("Commits", "commit_data", s["commit"], None, 210),
        ("Stars", "star_data", s["star"], None, 160),
        ("Followers", "follower_data", s["follower"], None, 180),
        ("Lines of code", "loc_data", s["loc"], [("+", None), (s["loc_add"], "loc_add"), ("  -", None), (s["loc_del"], "loc_del")], 0),
    ]
    used = sum(c[4] for c in cells)
    cells[-1] = cells[-1][:4] + (X1 - X0 - used,)
    num_chars, mono_chars = set("0123456789,"), set("0123456789,+- ")
    x, y_lab, y_num, y_sub = X0, 212, 284, 318
    for i, (lab, eid, val, sub, w) in enumerate(cells):
        if i:
            d.add(f'<rect x="{x}" y="{y_lab - 26}" width="1" height="{y_sub - y_lab + 30}" fill="{t["line"]}" fill-opacity="{t["line_op"]}"/>')
        cx = x + (0 if i == 0 else 24)
        label(d, lab, cx, y_lab, t["muted"], 15)
        d.add(f'<text class="num" x="{cx}" y="{y_num}" fill="{t["text"]}" id="{eid}">{val}</text>')
        if sub:
            spans = "".join(f'<tspan id="{sid}">{txt}</tspan>' if sid else f"<tspan>{txt}</tspan>" for txt, sid in sub)
            mono_chars |= set("".join(txt for txt, _ in sub))
            d.add(f'<text class="sub" x="{cx}" y="{y_sub}" fill="{t["muted"]}">{spans}</text>')
        x += w
    num_font = DISPLAY.woff2_subset("".join(sorted(num_chars)))
    mono_font = MONO.woff2_subset("".join(sorted(mono_chars | set("abcdefghijklmnopqrstuvwxyz"))))
    d.css += [
        f"@font-face{{font-family:'GeistNum';src:url(data:font/woff2;base64,{num_font}) format('woff2')}}",
        f"@font-face{{font-family:'GeistMonoNum';src:url(data:font/woff2;base64,{mono_font}) format('woff2')}}",
        ".num{font:64px 'GeistNum',sans-serif;letter-spacing:-2.6px;font-variant-numeric:tabular-nums}",
        ".sub{font:15px 'GeistMonoNum',monospace;letter-spacing:.6px}",
    ]
    return d


# ----------------------------------------------------------------------------- 6. contact
def contact(t):
    H = 470
    d = Doc(W, H, "Contact", f"Contact Kwik Andreas: {CONTACT['email']}")
    panel(d, t, 0, H, fill=t["alt"], rx=32, border=False)
    label(d, "05 / Contact", X0, 70, t["alt_muted"])
    pulse_dot(d, X1 - MONO.width("AVAILABLE FOR WORK", 17, LABEL_TRACK) - 22, 64, 5)
    label(d, "Available for work", X1, 70, t["alt_text"], anchor="end")
    heading(d, t, [("Let's build something ", "sans"), ("together", "serif"), (".", "sans")], X0, 170, 64, on="alt")
    email = CONTACT["email"]
    size = 96
    while DISPLAY.width(email, size, -0.04) > X1 - X0:
        size -= 1
    d.text(email, DISPLAY, size, X0 - 3, 330, t["alt_text"], -0.04)
    d.add(f'<rect x="{X0}" y="352" width="{DISPLAY.width(email, size, -0.04):.1f}" height="3" fill="{t["alt_text"]}"/>')
    label(d, "Click to write me an email", X0, 420, t["alt_muted"])
    d.add(f'<circle cx="{X1 - 30}" cy="413" r="30" fill="{RUST}"/>')
    arrow(d, X1 - 30, 413, 20, ON_ACCENT, "ne", 2.6)
    return d


# ----------------------------------------------------------------------------- 7. footer wordmark
def footer(t):
    H = 300
    d = Doc(W, H, "Kwik Andreas", "Kwik Andreas wordmark.")
    clip = panel(d, t, 0, H)
    label(d, f"© {PROFILE['year']} Kwik Andreas", X0, 64, t["muted"])
    label(d, "Built by hand, in Geist", W / 2, 64, t["muted"], anchor="middle")
    label(d, "Back to top ↑", X1, 64, t["muted"], anchor="end")
    word = "Kwik Andreas"
    size = 300
    while DISPLAY.width(word, size, -0.05) > X1 - X0 + 10:
        size -= 2
    y = H + size * 0.16
    d.text(word, DISPLAY, size, X0 - 6, y, t["wordmark"], -0.05)
    wid = d.uid("wm")
    d.defs.append(f'<clipPath id="{wid}">{d.clip_text(word, DISPLAY, size, X0 - 6, y, -0.05)}</clipPath>')
    gid = d.uid("light")
    d.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="{RUST}" stop-opacity=".95"/><stop offset=".55" stop-color="{RUST}" stop-opacity=".35"/><stop offset="1" stop-color="{RUST}" stop-opacity="0"/></radialGradient>')
    d.add(f'<g clip-path="url(#{wid})"><g clip-path="url(#{clip})"><circle cx="0" cy="{H - 40}" r="210" fill="url(#{gid})">'
          f'<animate attributeName="cx" values="{X0 + 60};{X1 - 60};{X0 + 60}" dur="14s" repeatCount="indefinite" calcMode="spline" '
          f'keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle></g></g>')
    return d


# ----------------------------------------------------------------------------- build
def write(d, name):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(d.render(), encoding="utf-8")
    return path


def main():
    sizes = {}
    lines_max = max(len(wrap(p["summary"], SANS, 22, CW - 2 * CI - 44)) for p in PROJECTS)
    for theme, t in THEMES.items():
        out = [
            write(hero(t), f"hero-{theme}.svg"),
            write(work_head(t), f"work-{theme}.svg"),
            *[write(card(t, i + 1, p, lines_max), f"work/{p['slug']}-{theme}.svg") for i, p in enumerate(PROJECTS)],
            write(work_more(t), f"work-more-{theme}.svg"),
            write(about(t), f"about-{theme}.svg"),
            write(milestones(t), f"milestones-{theme}.svg"),
            write(contact(t), f"contact-{theme}.svg"),
            write(footer(t), f"footer-{theme}.svg"),
        ]
        stats_path = REPO / f"{theme}_mode.svg"
        stats_path.write_text(stats(t, stats_path.name).render(), encoding="utf-8")
        out.append(stats_path)
        for p in out:
            sizes[p.relative_to(REPO).as_posix()] = p.stat().st_size // 1024
    for k, v in sizes.items():
        print(f"{v:5d} KB  {k}")


if __name__ == "__main__":
    main()
