"""Glyph skeletons for Sutra Mono.

Every glyph is a list of centre-line paths (see geometry.py). Metrics are in font units on a
1000-unit em; every glyph advances 600. `skeletons(S, e)` returns a dict of glyph name → item list
for pen width S and pen aspect e (height/width), so the same drawing serves every weight.
"""
import math
from geometry import sq, sq_point, spline, bez, translate, mirror, rot180, scale

UPM, W = 1000, 600
X, H, A, D = 520, 700, 740, -200        # x-height, cap height, ascender, descender (outer edges)
L, R, C = 118, 482, 300                 # stem centre-lines
OV = 9                                  # overshoot for round forms
AX = 330                                # math axis
GY = 270                                # guillemet / bullet axis (middle of the lowercase)


def _ang(v):
    return math.degrees(math.atan2(v[1], v[0]))


def _angdiff(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)


def s_shape(top, bot, rxu, rxl, bias=10, t_top=34, t_bot=-150, cxu=C - 2, cxl=C + 2, n=2.7):
    """An s / S skeleton: upper bowl → straight diagonal spine → lower bowl.
    The spine meets both bowls tangentially (solved numerically), so there is no kink.
    `bias` > 0 lifts the waist, making the lower bowl taller (it should look equal, so it must be bigger)."""
    top, bot = top + OV, bot - OV
    my = (top + bot) / 2 + bias
    ryu, ryl = (top - my) / 2, (my - bot) / 2
    yu, yl = my + ryu, bot + ryl
    P = lambda t: sq_point(cxu, yu, rxu, ryu, t, n)
    Q = lambda t: sq_point(cxl, yl, rxl, ryl, t, n)
    best = None
    for i in range(0, 161):
        tu = 180 + i * 0.5
        p0, p1 = P(tu - 0.2), P(tu + 0.2)
        tan_u = _ang((p1[0] - p0[0], p1[1] - p0[1]))          # CCW travel
        pu = P(tu)
        for j in range(0, 161):
            tl = j * 0.5
            q0, q1 = Q(tl + 0.2), Q(tl - 0.2)
            tan_l = _ang((q1[0] - q0[0], q1[1] - q0[1]))      # CW travel
            ql = Q(tl)
            ch = _ang((ql[0] - pu[0], ql[1] - pu[1]))
            err = _angdiff(ch, tan_u) + _angdiff(ch, tan_l)
            if best is None or err < best[0]:
                best = (err, tu, tl)
    _, tu, tl = best
    return sq(cxu, yu, rxu, ryu, t_top, tu, n) + sq(cxl, yl, rxl, ryl, tl, t_bot, n)


def _u(v):
    l = math.hypot(*v); return (v[0]/l, v[1]/l)

def s_curve(top, bot, rx, OV=OV, cx=C, n=2.4, waist=0.52, spine=0.40, upper_w=0.94, lean=0.03,
            a_top=34, a_bot=-146, hk=0.62, sk=0.55, steps=48):
    """s/S skeleton: upper bowl and lower bowl are exact superellipse arcs (so the hooks continue
    the bowls' own curves), joined by a two-piece Bézier spine whose ends leave the bowls along
    their vertical tangents and cross the centre on a gentle diagonal."""
    top, bot = top + OV, bot - OV
    Hh = top - bot
    X = lambda u: cx + u * rx
    Y = lambda v: bot + v * Hh
    vl = (1 + waist) / 2 + 0.02
    vr = waist / 2 - 0.01
    ucx, ucy, urx, ury = X(lean), Y(vl), upper_w * rx, Y(1.0) - Y(vl)
    lcx, lcy, lrx, lry = X(0), Y(vr), rx, Y(vr) - Y(0.0)
    upper = sq(ucx, ucy, urx, ury, a_top, 180, n, step=1.0)          # terminal → top → left extreme
    lower = sq(lcx, lcy, lrx, lry, 0, a_bot, n, step=1.0)            # right extreme → bottom → terminal
    L0, Mid, R0 = upper[-1], (X(0), Y(waist)), lower[0]
    d = _u((1, -spine))
    # left extreme → centre
    l1 = abs(Mid[1] - L0[1]) * hk
    lm = math.hypot(Mid[0] - L0[0], Mid[1] - L0[1]) * sk
    seg1 = bez(L0, (L0[0], L0[1] - l1), (Mid[0] - d[0] * lm, Mid[1] - d[1] * lm), Mid, steps)
    # centre → right extreme
    r1 = abs(R0[1] - Mid[1]) * hk
    rm = math.hypot(R0[0] - Mid[0], R0[1] - Mid[1]) * sk
    seg2 = bez(Mid, (Mid[0] + d[0] * rm, Mid[1] + d[1] * rm), (R0[0], R0[1] + r1), R0, steps)
    return upper + seg1[1:] + seg2[1:] + lower[1:]


def skeletons(S, e=0.92):
    h = S / 2                 # half width of a vertical stroke
    hv = e * S / 2            # half height of a horizontal stroke
    b, x, c, a, d = hv, X - hv, H - hv, A - hv, D + hv
    DR = h + 9                # dots are a touch heavier than the stroke
    rx = (R - L) / 2
    ry = X / 2 - hv + OV
    RY = H / 2 - hv + OV
    mx, mh = X / 2, H / 2
    BOWL = sq(C, mx, rx, ry, 0, 360)
    G = {}

    def dot(px, py, r=DR):
        return ('dot', px, py, r)

    def pen(k, items):
        out = []
        for it in items:
            if isinstance(it, tuple) and it[0] == 'dot':
                out.append(('dot', it[1], it[2], it[3] * (0.75 + 0.25 * k)))
            elif isinstance(it, tuple) and it[0] == 'pen':
                out.append(('pen', it[1] * k, it[2]))
            else:
                out.append(('pen', k, it))
        return out

    def arch(top, ry_=230):
        cy = top - ry_
        return sq(C, cy, rx, ry_, 180, 0) + [(R, b)]

    def dshape(top, bot, xs, xr, x0=L):
        return [(x0, top), (xs, top)] + sq(xs, (top + bot) / 2, xr - xs, (top - bot) / 2, 90, -90) + [(x0, bot)]

    # ── lowercase ───────────────────────────────────────────
    G['a'] = [BOWL, [(R, b), (R, x)]]
    G['b'] = [BOWL, [(L, b), (L, a)]]
    G['c'] = [sq(C, mx, rx, ry, 42, 318)]
    G['d'] = [BOWL, [(R, b), (R, a)]]
    G['e'] = [[(L + 2, mx), (R, mx)] + sq(C, mx, rx, ry, 0, 322)]
    G['f'] = [[(C - 50, b), (C - 50, a - 160)] + sq(C + 100, a - 160, 150, 160 + OV, 180, 40), [(L, x), (R - 30, x)]]
    G['g'] = [BOWL, [(R, x), (R, d + 160)] + sq(C, d + 160, rx, 160 + OV, 0, -152)]
    G['h'] = [[(L, b), (L, a)], arch(x)]
    G['i'] = [[(L + 30, x), (C, x), (C, b + 120)] + sq(C + 120, b + 120, 120, 120 + OV, 180, 270) + [(R + 10, b - OV)],
              dot(C, X + 150)]
    G['dotlessi'] = G['i'][:1]
    G['j'] = [[(L + 50, x), (C + 60, x), (C + 60, d + 150)] + sq(C - 90, d + 150, 150, 150 + OV, 0, -90) + [(L - 10, d - OV)],
              dot(C + 60, X + 150)]
    G['dotlessj'] = G['j'][:1]
    k1 = ((R - 5, x), (L, b + 175))
    t = 0.42
    G['k'] = [[(L, b), (L, a)], list(k1),
              [(k1[0][0] + t * (k1[1][0] - k1[0][0]), k1[0][1] + t * (k1[1][1] - k1[0][1])), (R + 5, b)]]
    G['l'] = [[(L + 20, a), (C, a), (C, b + 120)] + sq(C + 120, b + 120, 120, 120 + OV, 180, 270) + [(R + 10, b - OV)]]
    cy_m = x - 210
    G['m'] = [[(L, b), (L, x)],
              sq((L + C) / 2, cy_m, (C - L) / 2, 210 + OV, 180, 0) + [(C, b)],
              sq((C + R) / 2, cy_m, (R - C) / 2, 210 + OV, 180, 0) + [(R, b)]]
    G['n'] = [[(L, b), (L, x)], arch(x)]
    G['o'] = [BOWL]
    G['p'] = [BOWL, [(L, d), (L, x)]]
    G['q'] = [BOWL, [(R, d), (R, x)]]
    # r: a rolled shoulder that finishes in a small downturned terminal, so it fills its cell
    # r: stem on the same line as n/m/p so the gap before it matches every other letter;
    # the arm stops short of the right edge so the space after it evens out too
    G['r'] = [[(L, b), (L, x)],
              sq(L + 170, x - 200, 170, 200 + OV, 180, 90, n=2.2) +
              bez((L + 170, x + OV), (L + 240, x + OV), (R - 32, x + OV - 12), (R - 20, x - 40), 16)[1:]]
    G['s'] = [s_curve(x, b, 168)]
    G['t'] = [[(C - 40, a - 40), (C - 40, b + 120)] + sq(C + 80, b + 120, 120, 120 + OV, 180, 270) + [(R, b - OV)],
              [(L, x), (R - 20, x)]]
    G['u'] = [[(L, x), (L, b + 230)] + sq(C, b + 230, rx, 230 + OV, 180, 360), [(R, x), (R, b)]]
    G['v'] = [[(L - 4, x), (C, b), (R + 4, x)]]
    G['w'] = [[(L - 20, x), (L + 50, b), (C, x - 150), (R - 50, b), (R + 20, x)]]
    G['x'] = [[(L, x), (R, b)], [(R, x), (L, b)]]
    G['y'] = [[(L - 4, x), (C, b + 30)], [(R + 4, x), (C - 100, d + 10)]]
    G['z'] = [[(L, x), (R, x), (L, b), (R, b)]]

    # ── uppercase ───────────────────────────────────────────
    G['A'] = [[(L - 10, b), (C, c), (R + 10, b)], [(L + 52, 230), (R - 52, 230)]]
    G['B'] = [[(L, b), (L, c)], dshape(c, 382, 290, R - 22), dshape(382, b, 300, R)]
    G['C'] = [sq(C, mh, rx, RY, 40, 320)]
    G['D'] = [[(L, b), (L, c)], dshape(c, b, 220, R)]
    G['E'] = [[(R, c), (L, c), (L, b), (R, b)], [(L, mh), (R - 40, mh)]]
    G['F'] = [[(R, c), (L, c), (L, b)], [(L, mh), (R - 40, mh)]]
    G['G'] = [sq(C, mh, rx, RY, 40, 360) + [(C + 30, mh)]]
    G['H'] = [[(L, b), (L, c)], [(R, b), (R, c)], [(L, mh), (R, mh)]]
    G['I'] = [[(L + 40, c), (R - 40, c)], [(C, c), (C, b)], [(L + 40, b), (R - 40, b)]]
    G['J'] = [[(L + 50, c), (R, c), (R, b + 220)] + sq(C, b + 220, rx, 220 + OV, 0, -165)]
    k1 = ((R, c), (L, b + 220))
    t = 0.45
    G['K'] = [[(L, b), (L, c)], list(k1),
              [(k1[0][0] + t * (k1[1][0] - k1[0][0]), k1[0][1] + t * (k1[1][1] - k1[0][1])), (R + 5, b)]]
    G['L'] = [[(L, c), (L, b), (R, b)]]
    G['M'] = [[(L, b), (L, c), (C, 250), (R, c), (R, b)]]
    G['N'] = [[(L, b), (L, c), (R, b), (R, c)]]
    G['O'] = [sq(C, mh, rx, RY, 0, 360)]
    G['P'] = [[(L, b), (L, c)], dshape(c, 300, 290, R)]
    G['Q'] = [sq(C, mh, rx, RY, 0, 360), [(C + 60, 175), (R + 20, b - 50)]]
    G['R'] = [[(L, b), (L, c)], dshape(c, 300, 290, R), [(C + 10, 300), (R + 5, b)]]
    G['S'] = [s_curve(c, b, 180)]
    G['T'] = [[(L - 15, c), (R + 15, c)], [(C, c), (C, b)]]
    G['U'] = [[(L, c), (L, b + 230)] + sq(C, b + 230, rx, 230 + OV, 180, 360) + [(R, c)]]
    G['V'] = [[(L - 10, c), (C, b), (R + 10, c)]]
    G['W'] = [[(L - 25, c), (L + 45, b), (C, c - 240), (R - 45, b), (R + 25, c)]]
    G['X'] = [[(L, c), (R, b)], [(R, c), (L, b)]]
    G['Y'] = [[(L - 10, c), (C, 320), (R + 10, c)], [(C, 320), (C, b)]]
    G['Z'] = [[(L, c), (R, c), (L, b), (R, b)]]

    # ── extended letters ────────────────────────────────────
    G['AE'] = [[(L - 20, b), (C, c), (R + 5, c)], [(C, c), (C, b), (R + 5, b)], [(C, mh + 10), (R - 30, mh + 10)],
               [(L + 38, 230), (C, 230)]]
    G['ae'] = [sq(L + 91, mx, 91, ry, 0, 360), [(C, b), (C, x)],
               [(C, mx), (R, mx)] + sq(C + 91, mx, 91, ry, 0, 322)]
    G['OE'] = [sq(C, mh, C - L, c - mh, 90, 270), [(C, c), (R + 5, c)], [(C, b), (R + 5, b)], [(C, c), (C, b)],
               [(C, mh), (R - 30, mh)]]
    G['oe'] = [sq(L + 91, mx, 91, ry, 0, 360), [(C, mx), (R, mx)] + sq(C + 91, mx, 91, ry, 0, 322)]
    G['Oslash'] = G['O'] + [[(R + 18, c + 30), (L - 18, b - 30)]]
    G['oslash'] = G['o'] + [[(R + 14, x + 34), (L - 14, b - 34)]]
    G['Eth'] = G['D'] + [[(L - 62, mh), (L + 112, mh)]]
    G['Dcroat'] = G['Eth']
    G['dcroat'] = G['d'] + [[(C + 70, a - 98), (R + 62, a - 98)]]
    G['eth'] = [BOWL, [(R, mx), (R, mx + 60)] + bez((R, mx + 60), (R, X + 110), (C + 60, A - 40), (L + 70, a), 30)[1:],
                [(C - 35, 598), (R - 5, 690)]]
    G['Hbar'] = G['H'] + [[(L - 48, 560), (R + 48, 560)]]
    G['hbar'] = G['h'] + [[(L - 62, a - 98), (C + 30, a - 98)]]
    G['Lslash'] = G['L'] + [[(L - 58, 245), (L + 118, 425)]]
    G['lslash'] = G['l'] + [[(C - 95, 300), (C + 95, 460)]]
    G['Thorn'] = [[(L, b), (L, c)], dshape(c - 140, 160, 290, R)]
    G['thorn'] = [BOWL, [(L, d), (L, a)]]
    def clear_end(cx, cy, rx_, ry_, t_from=-150, t_to=-95, gap=16, n=2.5):
        """First angle (moving right along the bottom) whose terminal clears the stem by `gap`."""
        t_ = t_from
        while t_ < t_to:
            px, _ = sq_point(cx, cy, rx_, ry_, t_, n)
            if px - h - (L + h) >= gap:
                return t_
            t_ += 1
        return t_to

    # ß: stem, a small top bowl that folds back to a waist, then a larger lower bowl that opens left
    tb = sq(L + 150, a - 150, 150, 150 + OV, 180, -40, n=2.5)
    wx, wy = max(L + 95, L + 2 * h + 18), 410
    lcx, lcy, lrx, lry = L + 185, (wy + b - OV) / 2, R - (L + 185), (wy - (b - OV)) / 2
    lo = sq(lcx, lcy, lrx, lry, 110, clear_end(lcx, lcy, lrx, lry), n=2.5)
    G['germandbls'] = [[(L, b), (L, a - 150)] + tb +
                       bez(tb[-1], (tb[-1][0] - 40, tb[-1][1] - 45), (wx + 40, wy + 5), (wx, wy), 14)[1:],
                       [(wx, wy)] + lo[3:]]
    tb = sq(L + 175, c - 150, 175, 150 + OV, 180, 0)
    ucx, ucy, urx, ury = C + 5, b + 180, 177, 180 + OV
    G['uni1E9E'] = [[(L, b), (L, c - 150)] + tb + [(C - 10, 395)] +
                    sq(ucx, ucy, urx, ury, 95, clear_end(ucx, ucy, urx, ury, n=2.7), n=2.7)]

    # ── figures ─────────────────────────────────────────────
    G['zero'] = [sq(C, mh, rx - 8, RY, 0, 360), dot(C, mh, DR - 8)]
    G['one'] = [[(L + 25, c - 120), (C + 10, c), (C + 10, b)], [(L + 40, b), (R - 20, b)]]
    G['two'] = [sq(C, c - 165, 172, 165 + OV, 160, -25) + [(L, b), (R + 5, b)]]
    G['three'] = [sq(C, c - 150, 165, 150 + OV, 150, -90) + [(C - 60, c - 300)],
                  [(C - 60, c - 300)] + sq(C + 5, b + 165, 177, 165 + OV, 90, -150)]
    G['four'] = [[(R - 50, b), (R - 50, c), (L - 5, 220), (R + 15, 220)]]
    G['five'] = [[(R - 10, c), (L + 25, c), (L + 12, 410), (C - 10, 445)] + sq(C, 235, rx, 205 + OV, 100, -152)[1:]]
    G['five'] = [[(R - 10, c), (L + 25, c), (L + 12, 410)] + sq(C, 235, rx, 205 + OV, 125, -152)]
    G['six'] = [sq(C, 225, rx, 225 - hv + OV, 0, 360),
                [(L, 225), (L, 330)] + sq(C + 30, 330, rx + 30, c - 330 + OV, 180, 62)]
    G['nine'] = rot180(G['six'], C, mh)
    G['seven'] = [[(L, c), (R, c), (C - 30, b)]]
    G['eight'] = [sq(C, 525, 160, c - 525 + OV, 0, 360), sq(C, b + 172 - OV, rx, 172, 0, 360)]

    # ── punctuation ─────────────────────────────────────────
    comma = [dot(C, DR), [(C + 22, DR - 4), (C - 50, -130)]]
    G['period'] = [dot(C, DR)]
    G['comma'] = comma
    G['colon'] = [dot(C, DR), dot(C, X - DR)]
    G['semicolon'] = comma + [dot(C, X - DR)]
    G['exclam'] = [[(C, c), (C, 230)], dot(C, DR)]
    G['question'] = [sq(C, c - 150, 165, 150 + OV, 160, -90) + [(C, c - 300), (C, 230)], dot(C, DR)]
    G['exclamdown'] = rot180(G['exclam'], C, X / 2)
    G['questiondown'] = rot180(G['question'], C, X / 2)
    G['quotedbl'] = [[(C - 85, c + 20), (C - 85, c - 170)], [(C + 85, c + 20), (C + 85, c - 170)]]
    G['quotesingle'] = [[(C, c + 20), (C, c - 170)]]
    G['grave'] = [[(C - 70, c + 30), (C + 40, c - 90)]]
    qr = translate(comma, 0, 590)
    G['quoteright'] = qr
    G['quoteleft'] = rot180(qr, C, 590 + (DR - 130) / 2 + 0)
    G['quotesinglbase'] = comma
    G['quotedblright'] = translate(qr, -92, 0) + translate(qr, 92, 0)
    G['quotedblleft'] = translate(G['quoteleft'], -92, 0) + translate(G['quoteleft'], 92, 0)
    G['quotedblbase'] = translate(comma, -92, 0) + translate(comma, 92, 0)
    G['numbersign'] = [[(C - 95, 50), (C - 75, 650)], [(C + 75, 50), (C + 95, 650)],
                       [(L - 15, 235), (R + 15, 235)], [(L - 15, 465), (R + 15, 465)]]
    G['dollar'] = [s_curve(c - 40, b + 40, 168), [(C, c + 12), (C, c + 72)], [(C, b - 12), (C, b - 72)]]
    G['percent'] = [sq(C - 120, 540, 75, 100, 0, 360), sq(C + 120, 160, 75, 100, 0, 360), [(R + 10, c), (L - 10, b)]]
    G['ampersand'] = [spline([(R + 15, b), (C - 70, 410), (C - 115, 545), (C - 30, c), (C + 70, 590), (C + 30, 480),
                              (L + 5, 300), (L + 10, 120), (C - 10, b), (C + 120, 110), (R + 15, 330)])]
    G['parenleft'] = [sq(C + 175, 350, 235, 440, 113, 247)]
    G['parenright'] = mirror(G['parenleft'])
    G['bracketleft'] = [[(C + 110, 780), (C - 60, 780), (C - 60, -80), (C + 110, -80)]]
    G['bracketright'] = mirror(G['bracketleft'])
    G['braceleft'] = [spline([(C + 120, 780), (C + 10, 720), (C + 5, 460), (C - 110, 350)]),
                      spline([(C - 110, 350), (C + 5, 240), (C + 10, -20), (C + 120, -80)])]
    G['braceright'] = mirror(G['braceleft'])
    G['asterisk'] = [[(C + 170 * math.cos(math.radians(t_)), 450 + 170 * math.sin(math.radians(t_))),
                      (C - 170 * math.cos(math.radians(t_)), 450 - 170 * math.sin(math.radians(t_)))] for t_ in (90, 30, 150)]
    G['plus'] = [[(L + 10, AX), (R - 10, AX)], [(C, AX - 182), (C, AX + 182)]]
    G['hyphen'] = [[(L + 40, AX), (R - 40, AX)]]
    G['endash'] = [[(L - 40, AX), (R + 40, AX)]]
    G['emdash'] = [[(h + 4, AX), (W - h - 4, AX)]]
    G['minus'] = [[(L + 10, AX), (R - 10, AX)]]
    G['equal'] = [[(L + 10, AX - 90), (R - 10, AX - 90)], [(L + 10, AX + 90), (R - 10, AX + 90)]]
    G['less'] = [[(R - 15, AX + 220), (L + 15, AX), (R - 15, AX - 220)]]
    G['greater'] = mirror(G['less'])
    G['slash'] = [[(R + 10, 760), (L - 10, -80)]]
    G['backslash'] = mirror(G['slash'])
    G['bar'] = [[(C, 780), (C, -180)]]
    G['underscore'] = [[(L - 20, -110), (R + 20, -110)]]
    G['asciicircum'] = [[(L + 25, 420), (C, c), (R - 25, 420)]]
    G['asciitilde'] = [spline([(L - 5, AX - 40), (L + 85, AX + 45), (C, AX), (R - 85, AX - 45), (R + 5, AX + 40)])]
    G['at'] = [sq(C + 10, 305, 70, 92, 0, 360),
               [(C + 80, 397), (C + 80, 265)] + spline([(C + 80, 265), (C + 112, 205), (C + 170, 208), (C + 208, 250)])[1:]
               + sq(C, 315, rx + 30, 262, -15, 290)]
    G['divide'] = G['minus'] + [dot(C, AX + 165), dot(C, AX - 165)]
    G['guilsinglleft'] = [[(C + 62, GY + 122), (C - 62, GY), (C + 62, GY - 122)]]
    G['guilsinglright'] = mirror(G['guilsinglleft'])
    G['guillemotleft'] = [[(C - 18, GY + 122), (C - 133, GY), (C - 18, GY - 122)],
                          [(C + 132, GY + 122), (C + 17, GY), (C + 132, GY - 122)]]
    G['guillemotright'] = mirror(G['guillemotleft'])

    # ── currency and signs ──────────────────────────────────
    G['cent'] = [sq(C, mx, rx - 12, ry - 6, 42, 318), [(C + 5, x + 80), (C + 5, b - 80)]]
    G['sterling'] = [[(R + 8, c - 70)] + sq(C + 42, c - 150, 140, 150 + OV, 25, 180)[1:] + [(C + 42 - 140, 170)] +
                     bez((C + 42 - 140, 170), (C + 42 - 140, 70), (C - 140, b), (L - 10, b), 16)[1:] + [(R + 10, b)],
                     [(L + 5, 340), (C + 110, 340)]]
    G['yen'] = [[(L - 10, c), (C, 330), (R + 10, c)], [(C, 330), (C, b)], [(L + 35, 255), (R - 35, 255)],
                [(L + 35, 125), (R - 35, 125)]]
    G['Euro'] = [sq(C + 40, mh, rx - 8, RY, 45, 315), [(L - 35, mh + 62), (C + 70, mh + 62)],
                 [(L - 35, mh - 62), (C + 50, mh - 62)]]
    G['section'] = [s_curve(c + 10, 300, 146), s_curve(420, -60, 146)]
    ring_r = 248
    G['copyright'] = [sq(C, mh, ring_r, ring_r, 0, 360, n=2.0)] + pen(0.8, [sq(C, mh, 100, 112, 48, 312)])
    G['registered'] = [sq(C, mh, ring_r, ring_r, 0, 360, n=2.0)] + pen(0.8, [
        [(C - 70, mh - 120), (C - 70, mh + 115), (C + 15, mh + 115)] + sq(C + 15, mh + 52, 63, 63, 90, -90) +
        [(C - 70, mh - 11)], [(C + 5, mh - 11), (C + 80, mh - 120)]])
    G['trademark'] = pen(0.6, [[(L - 58, c), (C - 62, c)], [(L + 40, c), (L + 40, c - 230)],
                               [(C + 22, c - 230), (C + 22, c), (C + 112, c - 140), (R + 52, c), (R + 52, c - 230)]])
    G['ordfeminine'] = pen(0.78, scale(G['a'], 0.52, C, X, 0.52)) + pen(0.78, [[(L + 30, X - 280 + 0), (R - 30, X - 280)]])
    G['ordfeminine'] = pen(0.78, translate(scale(G['a'], 0.52, C, 0), 0, 420)) + pen(0.78, [[(L + 40, 340), (R - 40, 340)]])
    G['ordmasculine'] = pen(0.78, translate(scale(G['o'], 0.52, C, 0), 0, 420)) + pen(0.78, [[(L + 40, 340), (R - 40, 340)]])
    G['degree'] = pen(0.85, [sq(C, c - 105, 100, 100, 0, 360)])
    G['paragraph'] = [[(C, c), (R - 15, c)], [(C, c)] + sq(C, c - 150, 172, 150 + OV, 90, 270) + [(C, c - 300)],
                      [(C, c), (C, b - 0)], [(R - 15, c), (R - 15, b)]]
    G['brokenbar'] = [[(C, 780), (C, 360)], [(C, 220), (C, -180)]]

    # ── accents: spacing forms (lowercase height, centred at C) ──
    y0, y0c = X + 92, H + 68           # bottom centre-line of lowercase / capital marks
    ring_r2 = 52 + S * 0.32
    def marks(y, k=1.0):
        return {
            'grave': [[(C + 58, y), (C - 55, y + 135 * k)]],
            'acute': [[(C - 58, y), (C + 55, y + 135 * k)]],
            'circumflex': [[(C - 125, y), (C, y + 120 * k), (C + 125, y)]],
            'caron': [[(C - 125, y + 120 * k), (C, y), (C + 125, y + 120 * k)]],
            'breve': [sq(C, y + 100 * k, 118, 100 * k, 182, 358)],
            'macron': [[(C - 125, y + 55 * k), (C + 125, y + 55 * k)]],
            'dieresis': [dot(C - 105, y + 50 * k), dot(C + 105, y + 50 * k)],
            'dotaccent': [dot(C, y + 50 * k)],
            'ring': [sq(C, y + ring_r2 - 5, ring_r2, ring_r2, 0, 360, n=2.3)],
            'tilde': [spline([(C - 128, y + 12 * k), (C - 66, y + 82 * k), (C + 2, y + 48 * k),
                              (C + 66, y + 14 * k), (C + 128, y + 84 * k)])],
            'hungarumlaut': [[(C - 118, y), (C - 38, y + 135 * k)], [(C + 34, y), (C + 114, y + 135 * k)]],
        }
    lower_marks, cap_marks = marks(y0), marks(y0c, 0.85)
    below = {
        'cedilla': [[(C + 6, -12), (C + 6, -60)] + spline([(C + 6, -60), (C + 84, -98), (C + 76, -172),
                                                          (C - 4, -205), (C - 78, -192)])[1:]],
        'commaaccent': [[(C + 16, -62), (C - 42, -205)]],
        'ogonek': [spline([(C, 18), (C - 62, -78), (C - 42, -170), (C + 42, -204)])],
    }
    above_extra = {
        'commaturnedabove': [dot(C, y0 + 42), [(C - 22, y0 + 46), (C + 48, y0 + 176)]],
        'caronvertical': [[(C + 8, A - hv + 4), (C - 14, A - 175)]],     # apostrophe-style caron for ď ľ ť Ľ
    }
    spacing_names = {'grave': None, 'acute': 'acute', 'circumflex': 'circumflex', 'caron': 'caron', 'breve': 'breve',
                     'macron': 'macron', 'dieresis': 'dieresis', 'dotaccent': 'dotaccent', 'ring': 'ring',
                     'tilde': 'tilde', 'hungarumlaut': 'hungarumlaut'}
    for k_, v in lower_marks.items():
        if spacing_names.get(k_):
            G[spacing_names[k_]] = v
    G['cedilla'] = below['cedilla']
    G['ogonek'] = translate(below['ogonek'], 40, 0)

    # combining marks: zero-width, drawn over the previous cell (x - 600)
    comb = {'grave': 'gravecomb', 'acute': 'acutecomb', 'circumflex': 'uni0302', 'tilde': 'tildecomb',
            'macron': 'uni0304', 'breve': 'uni0306', 'dotaccent': 'uni0307', 'dieresis': 'uni0308',
            'ring': 'uni030A', 'hungarumlaut': 'uni030B', 'caron': 'uni030C'}
    M = {}
    for k_, nm in comb.items():
        M[nm] = translate(lower_marks[k_], -W, 0)
        M[nm + '.case'] = translate(cap_marks[k_], -W, 0)
    M['uni0326'] = translate(below['commaaccent'], -W, 0)
    M['uni0327'] = translate(below['cedilla'], -W, 0)
    M['uni0328'] = translate(below['ogonek'], -W, 0)
    M['commaturnedabovecomb'] = translate(above_extra['commaturnedabove'], -W, 0)
    M['caronvertical'] = above_extra['caronvertical']

    # ── the composition set ─────────────────────────────────
    U = {}
    U['uni2218'] = [sq(C, AX, 105, 105, 0, 360)]
    U['arrowright'] = [[(L - 40, AX), (R + 25, AX)], [(R - 120, AX + 130), (R + 25, AX), (R - 120, AX - 130)]]
    U['arrowleft'] = mirror(U['arrowright'])
    U['arrowdblright'] = [[(L - 40, AX + 75), (R - 85, AX + 75)], [(L - 40, AX - 75), (R - 85, AX - 75)],
                          [(R - 150, AX + 190), (R + 30, AX), (R - 150, AX - 190)]]
    U['arrowdblleft'] = mirror(U['arrowdblright'])
    U['uni21A6'] = U['arrowright'] + [[(L - 40, AX - 120), (L - 40, AX + 120)]]
    lt = 0.46
    U['uni03BB'] = [[(L + 20, a), (R + 5, b)], [(L + 20 + lt * (R + 5 - L - 20), a - lt * (a - b)), (L - 5, b)]]
    U['uni039B'] = [[(L - 10, b), (C, c), (R + 10, b)]]
    U['universal'] = [[(L - 10, c), (C, b), (R + 10, c)], [(L + 62, 440), (R - 62, 440)]]
    U['existential'] = [[(L, c), (R, c), (R, b), (L, b)], [(L + 40, mh), (R, mh)]]
    U['equivalence'] = [[(L + 10, AX + s_), (R - 10, AX + s_)] for s_ in (-140, 0, 140)]
    U['notequal'] = G['equal'] + [[(R - 40, AX + 230), (L + 40, AX - 230)]]
    U['lessequal'] = [[(R - 15, AX + 290), (L + 15, AX + 100), (R - 15, AX - 90)], [(L + 15, AX - 220), (R - 15, AX - 220)]]
    U['greaterequal'] = mirror(U['lessequal'])
    U['congruent'] = [spline([(L - 5, AX + 120), (L + 85, AX + 195), (C, AX + 155), (R - 85, AX + 115), (R + 5, AX + 190)]),
                      [(L + 10, AX - 20), (R - 10, AX - 20)], [(L + 10, AX - 160), (R - 10, AX - 160)]]
    ring = sq(C, AX, rx + 15, rx + 15, 0, 360)
    o45 = (rx + 15) * 0.7071
    U['circlemultiply'] = [ring, [(C - o45, AX - o45), (C + o45, AX + o45)], [(C - o45, AX + o45), (C + o45, AX - o45)]]
    U['circleplus'] = [ring, [(C - rx - 15, AX), (C + rx + 15, AX)], [(C, AX - rx - 15), (C, AX + rx + 15)]]
    U['multiply'] = [[(L + 30, AX - 165), (R - 30, AX + 165)], [(L + 30, AX + 165), (R - 30, AX - 165)]]
    U['periodcentered'] = [dot(C, AX)]
    U['bullet'] = [dot(C, AX, DR + 40)]
    U['element'] = [[(R - 5, AX + 250)] + sq(R - 5, AX, R - 5 - (L + 15), 250, 90, 270) + [(R - 5, AX - 250)],
                    [(L + 40, AX), (R - 5, AX)]]
    U['uni22A5'] = [[(C, c), (C, b)], [(L - 15, b), (R + 15, b)]]
    U['uni22A4'] = [[(C, c), (C, b)], [(L - 15, c), (R + 15, c)]]
    U['emptyset'] = [sq(C, mh, rx, RY, 0, 360), [(R + 25, c + 40), (L - 25, b - 40)]]
    U['uni25CC'] = [dot(C + 210 * math.cos(math.radians(k_ * 30)), GY + 210 * math.sin(math.radians(k_ * 30)),
                        DR * 0.5) for k_ in range(12)]
    U['ellipsis'] = [dot(C - 175, DR), dot(C, DR), dot(C + 175, DR)]
    U['logicalnot'] = [[(L + 10, AX + 100), (R - 10, AX + 100), (R - 10, AX - 60)]]
    G.update(U)

    # cedilla / ogonek letters are drawn as one stroke-set so the mark joins its letter cleanly
    def attach(base, mark, dx):
        return G[base] + translate(mark, dx, 0)
    J = {
        'Ccedilla': attach('C', below['cedilla'], 0), 'ccedilla': attach('c', below['cedilla'], 0),
        'Scedilla': attach('S', below['cedilla'], 0), 'scedilla': attach('s', below['cedilla'], 0),
        'Aogonek': attach('A', below['ogonek'], R - 5 - C), 'aogonek': attach('a', below['ogonek'], R - C),
        'Eogonek': attach('E', below['ogonek'], R - 10 - C), 'eogonek': attach('e', below['ogonek'], C + 70 - C),
        'Iogonek': attach('I', below['ogonek'], R - 50 - C), 'iogonek': attach('i', below['ogonek'], R - 10 - C),
        'iogonek.dotless': attach('dotlessi', below['ogonek'], R - 10 - C),
        'Uogonek': attach('U', below['ogonek'], C + 60 - C), 'uogonek': attach('u', below['ogonek'], R - C),
    }
    G.update(J)
    return G, M


# anchors: x position of the 'top' mark on each base (default: centre of the cell)
TOP_X = {'r': C - 5, 'L': L + 60, 'f': C + 20, 'dotlessj': C + 60, 'k': L + 40, 't': C - 10, 'l': C}
