"""Parser mínimo de 'd' SVG -> skia.Path (M L H V C S Q Z A, abs/rel)."""
import re
import skia

_tok = re.compile(r"[MmLlHhVvCcSsQqZzAa]|-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


def _flags(tokens):
    # Los flags de arco pueden venir pegados ("00"), separarlos.
    out = []
    for t in tokens:
        out.append(t)
    return out


def parse(d):
    toks = _tok.findall(d)
    p = skia.Path()
    i = 0
    cmd = None
    cx = cy = sx = sy = 0.0
    lcx = lcy = None
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                p.close(); cx, cy = sx, sy; lcx = None
                continue
        rel = cmd.islower(); c = cmd.upper()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        if c == "M":
            cx, cy = ox + num(), oy + num(); sx, sy = cx, cy
            p.moveTo(cx, cy); cmd = "l" if rel else "L"; lcx = None
        elif c == "L":
            cx, cy = ox + num(), oy + num(); p.lineTo(cx, cy); lcx = None
        elif c == "H":
            cx = ox + num(); p.lineTo(cx, cy); lcx = None
        elif c == "V":
            cy = (cy if rel else 0) + num(); p.lineTo(cx, cy); lcx = None
        elif c == "C":
            x1, y1 = ox + num(), oy + num(); x2, y2 = ox + num(), oy + num()
            cx, cy = ox + num(), oy + num(); p.cubicTo(x1, y1, x2, y2, cx, cy); lcx, lcy = x2, y2
        elif c == "S":
            x1, y1 = (2 * cx - lcx, 2 * cy - lcy) if lcx is not None else (cx, cy)
            x2, y2 = ox + num(), oy + num(); cx, cy = ox + num(), oy + num()
            p.cubicTo(x1, y1, x2, y2, cx, cy); lcx, lcy = x2, y2
        elif c == "Q":
            x1, y1 = ox + num(), oy + num(); cx, cy = ox + num(), oy + num()
            p.quadTo(x1, y1, cx, cy); lcx = None
        elif c == "A":
            rx, ry, rot = num(), num(), num()
            # flags: tokens tipo "00" o "0" "0"
            f = toks[i]
            if len(f) > 1 and set(f) <= set("01") :
                la, sw = int(f[0]), int(f[1]); i += 1
                if len(f) > 2:
                    toks.insert(i, f[2:])
            else:
                la = int(float(toks[i])); i += 1
                f2 = toks[i]
                if len(f2) > 1 and f2[0] in "01" and not f2.startswith(("0.", "1.")):
                    sw = int(f2[0]); toks[i] = f2[1:]
                else:
                    sw = int(float(f2)); i += 1
            x, y = ox + num(), oy + num()
            p.arcTo(rx, ry, rot, skia.Path.ArcSize.kLarge_ArcSize if la else skia.Path.ArcSize.kSmall_ArcSize,
                    skia.PathDirection.kCW if sw else skia.PathDirection.kCCW, x, y)
            cx, cy = x, y; lcx = None
    return p
