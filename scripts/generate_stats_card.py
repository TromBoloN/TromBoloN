#!/usr/bin/env python3
"""Generate the "Activity Ledger" and "Attendance Register" SVGs from the GitHub GraphQL API.

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
    BLOOD, DIM, FADED, FORM, LINE, PAPER, RUST, SECTOR, SOOT,
    barcode, desaturate, doc, e, frame, header_rule, label, stamp, text_width,
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
# Rendering: Activity Ledger
# --------------------------------------------------------------------------
WIDTH = 860


def shorten(text: str, limit: int = 13) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_svg(stats: dict) -> str:
    w, h = WIDTH, 318
    out = [frame(w, h), header_rule(28, 42, w - 56, "IV", "ACTIVITY LEDGER", "REF/CR-64-04")]

    rows = [
        ("ENTRIES ON RECORD", f'{stats["total"]:,}', "ALL TIME"),
        ("COMMITS FILED", f'{stats["commits"]:,}', "12 MO"),
        ("REQUISITIONS (PULL REQUESTS)", f'{stats["prs"]:,}', "12 MO"),
        ("CONSECUTIVE DAYS ON DUTY", f'{stats["current"]:,}', "DAYS"),
        ("LONGEST UNBROKEN SERVICE", f'{stats["longest"]:,}', "DAYS"),
        ("SITES OF OPERATION", f'{stats["repos"]:,}', "REPOS · 12 MO"),
    ]
    col_w, row_h, top = (w - 56 - 28) / 2, 36, 76
    for index, (name, value, unit) in enumerate(rows):
        col, row = index // 3, index % 3
        x = 28 + col * (col_w + 28)
        y = top + row * row_h
        value_w = text_width(value, 20, 0.55)
        unit_w = text_width(unit, 9)
        out.append(f'<g class="rise" style="animation-delay:{0.15 * index:.2f}s">')
        out.append(label(x, y + 20, f"{index + 1:02d}", 10, DIM))
        out.append(label(x + 28, y + 20, name, 11, FADED))
        leader_from = x + 28 + text_width(name, 11) + 8
        leader_to = x + col_w - value_w - unit_w - 18
        if leader_to > leader_from:
            out.append(
                f'<path class="cr" d="M{leader_from:.1f} {y + 19.5}H{leader_to:.1f}" '
                f'stroke="{DIM}" stroke-dasharray="1 3"/>'
            )
        out.append(
            f'<text x="{x + col_w - unit_w - 8:.1f}" y="{y + 22}" class="mo" font-size="20" '
            f'font-weight="700" fill="{PAPER}" text-anchor="end">{e(value)}</text>'
        )
        out.append(label(x + col_w, y + 22, unit, 9, DIM, "end"))
        out.append(f'<path class="cr" d="M{x} {y + row_h - 5.5}H{x + col_w}" stroke="{SOOT}"/>')
        out.append("</g>")
    out.append(f'<path class="cr" d="M{28 + col_w + 14:.1f} {top}V{top + 3 * row_h - 6}" stroke="{LINE}"/>')

    # Material composition (languages)
    bar_y = 222
    out.append(label(28, bar_y - 10, "MATERIAL COMPOSITION · WEIGHTED BY COMMITS · 12 MO", 10, FADED))
    languages = stats["languages"]
    bar_x, bar_w = 28, w - 56
    if languages:
        cursor = float(bar_x)
        for _, percent, color in languages:
            seg = bar_w * percent / 100
            out.append(
                f'<rect class="cr" x="{cursor:.1f}" y="{bar_y}" width="{max(seg - 2, 1):.1f}" '
                f'height="14" fill="{desaturate(color)}"/>'
            )
            cursor += seg
        out.append(f'<rect class="cr" x="{bar_x - 2.5}" y="{bar_y - 2.5}" width="{bar_w + 3}" height="19" fill="none" stroke="{LINE}"/>')
        slot = bar_w / len(languages)
        for index, (name, percent, color) in enumerate(languages):
            x = bar_x + index * slot
            out.append(f'<rect class="cr" x="{x:.1f}" y="{bar_y + 30}" width="9" height="9" fill="{desaturate(color)}"/>')
            out.append(
                f'<text x="{x + 15:.1f}" y="{bar_y + 39}" class="mo" font-size="11" fill="{PAPER}">'
                f'{e(shorten(name.upper()))} <tspan fill="{FADED}">{percent:.1f}%</tspan></text>'
            )
    else:
        out.append(label(28, bar_y + 12, "NO MATERIAL ON RECORD", 11, FADED))

    out.append(f'<path class="cr" d="M20 {h - 40.5}H{w - 20}" stroke="{LINE}"/>')
    out.append(label(28, h - 20, f"AUDITED {stats['updated']} · SOURCE: GITHUB GRAPHQL · {SECTOR} · {FORM}", 9, DIM))
    out.append(barcode(stats["updated"], w - 28 - 120, h - 31, 120, 13, FADED))
    out.append(stamp("AUDITED", w - 230, h - 24, -5, 15, RUST))
    title = (
        f'Activity ledger for {stats["name"]}: {stats["total"]:,} contributions on record, '
        f'{stats["commits"]:,} commits and {stats["prs"]:,} pull requests in 12 months, '
        f'current streak {stats["current"]} days, longest {stats["longest"]} days'
    )
    return doc(w, h, title, "\n".join(out))


# --------------------------------------------------------------------------
# Rendering: Attendance Register (last 53 weeks)
# --------------------------------------------------------------------------
def render_register(stats: dict) -> str:
    w, cell, pitch = WIDTH, 11, 14
    today = date.fromisoformat(stats["updated"])
    start = today - timedelta(days=52 * 7 + (today.weekday() + 1) % 7)
    calendar = stats.get("calendar", {})
    span = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    counts = [calendar.get(d.isoformat(), 0) for d in span]

    busy = sorted(c for c in counts if c > 0)
    cuts = [busy[int(len(busy) * q)] for q in (0.25, 0.5, 0.75)] if busy else [1, 2, 3]
    shades = [None, "#4a3a30", "#6b3f33", RUST, BLOOD]

    def level(count: int) -> int:
        if count <= 0:
            return 0
        return 1 + sum(count > cut for cut in cuts)

    gx, gy = 70, 92
    h = gy + 7 * pitch + 82
    out = [frame(w, h), header_rule(28, 42, w - 56, "V", "ATTENDANCE REGISTER", "REF/CR-64-05")]

    for row, name in ((1, "MON"), (3, "WED"), (5, "FRI")):
        out.append(label(gx - 10, gy + row * pitch + 9, name, 8.5, DIM, "end"))
    last_month = None
    cells = []
    for d, count in zip(span, counts):
        col = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        x, y = gx + col * pitch, gy + row * pitch
        if row == 0 and d.month != last_month and col < 52:
            out.append(label(x, gy - 8, d.strftime("%b").upper(), 8.5, FADED))
            last_month = d.month
        lvl = level(count)
        if lvl == 0:
            cells.append(
                f'<rect x="{x + .5}" y="{y + .5}" width="{cell - 1}" height="{cell - 1}" '
                f'fill="none" stroke="{SOOT}"/>'
            )
        else:
            cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{shades[lvl]}"/>')
    out.append(f'<g class="cr">{"".join(cells)}</g>')
    # mark today
    tx = gx + ((today - start).days // 7) * pitch
    ty = gy + ((today.weekday() + 1) % 7) * pitch
    out.append(f'<rect class="lamp cr" x="{tx - 1.5}" y="{ty - 1.5}" width="{cell + 3}" height="{cell + 3}" fill="none" stroke="{PAPER}"/>')

    present = sum(1 for c in counts if c > 0)
    absent = len(counts) - present
    ly = gy + 7 * pitch + 22
    out.append(label(gx, ly, "ABSENT", 9, DIM))
    lx = gx + 48
    for lvl in range(5):
        if lvl == 0:
            out.append(f'<rect class="cr" x="{lx + .5}" y="{ly - 9.5}" width="{cell - 1}" height="{cell - 1}" fill="none" stroke="{DIM}"/>')
        else:
            out.append(f'<rect class="cr" x="{lx}" y="{ly - 10}" width="{cell}" height="{cell}" fill="{shades[lvl]}"/>')
        lx += pitch
    out.append(label(lx + 4, ly, "PRESENT", 9, DIM))

    rx = w - 28
    out.append(label(rx, ly, f"DAYS PRESENT {present:03d} / {len(counts):03d}  ·  ABSENCES {absent:03d}", 10.5, PAPER, "end"))
    out.append(f'<path class="cr" d="M20 {h - 34.5}H{w - 20}" stroke="{LINE}"/>')
    out.append(label(28, h - 16, "ATTENDANCE IS MANDATORY · ABSENCES ARE NOTED", 9.5, BLOOD))
    out.append(label(rx, h - 16, f"PERIOD {start.isoformat()} — {today.isoformat()}", 9, DIM, "end"))
    title = f"Attendance register: contributions on {present} of the last {len(counts)} days"
    return doc(w, h, title, "\n".join(out))


# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--username", default=os.environ.get("GH_USERNAME"))
    parser.add_argument("--output", default="assets/dev-stats.svg")
    parser.add_argument("--register-output", default="assets/attendance-register.svg")
    parser.add_argument("--demo", action="store_true", help="use fake data (no token needed)")
    args = parser.parse_args()

    if args.demo:
        stats = demo_stats()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token or not args.username:
            sys.exit("Set GH_TOKEN and GH_USERNAME (or pass --username), or use --demo.")
        stats = fetch_stats(args.username, token)

    for path, content in ((args.output, render_svg(stats)), (args.register_output, render_register(stats))):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()