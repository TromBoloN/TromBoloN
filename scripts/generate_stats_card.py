#!/usr/bin/env python3
"""Generate an animated SVG "dev stats" card from the GitHub GraphQL API.

Why this exists: popular stats widgets only count repos you OWN and run on
free servers that can go down. This script counts contributions to ANY public
repo (including ones owned by other people) and runs inside your own GitHub
Action, so nothing depends on a third-party server.

Usage:
    GH_TOKEN=... GH_USERNAME=TromBoloN python scripts/generate_stats_card.py
    python scripts/generate_stats_card.py --demo        # fake data, no token

Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from html import escape

API_URL = "https://api.github.com/graphql"
WINDOW_DAYS = 364  # GitHub allows at most ~1 year per contributionsCollection query
MAX_WINDOWS = 15  # safety cap (about 15 years of history)
FALLBACK_COLOR = "#8b949e"

CYAN, PURPLE, PINK, GREEN = "#00F7FF", "#B26BFF", "#FF4F81", "#3FB950"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login
    name
    createdAt
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories: 25) {
        contributions { totalCount }
        repository {
          nameWithOwner
          languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
            edges { size node { name color } }
          }
        }
      }
    }
  }
}
"""


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------
def graphql(token: str, variables: dict) -> dict:
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "dev-stats-card",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:300]
        sys.exit(f"GitHub API error {err.code}: {detail}")
    if "errors" in payload:
        sys.exit(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def current_and_longest_streak(days: dict[str, int], today: date) -> tuple[int, int]:
    longest = run = 0
    for key in sorted(days):
        run = run + 1 if days[key] > 0 else 0
        longest = max(longest, run)

    current = 0
    cursor = today
    # A zero today doesn't break the streak yet (the day isn't over).
    if days.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    while days.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def fetch_stats(login: str, token: str) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    to = now
    days: dict[str, int] = {}
    recent = None
    profile = None

    for _ in range(MAX_WINDOWS):
        start = to - timedelta(days=WINDOW_DAYS)
        user = graphql(token, {"login": login, "from": iso(start), "to": iso(to)})
        if user is None:
            sys.exit(f"User {login!r} was not found")
        if recent is None:
            recent, profile = user["contributionsCollection"], user
        for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                key = day["date"]
                days[key] = max(days.get(key, 0), day["contributionCount"])
        created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
        to = start - timedelta(seconds=1)
        if to <= created:
            break

    # Languages: weight each repo's language mix by how many commits you made
    # there in the last 12 months. Works for repos you don't own.
    scores: dict[str, float] = defaultdict(float)
    colors: dict[str, str] = {}
    repos = recent["commitContributionsByRepository"]
    for entry in repos:
        commits = entry["contributions"]["totalCount"]
        edges = entry["repository"]["languages"]["edges"]
        size_total = sum(edge["size"] for edge in edges)
        if not size_total:
            continue
        for edge in edges:
            name = edge["node"]["name"]
            scores[name] += commits * edge["size"] / size_total
            colors.setdefault(name, edge["node"]["color"] or FALLBACK_COLOR)

    score_total = sum(scores.values())
    languages = []
    if score_total:
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        for name, score in ranked[:5]:
            languages.append((name, score / score_total * 100, colors[name]))
        other = sum(score for _, score in ranked[5:]) / score_total * 100
        if other >= 1:
            languages.append(("Other", other, "#6e7681"))

    current, longest = current_and_longest_streak(days, now.date())
    return {
        "name": profile["name"] or profile["login"],
        "total": sum(days.values()),
        "commits": recent["totalCommitContributions"],
        "prs": recent["totalPullRequestContributions"],
        "repos": len(repos),
        "current": current,
        "longest": longest,
        "languages": languages,
        "updated": now.date().isoformat(),
    }


def demo_stats() -> dict:
    return {
        "name": "Arif Abdurrahman",
        "total": 1234,
        "commits": 312,
        "prs": 14,
        "repos": 6,
        "current": 11,
        "longest": 35,
        "languages": [
            ("Python", 46.5, "#3572A5"),
            ("HTML", 21.0, "#e34c26"),
            ("CSS", 14.2, "#663399"),
            ("JavaScript", 11.8, "#f1e05a"),
            ("Other", 6.5, "#6e7681"),
        ],
        "updated": date.today().isoformat(),
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
STYLE = """
.t{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif}
.m{font-family:'Fira Code',Consolas,'SFMono-Regular','Courier New',monospace}
.fade{animation:fade .8s ease-out backwards}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.pulse{animation:pulse 1.8s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.2}}
.shine{animation:shine 3.4s linear infinite}
@keyframes shine{from{transform:translateX(-160px)}to{transform:translateX(800px)}}
"""


def shorten(text: str, limit: int = 13) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_svg(stats: dict) -> str:
    width, height = 800, 325
    out: list[str] = []
    add = out.append

    add(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Developer stats for {escape(stats["name"])}">'
    )
    add(f"<style>{STYLE}</style>")
    add(
        "<defs>"
        '<linearGradient id="border" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset=".55" stop-color="{PURPLE}"/>'
        f'<stop offset="1" stop-color="{PINK}"/></linearGradient>'
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#111827"/>'
        "</linearGradient>"
        '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".4"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<clipPath id="barclip"><rect x="30" y="258" width="740" height="10" rx="5"/></clipPath>'
        "</defs>"
    )
    add(
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14" '
        'fill="url(#bg)" stroke="url(#border)" stroke-width="2"/>'
    )

    # Header
    add(
        f'<text x="30" y="44" class="m" font-size="18" font-weight="700" fill="{CYAN}">'
        f'&gt;_ {escape(stats["name"])} <tspan fill="#8b949e" font-weight="400">/ dev stats</tspan></text>'
    )
    add(f'<circle cx="626" cy="39" r="4" fill="{GREEN}" class="pulse"/>')
    add(
        f'<text x="770" y="44" class="m" font-size="12" fill="#8b949e" text-anchor="end">'
        f'updated {escape(stats["updated"])}</text>'
    )

    # Stat tiles (3 x 2)
    tiles = [
        ("Total contributions", f'{stats["total"]:,}', CYAN),
        ("Commits · last 12 months", f'{stats["commits"]:,}', PURPLE),
        ("Pull requests · last 12 months", f'{stats["prs"]:,}', PINK),
        ("Current streak", f'{stats["current"]} days', CYAN),
        ("Longest streak", f'{stats["longest"]} days', PURPLE),
        ("Repos contributed to", f'{stats["repos"]:,}', PINK),
    ]
    for index, (label, value, color) in enumerate(tiles):
        col, row = index % 3, index // 3
        x, y = 30 + col * 250, 68 + row * 78
        add(f'<g class="fade" style="animation-delay:{0.12 * index:.2f}s">')
        add(
            f'<rect x="{x}" y="{y}" width="240" height="68" rx="10" '
            'fill="#161b22" stroke="#30363d"/>'
        )
        add(f'<rect x="{x}" y="{y + 12}" width="3" height="44" rx="1.5" fill="{color}"/>')
        add(
            f'<text x="{x + 20}" y="{y + 40}" class="t" font-size="28" font-weight="700" '
            f'fill="{color}" filter="url(#glow)">{escape(value)}</text>'
        )
        add(
            f'<text x="{x + 20}" y="{y + 58}" class="t" font-size="12" fill="#8b949e">'
            f"{escape(label)}</text>"
        )
        add("</g>")

    # Languages
    add(
        '<text x="30" y="248" class="m" font-size="11" fill="#8b949e" letter-spacing="1">'
        "TOP LANGUAGES · WEIGHTED BY COMMITS, LAST 12 MONTHS</text>"
    )
    languages = stats["languages"]
    if languages:
        add('<g clip-path="url(#barclip)">')
        add('<rect x="30" y="258" width="740" height="10" fill="#21262d"/>')
        cursor = 30.0
        for name, percent, color in languages:
            segment = 740 * percent / 100
            add(
                f'<rect x="{cursor:.2f}" y="258" width="{segment + 0.5:.2f}" height="10" '
                f'fill="{escape(color)}"/>'
            )
            cursor += segment
        add('<rect class="shine" x="0" y="258" width="120" height="10" fill="url(#shine)"/>')
        add("</g>")

        slot = 740 / len(languages)
        for index, (name, percent, color) in enumerate(languages):
            x = 30 + index * slot
            add(f'<circle cx="{x + 5:.1f}" cy="296" r="5" fill="{escape(color)}"/>')
            add(
                f'<text x="{x + 16:.1f}" y="300" class="t" font-size="12" fill="#c9d1d9">'
                f'{escape(shorten(name))} <tspan fill="#8b949e">{percent:.1f}%</tspan></text>'
            )
    else:
        add(
            '<text x="30" y="290" class="t" font-size="13" fill="#8b949e">'
            "No language data yet. Make some commits!</text>"
        )

    add("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--username", default=os.environ.get("GH_USERNAME"))
    parser.add_argument("--output", default="assets/dev-stats.svg")
    parser.add_argument("--demo", action="store_true", help="use fake data (no token needed)")
    args = parser.parse_args()

    if args.demo:
        stats = demo_stats()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token or not args.username:
            sys.exit("Set GH_TOKEN and GH_USERNAME (or pass --username), or use --demo.")
        stats = fetch_stats(args.username, token)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(render_svg(stats))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()