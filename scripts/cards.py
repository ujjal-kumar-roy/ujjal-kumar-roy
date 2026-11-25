"""Every card on the profile. Each function returns (svg_markup, alt_text)."""
from __future__ import annotations

import datetime as dt
import math

from svgkit import Svg, Theme, fit, fit_size, flow, icon, text_width, wrap

W = 900
PALETTE = ["blue", "green", "amber", "purple", "teal", "red"]
TILTS = [-1.0, 0.8, -0.6, 1.0, -0.8, 0.6]


def _date(d: dt.date) -> str:
    return f"{d.day} {d:%b %Y}"


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def hero(t: Theme, p: dict, data: dict, st: dict):
    x0, base = 164, 98
    name = p.get("display_name", p["name"])
    corner = p.get("corner", "")
    dot = 14 if corner and p.get("corner_dot") else 0
    cw = text_width(corner, "display-bold", 16) + 28 + dot if corner else 0
    right = W - 32 - cw - 18 if corner else W - 32
    hi = "Hi, I'm "
    size = fit_size(hi + name, "display-bold", 46, right - x0 - 14, 30, -0.03)
    lines = wrap(p["tagline"], "display", 17, W - x0 - 48, max_lines=3)
    h = 196 + (len(lines) - 1) * 24
    alt = p.get("hero_alt") or f"Hi, I'm {name}. {p['tagline']}"
    s = Svg(W, h, t, alt)
    s.board()

    s.sticker(32, 40, 104, 104, t["card"], r=20, shadow=6, stroke=2.5, shadow_fill=t["pop"])
    isz = fit_size(p["initials"], "display-bold", 46, 84, 28, -0.03)
    s.text(84, 92 + isz * 0.37, p["initials"], isz, "display-bold", t["text"], anchor="middle", tracking=-0.03)

    s.text(x0, base, hi, size, "display-bold", tracking=-0.03)
    nx = x0 + text_width(hi, "display-bold", size, -0.03)
    nw = text_width(name, "display-bold", size, -0.03)
    s.add(f'<rect x="{nx - 6:.1f}" y="{base - size * 0.913:.1f}" width="{nw + 14:.1f}" '
          f'height="{size * 1.174:.1f}" rx="8" fill="{t["red"]}"/>')
    s.text(nx, base, name, size, "display-bold", tracking=-0.03)

    y = base + 32
    for ln in lines:
        s.text(x0, y, ln, 17, "display", t["text"])
        y += 24
    s.chips(x0, y - 6, [(tag, t[PALETTE[i % len(PALETTE)]]) for i, tag in enumerate(p["tags"])], size=11)

    if corner:
        cx = W - 32 - cw
        s.sticker(cx, 26, cw, 36, t[p.get("corner_color", "pop")], r=10, shadow=3, tilt=3)
        s.add(f'<g transform="rotate(3 {cx + cw / 2:.1f} 44)">')
        if dot:
            s.add(f'<circle cx="{cx + 17:.1f}" cy="44.5" r="4.5" fill="{t["on-pop"]}">'
                  f'<animate attributeName="opacity" values="1;0.25;1" dur="1.8s" repeatCount="indefinite"/></circle>')
        s.text(cx + (cw + dot) / 2, 50, corner, 16, "display-bold", t["on-pop"], anchor="middle")
        s.add("</g>")
    return s.render(), alt


def badge(t: Theme, link: dict, login: str):
    label, handle = link["label"], link.get("handle", "").replace("{login}", login)
    lw = text_width(label, "display-bold", 18)
    hw = text_width(handle, "mono", 15) if handle else 0
    w = int(16 + 26 + 10 + lw + (12 + hw if handle else 0) + 18 + 6)
    alt = link.get("alt") or f"{label} {handle}".strip()
    s = Svg(w, 50, t, alt)
    fill = t[link.get("color", "blue")]
    s.sticker(2, 2, w - 8, 42, fill, r=10, shadow=4)
    s.add(icon(link["kind"], 16, 12, 22, t["line"], fill, t["line"]))
    s.text(48, 30, label, 18, "display-bold")
    if handle:
        s.text(48 + lw + 12, 29, handle, 15, "mono", t["text"])
    return s.render(), alt


def label(t: Theme, title: str, chip: str, color: str):
    s = Svg(W, 64, t, title)
    w = text_width(title, "display-bold", 22) + 28
    s.sticker(8, 12, w, 40, t[color], r=10, tilt=-2)
    s.add(f'<g transform="rotate(-2 {8 + w / 2:.1f} 32)">')
    s.text(8 + 14, 40, title, 22, "display-bold", tracking=-0.02)
    s.add("</g>")
    if chip:
        s.chip(8 + w + 18, 21, chip, t["card"], size=11)
    return s.render(), title


def whoami(t: Theme, term: dict):
    lh, x_max = 22, W - 56
    rows = []
    for b in term["blocks"]:
        rows.append(("cmd", b["cmd"]))
        x = 58 if b.get("arrows") else 40
        for ln in b["lines"]:
            if b.get("bold_first") and "  ·  " in ln:
                rows.append(("bold", x, ln, False))
                continue
            for j, part in enumerate(wrap(ln, "mono", 14, x_max - x, max_lines=4)):
                rows.append(("line", x, part, bool(b.get("arrows")) and j == 0))
        rows.append(("gap",))
    y_end = 92 + sum(10 if r[0] == "gap" else lh for r in rows)
    h = y_end + 64
    alt = term.get("alt") or "; ".join(f"{b['cmd']}: " + ". ".join(b["lines"]) for b in term["blocks"])
    s = Svg(W, h, t, alt)
    s.board()
    s.sticker(20, 20, W - 44, h - 44, t["screen"], r=14)
    for i, c in enumerate([t["pop"], "#ffbd2e", t["go"]]):
        s.add(f'<circle cx="{40 + i * 16}" cy="40" r="5" fill="{c}"/>')
    s.text((W - 4) / 2, 44, f"{term['host']}: ~", 12, "mono", t["on-screen-muted"], anchor="middle")
    s.add(f'<path d="M21 58H{W - 25}" stroke="{t["on-screen-muted"]}" stroke-opacity="0.25"/>')

    y = 92
    for r in rows:
        if r[0] == "gap":
            y += 10
            continue
        if r[0] == "cmd":
            s.text(40, y, "$", 14, "mono-bold", t["pop"])
            s.text(58, y, r[1], 14, "mono-bold", t["on-screen"])
        else:
            _, x, ln, arrow = r
            if arrow:
                s.add(f'<path d="M41 {y - 5}h9m-4 -4l4 4-4 4" fill="none" stroke="{t["go"]}" stroke-width="1.8" '
                      f'stroke-linecap="round" stroke-linejoin="round"/>')
            if r[0] == "bold":
                first, rest = ln.split("  ·  ", 1)
                s.text(x, y, first, 14, "mono-bold", t["on-screen"])
                s.text(x + text_width(first, "mono-bold", 14), y, "  ·  " + rest, 14, "mono", t["on-screen"])
            else:
                s.text(x, y, ln, 14, "mono", t["on-screen"])
        y += lh
    s.text(40, y, "$", 14, "mono-bold", t["pop"])
    s.add(f'<rect x="58" y="{y - 13}" width="9" height="17" fill="{t["on-screen"]}">'
          f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></rect>')
    return s.render(), alt


def tiles(t: Theme, items: list[dict], cols: int = 3, alt_prefix: str = ""):
    gap, rgap = 16, 20
    tw = (W - 56 - (cols - 1) * gap) / cols
    labels = [wrap(it["label"], "mono", 12, tw - 32, max_lines=3) for it in items]
    th = 72 + max(len(l) for l in labels) * 16
    rows = math.ceil(len(items) / cols)
    h = 28 + rows * th + (rows - 1) * rgap + 30
    alt = alt_prefix + "; ".join(f"{it['value']} {it['label']}" for it in items) + "."
    s = Svg(W, h, t, alt)
    s.board()
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        in_row = min(cols, len(items) - r * cols)
        x = 28 + (cols - in_row) * (tw + gap) / 2 + c * (tw + gap)
        y = 28 + r * (th + rgap)
        tilt = TILTS[i % len(TILTS)]
        inner = icon(it.get("icon", "star"), x + tw - 40, y + 14, 24, t["line"], t["card"], t["pop"])
        s.sticker(x, y, tw, th, t[it.get("color") or PALETTE[i % len(PALETTE)]], tilt=tilt, inner=inner)
        s.add(f'<g transform="rotate({tilt} {x + tw / 2:.1f} {y + th / 2:.1f})">')
        s.text(x + 16, y + 46, it["value"], 30, "display-bold", tracking=-0.02)
        for k, ln in enumerate(labels[i]):
            s.text(x + 16, y + 70 + k * 16, ln, 12, "mono")
        s.add("</g>")
    return s.render(), alt


def snapshot(t: Theme, rows: list[dict], title: str = "Snapshot"):
    kx, vx = 48, 248
    vw = W - 52 - vx
    laid, ry = [], 44
    for r in rows:
        lines = wrap(r["value"], "display", 15, vw, max_lines=4)
        bottom = max(ry + 24, ry + 17 + (len(lines) - 1) * 21 + 6)
        laid.append((ry, r["key"], lines, bottom))
        ry = bottom + 21
    inner_bottom = laid[-1][3] + 24
    h = inner_bottom + 24
    alt = f"{title}. " + "; ".join(f"{r['key']}: {r['value']}" for r in rows) + "."
    s = Svg(W, h, t, alt)
    s.board()
    s.sticker(20, 20, W - 44, inner_bottom - 20, t["card"], r=16)
    for i, (ry, key, lines, bottom) in enumerate(laid):
        s.chip(kx, ry, key, t[PALETTE[i % len(PALETTE)]], size=11, h=24)
        for k, ln in enumerate(lines):
            s.text(vx, ry + 17 + k * 21, ln, 15, "display")
        if i < len(laid) - 1:
            sy = bottom + 10.5
            s.add(f'<path d="M{kx} {sy:.1f}H{W - 48}" stroke="{t["muted"]}" stroke-opacity="0.3" stroke-dasharray="3 5"/>')
    return s.render(), alt


CARD_W = 440


def card_layout(items: list[dict]) -> dict:
    lines = max(len(wrap(c["desc"], "display", 15, CARD_W - 28 - 32, max_lines=4)) for c in items)
    return {"lines": lines, "impact": any(c.get("impact") for c in items),
            "tags": any(c.get("tags") for c in items), "footer": any(c.get("footer") for c in items)}


def _card_rows(lay: dict, y: float):
    cur = y + 92 + (lay["lines"] - 1) * 20 + 6
    impact_y = tags_y = footer_y = None
    if lay["impact"]:
        impact_y, cur = cur + 10, cur + 32
    if lay["tags"]:
        tags_y, cur = cur + 10, cur + 30
    if lay["footer"]:
        footer_y = cur + 24
        return impact_y, tags_y, footer_y, footer_y + 14
    return impact_y, tags_y, footer_y, cur + 16


def card(t: Theme, c: dict, i: int, linked: bool = False, lay: dict | None = None):
    lay = lay or card_layout([c])
    x, y, w = 12, 12, CARD_W - 28
    impact_y, tags_y, footer_y, bottom = _card_rows(lay, y)
    h = bottom - y
    alt = c.get("alt") or (f"{c['title']}: {c['desc']}" + (f" Impact: {c['impact']}." if c.get("impact") else ""))
    s = Svg(CARD_W, h + 28, t, alt)
    s.board(r=18)
    fill = t[c.get("color") or PALETTE[i % len(PALETTE)]]
    s.sticker(x, y, w, h, fill, r=16)

    s.sticker(x + 16, y + 16, 48, 48, t["card"], r=12, shadow=3)
    s.add(icon(c.get("icon", "repo"), x + 26, y + 26, 28, t["line"], t["card"], t["pop"]))
    if linked:
        s.add(icon("arrow", x + w - 36, y + 14, 22, t["line"], t["card"], t["pop"]))

    title_max = w - 80 - (40 if linked else 16)
    tsize = fit_size(c["title"], "display-bold", 22, title_max, 18, -0.02)
    s.text(x + 78, y + 38, fit(c["title"], "display-bold", tsize, title_max), tsize, "display-bold", tracking=-0.02)
    if c.get("status"):
        s.chip(x + 78, y + 46, c["status"], t["go"], size=10, color=t["on-pop"], h=19, pad=7)

    for k, ln in enumerate(wrap(c["desc"], "display", 15, w - 32, max_lines=lay["lines"])):
        s.text(x + 16, y + 92 + k * 20, ln, 15, "display")
    if c.get("impact") and impact_y is not None:
        cw = s.chip(x + 16, impact_y, "impact", t["pop"], size=10, color=t["on-pop"], h=22, pad=7)
        s.text(x + 16 + cw + 10, impact_y + 15.5, fit(c["impact"], "display-bold", 14, w - 32 - cw - 10),
               14, "display-bold")
    if c.get("tags") and tags_y is not None:
        tx, room = x + 16, w - 32
        for tag in c["tags"]:
            tw = text_width(tag, "mono-bold", 10) + 14
            if tx + tw > x + 16 + room:
                break
            tx += s.chip(tx, tags_y, tag, t["card"], size=10, h=20, pad=7) + 6
    if c.get("footer") and footer_y is not None:
        s.text(x + 16, footer_y, fit(c["footer"], "mono", 12, w - 32), 12, "mono", t["text"], opacity=0.85)
    return s.render(), alt


def repo_card_data(r: dict, login: str) -> dict:
    lang = (r.get("primaryLanguage") or {}).get("name")
    tags = [x for x in [lang, _plural(r["stargazerCount"], "star"), _plural(r["forkCount"], "fork")] if x]
    return {
        "title": r["name"],
        "desc": r.get("description") or "No description yet.",
        "status": "open source",
        "icon": "repo",
        "tags": tags,
        "footer": f"github.com/{login}/{r['name']}",
        "url": r["url"],
    }


def chipboard(t: Theme, groups: list[dict], title: str = "Tech stack"):
    x0, mw = 48, W - 96
    y, laid, bottom = 60, [], 60
    for g in groups:
        placed, bottom = flow(g["items"], x0, y + 16, mw, font="mono-bold", size=12, pad=10, h=26, gap=8, row_gap=10)
        laid.append((y, g, placed))
        y = bottom + 42
    inner_bottom = bottom + 28
    h = inner_bottom + 24
    alt = f"{title}. " + "; ".join(f"{g['title']}: {', '.join(g['items'])}" for g in groups) + "."
    s = Svg(W, h, t, alt)
    s.board()
    s.sticker(20, 20, W - 44, inner_bottom - 20, t["card"], r=16)
    for gi, (ty, g, placed) in enumerate(laid):
        s.text(x0, ty, g["title"], 17, "display-bold", tracking=-0.01)
        if g.get("note"):
            s.text(x0 + text_width(g["title"], "display-bold", 17, -0.01) + 10, ty - 1, g["note"], 12, "mono", t["muted"])
        fill = t[g.get("color") or PALETTE[gi % len(PALETTE)]]
        for cx, cy, lab, _ in placed:
            s.chip(cx, cy, lab, fill, size=12, h=26, pad=10)
    return s.render(), alt


def timeline(t: Theme, items: list[dict], title: str = "Experience"):
    lx, lw, rx = 48, 196, 286
    rw = W - 50 - rx
    y, laid = 24, []
    for it in items:
        company = wrap(it["company"], "display-bold", 18, lw, max_lines=3)
        role_y = y + 72 + (len(company) - 1) * 22 + 24
        desc = wrap(it["desc"], "display", 15, rw, max_lines=8)
        last = y + 46 + (len(desc) - 1) * 21
        placed, chips_bottom = flow(it.get("tags", []), rx, last + 16, rw, size=10, pad=7, h=20, gap=6, row_gap=6)
        bottom = max(role_y + 8, chips_bottom) + 22
        laid.append((y, it, company, role_y, desc, placed, bottom))
        y = bottom + 22
    h = laid[-1][6] + 30
    alt = f"{title}. " + "; ".join(f"{it['role']} at {it['company']} ({it['dates']}): {it['desc']}" for it in items)
    s = Svg(W, h, t, alt)
    s.board()
    for i, (top, it, company, role_y, desc, placed, bottom) in enumerate(laid):
        tilt = [-0.35, 0.3, -0.25][i % 3]
        sh = bottom - top
        s.sticker(20, top, W - 44, sh, t[it.get("color") or PALETTE[i % len(PALETTE)]], r=16, tilt=tilt)
        s.add(f'<g transform="rotate({tilt} {20 + (W - 44) / 2:.1f} {top + sh / 2:.1f})">')
        s.chip(lx, top + 22, it["dates"], t["card"], size=11)
        for k, ln in enumerate(company):
            s.text(lx, top + 72 + k * 22, ln, 18, "display-bold", tracking=-0.01)
        s.text(lx, role_y, it["role"], 12, "mono-bold", t["text"], opacity=0.9)
        s.add(f'<path d="M{rx - 22} {top + 20}V{bottom - 20}" stroke="{t["line"]}" stroke-opacity="0.35" stroke-dasharray="3 5"/>')
        for k, ln in enumerate(desc):
            s.text(rx, top + 46 + k * 21, ln, 15, "display")
        for cx, cy, lab, _ in placed:
            s.chip(cx, cy, lab, t["card"], size=10, h=20, pad=7)
        s.add("</g>")
    return s.render(), alt


def cta(t: Theme, c: dict):
    x, y, w = 28, 24, W - 60
    stamp_w = 176
    text_w = w - 64 - stamp_w - 24
    title = wrap(c["title"], "display-bold", 26, text_w, max_lines=3)
    body = wrap(c["body"], "display", 16, text_w, max_lines=3) if c.get("body") else []
    cy = y + 54
    after = cy + (len(title) - 1) * 32
    body_y = after + 32
    after = body_y + (len(body) - 1) * 22 if body else after
    note_y = after + 30
    h_in = max((note_y if c.get("note") else after) + 30 - y, 170)
    alt = c.get("alt") or " ".join([c["title"], c.get("body", ""), c.get("note", "")]).strip()
    s = Svg(W, y + h_in + 30, t, alt)
    s.board()
    s.sticker(x, y, w, h_in, t[c.get("color", "blue")], r=18, shadow=6)
    for k, ln in enumerate(title):
        s.text(x + 32, cy + k * 32, ln, 26, "display-bold", tracking=-0.02)
    for k, ln in enumerate(body):
        s.text(x + 32, body_y + k * 22, ln, 16, "display")
    if c.get("note"):
        s.text(x + 32, note_y, c["note"], 13, "mono", t["text"], opacity=0.9)
    stamp = c.get("stamp", [])
    if stamp:
        sh = 34 + 24 * len(stamp)
        sx, sy = x + w - 32 - stamp_w, y + h_in / 2 - sh / 2
        s.sticker(sx, sy, stamp_w, sh, t["pop"], r=14, shadow=5, tilt=-5)
        s.add(f'<g transform="rotate(-5 {sx + stamp_w / 2:.1f} {sy + sh / 2:.1f})">')
        for k, ln in enumerate(stamp):
            s.text(sx + stamp_w / 2, sy + sh / 2 - (len(stamp) - 1) * 12 + 7 + k * 24, ln, 19, "display-bold",
                   t["on-pop"], anchor="middle")
        s.add("</g>")
    return s.render(), alt


def stats(t: Theme, p: dict, data: dict, st: dict):
    s = Svg(W, 280, t, "GitHub stats")
    s.board()
    s.text(28, 46, "On GitHub", 24, "display-bold", tracking=-0.02)
    s.text(W - 28, 44, f"redrawn every night · {_date(dt.date.fromisoformat(data['today']))}",
           12, "mono", t["muted"], anchor="end")

    since = st["streak_since"]
    big = [
        (f"{st['last_year']:,}", ["contributions in", "the last year"], "calendar", "blue"),
        (_plural(st["current_streak"], "day"),
         ["current streak,", f"since {since.day} {since:%b}" if since else "start one today"], "flame", "green"),
        (_plural(st["longest_streak"], "day"), ["longest streak", "ever"], "trophy", "amber"),
        (f"{st['total']:,}", ["contributions", f"since {st['first_year']}"], "bars", "purple"),
    ]
    tilts = [-1.0, 0.8, -0.6, 1.0]
    bw, gap = (W - 56 - 3 * 16) / 4, 16
    for i, (val, lab, ic, col) in enumerate(big):
        x = 28 + i * (bw + gap)
        inner = icon(ic, x + bw - 36, 84, 22, t["line"], t["card"], t["pop"])
        s.sticker(x, 72, bw, 104, t[col], tilt=tilts[i], inner=inner)
        s.add(f'<g transform="rotate({tilts[i]} {x + bw / 2:.1f} 124)">')
        s.text(x + 16, 118, val, 30, "display-bold", tracking=-0.02)
        s.text(x + 16, 141, lab[0], 12, "mono")
        s.text(x + 16, 157, lab[1], 12, "mono")
        s.add("</g>")

    small = [
        (f"{data['public_repos']}", "public repos", "folder", "teal"),
        (f"{data['stars']}", "stars earned", "star", "red"),
        (f"{data['followers']}", "followers", "people", "green"),
    ]
    sw = (W - 56 - 2 * 16) / 3
    for i, (val, lab, ic, col) in enumerate(small):
        x = 28 + i * (sw + 16)
        s.sticker(x, 198, sw, 56, t[col], tilt=[0.5, -0.5, 0.4][i])
        s.add(icon(ic, x + 16, 214, 24, t["line"], t["card"], t["pop"]))
        s.text(x + 52, 235, val, 26, "display-bold")
        s.text(x + 52 + text_width(val, "display-bold", 26) + 10, 233, lab, 13, "mono")

    alt = (f"On GitHub: {st['last_year']:,} contributions in the last year, a {st['current_streak']}-day current streak, "
           f"longest streak {_plural(st['longest_streak'], 'day')}, {st['total']:,} contributions since {st['first_year']}, "
           f"{data['public_repos']} public repos, {data['stars']} stars earned, {data['followers']} followers.")
    return s.render(), alt


def _levels(values):
    nz = sorted(v for v in values if v > 0)
    if not nz:
        return lambda v: 0
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)]
    return lambda v: 0 if v == 0 else 1 + sum(v > x for x in q)


def heatmap(t: Theme, p: dict, data: dict, st: dict, months: int = 6):
    today = dt.date.fromisoformat(data["today"])
    weeks = 27 if months == 6 else 53
    start = today - dt.timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)
    start -= dt.timedelta(weeks=weeks - 1)
    days = data["days"]
    span = [start + dt.timedelta(days=i) for i in range((today - start).days + 1)]
    total = sum(days.get(d.isoformat(), 0) for d in span)
    lvl = _levels([days.get(d.isoformat(), 0) for d in span])

    pitch = 820 / weeks
    cw = pitch - 4
    ch = 22 if months == 6 else 13
    rp = ch + 4
    show_nums = cw >= 22
    gy = 92
    h = gy + 7 * rp + 66
    s = Svg(W, h, t, f"{total:,} contributions in the last {months} months")
    s.board()
    s.sticker(20, 20, W - 44, h - 44, t["card"], r=16)

    s.text(40, 56, f"{total:,}", 18, "display-bold")
    s.text(40 + text_width(f"{total:,}", "display-bold", 18) + 8, 55,
           f"contributions in the last {months} months", 13, "mono")

    last_month = None
    for d in span:
        col, row = (d - start).days // 7, (d - start).days % 7
        x, y = 40 + col * pitch, gy + row * rp
        if row == 0 and d.month != last_month and (d.day <= 7 or (col == 0 and d.day <= 14)):
            if col < weeks - 1:
                s.text(x, gy - 10, f"{d:%b}", 11, "mono", t["muted"])
            last_month = d.month
        v = days.get(d.isoformat(), 0)
        L = lvl(v)
        stroke = f' stroke="{t["pop"]}" stroke-width="2"' if d == today else ""
        s.add(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="5" fill="{t["heat"][L]}"{stroke}/>')
        if show_nums:
            size = 10 if v < 100 else 9
            s.text(x + cw / 2, y + ch / 2 + 3.6, str(v), size, "mono-bold", t["heat-text"][L], anchor="middle")

    ly = gy + 7 * rp + 22
    s.text(40, ly, "contributions per day", 12, "mono", t["muted"])
    lx = W - 44 - 40
    s.text(lx, ly, "More", 12, "mono", t["muted"], anchor="end")
    lx -= text_width("More", "mono", 12) + 8 + 5 * 16
    s.text(lx - 8, ly, "Less", 12, "mono", t["muted"], anchor="end")
    for i in range(5):
        s.add(f'<rect x="{lx + i * 16}" y="{ly - 11}" width="12" height="12" rx="3" fill="{t["heat"][i]}"/>')
    return s.render(), f"{total:,} contributions in the last {months} months"


def line30(t: Theme, p: dict, data: dict, st: dict):
    today = dt.date.fromisoformat(data["today"])
    span = [today - dt.timedelta(days=29 - i) for i in range(30)]
    vals = [data["days"].get(d.isoformat(), 0) for d in span]
    total, top = sum(vals), max(vals) or 1
    h = 270
    s = Svg(W, h, t, f"{total:,} contributions in the last 30 days")
    s.board()
    s.sticker(20, 20, W - 44, h - 44, t["card"], r=16)
    s.text(40, 56, f"{total:,}", 18, "display-bold")
    s.text(40 + text_width(f"{total:,}", "display-bold", 18) + 8, 55, "contributions in the last 30 days", 13, "mono")

    x0, x1, y0, y1 = 76, W - 60, 78, 190
    for frac in (0, 0.5, 1):
        y = y1 - (y1 - y0) * frac
        s.add(f'<path d="M{x0} {y:.1f}H{x1}" stroke="{t["muted"]}" stroke-opacity="0.25" stroke-dasharray="3 5"/>')
        s.text(x0 - 12, y + 4, f"{round(top * frac)}", 11, "mono", t["muted"], anchor="end")
    pts = [(x0 + (x1 - x0) * i / 29, y1 - (y1 - y0) * v / top) for i, v in enumerate(vals)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    s.add(f'<polygon points="{x0},{y1} {path} {x1},{y1}" fill="{t["go"]}" opacity="0.16"/>')
    s.add(f'<polyline points="{path}" fill="none" stroke="{t["go"]}" stroke-width="3" stroke-linejoin="round"/>')
    peak = vals.index(max(vals))
    for i, (x, y) in enumerate(pts):
        hot = i == peak
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5 if hot else 3.5}" fill="{t["pop"] if hot else t["card"]}" '
              f'stroke="{t["line"] if hot else t["go"]}" stroke-width="2"/>')
        s.text(x, y1 + 20, str(span[i].day), 10, "mono", t["muted"], anchor="middle")
        if i == 0 or span[i].day == 1:
            s.text(x, y1 + 34, f"{span[i]:%b}", 10, "mono-bold", t["text"], anchor="middle")
    px, py = pts[peak]
    s.text(px, py - 12, f"{max(vals)} best day", 11, "mono-bold", t["text"], anchor="middle")
    return s.render(), f"{total:,} contributions in the last 30 days"
