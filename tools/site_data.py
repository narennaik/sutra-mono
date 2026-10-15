"""Export Sutra Mono's centre-line skeletons for the website (docs/assets/glyphs.json).

Each character maps to {"p": [[x, y, x, y, ...], ...], "d": [[x, y, r], ...], "k": [pen scale per path]}
in font units (1000 em, 600 advance, y up). The site strokes these paths with round caps and an
elliptical pen, which is exactly how the font itself is built.
"""
import json, os, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(ROOT, 'sources', 'generator'))
from shapely.geometry import LineString
import skeletons as SK
import export as EX

CHARS = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
         '.,:;!?\'"`#$%&()[]{}*+-=<>/\\|_^~@∘→←⇒⇐↦λ∀∃≡≠≅≤≥⊗⊕×∈⊥⊤∅¬·…')


def simplify(pts, tol=0.6):
    if len(pts) < 3:
        return pts
    ls = LineString(pts).simplify(tol, preserve_topology=False)
    return list(ls.coords)


def main(S=82):
    G, _ = SK.skeletons(S, EX.PEN_ASPECT)
    by_uv = {EX.uv_of(n): n for n in G if EX.uv_of(n)}
    out = {}
    for ch in CHARS:
        name = by_uv.get(ord(ch))
        if not name:
            continue
        paths, dots, pens = [], [], []
        for it in G[name]:
            if isinstance(it, tuple) and it[0] == 'dot':
                dots.append([round(it[1], 1), round(it[2], 1), round(it[3], 1)])
                continue
            k = 1.0
            if isinstance(it, tuple) and it[0] == 'pen':
                k, it = it[1], it[2]
            pts = simplify([tuple(p) for p in it])
            paths.append([round(v, 1) for p in pts for v in p])
            pens.append(round(k, 3))
        out[ch] = {'p': paths, 'd': dots, 'k': pens}
    meta = {'pen': S, 'aspect': EX.PEN_ASPECT, 'advance': SK.W, 'xHeight': SK.X, 'cap': SK.H,
            'ascender': SK.A, 'descender': -200, 'n': 2.7}
    dst = os.path.join(ROOT, 'docs', 'assets', 'glyphs.json')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w') as f:
        json.dump({'meta': meta, 'glyphs': out}, f, separators=(',', ':'), ensure_ascii=False)
    print(dst, len(out), 'glyphs', os.path.getsize(dst) // 1024, 'KB')


if __name__ == '__main__':
    main()
