"""Build the SQLVER / KENAZ SVG loop. Standard library only; no runtime JS/fonts.

The glyph outlines are frozen in name-glyphs.json. Motion uses transforms and
opacity rather than font-size, letter-spacing, or browser layout changes.
"""
from pathlib import Path
from math import cos, sin, pi, tan
import json
import re

ROOT = Path(__file__).resolve().parents[1]
GLYPHS = json.loads((ROOT / "assets/name-glyphs.json").read_text(encoding="utf-8"))
DURATION = 16.0


def pct(seconds):
    return f"{seconds / DURATION * 100:.4f}%"


def frames(name, rows):
    return "@keyframes " + name + "{" + "".join(
        pct(t) + "{" + v + "}" for t, v in rows
    ) + "}"


def pose(x, y=0, sx=1, sy=1, angle=0):
    return f"transform:translate({x:.3f}px,{y:.3f}px) rotate({angle:.3f}deg) scale({sx:.4f},{sy:.4f});"


def word_layout(word):
    widths = [GLYPHS[c]["width"] for c in word]
    total = sum(widths) + 10 * (len(word) - 1)
    x = (636 - total) / 2
    positions = []
    for width in widths:
        positions.append(x)
        x += width + 10
    return positions


def make_name(mode):
    dark = mode == "dark"
    fg, accent = ("#f5f2eb", "#c2aeff") if dark else ("#191b24", "#7650bf")
    palette = [
        ("#ffb362", "#c45fcb"), ("#ffd1a1", "#efa49e"),
        ("#f5f2eb", "#e2cbea"), ("#e9f5ef", "#aee3df"),
        ("#b5ece7", "#7ac9d4"), ("#98e1e5", "#80c5dd"),
    ] if dark else [
        ("#b75a10", "#903b9c"), ("#b35b33", "#a34f75"),
        ("#5d3b80", "#7650bf"), ("#247c81", "#407797"),
        ("#176c74", "#4c77a1"), ("#276d81", "#466baa"),
    ]
    defs = []
    for c, data in GLYPHS.items():
        defs.append(f'<path id="name-{c}" d="{data["path"]}"/>')
    for i, (top, bottom) in enumerate(palette):
        defs.append(f'<linearGradient id="name-ink-{i}" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
    defs.append('<clipPath id="name-window"><rect x="12" y="76" width="733" height="171"/></clipPath>')
    css = [
        '.kinetic-running{display:none}.kinetic-fallback{display:inline}',
        '@media(prefers-reduced-motion:no-preference){.kinetic-running{display:inline}.kinetic-fallback{display:none}}',
        '.name-main,.name-track,.name-char{animation-duration:16s;animation-iteration-count:infinite;animation-timing-function:linear;animation-fill-mode:both}',
        '.name-char{transform-origin:0 0;vector-effect:non-scaling-stroke}',
        '.name-main{stroke:' + fg + ';stroke-width:1.25;stroke-linejoin:round;stroke-opacity:0}.name-track{fill:' + accent + '}',
        '.name-kenaz *{animation-delay:-8s!important}',
        '.name-main{animation-name:name-main-life,name-ink-life}.name-track{animation-name:name-track-life}',
        frames('name-main-life', [(0,'opacity:1'),(4.76,'opacity:1'),(4.8,'opacity:0'),(15.999,'opacity:0'),(16,'opacity:1')]),
        frames('name-ink-life', [(0,f'--name-fill:{accent};stroke-opacity:0'),(1.5,f'--name-fill:{accent};stroke-opacity:0'),(1.501,'--name-fill:transparent;stroke-opacity:1'),(2.519,'--name-fill:transparent;stroke-opacity:1'),(2.52,'--name-fill:initial;stroke-opacity:0'),(15.999,'--name-fill:initial;stroke-opacity:0'),(16,f'--name-fill:{accent};stroke-opacity:0')]),
        frames('name-track-life', [(0,'opacity:0'),(4.5,'opacity:0'),(4.74,'opacity:1'),(7.96,'opacity:1'),(8.38,'opacity:0'),(16,'opacity:0')]),
    ]
    words = []
    for word in ('SQLVER', 'KENAZ'):
        normal = word_layout(word)
        n = len(word)
        main, track = [], []
        for i, c in enumerate(word):
            data = GLYPHS[c]
            x = normal[i]
            delay = i * .07
            key = f'name-{word.lower()}-{i}'
            # First and last letters stretch tall; inner letters form two rows.
            if i == 0:
                stack = (117, -1, .95, 1.18)
            elif i == n - 1:
                stack = (437, -1, .95, 1.18)
            elif word == 'SQLVER':
                stack = (225 + ((i - 1) // 2) * 105, 0 if i % 2 else 73, .84, .57)
            else:
                stack = ((226, 0, .84, .57) if i == 1 else
                         (282, 73, .84, .57) if i == 2 else (332, 0, .84, .57))
            xs, ys, sx, sy = stack
            css.append(frames(key, [
                (0,pose(x,145, .96,1,9)+'opacity:0'),
                (.03 + delay,pose(x,145,.96,1,9)+'opacity:0;animation-timing-function:cubic-bezier(.16,1,.3,1)'),
                (.32 + delay,pose(x,-10,1,1,-2)+'opacity:1;animation-timing-function:ease-in-out'),
                (.49 + delay,pose(x,4,1,1,.5)+'opacity:1;animation-timing-function:ease-out'),
                (.71 + delay,pose(x)+'opacity:1'),
                (1.5,pose(x)),
                (1.7,pose(318+(x-318)*1.055,0,1.055,1)+'animation-timing-function:ease-in-out'),
                (1.95,pose(318+(x-318)*1.105,0,1.105,1)+'animation-timing-function:ease-in-out'),
                (2.34,pose(x)),
                (2.56,pose(x)+'animation-timing-function:cubic-bezier(.22,1,.36,1)'),
                (2.98,pose(xs,ys,sx,sy*1.03)+'animation-timing-function:ease-out'),
                (3.17,pose(xs,ys,sx,sy)),
                (4.28,pose(xs,ys,sx,sy)+'animation-timing-function:cubic-bezier(.7,0,.84,0)'),
                (4.8,pose(xs,ys-210,sx,sy)),
                (15.999,pose(x,145,.96,1,9)+'opacity:0'),
                (16,pose(x,145,.96,1,9)+'opacity:0'),
            ]))
            spread = (i - (n - 1) / 2) * 9
            css.append(frames(key+'-track', [
                (0,pose(x,150)),(4.5,pose(x,150)+'animation-timing-function:cubic-bezier(.16,1,.3,1)'),
                (4.99,pose(x)),(5.15,pose(x)+'animation-timing-function:cubic-bezier(.22,1,.36,1)'),
                (6.32,pose(x+spread)),(7.96,pose(x+spread)),
                (8.38,pose(x+spread, -8)),(16,pose(x,150)),
            ]))
            main.append(f'<use class="name-char" style="animation-name:{key};fill:var(--name-fill,url(#name-ink-{round(i*5/(n-1))}))" href="#name-{c}"/>')
            track.append(f'<use class="name-char" style="animation-name:{key}-track" href="#name-{c}"/>')
        words.append(f'<g class="name-{word.lower()}"><g class="name-main">{"".join(main)}</g><g class="name-track">{"".join(track)}</g></g>')
    static = ''.join(f'<use href="#name-{c}" transform="translate({x:.3f},0)"/>' for c,x in zip('SQLVER',word_layout('SQLVER')))
    return (f'<g id="name-kinetic"><defs>{"".join(defs)}</defs><style>{"".join(css)}</style>'
            f'<g clip-path="url(#name-window)"><g transform="translate(43,89)">'
            f'<g class="kinetic-fallback" fill="{fg}">{static}<path d="M647 125h40v12h-40z" fill="{accent}"/></g>'
            f'<g class="kinetic-running">{"".join(words)}</g></g></g></g><!-- /name-kinetic -->')


def ellipse_path(center, u, v):
    """Four cubic arcs: a compact projected circle, error below 0.05 px."""
    def point(t):
        return (center[0] + u[0]*cos(t) + v[0]*sin(t),
                center[1] + u[1]*cos(t) + v[1]*sin(t))
    def tangent(t):
        return (-u[0]*sin(t) + v[0]*cos(t), -u[1]*sin(t) + v[1]*cos(t))
    def xy(p):
        return f'{p[0]:.2f},{p[1]:.2f}'
    result = ['M' + xy(point(0))]
    k = 4/3*tan(pi/8)
    for i in range(4):
        a, b = i*pi/2, (i+1)*pi/2
        p, q, dp, dq = point(a), point(b), tangent(a), tangent(b)
        c1 = (p[0]+k*dp[0], p[1]+k*dp[1])
        c2 = (q[0]-k*dq[0], q[1]-k*dq[1])
        result.append('C' + xy(c1) + ' ' + xy(c2) + ' ' + xy(q))
    return ' '.join(result) + 'Z'


def make_orbit(mode):
    """Keep the mesh geometry cached; animate one transform and one satellite."""
    wire, lime = ('#c2aeff','#cff78b') if mode == 'dark' else ('#7650bf','#537e25')
    def project(x, y, z):
        a, b = .37, -.38
        yy = y*cos(a)-z*sin(a)
        return (x*cos(b)-yy*sin(b), x*sin(b)+yy*cos(b))
    center, radius = (982,220), 153
    latitudes = []
    for j in range(-7,8):
        lat = j*pi/18
        cy = project(0,radius*sin(lat),0)
        u = project(radius*cos(lat),0,0)
        v = project(0,0,radius*cos(lat))
        d = ellipse_path((center[0]+cy[0],center[1]+cy[1]),u,v)
        latitudes.append(f'<path d="{d}" stroke-opacity=".46"/>')
    meridians = []
    for j in range(7):
        longitude = j*pi/7
        u = project(radius*cos(longitude),0,radius*sin(longitude))
        v = project(0,radius,0)
        meridians.append(f'<path class="orb-meridian" d="{ellipse_path(center,u,v)}"/>')
    angle = -26*pi/180
    orbit = ellipse_path(center,(191*cos(angle),191*sin(angle)),(-46*sin(angle),46*cos(angle)))
    start = (center[0]+191*cos(angle), center[1]+191*sin(angle))
    return (f'<g id="orb-kinetic"><style>.orb-motion{{display:none}}.orb-still{{display:inline}}'
            '.orb-wire-spin{transform-origin:982px 220px}'
            '@media(prefers-reduced-motion:no-preference){.orb-motion{display:inline}.orb-still{display:none}.orb-wire-spin{animation:orb-wire-turn 36s linear infinite;will-change:transform}}'
            '@keyframes orb-wire-turn{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}'
            f'</style><defs><path id="orb-orbit-track" d="{orbit}"/></defs>'
            f'<g clip-path="url(#orb)" fill="none" stroke="{wire}" stroke-width="1.1"><g class="orb-wire-spin">'
            f'{"".join(latitudes)}<g stroke-opacity=".48">{"".join(meridians)}</g></g></g>'
            f'<ellipse cx="982" cy="220" rx="191" ry="46" transform="rotate(-26 982 220)" stroke="{lime}" stroke-width="2" fill="none"/>'
            f'<g class="orb-motion"><g class="orb-comet" fill="{lime}"><circle r="11" opacity=".12"/><circle r="6"/>'
            '<animateMotion dur="8s" repeatCount="indefinite" calcMode="paced"><mpath href="#orb-orbit-track"/></animateMotion></g></g>'
            f'<circle class="orb-still" cx="{start[0]:.2f}" cy="{start[1]:.2f}" r="6" fill="{lime}"/></g><!-- /orb-kinetic -->')


for mode in ('dark','light'):
    path = ROOT / f'assets/hero-kinetic-{mode}.svg'
    source = (ROOT / f'assets/hero-{mode}.svg').read_text(encoding='utf-8')
    replacement = make_name(mode)
    if '<g id="name-kinetic">' in source:
        source, count = re.subn(r'<g id="name-kinetic">.*?<!-- /name-kinetic -->',lambda _:replacement,source,flags=re.S)
    else:
        source, count = re.subn(r'<text x="43" y="215"[^>]*>SQLVER<tspan[^>]*>_</tspan></text>',lambda _:replacement,source)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one name region, found {count}')
    # Replace only the globe, its ring and satellite; the header layout stays.
    source, count = re.subn(
        r'<g clip-path="url\(#orb\)">.*?</g>\s*<ellipse cx="982".*?/>\s*<circle cx="1151".*?/>',
        lambda _:make_orbit(mode),source,flags=re.S)
    if count != 1:
        raise SystemExit(f'{path}: expected one original globe region, found {count}')
    source = source.replace('<rect x="760" y="60" width="420" height="305"/></clipPath>',
                            '<rect x="760" y="58" width="420" height="316"/></clipPath>')
    source = source.replace('aria-label="Sqlver. Useful software.', 'aria-label="Sqlver / Kenaz. Useful software.')
    path.write_text(source,encoding='utf-8')
    print(f'{path.name}: {len(source.encode()):,} bytes; name loop + rotating globe + 8s orbit')
