"""
Genera reporte_auditoria.html (reporte visual de la auditoria) a partir de
auditoria_datos.json y secuencia_de_armado.md. Todos los diagramas se dibujan a
escala desde los datos calculados, no a mano.

Corre: `python3 auditoria_independiente.py && python3 reporte_visual.py`
"""

import html
import json
import sys
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "auditoria_datos.json"), encoding="utf-8"))
# numeracion de taller: la del modelo original (la misma de secuencia_de_armado.md). La
# auditoria describe el domo tal como se publico, sin puerta, asi que la secuencia se
# calcula aqui sobre el domo cerrado en vez de leer el .md (que ahora trae la puerta).
sys.path.insert(0, os.path.join(HERE, ".."))
import dome_build_sequence as _seq  # noqa: E402
from dome_model import build_dome as _build_dome  # noqa: E402
_DOME = _build_dome()
_STEPS, _ = _seq.build_sequence(_DOME)
REPO = "https://github.com/luiscruces-dev/Claude/tree/claude/google-chica-glamping-review-veyz64/glamping-cucuchica"


def f(x, n=1):
    return f"{x:.{n}f}"


def esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------------ E1 discos

def hub_disc(name, size=210):
    h = D["hubs"][name]
    cx, cy = size/2, size/2 + 10
    R = size*0.40
    out = [f'<svg viewBox="0 0 {size} {size+20}" role="img" aria-label="Disco del nodo {name}: ángulos publicados contra azimuts correctos">']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R+6}" class="disc"/>')

    def ray(deg, cls, r=R, tip=""):
        a = math.radians(deg - 90)
        x, y = cx + r*math.cos(a), cy + r*math.sin(a)
        t = f' data-tip="{esc(tip)}"' if tip else ""
        return f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(x)}" y2="{f(y)}" class="{cls}"{t}/>'

    cum_pub, cum_ok = [0.0], [0.0]
    for a in h["ang3d"][:-1]:
        cum_pub.append(cum_pub[-1] + a)
    for a in h["az"][:-1]:
        cum_ok.append(cum_ok[-1] + a)
    gap = 360 - sum(h["ang3d"])
    # cuña del hueco que deja el angulo 3D
    a0 = math.radians(sum(h["ang3d"]) - 90); a1 = math.radians(360 - 90)
    rw = R*0.62
    out.append(f'<path d="M {f(cx)} {f(cy)} L {f(cx+rw*math.cos(a0))} {f(cy+rw*math.sin(a0))} '
               f'A {f(rw)} {f(rw)} 0 0 1 {f(cx+rw*math.cos(a1))} {f(cy+rw*math.sin(a1))} Z" class="gapwedge" '
               f'data-tip="Hueco que deja marcar el ángulo 3D: {f(gap, 2)}°"/>')
    for i, d in enumerate(cum_ok):
        out.append(ray(d, "ray-ok", tip=f"Correcto: pestaña {i+1} a {f(d, 2)}° (azimut)"))
    for i, d in enumerate(cum_pub):
        out.append(ray(d, "ray-bad", r=R*0.93, tip=f"Publicado: pestaña {i+1} a {f(d, 2)}° (ángulo 3D acumulado)"))
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="3.5" class="hubdot"/>')
    out.append(f'<text x="{f(cx)}" y="{f(cy - R - 14)}" class="lbl-crit" text-anchor="middle">faltan {f(gap, 2)}°</text>')
    out.append("</svg>")
    return "\n".join(out)


def hub_table():
    rows = []
    for n in ["H1", "H2", "H3", "H4", "H5"]:
        h = D["hubs"][n]
        pairs = sorted({(round(a, 2), round(z, 2)) for a, z in zip(h["ang3d"], h["az"])})
        pub = " / ".join(f"{a:.2f}°" for a, _ in pairs)
        ok = " / ".join(f"{z:.2f}°" for _, z in pairs)
        err = " / ".join(f"+{z-a:.2f}°" for a, z in pairs)
        tilt = " / ".join(sorted({f"{t:.2f}°" for t in h["tilts"]}))
        rows.append(f"<tr><td><b>{n}</b> <span class='muted'>×{h['count']}</span></td><td class='num bad'>{pub}</td>"
                    f"<td class='num ok'><b>{ok}</b></td><td class='num'>{err}</td><td class='num'>{tilt}</td></tr>")
    return "\n".join(rows)


# ------------------------------------------------------------------ E2 choque de tubos

def clash_svg():
    theta = D["setback"]["min_angle"]
    r = 16.0
    s = 2.4      # px por mm
    W, H = 440, 350
    ox, oy = 20 + 65*s, H/2
    half = math.radians(theta/2)
    axes = [(math.cos(half), -math.sin(half)), (math.cos(half), math.sin(half))]

    def P(x, y):
        return (ox + x*s, oy + y*s)

    def strip(ax, L0, L1):
        ux, uy = ax; nx, ny = -uy, ux
        pts = [(ux*L0 + nx*r, uy*L0 + ny*r), (ux*L1 + nx*r, uy*L1 + ny*r),
               (ux*L1 - nx*r, uy*L1 - ny*r), (ux*L0 - nx*r, uy*L0 - ny*r)]
        return pts

    def clip(poly, ax, sign_offset):
        # recorta poly al semiplano del strip (|dist a eje| <= r) y along >= 0
        ux, uy = ax; nx, ny = -uy, ux
        def half_plane(pts, fn):
            out = []
            for i in range(len(pts)):
                a, b = pts[i], pts[(i+1) % len(pts)]
                fa, fb = fn(a), fn(b)
                if fa >= 0: out.append(a)
                if (fa >= 0) != (fb >= 0):
                    t = fa/(fa-fb)
                    out.append((a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1])))
            return out
        p = half_plane(poly, lambda q: r - (q[0]*nx + q[1]*ny))
        p = half_plane(p, lambda q: r + (q[0]*nx + q[1]*ny))
        p = half_plane(p, lambda q: q[0]*ux + q[1]*uy)
        return p

    L = 100
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Dos tubos de 32 mm que llegan a un nodo formando {theta:.2f} grados">']
    for ax in axes:
        pts = " ".join(f"{f(P(*q)[0])},{f(P(*q)[1])}" for q in strip(ax, 0, L))
        out.append(f'<polygon points="{pts}" class="tube"/>')
    lens = clip(strip(axes[0], 0, L), axes[1], 1)
    pts = " ".join(f"{f(P(*q)[0])},{f(P(*q)[1])}" for q in lens)
    out.append(f'<polygon points="{pts}" class="clash" data-tip="Zona donde los dos tubos ocupan el mismo espacio"/>')
    for ax in axes:
        x2, y2 = P(ax[0]*L, ax[1]*L)
        out.append(f'<line x1="{ox}" y1="{oy}" x2="{f(x2)}" y2="{f(y2)}" class="axis-line"/>')
    # marcas: rango del .md (1–3 cm) bajo el eje inferior; minimo real y borde
    # del disco sobre el eje superior, para que no se monten las etiquetas
    marks = [(axes[1], 10, "1 cm", "bad"), (axes[1], 30, "3 cm", "bad"),
             (axes[0], D["setback"]["min_setback_cm"]*10, f"{D['setback']['min_setback_cm']:.1f} cm", "ink"), (axes[0], 65, "6.5 cm", "ink")]
    for ax, mm, lab, cls in marks:
        ux, uy = ax
        nx, ny = (-uy, ux) if ax is axes[1] else (uy, -ux)
        a = P(ux*mm + nx*(r+4), uy*mm + ny*(r+4)); b = P(ux*mm + nx*(r+18), uy*mm + ny*(r+18))
        out.append(f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" class="tick-{cls}"/>')
        t = P(ux*mm + nx*(r+26), uy*mm + ny*(r+26))
        out.append(f'<text x="{f(t[0])}" y="{f(t[1]+4)}" text-anchor="middle" class="lbl-{"crit" if cls == "bad" else "ink"}">{lab}</text>')
    # disco de 13 cm (solo el arco)
    out.append(f'<circle cx="{ox}" cy="{oy}" r="{f(65*s)}" class="disc-edge"/>')
    out.append(f'<circle cx="{ox}" cy="{oy}" r="3.5" class="hubdot"/>')
    out.append(f'<text x="{ox-6}" y="{oy+4}" text-anchor="end" class="lbl-ink">nodo</text>')
    tt = P(axes[1][0]*100, axes[1][1]*100)
    out.append(f'<text x="{f(tt[0])}" y="{f(tt[1]+40)}" class="lbl-muted" text-anchor="end">tubo ⌀32 mm</text>')
    out.append(f'<text x="{f(ox - 70)}" y="{f(oy - 92)}" class="lbl-muted" text-anchor="middle">borde del disco</text>')
    out.append(f'<text x="{f(ox - 70)}" y="{f(oy - 78)}" class="lbl-muted" text-anchor="middle">⌀13 cm</text>')
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ E3 alturas

def heights_svg():
    R = D["geometry"]["R"]; z0 = D["z0"]
    s = 72
    W, H = 560, 300
    ox, oy = W/2 + 10, H - 34
    P = D["mesh"]["P"]
    def X(r): return ox + r*s
    def Y(h): return oy - h*s
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Corte del domo con las alturas de armado publicadas y las reales">']
    # grilla horizontal cada 0.5 m
    for k in range(0, 7):
        hh = k*0.5
        out.append(f'<line x1="{X(-3.2)}" y1="{f(Y(hh))}" x2="{X(3.35)}" y2="{f(Y(hh))}" class="grid"/>')
        out.append(f'<text x="{X(-3.25)}" y="{f(Y(hh)+4)}" text-anchor="end" class="lbl-muted tab">{hh:.1f} m</text>')
    pts = []
    for i in range(0, 121):
        r = -3 + 6*i/120
        pts.append(f"{f(X(r))},{f(Y(math.sqrt(R*R - r*r) - z0))}")
    out.append(f'<polyline points="{" ".join(pts)}" class="dome-line"/>')
    out.append(f'<line x1="{X(-3.2)}" y1="{Y(0)}" x2="{X(3.35)}" y2="{Y(0)}" class="floor"/>')
    out.append(f'<text x="{X(-3)}" y="{Y(0)+18}" class="lbl-muted">piso (nodos bajos)</text>')
    for ring in D["erection"]:
        v = ring["nodes"][0]["node"]
        rho = math.hypot(P[v][0], P[v][1])
        real = ring["z_floor_m"]; pub = ring["z_center_m"]
        x = X(rho) if rho > 0.05 else X(0)
        out.append(f'<line x1="{f(x)}" y1="{f(Y(real))}" x2="{f(x)}" y2="{f(Y(pub))}" class="connector"/>')
        out.append(f'<circle cx="{f(x)}" cy="{f(Y(pub))}" r="5" class="pt-bad" data-tip="Paso {ring["ring"]}: el .md decía {pub:.3f} m"/>')
        out.append(f'<circle cx="{f(x)}" cy="{f(Y(real))}" r="5" class="pt-ok" data-tip="Paso {ring["ring"]}: altura real {real:.3f} m sobre el piso"/>')
        out.append(f'<text x="{f(x + 9)}" y="{f(Y(pub) + 4)}" class="lbl-ink tab">P{ring["ring"]}</text>')
    out.append("</svg>")
    return "\n".join(out)


def heights_rows():
    return "\n".join(f"<tr><td>Paso {r['ring']}</td><td class='num bad'>{r['z_center_m']:.3f} m</td>"
                     f"<td class='num ok'><b>{r['z_floor_m']:.3f} m</b></td></tr>" for r in D["erection"])


# ------------------------------------------------------------------ E4/E5 planta

def parse_anchors():
    rows = []
    for r in _seq.setting_out(_DOME):
        rows.append(dict(r, type=_seq.hub_type_of(_DOME, r["node"])))
    return rows


def parse_step1():
    step = _STEPS[1]
    sup = {}
    for e in step["edges"]:
        new = e["a"] if e["a"] in step["new_hubs"] else e["b"]
        sup.setdefault(new, []).append(e["b"] if new == e["a"] else e["a"])
    return sup


def plan_svg(anchors, step1):
    s = 44
    W = H = 360
    cx, cy = W/2, H/2
    byid = {a["node"]: a for a in anchors}
    def XY(x, y): return (cx + x*s, cy - y*s)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Planta de los 15 anclajes y de los 5 nodos que quedan como bisagra en el paso 1">']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{3*s}" class="ring-guide"/>')
    out.append(f'<line x1="{cx}" y1="{cy}" x2="{f(cx + 3.6*s)}" y2="{cy}" class="grid"/>')
    out.append(f'<text x="{f(cx + 3.62*s)}" y="{cy - 14}" class="lbl-muted" text-anchor="end">0°</text>')
    poly = " ".join(f"{f(XY(a['x'], a['y'])[0])},{f(XY(a['x'], a['y'])[1])}" for a in anchors)
    out.append(f'<polygon points="{poly}" class="ring-poly"/>')
    rho1 = [r for r in D["erection"] if r["ring"] == 1][0]
    P = D["mesh"]["P"]; v = rho1["nodes"][0]["node"]
    rho = math.hypot(P[v][0], P[v][1])
    for h3, sups in step1.items():
        a, b = byid[sups[0]], byid[sups[1]]
        ang = math.atan2(a["y"] + b["y"], a["x"] + b["x"])
        hx, hy = rho*math.cos(ang), rho*math.sin(ang)
        pa, pb, ph = XY(a["x"], a["y"]), XY(b["x"], b["y"]), XY(hx, hy)
        out.append(f'<polygon points="{f(pa[0])},{f(pa[1])} {f(pb[0])},{f(pb[1])} {f(ph[0])},{f(ph[1])}" class="flap" '
                   f'data-tip="Nodo #{h3} (H3): sostenido solo por #{sups[0]} y #{sups[1]} — gira sobre esa línea hasta el paso 2"/>')
        out.append(f'<line x1="{f(pa[0])}" y1="{f(pa[1])}" x2="{f(pb[0])}" y2="{f(pb[1])}" class="hinge"/>')
        out.append(f'<circle cx="{f(ph[0])}" cy="{f(ph[1])}" r="5" class="pt-crit"/>')
        tx, ty = XY(hx*0.78, hy*0.78)
        out.append(f'<text x="{f(tx)}" y="{f(ty+4)}" class="lbl-crit" text-anchor="middle">#{h3}</text>')
    for a in anchors:
        x, y = XY(a["x"], a["y"])
        high = a["type"] == "H5"
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{6 if high else 4.5}" class="{"anc-high" if high else "anc-low"}" '
                   f'data-tip="#{a["node"]} {a["type"]} · azimut {a["az"]:.3f}° · radio {a["r"]:.4f} m · X {a["x"]:+.4f} · Y {a["y"]:+.4f}"/>')
        lx, ly = XY(a["x"]*1.13, a["y"]*1.13)
        out.append(f'<text x="{f(lx)}" y="{f(ly+4)}" text-anchor="middle" class="lbl-ink tab">#{a["node"]}</text>')
    out.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" class="lbl-muted">⌀ 6.00 m</text>')
    out.append("</svg>")
    return "\n".join(out)


def anchor_rows(anchors):
    return "\n".join(
        f"<tr><td class='num'>#{a['node']}</td><td>{a['type']}</td><td class='num'>{a['az']:.3f}°</td><td class='num'>{a['r']:.4f}</td>"
        f"<td class='num'>{a['x']:+.4f}</td><td class='num'>{a['y']:+.4f}</td><td class='num'>{a['dz']*100:+.2f} cm</td></tr>"
        for a in anchors)


# ------------------------------------------------------------------ E6 membrana

def membrane_svg():
    rows = D["membrane"]["allowances"]
    budget = D["membrane"]["budget_m2"]
    W, H = 920, 210
    x0, x1 = 170, 860
    vmax = 70
    def X(v): return x0 + (x1 - x0)*v/vmax
    bh, gap, top = 22, 12, 28
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Área de membrana necesaria según el solape, contra lo presupuestado">']
    for v in range(0, vmax + 1, 10):
        out.append(f'<line x1="{f(X(v))}" y1="{top-6}" x2="{f(X(v))}" y2="{top + 4*(bh+gap)}" class="grid"/>')
        out.append(f'<text x="{f(X(v))}" y="{top + 4*(bh+gap) + 14}" text-anchor="middle" class="lbl-muted tab">{v}</text>')
    # banda recomendada
    out.append(f'<rect x="{f(X(60))}" y="{top-6}" width="{f(X(67)-X(60))}" height="{4*(bh+gap)+6}" class="band" '
               f'data-tip="Rango recomendado para presupuestar: 60–67 m²"/>')
    for i, r in enumerate(rows):
        y = top + i*(bh+gap)
        out.append(f'<text x="{x0-10}" y="{y+bh/2+4}" text-anchor="end" class="lbl-ink">Solape {r["allow_cm"]:.0f} cm/lado</text>')
        out.append(f'<path d="M {x0} {y} H {f(X(r["m2"])-4)} a 4 4 0 0 1 4 4 V {y+bh-4} a 4 4 0 0 1 -4 4 H {x0} Z" class="bar-seq" '
                   f'data-tip="Solape {r["allow_cm"]:.0f} cm por lado: {r["m2"]:.1f} m² de piezas ({r["vs_budget"]*100:.0f}% de lo presupuestado)"/>')
        out.append(f'<text x="{f(X(r["m2"])+6)}" y="{y+bh/2+4}" class="lbl-ink tab">{r["m2"]:.1f} m²</text>')
    out.append(f'<line x1="{f(X(budget))}" y1="{top-10}" x2="{f(X(budget))}" y2="{top + 4*(bh+gap)}" class="ref-bad"/>')
    out.append(f'<text x="{f(X(budget)-6)}" y="{top-12}" text-anchor="end" class="lbl-crit">✕ comprado según el .md: {budget:.1f} m²</text>')
    out.append(f'<text x="{f(X(60)+4)}" y="{top-12}" class="lbl-ink">✓ presupuestar 60–67 m²</text>')
    out.append(f'<text x="{x1}" y="{H-4}" text-anchor="end" class="lbl-muted">m² de tela en piezas cortadas, sin desperdicio de rollo</text>')
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ E7 viento por anclaje

def wind_data():
    P = D["mesh"]["P"]
    a = D["truss"]["Viento: Cp barlovento +0.6 / cresta -1.1 / sotavento -0.4"]["reactions"]
    b = D["truss"]["Id. + presion interna +0.55 (puerta abierta a barlovento)"]["reactions"]
    rows = []
    for v in a:
        x, y = P[int(v)][0], P[int(v)][1]
        ang = (math.degrees(math.atan2(y, x)) - 180) % 360   # 0 = barlovento (viento hacia +x)
        rows.append({"ang": ang, "up_a": -a[v][2], "up_b": -b[v][2], "sh_b": math.hypot(b[v][0], b[v][1])})
    rows.sort(key=lambda r: r["ang"])
    return rows


def wind_svg(rows, key_list, ref, ref_label, vmax, title, unit="kgf"):
    W, H = 480, 230
    x0, x1, top, base = 40, 470, 22, 190
    n = len(rows)
    slot = (x1 - x0)/n
    def Y(v): return base - (base - top)*v/vmax
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    step = 50 if vmax > 100 else 20
    for v in range(0, vmax + 1, step):
        out.append(f'<line x1="{x0}" y1="{f(Y(v))}" x2="{x1}" y2="{f(Y(v))}" class="grid"/>')
        out.append(f'<text x="{x0-6}" y="{f(Y(v)+4)}" text-anchor="end" class="lbl-muted tab">{v}</text>')
    nk = len(key_list)
    bw = min(12, (slot - 6)/nk)
    for i, r in enumerate(rows):
        cxs = x0 + slot*(i + 0.5)
        for k, (key, cls, lab) in enumerate(key_list):
            v = max(0.0, r[key])
            bx = cxs - nk*bw/2 - (nk-1) + k*(bw + 2)
            yv = Y(v)
            hgt = base - yv
            rr = min(4, hgt/2, bw/2)
            out.append(f'<path d="M {f(bx)} {base} V {f(yv+rr)} a {f(rr)} {f(rr)} 0 0 1 {f(rr)} {f(-rr)} H {f(bx+bw-rr)} a {f(rr)} {f(rr)} 0 0 1 {f(rr)} {f(rr)} V {base} Z" '
                       f'class="{cls}" data-tip="Anclaje a {r["ang"]:.0f}° del barlovento · {lab}: {v:.1f} {unit}"/>')
        if i % 1 == 0:
            out.append(f'<text x="{f(cxs)}" y="{base+14}" text-anchor="middle" class="lbl-muted tab small">{r["ang"]:.0f}°</text>')
    out.append(f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" class="baseline"/>')
    out.append(f'<line x1="{x0}" y1="{f(Y(ref))}" x2="{x1}" y2="{f(Y(ref))}" class="ref-bad"/>')
    out.append(f'<text x="{x0+4}" y="{f(Y(ref)-6)}" class="lbl-crit halo">{esc(ref_label)}</text>')
    out.append(f'<text x="{x0}" y="{H-6}" class="lbl-muted">grados desde barlovento (0° = de frente al viento)</text>')
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ E8 corte

def bar_row(pieces, lengths, label, note, cls_note, stock=6.0):
    W = 600
    x0, x1 = 0, 600
    s = (x1 - x0)/stock
    out = [f'<svg viewBox="0 0 {W} 30" class="cutbar" role="img" aria-label="{esc(label)}">']
    out.append(f'<rect x="0" y="4" width="{W}" height="22" rx="4" class="stock"/>')
    x = 0.0
    for p in pieces:
        w = lengths[p]*s
        out.append(f'<rect x="{f(x)}" y="4" width="{f(max(0, w-2))}" height="22" rx="3" class="seg-{p}" data-tip="Pieza {p}: {lengths[p]*100:.2f} cm"/>')
        out.append(f'<text x="{f(x + w/2)}" y="19" text-anchor="middle" class="seglbl">{p} · {lengths[p]*100:.1f}</text>')
        x += w + 0.003*s
    out.append("</svg>")
    return (f'<div class="cutrow"><div class="cutlabel">{label}</div>{"".join(out)}'
            f'<div class="cutnote {cls_note}">{note}</div></div>')


def cut_section():
    S = D["geometry"]["struts"]
    Lc = {k: S[k]["L_cm"]/100 for k in "ABC"}
    rows = []
    slack = D["cutting"]["6"]["tight_slack_mm"]
    rows.append(bar_row(list("BBBBC"), Lc, "✕ Publicado · 9 barras así", f"sobran {slack:.1f} mm", "bad"))
    rc = [r for r in D["cutting"]["6"]["real_cut"] if abs(r["setback_cm"] - 3.5) < 1e-6][0]
    Lr = {k: Lc[k] - 0.07 for k in "ABC"}
    for p in rc["patterns"]:
        pcs = [k for k in "ABC" for _ in range(p["pieces"][k])]
        used = sum(Lr[k] + 0.003 for k in pcs)
        rows.append(bar_row(pcs, Lr, f"✓ Corregido · {p['count']} barras así", f"sobran {(6-used)*1000:.0f} mm", "ok"))
    return "\n".join(rows), rc


# ------------------------------------------------------------------ altura libre

def headroom_svg():
    R = D["geometry"]["R"]; z0 = D["z0"]
    s = 72
    W, H = 520, 250
    ox, oy = W/2, H - 30
    def X(r): return ox + r*s
    def Y(h): return oy - h*s
    rr = [x for x in D["headroom"] if abs(x["h"] - 2.0) < 1e-9][0]["r"]
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Corte del domo: zona con 2 m de altura libre y una puerta de 2 m">']
    pts = [f"{f(X(-rr))},{f(Y(0))}"]
    for i in range(0, 61):
        r = -rr + 2*rr*i/60
        pts.append(f"{f(X(r))},{f(Y(math.sqrt(R*R-r*r)-z0))}")
    pts.append(f"{f(X(rr))},{f(Y(0))}")
    out.append(f'<polygon points="{" ".join(pts)}" class="head-zone" data-tip="Solo aquí hay 2.0 m o más de altura: {rr*2:.2f} m de ancho, {math.pi*rr*rr:.1f} m² de piso"/>')
    dome = []
    for i in range(0, 121):
        r = -3 + 6*i/120
        dome.append(f"{f(X(r))},{f(Y(math.sqrt(R*R-r*r)-z0))}")
    out.append(f'<polyline points="{" ".join(dome)}" class="dome-line"/>')
    out.append(f'<line x1="{X(-3.3)}" y1="{Y(0)}" x2="{X(3.3)}" y2="{Y(0)}" class="floor"/>')
    out.append(f'<line x1="{X(-3.3)}" y1="{Y(2.0)}" x2="{X(3.3)}" y2="{Y(2.0)}" class="grid"/>')
    out.append(f'<text x="{X(-3.3)}" y="{f(Y(2.0)-5)}" class="lbl-muted">2.0 m</text>')
    # puerta 0.9 x 2.0 pegada a la pared derecha
    dx0, dx1 = 3.0 - 0.9, 3.0
    out.append(f'<rect x="{f(X(dx0))}" y="{f(Y(2.0))}" width="{f(0.9*s)}" height="{f(2.0*s)}" class="door" '
               f'data-tip="Puerta de 0.90 × 2.00 m junto a la pared: el domo la corta"/>')
    out.append(f'<text x="{f(X(dx0)+0.45*s)}" y="{f(Y(2.0)-6)}" text-anchor="middle" class="lbl-crit">✕ puerta 2.0 m</text>')
    out.append(f'<text x="{ox}" y="{f(Y(1.2))}" text-anchor="middle" class="lbl-ink">≥ 2.0 m: {math.pi*rr*rr:.1f} m² ({rr*rr/9*100:.0f}% del piso)</text>')
    out.append(f'<text x="{ox}" y="{f(Y(2.52)-8)}" text-anchor="middle" class="lbl-muted">ápice 2.52 m</text>')
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ pagina

def page():
    g = D["geometry"]
    anchors = parse_anchors(); step1 = parse_step1()
    assert len(anchors) == 15 and len(step1) == 5, (len(anchors), len(step1))
    cut_html, rc = cut_section()
    wrows = wind_data()
    tr = D["truss"]
    up_b = max(r["up_b"] for r in wrows); sh_b = max(r["sh_b"] for r in wrows)
    wind_up = wind_svg(wrows, [("up_a", "bar-o1", "sin presión interna"), ("up_b", "bar-o2", "con presión interna +0.55")],
                       73, "promedio usado en el .md: 73 kgf", 150, "Arranque por anclaje")
    wind_sh = wind_svg(wrows, [("sh_b", "bar-o2", "corte horizontal")], 22, "promedio usado en el .md: 22 kgf", 60,
                       "Corte horizontal por anclaje")
    hub_svgs = "".join(f'<figure class="disc-fig">{hub_disc(n)}<figcaption><b>{n}</b> · {D["hubs"][n]["count"]} nodos</figcaption></figure>'
                       for n in ["H1", "H2", "H3"])
    S = g["struts"]

    confirmed = [
        ("Radio de la esfera", "3.0452 m", f"{g['R']:.4f} m"),
        ("Altura del ápice", "2.5225 m", f"{g['apex']:.4f} m"),
        ("Barras A / B / C", "125.59 · 122.89 · 106.16 cm", " · ".join(f"{S[k]['L_cm']:.2f}" for k in "ABC") + " cm"),
        ("Cantidades A / B / C", "50 · 40 · 30", " · ".join(str(S[k]['n']) for k in "ABC")),
        ("Tubo total", "143.80 m", f"{g['tube']:.2f} m"),
        ("Nodos H1–H5", "20 · 5 · 6 · 10 · 5", " · ".join(str(g['hub_counts'][k]) for k in ['H1', 'H2', 'H3', 'H4', 'H5'])),
        ("Área de membrana", "46.24 m²", f"{g['membrane']:.2f} m²"),
        ("Desnivel del zigzag", "4.86 cm", "4.858 cm"),
        ("Peso del domo", "278 kg", f"{tr['Peso propio']['sum_vertical_kgf']:.1f} kg"),
        ("Empuje lateral de viento", "330 kgf", f"{tr['Viento: Cp barlovento +0.6 / cresta -1.1 / sotavento -0.4']['sum_horizontal_kgf']:.1f} kgf"),
        ("Barras en 12 m", "13 barras", f"{D['cutting']['12']['optimal']} barras (óptimo)"),
    ]
    conf_rows = "\n".join(f"<tr><td>{a}</td><td class='num'>{b}</td><td class='num ok'>{c}</td><td class='ok'>✓</td></tr>" for a, b, c in confirmed)

    missing = [
        ("good", "Resuelto", "Puerta", "Ya diseñada y verificada: portal con marco de 50×50 sobre dos anclajes existentes, techo de vestíbulo y vano libre de 117.9 × 207.5 cm (dome_door.py y §11 del documento). Sube el corte en los anclajes de los postes de 59 a 94 kgf: el perno sigue sobrando."),
        ("good", "Resuelto", "Plataforma y pilotes", "Ya diseñada y verificada (dome_platform.py): 23 pilotes con zapata, uno bajo cada anclaje, viga de anillo de concreto, vigas de acero y viguetas cada 40 cm para 200 kgf/m². El jacuzzi va afuera. Falta confirmar el suelo."),
        ("good", "Resuelto", "Arranque de pilotes", "Con la viga de anillo y un pilote bajo cada anclaje, el peso que sujeta cada anclaje es ≈5.9 veces el arranque del viento."),
        ("serious", "Medio", "Diseño del conector (hub)", "De él dependen el retiro de corte, la lista de corte, el galvanizado y la resistencia de las uniones."),
        ("serious", "Medio", "Lista de materiales incompleta", "Pestañas (~0.77 m² de plancha), pernos, soldadura, anclajes, tacos, concreto, deck, aislante, forro, ventanas, puerta, faldón."),
        ("serious", "Medio", "Grado real del tubo local", "Confirmar Fy, espesor real y diámetro disponible (1¼\" = 31.75 mm)."),
        ("warn", "Bajo", "Datos oficiales de viento y sismo", "COVENIN-MINDUR 2003 y COVENIN 1756 para Tovar, incluida la topografía de montaña."),
        ("warn", "Bajo", "Firma de un ingeniero", "Esta auditoría corrige números. No reemplaza la firma de un ingeniero matriculado."),
    ]
    pending_n = sum(1 for m in missing if m[0] != "good")
    miss_html = "\n".join(f"<li class='miss'><span class='chip {c}'>{'✓' if c == 'good' else '▲' if c == 'crit' else '◆' if c == 'serious' else '●'} {lab}</span>"
                          f"<div><b>{t}</b><p>{d}</p></div></li>" for c, lab, t, d in missing)

    body = f"""<title>Auditoría Domo Cucuchica</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
:root{{
  --page:#f1f3f1; --surface:#fbfbf9; --surface-2:#e9ece9; --ink:#15181b; --ink-2:#4b5257; --muted:#7c8388;
  --grid:#dde1dd; --line:#bfc5c1; --accent:#2b5a78;
  --crit:#d03b3b; --crit-text:#b3302f; --crit-wash:rgba(208,59,59,.12); --serious:#ec835a; --warn:#fab219;
  --good:#0ca30c; --good-text:#006300; --good-wash:rgba(12,163,12,.10);
  --sA:#2a78d6; --sB:#eb6834; --sC:#1baf7a; --o1:#86b6ef; --o2:#1c5cab; --seq:#2a78d6; --band:rgba(42,120,214,.10);
  --tube:rgba(75,82,87,.22);
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    color-scheme:dark;
    --page:#0f1112; --surface:#1b1d1f; --surface-2:#24272a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
    --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6;
    --crit-text:#ec7070; --crit-wash:rgba(208,59,59,.20); --good-text:#2fc12f; --good-wash:rgba(12,163,12,.16);
    --sA:#3987e5; --sB:#d95926; --sC:#199e70; --o1:#5598e7; --o2:#9ec5f4; --seq:#3987e5; --band:rgba(57,135,229,.16);
    --tube:rgba(193,198,195,.22);
  }}
}}
:root[data-theme="dark"]{{
  color-scheme:dark;
  --page:#0f1112; --surface:#1b1d1f; --surface-2:#24272a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6;
  --crit-text:#ec7070; --crit-wash:rgba(208,59,59,.20); --good-text:#2fc12f; --good-wash:rgba(12,163,12,.16);
  --sA:#3987e5; --sB:#d95926; --sC:#199e70; --o1:#5598e7; --o2:#9ec5f4; --seq:#3987e5; --band:rgba(57,135,229,.16);
  --tube:rgba(193,198,195,.22);
}}
*{{box-sizing:border-box}}
body{{background:var(--page); color:var(--ink); font:15px/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; padding-inline:16px; padding-block:0 56px}}
.wrap{{max-width:980px; margin:0 auto}}
h1,h2,h3{{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif; text-wrap:balance; letter-spacing:-.005em}}
h1{{font-size:clamp(30px,5vw,44px); line-height:1.05; margin:0 0 12px}}
h2{{font-size:24px; margin:0 0 6px}}
h3{{font-size:17px; margin:0 0 6px}}
p{{margin:0 0 10px; max-width:70ch}}
.mono,.num,.tab{{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace; font-variant-numeric:tabular-nums}}
.muted{{color:var(--muted)}}
a{{color:var(--accent)}}
a:focus-visible,button:focus-visible{{outline:2px solid var(--accent); outline-offset:2px}}
header.top{{padding-block:34px 26px; border-bottom:1px solid var(--grid)}}
.eyebrow{{font:600 12px/1 "IBM Plex Mono",monospace; letter-spacing:.09em; text-transform:uppercase; color:var(--accent); margin-bottom:12px}}
.lede{{font-size:17px; color:var(--ink-2); max-width:64ch}}
.verdict{{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin-top:22px}}
.vcell{{background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:12px 14px; display:flex; flex-direction:column; gap:4px}}
.vcell .n{{font:600 26px/1 "IBM Plex Mono",monospace}}
.vcell .t{{font-size:13px; color:var(--ink-2)}}
.chip{{display:inline-flex; align-items:center; gap:6px; font:600 12px/1 "IBM Plex Mono",monospace; padding:5px 8px; border-radius:4px; white-space:nowrap; align-self:flex-start}}
.chip.crit{{background:var(--crit-wash); color:var(--crit-text)}}
.chip.serious{{background:rgba(236,131,90,.16); color:var(--ink)}}
.chip.warn{{background:rgba(250,178,25,.18); color:var(--ink)}}
.chip.good{{background:var(--good-wash); color:var(--good-text)}}
.chip.neutral{{background:var(--surface-2); color:var(--ink-2)}}
section.f{{padding-block:34px; border-bottom:1px solid var(--grid); display:grid; gap:14px}}
.fhead{{display:flex; gap:10px; align-items:baseline; flex-wrap:wrap}}
.fid{{font:600 13px/1 "IBM Plex Mono",monospace; color:var(--muted)}}
.twocol{{display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,1fr); gap:22px; align-items:start}}
@media (max-width:760px){{ .twocol{{grid-template-columns:minmax(0,1fr)}} }}
.panel{{background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:14px}}
.panel svg{{width:100%; height:auto; display:block}}
.discs{{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px}}
@media (max-width:620px){{ .discs{{grid-template-columns:repeat(2,minmax(0,1fr))}} }}
.disc-fig{{margin:0; background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:8px 8px 10px; text-align:center}}
.disc-fig svg{{width:100%; height:auto; display:block}}
.disc-fig figcaption{{font-size:13px; color:var(--ink-2)}}
.legend{{display:flex; gap:16px; flex-wrap:wrap; font-size:13px; color:var(--ink-2)}}
.legend span{{display:inline-flex; align-items:center; gap:6px}}
.sw{{width:14px; height:3px; border-radius:2px; display:inline-block}}
.swb{{width:12px; height:12px; border-radius:3px; display:inline-block}}
.tbl{{overflow-x:auto; border:1px solid var(--grid); border-radius:8px; background:var(--surface)}}
table{{border-collapse:collapse; width:100%; font-size:13.5px}}
th,td{{text-align:left; padding:8px 10px; border-bottom:1px solid var(--grid); vertical-align:top}}
th{{font:600 11px/1.3 "IBM Plex Mono",monospace; letter-spacing:.05em; text-transform:uppercase; color:var(--muted)}}
tr:last-child td{{border-bottom:none}}
td.num{{white-space:nowrap}}
.bad{{color:var(--crit-text)}} .ok{{color:var(--good-text)}}
.callout{{border-left:3px solid var(--crit); background:var(--crit-wash); padding:10px 14px; border-radius:0 6px 6px 0}}
.callout p{{margin:0}}
/* svg */
.disc{{fill:var(--surface-2); stroke:var(--line); stroke-width:1}}
.ray-ok{{stroke:var(--good); stroke-width:2.5; stroke-linecap:round}}
.ray-bad{{stroke:var(--crit); stroke-width:2; stroke-linecap:round}}
.gapwedge{{fill:var(--crit-wash); stroke:var(--crit); stroke-width:1}}
.hubdot{{fill:var(--ink)}}
.lbl-crit{{fill:var(--crit-text); font:600 11.5px "IBM Plex Mono",monospace}}
.lbl-ink{{fill:var(--ink); font:500 11.5px "IBM Plex Mono",monospace}}
.lbl-muted{{fill:var(--muted); font:11px "IBM Plex Mono",monospace}}
.halo{{paint-order:stroke; stroke:var(--surface); stroke-width:4px; stroke-linejoin:round}}
.small{{font-size:9.5px}}
.tube{{fill:var(--tube); stroke:var(--ink-2); stroke-width:1}}
.clash{{fill:var(--crit-wash); stroke:var(--crit); stroke-width:1.5}}
.axis-line{{stroke:var(--ink-2); stroke-width:1}}
.tick-bad{{stroke:var(--crit); stroke-width:2}}
.tick-ink{{stroke:var(--ink); stroke-width:2}}
.disc-edge{{fill:none; stroke:var(--line); stroke-width:1.5}}
.grid{{stroke:var(--grid); stroke-width:1}}
.floor,.baseline{{stroke:var(--line); stroke-width:1.5}}
.dome-line{{fill:none; stroke:var(--ink-2); stroke-width:2}}
.connector{{stroke:var(--crit); stroke-width:1.5}}
.pt-bad{{fill:var(--surface); stroke:var(--crit); stroke-width:2}}
.pt-ok{{fill:var(--good); stroke:var(--surface); stroke-width:2}}
.pt-crit{{fill:var(--crit); stroke:var(--surface); stroke-width:2}}
.ring-guide{{fill:none; stroke:var(--grid); stroke-width:1}}
.ring-poly{{fill:var(--band); stroke:var(--ink-2); stroke-width:1.2}}
.flap{{fill:var(--crit-wash); stroke:var(--crit); stroke-width:1.5}}
.hinge{{stroke:var(--crit); stroke-width:3.5; stroke-linecap:round}}
.anc-low{{fill:var(--ink); stroke:var(--surface); stroke-width:2}}
.anc-high{{fill:var(--sA); stroke:var(--surface); stroke-width:2}}
.bar-seq{{fill:var(--seq)}}
.band{{fill:var(--band)}}
.ref-bad{{stroke:var(--crit); stroke-width:2}}
.bar-o1{{fill:var(--o1)}} .bar-o2{{fill:var(--o2)}}
.stock{{fill:var(--surface-2); stroke:var(--line); stroke-width:1}}
.seg-A{{fill:var(--sA)}} .seg-B{{fill:var(--sB)}} .seg-C{{fill:var(--sC)}}
.seglbl{{fill:#fff; font:600 10.5px "IBM Plex Mono",monospace}}
.head-zone{{fill:var(--band); stroke:var(--seq); stroke-width:1}}
.door{{fill:none; stroke:var(--crit); stroke-width:2}}
[data-tip]{{cursor:default}}
[data-tip]:hover{{opacity:.8}}
.cutrow{{display:grid; grid-template-columns:190px minmax(0,1fr) 110px; gap:10px; align-items:center}}
@media (max-width:620px){{ .cutrow{{grid-template-columns:minmax(0,1fr)}} }}
.cutrow svg{{width:100%; height:auto; display:block}}
.cutlabel{{font-size:13px}}
.cutnote{{font:600 12.5px "IBM Plex Mono",monospace}}
.cutnote.bad{{color:var(--crit-text)}} .cutnote.ok{{color:var(--good-text)}}
.cuts{{display:grid; gap:8px}}
ul.misslist{{list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr)); gap:10px}}
li.miss{{display:grid; grid-template-columns:110px minmax(0,1fr); gap:12px; background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:12px 14px}}
@media (max-width:520px){{ li.miss{{grid-template-columns:minmax(0,1fr)}} }}
li.miss p{{margin:2px 0 0; color:var(--ink-2); font-size:14px}}
#tip{{position:fixed; pointer-events:none; z-index:10; background:var(--ink); color:var(--page); font:12px/1.4 "IBM Plex Mono",monospace; padding:6px 8px; border-radius:5px; max-width:280px}}
footer{{padding-block:28px; color:var(--muted); font-size:13px}}
@media (prefers-reduced-motion: reduce){{ *{{transition:none!important}} }}
</style>
<div class="wrap">
<header class="top">
  <div class="eyebrow">Glamping Cucuchica · Domo geodésico 3V ⌀6 m · 24 sep 2026</div>
  <h1>Auditoría del domo: qué está bien, qué estaba mal y qué falta calcular</h1>
  <p class="lede">La geometría es correcta: 120 barras, 46 nodos y 75 paneles, reproducidos con un cálculo independiente. Pero con los documentos anteriores el domo no se podía fabricar ni armar sin errores: los ángulos del disco de nodo, el retiro de corte y las alturas de armado estaban mal, y la membrana no alcanzaba. Ya está corregido en el repositorio. Antes de comprometer dinero falta diseñar la puerta, la plataforma y los pilotes.</p>
  <div class="verdict">
    <div class="vcell"><span class="chip good">✓ Correcto</span><span class="n">100%</span><span class="t">de la geometría y la aritmética de cargas</span></div>
    <div class="vcell"><span class="chip crit">▲ Alto</span><span class="n">4</span><span class="t">errores que bloqueaban la fabricación o el armado seguro, ya corregidos</span></div>
    <div class="vcell"><span class="chip serious">◆ Medio</span><span class="n">5</span><span class="t">errores de dinero o de riesgo, corregidos o anotados</span></div>
    <div class="vcell"><span class="chip neutral">○ Sin calcular</span><span class="n">{pending_n}</span><span class="t">temas que cuestan dinero y todavía no tienen cálculo</span></div>
  </div>
</header>

<section class="f" id="ok">
  <div class="fhead"><h2>Lo que está bien</h2><span class="chip good">✓ confirmado</span></div>
  <p>Un programa nuevo que no usa el modelo original (construye el icosaedro por otro camino) llegó a los mismos números. También coinciden con las tablas estándar de un domo 3V de 3/8 de esfera.</p>
  <div class="tbl"><table><thead><tr><th>Dato</th><th>Publicado</th><th>Recalculado</th><th></th></tr></thead><tbody>{conf_rows}</tbody></table></div>
</section>

<section class="f" id="e1">
  <div class="fhead"><span class="fid">E1</span><h2>Ángulos para marcar el disco del nodo</h2><span class="chip crit">▲ Alto · corregido</span></div>
  <p>El documento decía que los ángulos entre barras (54.63°, 60.71°, 58.58°, 70.73°) se marcan directamente alrededor del disco. Son ángulos 3D entre tubos que bajan 10–12° respecto al disco, y suman menos de 360°. En el disco se marca el <b>azimut</b>: el ángulo proyectado sobre el plano del disco, que sí cierra en 360°.</p>
  <div class="legend"><span><i class="sw" style="background:var(--crit)"></i>✕ publicado (ángulo 3D acumulado)</span><span><i class="sw" style="background:var(--good)"></i>✓ correcto (azimut)</span></div>
  <div class="discs">{hub_svgs}</div>
  <div class="callout"><p>Con 1.45° de error, la otra punta de una barra A queda unos <b>3.2 cm</b> fuera de lugar. Con 46 discos marcados así, el domo no cierra.</p></div>
  <div class="tbl"><table><thead><tr><th>Nodo</th><th>✕ Publicado (3D)</th><th>✓ Marcar en el disco</th><th>Diferencia</th><th>Inclinación de la pestaña</th></tr></thead><tbody>{hub_table()}</tbody></table></div>
</section>

<section class="f" id="e2">
  <div class="fhead"><span class="fid">E2</span><h2>Retiro de corte en cada extremo del tubo</h2><span class="chip crit">▲ Alto · corregido</span></div>
  <div class="twocol">
    <div>
      <p>El documento decía que al largo de centro a centro se le restan "entre 1 y 3 cm por extremo". Con tubo de 32 mm, donde dos barras forman {D['setback']['min_angle']:.2f}° los tubos ocupan el mismo espacio hasta <b>{D['setback']['min_setback_cm']:.1f} cm</b> del centro del nodo. Con el disco de ⌀13 cm propuesto, el tubo arranca en el borde, a unos 6.5 cm.</p>
      <p>Hay que definir el conector antes de cortar un solo tubo.</p>
      <div class="tbl"><table><thead><tr><th>Retiro por extremo</th><th>Corte A</th><th>Corte B</th><th>Corte C</th></tr></thead><tbody>
      {"".join(f"<tr><td class='num'>{sb:.1f} cm</td>" + "".join(f"<td class='num'>{S[k]['L_cm']-2*sb:.2f}</td>" for k in 'ABC') + "</tr>" for sb in (3.5, 5.0, 6.5))}
      </tbody></table></div>
    </div>
    <div class="panel">{clash_svg()}</div>
  </div>
</section>

<section class="f" id="e3">
  <div class="fhead"><span class="fid">E3</span><h2>Alturas de armado 52.3 cm más altas</h2><span class="chip crit">▲ Alto · corregido</span></div>
  <div class="twocol">
    <div class="panel">{heights_svg()}
      <div class="legend"><span><i class="swb" style="border:2px solid var(--crit)"></i>✕ lo que decía la secuencia</span><span><i class="swb" style="background:var(--good)"></i>✓ altura real sobre el piso</span></div>
    </div>
    <div>
      <p>La secuencia de armado medía desde el <b>centro de la esfera</b>, que está 52.3 cm por debajo del piso. Por eso el ápice aparecía a 3.045 m, fuera del domo, cuando el documento principal dice 2.52 m.</p>
      <div class="tbl"><table><thead><tr><th>Paso</th><th>✕ Decía</th><th>✓ Real</th></tr></thead><tbody>{heights_rows()}</tbody></table></div>
    </div>
  </div>
</section>

<section class="f" id="e4">
  <div class="fhead"><span class="fid">E4 · E5</span><h2>Nodos sin arriostrar en el paso 1 y replanteo de anclajes</h2><span class="chip crit">▲ Alto · corregido</span></div>
  <div class="twocol">
    <div class="panel">{plan_svg(anchors, step1)}
      <div class="legend"><span><i class="swb" style="background:var(--ink)"></i>anclaje bajo H4</span><span><i class="swb" style="background:var(--sA)"></i>anclaje alto H5 (+4.86 cm)</span><span><i class="swb" style="background:var(--crit)"></i>▲ nodo bisagra: puntal</span></div>
    </div>
    <div>
      <p>La secuencia decía que "0 nodos necesitan sujeción temporal". Un nodo con 2 barras está fijo en un plano, pero en el espacio es una <b>bisagra</b> y gira sobre la línea entre sus apoyos. Los 5 triángulos del paso 1 (<span class="mono">#{", #".join(str(k) for k in sorted(step1))}</span>) quedan como aletas hasta que el paso 2 los amarra. Hacen falta 5 puntales o cuerdas, y nadie debe estar debajo.</p>
      <p>El documento también decía que las posiciones de los anclajes estaban en la secuencia, y no estaban. Ya están: azimut, radio y coordenadas desde el centro.</p>
    </div>
  </div>
  <div class="tbl"><table><thead><tr><th>Nodo</th><th>Tipo</th><th>Azimut</th><th>Radio (m)</th><th>X (m)</th><th>Y (m)</th><th>Sobre el piso</th></tr></thead><tbody>{anchor_rows(anchors)}</tbody></table></div>
</section>

<section class="f" id="e6">
  <div class="fhead"><span class="fid">E6</span><h2>La membrana no alcanza</h2><span class="chip serious">◆ Medio · dinero</span></div>
  <p>Se presupuestaron 46.24 m² + 12% = 51.8 m², cortando 75 paneles. Cada panel mide unos 3.5 m de perímetro y el solape de costura se suma en todo ese borde. Con 3–5 cm de solape, las piezas solas ya superan lo presupuestado, antes de contar el desperdicio del rollo.</p>
  <div class="panel">{membrane_svg()}</div>
  <p class="muted">Tampoco están en la lista: aislante, forro interior, ventanas, puerta y el faldón que tapa el hueco de 4.86 cm bajo el zigzag.</p>
</section>

<section class="f" id="e7">
  <div class="fhead"><span class="fid">E7</span><h2>Viento: el reparto por anclaje no es parejo</h2><span class="chip serious">◆ Medio · riesgo</span></div>
  <p>La auditoría resolvió el domo como armadura espacial con el mismo viento de 100 km/h. El patrón de presiones usado da exactamente el empuje total del documento ({tr['Viento: Cp barlovento +0.6 / cresta -1.1 / sotavento -0.4']['sum_horizontal_kgf']:.0f} kgf), pero repartido: algunos anclajes cargan mucho más que el promedio. Además, si una puerta abierta presuriza el interior, el arranque crece. El documento no consideraba la presión interna.</p>
  <div class="legend"><span><i class="swb" style="background:var(--o1)"></i>sin presión interna</span><span><i class="swb" style="background:var(--o2)"></i>con presión interna (puerta abierta al viento)</span><span><i class="sw" style="background:var(--crit)"></i>✕ promedio del .md</span></div>
  <div class="twocol">
    <div class="panel"><h3>Arranque por anclaje (kgf)</h3>{wind_up}</div>
    <div class="panel"><h3>Corte horizontal por anclaje (kgf)</h3>{wind_sh}</div>
  </div>
  <div class="tbl"><table><thead><tr><th>Base de diseño por perno (§9.4)</th><th>✕ El .md decía</th><th>✓ Con reparto real y presión interna</th></tr></thead><tbody>
    <tr><td>Arranque (FS 2.5)</td><td class="num bad">274 kgf</td><td class="num ok"><b>≈{up_b*2.5:.0f} kgf</b></td></tr>
    <tr><td>Corte (FS 2.0)</td><td class="num bad">66 kgf</td><td class="num ok"><b>≈{sh_b*2.0:.0f} kgf</b></td></tr>
  </tbody></table></div>
  <p class="muted">El perno M12 sigue sobrando por acero (≈2000 kgf). Lo que cambia es el embebido en el concreto y el peso que necesitan los pilotes para no levantarse.</p>
</section>

<section class="f" id="e8">
  <div class="fhead"><span class="fid">E8</span><h2>Lista de corte en barras de 6 m</h2><span class="chip serious">◆ Medio · dinero</span></div>
  <p>El patrón publicado deja <b>{D['cutting']['6']['tight_slack_mm']:.1f} mm</b> de sobra: una barra de 5.99 m o un extremo dañado arruinan la quinta pieza. Con el largo real de corte (3.5 cm de retiro por extremo), bastan <b>{rc['bars6']} barras en lugar de 27</b>, con al menos 20 mm de holgura en cada una. Hay que recalcularlo cuando esté definido el conector.</p>
  <div class="legend"><span><i class="swb" style="background:var(--sA)"></i>A</span><span><i class="swb" style="background:var(--sB)"></i>B</span><span><i class="swb" style="background:var(--sC)"></i>C</span><span class="muted">largos en cm · barra comercial de 6.00 m a escala</span></div>
  <div class="panel cuts">{cut_html}</div>
</section>

<section class="f" id="e9">
  <div class="fhead"><span class="fid">E9–E12</span><h2>Otros hallazgos</h2><span class="chip warn">● Bajo / Medio</span></div>
  <div class="tbl"><table><thead><tr><th>Hallazgo</th><th>Detalle</th></tr></thead><tbody>
    <tr><td>Galvanizado contra soldadura en sitio</td><td>"Galvanizar después de soldar" choca con "soldar en sitio". Hay que elegir entre uniones empernadas o reparación en frío. Los tubos cerrados necesitan venteo para el baño en caliente.</td></tr>
    <tr><td>"2.7 t" de pandeo</td><td>Es la carga elástica de Euler. La capacidad de diseño es ≈1.3–2.1 t. La barra más cargada llega a ≈{max(v['max_comp_kgf'] for v in tr.values()):.0f} kgf, un 5%, así que la sección alcanza. Pero <b>100 kg parados a media barra la llevan a ≈{D['bending_person']['A']['sigma_MPa']:.0f} MPa, en fluencia</b>: nadie camina sobre las barras.</td></tr>
    <tr><td>Verificador "independiente"</td><td><span class="mono">dome_verify.py</span> usa el mismo modelo y no lee el .md, aunque el documento dice lo contrario.</td></tr>
    <tr><td>Textos</td><td>"12–19 cm" entre barras: en realidad 2.7–19.4 cm. Volumen: 44.07 m³ es el de la esfera; el poliedro encierra {g['vol_poly']:.1f} m³.</td></tr>
  </tbody></table></div>
</section>

<section class="f" id="falta">
  <div class="fhead"><h2>Lo que no está calculado y cuesta dinero</h2><span class="chip neutral">○ antes de comprar</span></div>
  <div class="twocol">
    <div class="panel"><h3>Altura libre y puerta</h3>{headroom_svg()}</div>
    <div>
      <p>El domo mide 2.52 m en el centro. A 2.0 m del centro el techo está a 1.77 m, y a 2.5 m está a 1.22 m. Una puerta de 2 m pegada a la pared queda cortada por el domo.</p>
      <p><b>Actualización:</b> la puerta ya está resuelta con un portal: el marco se apoya en el borde y un techo de vestíbulo entra al domo hasta donde el techo pasa de 2 m (ver el plano de taller). La altura útil del resto del domo no cambia: si hiciera falta más espacio de pie, las opciones siguen siendo un domo 5/8, un 4V o un muro de arranque.</p>
    </div>
  </div>
  <ul class="misslist">{miss_html}</ul>
</section>

<footer>
  <p><b>Actualización 24 sep 2026:</b> después de esta auditoría se diseñó la puerta y se rehízo el plano de taller (<span class="mono">domo-3v-cucuchica.html</span>) con todas las correcciones. El jacuzzi va en la terraza exterior con fundación propia. Esta página describe el domo tal como estaba publicado, sin puerta: por eso el paso 1 tiene 5 nodos bisagra; con la puerta son 4, más 2 en el paso 2 que se amarran dentro del mismo paso.</p>
  <p>Todo se reproduce con <span class="mono">python3 auditoria_independiente.py</span> y <span class="mono">python3 reporte_visual.py</span> en <a href="{REPO}/auditoria">glamping-cucuchica/auditoria</a>. Informe completo: <a href="{REPO}/auditoria/AUDITORIA.md">AUDITORIA.md</a>. El análisis de barras supone nodos articulados, y el viento es el valor ilustrativo del documento: esto no reemplaza la firma de un ingeniero estructural.</p>
</footer>
</div>
<div id="tip" hidden></div>
<script>
(function(){{
  var tip=document.getElementById('tip');
  function show(e){{ var t=e.target.closest('[data-tip]'); if(!t){{tip.hidden=true;return;}}
    tip.textContent=t.getAttribute('data-tip'); tip.hidden=false;
    var x=e.clientX+14, y=e.clientY+12; var w=tip.offsetWidth;
    if(x+w>window.innerWidth-8) x=e.clientX-w-14; tip.style.left=x+'px'; tip.style.top=y+'px'; }}
  document.addEventListener('pointermove',show);
  document.addEventListener('pointerdown',show);
  document.addEventListener('scroll',function(){{tip.hidden=true;}},{{passive:true}});
}})();
</script>
"""
    return body


if __name__ == "__main__":
    out = os.path.join(HERE, "reporte_auditoria.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page())
    print("Escrito:", out)
