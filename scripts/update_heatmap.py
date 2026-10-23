"""Draw an animated calendar from the same public day counts GitHub displays.

Original implementation. Reveal effect inspired by AVIVASHISHTA29's profile:
https://github.com/AVIVASHISHTA29/AVIVASHISHTA29
Only the public contributions HTML is fetched; no token or private repo data.
"""
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'xsqlverx'


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells = {}
        self.tooltips = {}
        self.heading = []
        self.in_heading = False
        self.tooltip_target = None

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'h2' and attrs.get('id') == 'js-contribution-activity-description':
            self.in_heading = True
        if tag == 'td' and 'data-date' in attrs and 'data-level' in attrs:
            day = date.fromisoformat(attrs['data-date'])
            level = int(attrs['data-level'])
            if not 0 <= level <= 4 or day in self.cells:
                raise ValueError('Unexpected GitHub contribution cell')
            self.cells[day] = {'id': attrs['id'], 'date': day, 'level': level}
        if tag == 'tool-tip' and attrs.get('for', '').startswith('contribution-day-component-'):
            self.tooltip_target = attrs['for']
            self.tooltips[self.tooltip_target] = []

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)
        if self.tooltip_target is not None:
            self.tooltips[self.tooltip_target].append(data)

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_heading = False
        if tag == 'tool-tip':
            self.tooltip_target = None

    def calendar(self):
        days = sorted(self.cells.values(), key=lambda cell: cell['date'])
        if not 350 <= len(days) <= 378:
            raise ValueError(f'Incomplete public calendar ({len(days)} days); preserving existing artwork')
        for index, cell in enumerate(days):
            if index and cell['date'] != days[index - 1]['date'] + timedelta(days=1):
                raise ValueError('Public calendar has a missing date')
            label = ''.join(self.tooltips.get(cell['id'], [])).strip()
            match = re.match(r'([\d,]+) contributions?\b', label)
            if label.startswith('No contributions'):
                count = 0
            elif match:
                count = int(match[1].replace(',', ''))
            else:
                raise ValueError(f'Missing contribution count for {cell["date"]}')
            if (count == 0) != (cell['level'] == 0):
                raise ValueError('Public day count and colour level disagree')
            cell['count'] = count
        match = re.search(r'([\d,]+)\s+contributions?\s+in the last year', ' '.join(self.heading))
        if not match:
            raise ValueError('Public contribution total missing')
        total = int(match[1].replace(',', ''))
        if sum(cell['count'] for cell in days) != total:
            raise ValueError('Day counts do not match GitHub\'s displayed total')
        return days, total


def render(days, total, theme):
    dark = theme == 'dark'
    bg, fg, muted = ('#0d1018', '#f5f2eb', '#a2a9bd') if dark else ('#eeece6', '#191b24', '#596175')
    colors = ['#1c2430', '#0e4429', '#006d32', '#26a641', '#39d353'] if dark else [
        '#dedfd9', '#b4dda1', '#73bd59', '#3c9238', '#216e39']
    start = days[0]['date'] - timedelta(days=(days[0]['date'].weekday() + 1) % 7)
    columns = (days[-1]['date'] - start).days // 7 + 1
    pitch, size, left, top = 20, 16, 65, 53
    width, height = left + columns * pitch + 30, 239
    cells, months = [], []
    previous_month = None
    previous_label_x = -100
    for cell in days:
        offset = (cell['date'] - start).days
        column, row = divmod(offset, 7)
        x, y = left + column * pitch, top + row * pitch
        month = (cell['date'].year, cell['date'].month)
        if month != previous_month:
            # Start month labels at the next Sunday, as the native calendar does.
            label_x = left + min(column + (1 if row else 0), columns - 1) * pitch
            if label_x - previous_label_x >= 36:
                months.append(f'<text x="{label_x}" y="34">{cell["date"]:%b}</text>')
                previous_label_x = label_x
            previous_month = month
        delay = column * .057 + row * .038
        label = f'{cell["date"]}: {cell["count"]:,} contribution' + ('' if cell['count'] == 1 else 's')
        active = ' class="active"' if cell['count'] else ''
        cells.append(f'<g class="day" style="animation-delay:{delay:.3f}s">'
                     f'<title>{escape(label)}</title><rect{active} x="{x}" y="{y}" '
                     f'width="{size}" height="{size}" rx="3" fill="{colors[cell["level"]]}" '
                     f'style="animation-delay:{delay:.3f}s"/></g>')
    labels = ''.join(f'<text x="12" y="{top + row*pitch + 13}">{label}</text>'
                     for row, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')])
    legend_x = width - 179
    legend = f'<text x="{legend_x-46}" y="222">Less</text>'
    for level, color in enumerate(colors):
        legend += f'<rect x="{legend_x+level*20}" y="209" width="16" height="16" rx="3" fill="{color}"/>'
    legend += f'<text x="{legend_x+107}" y="222">More</text>'
    description = (f'{total:,} contributions in the last year for {USER}. '
                   f'{days[0]["date"]} through {days[-1]["date"]}. Each square is one day. '
                   'Green intensity follows GitHub\'s public contribution levels.')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{USER}'s contribution heatmap</title><desc id="desc">{escape(description)}</desc>
<style>
text{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;font-size:16px;fill:{muted}}}
.day{{transform-box:fill-box;transform-origin:center;animation:reveal .52s cubic-bezier(.2,.7,.2,1) backwards}}
.active{{animation:gleam .68s ease-out backwards}}
@keyframes reveal{{0%{{opacity:0;transform:scale(.3)}}65%{{opacity:1;transform:scale(1.08)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes gleam{{0%{{filter:brightness(1.9)}}100%{{filter:brightness(1)}}}}
@media(prefers-reduced-motion:reduce){{.day,.active{{animation:none!important}}}}
</style>
<rect width="{width}" height="{height}" rx="18" fill="{bg}"/>
{''.join(months)}{labels}{''.join(cells)}
<text x="{left}" y="222" style="font-size:18px;font-weight:600;fill:{fg}">{total:,} contributions in the last year</text>
{legend}</svg>'''


def main():
    if len(sys.argv) > 1:
        source = Path(sys.argv[1]).read_text(encoding='utf-8-sig')
    else:
        request = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={
            'User-Agent': 'xsqlverx-profile', 'Accept': 'text/html', 'Accept-Language': 'en-US,en;q=0.9'})
        with urllib.request.urlopen(request, timeout=30) as response:
            source = response.read().decode('utf-8')
    parser = CalendarParser()
    parser.feed(source)
    days, total = parser.calendar()
    readme = ROOT / 'README.md'
    snapshot = (f'**{total:,} contributions in the last year** · '
                f'Calendar through {days[-1]["date"]:%d %b %Y}.')
    updated, count = re.subn(r'<!-- heatmap:start -->.*?<!-- heatmap:end -->',
                            '<!-- heatmap:start -->\n' + snapshot + '\n<!-- heatmap:end -->',
                            readme.read_text(encoding='utf-8'), flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one heatmap snapshot marker')
    # Finish parsing and validating before replacing any committed artwork.
    artwork = {theme: render(days, total, theme) for theme in ['dark', 'light']}
    for theme, svg in artwork.items():
        (ROOT / 'assets' / f'contributions-{theme}.svg').write_text(svg, encoding='utf-8')
    readme.write_text(updated, encoding='utf-8')
    print(f'Validated {len(days)} dates and {total:,} contributions; rendered both themes')


if __name__ == '__main__':
    main()
