"""Small SVG toolkit for the sticker-board profile cards.

Everything here is plain string building: no dependencies beyond fontTools
(used to measure text so chips and highlights fit their words exactly).
"""
from __future__ import annotations

import base64
import functools
import html
import io
import json
import math
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "fonts"
TOKENS = json.loads((ROOT / "tokens.json").read_text())

FONTS = {
    "display": ("Fredoka", 500, "fredoka-latin-500-normal.woff2"),
    "display-bold": ("Fredoka", 700, "fredoka-latin-700-normal.woff2"),
    "mono": ("DM Mono", 400, "dm-mono-latin-400-normal.woff2"),
    "mono-bold": ("DM Mono", 500, "dm-mono-latin-500-normal.woff2"),
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


@functools.lru_cache(maxsize=None)
def _font(key: str):
    _, _, file = FONTS[key]
    f = TTFont(FONT_DIR / file)
    return f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm


@functools.lru_cache(maxsize=None)
def _subset_b64(key: str, chars: str) -> str:
    """Embed only the glyphs this card uses (keeps each SVG small)."""
    from fontTools import subset
    font = TTFont(FONT_DIR / FONTS[key][2])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    sub = subset.Subsetter(opts)
    sub.populate(text=chars + "?.")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def text_width(text: str, key: str, size: float, tracking: float = 0) -> float:
    cmap, hmtx, upem = _font(key)
    total = 0
    for ch in str(text):
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        total += hmtx[g][0]
    return total * size / upem + tracking * size * max(len(str(text)) - 1, 0)


def fit(text: str, key: str, size: float, max_w: float) -> str:
    """Trim text with an ellipsis-like '...' so it fits max_w."""
    text = str(text)
    if text_width(text, key, size) <= max_w:
        return text
    while text and text_width(text + "...", key, size) > max_w:
        text = text[:-1]
    return text.rstrip() + "..."


def fit_size(text: str, key: str, size: float, max_w: float, floor: float, tracking: float = 0) -> float:
    """Largest font size (down to floor) at which text fits max_w."""
    while size > floor and text_width(text, key, size, tracking) > max_w:
        size -= 1
    return size


def wrap(text: str, key: str, size: float, max_w: float, max_lines: int = 3) -> list[str]:
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_width(trial, key, size) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(lines[-1] + " ...", key, size, max_w)
    return lines


def flow(labels: list[str], x: float, y: float, max_w: float, font: str = "mono-bold",
         size: float = 11, pad: float = 8, h: float = 22, gap: float = 8, row_gap: float = 8):
    """Lay chips out left to right, wrapping onto new rows. Returns (placements, bottom_y)."""
    placed, cx, cy = [], x, y
    for label in labels:
        w = text_width(label, font, size) + pad * 2
        if cx > x and cx + w > x + max_w:
            cx, cy = x, cy + h + row_gap
        placed.append((cx, cy, label, w))
        cx += w + gap
    return placed, (cy + h if labels else y)


class Theme:
    def __init__(self, mode: str):
        self.mode = mode
        self.c = TOKENS["color"][mode]

    def __getitem__(self, k: str) -> str:
        return self.c[k]


class Svg:
    """Collects elements, then wraps them with fonts, styles and a dot grid."""

    def __init__(self, w: int, h: int, theme: Theme, title: str):
        self.w, self.h, self.t, self.title = w, h, theme, title
        self.parts: list[str] = []
        self.used_fonts: dict[str, set[str]] = {}

    def add(self, s: str):
        self.parts.append(s)
        return self

    def text(self, x, y, s, size=16, font="display", fill=None, anchor="start",
             tracking=0.0, opacity=1.0):
        self.used_fonts.setdefault(font, set()).update(str(s))
        fam, weight, _ = FONTS[font]
        ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ""
        op = f' opacity="{opacity}"' if opacity != 1 else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill or self.t["text"]}" text-anchor="{anchor}"{ls}{op}>'
            f"{esc(s)}</text>"
        )

    def sticker(self, x, y, w, h, fill, r=14, shadow=4, stroke=2, tilt=0.0,
                shadow_fill=None, inner: str = ""):
        """A card with an ink outline and a hard offset shadow."""
        line = self.t["line"]
        cx, cy = x + w / 2, y + h / 2
        tf = f' transform="rotate({tilt} {cx:.1f} {cy:.1f})"' if tilt else ""
        self.add(
            f"<g{tf}>"
            f'<rect x="{x + shadow:.1f}" y="{y + shadow:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{shadow_fill or line}"/>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" stroke="{line}" stroke-width="{stroke}"/>'
            f"{inner}</g>"
        )

    def chip(self, x, y, label, fill, size=11, font="mono-bold", color=None, pad=8, h=22):
        """Small label pill. Returns its width so callers can lay chips out in a row."""
        w = text_width(label, font, size) + pad * 2
        line = self.t["line"]
        self.add(
            f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{w:.1f}" height="{h}" rx="6" fill="{line}"/>'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="6" fill="{fill}" stroke="{line}" stroke-width="1.5"/>'
        )
        self.text(x + pad, y + h / 2 + size * 0.36, label, size, font, color or self.t["text"])
        return w

    def chips(self, x, y, labels_fills, gap=8, **kw):
        for label, fill in labels_fills:
            x += self.chip(x, y, label, fill, **kw) + gap
        return x

    def board(self, x=0, y=0, w=None, h=None, r=18):
        """The dotted 'paper' panel every card sits on."""
        w = w if w is not None else self.w
        h = h if h is not None else self.h
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{self.t["bg"]}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#dots)"/>'
        )

    def render(self) -> str:
        faces = "".join(
            f'@font-face{{font-family:"{FONTS[k][0]}";font-weight:{FONTS[k][1]};'
            f'src:url(data:font/woff2;base64,{_subset_b64(k, "".join(sorted(chars)))}) format("woff2");}}'
            for k, chars in sorted(self.used_fonts.items())
        )
        dot = self.t["muted"]
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h:.0f}" '
            f'viewBox="0 0 {self.w} {self.h:.0f}" xml:space="preserve" role="img" aria-label="{esc(self.title)}">'
            f"<title>{esc(self.title)}</title>"
            f"<defs><style>{faces}text{{font-kerning:normal;white-space:pre}}</style>"
            f'<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">'
            f'<circle cx="2" cy="2" r="1.1" fill="{dot}" opacity="{0.16 if self.t.mode == "dark" else 0.22}"/></pattern>'
            f"</defs>" + "".join(self.parts) + "</svg>"
        )


def icon(name: str, x: float, y: float, s: float, ink: str, fill: str, accent: str) -> str:
    """Tiny hand-drawn icons in a 24x24 box."""
    k = s / 24
    g = f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.3f})" stroke="{ink}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round">'
    body = {
        "calendar": f'<rect x="3" y="5" width="18" height="16" rx="3" fill="{fill}"/><path d="M3 10h18" fill="none"/><path d="M8 3v4M16 3v4" fill="none"/><rect x="7" y="13" width="4" height="4" rx="1" fill="{accent}"/>',
        "flame": f'<path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-7 0 2 1 3 2 3 0-3 0-5 1-8z" fill="{accent}"/>',
        "trophy": f'<path d="M7 4h10v5a5 5 0 0 1-10 0z" fill="{accent}"/><path d="M7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4" fill="none"/><path d="M12 14v4M8 21h8M9 18h6" fill="none"/>',
        "bars": f'<rect x="4" y="12" width="4" height="9" rx="1" fill="{fill}"/><rect x="10" y="7" width="4" height="14" rx="1" fill="{accent}"/><rect x="16" y="3" width="4" height="18" rx="1" fill="{fill}"/>',
        "folder": f'<path d="M3 6a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" fill="{accent}"/>',
        "star": f'<path d="M12 3l2.8 5.8 6.2.9-4.5 4.4 1 6.3L12 17.4 6.5 20.4l1-6.3L3 9.7l6.2-.9z" fill="{accent}"/>',
        "people": f'<circle cx="9" cy="8" r="3.5" fill="{accent}"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0z" fill="{accent}"/><circle cx="17" cy="9" r="2.8" fill="{fill}"/><path d="M15 14.5a5 5 0 0 1 6.5 5.5H17" fill="{fill}"/>',
        "wheel": f'<circle cx="12" cy="12" r="9" fill="{accent}"/><circle cx="12" cy="12" r="3" fill="{fill}"/>'
                 + "".join(f'<path d="M{12 + 3 * math.cos(a):.2f} {12 + 3 * math.sin(a):.2f}L{12 + 9 * math.cos(a):.2f} {12 + 9 * math.sin(a):.2f}" fill="none"/>'
                           for a in [i * 2 * math.pi / 7 - math.pi / 2 for i in range(7)]),
        "cloud": f'<path d="M7 19a5 5 0 0 1-.5-10A6 6 0 0 1 18 8a4.5 4.5 0 0 1-.5 11z" fill="{accent}"/>',
        "network": f'<path d="M12 6v5M12 11L6 17M12 11l6 6" fill="none"/><rect x="9" y="2" width="6" height="5" rx="1.5" fill="{accent}"/><rect x="3" y="16" width="6" height="5" rx="1.5" fill="{fill}"/><rect x="15" y="16" width="6" height="5" rx="1.5" fill="{fill}"/>',
        "pulse": f'<rect x="2" y="4" width="20" height="16" rx="3" fill="{fill}"/><path d="M5 13h3l2-5 3 9 2-4h4" fill="none" stroke="{accent}" stroke-width="2.4"/>',
        "pipeline": f'<circle cx="5" cy="12" r="3" fill="{accent}"/><circle cx="19" cy="12" r="3" fill="{fill}"/><rect x="9.5" y="9" width="5" height="6" rx="1.5" fill="{accent}"/><path d="M8 12h1.5M14.5 12H16" fill="none"/>',
        "shield": f'<path d="M12 2l8 3v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V5z" fill="{accent}"/><path d="M8.5 12l2.5 2.5 4.5-5" fill="none"/>',
        "repo": f'<path d="M5 4a2 2 0 0 1 2-2h12v17H7a2 2 0 0 0-2 2z" fill="{accent}"/><path d="M5 21a2 2 0 0 1 2-2h12v3H7a2 2 0 0 1-2-1z" fill="{fill}"/>',
        "terminal": f'<rect x="2" y="4" width="20" height="16" rx="3" fill="{fill}"/><path d="M6 9l3 3-3 3M11 15h6" fill="none" stroke="{accent}" stroke-width="2.4"/>',
        "arrow": f'<rect x="2" y="2" width="20" height="20" rx="5" fill="{accent}"/><path d="M8 16L16 8M10 8h6v6" fill="none"/>',
        "linkedin": f'<rect x="2" y="2" width="20" height="20" rx="4" fill="{accent}"/><path d="M7 10v7M7 7v.01M11 17v-7M11 13a3 3 0 0 1 6 0v4" fill="none" stroke="{fill}" stroke-width="2.4"/>',
        "mail": f'<rect x="2" y="5" width="20" height="14" rx="3" fill="{accent}"/><path d="M5 8.5l7 5 7-5" fill="none" stroke="{fill}" stroke-width="2.2"/>',
        "globe": f'<circle cx="12" cy="12" r="10" fill="{accent}"/><path d="M3 12h18M12 3c3.2 3 3.2 15 0 18M12 3c-3.2 3-3.2 15 0 18" fill="none" stroke="{fill}" stroke-width="1.8"/>',
        "github": f'<circle cx="12" cy="12" r="10" fill="{accent}"/><path d="M9 19v-3a3 3 0 0 1 .8-2.2C7 13.4 6 12 6 10a4 4 0 0 1 1-2.6 3.5 3.5 0 0 1 .1-2.4s1 0 2.6 1a8 8 0 0 1 4.6 0c1.6-1 2.6-1 2.6-1a3.5 3.5 0 0 1 .1 2.4A4 4 0 0 1 18 10c0 2-1 3.4-3.8 3.8A3 3 0 0 1 15 16v3" fill="none" stroke="{fill}" stroke-width="1.8"/>',
        "code": f'<rect x="2" y="2" width="20" height="20" rx="4" fill="{accent}"/><path d="M9.5 8L5.5 12l4 4M14.5 8l4 4-4 4" fill="none" stroke="{fill}" stroke-width="2.2"/>',
        "stack": f'<rect x="2" y="2" width="20" height="20" rx="4" fill="{accent}"/><path d="M6 13.5V18h12v-4.5M9 15.8h6M9.2 12.6l5.8.6M10.1 9.6l5.5 1.7M11.6 6.8l4.9 3" fill="none" stroke="{fill}" stroke-width="1.7"/>',
        "layers": f'<path d="M3 16.5l9 4.5 9-4.5" fill="none"/><path d="M3 12l9 4.5 9-4.5" fill="none"/><path d="M12 3l9 4.5-9 4.5-9-4.5z" fill="{accent}"/>',
        "payment": f'<rect x="2" y="5" width="20" height="14" rx="3" fill="{fill}"/><path d="M2 10h20" fill="none" stroke-width="2.6"/><rect x="5" y="13.5" width="6" height="2.5" rx="1" fill="{accent}"/>',
        "scales": f'<path d="M12 3v17M7 21h10M5 6h14" fill="none"/><path d="M2 12l3-6 3 6a3 3 0 0 1-6 0z" fill="{accent}"/><path d="M16 12l3-6 3 6a3 3 0 0 1-6 0z" fill="{accent}"/>',
        "cap": f'<path d="M6 11v5c0 1.7 2.7 3 6 3s6-1.3 6-3v-5" fill="{fill}"/><path d="M12 4L2 9l10 5 10-5z" fill="{accent}"/><path d="M21 9v6" fill="none"/>',
        "chart": f'<rect x="3" y="3" width="18" height="18" rx="3" fill="{fill}"/><path d="M7 15l3-4 3 2 4-6" fill="none" stroke="{accent}" stroke-width="2.4"/>',
        "bug": f'<rect x="7" y="8" width="10" height="12" rx="5" fill="{accent}"/><path d="M9 8a3 3 0 0 1 6 0" fill="{fill}"/><path d="M12 11v8M3 13h4M17 13h4M4 8l3 2M20 8l-3 2M4 19l3-2M20 19l-3-2" fill="none"/>',
        "bolt": f'<path d="M13 2L4 14h7l-1 8 9-12h-7z" fill="{accent}"/>',
        "briefcase": f'<rect x="2" y="7" width="20" height="13" rx="3" fill="{accent}"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M2 12.5h20" fill="none"/>',
        "sparkle": f'<path d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2z" fill="{accent}"/>',
        "medal": f'<path d="M8 2l3 7M16 2l-3 7" fill="none"/><circle cx="12" cy="15" r="6.5" fill="{accent}"/><circle cx="12" cy="15" r="2.6" fill="{fill}"/>',
    }.get(name)
    if body is None:
        body = f'<rect x="3" y="3" width="18" height="18" rx="4" fill="{accent}"/>'
    return g + body + "</g>"
