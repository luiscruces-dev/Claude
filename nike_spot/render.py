"""Render del spot Nike 15 s, 1080x1920 @ 60 fps.

Motion blur real: cada fotograma integra N submuestras temporales dentro de
un obturador de 216° (0.6 fotograma), acumuladas en luz lineal. Todas las
submuestras de un fotograma se evalúan con el plano (shot) al que pertenece
ese fotograma, y los cortes caen siempre en el límite exacto de fotograma, así
que nunca se mezclan dos planos en un mismo fotograma."""
import math
import re
import sys

import numpy as np
import skia

import font
import svgpath
from timeline import *

W, H = 1080, 1920
CX, CY = W / 2, H / 2
SHUTTER = 0.6
SAMPLES = 24

BLACK = skia.Color(0, 0, 0)
WHITE = skia.Color(255, 255, 255)
VOLT = skia.Color(212, 255, 0)
GREY = skia.Color(30, 30, 30)

# --- Recursos -------------------------------------------------------------
_d = re.search(r'd="([^"]+)"', open(__file__.rsplit("/", 1)[0] + "/brand/nike-swoosh.svg").read()).group(1)
SWOOSH = svgpath.parse(_d)          # unidades 24x24, bounds x 0..24, y 7.8..16.2
SW_C = (12.0, 12.0)
# Espina del swoosh (punta del gancho -> curva -> punta de la hoja) para "draw-on"
SPINE = skia.Path()
SPINE.moveTo(3.35, 10.05)
SPINE.cubicTo(1.2, 12.3, 0.4, 14.6, 1.8, 15.6)
SPINE.cubicTo(3.0, 16.4, 5.2, 15.9, 7.0, 15.2)
SPINE.lineTo(24.0, 7.8)
SPINE_LEN = skia.PathMeasure(SPINE, False).getLength()
# Filo superior de la hoja (línea de corte)
BLADE_A = (6.442, 15.276)
BLADE_B = (24.0, 7.8)
BLADE_ANG = math.atan2(BLADE_B[1] - BLADE_A[1], BLADE_B[0] - BLADE_A[0])

WORD_CACHE = {}


def word(text):
    if text not in WORD_CACHE:
        WORD_CACHE[text] = font.word_path(text)
    return WORD_CACHE[text]


# --- Utilidades de animación ---------------------------------------------
def T(step):
    return step * STEP


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_expo(x):
    x = clamp(x)
    return 0.0 if x <= 0 else 2 ** (10 * (x - 1))


def in_cubic(x):
    x = clamp(x); return x * x * x


def out_cubic(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def in_out_cubic(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.7):
    x = clamp(x) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def env(t, t0, tau):
    return math.exp(-(t - t0) / tau) if t >= t0 else 0.0


def spring(x, freq=4.5, damp=5.0):
    """Respuesta de muelle 0->1 (con overshoot)."""
    if x <= 0:
        return 0.0
    return 1 - math.exp(-damp * x) * math.cos(2 * math.pi * freq * x)


def hash01(*a):
    h = math.sin(sum(v * k for v, k in zip(a, (12.9898, 78.233, 37.719, 4.581)))) * 43758.5453
    return h - math.floor(h)


def smooth_noise(t, seed):
    i = math.floor(t); f = t - i
    a, b = hash01(i, seed) * 2 - 1, hash01(i + 1, seed) * 2 - 1
    f = f * f * (3 - 2 * f)
    return a + (b - a) * f


def paint(color, aa=True, alpha=1.0, style=None, sw=0):
    p = skia.Paint(AntiAlias=aa, Color=color)
    if alpha < 1:
        p.setAlphaf(alpha)
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(sw)
    return p


def lerp_color(c1, c2, a):
    a = clamp(a)
    r = skia.Color4f(c1); s = skia.Color4f(c2)
    return skia.Color4f(r.fR + (s.fR - r.fR) * a, r.fG + (s.fG - r.fG) * a,
                        r.fB + (s.fB - r.fB) * a, 1).toColor()


# --- Primitivas de marca --------------------------------------------------
def swoosh_matrix(cx, cy, width, rot_deg, anchor=SW_C):
    m = skia.Matrix()
    s = width / 24.0
    m.setTranslate(-anchor[0], -anchor[1])
    m.postScale(s, s)
    m.postRotate(rot_deg)
    m.postTranslate(cx, cy)
    return m


def draw_swoosh(c, m, p, reveal=1.0, reveal_from=0.0):
    if reveal <= 0:
        return
    c.save()
    c.concat(m)
    if reveal >= 1 and reveal_from <= 0:
        c.drawPath(SWOOSH, p)
    else:
        seg = skia.Path()
        pm = skia.PathMeasure(SPINE, False)
        pm.getSegment(SPINE_LEN * reveal_from, SPINE_LEN * reveal, seg, True)
        c.clipPath(SWOOSH, doAntiAlias=True)
        sp = skia.Paint(p)
        sp.setStyle(skia.Paint.kStroke_Style)
        sp.setStrokeWidth(3.4)
        sp.setStrokeCap(skia.Paint.kRound_Cap)
        c.drawPath(seg, sp)
    c.restore()


def draw_word(c, text, x, y_base, cap, p, align="left"):
    path, w, _ = word(text)
    if align == "center":
        x -= w * cap / 2
    elif align == "right":
        x -= w * cap
    c.save(); c.translate(x, y_base); c.scale(cap, cap); c.drawPath(path, p); c.restore()
    return w * cap


def shake(c, t, hits, amp=26.0, tau=0.12, rot=1.2):
    a = sum(env(t, h, tau) * k for h, k in hits)
    if a <= 0.001:
        return
    dx = smooth_noise(t * 38, 1) * amp * a
    dy = smooth_noise(t * 38, 2) * amp * a
    r = smooth_noise(t * 31, 3) * rot * a
    c.translate(CX + dx, CY + dy); c.rotate(r); c.translate(-CX, -CY)


# --- ESCENA 1: latido (0 – 1.6 s) -----------------------------------------
def heart_pulse(t, lubs):
    s = 0.0
    for l in lubs:
        s += 0.95 * env(t, l, 0.085) + 0.45 * env(t, l + T(2), 0.07)
    return s


def scene_heart(c, t):
    c.clear(BLACK)
    lubs = [T(0), T(8)]
    z = 1 + 0.035 * t
    c.translate(CX, CY); c.scale(z, z); c.translate(-CX, -CY)
    for l in lubs:
        for k, (d, a0) in enumerate([(0.0, 0.55), (T(2), 0.3)]):
            u = (t - l - d) / 0.95
            if 0 <= u <= 1:
                r = 20 + 980 * out_expo(u)
                c.drawCircle(CX, CY, r, paint(WHITE, alpha=a0 * (1 - u) ** 2, style="stroke",
                                              sw=6 * (1 - u) + 1))
    r = 19 * (1 + heart_pulse(t, lubs))
    c.drawCircle(CX, CY, r, paint(WHITE))


# --- ESCENA 2: excusas (1.6 – 3.1 s) --------------------------------------
LEFT = 80
COLW = W - 2 * LEFT


def excuse_layout(w2):
    """Dos líneas justificadas a 920 px: TOO / <palabra>."""
    _, wt, _ = word("TOO")
    _, ww, _ = word(w2)
    h1 = COLW / wt
    h2 = min(COLW / ww, 560)
    gap = 44
    total = h1 + gap + h2
    top = CY - total / 2 - 60
    return [("TOO", LEFT, top + h1, h1), (w2, LEFT, top + h1 + gap + h2, h2)], top + total


def draw_excuse(c, t, t0, w2, col):
    lines, bottom = excuse_layout(w2)
    u = t - t0
    s = 1 + 0.22 * (1 - out_expo(u / 0.16)) + 0.02 * env(t, t0 + T(2), 0.06) + 0.04 * u
    c.save()
    c.translate(CX, CY); c.scale(s, s); c.translate(-CX, -CY)
    for txt, x, yb, cap in lines:
        draw_word(c, txt, x, yb, cap, paint(col))
    c.restore()
    return bottom


def scene_excuse(i):
    s0, w2 = WORDS[i]
    w2 = w2.split()[1]

    def f(c, t):
        c.clear(BLACK)
        t0 = T(s0)
        # temblor creciente: la presión sube con cada excusa
        if i >= 2:
            step = math.floor((t - T(24)) / STEP)
            amp = 4 + 3 * max(0, step)
            c.translate(amp * (hash01(step, 1) * 2 - 1), amp * (hash01(step, 2) * 2 - 1))
            c.translate(CX, CY); c.rotate((hash01(step, 3) * 2 - 1) * 0.25 * max(0, step)); c.translate(-CX, -CY)
        bottom = draw_excuse(c, t, t0, w2, WHITE)
        # el punto-latido sigue debajo
        lubs = [T(s) for s in HEART if s <= s0]
        r = 15 * (1 + heart_pulse(t, lubs))
        c.drawCircle(CX, bottom + 150, r, paint(WHITE))
    return f


def scene_black(c, t):
    c.clear(BLACK)


# --- ESCENA 3: el corte (3.2 – 4.4 s) --------------------------------------
SL_P0 = (CX - 110, 1045.0)
SL_W = 1180.0
SL_ROT = 12.0
SL_ANG = BLADE_ANG + math.radians(SL_ROT)


def slice_swoosh_matrix(t):
    u = t - T(DROP)
    # anclado en el punto medio del filo superior de la hoja
    fa = 0.22
    anchor = (BLADE_A[0] + (BLADE_B[0] - BLADE_A[0]) * fa, BLADE_A[1] + (BLADE_B[1] - BLADE_A[1]) * fa)
    exit_ = in_expo((t - T(42)) / 0.16)
    ang = SL_ANG
    d = 3200 * exit_
    m = swoosh_matrix(SL_P0[0] + math.cos(ang) * d, SL_P0[1] + math.sin(ang) * d, SL_W, SL_ROT, anchor)
    return m


def scene_slice(c, t):
    u = t - T(DROP)
    flip = T(36) <= t < T(38)
    bg, fg, sw = (VOLT, BLACK, BLACK) if flip else (BLACK, WHITE, VOLT)
    c.clear(bg)
    shake(c, t, [(T(DROP), 1.4), (T(38), 0.6), (T(42), 0.5)])
    # texto "TOO LATE" con el mismo estado que el último fotograma de la escena 2
    lines, _ = excuse_layout("TOO LATE".split()[1])
    s = 1 + 0.04 * (T(31) - T(28))
    ang = SL_ANG
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx                       # normal (hacia abajo-derecha de la línea)
    reveal = out_expo(u / 0.11)
    sep_slide = 70 * out_expo(u / 0.35) + 2600 * in_cubic((t - T(38)) / 0.28)
    wedge = 70 * out_expo(u / 0.14)
    big = 1e4
    for side in (-1, 1):
        c.save()
        # semiplano a un lado del filo
        poly = skia.Path()
        px, py = SL_P0
        pts = [(px - dx * big, py - dy * big), (px + dx * big, py + dy * big)]
        off = side * big
        pts += [(pts[1][0] + nx * off, pts[1][1] + ny * off), (pts[0][0] + nx * off, pts[0][1] + ny * off)]
        poly.addPoly([skia.Point(*q) for q in pts], True)
        c.clipPath(poly, doAntiAlias=True)
        # desplazamiento: cada mitad resbala a un lado del filo
        mv = side * sep_slide
        c.translate(dx * mv + nx * (wedge if side > 0 else -wedge * 0.25),
                    dy * mv + ny * (wedge if side > 0 else -wedge * 0.25))
        c.translate(CX, CY); c.scale(s, s); c.translate(-CX, -CY)
        for txt, x, yb, cap in lines:
            draw_word(c, txt, x, yb, cap, paint(fg))
        c.restore()
    m = slice_swoosh_matrix(t)
    draw_swoosh(c, m, paint(sw), reveal=reveal)


# --- ESCENA 4: pista (4.4 – 6.4 s) -----------------------------------------
TRACK_KICKS = [T(s) for s in KICK if 44 <= s < 64]
TRACK_CLAPS = [T(s) for s in CLAP if 44 <= s < 64] + [T(44)]


def cam_z(t):
    """Posición de cámara: velocidad base + empujones en cada bombo (zancadas)."""
    t0 = T(44)
    z = 15.0 * (t - t0)
    for k in TRACK_KICKS:
        if t > k:
            z += 2.2 * (1 - math.exp(-(t - k) / 0.12))
    return z


def scene_track(c, t):
    c.clear(BLACK)
    z0 = cam_z(t)
    bob = sum(0.10 * env(t, k, 0.09) for k in TRACK_KICKS)
    hcam = 1.05 - bob
    roll = 1.6 * math.sin((t - T(44)) * math.pi / (T(6) * 1.0)) + 2.0 * smooth_noise(t * 3, 9)
    f = 760.0
    yh = 640.0
    c.save()
    shake(c, t, [(k, 0.25) for k in TRACK_KICKS] + [(k, 0.45) for k in TRACK_CLAPS], amp=14)
    c.translate(CX, yh); c.rotate(roll); c.translate(-CX, -yh)
    # resplandor muy sutil en el horizonte
    g = skia.GradientShader.MakeRadial(skia.Point(CX, yh), 900,
                                       [skia.Color(34, 34, 34), BLACK])
    c.drawRect(skia.Rect.MakeXYWH(-400, -400, W + 800, H + 800), skia.Paint(Shader=g))
    camx = 0.0

    def proj(X, Z):
        zz = max(Z, 0.05)
        return CX + f * (X - camx) / zz, yh + f * hcam / zz

    lane = 1.22
    znear, zfar = 0.35, 260
    for k in range(-5, 6):
        X = (k + 0.5) * lane
        mine = k in (-1, 0)
        col = VOLT if mine else WHITE
        wline = 0.06
        pts = [proj(X - wline, znear), proj(X + wline, znear), proj(X + wline, zfar), proj(X - wline, zfar)]
        pth = skia.Path(); pth.addPoly([skia.Point(*q) for q in pts], True)
        c.drawPath(pth, paint(col, alpha=1.0 if mine else 0.85))
    # marcas de escalonado cada 4 m (lo que delata la velocidad)
    for i in range(0, 70):
        Zw = math.floor(z0 / 4) * 4 + i * 4
        Zr = Zw - z0
        if Zr < znear or Zr > 120:
            continue
        for k in range(-5, 5):
            X0 = (k + 0.5) * lane + 0.15
            X1 = X0 + 0.45
            pts = [proj(X0, Zr), proj(X1, Zr), proj(X1, Zr + 0.18), proj(X0, Zr + 0.18)]
            pth = skia.Path(); pth.addPoly([skia.Point(*q) for q in pts], True)
            c.drawPath(pth, paint(WHITE, alpha=0.55))
    # bandas de meta: llegan a cámara exactamente en cada palmada
    for tc in TRACK_CLAPS:
        Zb = cam_z(tc) + 0.42
        Zr = Zb - z0
        if znear * 0.5 < Zr < 200:
            pts = [proj(-7, Zr), proj(7, Zr), proj(7, Zr + 0.55), proj(-7, Zr + 0.55)]
            pth = skia.Path(); pth.addPoly([skia.Point(*q) for q in pts], True)
            c.drawPath(pth, paint(WHITE))
    c.restore()
    fl = sum(env(t, k, 0.07) for k in TRACK_CLAPS)
    if fl > 0.01:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(WHITE, alpha=min(0.5, 0.5 * fl)))


# --- ESCENA 5: bote (6.4 – 8.0 s) ------------------------------------------
LANDS = [(T(64), 190.0), (T(70), 470.0), (T(74), 730.0)]
GROUND = 1460.0
BALL_R = 74.0
G = 2 * 760 / (0.3 ** 2)


def ball_state(t):
    """Posición, velocidad y escala de la pelota. Botes = bombos."""
    for i, (tl, xl) in enumerate(LANDS):
        if i + 1 < len(LANDS):
            tn, xn = LANDS[i + 1]
        else:
            tn, xn = T(80), 900.0
        if tl <= t < tn or (i == len(LANDS) - 1 and t >= tl):
            d = tn - tl
            u = t - tl
            vy0 = G * d / 2
            y = GROUND - BALL_R - (vy0 * u - G * u * u / 2)
            vx = (xn - xl) / d
            x = xl + vx * u
            vy = -(vy0 - G * u)
            return x, y, vx, vy, tl
    return LANDS[0][1], GROUND - BALL_R, 0, 0, LANDS[0][0]


def scene_bounce(c, t):
    flip = any(T(s) <= t < T(s + 2) for s in (68, 76))
    bg, fg = (BLACK, VOLT) if flip else (VOLT, BLACK)
    c.clear(bg)
    shake(c, t, [(tl, 0.35) for tl, _ in LANDS], amp=12)
    zoom_u = in_expo((t - T(76)) / (T(80) - T(76)))
    x, y, vx, vy, tl = ball_state(t)
    # zoom final: la pelota viene a cámara y tapa el cuadro
    zs = 1 + 34 * zoom_u
    c.save()
    c.translate(x, y); c.scale(zs, zs); c.translate(-x, -y)
    # suelo
    c.drawRect(skia.Rect.MakeLTRB(-2000, GROUND, W + 2000, GROUND + 10), paint(fg))
    # estela: trayectoria ya recorrida
    trail = skia.Path()
    first = True
    tt0 = LANDS[0][0]
    n = 90
    for k in range(n + 1):
        tk = tt0 + (t - tt0) * k / n
        bx, by, *_ = ball_state(tk)
        if first:
            trail.moveTo(bx, by); first = False
        else:
            trail.lineTo(bx, by)
    tp = paint(fg, style="stroke", sw=5)
    tp.setPathEffect(skia.DashPathEffect.Make([2, 16], 0))
    tp.setStrokeCap(skia.Paint.kRound_Cap)
    c.drawPath(trail, tp)
    # sombra
    hgt = GROUND - BALL_R - y
    sh = clamp(1 - hgt / 900)
    c.drawOval(skia.Rect.MakeXYWH(x - BALL_R * 1.1 * sh, GROUND - 6, 2.2 * BALL_R * sh, 12),
               paint(fg, alpha=0.25 * sh))
    # squash & stretch
    squash = env(t, tl, 0.055)
    speed = math.hypot(vx, vy)
    st_ = 1 + 0.28 * clamp(speed / 3200) * (1 - squash)
    ang = math.degrees(math.atan2(vy, vx)) if speed > 1 else 0
    c.save()
    c.translate(x, y + BALL_R * 0.4 * squash)
    if squash > 0.02:
        c.scale(1 + 0.5 * squash, 1 - 0.4 * squash)
    else:
        c.rotate(ang); c.scale(st_, 1 / st_)
    c.drawCircle(0, 0, BALL_R, paint(fg))
    c.restore()
    c.restore()


# --- ESCENA 6: subida (8.0 – 9.4 s) ----------------------------------------
BUILD_CUTS = [80, 82, 84, 86, 88, 89, 90, 91, 92, 93]


def scene_build(idx):
    s0 = BUILD_CUTS[idx]

    def f(c, t):
        t0 = T(s0)
        u = t - t0
        punch = 1 + 0.12 * env(t, t0, 0.08)
        kind = idx if idx < 4 else 4
        if kind == 0:   # rejilla de swooshes girando
            c.clear(BLACK)
            rot = -25 + 220 * out_cubic(u / 0.2) * 0.2 + 90 * u
            for r in range(7):
                for q in range(3):
                    m = swoosh_matrix(180 + q * 360, 160 + r * 270, 260 * punch, rot + (r + q) * 0)
                    draw_swoosh(c, m, paint(WHITE))
        elif kind == 1:  # swoosh gigante recortado
            c.clear(VOLT)
            m = swoosh_matrix(CX - 40, CY + 80, 2600 * punch, -30 + 140 * u)
            draw_swoosh(c, m, paint(BLACK))
        elif kind == 2:  # columna que sube
            c.clear(BLACK)
            off = (u * 2600) % 300
            for r in range(-1, 9):
                m = swoosh_matrix(CX, r * 300 - off + 120, 860 * punch, 0)
                draw_swoosh(c, m, paint(VOLT if r % 2 else WHITE))
        elif kind == 3:  # swoosh blanco a toda velocidad
            c.clear(BLACK)
            m = swoosh_matrix(CX, CY, 1000 * punch, -720 * u - 20)
            draw_swoosh(c, m, paint(WHITE))
        else:            # túnel de swooshes, cada semicorchea más cerca
            k = idx - 4
            inv = k % 2 == 1
            c.clear(VOLT if inv else BLACK)
            base = 1.0 + 0.55 * k + 2.2 * u
            rot0 = 15 * k + 60 * u
            for j in range(14, -1, -1):
                sc = 140 * base * (1.42 ** j) / 1.42 ** 4
                if sc > 9000 or sc < 4:
                    continue
                col = (BLACK if j % 2 else WHITE) if inv else (WHITE if j % 2 else VOLT)
                if inv and j % 2 == 0:
                    col = WHITE
                m = swoosh_matrix(CX, CY + 120, sc, rot0 + j * 9, anchor=(5.0, 14.6))
                draw_swoosh(c, m, paint(col))
    return f


# --- ESCENA 7: tagline (9.6 – 11.2 s) ---------------------------------------
TAG_LINES = [("JUST", 96), ("DO", 100), ("IT.", 104)]


def tag_layout():
    _, wj, _ = word("JUST")
    cap = COLW / wj
    gap = 0.12 * cap
    total = 3 * cap + 2 * gap
    top = CY - total / 2
    return cap, gap, top


def scene_tag(c, t):
    c.clear(BLACK)
    hits = [(T(s), 1.3) for _, s in TAG_LINES]
    shake(c, t, hits, amp=30, tau=0.1, rot=1.6)
    cap, gap, top = tag_layout()
    # wind-up antes del impacto final
    wind = in_cubic((t - T(109)) / (T(112) - T(109)))
    gs = 1 - 0.06 * wind
    c.translate(CX, CY); c.scale(gs, gs); c.translate(-CX, -CY)
    for i, (txt, s) in enumerate(TAG_LINES):
        t0 = T(s)
        if t < t0:
            continue
        u = (t - t0) / 0.13
        sc = 1 + 0.9 * (1 - out_expo(u))
        yb = top + cap * (i + 1) + gap * i
        c.save()
        cx_, cy_ = LEFT + COLW / 2, yb - cap / 2
        c.translate(cx_, cy_); c.scale(sc, sc); c.translate(-cx_, -cy_)
        if txt == "IT.":
            path, w, info = word("IT")
            draw_word(c, "IT", LEFT, yb, cap, paint(WHITE))
            # el punto es el corazón del principio
            r0 = font.WV * 0.62 * cap
            dotx = LEFT + (w + font.TRACK + font.KERN.get("T.", 0)) * cap + r0
            puls = heart_pulse(t, [T(108)])
            for d, a0 in ((0.0, 0.5), (T(2), 0.25)):
                uu = (t - T(108) - d) / 0.9
                if 0 <= uu <= 1:
                    c.drawCircle(dotx, yb - r0, r0 + 900 * out_expo(uu),
                                 paint(WHITE, alpha=a0 * (1 - uu) ** 2, style="stroke", sw=6 * (1 - uu) + 1))
            c.drawCircle(dotx, yb - r0, r0 * (1 + 0.55 * puls), paint(WHITE))
        else:
            draw_word(c, txt, LEFT, yb, cap, paint(WHITE))
        c.restore()


# --- ESCENA 8: firma (11.2 – 15.0 s) ----------------------------------------
END_W = 820.0


def scene_end(c, t):
    c.clear(BLACK)
    u = t - T(FINAL)
    shake(c, t, [(T(FINAL), 1.0)], amp=22, tau=0.14)
    push = 1 + 0.035 * out_cubic(u / (DUR - T(FINAL)))
    c.translate(CX, CY); c.scale(push, push); c.translate(-CX, -CY)
    reveal = out_expo(u / 0.13)
    settle = spring(u / 1.0, freq=2.2, damp=6.0)
    sc = 1.18 - 0.18 * settle
    rot = -8 * (1 - settle)
    m = swoosh_matrix(CX, CY - 40, END_W * sc, rot)
    draw_swoosh(c, m, paint(WHITE), reveal=reveal)
    # onda expansiva + flash del impacto
    uu = u / 0.7
    if 0 <= uu <= 1:
        c.drawCircle(CX, CY - 40, 60 + 1400 * out_expo(uu),
                     paint(WHITE, alpha=0.6 * (1 - uu) ** 2, style="stroke", sw=30 * (1 - uu) + 2))
    fl = env(t, T(FINAL), 0.028)
    if fl > 0.01:
        c.drawRect(skia.Rect.MakeLTRB(-200, -200, W + 200, H + 200), paint(WHITE, alpha=min(1.0, 1.0 * fl)))
    # tagline: cada letra sube desde una máscara, escalonada
    tl = T(LOCK)
    if t >= tl - 0.2:
        cap = 74.0
        path, w, info = word("JUST DO IT.")
        x0 = CX - w * cap / 2
        yb = CY + 300
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(0, yb - cap - 6, W, yb + 6))
        for k, (ch, x, gw) in enumerate(info):
            v = out_expo((t - tl - k * 0.025) / 0.35)
            g, _ = font.glyph(ch)
            c.save()
            c.translate(x0 + x * cap, yb + (1 - v) * cap * 1.15)
            c.scale(cap, cap)
            c.drawPath(g, paint(WHITE))
            c.restore()
        c.restore()


# --- Montaje (edición) ------------------------------------------------------
def build_edl():
    edl = [(0, scene_heart)]
    for i, (s, _) in enumerate(WORDS):
        edl.append((s, scene_excuse(i)))
    edl.append((GAP_PRE_DROP, scene_black))
    edl.append((DROP, scene_slice))
    edl.append((44, scene_track))
    edl.append((64, scene_bounce))
    for i, s in enumerate(BUILD_CUTS):
        edl.append((s, scene_build(i)))
    edl.append((GAP_PRE_TAG, scene_black))
    edl.append((96, scene_tag))
    edl.append((FINAL, scene_end))
    return [(fr(s), f) for s, f in edl]


EDL = build_edl()
CUT_FRAMES = [f for f, _ in EDL]
IMPACTS = [T(DROP), T(96), T(100), T(104), T(FINAL)]


def shot_for_frame(fi):
    cur = EDL[0][1]
    for f0, fn in EDL:
        if fi >= f0:
            cur = fn
    return cur


# --- Render ----------------------------------------------------------------
LUT_LIN = ((np.arange(256) / 255.0) ** 2.2).astype(np.float32)
_q = np.arange(4096) / 4095.0
LUT_SRGB = np.clip(np.round(255 * _q ** (1 / 2.2)), 0, 255).astype(np.uint8)
_surface = None


def render_frame(fi, samples=SAMPLES):
    global _surface
    if _surface is None:
        _surface = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    scene = shot_for_frame(fi)
    acc = np.zeros((H, W, 3), np.float32)
    t0 = fi / FPS
    for k in range(samples):
        t = t0 + (k + 0.5) / samples * SHUTTER / FPS
        c = _surface.getCanvas()
        c.save()
        scene(c, t)
        c.restore()
        arr = _surface.makeImageSnapshot().toarray()[:, :, :3]
        acc += LUT_LIN[arr]
    acc /= samples
    # aberración cromática en los impactos (en luz lineal, antes de cuantizar)
    tc = t0 + 0.5 * SHUTTER / FPS
    ab = sum(env(tc, h, 0.06) for h in IMPACTS)
    shift = int(round(14 * min(ab, 1.2)))
    if shift > 0:
        r = acc[:, :, 0].copy(); b = acc[:, :, 2].copy()
        acc[:, shift:, 0] = r[:, :-shift]; acc[:, :shift, 0] = r[:, :1]
        acc[:, :-shift, 2] = b[:, shift:]; acc[:, -shift:, 2] = b[:, -1:]
    out = LUT_SRGB[np.clip(acc * 4095 + 0.5, 0, 4095).astype(np.int32)]
    # grano fino (también dithering contra el banding)
    rng = np.random.default_rng(fi)
    g = rng.normal(0, 2.2, (H, W, 1)).astype(np.float32)
    out = np.clip(out.astype(np.float32) + g, 0, 255).astype(np.uint8)
    return out


def _work(fi):
    return fi, render_frame(fi).tobytes()


if __name__ == "__main__":
    import subprocess
    from multiprocessing import Pool
    audio = sys.argv[1]
    out = sys.argv[2]
    frames = range(NFRAMES)
    if len(sys.argv) > 3:
        a, b = map(int, sys.argv[3].split(":"))
        frames = range(a, b)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", audio,
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.2",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-x264-params", "keyint=60:min-keyint=1",
           "-c:a", "aac", "-b:a", "320k", "-ar", str(SR),
           "-t", str(DUR), "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for n, (fi, buf) in enumerate(pool.imap(_work, frames, chunksize=2)):
            p.stdin.write(buf)
            if n % 60 == 0:
                print("frame", fi, flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)
