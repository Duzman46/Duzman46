"""Render the public GitHub contribution calendar as a living circuit network."""
import argparse
import datetime as dt
from html.parser import HTMLParser
import re
from pathlib import Path
from urllib.request import Request, urlopen


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'data-date' in a and 'data-level' in a:
            day = dt.date.fromisoformat(a['data-date'])
            level = int(a['data-level'])
            if 0 <= level <= 4:
                self.days.append((day, level))


def render(html, username):
    calendar = Calendar()
    calendar.feed(html)
    days = sorted(set(calendar.days))
    if len(days) < 300:
        raise ValueError('GitHub did not return a complete contribution calendar; keeping the existing graphic.')
    total_match = re.search(r'id="js-contribution-activity-description"[^>]*>\s*([\d,]+)', html)
    total = int(total_match.group(1).replace(',', '')) if total_match else None
    if total is None:
        raise ValueError('Missing public contribution total; keeping the existing graphic.')
    active = sum(level > 0 for _, level in days)
    first = days[0][0]
    colors = ['#152b3c', '#245777', '#3588ab', '#4bc4d3', '#9cfcdf']
    tiles = []
    last_x = 0
    for day, level in days:
        col = (day-first).days // 7
        row = (day.weekday()+1) % 7
        x, y = 64+col*28, 132+row*27
        last_x = max(last_x, x)
        tiles.append(f'<g><title>{day.isoformat()}: contribution intensity {level}/4</title>'
                     f'<path d="M{x+10} {y-2}V{y-7}M{x+20} {y+10}h8" stroke="#1d3b50"/>'
                     f'<rect x="{x}" y="{y}" width="20" height="20" rx="4" fill="{colors[level]}" '
                     f'stroke="{colors[level] if level else "#254155"}"/>'
                     +(f'<rect class="chip" style="animation-delay:{(col*.13+row*.3)%5:.2f}s" x="{x+6}" y="{y+6}" '
                       f'width="8" height="8" rx="2" fill="#d9fffa" opacity="{.2+level*.15:.2f}"/>' if level else '')+'</g>')
    # Only anonymous aggregate activity enters the SVG. No repository names or private project details.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="418" viewBox="0 0 1600 418" role="img" aria-labelledby="title desc">
<title id="title">{username}'s living energy network — {total} public profile contributions</title>
<desc id="desc">Each chip is a day in the actual GitHub contribution calendar. Brighter chips indicate more activity. {active} days have contributions. Calendar range {days[0][0]} to {days[-1][0]}.</desc>
<defs><linearGradient id="power"><stop stop-color="#61e7f7"/><stop offset=".5" stop-color="#c49aff"/><stop offset="1" stop-color="#ffca70"/></linearGradient></defs>
<style>@keyframes chip{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}@keyframes current{{to{{stroke-dashoffset:-1900}}}}.chip{{animation:chip 5s infinite}}.current{{stroke-dasharray:60 900;animation:current 8s linear infinite}}@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect x="1" y="1" width="1598" height="416" rx="20" fill="#0b1321" stroke="#244257"/>
<text x="40" y="44" font-family="Consolas,monospace" font-size="17" fill="#68e8f7" letter-spacing="3">THE GRID IS ALIVE</text>
<text x="40" y="88" font-family="Segoe UI,Arial,sans-serif" font-size="32" font-weight="700" fill="#f4f8ff">Every commit adds energy to the world.</text>
<text x="1560" y="44" text-anchor="end" font-family="Consolas,monospace" font-size="17" fill="#a8bdd3">{total} CONTRIBUTIONS / {active} ACTIVE DAYS</text>
<path d="M42 112H{last_x+32}V332H42Z" fill="none" stroke="#22445d"/>
<path d="M42 112H{last_x+32}V332H42Z" class="current" fill="none" stroke="url(#power)" stroke-width="2"/>
{''.join(tiles)}
<text x="40" y="368" font-family="Consolas,monospace" font-size="14" fill="#7c9ab6">REAL CONTRIBUTION DATA · {days[0][0].strftime('%b %Y').upper()} → {days[-1][0].strftime('%b %Y').upper()}</text>
<text x="40" y="398" font-family="Segoe UI,Arial,sans-serif" font-size="14" fill="#57718f">Small steps power bigger worlds.</text>
<text x="1324" y="368" font-family="Consolas,monospace" font-size="13" fill="#7c9ab6">IDLE</text>
{''.join(f'<rect x="{1375+i*25}" y="355" width="17" height="17" rx="3" fill="{c}"/>' for i,c in enumerate(colors))}
<text x="1520" y="368" font-family="Consolas,monospace" font-size="13" fill="#9cfcdf">LIVE</text>
</svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path)
    parser.add_argument('--username', default='Duzman46')
    parser.add_argument('--output', type=Path, default=Path('world-energy.svg'))
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]{1,39}', args.username):
        raise ValueError('Invalid GitHub username')
    if args.html:
        html = args.html.read_text(encoding='utf-8-sig')
    else:
        req = Request(f'https://github.com/users/{args.username}/contributions', headers={'User-Agent':'CodeWorldProfile/1.0'})
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
    svg = render(html, args.username)
    # Replace the output only after validation and a complete render succeeded.
    args.output.write_text(svg, encoding='utf-8')
    print(f'Rendered {args.output}')


if __name__ == '__main__':
    main()
