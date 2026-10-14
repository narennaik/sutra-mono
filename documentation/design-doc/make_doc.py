import sys, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from fontTools.ttLib import TTFont
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'sources', 'generator'))
import geometry, skeletons as SK, export as EX


class build:
    """Adapter: the doc's diagrams draw the same skeletons that build the font."""
    sq = staticmethod(geometry.sq)

    @staticmethod
    def glyphs(S):
        G, _ = SK.skeletons(S, EX.PEN_ASPECT)
        out = {}
        for name, items in G.items():
            uv = EX.uv_of(name)
            if uv:
                out[chr(uv)] = items
        return out

FD = os.path.join(HERE, 'fonts') + os.sep
SD = os.path.join(ROOT, 'fonts', 'ttf') + os.sep
for n, f in [('Sutra', SD + 'SutraMono-Regular.ttf'), ('SutraL', SD + 'SutraMono-Light.ttf'),
             ('SutraB', SD + 'SutraMono-Bold.ttf'), ('Serif', FD + 'Newsreader-Text.ttf'),
             ('SerifM', FD + 'Newsreader-TextMedium.ttf'), ('SerifI', FD + 'Newsreader-Italic.ttf'),
             ('Disp', FD + 'Newsreader-Display.ttf'), ('DispI', FD + 'Newsreader-DisplayItalic.ttf')]:
    pdfmetrics.registerFont(RLFont(n, f))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('Serif', normal='Serif', bold='SerifM', italic='SerifI', boldItalic='SerifI')

PAPER = HexColor('#F1F3F2'); SHEET = HexColor('#FAFBFA'); INK = HexColor('#16212A')
MUTED = HexColor('#5E6B72'); RULE = HexColor('#D3DADB'); BLUE = HexColor('#1E5C73')
BLUE_SOFT = HexColor('#D7E6EB'); NIGHT = HexColor('#121B21'); NIGHT_FG = HexColor('#DCE4E7')
NIGHT_MUTED = HexColor('#7D8E96'); NIGHT_BLUE = HexColor('#74B6CB'); NIGHT_WARM = HexColor('#D9B98C')

PW, PH = 595.28, 841.89
M = 58
COL = PW - 2 * M

body = ParagraphStyle('body', fontName='Serif', fontSize=11.4, leading=17.2, textColor=INK, alignment=TA_LEFT)
lede = ParagraphStyle('lede', parent=body, fontName='SerifI', fontSize=15, leading=22, textColor=INK)
small = ParagraphStyle('small', parent=body, fontSize=9.4, leading=13.5, textColor=MUTED)
cap = ParagraphStyle('cap', parent=body, fontName='SerifI', fontSize=9.6, leading=13.5, textColor=MUTED)

TT = {w: TTFont(SD + f'SutraMono-{w}.ttf') for w in ('Light', 'Regular', 'Bold')}


from fontTools.pens.basePen import BasePen


class _RLPen(BasePen):
    """Draw a TrueType glyph (quadratic curves, components) into a ReportLab path."""
    def __init__(self, gs, path, x, y, k):
        super().__init__(gs)
        self.p, self.x, self.y, self.k = path, x, y, k

    def _t(self, pt):
        return self.x + pt[0] * self.k, self.y + pt[1] * self.k

    def _moveTo(self, pt): self.p.moveTo(*self._t(pt))
    def _lineTo(self, pt): self.p.lineTo(*self._t(pt))
    def _curveToOne(self, a, b, c): self.p.curveTo(*self._t(a), *self._t(b), *self._t(c))
    def _closePath(self): self.p.close()


def draw_glyph(c, ch, x, y, size, color=INK, weight='Regular'):
    """x,y = origin of the em box (baseline), size = em in points"""
    f = TT[weight]
    gname = f.getBestCmap().get(ord(ch))
    if gname is None:
        return
    gs = f.getGlyphSet()
    p = c.beginPath()
    gs[gname].draw(_RLPen(gs, p, x, y, size / 1000))
    c.setFillColor(color)
    c.drawPath(p, fill=1, stroke=0, fillMode=0)


def draw_text_glyphs(c, s, x, y, size, color=INK, weight='Regular'):
    for i, ch in enumerate(s):
        if ch != ' ':
            draw_glyph(c, ch, x + i * size * 0.6, y, size, color, weight)


def skeleton(c, ch, x, y, size, color=BLUE, S=82, nodes=True, lw=0.9):
    k = size / 1000
    G = build.glyphs(S)
    c.setStrokeColor(color); c.setLineWidth(lw); c.setLineCap(1); c.setLineJoin(1)
    for p in G[ch]:
        if isinstance(p, tuple) and p[0] == 'pen':
            p = p[2]
        if isinstance(p, tuple):
            c.setFillColor(color); c.circle(x + p[1] * k, y + p[2] * k, 1.6, fill=1, stroke=0); continue
        path = c.beginPath(); path.moveTo(x + p[0][0] * k, y + p[0][1] * k)
        for px, py in p[1:]:
            path.lineTo(x + px * k, y + py * k)
        c.drawPath(path, stroke=1, fill=0)
        if nodes:
            c.setFillColor(color)
            for q in (p[0], p[-1]):
                c.circle(x + q[0] * k, y + q[1] * k, 1.7, fill=1, stroke=0)


def para(c, text, x, ytop, w, style=body):
    p = Paragraph(text, style)
    _, h = p.wrapOn(c, w, 2000)
    p.drawOn(c, x, ytop - h)
    return ytop - h


def page_bg(c, color=PAPER):
    c.setFillColor(color); c.rect(0, 0, PW, PH, fill=1, stroke=0)


def folio(c, n, label, dark=False):
    c.setFont('Sutra', 7.6); c.setFillColor(NIGHT_MUTED if dark else MUTED)
    c.drawString(M, 34, 'sutra mono  ∘  product document')
    c.drawRightString(PW - M, 34, f'{label}  {n:02d}')


def chapter_head(c, num, title, ytop):
    c.setFont('Sutra', 9); c.setFillColor(BLUE)
    c.drawString(M, ytop, f'## chapter {num}')
    c.setFont('Disp', 34); c.setFillColor(INK)
    c.drawString(M, ytop - 42, title)
    return ytop - 66


# ────────────────────────────────────────────────────────────
c = canvas.Canvas(os.path.join(HERE, 'Sutra-Mono-Design-Document.pdf'), pagesize=(PW, PH))
c.setTitle('Sutra Mono — Product Document'); c.setAuthor('Naren Naik'); c.setSubject('A monospace drawn as a single thread')

# ── 1 cover ─────────────────────────────────────────────────
page_bg(c)
# a large composition ring, the font's own ∘, bleeding off the top right
draw_glyph(c, '∘', PW - 560, PH - 520, 1150, BLUE_SOFT)
c.setFont('Sutra', 9); c.setFillColor(MUTED)
c.drawString(M, PH - 70, 'product document  ·  v1.100  ·  october 2026')
draw_text_glyphs(c, 'Sutra', M - 4, 370, 132, INK)
draw_text_glyphs(c, 'Mono', M - 4, 248, 132, BLUE)
para(c, 'A monospace drawn as a single thread. One centre-line, one pen, nothing that is there for show.',
     M, 205, 330, lede)
c.setStrokeColor(RULE); c.setLineWidth(0.6); c.line(M, 96, PW - M, 96)
c.setFont('Sutra', 8.2); c.setFillColor(MUTED)
c.drawString(M, 78, '3 weights  ·  358 glyphs  ·  600/1000 em  ·  truetype')
c.drawRightString(PW - M, 78, 'designed by naren naik')
c.showPage()

# ── 2 prologue ──────────────────────────────────────────────
page_bg(c)
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, PH - 90, '## prologue')
c.setFont('Disp', 34); c.setFillColor(INK); c.drawString(M, PH - 132, 'The brief was')
c.setFont('DispI', 34); c.drawString(M, PH - 170, 'one sentence long.')
y = para(c, '“Smooth, with a flow between the characters. Nothing unessential. Rounded, and feeling '
            'complete, like San Francisco.”', M, PH - 205, COL * 0.86, lede)
y = para(c, 'Most coding fonts begin from a sans-serif and squeeze it into a fixed grid. Sutra began from a '
            'different question: what is the least you could draw and still have every letter read? The answer '
            'turned out to be a single line per letter, the path a pen would take if it never lifted, and a '
            'single nib to trace it.', M, y - 22, COL * 0.86)
y = para(c, 'The name comes from Sanskrit. <i>Sūtra</i> means thread, and by extension a short rule, the '
            'compressed aphorisms that hold a whole system in a line. Code is that kind of writing. A function '
            'signature, a type, a composition such as <font name="Sutra">cata = alg ∘ fmap cata</font> carries an '
            'argument in a dozen characters. The font is meant to stay out of the way of that.', M, y - 12, COL * 0.86)
y = para(c, 'This document follows the decisions in the order they were made: the pen, the curve, the grid, '
            'the letters that share their parts, the symbols that make it a font for people who compose '
            'functions, and finally what the first version taught us about the gap between geometry and the eye.',
         M, y - 12, COL * 0.86)
# a little thread motif: the skeleton of "sutra" drawn as pure centre-lines
for i, ch in enumerate('sutra'):
    skeleton(c, ch, M + i * 62, 130, 104, BLUE, nodes=False, lw=1.1)
para(c, 'The word “sutra” as its skeletons: the thread before the pen.', M, 112, 300, cap)
folio(c, 2, 'prologue')
c.showPage()

# ── 3 chapter 1: one line, one pen ─────────────────────────
page_bg(c)
y = chapter_head(c, 1, 'One line, one pen', PH - 90)
y = para(c, 'Every glyph in Sutra is stored as a <i>skeleton</i>: a few centre-line paths, sometimes a dot. '
            'Nothing about weight lives in the drawing. The outline you see is produced by sweeping one pen '
            'along each path, with round caps where a stroke ends and round joins where it turns.', M, y, COL)
y = para(c, 'Mathematically it is a Minkowski sum, the set of every point within one pen-radius of the line. '
            'In practice it means three promises are kept automatically. Every terminal ends in the same soft '
            'half-circle. No corner is ever sharp. And weight is a single number.', M, y - 10, COL)

# diagram: skeleton → outline for n, a, e, g
yb = y - 210
c.setFillColor(SHEET); c.setStrokeColor(RULE); c.setLineWidth(0.6)
c.roundRect(M, yb - 40, COL, 230, 10, fill=1, stroke=1)
labels = [('n', 'arch'), ('a', 'bowl + stem'), ('e', 'bar into arc'), ('g', 'bowl + tail')]
for i, (ch, lab) in enumerate(labels):
    x0 = M + 18 + i * (COL - 20) / 4
    draw_glyph(c, ch, x0 + 2, yb + 22, 150, HexColor('#DDE3E4'))
    skeleton(c, ch, x0 + 2, yb + 22, 150, BLUE)
    c.setFont('Sutra', 8); c.setFillColor(MUTED); c.drawString(x0 + 14, yb - 22, lab)
y = para(c, 'Skeletons in blue over the stroked result. The pen radius does the rest.', M, yb - 50, COL, cap)

# weights row
y -= 30
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, y, 'weight = pen radius')
y -= 16
for i, (w, r) in enumerate([('Light', 58), ('Regular', 82), ('Bold', 114)]):
    yy = y - 46 - i * 62
    draw_text_glyphs(c, 'cata ∘ fmap', M, yy, 52, INK, w)
    c.setFont('Sutra', 8); c.setFillColor(MUTED)
    c.drawRightString(PW - M, yy + 12, f'{w.lower()}  {r}u')
    c.setStrokeColor(RULE); c.line(M, yy - 14, PW - M, yy - 14)
folio(c, 3, 'one line, one pen')
c.showPage()

# ── 4 chapter 2: the soft square ───────────────────────────
page_bg(c)
y = chapter_head(c, 2, 'The soft square', PH - 90)
y = para(c, 'San Francisco feels calm partly because its rounds are not circles. They are flatter at the sides and '
            'fuller at the shoulders, somewhere between a circle and a box. Sutra makes that shape explicit with '
            'a superellipse, a curve the Danish poet and designer Piet Hein made famous for a Stockholm square.',
         M, y, COL)
c.setFont('Sutra', 15); c.setFillColor(INK)
c.drawCentredString(PW / 2, y - 40, '|x|ⁿ + |y|ⁿ = 1')
# Sutra lacks superscript n; draw manually instead
c.setFillColor(PAPER); c.rect(M, y - 52, COL, 30, fill=1, stroke=0)
cx = PW / 2 - 92
c.setFillColor(INK); c.setFont('Sutra', 16); c.drawString(cx, y - 40, '|x|')
c.setFont('Sutra', 10); c.drawString(cx + 29, y - 32, 'n')
c.setFont('Sutra', 16); c.drawString(cx + 42, y - 40, '+ |y|')
c.setFont('Sutra', 10); c.drawString(cx + 90, y - 32, 'n')
c.setFont('Sutra', 16); c.drawString(cx + 103, y - 40, '= 1')

# the three curves
yb = y - 270; cxs = [M + COL * 0.17, M + COL * 0.5, M + COL * 0.83]
for (n, lab, col), cx in zip([(2.0, 'n = 2  circle', MUTED), (2.7, 'n = 2.7  sutra', BLUE), (6.0, 'n = 6  box', MUTED)], cxs):
    pts = build.sq(cx, yb + 95, 70, 85, 0, 360, n=n)
    p = c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close()
    c.setStrokeColor(col); c.setLineWidth(2.2 if n == 2.7 else 1.1); c.drawPath(p, stroke=1, fill=0)
    c.setFont('Sutra', 8.6); c.setFillColor(col); c.drawCentredString(cx, yb - 14, lab)
# overlay comparison on the middle one
for n, colr in [(2.0, HexColor('#B9C3C6')), (6.0, HexColor('#B9C3C6'))]:
    pts = build.sq(cxs[1], yb + 95, 70, 85, 0, 360, n=n)
    p = c.beginPath(); p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close()
    c.setStrokeColor(colr); c.setLineWidth(0.5); c.setDash(2, 2); c.drawPath(p, stroke=1, fill=0); c.setDash()
y = yb - 40
y = para(c, 'At <font name="Sutra">n = 2</font> the curve is a circle; as <font name="Sutra">n</font> grows it '
            'approaches a box. Sutra uses <font name="Sutra">2.7</font>: straight enough that the sides of '
            '<font name="Sutra">o</font> read as walls of a column of text, round enough that nothing has a corner. '
            'JetBrains Mono reaches a similar place by eye; it argues that near-rectangular ovals make the text '
            'pattern clearer and leave open lanes for the eye moving down a file.', M, y, COL)
y = para(c, 'One curve serves ten letters and four figures: <font name="Sutra">o b d p q a g</font>, '
            '<font name="Sutra">O C G 0 6 8 9</font>. Round forms also rise about 1.7 percent above and below '
            'the flat letters, an overshoot, so that an <font name="Sutra">o</font> beside an '
            '<font name="Sutra">x</font> looks the same height rather than smaller.', M, y - 10, COL)
# overshoot demo
yo = y - 98
draw_text_glyphs(c, 'xox', M, yo, 88, INK)
k = 88 / 1000
c.setStrokeColor(BLUE); c.setLineWidth(0.5)
for yy in (0, 520):
    c.line(M - 6, yo + yy * k, M + 168, yo + yy * k)
c.setFont('Sutra', 7.6); c.setFillColor(BLUE)
c.drawString(M + 176, yo + 520 * k - 3, 'x-height 520'); c.drawString(M + 176, yo - 3, 'baseline 0')
para(c, 'The o crosses both lines by nine units. The x does not.', M + 290, yo + 34, COL - 290, cap)
folio(c, 4, 'the soft square')
c.showPage()

# ── 5 chapter 3: the grid ──────────────────────────────────
page_bg(c)
y = chapter_head(c, 3, 'Six hundred units', PH - 90)
y = para(c, 'A monospace font makes one promise above all others: every character takes the same width, so a '
            'column of code stays a column. Sutra’s cell is 600 units of a 1000-unit em. Inside that cell the '
            'stems sit at 118 and 482, which leaves the same breathing room on either side of every letter.',
         M, y, COL)
y = para(c, 'The x-height is set high, at 520 units, so lowercase letters fill more pixels at small sizes '
            'without making lines longer. Capitals stand at 700, ascenders at 740, descenders drop to −200. '
            'The math axis, where <font name="Sutra">+ - = ∘ →</font> sit, is at 330, the optical middle of the '
            'lowercase rather than its geometric centre.', M, y - 10, COL)
# metrics diagram
size = 128; k = size / 1000; word = 'Hxgo∘'
x0 = M + 62; yb = y - 150
cell = 600 * k
for i in range(len(word) + 1):
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.setDash(1.5, 2)
    c.line(x0 + i * cell, yb - 220 * k, x0 + i * cell, yb + 780 * k)
c.setDash()
for i in range(len(word)):
    c.setFillColor(HexColor('#E7ECEC')); c.rect(x0 + i * cell + 118 * k - 2, yb - 228 * k, (482 - 118) * k + 4, 4, fill=1, stroke=0)
draw_text_glyphs(c, word, x0, yb, size, INK)
for yy, lab in [(740, 'ascender 740'), (700, 'cap 700'), (520, 'x-height 520'), (330, 'math axis 330'),
                (0, 'baseline 0'), (-200, 'descender -200')]:
    c.setStrokeColor(BLUE if yy in (0, 520) else HexColor('#9FBAC4')); c.setLineWidth(0.6 if yy in (0, 520) else 0.4)
    c.line(x0 - 4, yb + yy * k, x0 + cell * len(word) + 4, yb + yy * k)
    c.setFont('Sutra', 7.4); c.setFillColor(BLUE)
    if yy in (700, 330):
        c.drawRightString(x0 - 10, yb + yy * k - 2.5, lab)
    else:
        c.drawString(x0 + cell * len(word) + 10, yb + yy * k - 2.5, lab)
c.setFont('Sutra', 7.4); c.setFillColor(MUTED); c.drawString(x0, yb - 244 * k, '← 600 →')
y = yb - 260 * k - 20
y = para(c, 'Dotted lines mark the fixed cells; the grey bars under each cell show the stem positions, 118 to 482.',
         M, y, COL, cap)
lines = ['let advance = 600   -- every glyph', 'let xh      = 520   -- lowercase', 'let capH    = 700   -- capitals',
         'let axis    = 330   -- operators', 'let pen     = 82    -- regular']
by = y - 34; fs2 = 14; cw2 = fs2 * 0.6
c.setFillColor(SHEET); c.setStrokeColor(RULE); c.roundRect(M, by - 26 - 24 * len(lines), COL, 24 * len(lines) + 40, 8, fill=1, stroke=1)
for col_ in range(0, 37):
    if col_ in (12, 18):
        c.setStrokeColor(BLUE_SOFT); c.setLineWidth(0.8)
        c.line(M + 22 + col_ * cw2, by - 6, M + 22 + col_ * cw2, by - 16 - 24 * len(lines))
for i, ln in enumerate(lines):
    c.setFont('Sutra', fs2); c.setFillColor(INK); c.drawString(M + 22, by - 24 - i * 24, ln[:20])
    c.setFillColor(MUTED); c.drawString(M + 22 + 20 * cw2, by - 24 - i * 24, ln[20:])
para(c, 'Because every character is 600 units wide, the equals signs and comments line up without any help from the editor.',
     M, by - 40 - 24 * len(lines), COL, cap)
folio(c, 5, 'six hundred units')
c.showPage()

# ── 6 chapter 4: one bowl ──────────────────────────────────
page_bg(c)
y = chapter_head(c, 4, 'One bowl, seven letters', PH - 90)
y = para(c, 'Once the curve existed, the lowercase almost drew itself. The same squircle bowl, with a straight '
            'stem placed on its left or right, rising or descending, gives seven letters. The '
            '<font name="Sutra">a</font> and <font name="Sutra">g</font> are single-storey for the same reason: '
            'a two-storey <font name="Sutra">a</font> would need a second, smaller bowl and a hook, which is two '
            'more ideas than the letter needs.', M, y, COL)
y = para(c, 'This is the font’s version of “nothing unessential”. A reader learns one shape and gets seven '
            'letters back, and the letters agree with one another because they are, literally, the same object.',
         M, y - 10, COL)
# bowl family: bowl in blue, stems in ink
G = build.glyphs(82)
size = 92; k = size / 1000
letters = 'obdpqag'
yb = y - 200
c.setFillColor(SHEET); c.setStrokeColor(RULE); c.roundRect(M, yb - 70, COL, 250, 10, fill=1, stroke=1)
from shapely.geometry import LineString
from shapely.ops import unary_union
for i, ch in enumerate(letters):
    x0 = M + 14 + i * (COL - 20) / 7
    paths = G[ch]
    for j, p in enumerate(paths):
        if isinstance(p, tuple): continue
        poly = LineString(p).buffer(41, cap_style='round', join_style='round', quad_segs=16)
        polys = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
        for pg in polys:
            path = c.beginPath()
            ex = list(pg.exterior.coords)
            path.moveTo(x0 + ex[0][0] * k, yb + ex[0][1] * k)
            for px, py in ex[1:]: path.lineTo(x0 + px * k, yb + py * k)
            path.close()
            for ring in pg.interiors:
                r = list(ring.coords); path.moveTo(x0 + r[0][0] * k, yb + r[0][1] * k)
                for px, py in r[1:]: path.lineTo(x0 + px * k, yb + py * k)
                path.close()
            c.setFillColor(Color(0.118, 0.361, 0.451, alpha=0.88) if j == 0 else Color(0.086, 0.129, 0.165, alpha=0.82))
            c.drawPath(path, fill=1, stroke=0, fillMode=0)
    c.setFont('Sutra', 8); c.setFillColor(MUTED); c.drawCentredString(x0 + 300 * k, yb - 52, ch)
y = para(c, 'Blue: the shared bowl. Ink: the stem or tail that turns it into a letter.', M, yb - 82, COL, cap)
y -= 18
y = para(c, 'The same economy runs through the rest of the alphabet. <font name="Sutra">n</font>, '
            '<font name="Sutra">h</font> and <font name="Sutra">m</font> share one arch; <font name="Sutra">u</font> '
            'is that arch turned over. <font name="Sutra">i</font> and <font name="Sutra">l</font> end in a small '
            'tail that curls into the next character, which is where the “flow between letters” in the brief '
            'lives: it fills the empty space a narrow letter leaves in a wide cell and leads the eye forward.',
         M, y, COL)
draw_text_glyphs(c, 'nhmu  il', M, y - 92, 64, INK)
folio(c, 6, 'one bowl, seven letters')
c.showPage()

# ── 7 chapter 5: told apart ────────────────────────────────
page_bg(c)
y = chapter_head(c, 5, 'Told apart at a glance', PH - 90)
y = para(c, 'In prose, context forgives a lot: nobody misreads “l00k” because they know the word. In code there '
            'is no such mercy. <font name="Sutra">O</font> and <font name="Sutra">0</font>, '
            '<font name="Sutra">l</font> and <font name="Sutra">1</font>, a comma and a period, each confusion is '
            'a bug. Sutra resolves each one with the smallest difference that works.', M, y, COL)
pairs = [('0O', 'Zero is narrower than O and carries a single dot. No slash, so it never looks like Ø.'),
         ('Il1|', 'Capital I has bars. Lowercase l ends in a tail. One has a flag and a foot. The pipe runs the full height.'),
         ('rn m', 'The r shoulder rolls over and turns down early, so rn never fuses into m.'),
         ('.,:;', 'Dots are a touch heavier than the stroke, so punctuation survives at eleven pixels.')]
yy = y - 30
for g, txt in pairs:
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, yy, PW - M, yy)
    draw_text_glyphs(c, g, M, yy - 92, 92, INK)
    para(c, txt, M + 290, yy - 34, COL - 290, body)
    yy -= 128
folio(c, 7, 'told apart')
c.showPage()

# ── 8 chapter 6: composition set ───────────────────────────
page_bg(c)
y = chapter_head(c, 6, 'The composition set', PH - 90)
y = para(c, 'Most coding fonts treat mathematical symbols as an afterthought, borrowed from a fallback font in '
            'a different weight and sitting at a different height. Sutra draws them with the same pen, on the '
            'same axis, as first-class citizens. If you write <font name="Sutra">g ∘ f</font>, the ring sits '
            'exactly where the eye expects an operator, and it has the same stroke as the letters on either side.',
         M, y, COL)
syms = [('∘', 'compose'), ('→', 'arrow'), ('⇒', 'implies'), ('↦', 'maps to'), ('λ', 'lambda'), ('∀', 'for all'),
        ('∃', 'exists'), ('≡', 'identical'), ('≅', 'isomorphic'), ('≠', 'not equal'), ('≤', 'at most'), ('≥', 'at least'),
        ('⊗', 'tensor'), ('⊕', 'direct sum'), ('×', 'product'), ('∈', 'element of'), ('⊥', 'bottom'), ('⊤', 'top'),
        ('∅', 'empty'), ('¬', 'not'), ('←', 'from'), ('⇐', 'implied by'), ('·', 'dot'), ('…', 'ellipsis')]
cols, cw, ch_ = 6, COL / 6, 78
gy = y - 24
for i, (s, n) in enumerate(syms):
    r, q = divmod(i, cols)
    x0, y0 = M + q * cw, gy - (r + 1) * ch_
    c.setFillColor(SHEET); c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.rect(x0, y0, cw, ch_, fill=1, stroke=1)
    draw_glyph(c, s, x0 + cw / 2 - 21, y0 + 28, 70, BLUE if s == '∘' else INK)
    c.setFont('Sutra', 6.8); c.setFillColor(MUTED); c.drawCentredString(x0 + cw / 2, y0 + 8, n)
y = gy - 4 * ch_ - 28
c.setFillColor(SHEET); c.setStrokeColor(RULE); c.roundRect(M, y - 88, COL, 84, 8, fill=1, stroke=1)
c.setFont('Sutra', 15); c.setFillColor(INK)
c.drawString(M + 22, y - 36, 'cata alg = alg ∘ fmap (cata alg) ∘ unfix')
c.setFont('Sutra', 15); c.drawString(M + 22, y - 64, '∀ f g h. (f ∘ g) ∘ h ≡ f ∘ (g ∘ h)')
para(c, 'A catamorphism and the associativity law, set in Sutra Mono Regular.', M, y - 100, COL, cap)
folio(c, 8, 'the composition set')
c.showPage()

# ── 9 chapter 7: in the editor ─────────────────────────────
page_bg(c, NIGHT)
c.setFont('Sutra', 9); c.setFillColor(NIGHT_BLUE); c.drawString(M, PH - 90, '## chapter 7')
c.setFont('Disp', 34); c.setFillColor(NIGHT_FG); c.drawString(M, PH - 132, 'Where it lives')
nightbody = ParagraphStyle('nb', parent=body, textColor=NIGHT_FG)
y = para(c, 'A coding font is read for hours at a time, mostly at thirteen or fourteen points, mostly on a dark '
            'background. This is the page that matters. Read it at arm’s length and notice what you do not '
            'notice: no terminal catches the eye, no letter is louder than its neighbours.', M, PH - 160, COL, nightbody)
code = [
    ('c', '-- ad format spec ⇒ deterministic Moore machine'),
    ('k', 'compile ', 'o', '= ', 'f', 'emit ∘ minimise ∘ determinise ∘ parse'),
    ('', ''),
    ('k', 'fold ', 'o', ':: ', 't', '(F a → a) → Fix F → a'),
    ('k', 'fold alg ', 'o', '= ', 'f', 'alg ∘ fmap (fold alg) ∘ unfix'),
    ('', ''),
    ('k', 'const ', 'f', 'step ', 'o', '= ', 'f', '(s: State, e: Event): State =>'),
    ('f', '  s.on[e.kind]?.(e) ?? s;   ', 'c', '// total, never throws'),
    ('', ''),
    ('k', 'if ', 'f', '(bid >= floor && fill != 0) {'),
    ('f', '  render(', 's', '"LAGOM_BANNER"', 'f', ');'),
    ('f', '}'),
    ('', ''),
    ('c', '// 0O o Il1| {}[]() #$%&@ → ← ↦ ⊗ ⊕ ⊥ ⊤ ∈ ≅ ¬'),
]
colors = {'c': NIGHT_MUTED, 'k': NIGHT_BLUE, 'o': NIGHT_MUTED, 'f': NIGHT_FG, 't': NIGHT_WARM, 's': NIGHT_WARM, '': NIGHT_FG}
panel_top = y - 26; lh = 21.5; fs = 12.6
c.setFillColor(HexColor('#0B1115')); c.setStrokeColor(HexColor('#22313A'))
c.roundRect(M, panel_top - 34 - lh * len(code), COL, 34 + lh * len(code) + 14, 10, fill=1, stroke=1)
c.setFont('Sutra', 7.6); c.setFillColor(NIGHT_MUTED); c.drawString(M + 18, panel_top - 14, 'naruto/v7/compile.ts')
for i, row in enumerate(code):
    ly = panel_top - 40 - i * lh
    c.setFont('Sutra', 7.4); c.setFillColor(HexColor('#3A4B54')); c.drawRightString(M + 34, ly, str(i + 1))
    x = M + 46
    for j in range(0, len(row), 2):
        t, s = row[j], row[j + 1]
        c.setFont('Sutra', fs); c.setFillColor(colors[t]); c.drawString(x, ly, s)
        x += len(s) * fs * 0.6
para(c, 'Sutra Mono Regular at 12.6 pt on a night background, with a quiet syntax palette.',
     M, panel_top - 40 - lh * len(code) - 16, COL, ParagraphStyle('nc', parent=cap, textColor=NIGHT_MUTED))
folio(c, 9, 'where it lives', dark=True)
c.showPage()

# ── 10 chapter 8: what the eye wants ───────────────────────
page_bg(c)
y = chapter_head(c, 8, 'What the eye wants', PH - 90)
y = para(c, 'Version one was honest geometry, and the first round of use showed exactly where geometry and '
            'perception part ways. Type designers have known these things for a long time; Sutra learned them '
            'by drawing, and version 1.100 applies each one.', M, y, COL)
lessons = [
    ('Horizontals look heavier than verticals.',
     'A round pen gives every direction the same width, so bars and the tops of bowls read slightly heavy. '
     'Sutra keeps the single-pen idea but changes the nib: an ellipse 8 percent wider than it is tall, which '
     'thins horizontals and sets diagonals between the two automatically.'),
    ('Curves need matching curvature, not only direction.',
     'Outlines are now fitted to clean Bézier curves with a node at every extreme, and the spine of the s '
     'is solved so that it meets both bowls tangentially, without a kink.'),
    ('An s is not two stacked c’s.',
     'The first one felt as if it leaned left. The redrawn s has a slightly larger lower half and a straight '
     'diagonal spine, so the two halves look equal and the letter stands upright.'),
    ('Narrow letters need a job in a wide cell.',
     'The first r looked like an n that had lost a leg. It now has a rounder shoulder that finishes with a '
     'small downturned terminal, filling its cell without borrowing anyone else’s.'),
]
yy = y - 18
for i, (h, t) in enumerate(lessons):
    c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, yy - 12, f'{i + 1:02d}')
    yh = para(c, f'<font name="SerifM">{h}</font>', M + 34, yy, COL - 34, body)
    yy = para(c, t, M + 34, yh - 3, COL - 34, body) - 16
c.setStrokeColor(RULE); c.line(M, yy, PW - M, yy)
yy -= 22
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, yy, '## next')
road = ['Texture healing: contextual alternates that let i and l lend space to m and w, without breaking the grid.',
        'Optional functional ligatures for -> => != >=, nothing decorative.',
        'A variable weight axis, with 400 recommended on dark backgrounds and 450 on light.',
        'Submitted to Google Fonts under the SIL Open Font License (google/fonts #11111).']
yy -= 8
for r in road:
    yy = para(c, f'<font name="Sutra" color="#1E5C73">∘</font>&nbsp;&nbsp;{r}', M, yy - 4, COL, body)
folio(c, 10, 'what the eye wants')
c.showPage()

# ── 11 colophon ────────────────────────────────────────────
page_bg(c)
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, PH - 90, '## colophon')
c.setFont('Disp', 34); c.setFillColor(INK); c.drawString(M, PH - 132, 'Specification')
rows = [('family', 'Sutra Mono'), ('weights', 'Light (pen 58)  ·  Regular (82)  ·  Bold (114)'),
        ('glyphs', '358  ·  GF Latin Core plus the composition set'), ('em / advance', '1000 / 600'),
        ('vertical metrics', 'x 520  ·  cap 700  ·  asc 740  ·  desc −200  ·  axis 330'),
        ('curve', 'superellipse, n = 2.7, overshoot 9 units'), ('format', 'TrueType, fixed pitch'),
        ('source', 'github.com/narennaik/sutra-mono')]
yy = PH - 170
for k_, v in rows:
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, yy + 14, PW - M, yy + 14)
    c.setFont('Sutra', 8.6); c.setFillColor(MUTED); c.drawString(M, yy, k_)
    c.setFont('Serif', 11.2); c.setFillColor(INK); c.drawString(M + 140, yy, v)
    yy -= 30
c.line(M, yy + 14, PW - M, yy + 14)
yy -= 14
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, yy, '## install')
yy = para(c, 'Install the three .ttf files, then set <font name="Sutra">"editor.fontFamily": "Sutra Mono"</font> '
             'in VS Code, or <font name="Sutra">font-family = Sutra Mono</font> in Ghostty. Recommended size '
             '13 to 15 pt with a line height of about 1.5.', M, yy - 10, COL)
yy -= 34
c.setFont('Sutra', 9); c.setFillColor(BLUE); c.drawString(M, yy, '## character set')
sets = ['abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789 .,:;!?\'"`',
        '()[]{}<>/\\|_^~*+-=#$%&@', '∘→←⇒⇐↦λ∀∃≡≠≅≤≥⊗⊕×∈⊥⊤∅¬·…']
yy -= 40
for s in sets:
    draw_text_glyphs(c, s, M, yy, 30.5, INK)
    yy -= 40
c.setStrokeColor(RULE); c.line(M, 110, PW - M, 110)
para(c, 'Set in Sutra Mono and Newsreader. Glyphs in this document are drawn directly from the shipped font '
        'outlines; construction diagrams are drawn from the same skeletons that generated them.', M, 98, COL, small)
folio(c, 11, 'colophon')
c.showPage()
c.save()
print('ok')
