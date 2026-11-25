"""Fetch the numbers the cards show from the GitHub GraphQL API.

Needs a token in GH_TOKEN (the workflow passes one). The default Actions
token sees public data only; add a PROFILE_TOKEN secret (a classic PAT with
read:user) if you want private contributions counted too.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import time
import urllib.error
import urllib.request

API = "https://api.github.com/graphql"

USER_Q = """
query($login: String!, $after: String) {
  user(login: $login) {
    login name createdAt
    followers { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, privacy: PUBLIC,
                 isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { name description url stargazerCount forkCount isArchived
              primaryLanguage { name color } }
    }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { name description url stargazerCount forkCount
                                  primaryLanguage { name color } } }
    }
  }
}"""

YEAR_Q = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def _gql(token: str, query: str, attempts: int = 4, **variables) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme-build"},
    )
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code not in (403, 429) or attempt == attempts:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts:
                raise
        time.sleep(10 * attempt)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def fetch(login: str, token: str) -> dict:
    repos, pinned, after, user = [], [], None, None
    while True:
        u = _gql(token, USER_Q, login=login, after=after)["user"]
        user = user or u
        repos += u["repositories"]["nodes"]
        pinned = pinned or u["pinnedItems"]["nodes"]
        page = u["repositories"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        after = page["endCursor"]

    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    start_year = int(user["createdAt"][:4])
    days: dict[str, int] = {}
    for year in range(start_year, today.year + 1):
        frm = f"{year}-01-01T00:00:00Z"
        to = f"{year}-12-31T23:59:59Z" if year < today.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
        cal = _gql(token, YEAR_Q, login=login, **{"from": frm, "to": to})
        for w in cal["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                if d["date"] <= today.isoformat():
                    days[d["date"]] = d["contributionCount"]

    return {
        "login": user["login"],
        "name": user["name"] or user["login"],
        "created": user["createdAt"][:10],
        "followers": user["followers"]["totalCount"],
        "public_repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": repos,
        "pinned": pinned,
        "days": dict(sorted(days.items())),
        "today": today.isoformat(),
    }


def demo(login: str = "your-github") -> dict:
    """Believable fake data, so the cards can be previewed with no token."""
    rnd = random.Random(43)
    today = dt.date.today()
    days, d = {}, dt.date(2021, 3, 1)
    while d <= today:
        busy = 0.35 if d.year < 2025 else 0.8
        if d.weekday() >= 5:
            busy *= 0.4
        days[d.isoformat()] = rnd.randint(1, 14 if d.year >= 2025 else 6) if rnd.random() < busy else 0
        d += dt.timedelta(days=1)
    for i in range(23):
        days[(today - dt.timedelta(days=i)).isoformat()] = rnd.randint(2, 12)
    pinned = [
        {"name": "sample-repo", "description": "Preview data. The real build reads your pinned repos.",
         "url": "#", "stargazerCount": 12, "forkCount": 3, "primaryLanguage": {"name": "TypeScript", "color": "#3178c6"}},
    ]
    return {"login": login, "name": login, "created": "2021-03-01", "followers": 48, "public_repos": 27,
            "stars": 61, "repos": pinned, "pinned": pinned, "days": days, "today": today.isoformat()}


def stats(data: dict) -> dict:
    """Derive the headline numbers from the raw day counts."""
    days = data["days"]
    today = dt.date.fromisoformat(data["today"])
    keys = sorted(days)

    longest = run = 0
    prev = None
    for k in keys:
        d = dt.date.fromisoformat(k)
        if days[k] > 0:
            run = run + 1 if prev and (d - prev).days == 1 and days[prev.isoformat()] > 0 else 1
            longest = max(longest, run)
        else:
            run = 0
        prev = d

    cur, d = 0, today
    if days.get(d.isoformat(), 0) == 0:
        d -= dt.timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        cur += 1
        d -= dt.timedelta(days=1)
    streak_since = (d + dt.timedelta(days=1)) if cur else None

    year_ago = (today - dt.timedelta(days=365)).isoformat()
    return {
        "last_year": sum(v for k, v in days.items() if k > year_ago),
        "total": sum(days.values()),
        "first_year": keys[0][:4] if keys else data["created"][:4],
        "current_streak": cur,
        "streak_since": streak_since,
        "longest_streak": longest,
    }


def load(login: str, demo_mode: bool) -> dict:
    if demo_mode:
        return demo(login)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("No GH_TOKEN set. Run with --demo to preview with fake numbers.")
    return fetch(login, token)
