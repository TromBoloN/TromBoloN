#!/usr/bin/env python3
"""Generate the activity panel SVG (big numbers + last 12 months) from the GitHub GraphQL API.

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
import random
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dossier_style import (  # noqa: E402
    AMBER, COPPER_LO, CREAM, MUTED, RED, RED_DIM, RED_HI, desk, display, doc,
    plate, tag,
)

API_URL = "https://api.github.com/graphql"
WINDOW_DAYS = 364  # GitHub allows at most ~1 year per contributionsCollection query
MAX_WINDOWS = 15  # safety cap (about 15 years of history)
FALLBACK_COLOR = "#8b949e"

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
        "calendar": days,
    }


def demo_stats() -> dict:
    rng = random.Random(64)
    today = date.today()
    calendar = {}
    for offset in range(400):
        day = today - timedelta(days=offset)
        busy = rng.random() < (0.55 if day.weekday() < 5 else 0.25)
        calendar[day.isoformat()] = rng.choice((1, 2, 3, 5, 8, 13)) if busy else 0
    return {
        "calendar": calendar,
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
# Rendering: Activity panel (three numbers + the last 53 weeks)
# --------------------------------------------------------------------------
WIDTH = 860


def render_activity(stats: dict) -> str:
    w, h = WIDTH, 236
    out = [desk(w, h, seed=7)]

    # Numbers plate
    svg, (ix, iy, iw, ih), _ = plate(14, 14, 290, h - 30)
    out.append(svg)
    rows = [
        (f'{stats["total"]:,}', "CONTRIBUTIONS"),
        (f'{stats["current"]}', "DAY STREAK"),
        (f'{stats["longest"]}', "BEST STREAK"),
    ]
    for i, (value, name) in enumerate(rows):
        y = iy + 50 + i * 56
        out.append(f'<g class="in" style="animation-delay:{.2 * i:.1f}s">')
        out.append(display(ix + 24, y, value, 38, AMBER if i == 0 else CREAM, spacing=1))
        out.append(display(ix + iw - 22, y - 2, name, 14, MUTED, "end", spacing=1.5))
        out.append("</g>")
        if i < 2:
            out.append(f'<rect class="cr" x="{ix + 22}" y="{y + 14}" width="{iw - 44}" height="1.5" fill="{COPPER_LO}"/>')

    # Year grid plate
    svg, (gx0, gy0, gw, gh), _ = plate(320, 14, w - 334, h - 30, metal="#7a2a1c", hi="#c0573b", lo="#3d120c", fill="#220806")
    out.append(svg)
    out.append(tag(gx0 + 14, gy0 + 14, "LAST 12 MONTHS", 13, RED))

    today = date.fromisoformat(stats["updated"])
    start = today - timedelta(days=52 * 7 + (today.weekday() + 1) % 7)
    calendar = stats.get("calendar", {})
    span = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    counts = [calendar.get(d.isoformat(), 0) for d in span]
    busy = sorted(c for c in counts if c > 0)
    cuts = [busy[int(len(busy) * q)] for q in (0.25, 0.5, 0.75)] if busy else [1, 2, 3]
    shades = ["#3a120d", RED_DIM, RED, RED_HI, AMBER]

    pitch, cell = 8.9, 7
    grid_w = 53 * pitch
    gx = gx0 + (gw - grid_w) / 2
    gy = gy0 + 54
    cells = []
    for d, count in zip(span, counts):
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        lvl = 0 if count <= 0 else 1 + sum(count > cut for cut in cuts)
        x, y = gx + col * pitch, gy + row * pitch
        if lvl == 0:
            cells.append(f'<rect x="{x + 2.5:.1f}" y="{y + 2.5:.1f}" width="2" height="2" fill="{shades[0]}"/>')
        else:
            cells.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" fill="{shades[lvl]}"/>')
    out.append(f'<g class="cr">{"".join(cells)}</g>')
    tx = gx + ((today - start).days // 7) * pitch
    ty = gy + ((today.weekday() + 1) % 7) * pitch
    out.append(f'<rect class="lamp cr" x="{tx - 2:.1f}" y="{ty - 2:.1f}" width="{cell + 4}" height="{cell + 4}" fill="none" stroke="{CREAM}" stroke-width="1.5"/>')

    present = sum(1 for c in counts if c > 0)
    out.append(display(gx0 + gw - 20, gy0 + gh - 20, f"{present} OF {len(counts)} DAYS PRESENT", 16, CREAM, "end", spacing=1.5))

    title = (
        f'{stats["total"]:,} contributions; current streak {stats["current"]} days, '
        f'best {stats["longest"]} days; active on {present} of the last {len(counts)} days'
    )
    return doc(w, h, title, "\n".join(out))


# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--username", default=os.environ.get("GH_USERNAME"))
    parser.add_argument("--output", default="assets/activity.svg")
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
        handle.write(render_activity(stats))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()