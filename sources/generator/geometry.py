"""Geometry for Sutra Mono.

A glyph is a list of skeleton items:
  * a polyline  [(x, y), ...]            stroked with the pen
  * ('dot', x, y, r)                       a filled round dot
  * ('pen', scale, polyline)               a polyline stroked with a smaller/larger pen

`stroke` turns skeletons into a filled shape with an elliptical pen (horizontals a little
lighter than verticals, the classic optical correction), and `fit_contours` turns the dense
polygon back into clean cubic Bézier contours with nodes at extrema.
"""
import math
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import affinity

N_DEFAULT = 2.7


# ── curve primitives ─────────────────────────────────────────────────────────
def sq(cx, cy, rx, ry, t0, t1, n=N_DEFAULT, step=1.5):
    """Superellipse arc |x/rx|^n + |y/ry|^n = 1, angles in degrees; t1 < t0 runs clockwise."""
    k = max(2, int(abs(t1 - t0) / step))
    out = []
    for i in range(k + 1):
        t = math.radians(t0 + (t1 - t0) * i / k)
        c, s = math.cos(t), math.sin(t)
        out.append((cx + rx * math.copysign(abs(c) ** (2 / n), c),
                    cy + ry * math.copysign(abs(s) ** (2 / n), s)))
    return out


def sq_point(cx, cy, rx, ry, t, n=N_DEFAULT):
    t = math.radians(t)
    c, s = math.cos(t), math.sin(t)
    return (cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(s) ** (2 / n), s))


def spline(pts, k=28):
    """Centripetal Catmull–Rom through pts."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t +
                                    (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 +
                                    (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3) for d in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def bez(p0, p1, p2, p3, k=40):
    return [tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * p1[i] + 3 * (1 - t) * t * t * p2[i] + t ** 3 * p3[i]
                  for i in (0, 1)) for t in (j / k for j in range(k + 1))]


# ── skeleton transforms ──────────────────────────────────────────────────────
def _map(items, f):
    out = []
    for it in items:
        if isinstance(it, tuple) and it and it[0] == 'dot':
            x, y = f((it[1], it[2]))
            out.append(('dot', x, y, it[3]))
        elif isinstance(it, tuple) and it and it[0] == 'pen':
            out.append(('pen', it[1], [f(p) for p in it[2]]))
        else:
            out.append([f(p) for p in it])
    return out


def translate(items, dx, dy):
    return _map(items, lambda p: (p[0] + dx, p[1] + dy))


def mirror(items, cx=300):
    return _map(items, lambda p: (2 * cx - p[0], p[1]))


def rot180(items, cx, cy):
    return _map(items, lambda p: (2 * cx - p[0], 2 * cy - p[1]))


def scale(items, s, cx, cy, sy=None):
    sy = s if sy is None else sy
    return _map(items, lambda p: (cx + (p[0] - cx) * s, cy + (p[1] - cy) * sy))


# ── stroking ─────────────────────────────────────────────────────────────────
def _clean(p):
    out = [p[0]]
    for q in p[1:]:
        if abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) > 0.01:
            out.append(q)
    return out


def stroke(items, S, e=0.92, qs=40):
    """Sweep an elliptical pen (width S, height e*S) along every skeleton path; dots stay round."""
    shapes = []
    for it in items:
        if isinstance(it, tuple) and it[0] == 'dot':
            shapes.append(Point(it[1], it[2]).buffer(it[3], quad_segs=qs))
            continue
        k = 1.0
        if isinstance(it, tuple) and it[0] == 'pen':
            k, it = it[1], it[2]
        pts = _clean(it)
        if len(pts) < 2:
            continue
        ls = LineString([(x, y / e) for x, y in pts])
        g = ls.buffer(S * k / 2, cap_style='round', join_style='round', quad_segs=qs)
        shapes.append(affinity.scale(g, 1, e, origin=(0, 0)))
    u = unary_union(shapes)
    if u.is_empty:
        return []
    polys = [u] if u.geom_type == 'Polygon' else [g for g in u.geoms if g.geom_type == 'Polygon']
    return [orient(p, sign=1.0) for p in polys]   # PostScript direction: outer counter-clockwise


# ── curve fitting (Schneider, with extrema and corners as fixed nodes) ───────
def _sub(a, b): return (a[0] - b[0], a[1] - b[1])
def _add(a, b): return (a[0] + b[0], a[1] + b[1])
def _mul(a, s): return (a[0] * s, a[1] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1]
def _len(a): return math.hypot(a[0], a[1])


def _unit(a):
    l = _len(a)
    return (a[0] / l, a[1] / l) if l > 1e-12 else (0.0, 0.0)


def _bez_pt(b, t):
    mt = 1 - t
    return (mt ** 3 * b[0][0] + 3 * mt * mt * t * b[1][0] + 3 * mt * t * t * b[2][0] + t ** 3 * b[3][0],
            mt ** 3 * b[0][1] + 3 * mt * mt * t * b[1][1] + 3 * mt * t * t * b[2][1] + t ** 3 * b[3][1])


def _bez_d1(b, t):
    mt = 1 - t
    return (3 * mt * mt * (b[1][0] - b[0][0]) + 6 * mt * t * (b[2][0] - b[1][0]) + 3 * t * t * (b[3][0] - b[2][0]),
            3 * mt * mt * (b[1][1] - b[0][1]) + 6 * mt * t * (b[2][1] - b[1][1]) + 3 * t * t * (b[3][1] - b[2][1]))


def _bez_d2(b, t):
    mt = 1 - t
    return (6 * mt * (b[2][0] - 2 * b[1][0] + b[0][0]) + 6 * t * (b[3][0] - 2 * b[2][0] + b[1][0]),
            6 * mt * (b[2][1] - 2 * b[1][1] + b[0][1]) + 6 * t * (b[3][1] - 2 * b[2][1] + b[1][1]))


def _chord_params(pts):
    u = [0.0]
    for i in range(1, len(pts)):
        u.append(u[-1] + _len(_sub(pts[i], pts[i - 1])))
    tot = u[-1] or 1.0
    return [x / tot for x in u]


def _generate(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    C = [[0, 0], [0, 0]]
    X = [0, 0]
    for i, ui in enumerate(u):
        mt = 1 - ui
        A1 = _mul(t1, 3 * mt * mt * ui)
        A2 = _mul(t2, 3 * mt * ui * ui)
        C[0][0] += _dot(A1, A1); C[0][1] += _dot(A1, A2); C[1][1] += _dot(A2, A2)
        b0, b1, b2, b3 = mt ** 3, 3 * mt * mt * ui, 3 * mt * ui * ui, ui ** 3
        tmp = _sub(pts[i], _add(_mul(p0, b0 + b1), _mul(p3, b2 + b3)))
        X[0] += _dot(A1, tmp); X[1] += _dot(A2, tmp)
    C[1][0] = C[0][1]
    det = C[0][0] * C[1][1] - C[0][1] * C[1][0]
    seg = _len(_sub(p3, p0))
    if abs(det) > 1e-12:
        a1 = (X[0] * C[1][1] - X[1] * C[0][1]) / det
        a2 = (C[0][0] * X[1] - C[1][0] * X[0]) / det
    else:
        a1 = a2 = seg / 3
    eps = 1e-6 * seg
    if a1 < eps or a2 < eps or a1 > seg * 1.2 or a2 > seg * 1.2:
        a1 = a2 = seg / 3
    return (p0, _add(p0, _mul(t1, a1)), _add(p3, _mul(t2, a2)), p3)


def _max_err(pts, b, u):
    m, idx = 0.0, len(pts) // 2
    for i, ui in enumerate(u):
        d = _len(_sub(_bez_pt(b, ui), pts[i]))
        if d > m:
            m, idx = d, i
    return m, idx


def _reparam(pts, b, u):
    out = []
    for p, ui in zip(pts, u):
        d = _sub(_bez_pt(b, ui), p)
        d1, d2 = _bez_d1(b, ui), _bez_d2(b, ui)
        num = _dot(d, d1)
        den = _dot(d1, d1) + _dot(d, d2)
        out.append(min(1.0, max(0.0, ui - num / den)) if abs(den) > 1e-12 else ui)
    return out


def _fit(pts, t1, t2, tol, depth=0):
    if len(pts) == 2 or _len(_sub(pts[-1], pts[0])) < 1.5:
        d = _len(_sub(pts[-1], pts[0])) / 3
        return [(pts[0], _add(pts[0], _mul(t1, d)), _add(pts[-1], _mul(t2, d)), pts[-1])]
    u = _chord_params(pts)
    b = _generate(pts, u, t1, t2)
    err, idx = _max_err(pts, b, u)
    if err < tol:
        return [b]
    if err < tol * 6:
        for _ in range(8):
            u = _reparam(pts, b, u)
            b = _generate(pts, u, t1, t2)
            err, idx = _max_err(pts, b, u)
            if err < tol:
                return [b]
    if depth > 12 or len(pts) < 4:
        return [b]
    idx = max(1, min(len(pts) - 2, idx))
    tc = _unit(_sub(pts[idx - 1], pts[idx + 1]))
    return (_fit(pts[:idx + 1], t1, tc, tol, depth + 1) +
            _fit(pts[idx:], _mul(tc, -1), t2, tol, depth + 1))


def _turn(a, b, c):
    v1, v2 = _sub(b, a), _sub(c, b)
    l1, l2 = _len(v1), _len(v2)
    if l1 < 1e-9 or l2 < 1e-9:
        return 0.0
    cr = (v1[0] * v2[1] - v1[1] * v2[0]) / (l1 * l2)
    dt = _dot(v1, v2) / (l1 * l2)
    return math.degrees(math.atan2(cr, dt))


def _densify(ring, maxlen=6.0):
    out = []
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        out.append(a)
        d = _len(_sub(b, a))
        if d > maxlen and not _is_axis(a, b):
            k = int(d // maxlen)
            for j in range(1, k + 1):
                t = j / (k + 1)
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _is_axis(a, b, tol=0.02):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < tol or dy < tol


def fit_ring(ring, tol=0.55, corner=28.0, straight=36.0):
    """Return a closed contour as a list of segments: ('line', p0, p1) or ('curve', p0, c1, c2, p3)."""
    pts = [tuple(p) for p in ring]
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    clean = []
    for p in pts:
        if not clean or _len(_sub(p, clean[-1])) > 0.05:
            clean.append(p)
    if _len(_sub(clean[0], clean[-1])) <= 0.05:
        clean.pop()
    # merge collinear runs so a straight stem is one edge
    merged = True
    while merged and len(clean) > 4:
        merged = False
        out = []
        m = len(clean)
        i = 0
        drop = set()
        for i in range(m):
            if i in drop:
                continue
            if abs(_turn(clean[i - 1], clean[i], clean[(i + 1) % m])) < 0.25 and (i - 1) % m not in drop:
                drop.add(i)
        if drop:
            clean = [p for k, p in enumerate(clean) if k not in drop]
            merged = True
    pts = clean
    n = len(pts)
    # 1. long straight edges (stems, bars, diagonals)
    is_line_seg = [_len(_sub(pts[(i + 1) % n], pts[i])) >= straight for i in range(n)]
    # 2. nodes: corners, ends of straight edges, extrema
    node = [False] * n
    for i in range(n):
        if abs(_turn(pts[i - 1], pts[i], pts[(i + 1) % n])) > corner:
            node[i] = True
        if is_line_seg[i] or is_line_seg[i - 1]:
            node[i] = True
    for d in (0, 1):
        # direction sign per edge with a dead zone; an extremum is where the sign flips
        sg = []
        for i in range(n):
            v = pts[(i + 1) % n][d] - pts[i][d]
            el = _len(_sub(pts[(i + 1) % n], pts[i])) or 1
            sg.append(0 if abs(v) / el < 0.01 else (1 if v > 0 else -1))
        if not any(sg):
            continue
        k0 = next(i for i in range(n) if sg[i] != 0)
        prev, prev_i = sg[k0], k0
        for step in range(1, n + 1):
            i = (k0 + step) % n
            if sg[i] == 0:
                continue
            if sg[i] != prev:
                # flat zone between prev_i+1 .. i : put the node at its middle (or the vertex if none)
                a, b = (prev_i + 1) % n, i
                span = (b - a) % n
                if any(is_line_seg[(a + j) % n] for j in range(span)):
                    pass                              # a straight edge already carries the nodes
                else:
                    if span == 0:
                        node[a] = True
                    else:
                        # pick the vertex with the extreme coordinate in the flat zone
                        cand = [(a + j) % n for j in range(span + 1)]
                        tgt = max if prev > 0 else min
                        node[tgt(cand, key=lambda q: pts[q][d])] = True
            prev, prev_i = sg[i], i
    if not any(node):
        node[max(range(n), key=lambda i: pts[i][1])] = True
    start = node.index(True)
    pts = pts[start:] + pts[:start]
    node = node[start:] + node[:start]
    is_line_seg = is_line_seg[start:] + is_line_seg[:start]
    idxs = [i for i in range(n) if node[i]] + [n]

    def tangent_out(i):
        # direction leaving node i along the ring
        for j in range(1, 4):
            v = _sub(pts[(i + j) % n], pts[i])
            if _len(v) > 0.5:
                return _snap(_unit(v), pts, i, n)
        return _unit(_sub(pts[(i + 1) % n], pts[i]))

    def tangent_in(i):
        for j in range(1, 4):
            v = _sub(pts[i % n], pts[(i - j) % n])
            if _len(v) > 0.5:
                return _snap(_unit(v), pts, i % n, n)
        return _unit(_sub(pts[i % n], pts[(i - 1) % n]))

    segs = []
    for a, b in zip(idxs[:-1], idxs[1:]):
        run = [pts[k % n] for k in range(a, b + 1)]
        if b - a == 1 and is_line_seg[a]:
            segs.append(('line', run[0], run[-1]))
            continue
        if _max_dev(run) < tol:
            segs.append(('line', run[0], run[-1]))
            continue
        run = _densify(run[:-1] + [run[-1]], 4.0) if len(run) < 8 else run
        t1 = tangent_out(a)
        t2 = _mul(tangent_in(b), -1)
        # smooth joins: if the previous / next segment is a straight line, use its direction
        if is_line_seg[(a - 1) % n] and not node_is_corner(pts, a, n, corner):
            t1 = _unit(_sub(pts[a % n], pts[(a - 1) % n]))
        if is_line_seg[b % n] and not node_is_corner(pts, b, n, corner):
            t2 = _mul(_unit(_sub(pts[(b + 1) % n], pts[b % n])), -1)
        for bz in _fit(run, t1, t2, tol):
            segs.append(('curve',) + tuple(bz))
    return segs


def node_is_corner(pts, i, n, corner):
    return abs(_turn(pts[(i - 1) % n], pts[i % n], pts[(i + 1) % n])) > corner


def _snap(t, pts, i, n, ang=4.0):
    """Snap a tangent to horizontal/vertical when it is within `ang` degrees (keeps extrema clean)."""
    a = math.degrees(math.atan2(t[1], t[0]))
    for target in (0, 90, 180, -90, -180):
        if abs(a - target) < ang:
            r = math.radians(target)
            return (round(math.cos(r)), round(math.sin(r)))
    return t


def _max_dev(run):
    a, b = run[0], run[-1]
    v = _sub(b, a)
    l = _len(v)
    if l < 1e-9:
        return max(_len(_sub(p, a)) for p in run)
    return max(abs((p[0] - a[0]) * v[1] - (p[1] - a[1]) * v[0]) / l for p in run)


def fit_polygons(polys, tol=0.55):
    """Polygons → list of contours (each a list of segments)."""
    out = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            coords = list(ring.coords)
            if len(coords) < 4:
                continue
            out.append(fit_ring(coords, tol))
    return out


def _merge_lines(segs):
    """Join consecutive straight segments that are collinear after rounding."""
    r = lambda p: (int(round(p[0])), int(round(p[1])))
    out = []
    for s in segs:
        if out and s[0] == 'line' and out[-1][0] == 'line':
            a, b, c = r(out[-1][1]), r(out[-1][2]), r(s[2])
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            l1 = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            l2 = math.hypot(c[0] - b[0], c[1] - b[1]) or 1
            tol = 0.15 if min(l1, l2) < 12 else 0.035
            if abs(cr) / (l1 * l2) < tol and ((b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])) > 0:
                out[-1] = ('line', out[-1][1], s[2])
                continue
        out.append(s)
    # wrap-around: last line + first line
    if len(out) > 2 and out[0][0] == 'line' and out[-1][0] == 'line':
        a, b, c = r(out[-1][1]), r(out[-1][2]), r(out[0][2])
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        l1 = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        l2 = math.hypot(c[0] - b[0], c[1] - b[1]) or 1
        if abs(cr) / (l1 * l2) < 0.02 and ((b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])) > 0:
            first = ('line', out[-1][1], out[0][2])
            out = [first] + out[1:-1]
    return out


def draw_contours(contours, pen, round_to=1):
    """Draw fitted contours into a segment pen with integer coordinates."""
    r = lambda p: (int(round(p[0])), int(round(p[1])))
    for segs in contours:
        segs = _merge_lines(segs)
        if not segs:
            continue
        start = r(segs[0][1])
        pen.moveTo(start)
        last = start
        for i, s in enumerate(segs):
            if s[0] == 'line':
                q = r(s[2])
                if i == len(segs) - 1 and q == start:
                    continue          # closePath draws the closing line
                if q != last:
                    pen.lineTo(q)
                    last = q
            else:
                q = r(s[4])
                c1, c2 = r(s[2]), r(s[3])
                if q == last and c1 == last and c2 == last:
                    continue
                if c1 == last and c2 == q:
                    if q != last:
                        pen.lineTo(q)
                else:
                    pen.curveTo(c1, c2, q)
                last = q
        pen.closePath()
