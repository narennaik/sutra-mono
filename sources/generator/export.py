"""Write the Sutra Mono UFO sources.

    python sources/generator/export.py

Each weight is the same set of skeletons stroked with a different pen. Outlines are fitted to
cubic Béziers with nodes at extrema; accented letters are components with mark anchors.
"""
import os, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ufoLib2
from ufoLib2.objects import Anchor, Component
from fontTools.agl import AGL2UV, UV2AGL
from geometry import stroke, fit_polygons, draw_contours
from skeletons import skeletons, W, X, H, A, C, L, R, TOP_X

VERSION = (1, 100)
FAMILY = 'Sutra Mono'
REPO = 'https://github.com/narennaik/sutra-mono'
DESIGNER = 'Naren Laxmidas Naik'
WEIGHTS = [('Light', 300, 58), ('Regular', 400, 82), ('Bold', 700, 114)]
PEN_ASPECT = 0.92        # horizontals 8% lighter than verticals

EXTRA_UV = {
    'dotlessj': 0x0237, 'Dcroat': 0x0110, 'Eth': 0x00D0, 'dcroat': 0x0111, 'quotesingle': 0x27, 'grave': 0x60,
    'minus': 0x2212, 'uni00A0': 0x00A0, 'space': 0x20,
}

TOP_MARKS = {0x0300: 'gravecomb', 0x0301: 'acutecomb', 0x0302: 'uni0302', 0x0303: 'tildecomb', 0x0304: 'uni0304',
             0x0306: 'uni0306', 0x0307: 'uni0307', 0x0308: 'uni0308', 0x030A: 'uni030A', 0x030B: 'uni030B',
             0x030C: 'uni030C'}
ASCENDER_BASES = set('bdhklt')
BOTTOM_X = {'k': L + 40, 'r': L + 40, 'R': C - 30, 'L': C - 20, 'l': C}


def uv_of(name):
    if name in EXTRA_UV:
        return EXTRA_UV[name]
    if name.startswith('uni') and len(name) == 7:
        try:
            return int(name[3:], 16)
        except ValueError:
            return None
    return AGL2UV.get(name)


def name_of(uv):
    for k, v in EXTRA_UV.items():
        if v == uv:
            return k
    return UV2AGL.get(uv) or f'uni{uv:04X}'


def latin_core():
    """GF Latin Core code points (from the googlefonts glyphsets package when available)."""
    try:
        import glyphsets
        return sorted(set(glyphsets.unicodes_per_glyphset('GF_Latin_Core')))
    except Exception:
        return []


def composites(drawn):
    """Precomposed letters → list of (component, dx, dy)."""
    out = {}
    targets = set(latin_core()) | {0x1EF2, 0x1EF3}
    for uv in sorted(targets):
        nm = name_of(uv)
        if nm in drawn:
            continue
        dec = unicodedata.decomposition(chr(uv))
        if not dec or dec.startswith('<'):
            continue
        parts = [int(p, 16) for p in dec.split()]
        if len(parts) != 2:
            continue
        base_uv, mark_uv = parts
        base = name_of(base_uv)
        base_ch = chr(base_uv)
        upper = base_ch.isupper()
        if mark_uv in TOP_MARKS:
            if base == 'i':
                base = 'dotlessi'
            if base == 'j':
                base = 'dotlessj'
            # apostrophe-style caron on letters with ascenders
            if mark_uv == 0x030C and base_ch in 'dltL':
                dx = {'d': R + 58 - C, 'l': 112, 't': 78, 'L': 28}[base_ch]
                dy = {'d': 0, 'l': 0, 't': -24, 'L': H - A}[base_ch]
                out[nm] = [(base, 0, 0), ('caronvertical', dx, dy)]
                continue
            mark = TOP_MARKS[mark_uv] + ('.case' if upper else '')
            tx = TOP_X.get(base, C) if not upper else TOP_X.get(base_ch, C)
            dy = 0
            if base_ch in ASCENDER_BASES:
                mark = TOP_MARKS[mark_uv] + '.case'
                dy = A - H + 14
            out[nm] = [(base, 0, 0), (mark, tx + (W - C), dy)]
        elif mark_uv in (0x0326, 0x0327):
            if mark_uv == 0x0327 and base_ch in 'cCsS':
                continue                                  # drawn with an attached cedilla
            if base_ch == 'g':
                out[nm] = [('g', 0, 0), ('commaturnedabovecomb', W, 0)]
                continue
            bx = BOTTOM_X.get(base_ch, C)
            out[nm] = [(base, 0, 0), ('uni0326', bx + (W - C), 0)]
        # ogonek letters are drawn whole
    return out


def anchors_for(name, uv):
    ch = chr(uv) if uv else ''
    out = []
    if ch.isalpha() and len(ch) == 1 and ch.isascii():
        top_y = H if ch.isupper() else (A if ch in ASCENDER_BASES else X)
        tx = TOP_X.get(ch, C) if ch.isupper() else TOP_X.get(name, C)
        out.append(Anchor(tx, top_y, 'top'))
        out.append(Anchor(BOTTOM_X.get(ch, C), 0, 'bottom'))
    if name in ('dotlessi', 'dotlessj'):
        out.append(Anchor(TOP_X.get(name, C), X, 'top'))
    if name == 'uni25CC':                          # dotted circle: shows a lone mark in context
        out += [Anchor(C, X, 'top'), Anchor(C, 0, 'bottom')]
    return out


def mark_anchors(name):
    if name.endswith('.case'):
        return [Anchor(C - W, H, '_top')]
    if name in ('uni0326', 'uni0327', 'uni0328'):
        return [Anchor(C - W, 0, '_bottom')]
    if name in ('caronvertical',):
        return []
    return [Anchor(C - W, X, '_top')]


FEATURES = """\
languagesystem DFLT dflt;
languagesystem latn dflt;

@TopMarks = [gravecomb acutecomb uni0302 tildecomb uni0304 uni0306 uni0307 uni0308 uni030A uni030B uni030C];
@TopMarksCase = [gravecomb.case acutecomb.case uni0302.case tildecomb.case uni0304.case uni0306.case uni0307.case uni0308.case uni030A.case uni030B.case uni030C.case];
@Upper = [A B C D E F G H I J K L M N O P Q R S T U V W X Y Z];

@BottomMarks = [uni0326 uni0327 uni0328];

feature ccmp {
    lookup dotless {
        sub [i j]' @TopMarks by [dotlessi dotlessj];
        sub [i j]' @BottomMarks @TopMarks by [dotlessi dotlessj];
        sub iogonek' @TopMarks by iogonek.dotless;
    } dotless;
    lookup casemarks {
        sub @Upper @TopMarks' by @TopMarksCase;
    } casemarks;
} ccmp;
"""


def build_ufo(style, weight, S, out_dir):
    G, M = skeletons(S, PEN_ASPECT)
    f = ufoLib2.Font()
    info = f.info
    info.familyName = FAMILY
    info.styleName = style
    info.styleMapFamilyName = FAMILY if style in ('Regular', 'Bold') else f'{FAMILY} {style}'
    info.styleMapStyleName = 'bold' if style == 'Bold' else 'regular'
    info.openTypeNamePreferredFamilyName = FAMILY if style not in ('Regular', 'Bold') else None
    info.openTypeNamePreferredSubfamilyName = style if style not in ('Regular', 'Bold') else None
    info.versionMajor, info.versionMinor = VERSION
    info.unitsPerEm = 1000
    info.xHeight, info.capHeight, info.ascender, info.descender = X, H, A, -200
    info.italicAngle = 0
    info.copyright = f'Copyright 2026 The Sutra Mono Project Authors ({REPO})'
    info.openTypeNameDesigner = DESIGNER
    info.openTypeNameDesignerURL = REPO
    info.openTypeNameManufacturerURL = REPO
    info.openTypeNameLicense = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
                                'This license is available with a FAQ at: https://openfontlicense.org')
    info.openTypeNameLicenseURL = 'https://openfontlicense.org'
    info.openTypeOS2WeightClass = weight
    info.openTypeOS2WidthClass = 5
    info.openTypeOS2VendorID = 'NONE'
    info.openTypeOS2Type = []                     # installable embedding (fsType 0)
    info.postscriptIsFixedPitch = True
    info.postscriptUnderlinePosition = -150
    info.postscriptUnderlineThickness = 75
    # Google Fonts vertical metrics: typo = hhea, no line gap, win covers every glyph in the family
    info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = 1000, -260, 0
    info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = 1000, -260, 0
    info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = 1000, 260
    info.openTypeOS2Selection = [7]               # USE_TYPO_METRICS
    info.openTypeOS2Panose = [2, 11, {300: 3, 400: 5, 700: 8}[weight], 9, 2, 2, 2, 2, 2, 4]
    info.openTypeOS2CodePageRanges = [0, 1]       # Latin 1, Latin 2
    info.openTypeOS2UnicodeRanges = [0, 1, 2, 31, 33, 35, 38]

    order = ['.notdef', 'space', 'uni00A0']
    # .notdef: an open box
    g = f.newGlyph('.notdef'); g.width = W
    p = g.getPen()
    for rect, ccw in (((80, 0, 520, 700), True), ((140, 60, 460, 640), False)):
        x0, y0, x1, y1 = rect
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)] if ccw else [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
        p.moveTo(pts[0]); [p.lineTo(q) for q in pts[1:]]; p.closePath()
    for nm, uv in (('space', 0x20), ('uni00A0', 0xA0)):
        g = f.newGlyph(nm); g.width = W; g.unicodes = [uv]

    def add(name, items, width, uv, anchors):
        g = f.newGlyph(name)
        g.width = width
        if uv:
            g.unicodes = [uv]
        draw_contours(fit_polygons(stroke(items, S, PEN_ASPECT)), g.getPen())
        g.anchors = anchors
        order.append(name)

    for name, items in G.items():
        add(name, items, W, uv_of(name), anchors_for(name, uv_of(name)))
    for name, items in M.items():
        uv = uv_of(name) if '.' not in name and name != 'caronvertical' and name != 'commaturnedabovecomb' else None
        if name == 'caronvertical':
            add(name, items, W, None, [])
        else:
            add(name, items, 0, uv, mark_anchors(name))
    # spacing grave is the ASCII backtick (already drawn); register composites
    for name, comps in composites(set(G) | set(M)).items():
        g = f.newGlyph(name)
        g.width = W
        uv = uv_of(name)
        if uv:
            g.unicodes = [uv]
        for base, dx, dy in comps:
            g.components.append(Component(base, (1, 0, 0, 1, dx, dy)))
        order.append(name)
    f.lib['public.glyphOrder'] = order
    f.features.text = FEATURES
    path = os.path.join(out_dir, f'SutraMono-{style}.ufo')
    f.save(path, overwrite=True)
    return path, len(order)


if __name__ == '__main__':
    out = os.path.normpath(os.path.join(HERE, '..'))
    for style, wt, S in WEIGHTS:
        path, n = build_ufo(style, wt, S, out)
        print(f'{os.path.relpath(path)}  {n} glyphs')
