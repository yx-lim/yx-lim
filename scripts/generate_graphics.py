"""Generate repository-hosted profile graphics from public GitHub data."""

import datetime
import html
import json
import os
from pathlib import Path
import subprocess
import urllib.request

DISPLAY_NAME = "Nathan Lim"
USERNAME = os.environ.get("GH_LOGIN", "yx-lim")
ACCENT_LIGHT = "#007d75"
ACCENT_DARK = "#59d8c2"
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def api(path, payload=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        command = ["gh", "api", path]
        if payload is not None:
            command.extend(["--input", "-"])
        result = subprocess.run(command, input=json.dumps(payload) if payload else None,
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)
    request = urllib.request.Request(
        "https://api.github.com/" + path,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "yx-lim-profile"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def text(x, y, value, size=12, css="muted", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" class="{css}" {extra}>'
            f'{html.escape(str(value))}</text>')


def svg(height, content, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="620" height="{height}" viewBox="0 0 620 {height}" role="img" aria-label="{html.escape(label, quote=True)}">
<title>{html.escape(label)}</title>
<style>
text {{ font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace; }}
.ink {{ fill: #24292f; }} .muted {{ fill: #57606a; }}
.accent {{ fill: {ACCENT_LIGHT}; }} .rule {{ stroke: #d0d7de; }}
.empty {{ fill: #ebedf0; }}
@media (prefers-color-scheme: dark) {{
 .ink {{ fill: #f0f6fc; }} .muted {{ fill: #a4adb7; }}
 .accent {{ fill: {ACCENT_DARK}; }} .rule {{ stroke: #30363d; }}
 .empty {{ fill: #21262d; }}
}}
</style>
{content}
</svg>
'''


def identity():
    glyphs = (ASSETS / "portrait.txt").read_text().splitlines()
    width = max(map(len, glyphs)) * 3.9
    left = (620 - width) / 2
    art = "".join(text(left, 14 + i * 6.7, line, 6.5, "ink",
                       f'xml:space="preserve" textLength="{width}" lengthAdjust="spacingAndGlyphs"')
                  for i, line in enumerate(glyphs))
    baseline = 14 + len(glyphs) * 6.7 + 32
    art += text(310, baseline, DISPLAY_NAME, 25, "ink", 'text-anchor="middle"')
    art += text(310, baseline + 25, "@" + USERNAME, 12, "accent", 'text-anchor="middle"')
    return svg(round(baseline + 48), art, DISPLAY_NAME + " / ASCII portrait")


def heading(index, label):
    art = text(0, 28, f"0{index}", 11, "accent")
    art += text(35, 28, label, 13, "ink")
    # Fixed labels end before the divider, including on narrow GitHub layouts.
    start = 50 + len(label) * 8
    art += f'<line x1="{start}" y1="24" x2="620" y2="24" class="rule" />'
    return svg(46, art, label)


def generate():
    repositories = []
    page = 1
    while True:
        batch = api(f"users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    originals = [r for r in repositories if not r["fork"] and r["name"] != USERNAME]
    language_bytes = {}
    for repo in originals:
        for language, count in api(f"repos/{USERNAME}/{repo['name']}/languages").items():
            language_bytes[language] = language_bytes.get(language, 0) + count

    query = '''query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount contributionLevel } }
          }
        }
      }
    }'''
    result = api("graphql", {"query": query, "variables": {"login": USERNAME}})
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"]))
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

    art = ""
    metrics = [(len(repositories), "public repos"), (len(originals), "original repos"),
               (sum(r["stargazers_count"] for r in originals), "stars / originals")]
    for i, (value, label) in enumerate(metrics):
        x = 15 + i * 207
        art += text(x, 41, value, 28, "ink") + text(x, 65, label, 11)
    graphics = {"identity.svg": identity(), "stats.svg": svg(86, art, "Public repository statistics")}

    palette = ["#008a80", "#c77dba", "#d39b35", "#588bc4", "#859747"]
    ranked = sorted(language_bytes.items(), key=lambda pair: (-pair[1], pair[0]))
    groups = ranked[:4]
    if len(ranked) > 4:
        groups.append(("Other", sum(count for _, count in ranked[4:])))
    total = sum(language_bytes.values())
    art = text(0, 18, "LANGUAGES / PUBLIC ORIGINAL REPOS", 11)
    x = 0
    for i, (language, count) in enumerate(groups):
        width = 620 * count / total
        art += f'<rect x="{x:.3f}" y="32" width="{width:.3f}" height="6" fill="{palette[i]}" />'
        x += width
        y = 62 + i * 22
        art += f'<rect x="0" y="{y-8}" width="6" height="6" fill="{palette[i]}" />'
        art += text(16, y, language, 12, "ink")
        art += text(620, y, f"{count / total:.1%}", 12, "muted", 'text-anchor="end"')
    if not groups:
        art += text(0, 55, "No public language data yet.")
    graphics["languages.svg"] = svg(max(88, 62 + len(groups) * 22), art, "Languages by code bytes")

    weeks = calendar["weeks"]
    cell = min(11, 620 / len(weeks))
    ramp = {"NONE": ":", "FIRST_QUARTILE": "+", "SECOND_QUARTILE": "*",
            "THIRD_QUARTILE": "#", "FOURTH_QUARTILE": "@"}
    art = text(0, 17, "CONTRIBUTIONS / PAST YEAR", 11)
    art += text(620, 17, calendar["totalContributions"], 12, "accent", 'text-anchor="end"')
    for column, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = datetime.date.fromisoformat(day["date"])
            row = (date.weekday() + 1) % 7
            level = day["contributionLevel"]
            symbol = ramp[level]
            art += (f'<g><title>{day["date"]}: {day["contributionCount"]} contributions</title>'
                    + text(column * cell, 40 + row * 12, symbol, 10,
                           "muted" if level == "NONE" else "accent") + '</g>')
    art += text(0, 139, ": quiet   + * # @ active", 10)
    graphics["year.svg"] = svg(154, art, "GitHub contribution calendar")
    for index, (slug, label) in enumerate([
            ("about", "ABOUT"), ("stack", "STACK"), ("projects", "SELECTED PROJECTS"),
            ("activity", "ACTIVITY"), ("colophon", "ABOUT THIS PAGE")], 1):
        graphics[f"heading-{slug}.svg"] = heading(index, label)

    ASSETS.mkdir(parents=True, exist_ok=True)
    for name, content in graphics.items():
        destination = ASSETS / name
        if not destination.exists() or destination.read_text() != content:
            destination.write_text(content)
    print(f"Generated {len(graphics)} SVGs for {USERNAME} from public repository data.")


if __name__ == "__main__":
    generate()
