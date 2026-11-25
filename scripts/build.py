"""Build every SVG card and the README from profile.json.

    python scripts/build.py            # real numbers (needs GH_TOKEN)
    python scripts/build.py --demo     # fake numbers, for previewing
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cards
import fetch
from svgkit import Theme

REPO = Path(__file__).resolve().parent.parent
ASSETS = REPO / "assets"


def _a(s: str) -> str:
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


class Builder:
    def __init__(self, profile: dict, data: dict, st: dict):
        self.p, self.data, self.st = profile, data, st
        self.alts: dict[str, str] = {}
        self.out: list[str] = []
        self.links = {l["kind"]: l for l in profile.get("links", []) if l.get("enabled", True)}

    def emit(self, name: str, fn, *args) -> str:
        for mode in ("light", "dark"):
            svg, alt = fn(Theme(mode), *args)
            (ASSETS / f"{name}-{mode}.svg").write_text(svg)
        self.alts[name] = alt
        return name

    def pic(self, name: str, width: str = "100%", href: str | None = None, height: str | None = None) -> str:
        size = f'height="{height}"' if height else f'width="{width}"'
        tag = (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
               f'<img src="assets/{name}-light.svg" {size} alt="{_a(self.alts[name])}"></picture>')
        return f'<a href="{_a(href)}">{tag}</a>' if href else tag

    def add(self, *lines: str):
        self.out.extend(lines)

    def url(self, link: dict) -> str:
        return link["url"].replace("{login}", self.data["login"])

    def badges(self, kinds: list[str]):
        row = [self.pic(f"badge-{k}", href=self.url(self.links[k]), height="46") for k in kinds if k in self.links]
        if row:
            self.add('<p align="center">', *row, "</p>", "")

    def label(self, s: dict, slug: str, i: int):
        if s.get("label"):
            color = s.get("label_color") or cards.PALETTE[i % len(cards.PALETTE)]
            self.add(self.pic(self.emit(f"label-{slug}", cards.label, s["label"], s.get("chip", ""), color)), "")

    def section(self, s: dict, i: int):
        kind = s["type"]
        slug = s.get("name") or f"{kind}-{i}"
        self.label(s, slug, i)
        getattr(self, f"_{kind.replace('-', '_')}")(s, slug)
        if s.get("more"):
            m = s["more"]
            self.add(f'<p align="center"><a href="{_a(m["url"])}"><b>{m["text"]}</b></a></p>', "")

    def _whoami(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.whoami, s)), "")

    def _tiles(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.tiles, s["items"], s.get("cols", 3), s.get("alt_prefix", ""))), "")

    def _snapshot(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.snapshot, s["rows"], s.get("label", "Snapshot"))), "")

    def _cards(self, s, slug, items=None):
        items = items if items is not None else s["items"]
        if not items:
            return
        lay = cards.card_layout(items)
        linked = s.get("linked", False)
        row = []
        for j, c in enumerate(items):
            name = self.emit(f"{slug}-{j}", cards.card, c, j, linked, lay)
            row.append(self.pic(name, "49%", href=c.get("url") if linked else None))
        self.add('<p align="center">', *row, "</p>", "")

    def _repos(self, s, slug):
        repos = self.data["pinned"] if s.get("source", "pinned") == "pinned" else []
        if not repos:
            repos = [r for r in self.data["repos"] if not r.get("isArchived")]
        repos = repos[: s.get("limit", 4)]
        self._cards({**s, "linked": True}, slug, [cards.repo_card_data(r, self.data["login"]) for r in repos])

    def _chips(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.chipboard, s["groups"], s.get("label", "Tech stack"))), "")
        d = s.get("details")
        if d:
            head = d.get("head", ["Layer", "Tools"])
            self.add("<details>", f"<summary><b>{d['summary']}</b></summary>", "<br/>", "",
                     f"| {head[0]} | {head[1]} |", "|:---|:---|",
                     *[f"| **{k}** | {v} |" for k, v in d["rows"]], "", "</details>", "")

    def _timeline(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.timeline, s["items"], s.get("label", "Experience"))), "")

    def _github(self, s, slug):
        p, data, st = self.p, self.data, self.st
        body = [
            self.pic(self.emit("stats", cards.stats, p, data, st)), "",
            self.pic(self.emit("graph-6m", cards.heatmap, p, data, st, 6)), "",
            self.pic(self.emit("graph-12m", cards.heatmap, p, data, st, 12)), "",
            self.pic(self.emit("line-30d", cards.line30, p, data, st)), "",
        ]
        if s.get("collapsed"):
            self.add("<details>", f"<summary><b>{s['collapsed']}</b></summary>", "<br/>", "", *body, "</details>", "")
        else:
            self.add(*body)

    def _cta(self, s, slug):
        self.add(self.pic(self.emit(slug, cards.cta, s), href=s.get("href")), "")
        self.badges(s.get("links", []))

    def build(self) -> str:
        p = self.p
        if p.get("comment"):
            self.add(f"<!-- {p['comment']} -->", "")
        self.add(self.pic(self.emit("hero", cards.hero, p, self.data, self.st)), "")
        for kind, link in self.links.items():
            self.emit(f"badge-{kind}", cards.badge, link, self.data["login"])
        self.badges(list(self.links))
        for i, s in enumerate(p.get("sections", [])):
            self.section(s, i)
        if p.get("views_badge"):
            self.add(f'<p align="center"><img alt="Profile views" src="{_a(p["views_badge"])}"/></p>', "")
        if p.get("footer"):
            self.add(f'<p align="center"><sub>{p["footer"]}</sub></p>', "")
        return "\n".join(self.out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use fake numbers")
    args = ap.parse_args()

    p = json.loads((REPO / "profile.json").read_text())
    login = p.get("github") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "your-github"
    data = fetch.load(login, args.demo)
    st = fetch.stats(data)

    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    readme = Builder(p, data, st).build()
    (REPO / "README.md").write_text(readme)
    print(f"built {len(list(ASSETS.glob('*.svg')))} svgs for @{data['login']}"
          f" · {st['last_year']} contributions last year · streak {st['current_streak']}")


if __name__ == "__main__":
    main()
