"""Generate self-hosted profile artwork using only public GitHub repository data."""
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'xsqlverx'
FEATURED = ['AURA-V2', 'arise', 'Skholario', 'Emerald-math']
COLORS = ['#bca8ff', '#ffb393', '#cff78b', '#7cdbbd']


def load_repositories():
    if len(sys.argv) > 1:
        return json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    repos = []
    for page in range(1, 101):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'xsqlverx-profile',
                   'X-GitHub-Api-Version': '2022-11-28'}
        token = os.environ.get('GH_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(
            f'https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}',
            headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
    raise RuntimeError('Repository pagination exceeded its safety limit')


def render(repos, mode, stamp):
    dark = mode == 'dark'
    bg, fg, muted, line = ('#10131c', '#f4f1eb', '#a2a9bd', '#2a3041') if dark else (
        '#f2f0eb', '#171a22', '#596175', '#d6d5d3')
    accents = COLORS if dark else ['#6b45bf', '#b54b27', '#507d19', '#087b60']
    languages = len({r['language'] for r in repos if r.get('language')})
    rows = []
    by_name = {r['name']: r for r in repos}
    for i, name in enumerate(FEATURED):
        repo = by_name[name]
        date = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00')).strftime('%d %b %Y')
        y = 194 + i * 51
        color = accents[i]
        rows.append(f'<circle cx="48" cy="{y-6}" r="5" fill="{color}"/>'
                    f'<text x="69" y="{y}" font-size="23" fill="{fg}">{escape(name)}</text>'
                    f'<path d="M365 {y-7}H775" stroke="{line}" stroke-dasharray="2 8"/>'
                    f'<text x="816" y="{y}" font-size="19" fill="{muted}">{date}</text>'
                    f'<path d="M1130 {y-15}l12 12m-12 0h12v-12" fill="none" stroke="{color}" stroke-width="2"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="418" viewBox="0 0 1200 418" role="img" aria-labelledby="title desc">
<title id="title">Public repository pulse</title><desc id="desc">{len(repos)} public original projects, {languages} primary languages. Latest push dates for four featured projects.</desc>
<rect width="1200" height="418" rx="22" fill="{bg}"/>
<g font-family="Arial, Helvetica, sans-serif">
<text x="42" y="44" font-size="17" letter-spacing="3" fill="{muted}">THE BUILD CONTINUES</text>
<text x="42" y="112" font-size="47" font-weight="700" letter-spacing="-1" fill="{fg}">{len(repos)} projects<tspan fill="{muted}"> / </tspan>{languages} languages<tspan fill="{muted}"> / </tspan>still building.</text>
<path d="M42 144H1158" stroke="{line}"/>{''.join(rows)}
<path d="M42 365H1158" stroke="{line}"/>
<text x="42" y="395" font-size="15" fill="{muted}" letter-spacing="1">PUBLIC ORIGINAL REPOSITORIES · LAST PUSH DATES</text>
<text x="1158" y="395" text-anchor="end" font-size="15" fill="{muted}">{stamp} UTC</text>
</g></svg>'''


def main():
    repos = [r for r in load_repositories() if not r.get('private', True)
             and not r['fork'] and r['name'].lower() != USER]
    by_name = {r['name']: r for r in repos}
    missing = set(FEATURED) - by_name.keys()
    if missing:
        raise ValueError('Featured repository missing; preserving previous snapshot: ' + ', '.join(sorted(missing)))
    stamp = datetime.now(timezone.utc).strftime('%d %b %Y')
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    for mode in ['dark', 'light']:
        (assets / f'pulse-{mode}.svg').write_text(render(repos, mode, stamp), encoding='utf-8')
    languages = len({r['language'] for r in repos if r.get('language')})
    latest = sorted(repos, key=lambda r: r['pushed_at'], reverse=True)[0]
    snapshot = (f'**{len(repos)} public original projects · {languages} primary languages**  \n'
                f'Latest push: [{latest["name"]}]({latest["html_url"]}) · '
                f'{latest["pushed_at"][:10]} · Snapshot: {stamp} UTC.')
    readme = ROOT / 'README.md'
    content = readme.read_text(encoding='utf-8')
    updated, count = re.subn(r'<!-- pulse:start -->.*?<!-- pulse:end -->',
                            '<!-- pulse:start -->\n' + snapshot + '\n<!-- pulse:end -->',
                            content, flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one public snapshot marker')
    readme.write_text(updated, encoding='utf-8')
    print(f'Refreshed {len(repos)} public original projects on {stamp} UTC')


if __name__ == '__main__':
    main()
