"""Rotulación propia en vectores, inspirada en una grotesca geométrica
condensada y ultra-negra (familia visual Futura Condensed ExtraBold).
Unidades: altura de mayúscula = 1, línea base en y=0, y hacia abajo."""
import skia

WV = 0.225   # grosor de astas verticales
WH = 0.165   # grosor de trazos horizontales
K = WV / WH  # contraste: se trazan curvas en espacio escalado en x


def _rect(x0, y0, x1, y1):
    p = skia.Path(); p.addRect(skia.Rect.MakeLTRB(x0, y0, x1, y1)); return p


def _poly(pts):
    p = skia.Path(); p.addPoly([skia.Point(*q) for q in pts], True); return p


def _u(*ps):
    out = ps[0]
    for p in ps[1:]:
        out = skia.Op(out, p, skia.PathOp.kUnion_PathOp)
    return out


def _sub(a, b):
    return skia.Op(a, b, skia.PathOp.kDifference_PathOp)


def _isect(a, b):
    return skia.Op(a, b, skia.PathOp.kIntersect_PathOp)


def _rrect_stroke(x0, y0, x1, y1, radii):
    """Contorno de rrect por línea central, con contraste vertical/horizontal.
    radii = (tl, tr, br, bl) cada uno (rx, ry) en espacio real."""
    m = skia.Matrix.Scale(1 / K, 1)
    rr = skia.RRect()
    rr.setRectRadii(skia.Rect.MakeLTRB(x0 / K, y0, x1 / K, y1),
                    [skia.Point(rx / K, ry) for rx, ry in radii])
    p = skia.Path(); p.addRRect(rr)
    paint = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=WH,
                       StrokeJoin=skia.Paint.kMiter_Join)
    dst = skia.Path(); paint.getFillPath(p, dst)
    dst.transform(skia.Matrix.Scale(K, 1))
    return dst


def _stadium(x0, y0, x1, y1, ry_k=1.25):
    rx = (x1 - x0) / 2
    ry = min(rx * ry_k, (y1 - y0) / 2)
    return _rrect_stroke(x0, y0, x1, y1, [(rx, ry)] * 4)


def g_T():
    W = 0.50
    return _u(_rect(0, -1, W, -1 + WH), _rect(W / 2 - WV / 2, -1, W / 2 + WV / 2, 0)), W


def g_I():
    return _rect(0, -1, WV, 0), WV


def g_L():
    W = 0.40
    return _u(_rect(0, -1, WV, 0), _rect(0, -WH, W, 0)), W


def g_E():
    W = 0.42
    return _u(_rect(0, -1, WV, 0), _rect(0, -1, W, -1 + WH), _rect(0, -WH, W, 0),
              _rect(0, -0.5 - WH / 2, W - 0.03, -0.5 + WH / 2)), W


def g_O():
    W = 0.56
    return _stadium(WV / 2, -1 + WH / 2, W - WV / 2, -WH / 2), W


def g_C():
    W = 0.50
    o = _stadium(WV / 2, -1 + WH / 2, W - WV / 2, -WH / 2)
    return _sub(o, _rect(W * 0.52, -0.66, W + 1, -0.34)), W


def g_D():
    W = 0.54
    rx = (W - WV) * 0.80
    ry = 0.40
    d = _rrect_stroke(WV / 2, -1 + WH / 2, W - WV / 2, -WH / 2,
                      [(0, 0), (rx, ry), (rx, ry), (0, 0)])
    return _u(d, _rect(0, -1, WV, 0)), W


def g_U():
    W = 0.54
    s = _stadium(WV / 2, -2, W - WV / 2, -WH / 2)
    return _isect(s, _rect(-1, -1, 2, 0.5)), W


def g_J():
    W = 0.46
    s = _stadium(WV / 2 - 0.02, -2, W - WV / 2, -WH / 2)
    s = _isect(s, _rect(-1, -1, 2, 0.5))
    return _sub(s, _rect(-1, -2, W * 0.45, -0.30)), W


def g_S():
    W = 0.50
    mid = -0.5
    t = _stadium(WV / 2 + 0.01, -1 + WH / 2, W - WV / 2 - 0.01, mid, ry_k=0.9)
    b = _stadium(WV / 2, mid, W - WV / 2, -WH / 2, ry_k=0.9)
    cyT = (-1 + WH / 2 + mid) / 2
    cyB = (mid - WH / 2) / 2
    cx = W / 2
    keep_t = _u(_rect(-1, -2, 2, cyT - 0.06), _rect(-1, cyT - 0.1, cx, 0))
    keep_b = _u(_rect(-1, cyB + 0.06, 2, 1), _rect(cx, -2, 2, cyB + 0.1))
    return _u(_isect(t, keep_t), _isect(b, keep_b)), W


def g_A():
    W = 0.58
    th = 0.235   # grosor horizontal de pierna
    a0, a1 = W / 2 - 0.06, W / 2 + 0.06
    lft = _poly([(0, 0), (a0, -1), (a1, -1), (th, 0)])
    rgt = _poly([(W, 0), (a1, -1), (a0, -1), (W - th, 0)])
    bar = _rect(0.1, -0.33, W - 0.1, -0.33 + WH * 0.9)
    return _u(lft, rgt, bar), W


def g_R():
    W = 0.52
    mid = -0.44
    rx = (W - 0.03 - WV / 2) - WV / 2
    ry = min(rx * 1.1, 0.25)
    bowl = _rrect_stroke(WV / 2, -1 + WH / 2, W - 0.03 - WV / 2, mid,
                         [(0, 0), (rx, ry), (rx, ry), (0, 0)])
    leg = _poly([(W * 0.40, mid + WH / 2 - 0.02), (W * 0.40 + 0.23, mid + WH / 2 - 0.02),
                 (W, 0), (W - 0.24, 0)])
    return _u(bowl, _rect(0, -1, WV, 0), leg), W


def g_Y():
    W = 0.58
    th = 0.235
    j = -0.44
    cx = W / 2
    la = _poly([(0, -1), (th, -1), (cx + WV / 2, j), (cx - WV / 2, j + 0.08)])
    ra = _poly([(W, -1), (W - th, -1), (cx - WV / 2, j), (cx + WV / 2, j + 0.08)])
    return _u(la, ra, _rect(cx - WV / 2, j - 0.05, cx + WV / 2, 0)), W


def g_dot():
    p = skia.Path(); r = WV * 0.62
    p.addCircle(r, -r, r); return p, 2 * r


GLYPHS = {c: globals()["g_" + c]() for c in "TILEOCDUJSARY"}
GLYPHS["."] = g_dot()
TRACK = 0.06
SPACE = 0.24


KERN = {"LA": -0.13, "AT": -0.11, "TA": -0.11, "LY": -0.10, "AY": -0.06,
        "RY": -0.04, "YT": -0.04, "T.": -0.06, "TO": -0.015, "OT": -0.015}


def word_path(text, track=TRACK):
    """Devuelve (path, ancho, [(char, x, w)]) en unidades de altura=1."""
    p = skia.Path(); x = 0.0; info = []
    for i, ch in enumerate(text):
        if ch == " ":
            x += SPACE; continue
        if i > 0:
            x += KERN.get(text[i - 1] + ch, 0.0)
        g, w = GLYPHS[ch]
        q = skia.Path(g); q.offset(x, 0); p.addPath(q)
        info.append((ch, x, w))
        x += w + track
    return p, x - track, info


def glyph(ch):
    return GLYPHS[ch]
