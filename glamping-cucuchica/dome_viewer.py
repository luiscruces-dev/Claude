"""
Genera domo-3v-cucuchica.html: el plano de taller del domo con puerta.

Corre: `python3 dome_viewer.py`  (Python estandar; usa dome_model.py,
dome_door.py, dome_build_sequence.py, dome_platform.py y escena3d.py).

Todo lo que muestra la pagina sale de esos modulos al momento de generarla:
vista 3D (three.js, la misma escena que la maqueta, con filtros por tipo de
barra y por paso de armado), piezas y plan de corte (para 3 retiros posibles), plantillas de
los discos de nodo (estandar y los especiales de la puerta), dibujos de la
puerta, replanteo de anclajes, resumen de armado, cubierta y cargas. Si
cambia un parametro en dome_model.py o dome_door.py, se vuelve a correr y la
pagina queda al dia sola.
"""

import html
import json
import math
import os
from collections import Counter, defaultdict

import dome_build_sequence as seq
import dome_door as door
import comparar_tubos
import dome_platform as plat
import escena3d
from dome_model import v_sub, v_norm

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
SETBACKS = (0.035, 0.050, 0.065)
DOOR_CODES = {"P", "D", "V", "K1", "K2"}
HUB_DESC = {"H1": "interior", "H2": "interior", "H3": "interior, incluye el ápice", "H4": "base, nodo bajo",
            "H5": "base, nodo alto (+4.86 cm)", "PA": "base, lleva el poste de la puerta",
            "PB": "junto a la puerta, amarre bajo K1", "PC": "junto a la puerta, amarre alto K2",
            "PD": "sobre el vestíbulo, recibe las 2 vigas V", "PE": "tope del marco de la puerta"}


def esc(s):
    return html.escape(str(s), quote=True)


def f(x, n=1):
    return f"{x:.{n}f}"


def color_var(lab):
    return {"A": "var(--sA)", "B": "var(--sB)", "C": "var(--sC)"}.get(lab, "var(--door)")


def code_chip(lab):
    fg = "#fff" if lab in ("A", "B", "C") else "var(--page)"
    return f"<span class='code' style='--c:{color_var(lab)};color:{fg}'>{esc(lab)}</span>"


# ------------------------------------------------------------------ datos

def collect():
    D = door.build_dome_with_door()
    door.FAILS.clear()
    results, q = door.run_structure(D)
    env, anc, dmax = door.envelope(D, results)
    D0 = door.build_dome_plain()
    res0, _ = door.run_structure(D0)
    env0, anc0, _ = door.envelope(D0, res0)
    seq.WARNINGS.clear()
    steps, missing = seq.build_sequence(D)
    assert not missing
    return D, {"env": env, "anc": anc, "dmax": dmax, "q": q, "anc0": anc0, "env0": env0}, steps


def panel_groups(D):
    """Agrupa los paneles por forma (lados redondeados al mm)."""
    groups = defaultdict(list)
    for t in D.triangles:
        sides = tuple(sorted(round(v_norm(v_sub(D.verts[t[i]], D.verts[t[(i+1) % 3]])), 3) for i in range(3)))
        groups[sides].append(t)
    out = []
    new = set(map(tuple, D.new_triangles))
    k = 0
    for sides, ts in sorted(groups.items(), key=lambda kv: (any(tuple(t) in new for t in kv[1]), -len(kv[1]))):
        vest = any(tuple(t) in new for t in ts)
        if vest:
            k += 1
            name = f"V{k}"
        else:
            name = "P1" if len(ts) > 35 else "P2"
        a, b, c = sides
        s2 = (a+b+c)/2
        area = math.sqrt(max(0.0, s2*(s2-a)*(s2-b)*(s2-c)))
        angs = [math.degrees(math.acos((b*b+c*c-a*a)/(2*b*c))), math.degrees(math.acos((a*a+c*c-b*b)/(2*a*c))),
                math.degrees(math.acos((a*a+b*b-c*c)/(2*a*b)))]
        out.append({"name": name, "sides": sides, "n": len(ts), "area": area, "angs": angs, "vest": vest})
    return out


def seam_area(panels, allow):
    tot = 0.0
    for p in panels:
        cot = sum(1/math.tan(math.radians(x/2)) for x in p["angs"])
        tot += p["n"]*(p["area"] + sum(p["sides"])*allow + allow*allow*cot)
    return tot


def dead_weight(D):
    kg = 0.0
    for e in D.edges:
        kg += D.edge_len[e]*door.section_of(D, e)["kg_m"]
    kg += 0.521*len(D.active)
    mem = sum(door.tri_info(D, t)[1] for t in D.triangles)*0.9
    return kg, mem


# ------------------------------------------------------------------ dibujos

def disc_svg(members, gaps, is_open, title):
    """Plantilla del disco: primera pestana arriba, azimuts en sentido horario
    visto desde afuera del domo."""
    size = 270
    Wd = 330
    cx, cy, R = Wd/2, size/2 + 4, 84
    n = len(members)
    cum = [0.0]
    for g in gaps[:n-1]:
        cum.append(cum[-1] + g)
    o = [f'<svg viewBox="0 0 {Wd} {size+8}" role="img" aria-label="{esc(title)}">']
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{R*0.62}" class="disc"/>')
    if is_open:
        a0 = math.radians(cum[-1] - 90); a1 = math.radians(360 - 90)
        rw = R*0.62
        large = 1 if (360 - cum[-1]) > 180 else 0
        o.append(f'<path d="M {f(cx)} {f(cy)} L {f(cx+rw*math.cos(a0))} {f(cy+rw*math.sin(a0))} A {f(rw)} {f(rw)} 0 {large} 1 '
                 f'{f(cx+rw*math.cos(a1))} {f(cy+rw*math.sin(a1))} Z" class="openwedge"/>')
        am = math.radians((cum[-1] + 360)/2 - 90)
        o.append(f'<text x="{f(cx+R*0.36*math.cos(am))}" y="{f(cy+R*0.36*math.sin(am)+4)}" text-anchor="middle" class="t-muted">abierto</text>')
    arcs = n if not is_open else n-1
    for i in range(arcs):
        a0 = cum[i]; a1 = cum[i+1] if i+1 < n else 360.0
        r = 42
        p0 = (cx + r*math.cos(math.radians(a0-90)), cy + r*math.sin(math.radians(a0-90)))
        p1 = (cx + r*math.cos(math.radians(a1-90)), cy + r*math.sin(math.radians(a1-90)))
        o.append(f'<path d="M {f(p0[0])} {f(p0[1])} A {r} {r} 0 {1 if a1-a0 > 180 else 0} 1 {f(p1[0])} {f(p1[1])}" class="arc"/>')
        am = math.radians((a0+a1)/2 - 90)
        o.append(f'<text x="{f(cx+60*math.cos(am))}" y="{f(cy+60*math.sin(am)+4)}" text-anchor="middle" class="t-angle">{gaps[i]:.2f}°</text>')
    for i, m in enumerate(members):
        a = math.radians(cum[i] - 90)
        x2, y2 = cx + R*math.cos(a), cy + R*math.sin(a)
        o.append(f'<line x1="{f(cx)}" y1="{f(cy)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{color_var(m["label"])}" class="ray" '
                 f'data-tip="Pestaña {i+1}: barra {m["label"]} hacia #{m["to"]} · azimut acumulado {cum[i]:.2f}° · inclinación {m["tilt"]:+.2f}°"/>')
        lx, ly = cx + (R+16)*math.cos(a), cy + (R+16)*math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.3 else ("start" if math.cos(a) > 0 else "end")
        o.append(f'<text x="{f(lx)}" y="{f(ly+4)}" text-anchor="{anchor}" class="t-code">{esc(m["label"])} '
                 f'<tspan class="t-tilt">{m["tilt"]:+.1f}°</tspan></text>')
    o.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="4" class="hubdot"/>')
    o.append("</svg>")
    return "".join(o)


def rotate_start(members, gaps, is_open, prefer):
    if is_open:
        return members, gaps
    n = len(members)
    k = next((i for i, m in enumerate(members) if m["label"] in prefer), 0)
    return members[k:] + members[:k], gaps[k:] + gaps[:k]


def door_elevation_svg(D):
    """Vista de frente de la puerta desde afuera: domo en elevacion, marco y amarres."""
    s = 92
    W, H = 640, 365
    ox, oy = W/2, H - 72
    P = D.verts; uv = D.uv
    def X(vv): return ox + vv*s
    def Y(z): return oy - z*s
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Vista de frente de la puerta">']
    R = D.R; z0 = -D.center[2]
    pts = " ".join(f"{f(X(v))},{f(Y(math.sqrt(R*R-v*v)-z0))}" for v in [i/40*3 - 3 for i in range(0, 241)] if abs(v) <= 3)
    o.append(f'<polyline points="{pts}" class="dome-outline"/>')
    o.append(f'<line x1="{X(-3.25)}" y1="{Y(0)}" x2="{X(3.25)}" y2="{Y(0)}" class="floor"/>')
    # barras del domo visibles desde el frente (mitad de adelante)
    for e in D.edges:
        a, b = e
        if D.edge_label[e] in DOOR_CODES:
            continue
        ua, va, za = uv(P[a]); ub, vb, zb = uv(P[b])
        if (ua + ub)/2 > 0.2:
            o.append(f'<line x1="{f(X(va))}" y1="{f(Y(za))}" x2="{f(X(vb))}" y2="{f(Y(zb))}" class="strut-faint"/>')
    for e in D.edges:
        lab = D.edge_label[e]
        if lab in ("V", "K1", "K2"):
            a, b = e
            _, va, za = uv(P[a]); _, vb, zb = uv(P[b])
            o.append(f'<line x1="{f(X(va))}" y1="{f(Y(za))}" x2="{f(X(vb))}" y2="{f(Y(zb))}" class="door-member" '
                     f'data-tip="{lab}: #{a}–#{b}, {D.edge_len[e]*100:.2f} cm"/>')
    dd = D.door
    va = uv(P[dd["a"]])[1]; vb = uv(P[dd["b"]])[1]; hz = dd["head_z"]; hb = door.FRAME_B
    # marco 50x50 dibujado con su ancho real
    for vv in (va, vb):
        o.append(f'<rect x="{f(X(vv-hb/2))}" y="{f(Y(hz+hb/2))}" width="{f(hb*s)}" height="{f((hz+hb/2)*s)}" class="frame" data-tip="Poste P 50×50×2"/>')
    o.append(f'<rect x="{f(X(va+hb/2))}" y="{f(Y(hz+hb/2))}" width="{f((vb-va-hb)*s)}" height="{f(hb*s)}" class="frame" data-tip="Dintel D 50×50×2"/>')
    o.append(f'<rect x="{f(X(va+hb/2))}" y="{f(Y(hz-hb/2))}" width="{f((vb-va-hb)*s)}" height="{f((hz-hb/2)*s)}" class="door-open"/>')
    o.append(f'<line x1="{f(X(va))}" y1="{f(Y(0))}" x2="{f(X(vb))}" y2="{f(Y(0))}" class="sill" data-tip="Umbral: barra B del domo (se conserva)"/>')
    # cotas
    cw = vb - va - hb; ch = hz - hb/2
    yd = Y(-0.28)
    o.append(f'<line x1="{f(X(va+hb/2))}" y1="{f(yd)}" x2="{f(X(vb-hb/2))}" y2="{f(yd)}" class="dim"/>')
    for xx in (X(va+hb/2), X(vb-hb/2)):
        o.append(f'<line x1="{f(xx)}" y1="{f(yd-5)}" x2="{f(xx)}" y2="{f(yd+5)}" class="dim"/>')
    o.append(f'<text x="{f(ox)}" y="{f(yd+16)}" text-anchor="middle" class="t-dim">vano libre {cw*100:.1f} cm</text>')
    xd = X(va + hb/2 + 0.09)
    o.append(f'<line x1="{f(xd)}" y1="{f(Y(0))}" x2="{f(xd)}" y2="{f(Y(ch))}" class="dim"/>')
    for yy in (Y(0), Y(ch)):
        o.append(f'<line x1="{f(xd-5)}" y1="{f(yy)}" x2="{f(xd+5)}" y2="{f(yy)}" class="dim"/>')
    o.append(f'<text x="{f(xd+7)}" y="{f(Y(ch/2))}" class="t-dim">{ch*100:.1f}</text>')
    o.append(f'<text x="{f(xd+7)}" y="{f(Y(ch/2)+14)}" class="t-muted">cm libre</text>')
    o.append(f'<text x="{f(ox)}" y="{f(yd+32)}" text-anchor="middle" class="t-muted">eje del dintel a {hz*100:.0f} cm sobre el piso · postes y dintel 50×50×2</text>')
    for node in (dd["a"], dd["b"], dd["top"], dd["side_low"][dd["a"]], dd["side_up"][dd["a"]], dd["side_low"][dd["b"]], dd["side_up"][dd["b"]]):
        _, vv, zz = uv(P[node])
        o.append(f'<circle cx="{f(X(vv))}" cy="{f(Y(zz))}" r="4" class="node" data-tip="#{node} ({seq.hub_type_of(D, node)})"/>')
        o.append(f'<text x="{f(X(vv)+(8 if vv >= 0 else -8))}" y="{f(Y(zz)-6)}" text-anchor="{"start" if vv >= 0 else "end"}" class="t-node">#{node}</text>')
    o.append("</svg>")
    return "".join(o)


def door_section_svg(D):
    """Corte por el eje de la puerta: domo (solo donde existe), techo del
    vestibulo, marco, paso libre, y el domo al costado del paso (linea tenue)."""
    s = 128
    W, H = 640, 400
    P = D.verts; uv = D.uv
    u0 = -0.55
    ox, oy = 30, H - 44
    def X(u): return ox + (u - u0)*s
    def Y(z): return oy - z*s
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Corte por el eje de la puerta">']
    R = D.R; z0 = -D.center[2]
    dd = D.door
    ua = uv(P[dd["a"]])[0]; ut = uv(P[dd["top"]])[0]; zt = uv(P[dd["top"]])[2]; hz = dd["head_z"]; hb = door.FRAME_B
    half = abs(uv(P[dd["a"]])[1])
    side = " ".join(f"{f(X(u))},{f(Y(math.sqrt(max(0.0, R*R-u*u-half*half))-z0))}" for u in [u0 + i*(math.sqrt(9-half*half)-u0)/120 for i in range(121)])
    o.append(f'<polyline points="{side}" class="strut-faint" data-tip="Superficie del domo al costado del paso"/>')
    o.append(f'<text x="{f(X(2.55))}" y="{f(Y(0.95))}" class="t-muted" text-anchor="end">domo al costado</text>')
    arc = " ".join(f"{f(X(u))},{f(Y(math.sqrt(R*R-u*u)-z0))}" for u in [u0 + i*(ut-u0)/40 for i in range(41)])
    o.append(f'<polyline points="{arc}" class="dome-outline"/>')
    o.append(f'<line x1="{f(X(u0))}" y1="{f(Y(0))}" x2="{f(X(3.55))}" y2="{f(Y(0))}" class="floor"/>')
    box, _ = door.clearance(D)
    o.append(f'<rect x="{f(X(box[0]))}" y="{f(Y(box[5]))}" width="{f((box[1]-box[0])*s)}" height="{f((box[5]-box[4])*s)}" class="passage" '
             f'data-tip="Paso libre revisado: ninguna barra ni panel entra aquí"/>')
    o.append(f'<rect x="{f(X(ua-hb/2))}" y="{f(Y(hz+hb/2))}" width="{f(hb*s)}" height="{f((hz+hb/2)*s)}" class="frame" data-tip="Poste P"/>')
    o.append(f'<line x1="{f(X(ua))}" y1="{f(Y(hz))}" x2="{f(X(ut))}" y2="{f(Y(zt))}" class="door-member" data-tip="Techo del vestíbulo (vigas V)"/>')
    o.append(f'<circle cx="{f(X(ut))}" cy="{f(Y(zt))}" r="4" class="node" data-tip="#{dd["top"]} (PD)"/>')
    o.append(f'<text x="{f(X(ut))}" y="{f(Y(zt)-10)}" text-anchor="middle" class="t-node">#{dd["top"]} · {zt*100:.0f} cm</text>')
    slope = (zt-hz)/(ua-ut)*100
    o.append(f'<text x="{f(X((ua+ut)/2+0.25))}" y="{f(Y((hz+zt)/2)-12)}" text-anchor="middle" class="t-muted">techo del vestíbulo, cae {slope:.0f}% hacia la puerta</text>')
    o.append(f'<text x="{f(X(ua)+8)}" y="{f(Y(hz)+4)}" class="t-node">dintel {hz*100:.0f} cm</text>')
    o.append(f'<text x="{f(X((box[0]+box[1])/2))}" y="{f(Y(1.05))}" text-anchor="middle" class="t-dim">paso libre</text>')
    o.append(f'<text x="{f(X((box[0]+box[1])/2))}" y="{f(Y(1.05)+15)}" text-anchor="middle" class="t-dim">{box[5]*100:.0f} cm de alto</text>')
    o.append(f'<text x="{f(X(ua)+10)}" y="{f(Y(0.35))}" class="t-muted">afuera →</text>')
    o.append(f'<text x="{f(X(u0)+6)}" y="{f(Y(0.35))}" class="t-muted">← centro del domo</text>')
    o.append(f'<text x="{f(X(0))}" y="{f(Y(0)+18)}" text-anchor="middle" class="t-muted">0</text>')
    o.append(f'<text x="{f(X(ut))}" y="{f(Y(0)+18)}" text-anchor="middle" class="t-muted">{ut:.2f} m</text>')
    o.append(f'<text x="{f(X(ua))}" y="{f(Y(0)+18)}" text-anchor="middle" class="t-muted">{ua:.2f} m</text>')
    o.append("</svg>")
    return "".join(o)


def base_plan_svg(D, rows):
    s = 50
    W = H = 400
    cx, cy = W/2, H/2
    byid = {r["node"]: r for r in rows}
    def XY(x, y): return (cx + x*s, cy - y*s)
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Planta de anclajes con la puerta">']
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{3*s}" class="ring-guide"/>')
    poly = " ".join(f"{f(XY(r['x'], r['y'])[0])},{f(XY(r['x'], r['y'])[1])}" for r in rows)
    o.append(f'<polygon points="{poly}" class="ring-poly"/>')
    o.append(f'<line x1="{cx}" y1="{cy}" x2="{W-2}" y2="{cy}" class="grid"/>')
    o.append(f'<text x="{W-2}" y="{cy-10}" text-anchor="end" class="t-muted">0°</text>')
    dd = D.door
    pa, pb = byid[dd["a"]], byid[dd["b"]]
    A_, B_ = XY(pa["x"], pa["y"]), XY(pb["x"], pb["y"])
    o.append(f'<line x1="{f(A_[0])}" y1="{f(A_[1])}" x2="{f(B_[0])}" y2="{f(B_[1])}" class="door-plan" data-tip="Puerta: marco sobre #{dd["a"]} y #{dd["b"]}"/>')
    az = math.radians(dd["azimuth_deg"])
    tx, ty = XY(3.55*math.cos(az), 3.55*math.sin(az))
    o.append(f'<text x="{f(tx)}" y="{f(ty+4)}" text-anchor="middle" class="t-door">PUERTA</text>')
    for r in rows:
        x, y = XY(r["x"], r["y"])
        high = r["dz"] > 1e-6
        post = r["node"] in (dd["a"], dd["b"])
        cls = "anc-post" if post else ("anc-high" if high else "anc-low")
        o.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{7 if post else (6 if high else 4.5)}" class="{cls}" '
                 f'data-tip="#{r["node"]} {seq.hub_type_of(D, r["node"])} · azimut {r["az"]:.3f}° · X {r["x"]:+.4f} · Y {r["y"]:+.4f}'
                 f'{" · lleva poste de la puerta" if post else ""}"/>')
        lx, ly = XY(r["x"]*1.12, r["y"]*1.12)
        o.append(f'<text x="{f(lx)}" y="{f(ly+4)}" text-anchor="middle" class="t-node">#{r["node"]}</text>')
    o.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" class="t-muted">⌀ 6.00 m</text>')
    o.append("</svg>")
    return "".join(o)


def cutbar_svg(pieces, L, stock=6.0):
    W = 600
    sc = W/stock
    o = [f'<svg viewBox="0 0 {W} 30" role="img" aria-label="Barra de 6 m">', f'<rect x="0" y="4" width="{W}" height="22" rx="4" class="stock"/>']
    x = 0.0
    for p in pieces:
        w = L[p]*sc
        cls = f"seg-{p}" if p in ("A", "B", "C") else "seg-door"
        o.append(f'<rect x="{f(x)}" y="4" width="{f(max(0, w-2))}" height="22" rx="3" class="{cls}" data-tip="{p}: cortar a {L[p]*100:.1f} cm"/>')
        o.append(f'<text x="{f(x+w/2)}" y="19" text-anchor="middle" class="seglbl">{p} · {L[p]*100:.1f}</text>')
        x += w + 0.003*sc
    o.append("</svg>")
    return "".join(o)



# ------------------------------------------------------------------ plataforma

def platform_plan_svg(P):
    """Planta de fundaciones y entrepiso con el eje de la puerta hacia arriba."""
    s = 58
    umax = P.steps[-1]["u1"] + 0.3; umin = -3.4
    vmin, vmax = -3.45, 3.45
    W = (vmax-vmin)*s + 20; H = (umax-umin)*s + 30
    def X(v): return 10 + (v-vmin)*s
    def Y(u): return 18 + (umax-u)*s
    o = [f'<svg viewBox="0 0 {f(W)} {f(H)}" role="img" aria-label="Planta de la plataforma y los pilotes">']
    for p in P.piles:
        o.append(f'<rect x="{f(X(p["v"]-plat.FOOT/2))}" y="{f(Y(p["u"]+plat.FOOT/2))}" width="{f(plat.FOOT*s)}" height="{f(plat.FOOT*s)}" class="zap"/>')
    ring = "M " + " L ".join(f"{f(X(v))} {f(Y(u))}" for u, v in P.outer) + " Z M " + " L ".join(f"{f(X(v))} {f(Y(u))}" for u, v in P.inner) + " Z"
    o.append(f'<path d="{ring}" class="ringband" fill-rule="evenodd" data-tip="Viga de anillo de concreto 25×30 cm"/>')
    for j in P.joists:
        o.append(f'<line x1="{f(X(j["v0"]))}" y1="{f(Y(j["u"]))}" x2="{f(X(j["v1"]))}" y2="{f(Y(j["u"]))}" class="joist" data-tip="Vigueta 2×4&quot; a {j["u"]:+.2f} m"/>')
    for lj in P.landing_joists:
        o.append(f'<line x1="{f(X(lj["v"]))}" y1="{f(Y(lj["u0"]))}" x2="{f(X(lj["v"]))}" y2="{f(Y(lj["u1"]))}" class="joist"/>')
    for bm in P.beams:
        o.append(f'<rect x="{f(X(bm["v"]-plat.BEAM_B/2))}" y="{f(Y(bm["u1"]))}" width="{f(plat.BEAM_B*s)}" height="{f((bm["u1"]-bm["u0"])*s)}" class="beam" '
                 f'data-tip="Viga principal 100×50×3, {bm["u1"]-bm["u0"]:.2f} m"/>')
    L = P.landing
    o.append(f'<rect x="{f(X(L["v0"]))}" y="{f(Y(L["u1"]))}" width="{f((L["v1"]-L["v0"])*s)}" height="{f((L["u1"]-L["u0"])*s)}" class="landing" data-tip="Descanso de entrada 1.80 × 1.20 m"/>')
    o.append(f'<rect x="{f(X(L["v0"]))}" y="{f(Y(L["beam_u"]+plat.BEAM_B/2))}" width="{f((L["v1"]-L["v0"])*s)}" height="{f(plat.BEAM_B*s)}" class="beam"/>')
    for st in P.steps:
        o.append(f'<rect x="{f(X(st["v0"]))}" y="{f(Y(st["u1"]))}" width="{f((st["v1"]-st["v0"])*s)}" height="{f((st["u1"]-st["u0"])*s)}" class="step" data-tip="Escalón, contrahuella {plat.STEP_RISE*100:.1f} cm"/>')
    for p in P.piles:
        o.append(f'<rect x="{f(X(p["v"]-plat.PED/2))}" y="{f(Y(p["u"]+plat.PED/2))}" width="{f(plat.PED*s)}" height="{f(plat.PED*s)}" class="ped" '
                 f'data-tip="Pilote {p["id"]} ({p["kind"]}) · X {p["x"]:+.3f} · Y {p["y"]:+.3f}"/>')
        dx = 0.22 if p["v"] >= 0 else -0.22
        o.append(f'<text x="{f(X(p["v"]+dx))}" y="{f(Y(p["u"]+0.2))}" text-anchor="{"start" if dx > 0 else "end"}" class="t-pile">{p["id"]}</text>')
    nodes = [r["node"] for r in P.rows]
    ia, ib = nodes.index(P.D.door["a"]), nodes.index(P.D.door["b"])
    (ua, va), (ub, vb) = P.ring[ia], P.ring[ib]
    o.append(f'<line x1="{f(X(va))}" y1="{f(Y(ua))}" x2="{f(X(vb))}" y2="{f(Y(ub))}" class="door-plan"/>')
    o.append(f'<text x="{f(X(0))}" y="{f(Y(ua)+16)}" text-anchor="middle" class="t-door">PUERTA</text>')
    o.append(f'<text x="{f(X(0))}" y="{f(Y(-0.5))}" text-anchor="middle" class="t-muted">↑ eje de la puerta (u)</text>')
    o.append(f'<text x="{f(X(0.75))}" y="{f(Y(-2.3))}" text-anchor="middle" class="t-muted halo">vigas c/1.50 m</text>')
    o.append(f'<text x="{f(X(-0.75))}" y="{f(Y(-2.3))}" text-anchor="middle" class="t-muted halo">viguetas c/40 cm</text>')
    o.append("</svg>")
    return "".join(o)


def platform_section_svg(P):
    """Corte por el eje de la puerta (v = 0), del fondo de zapata al domo."""
    D = P.D; lv = P.levels
    s = 58
    umin = -3.45; umax = P.steps[-1]["u1"] + 0.35
    zmin, zmax = lv["footing_bottom"] - 0.12, 2.72
    W = (umax-umin)*s + 110; H = (zmax-zmin)*s + 16
    def X(u): return 10 + (u-umin)*s
    def Y(z): return 8 + (zmax-z)*s
    o = [f'<svg viewBox="0 0 {f(W)} {f(H)}" role="img" aria-label="Corte de la plataforma por el eje de la puerta">']
    o.append(f'<rect x="{f(X(umin))}" y="{f(Y(lv["ground"]))}" width="{f((umax-umin)*s)}" height="{f((lv["ground"]-zmin)*s)}" class="soil"/>')
    o.append(f'<line x1="{f(X(umin))}" y1="{f(Y(lv["ground"]))}" x2="{f(X(umax))}" y2="{f(Y(lv["ground"]))}" class="ground"/>')
    # pilotes en (o proyectados sobre) el corte
    sec_piles = [p for p in P.piles if abs(p["v"]) < 0.05]
    proj = [p for p in P.piles if p["kind"] == "descanso"][:1] + \
           [p for p in P.piles if p["kind"] == "perimetral" and p["anchor"] == D.door["a"]]
    for p, cls in [(p, "") for p in sec_piles] + [(p, " proj") for p in proj]:
        top = lv["ring_bottom"] if p["kind"] == "perimetral" else lv["beam_bottom"]
        o.append(f'<rect x="{f(X(p["u"]-plat.FOOT/2))}" y="{f(Y(lv["footing_top"]))}" width="{f(plat.FOOT*s)}" height="{f(plat.FOOT_T*s)}" class="conc{cls}"/>')
        o.append(f'<rect x="{f(X(p["u"]-plat.PED/2))}" y="{f(Y(top))}" width="{f(plat.PED*s)}" height="{f((top-lv["footing_top"])*s)}" class="conc{cls}" '
                 f'data-tip="Pilote {p["id"]}{" (proyectado)" if cls else ""}: pedestal 25×25, zapata 50×50×20"/>')
    # viga de anillo donde el corte la cruza
    for u in (P.ring[[r["node"] for r in P.rows].index(D.door["a"])][0],
              min(P.ring, key=lambda q: abs(q[1]) + (0 if q[0] < 0 else 99))[0]):
        o.append(f'<rect x="{f(X(u-plat.RING_B/2))}" y="{f(Y(0))}" width="{f(plat.RING_B*s)}" height="{f(plat.RING_H*s)}" class="conc" data-tip="Viga de anillo 25×30"/>')
    bm = [b for b in P.beams if b["v"] == 0.0][0]
    o.append(f'<rect x="{f(X(bm["u0"]))}" y="{f(Y(lv["beam_top"]))}" width="{f((bm["u1"]-bm["u0"])*s)}" height="{f(plat.BEAM_H*s)}" class="beam" data-tip="Viga principal 100×50×3"/>')
    for j in P.joists:
        o.append(f'<rect x="{f(X(j["u"]-plat.JOIST_B/2))}" y="{f(Y(lv["joist_top"]))}" width="{f(max(1.5, plat.JOIST_B*s))}" height="{f(plat.JOIST_H*s)}" class="wood"/>')
    u_in = [q[0] for q in P.inner]
    o.append(f'<rect x="{f(X(bm["u0"]))}" y="{f(Y(0))}" width="{f((bm["u1"]-bm["u0"])*s)}" height="{f(plat.DECK_T*s)}" class="wood" data-tip="Entablado 1&quot;"/>')
    L = P.landing
    o.append(f'<rect x="{f(X(L["u0"]))}" y="{f(Y(lv["joist_top"]))}" width="{f((L["beam_u"]-L["u0"])*s)}" height="{f(plat.JOIST_H*s)}" class="wood"/>')
    o.append(f'<rect x="{f(X(L["u0"]))}" y="{f(Y(0))}" width="{f((L["u1"]-L["u0"])*s)}" height="{f(plat.DECK_T*s)}" class="wood"/>')
    o.append(f'<rect x="{f(X(L["beam_u"]-plat.BEAM_B/2))}" y="{f(Y(lv["beam_top"]))}" width="{f(plat.BEAM_B*s)}" height="{f(plat.BEAM_H*s)}" class="beam"/>')
    for st in P.steps:
        o.append(f'<rect x="{f(X(st["u0"]))}" y="{f(Y(st["z"]+plat.STEP_RISE))}" width="{f((st["u1"]-st["u0"])*s)}" height="{f((st["z"]+plat.STEP_RISE-lv["ground"])*s)}" class="stepsec"/>')
    # domo sobre la plataforma: perfil por v = 0 hasta el nodo sobre el vestibulo, techo, poste
    R = D.R; z0 = -D.center[2]
    top = D.door["top"]; ut = D.uv(D.verts[top])[0]; zt = D.verts[top][2]
    ub = min(P.ring, key=lambda q: abs(q[1]) + (0 if q[0] < 0 else 99))[0]
    arc = " ".join(f"{f(X(u))},{f(Y(math.sqrt(R*R-u*u)-z0))}" for u in [ub + i*(ut-ub)/60 for i in range(61)])
    o.append(f'<polyline points="{arc}" class="dome-outline"/>')
    ua = P.ring[[r["node"] for r in P.rows].index(D.door["a"])][0]
    o.append(f'<line x1="{f(X(ut))}" y1="{f(Y(zt))}" x2="{f(X(ua))}" y2="{f(Y(D.door["head_z"]))}" class="door-member"/>')
    o.append(f'<rect x="{f(X(ua-door.FRAME_B/2))}" y="{f(Y(D.door["head_z"]))}" width="{f(door.FRAME_B*s)}" height="{f(D.door["head_z"]*s)}" class="frame"/>')
    for z, lab in ((0.0, "±0.00 piso"), (lv["beam_bottom"], f"{lv['beam_bottom']:+.2f} fondo de vigas"),
                   (lv["ground"], f"{lv['ground']:+.2f} terreno"), (lv["footing_top"], f"{lv['footing_top']:+.2f} tope de zapata"),
                   (lv["footing_bottom"], f"{lv['footing_bottom']:+.2f} fondo de zapata")):
        o.append(f'<line x1="{f(X(umax)-4)}" y1="{f(Y(z))}" x2="{f(X(umax)+6)}" y2="{f(Y(z))}" class="dim"/>')
        o.append(f'<text x="{f(X(umax)+9)}" y="{f(Y(z)+4)}" class="t-lev">{lab}</text>')
    o.append(f'<text x="{f(X(0))}" y="{f(Y(1.4))}" text-anchor="middle" class="t-muted">interior del domo</text>')
    o.append(f'<text x="{f(X((L["u0"]+P.steps[-1]["u1"])/2))}" y="{f(Y(0.35))}" text-anchor="middle" class="t-muted">descanso</text>')
    o.append("</svg>")
    return "".join(o)


def platform_html(P, R, Q, checks):
    lv = P.levels
    pile_rows = "".join(
        f"<tr><td class='mono'>{r['id']}</td><td>{r['kind']}{(' · anclaje #' + str(r['anchor'])) if r['anchor'] is not None else ''}</td>"
        f"<td class='num'>{r['x']:+.3f}</td><td class='num'>{r['y']:+.3f}</td><td class='num'>{r['u']:+.3f}</td><td class='num'>{r['v']:+.3f}</td>"
        f"<td class='num'>{(lv['ring_bottom'] if r['kind'] == 'perimetral' else lv['beam_bottom']):+.3f}</td>"
        f"<td class='num'>{r['service']:.0f}</td><td class='num'>{r['pressure']/1e4:.2f}</td></tr>" for r in R["piles"])
    conc = Q["concrete"]; rebar = Q["rebar"]
    conc_rows = "".join(f"<tr><td>{k}</td><td class='num'>{v:.2f} m³</td></tr>" for k, v in conc.items())
    rebar_rows = "".join(f"<tr><td>{k}</td><td class='num'>{v:.0f} kg</td></tr>" for k, v in rebar.items())
    st = Q["steel"]; wd = Q["wood"]
    beams = st["tubo rectangular 100×50×3 (vigas)"]
    joists = wd["vigueta 2×4\" pino tratado"]
    deck = wd["entablado machihembrado 1\""]
    chk = "".join(f"<li class='{'okli' if c['ok'] else 'badli'}'>{'✓' if c['ok'] else '✕'} {esc(c['name'])}<span class='muted'> — {esc(c['detail'])}</span></li>" for c in checks)
    m = R["metrics"]
    n_per = sum(1 for p in P.piles if p["kind"] == "perimetral"); n_int = sum(1 for p in P.piles if p["kind"] == "interior")
    n_des = sum(1 for p in P.piles if p["kind"] == "descanso")
    return f"""<section id="plataforma">
  <div class="sec-head"><h2>Plataforma del piso y pilotes</h2></div>
  <p class="sec-sub">Piso elevado {plat.FREEBOARD*100:.0f} cm sobre el terreno, por las crecidas y para ventilar la madera. <b>{len(P.piles)} pilotes</b>: {n_per} bajo los anclajes del domo (cada perno baja directo a su pilote), {n_int} interiores y {n_des} del descanso de entrada. El jacuzzi no va aquí: va en la terraza, con fundación propia.</p>
  <div class="twocol">
    <div class="panel"><h3>Planta (eje de la puerta hacia arriba)</h3>{platform_plan_svg(P)}
      <div class="legend"><span><i class="swb" style="background:var(--conc)"></i>concreto</span><span><i class="swb" style="background:var(--steel)"></i>acero</span><span><i class="swb" style="background:var(--wood)"></i>madera</span></div></div>
    <div>
      <div class="tbl" style="margin-top:0"><table><thead><tr><th>Elemento</th><th>Especificación</th></tr></thead><tbody>
        <tr><td>Pilote</td><td>Pedestal de concreto 25×25 cm (4 Ø12, estribos Ø8 c/15) sobre zapata 50×50×20 cm (parrilla Ø10 c/15), fondo a {plat.FOOTING_DEPTH:.2f} m bajo el terreno <b>a confirmar con estudio de suelo</b></td></tr>
        <tr><td>Viga de anillo</td><td>Concreto armado 25×30 cm, 2 Ø12 por cara, estribos Ø8 c/15, cara superior = piso ±0.00. Lleva los 15 pernos del domo</td></tr>
        <tr><td>Vigas principales</td><td>Tubo rectangular 100×50×3, a v = −1.50 / 0 / +1.50 m, apoyadas en el anillo y en pilotes a u = ±1.00 m</td></tr>
        <tr><td>Viguetas</td><td>Pino tratado 2×4" cada 40 cm, apoyadas en las vigas y en un angular 50×50×5 fijado al anillo</td></tr>
        <tr><td>Entablado</td><td>Machihembrado de 1" (o contrachapado marino de 18 mm)</td></tr>
        <tr><td>Descanso</td><td>{plat.LANDING_W:.2f} × {plat.LANDING_D:.2f} m al nivel del piso, 3 escalones de {plat.STEP_RISE*100:.1f} cm</td></tr>
      </tbody></table></div>
    </div>
  </div>
  <div class="panel" style="margin-top:14px"><h3>Corte por el eje de la puerta</h3>{platform_section_svg(P)}</div>
  <h3 class="sub">Replanteo de los pilotes</h3>
  <p class="small muted">X/Y en el mismo sistema que los anclajes (origen en el centro, 0° en el primer nodo alto). u/v a lo largo del eje de la puerta y perpendicular. Carga en servicio incluye el peso del pilote; presión bajo la zapata de 50×50.</p>
  <div class="tbl"><table><thead><tr><th>Pilote</th><th>Tipo</th><th class="num">X (m)</th><th class="num">Y (m)</th><th class="num">u (m)</th><th class="num">v (m)</th><th class="num">Cara sup.</th><th class="num">Carga kgf</th><th class="num">kgf/cm²</th></tr></thead><tbody>{pile_rows}</tbody></table></div>
  <div class="twocol">
    <div>
      <h3>Materiales</h3>
      <div class="tbl"><table><tbody>
        {conc_rows}<tr class="total"><td>Concreto total (sin desperdicio)</td><td class="num">{sum(conc.values()):.2f} m³</td></tr>
        {rebar_rows}<tr class="total"><td>Acero de refuerzo (estimado)</td><td class="num">{sum(rebar.values()):.0f} kg</td></tr>
        <tr><td>Tubo rectangular 100×50×3 (vigas)</td><td class="num">{beams['barras6m']} barras de 6 m</td></tr>
        <tr><td>Angular 50×50×5 (apoyo de viguetas)</td><td class="num">{st['angular L 50×50×5 (apoyo de viguetas en la viga de anillo)']['barras6m']} barras de 6 m</td></tr>
        <tr><td>Placas 150×150×8 con 2 pernos (cabeza de pilotes)</td><td class="num">8</td></tr>
        <tr><td>Asientos L 75×75×6 (extremos de vigas)</td><td class="num">{2*len(P.beams)}</td></tr>
        <tr><td>Viguetas 2×4" pino tratado</td><td class="num">{joists['tablas_10pies']} piezas de 10 pies</td></tr>
        <tr><td>Entablado 1" (+15%)</td><td class="num">{deck['m2_con_desperdicio']:.1f} m²</td></tr>
      </tbody></table></div>
    </div>
    <div>
      <h3>Verificación (<span class="mono">python3 dome_platform.py</span>)</h3>
      <ul class="checks">{chk}</ul>
      <p class="small muted">Cargas: {plat.LIVE_ROOM:.0f} kgf/m² en la habitación, {plat.LIVE_LANDING:.0f} en el descanso, {plat.DEAD_FLOOR:.0f} de peso propio del piso. El arranque del viento sale de las reacciones del domo con puerta. Sismo con Ao 0.30 y la meseta del espectro, sin reducción. La capacidad del suelo ({plat.Q_ADM/1e4:.1f} kgf/cm²) es un supuesto: la confirma el estudio de suelo.</p>
    </div>
  </div>
</section>
"""


# ------------------------------------------------------------------ pagina

def build_page():
    D, A, steps = collect()
    PL, PR, PQ, PCHK = plat.evaluate(verbose=False)
    dd = D.door
    P = D.verts
    rows = seq.setting_out(D)
    panels = panel_groups(D)
    mem_area = sum(p["area"]*p["n"] for p in panels)
    seam5 = seam_area(panels, 0.05)
    steel_kg, mem_kg = dead_weight(D)
    types = {t["name"]: t for t in D.hub_types}
    round_m = sum(D.edge_len[e] for e in D.edges if door.MEMBER_INFO[D.edge_label[e]][0] == "tubo32x2")

    # ---- 3D: la misma escena que la maqueta, mas los datos de cada pieza para tocarla
    data3d = escena3d.scene_data(D, PL)
    by_edge = {tuple(sorted((p["from"], p["to"]))): p for p in escena3d.sequence_pieces(D, steps)}
    for s3, e in zip(data3d["struts"], D.edges):
        sp = by_edge[tuple(sorted(e))]
        s3.update({"i": [sp["from"], sp["to"]], "L": round(D.edge_len[e], 4), "id": sp["id"], "step": sp["step"]})
    for n in data3d["nodes"]:
        n["tt"] = seq.hub_type_of(D, n["id"])
        n["d"] = HUB_DESC.get(n["t"], "")
    pcs = [{p["code"]: p for p in door.pieces(D, sb)} for sb in SETBACKS]
    data3d["info"] = {c: {"desc": p["desc"], "section": p["section"], "note": p.get("note", ""),
                          "cut": [round(x[c]["cut"], 4) for x in pcs]} for c, p in pcs[0].items()}
    data3d["sb"] = list(SETBACKS)
    step_names = []
    for s_ in steps:
        if s_["kind"] == "fundacion":
            name = f"Base: {len(D.boundary_verts)} anclajes y el anillo de base"
        elif set(s_["new_hubs"]) == {dd["Ta"], dd["Tb"]}:
            name = "Marco de la puerta y amarres K1, K2"
        elif len(s_["new_hubs"]) == 1:
            name = f"Ápice (#{s_['new_hubs'][0]})"
        else:
            name = f"Anillo de {len(s_['new_hubs'])} nodos a {s_['height_m']:.3f} m"
        step_names.append({"n": s_["ring"], "name": name, "bars": len(s_["edges"])})
    data3d["steps"] = step_names

    # ---- piezas y corte por retiro
    cut_blocks = []
    for i, sb in enumerate(SETBACKS):
        pcs = door.pieces(D, sb)
        plan = door.cut_plan(D, sb)
        pats = Counter(tuple(sorted(b, key=lambda c: ("ABCVK".find(c[0]), c))) for b in plan["bars"])
        rows_html = "".join(
            f"<tr><td>{code_chip(p['code'])}</td><td>{esc(p['desc'])}</td>"
            f"<td>{esc(p['section'])}</td><td class='num'>{p['n']}</td><td class='num'>{p['L_cc']*100:.2f}</td>"
            f"<td class='num strong'>{p['cut']*100:.2f}</td><td class='small muted'>{esc(p.get('note', 'L − 2 × retiro'))}</td></tr>"
            for p in pcs)
        bars_html = "".join(
            f"<div class='cutrow'><div class='cutlabel'>× {n} barra{'s' if n > 1 else ''}</div>{cutbar_svg(list(pat), plan['lengths'])}"
            f"<div class='cutnote'>sobran {(6-sum(plan['lengths'][k]+0.003 for k in pat))*1000:.0f} mm</div></div>"
            for pat, n in sorted(pats.items(), key=lambda kv: -kv[1]))
        cut_blocks.append(f"""<div class="cutblock" data-sb="{i}" {'' if i == 1 else 'hidden'}>
  <div class="tbl"><table><thead><tr><th>Pieza</th><th>Qué es</th><th>Tubo</th><th class="num">Cant.</th><th class="num">Centro a centro (cm)</th><th class="num">Cortar a (cm)</th><th>Nota</th></tr></thead><tbody>{rows_html}</tbody></table></div>
  <p class="sum"><b>{plan['n_bars']} barras de 6 m</b> de tubo redondo 32×2 (desperdicio {plan['waste_pct']:.1f}%, al menos {plan['min_slack_mm']:.0f} mm de sobra en cada barra) <b>+ 1 barra de 6 m</b> de tubo cuadrado 50×50×2 para el marco.</p>
  <div class="panel cuts">{bars_html}</div>
</div>""")

    # ---- nodos
    def hub_card(name, prefer=("C",)):
        t = types[name]
        v = t["hub_ids"][0]
        side_ids = t["hub_ids"]
        g = door.hub_geometry(D, v)
        mem, gaps = rotate_start(g["members"], g["az_gaps"], g["open"], prefer)
        nodes = ", ".join(f"#{x}{'-' + D.side[x] if x in D.side else ''}" for x in side_ids)
        tot = sum(gaps[:len(mem) - (1 if g['open'] else 0)])
        mirror = "<p class='small muted'>El nodo <b>-der</b> es la imagen espejo: mismas pestañas en el orden contrario.</p>" if any(x in D.side for x in side_ids) else ""
        desc = HUB_DESC.get(name, "")
        return (f"<figure class='hubcard'><div class='hh'><b>{name}</b><span class='muted'>× {t['count']}</span></div>"
                f"<div class='small muted'>{esc(desc)}</div>{disc_svg(mem, gaps, g['open'], name)}"
                f"<div class='small'>Nodos: <span class='mono'>{nodes}</span></div>"
                f"<div class='small muted'>{len(mem)} barras · azimuts suman {tot:.2f}°{' + abierto' if g['open'] else ''}</div>{mirror}</figure>")

    std_cards = "".join(hub_card(n) for n in ["H1", "H2", "H3", "H4", "H5"])
    door_cards = "".join(hub_card(n, prefer=("P", "K1", "K2", "V")) for n in ["PA", "PB", "PC", "PD"])
    ge = door.hub_geometry(D, dd["Ta"])
    def plan_txt(m):
        return "vertical" if m["plan_from_head_deg"] is None else f"{m['plan_from_head_deg']:.1f}°"
    pe_rows = "".join(
        f"<tr><td>{code_chip(m['label'])}</td><td class='mono'>#{m['to']}</td>"
        f"<td class='num'>{m['len']*100:.2f}</td><td class='num'>{plan_txt(m)}</td>"
        f"<td class='num'>{m['slope_deg']:+.1f}°</td></tr>" for m in ge["members"])

    # ---- armado
    step_rows = []
    for s_ in steps:
        if s_["kind"] == "fundacion":
            step_rows.append(f"<tr><td class='num'>0</td><td>Fundación: 15 anclajes (replanteo abajo) y 15 barras de la base</td><td class='num'>0</td>"
                             f"<td class='num'>{len(s_['edges'])}</td><td>—</td></tr>")
            continue
        frame = set(s_["new_hubs"]) == {dd["Ta"], dd["Tb"]}
        later = [v for v in s_["needs_bracing"] if v in s_["unfixed_at_end"]]
        within = [v for v in s_["needs_bracing"] if v not in s_["unfixed_at_end"]]
        note = []
        if later:
            note.append("<span class='warn'>▲ puntal hasta el paso siguiente: " + ", ".join(f"#{v}" for v in later) + "</span>")
        if within:
            note.append("<span class='warn2'>◆ sujetar hasta soldar las barras del paso: " + ", ".join(f"#{v}" for v in within) + "</span>")
        what = "Marco de la puerta (soldado en taller) + amarres K1 y K2" if frame else f"Anillo de {len(s_['new_hubs'])} nodo{'s' if len(s_['new_hubs']) > 1 else ''}"
        step_rows.append(f"<tr><td class='num'>{s_['ring']}</td><td>{what}</td><td class='num'>{s_['height_m']:.3f}</td>"
                         f"<td class='num'>{len(s_['edges'])}</td><td>{'<br>'.join(note) or '—'}</td></tr>")

    # ---- anclajes
    anc_rows = "".join(
        f"<tr{' class=hl' if r['node'] in (dd['a'], dd['b']) else ''}><td class='mono'>#{r['node']}</td><td>{seq.hub_type_of(D, r['node'])}</td>"
        f"<td class='num'>{r['az']:.3f}°</td><td class='num'>{r['r']:.4f}</td><td class='num'>{r['x']:+.4f}</td><td class='num'>{r['y']:+.4f}</td>"
        f"<td class='num'>{r['dz']*100:+.2f} cm</td><td class='num'>{A['anc'][r['node']]['up']/G:.0f}</td><td class='num'>{A['anc'][r['node']]['shear']/G:.0f}</td></tr>"
        for r in rows)

    # ---- cubierta
    pan_rows = "".join(
        f"<tr><td><b>{p['name']}</b>{' <span class=muted>(vestíbulo)</span>' if p['vest'] else ''}</td>"
        f"<td class='num'>{' · '.join(f'{x*100:.1f}' for x in p['sides'])}</td><td class='num'>{' · '.join(f'{a:.2f}°' for a in p['angs'])}</td>"
        f"<td class='num'>{p['area']:.3f}</td><td class='num'>{p['n']}</td><td class='num'>{p['area']*p['n']:.2f}</td></tr>" for p in panels)

    # ---- cargas
    env = A["env"]
    worst = max(D.edges, key=lambda e: env[e]["comp"]/door.aisc_phiPn(door.section_of(D, e), D.edge_len[e])[0])
    wcap = door.aisc_phiPn(door.section_of(D, worst), D.edge_len[worst])[0]
    up = max(x["up"] for x in A["anc"].values()); sh = max(x["shear"] for x in A["anc"].values())
    up0 = max(x["up"] for x in A["anc0"].values()); sh0 = max(x["shear"] for x in A["anc0"].values())
    fb = door.bending_door_frame(D, A["q"])
    Ab = math.pi/4*0.012**2
    bolt_t, bolt_v = 0.75*310e6*Ab/(up*2.5), 0.75*188e6*Ab/(sh*2.0)
    bolt_t0, bolt_v0 = 0.75*310e6*Ab/(up0*2.5), 0.75*188e6*Ab/(sh0*2.0)
    ms_clear = door.bending_door_frame(D, 1.0)

    counts = Counter(D.edge_label.values())
    dome_bars = counts["A"] + counts["B"] + counts["C"]
    door_bars = sum(v for k, v in counts.items() if k in DOOR_CODES)

    # ---- alternativa de tubo: cuadrado 1x1 contra el redondo 32x2
    tubes = comparar_tubos.compare()
    fy = comparar_tubos.FY/1e6
    tube_rows = "".join(
        f"<tr><td class='nw'>{'<b>' + esc(t['name']) + '</b>' if i == 0 else esc(t['name'])}</td><td class='num'>{t['kg_m']:.2f}</td><td class='num'>{t['kg']:.0f} kg</td>"
        f"<td class='num'>{t['cap_A_kgf']:.0f} kgf</td><td class='num'>{t['worst']['comp']/G:.0f} kgf ({t['worst']['ut']*100:.0f}%)</td>"
        f"<td class='num'>{t['sigma_person']/fy*100:.0f}% de fluencia</td><td class='num'>{t['kg_m']*6:.1f} kg</td></tr>" for i, t in enumerate(tubes))
    thin = min((t for t in tubes if "1×1" in t["name"]), key=lambda t: t["t"])
    big = next(t for t in tubes if t["name"].startswith("redondo 2"))

    css = CSS
    js = JS.replace("__DATA__", json.dumps(data3d, separators=(",", ":")))
    return f"""<title>Domo Cucuchica · Plano de taller</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>{css}</style>
<div class="wrap">
<header class="top"><div class="top-inner">
  <div class="brand">DOMO 3V <span class="dim">/ CUCUCHICA · PLANO DE TALLER</span></div>
  <nav class="jump"><a href="#vista">Vista 3D</a><a href="#piezas">Piezas y corte</a><a href="#nodos">Nodos</a><a href="#puerta">Puerta</a><a href="#base">Base</a><a href="#plataforma">Plataforma</a><a href="#armado">Armado</a><a href="#cubierta">Cubierta</a><a href="#cargas">Cargas</a><a href="#notas">Notas</a></nav>
</div></header>

<section class="hero" id="resumen">
  <div class="eyebrow">Glamping Cucuchica · domo geodésico 3V ⌀6 m con puerta · generado desde el modelo verificado</div>
  <h1>Domo de 6 m con portal de entrada</h1>
  <p class="lede">Todo lo necesario para cortar, soldar y armar la estructura: piezas y plan de corte, plantillas de cada disco de nodo, el marco de la puerta, el replanteo de los anclajes y el orden de armado. Cada número sale del mismo modelo que pasó la auditoría independiente; esta página se regenera con <span class="mono">python3 dome_viewer.py</span>.</p>
  <div class="statgrid">
    <div class="stat"><div class="v">6.00<span class="u">m</span></div><div class="l">Diámetro de base (anclajes bajos)</div></div>
    <div class="stat"><div class="v">2.52<span class="u">m</span></div><div class="l">Altura al ápice</div></div>
    <div class="stat"><div class="v">{int(ms_clear['clear_w']*100)}×{int(ms_clear['clear_h']*100)}<span class="u">cm</span></div><div class="l">Vano libre de la puerta</div></div>
    <div class="stat"><div class="v">{len(PL.piles)}</div><div class="l">Pilotes (piso de 28.3 m² a {plat.FREEBOARD*100:.0f} cm del suelo)</div></div>
    <div class="stat"><div class="v">{dome_bars}+{door_bars}</div><div class="l">Barras del domo + piezas de la puerta</div></div>
    <div class="stat"><div class="v">{len(D.active)}</div><div class="l">Nodos ({len(D.boundary_verts)} anclados)</div></div>
    <div class="stat"><div class="v">{round_m:.1f}<span class="u">m</span></div><div class="l">Tubo 32×2 (centro a centro)</div></div>
    <div class="stat"><div class="v">{steel_kg:.0f}<span class="u">kg</span></div><div class="l">Acero (sin soldadura ni pernos)</div></div>
  </div>
  <div class="card note warn"><h3>Antes de cortar</h3><p>Falta decidir cómo se une cada barra al disco del nodo. De eso depende el <b>retiro</b> que se le resta a cada barra (mínimo 3.1 cm, porque los tubos chocan en los nodos de 54.6°). Arme primero <b>un nodo de prueba</b> con una barra de cada tipo, mida el retiro real y recién ahí corte el lote completo.</p></div>
</section>

<section id="vista">
  <div class="sec-head"><h2>Vista 3D</h2></div>
  <p class="sec-sub">El domo armado completo, a escala real, con la plataforma. Arrastre para girar; rueda, pellizco o los botones + y − para acercar y alejar; clic derecho o dos dedos para desplazar. Toque una barra o un nodo para ver su código, su largo y en qué paso se arma.</p>
  <div class="viewer" id="viewer">
    <div id="scene" role="img" aria-label="Vista 3D del domo con la puerta y la plataforma">
      <div id="labels" aria-hidden="true" hidden></div>
      <div class="views" role="group" aria-label="Vistas">
        <button type="button" class="vbtn" data-view="tres">3/4</button><button type="button" class="vbtn" data-view="frente">Frente</button><button type="button" class="vbtn" data-view="lado">Lado</button><button type="button" class="vbtn" data-view="planta">Planta</button><button type="button" class="vbtn" data-view="adentro">Adentro</button>
      </div>
      <div class="zoomctl" role="group" aria-label="Zoom">
        <button type="button" class="iconbtn" id="z-in" title="Acercar" aria-label="Acercar"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 4v12M4 10h12"/></svg></button>
        <button type="button" class="iconbtn" id="z-out" title="Alejar" aria-label="Alejar"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h12"/></svg></button>
        <button type="button" class="iconbtn" id="z-fit" title="Vista inicial" aria-label="Vista inicial"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 7V3h4M13 3h4v4M17 13v4h-4M7 17H3v-4"/></svg></button>
        <button type="button" class="iconbtn" id="z-full" title="Pantalla completa" aria-label="Pantalla completa" hidden><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 8V3h5M3 3l5 5M17 12v5h-5M17 17l-5-5"/></svg></button>
      </div>
      <div id="pick" hidden></div>
      <div id="hubTip" hidden></div>
      <div id="nogl" hidden>Este navegador no pudo abrir la vista 3D (WebGL). El resto del plano funciona igual.</div>
    </div>
    <div class="filters">
      <div class="frow"><span class="flab">Barras</span>
        <label class="chip"><input type="checkbox" data-f="A" checked><i style="background:var(--sA)"></i>A <span class="muted">× {counts["A"]}</span></label>
        <label class="chip"><input type="checkbox" data-f="B" checked><i style="background:var(--sB)"></i>B <span class="muted">× {counts["B"]}</span></label>
        <label class="chip"><input type="checkbox" data-f="C" checked><i style="background:var(--sC)"></i>C <span class="muted">× {counts["C"]}</span></label>
        <label class="chip"><input type="checkbox" data-f="door" checked><i style="background:var(--door)"></i>Puerta P D V K <span class="muted">× {door_bars}</span></label>
      </div>
      <div class="frow"><span class="flab">Mostrar</span>
        <label class="chip"><input type="checkbox" id="t-hub" checked>discos de nodo</label>
        <label class="chip"><input type="checkbox" id="t-num">números de nodo</label>
        <label class="chip"><input type="checkbox" id="t-leaf" checked>hoja de la puerta</label>
        <label class="chip"><input type="checkbox" id="t-mem">membrana</label>
        <label class="chip"><input type="checkbox" id="t-plat" checked>plataforma</label>
        <label class="chip"><input type="checkbox" id="t-und">pilotes bajo tierra</label>
        <label class="chip"><input type="checkbox" id="t-people">persona y cama</label>
      </div>
      <div class="frow"><span class="flab">Color</span>
        <div class="cmode" role="group" aria-label="Color de las barras"><button type="button" data-c="acero" aria-pressed="true">acero</button><button type="button" data-c="tipo" aria-pressed="false">por tipo de barra</button></div>
      </div>
      <div class="frow"><span class="flab">Armado</span>
        <input type="range" id="t-step" min="0" max="{len(steps) - 1}" value="{len(steps) - 1}" step="1" aria-label="Armado hasta el paso">
        <button type="button" class="vbtn" id="t-play">▶ animar</button>
        <span id="stepname" class="small"></span>
      </div>
    </div>
  </div>
</section>

<section id="piezas">
  <div class="sec-head"><h2>Piezas y plan de corte</h2></div>
  <p class="sec-sub">Largos de centro de nodo a centro de nodo, y el largo de corte según el retiro por extremo que resulte del nodo de prueba. Plan de corte en barras comerciales de 6 m con 3 mm de disco por corte.</p>
  <div class="seg" role="group" aria-label="Retiro por extremo">
    <span class="seg-l">Retiro por extremo:</span>
    {''.join(f'<button type="button" class="segbtn" data-sb="{i}" aria-pressed="{str(i == 1).lower()}">{sb*100:.1f} cm</button>' for i, sb in enumerate(SETBACKS))}
  </div>
  {''.join(cut_blocks)}
</section>

<section id="nodos">
  <div class="sec-head"><h2>Plantillas de los discos de nodo</h2></div>
  <p class="sec-sub">Cada dibujo es el disco visto desde afuera del domo. El número en cada arco es el <b>azimut</b> a marcar entre pestañas consecutivas; al lado de cada barra va su <b>inclinación</b> respecto al disco (negativa = hacia adentro del domo, positiva = hacia afuera). Los azimuts de los nodos cerrados suman 360°.</p>
  <h3 class="sub">Nodos estándar</h3>
  <div class="hubgrid">{std_cards}</div>
  <h3 class="sub">Nodos especiales alrededor de la puerta</h3>
  <p class="small muted">Se fabrican de a pares: izquierda y derecha (mirando la puerta desde afuera). Las pestañas de la puerta (P, K1, K2, V) salen hacia afuera del disco, con inclinación positiva.</p>
  <div class="hubgrid">{door_cards}</div>
  <h3 class="sub">PE · esquinas del marco (#{dd['Ta']}-izq, #{dd['Tb']}-der)</h3>
  <p class="small muted">No llevan disco: las pestañas se sueldan directo a la esquina del marco de 50×50. Ángulo en planta medido desde el dintel, girando hacia adentro del domo; pendiente respecto a la horizontal. La esquina derecha es espejo.</p>
  <div class="tbl narrow"><table><thead><tr><th>Pieza</th><th>Va a</th><th class="num">Largo c-c (cm)</th><th class="num">En planta</th><th class="num">Pendiente</th></tr></thead><tbody>{pe_rows}</tbody></table></div>
</section>

<section id="puerta">
  <div class="sec-head"><h2>Puerta · portal de acceso</h2></div>
  <p class="sec-sub">El domo mide 2.52 m en el centro y baja hasta el piso en el borde, así que la puerta necesita un pequeño techo de vestíbulo que entra al domo hasta donde el techo ya pasa de 2 m. El marco se apoya en dos anclajes que ya existen (#{dd['a']} y #{dd['b']}), así que no hay anclajes nuevos.</p>
  <div class="twocol">
    <div class="panel"><h3>Vista de frente (desde afuera)</h3>{door_elevation_svg(D)}</div>
    <div class="panel"><h3>Corte por el eje de la puerta</h3>{door_section_svg(D)}</div>
  </div>
  <div class="twocol">
    <div>
      <h3>Qué cambia en el domo</h3>
      <ul class="plain">
        <li>Se quitan los nodos <b>#{dd['removed_nodes'][0]}</b> y <b>#{dd['removed_nodes'][1]}</b> y sus <b>{len(dd['removed_edges'])} barras</b> (2 A, 3 B, 5 C).</li>
        <li>La barra B del piso entre #{dd['a']} y #{dd['b']} <b>se queda</b>: es el umbral y amarra la base de los postes.</li>
        <li>Se agregan <b>9 piezas</b>: 2 postes P y 1 dintel D (tubo cuadrado 50×50×2), 2 vigas V del techo, y 4 amarres K1 y K2 (tubo 32×2).</li>
        <li>7 nodos del domo pasan a ser especiales (PA–PD) y aparecen 2 esquinas de marco (PE).</li>
        <li>La membrana pierde 9 paneles y gana 7 del vestíbulo (V1–V4).</li>
      </ul>
    </div>
    <div>
      <h3>Puerta a comprar o fabricar</h3>
      <ul class="plain">
        <li>Vano libre del marco: <b>{ms_clear['clear_w']*100:.1f} × {ms_clear['clear_h']*100:.1f} cm</b>.</li>
        <li>Opciones: puerta de 100 × 200 cm con su marco + un fijo lateral de unos 15 cm, o una puerta a medida de unos 115 × 205 cm.</li>
        <li>Si abre hacia afuera, poner retenedor: el viento no la debe poder golpear contra el domo.</li>
        <li>El techo del vestíbulo cae 13% hacia la puerta: <b>gotero o canalito sobre el dintel</b>.</li>
        <li>La membrana se sella al marco con solapa y cinta; el marco queda por fuera de la tela.</li>
      </ul>
    </div>
  </div>
  <div class="card note"><h3>Verificación de la puerta</h3><p>Paso libre revisado barra por barra y panel por panel: nada invade el paso. Cada nodo queda fijo con 3 barras o más no coplanares. Con viento de 100 km/h desde 12 direcciones, con la puerta abierta y cerrada, la barra más exigida trabaja al <b>{env[worst]['comp']/wcap*100:.0f}%</b> de su capacidad. Los postes de 50×50 llegan a {fb['sig_post']:.0f} MPa por el viento sobre la puerta cerrada; en tubo redondo 32×2 llegarían a unos 104 MPa, por eso el marco va en tubo cuadrado.</p></div>
</section>

<section id="base">
  <div class="sec-head"><h2>Base y replanteo de anclajes</h2></div>
  <p class="sec-sub">Origen en el centro del domo; 0° en el primer nodo alto; ángulos crecientes en sentido antihorario visto desde arriba. Los 5 nodos altos van 4.86 cm por encima de los demás (taco). Los anclajes #{dd['a']} y #{dd['b']} reciben además los postes de la puerta.</p>
  <div class="panel planpanel">{base_plan_svg(D, rows)}
    <div class="legend"><span><i class="swb" style="background:var(--ink)"></i>bajo H4</span><span><i class="swb" style="background:var(--sA)"></i>alto H5 (+4.86 cm)</span><span><i class="swb" style="background:var(--door)"></i>con poste de puerta</span></div>
  </div>
    <div class="tbl"><table><thead><tr><th>Nodo</th><th>Tipo</th><th class="num">Azimut</th><th class="num">Radio (m)</th><th class="num">X (m)</th><th class="num">Y (m)</th><th class="num">Sobre el piso</th><th class="num">Arranque kgf</th><th class="num">Corte kgf</th></tr></thead><tbody>{anc_rows}</tbody></table></div>
  <p class="small muted">Arranque y corte: máximos por anclaje con el viento ilustrativo de 100 km/h, sin factor de seguridad. Para la fundación los tiene que usar el ingeniero con los datos oficiales del sitio.</p>
</section>

{platform_html(PL, PR, PQ, PCHK)}
<section id="armado">
  <div class="sec-head"><h2>Orden de armado</h2></div>
  <p class="sec-sub">De la base al ápice, anillo por anillo. Alturas desde el piso. El detalle barra por barra está en <span class="mono">secuencia_de_armado.md</span>.</p>
  <div class="tbl"><table><thead><tr><th class="num">Paso</th><th>Qué se arma</th><th class="num">Altura (m)</th><th class="num">Barras</th><th>Sujeción temporal</th></tr></thead><tbody>{''.join(step_rows)}</tbody></table></div>
  <div class="card note warn"><h3>Nadie camina sobre las barras</h3><p>Una persona de 100 kg parada a media barra lleva el tubo de 32×2 al límite de fluencia. Armar y montar la membrana desde andamio o escalera. Los nodos marcados con ▲ quedan como bisagra: puntal o cuerda, y nadie debajo.</p></div>
</section>

<section id="cubierta">
  <div class="sec-head"><h2>Cubierta (membrana)</h2></div>
  <p class="sec-sub">Lados de cada panel de centro de nodo a centro de nodo. Al cortar la tela hay que sumar el solape de costura en cada borde.</p>
  <div class="tbl"><table><thead><tr><th>Panel</th><th class="num">Lados (cm)</th><th class="num">Ángulos</th><th class="num">Área c/u (m²)</th><th class="num">Cant.</th><th class="num">Total (m²)</th></tr></thead><tbody>{pan_rows}
    <tr class="total"><td>Total</td><td></td><td></td><td></td><td class="num">{len(D.triangles)}</td><td class="num">{mem_area:.2f}</td></tr></tbody></table></div>
  <p>Con 5 cm de solape por lado, las piezas cortadas suman <b>{seam5:.1f} m²</b>, sin contar lo que se pierde al acomodarlas en el rollo. <b>Presupuestar unos {math.floor(seam5)}–{math.ceil(seam5*1.1)} m²</b>, o pedir la cotización al fabricante con su propio patronaje. Aislante, forro interior y ventanas van aparte.</p>
</section>

<section id="cargas">
  <div class="sec-head"><h2>Cargas (orden de magnitud)</h2></div>
  <p class="sec-sub">Armadura espacial con nodos articulados, peso propio, una persona en el ápice o colgada del dintel, y viento ilustrativo de 100 km/h desde 12 direcciones con la puerta abierta y cerrada. No sustituye la firma del ingeniero.</p>
  <div class="tbl"><table><thead><tr><th>Dato</th><th class="num">Con puerta</th><th class="num">Sin puerta</th></tr></thead><tbody>
    <tr><td>Peso de la estructura de acero + membrana</td><td class="num">{steel_kg+mem_kg:.0f} kg</td><td class="num">278 kg</td></tr>
    <tr><td>Barra más exigida a compresión (% de su capacidad)</td><td class="num">{env[worst]['comp']/G:.0f} kgf ({env[worst]['comp']/wcap*100:.0f}%)</td><td class="num">{max(x['comp'] for x in A['env0'].values())/G:.0f} kgf</td></tr>
    <tr><td>Arranque máximo en un anclaje</td><td class="num">{up/G:.0f} kgf</td><td class="num">{up0/G:.0f} kgf</td></tr>
    <tr><td>Corte máximo en un anclaje</td><td class="num">{sh/G:.0f} kgf</td><td class="num">{sh0/G:.0f} kgf</td></tr>
    <tr><td>Perno M12 por anclaje: capacidad del acero / demanda con FS 2.5 (tracción) y 2.0 (corte)</td><td class="num">{bolt_t:.1f}× · {bolt_v:.1f}×</td><td class="num">{bolt_t0:.1f}× · {bolt_v0:.1f}×</td></tr>
  </tbody></table></div>
  <p class="small muted">La puerta sube el corte en los anclajes de los postes de unos {sh0/G:.0f} a {sh/G:.0f} kgf. El perno alcanza; el embebido en el concreto y el peso de los pilotes los define el ingeniero.</p>
  <h3 class="sub">¿Y con otro tubo?</h3>
  <p class="small">El mismo cálculo, con los 39 casos de carga, cambiando todas las barras redondas por otros tubos estructurales que se consiguen: redondo de 1¼" y de 2", y cuadrado de 1" (25.4 mm). "Capacidad" es la carga de diseño a compresión de la barra más larga (A); "persona a media barra" es un adulto de 100 kg parado en el medio de una barra A. El marco de la puerta sigue en 50×50×2. Se corre con <span class="mono">python3 comparar_tubos.py</span>.</p>
  <div class="tbl"><table><thead><tr><th>Tubo</th><th class="num">kg/m</th><th class="num">Peso barras</th><th class="num">Capacidad barra A</th><th class="num">Más cargada (uso)</th><th class="num">Persona a media barra</th><th class="num">Barra de 6 m pesa</th></tr></thead><tbody>{tube_rows}</tbody></table></div>
  <div class="card note"><h3>Qué dicen los números</h3><p>Con las cargas de este domo, el 1×1 alcanza con cualquier espesor. La barra más cargada lleva unos {tubes[0]['worst']['comp']/G:.0f} kgf, y hasta el 1×1 de {thin['t']:.1f} mm tiene una capacidad de {thin['cap_A_kgf']:.0f} kgf. Lo que cambia es la robustez: la pared de 0.9–1.1 mm se abolla con un golpe, se perfora al soldar con electrodo y el óxido la atraviesa antes, y una persona parada a media barra la dobla. <b>Mínimo 1×1 de 1.5 mm; con 2.0 mm queda igual que el redondo 32×2</b>, con el mismo peso. El redondo de 1¼" con 1.8 mm también sirve. El de 2" es mucho más fuerte (una persona a media barra llega al {big['sigma_person']/fy*100:.0f}% de la fluencia), pero lleva {(big['kg']/tubes[0]['kg']-1)*100:.0f}% más acero y los nodos salen más grandes: no hace falta. Para comparar publicaciones, la última columna sirve de control: si la barra pesa bastante menos, la pared es más delgada de lo que dice. Si se cambia, los largos de centro a centro no cambian; hay que regenerar este plano para los pesos y los dibujos de los nodos. Acero supuesto: Fy {fy:.0f} MPa, conservador.</p></div>
</section>

<section id="notas">
  <div class="sec-head"><h2>Notas de taller y pendientes</h2></div>
  <div class="notegrid">
    <div class="card note"><h3>Galvanizado</h3><p>No soldar tubo ya galvanizado: el zinc se quema en la unión. Si el domo se suelda en obra, reparar cada unión con galvanizado en frío (pintura rica en zinc), o hacer uniones empernadas y galvanizar en caliente las piezas ya soldadas en taller. Tubos cerrados: agujeros de venteo antes del baño en caliente.</p></div>
    <div class="card note"><h3>Tubo</h3><p>Redondo 32×2 (o 1¼" = 31.75 mm) y cuadrado 50×50×2, acero estructural. Confirmar con el proveedor el grado del acero y el espesor real de pared.</p></div>
    <div class="card note"><h3>Jacuzzi afuera</h3><p>El jacuzzi va en la terraza, fuera del domo, con su propia fundación: 1–2 t de agua no deben cargar la viga de anillo ni los pilotes del domo. Desaguar lejos de los pilotes.</p></div>
    <div class="card note warn"><h3>Pendiente antes de construir</h3><p>Diseño de la unión en el nodo y nodo de prueba · estudio de suelo: confirmar la capacidad supuesta de 1.0 kgf/cm² y la profundidad de zapata · resistencia real del concreto · viento y sismo oficiales para Tovar · firma de un ingeniero estructural matriculado.</p></div>
  </div>
</section>

<footer>Maqueta 1:10 de la estructura con palos chinos (prueba de las medidas): <a href="https://claude.ai/artifact/QzhQ4UyVbxqeMXogM7poM6">maqueta del domo</a> (en el repositorio: <span class="mono">maqueta/maqueta.html</span>).<br>Generado por <span class="mono">dome_viewer.py</span> desde <span class="mono">dome_model.py</span>, <span class="mono">dome_door.py</span> y <span class="mono">dome_build_sequence.py</span>. Verificación de la geometría: <span class="mono">dome_verify.py</span> y <span class="mono">auditoria/</span>. Verificación de la puerta: <span class="mono">python3 dome_door.py</span>.</footer>
</div>
<div id="tip" hidden></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>{js}</script>
"""


CSS = """
:root{
  --page:#f5f6f3; --surface:#fcfcfa; --surface-2:#eceeea; --ink:#121517; --ink-2:#4a5156; --muted:#7c8388;
  --grid:#dfe2de; --line:#c1c6c2; --accent:#2b5a78; --door:#3b3f44;
  --sA:#2a78d6; --sB:#eb6834; --sC:#1baf7a; --warn:#b3302f; --warn-wash:rgba(208,59,59,.10); --warn2-wash:rgba(236,131,90,.16);
  --passage:rgba(42,120,214,.12); --open:rgba(124,131,136,.12);
  --conc:#8e9599; --conc-wash:rgba(142,149,153,.20); --steel:#4a5a6a; --wood:#b0804a; --soil:rgba(150,120,80,.14);
  --scene:#dfe6ea;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --door:#d6d9d6;
  --sA:#3987e5; --sB:#d95926; --sC:#199e70; --warn:#ec7070; --warn-wash:rgba(208,59,59,.18); --warn2-wash:rgba(236,131,90,.20);
  --passage:rgba(57,135,229,.18); --open:rgba(193,198,195,.10);
  --conc:#8a9195; --conc-wash:rgba(138,145,149,.22); --steel:#9fb2c4; --wood:#c89a62; --soil:rgba(170,140,95,.14);
  --scene:#1d2328;
}}
:root[data-theme="dark"]{
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --door:#d6d9d6;
  --sA:#3987e5; --sB:#d95926; --sC:#199e70; --warn:#ec7070; --warn-wash:rgba(208,59,59,.18); --warn2-wash:rgba(236,131,90,.20);
  --passage:rgba(57,135,229,.18); --open:rgba(193,198,195,.10);
  --conc:#8a9195; --conc-wash:rgba(138,145,149,.22); --steel:#9fb2c4; --wood:#c89a62; --soil:rgba(170,140,95,.14);
  --scene:#1d2328;
}
*{box-sizing:border-box}
body{background:var(--page); color:var(--ink); font:15px/1.5 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; padding-inline:16px; padding-block:0 40px}
.wrap{max-width:1040px; margin:0 auto}
h1,h2,h3{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif; text-wrap:balance}
h1{font-size:clamp(28px,4.4vw,40px); line-height:1.08; margin:0 0 10px}
h2{font-size:23px; margin:0}
h3{font-size:16px; margin:0 0 8px}
h3.sub{margin-top:18px}
p{max-width:72ch; margin:0 0 10px}
.mono,.num{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace; font-variant-numeric:tabular-nums}
.muted{color:var(--muted)} .small{font-size:13px} .strong{font-weight:700}
header.top{position:sticky; top:env(safe-area-inset-top,0px); z-index:20; background:color-mix(in srgb,var(--page) 90%,transparent); backdrop-filter:blur(8px); border-bottom:1px solid var(--grid); margin-inline:-16px; padding-inline:16px}
.top-inner{max-width:1040px; margin:0 auto; display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap; padding-block:10px}
.brand{font:700 13px "IBM Plex Mono",monospace; letter-spacing:.04em} .brand .dim{color:var(--muted); font-weight:500}
nav.jump{display:flex; gap:12px; flex-wrap:wrap} nav.jump a{color:var(--ink-2); text-decoration:none; font-size:12.5px} nav.jump a:hover{color:var(--ink)}
a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.hero{padding-block:26px 8px}
.eyebrow{font:600 11.5px "IBM Plex Mono",monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin-bottom:10px}
.lede{color:var(--ink-2); font-size:16px}
.statgrid{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1px; background:var(--grid); border:1px solid var(--grid); border-radius:8px; overflow:hidden; margin-block:18px}
@media (max-width:640px){.statgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat{background:var(--surface); padding:12px 14px}
.stat .v{font:600 21px "IBM Plex Mono",monospace} .stat .u{font-size:11px; color:var(--muted); margin-left:2px} .stat .l{font-size:12px; color:var(--ink-2)}
section{padding-block:34px; border-top:1px solid var(--grid); scroll-margin-top:60px}
.sec-head{margin-bottom:6px} .sec-sub{color:var(--ink-2); font-size:14px}
.card{background:var(--surface); border:1px solid var(--grid); border-radius:8px}
.note{padding:12px 16px; margin-top:12px} .note p{margin:0; font-size:14px; color:var(--ink-2)}
.note.warn{border-color:color-mix(in srgb,var(--warn) 40%,var(--grid)); background:var(--warn-wash)} .note.warn h3{color:var(--warn)}
.panel{background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:14px} .panel svg{width:100%; height:auto; display:block}
.twocol{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:18px; align-items:start; margin-top:14px}
@media (max-width:820px){.twocol{grid-template-columns:minmax(0,1fr)}}
.viewer{background:var(--surface); border:1px solid var(--grid); border-radius:10px; overflow:hidden}
#scene{position:relative; width:100%; height:min(74vh,600px); background:var(--scene); touch-action:none; overflow:hidden}
#scene canvas{display:block; width:100%; height:100%; position:relative; z-index:1; cursor:grab}
#scene canvas:active{cursor:grabbing}
#nogl{position:absolute; inset:0; display:grid; place-items:center; padding:20px; color:var(--ink-2); text-align:center; z-index:2}
#nogl[hidden],#labels[hidden],#pick[hidden],#hubTip[hidden]{display:none}
#labels{position:absolute; inset:0; pointer-events:none; overflow:hidden; z-index:2}
.nlab{position:absolute; left:0; top:0; font:600 10.5px "IBM Plex Mono",monospace; color:#fff; background:rgba(21,23,26,.78); padding:1px 4px; border-radius:3px; white-space:nowrap}
.nlab-d{background:rgba(179,48,47,.88)}
.views{position:absolute; left:10px; top:10px; z-index:3; display:flex; gap:6px; flex-wrap:wrap; max-width:calc(100% - 70px)}
.vbtn{font:600 12px "IBM Plex Mono",monospace; color:var(--ink-2); background:color-mix(in srgb,var(--surface) 92%,transparent); border:1px solid var(--line); border-radius:6px; padding:6px 9px; cursor:pointer}
.vbtn:hover{color:var(--ink)}
.zoomctl{position:absolute; right:10px; top:10px; z-index:3; display:flex; flex-direction:column; gap:6px}
.iconbtn{width:38px; height:38px; display:grid; place-items:center; padding:0; background:color-mix(in srgb,var(--surface) 92%,transparent); border:1px solid var(--line); border-radius:8px; color:var(--ink); cursor:pointer}
.iconbtn[hidden]{display:none}
.iconbtn svg{width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:2; stroke-linecap:round; stroke-linejoin:round}
#pick{position:absolute; left:10px; bottom:10px; z-index:4; width:min(310px,calc(100% - 20px)); background:var(--surface); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13px; box-shadow:0 6px 18px rgba(0,0,0,.18)}
#pick .pk-h{display:flex; align-items:center; gap:8px; font-size:14px}
#pick .pk-x{margin-left:auto; font:600 16px/1 "IBM Plex Sans",sans-serif; background:none; border:0; color:var(--muted); cursor:pointer; padding:2px 4px}
#pick .pk-d{color:var(--ink-2); margin-top:4px}
#pick dl{display:grid; grid-template-columns:auto minmax(0,1fr); gap:3px 12px; margin:8px 0 0}
#pick dt{color:var(--muted)} #pick dd{margin:0; font-family:"IBM Plex Mono",monospace; font-size:12.5px}
.filters{display:grid; gap:9px; padding:12px 14px; border-top:1px solid var(--grid)}
.frow{display:flex; flex-wrap:wrap; gap:6px 8px; align-items:center}
.flab{flex:none; width:72px; font:600 11px "IBM Plex Mono",monospace; letter-spacing:.06em; text-transform:uppercase; color:var(--muted)}
label.chip{display:inline-flex; align-items:center; gap:6px; font-size:12.5px; color:var(--ink-2); border:1px solid var(--line); border-radius:999px; padding:4px 10px 4px 8px; cursor:pointer; user-select:none}
label.chip:has(input:checked){background:var(--surface-2); color:var(--ink); border-color:var(--ink-2)}
label.chip input{margin:0; accent-color:var(--accent)}
label.chip i{width:14px; height:4px; border-radius:2px; display:inline-block}
.cmode{display:inline-flex; border:1px solid var(--line); border-radius:6px; overflow:hidden}
.cmode button{font:600 12px "IBM Plex Mono",monospace; background:var(--surface); color:var(--ink-2); border:0; padding:6px 10px; cursor:pointer}
.cmode button+button{border-left:1px solid var(--line)}
.cmode button[aria-pressed="true"]{background:var(--ink); color:var(--page)}
#t-step{flex:1 1 150px; max-width:280px; accent-color:var(--accent)}
#stepname{color:var(--ink-2); flex:1 1 220px}
.viewer:fullscreen{display:flex; flex-direction:column; width:100vw; height:100vh; border-radius:0; border:0}
.viewer:fullscreen #scene{flex:1 1 auto; height:auto; min-height:0}
.viewer:fullscreen .filters{max-height:42vh; overflow:auto}
.viewer:-webkit-full-screen{display:flex; flex-direction:column; width:100vw; height:100vh; border-radius:0; border:0}
.viewer:-webkit-full-screen #scene{flex:1 1 auto; height:auto; min-height:0}
@media (max-width:560px){.flab{width:100%} #scene{height:min(66vh,520px)}}
.legend{display:flex; gap:14px; flex-wrap:wrap; font-size:12.5px; color:var(--ink-2)} .legend span{display:inline-flex; gap:6px; align-items:center}
.swb{width:11px; height:11px; border-radius:50%; display:inline-block}
#hubTip,#tip{position:absolute; pointer-events:none; background:var(--ink); color:var(--page); font:12px/1.4 "IBM Plex Mono",monospace; padding:6px 8px; border-radius:5px; max-width:280px; z-index:5}
#tip{position:fixed}
.tbl{overflow-x:auto; border:1px solid var(--grid); border-radius:8px; background:var(--surface); margin-top:12px}
.tbl.narrow{max-width:620px}
.planpanel{max-width:480px; margin-top:12px}
table{border-collapse:collapse; width:100%; font-size:13.5px}
th,td{text-align:left; padding:7px 10px; border-bottom:1px solid var(--grid); vertical-align:top}
td.nw{white-space:nowrap}
th{font:600 10.5px "IBM Plex Mono",monospace; letter-spacing:.05em; text-transform:uppercase; color:var(--muted)}
th.num,td.num{text-align:right; white-space:nowrap}
tr:last-child td{border-bottom:none} tr.total td{font-weight:700; border-top:1px solid var(--line)} tr.hl td{background:var(--warn2-wash)}
.code{display:inline-block; min-width:26px; text-align:center; font:700 12px "IBM Plex Mono",monospace; color:#fff; background:var(--c); border-radius:4px; padding:2px 5px}
.seg{display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-top:12px}
.seg-l{font-size:13px; color:var(--ink-2)}
.segbtn{font:600 13px "IBM Plex Mono",monospace; background:var(--surface); color:var(--ink-2); border:1px solid var(--line); border-radius:6px; padding:6px 12px; cursor:pointer}
.segbtn[aria-pressed="true"]{background:var(--ink); color:var(--page); border-color:var(--ink)}
.sum{margin-top:12px}
.cuts{display:grid; gap:8px}
.cutrow{display:grid; grid-template-columns:90px minmax(0,1fr) 100px; gap:10px; align-items:center}
@media (max-width:560px){.cutrow{grid-template-columns:minmax(0,1fr)}}
.cutrow svg{width:100%; height:auto; display:block}
.cutlabel{font:600 13px "IBM Plex Mono",monospace} .cutnote{font:12px "IBM Plex Mono",monospace; color:var(--muted)}
.stock{fill:var(--surface-2); stroke:var(--line)}
.seg-A{fill:var(--sA)} .seg-B{fill:var(--sB)} .seg-C{fill:var(--sC)} .seg-door{fill:var(--door)}
.seglbl{fill:#fff; font:600 10px "IBM Plex Mono",monospace}
.seg-door + .seglbl{fill:var(--page)}
.hubgrid{display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:12px}
.hubcard{margin:0; background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:4px}
.hubcard .hh{display:flex; justify-content:space-between; font:600 15px "IBM Plex Mono",monospace}
.hubcard svg{width:100%; height:auto}
.disc{fill:var(--surface-2); stroke:var(--line)}
.openwedge{fill:var(--open); stroke:var(--line); stroke-dasharray:none}
.arc{fill:none; stroke:var(--line); stroke-width:1.2}
.ray{stroke-width:4; stroke-linecap:round}
.hubdot{fill:var(--ink)}
.t-angle{fill:var(--ink); font:700 11px "IBM Plex Mono",monospace; paint-order:stroke; stroke:var(--surface-2); stroke-width:3px}
.t-code{fill:var(--ink); font:700 11.5px "IBM Plex Mono",monospace} .t-tilt{fill:var(--muted); font-weight:500; font-size:10px}
.t-muted{fill:var(--muted); font:11px "IBM Plex Mono",monospace}
.t-dim{fill:var(--ink); font:600 11.5px "IBM Plex Mono",monospace}
.t-node{fill:var(--ink-2); font:600 11px "IBM Plex Mono",monospace}
.t-door{fill:var(--door); font:700 12px "IBM Plex Mono",monospace; letter-spacing:.08em}
.dome-outline{fill:none; stroke:var(--ink-2); stroke-width:1.6}
.floor{stroke:var(--line); stroke-width:2}
.strut-faint{fill:none; stroke:var(--line); stroke-width:1.3}
.door-member{stroke:var(--door); stroke-width:3; stroke-linecap:round}
.frame{fill:var(--door)}
.door-open{fill:var(--passage)}
.sill{stroke:var(--sB); stroke-width:4; stroke-linecap:round}
.dim{stroke:var(--ink); stroke-width:1}
.node{fill:var(--surface); stroke:var(--ink); stroke-width:2}
.passage{fill:var(--passage); stroke:var(--sA); stroke-width:1}
.ring-guide{fill:none; stroke:var(--grid)} .ring-poly{fill:color-mix(in srgb,var(--sA) 7%,transparent); stroke:var(--ink-2); stroke-width:1.2}
.grid{stroke:var(--grid)}
.door-plan{stroke:var(--door); stroke-width:6; stroke-linecap:round}
.anc-low{fill:var(--ink); stroke:var(--surface); stroke-width:2} .anc-high{fill:var(--sA); stroke:var(--surface); stroke-width:2}
.anc-post{fill:var(--door); stroke:var(--sB); stroke-width:3}
ul.plain{margin:0; padding-left:18px; display:grid; gap:6px; font-size:14px}
.warn{color:var(--warn); font-size:13px} .warn2{color:var(--ink-2); font-size:13px}
.notegrid{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:12px; margin-top:12px}
.notegrid .note{margin-top:0}
.zap{fill:var(--conc-wash); stroke:var(--conc); stroke-width:1}
.ped{fill:var(--conc)} .conc{fill:var(--conc)} .conc.proj{fill:var(--conc-wash); stroke:var(--conc)}
.ringband{fill:var(--conc-wash); stroke:var(--conc); stroke-width:1.2}
.beam{fill:var(--steel)} .joist{stroke:var(--wood); stroke-width:1.4} .wood{fill:var(--wood)}
.landing{fill:color-mix(in srgb,var(--wood) 18%,transparent); stroke:var(--wood); stroke-width:1.2}
.step{fill:var(--conc-wash); stroke:var(--conc)} .stepsec{fill:var(--conc-wash); stroke:var(--conc)}
.soil{fill:var(--soil)} .ground{stroke:var(--ink-2); stroke-width:1.5}
.halo{paint-order:stroke; stroke:var(--surface); stroke-width:4px}
.t-pile{fill:var(--ink); font:600 10.5px "IBM Plex Mono",monospace} .t-lev{fill:var(--ink-2); font:11px "IBM Plex Mono",monospace}
ul.checks{list-style:none; padding:0; margin:0; display:grid; gap:6px; font-size:13.5px}
.okli{color:var(--ink)} .okli::first-letter{color:var(--sC)} .badli{color:var(--warn)}
footer a{color:var(--accent)}
footer{padding-block:26px; color:var(--muted); font-size:12.5px; border-top:1px solid var(--grid)}
[data-tip]{cursor:default}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
"use strict";
var DATA=__DATA__;
function cssv(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim();}
/* ---- selector de retiro ---- */
var btns=document.querySelectorAll('.segbtn');
btns.forEach(function(b){b.addEventListener('click',function(){
  btns.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
  document.querySelectorAll('.cutblock').forEach(function(blk){blk.hidden=blk.getAttribute('data-sb')!==b.getAttribute('data-sb');});
  try{localStorage.setItem('retiro',b.getAttribute('data-sb'));}catch(e){}
});});
try{var saved=localStorage.getItem('retiro'); if(saved){var sb=document.querySelector('.segbtn[data-sb="'+saved+'"]'); if(sb) sb.click();}}catch(e){}
/* ---- tooltips de los dibujos ---- */
var tip=document.getElementById('tip');
function showTip(e){var t=e.target.closest&&e.target.closest('[data-tip]'); if(!t){tip.hidden=true;return;}
  tip.textContent=t.getAttribute('data-tip'); tip.hidden=false; var x=e.clientX+14,y=e.clientY+12,w=tip.offsetWidth;
  if(x+w>window.innerWidth-8)x=e.clientX-w-14; tip.style.left=x+'px'; tip.style.top=y+'px';}
document.addEventListener('pointermove',showTip); document.addEventListener('pointerdown',showTip);
document.addEventListener('scroll',function(){tip.hidden=true;},{passive:true});
/* ---- vista 3D (three.js): la misma escena que la maqueta, con filtros ---- */
function start3d(){
  function $(id){return document.getElementById(id);}
  var host=$('scene');
  if(!window.THREE||!THREE.OrbitControls){$('nogl').hidden=false;return;}
  var renderer;
  try{renderer=new THREE.WebGLRenderer({antialias:true});}catch(e){$('nogl').hidden=false;return;}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.outputEncoding=THREE.sRGBEncoding;
  host.insertBefore(renderer.domElement,host.firstChild);
  var cvs=renderer.domElement;
  var scene=new THREE.Scene();
  var camera=new THREE.PerspectiveCamera(38,1,0.03,400);
  var controls=new THREE.OrbitControls(camera,cvs);
  controls.maxPolarAngle=Math.PI*0.96;controls.minDistance=0.3;controls.maxDistance=60;controls.screenSpacePanning=true;
  scene.add(new THREE.HemisphereLight(0xffffff,0x8d7d62,0.72));
  var sun=new THREE.DirectionalLight(0xffffff,0.95);sun.position.set(7,11,5);sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);var sc=sun.shadow.camera;sc.left=-7;sc.right=7;sc.top=7;sc.bottom=-7;sc.near=1;sc.far=40;sun.shadow.bias=-0.0006;
  scene.add(sun);
  function V3(p){return new THREE.Vector3(p[0],p[2],-p[1]);}
  function mat(c,o){return new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:0.6,metalness:0.1},o||{}));}
  var M={steel:mat(0xb9c0c6,{metalness:0.55,roughness:0.38}),frame:mat(0x7f878e,{metalness:0.5,roughness:0.4}),
    hub:mat(0xa9b1b7,{metalness:0.6,roughness:0.35}),mem:mat(0xf5f2ea,{roughness:0.92,transparent:true,opacity:0.9,side:THREE.DoubleSide}),
    glass:mat(0x9fb9c9,{transparent:true,opacity:0.45,roughness:0.1,metalness:0.1,side:THREE.DoubleSide}),doorw:mat(0x6b4a2f,{roughness:0.7}),
    conc:mat(0xa7a69f,{roughness:0.95}),deck:mat(0xb88a55,{roughness:0.8}),joist:mat(0x9d7244,{roughness:0.85}),beam:mat(0x56626d,{metalness:0.4,roughness:0.5}),
    ground:mat(0x7d9656,{roughness:1,transparent:true,opacity:1}),skin:mat(0xc99a7a,{roughness:0.8}),cloth:mat(0x3f566e,{roughness:0.9}),
    pants:mat(0x2f3338,{roughness:0.9}),bed:mat(0xe7e2d6,{roughness:0.95}),bedframe:mat(0x7a5a3c,{roughness:0.8}),
    tA:mat(0x2a78d6,{roughness:0.45,metalness:0.2}),tB:mat(0xeb6834,{roughness:0.45,metalness:0.2}),tC:mat(0x1baf7a,{roughness:0.45,metalness:0.2}),
    tdoor:mat(0x3b3f44,{roughness:0.5,metalness:0.3}),now:mat(0xf2b705,{emissive:0x6b4d00,roughness:0.4}),
    sel:mat(0xffd21f,{emissive:0xb38600,roughness:0.3}),pick:new THREE.MeshBasicMaterial({visible:false})};
  var G={bars:new THREE.Group(),hubs:new THREE.Group(),mem:new THREE.Group(),door:new THREE.Group(),plat:new THREE.Group(),
    under:new THREE.Group(),people:new THREE.Group(),pick:new THREE.Group()};
  Object.keys(G).forEach(function(k){scene.add(G[k]);});
  var UP=new THREE.Vector3(0,1,0);
  function along(a,b,geo,m){var A=V3(a),B=V3(b),dir=B.clone().sub(A),len=dir.length();var mesh=new THREE.Mesh(geo(len),m);
    mesh.position.copy(A.clone().add(B).multiplyScalar(0.5));mesh.quaternion.setFromUnitVectors(UP,dir.normalize());mesh.castShadow=true;mesh.receiveShadow=true;return mesh;}
  function grp(c){return /^[ABC]$/.test(c)?c:'door';}
  // barras, cada una con un cilindro invisible mas grueso para poder tocarla
  var bars=DATA.struts.map(function(s,k){
    var m=s.sq?along(s.a,s.b,function(L){return new THREE.BoxGeometry(0.05,L,0.05);},M.frame):along(s.a,s.b,function(L){return new THREE.CylinderGeometry(0.016,0.016,L,12);},M.steel);
    G.bars.add(m);
    var p=along(s.a,s.b,function(L){return new THREE.CylinderGeometry(0.06,0.06,L*0.8,6);},M.pick);p.castShadow=p.receiveShadow=false;p.userData={kind:'bar',k:k};G.pick.add(p);
    return {m:m,p:p,s:s,k:k};});
  // paso en que se coloca cada nodo: el de su primera barra
  var nodeStep={};
  DATA.struts.forEach(function(s){s.i.forEach(function(v){nodeStep[v]=Math.min(nodeStep[v]===undefined?99:nodeStep[v],s.step);});});
  var nodes=DATA.nodes.map(function(n,k){var hub=null;
    if(n.t!=='PE'){hub=new THREE.Mesh(new THREE.CylinderGeometry(0.065,0.065,0.006,24),M.hub);hub.position.copy(V3(n.p));
      hub.quaternion.setFromUnitVectors(UP,V3(n.n).normalize());hub.castShadow=true;G.hubs.add(hub);}
    var p=new THREE.Mesh(new THREE.SphereGeometry(0.12,8,6),M.pick);p.position.copy(V3(n.p));p.userData={kind:'node',k:k};G.pick.add(p);
    return {n:n,hub:hub,p:p,k:k};});
  var marker=new THREE.Mesh(new THREE.SphereGeometry(0.055,16,12),M.sel);marker.visible=false;scene.add(marker);
  // numeros de nodo
  var labelsHost=$('labels'),labels=nodes.map(function(o){var el=document.createElement('span');el.className='nlab'+(o.n.t[0]==='P'?' nlab-d':'');
    el.textContent=o.n.id;labelsHost.appendChild(el);return {el:el,o:o,p:V3(o.n.p),n:V3(o.n.n).normalize()};});
  function placeLabels(){var show=$('t-num').checked;labelsHost.hidden=!show;if(!show)return;var w=host.clientWidth,h=host.clientHeight;
    labels.forEach(function(L){if(!nodeOn(L.o)){L.el.style.display='none';return;}
      var toCam=camera.position.clone().sub(L.p);var front=toCam.dot(L.n)>-0.05*toCam.length();var v=L.p.clone().project(camera);
      if(!front||v.z>1||v.x<-1.05||v.x>1.05||v.y<-1.05||v.y>1.05){L.el.style.display='none';return;}
      L.el.style.display='';L.el.style.transform='translate('+((v.x+1)/2*w).toFixed(1)+'px,'+((1-v.y)/2*h).toFixed(1)+'px) translate(-50%,-130%)';});}
  // membrana, un poco por fuera de los tubos
  var C=V3(DATA.center),pos=[];
  DATA.tris.forEach(function(t){t.forEach(function(p){var q=V3(p),dir=q.clone().sub(C).normalize();q.add(dir.multiplyScalar(0.03));pos.push(q.x,q.y,q.z);});});
  var mg=new THREE.BufferGeometry();mg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));mg.computeVertexNormals();
  var memMesh=new THREE.Mesh(mg,M.mem);memMesh.castShadow=true;memMesh.receiveShadow=true;G.mem.add(memMesh);
  // hoja de la puerta de 1.00 con vidrio + fijo lateral
  (function(){var q=DATA.door.map(V3),a=q[0],b=q[1],ta=q[3];var w=b.clone().sub(a),wl=w.length(),wd=w.clone().normalize();
    var h=ta.y-a.y-0.025,fr=0.025,leafW=Math.min(1.0,wl-0.05-0.1);var yaw=Math.atan2(-wd.z,wd.x);
    function panel(x0,x1,y0,y1,m,depth){var g=new THREE.BoxGeometry(x1-x0,y1-y0,depth||0.04);var mesh=new THREE.Mesh(g,m);
      var c=a.clone().add(wd.clone().multiplyScalar((x0+x1)/2)).add(new THREE.Vector3(0,(y0+y1)/2,0));mesh.position.copy(c);mesh.rotation.y=yaw;mesh.castShadow=true;return mesh;}
    var x0=fr,x1=fr+leafW;G.door.add(panel(x0,x1,0.01,h,M.doorw,0.045));G.door.add(panel(x0+0.12,x1-0.12,0.35,h-0.15,M.glass,0.05));
    G.door.add(panel(x1+0.01,wl-fr,0.01,h,M.glass,0.02));})();
  // plataforma: viga de anillo, piso, descanso, pilotes, vigas, viguetas y escalones
  var pl=DATA.plat,lv=pl.levels;
  function shapeOf(pts){var s=new THREE.Shape();pts.forEach(function(p,i){if(i===0)s.moveTo(p[0],p[1]);else s.lineTo(p[0],p[1]);});s.closePath();return s;}
  function slab(shape,bottom,thick,m){var g=new THREE.ExtrudeGeometry(shape,{depth:thick,bevelEnabled:false});var mesh=new THREE.Mesh(g,m);mesh.rotation.x=-Math.PI/2;mesh.position.y=bottom;mesh.castShadow=true;mesh.receiveShadow=true;return mesh;}
  var ringShape=shapeOf(pl.outer);var hole=new THREE.Path();pl.inner.forEach(function(p,i){if(i===0)hole.moveTo(p[0],p[1]);else hole.lineTo(p[0],p[1]);});ringShape.holes.push(hole);
  G.plat.add(slab(ringShape,-pl.ringH,pl.ringH,M.conc));
  G.plat.add(slab(shapeOf(pl.inner),-pl.deckT,pl.deckT,M.deck));
  G.plat.add(slab(shapeOf(pl.landing),-pl.deckT,pl.deckT,M.deck));
  var yawU=Math.atan2(DATA.u[1],DATA.u[0]);
  function box(cx,cy,z0,z1,su,sv,m,g){var mesh=new THREE.Mesh(new THREE.BoxGeometry(su,z1-z0,sv),m);mesh.position.set(cx,(z0+z1)/2,-cy);mesh.rotation.y=yawU;mesh.castShadow=true;mesh.receiveShadow=true;(g||G.plat).add(mesh);return mesh;}
  pl.piles.forEach(function(p){box(p.x,p.y,lv.ground-0.001,p.top,pl.ped,pl.ped,M.conc);box(p.x,p.y,lv.footing_top,lv.ground,pl.ped,pl.ped,M.conc,G.under);
    box(p.x,p.y,lv.footing_bottom,lv.footing_top,pl.foot,pl.foot,M.conc,G.under);});
  function beamAlong(a,b,z0,z1,w,m){var A=new THREE.Vector3(a[0],(z0+z1)/2,-a[1]),B=new THREE.Vector3(b[0],(z0+z1)/2,-b[1]);var dir=B.clone().sub(A),L=dir.length();
    var mesh=new THREE.Mesh(new THREE.BoxGeometry(L,z1-z0,w),m);mesh.position.copy(A.add(B).multiplyScalar(0.5));mesh.rotation.y=Math.atan2(-dir.z,dir.x);mesh.castShadow=true;mesh.receiveShadow=true;G.plat.add(mesh);}
  pl.beams.forEach(function(b){beamAlong(b.a,b.b,lv.beam_bottom,lv.beam_top,pl.beamB,M.beam);});
  pl.joists.forEach(function(j){beamAlong(j.a,j.b,lv.beam_top,lv.joist_top,pl.joistB,M.joist);});
  pl.steps.forEach(function(s){var c=s.c;var cx=(c[0][0]+c[2][0])/2,cy=(c[0][1]+c[2][1])/2;
    var su=Math.hypot(c[1][0]-c[0][0],c[1][1]-c[0][1]),sv=Math.hypot(c[3][0]-c[0][0],c[3][1]-c[0][1]);box(cx,cy,lv.ground,s.top,su,sv,M.conc);});
  var ground=new THREE.Mesh(new THREE.CircleGeometry(16,64),M.ground);ground.rotation.x=-Math.PI/2;ground.position.y=lv.ground;ground.receiveShadow=true;scene.add(ground);
  // persona de 1.75 m y cama de 1.60 x 2.00, para dar escala
  function uv(u,v){return [u*DATA.u[0]+v*DATA.v[0],u*DATA.u[1]+v*DATA.v[1]];}
  (function(){var p=uv(0.95,0.35),g=new THREE.Group();
    function part(geo,m,x,y){var mesh=new THREE.Mesh(geo,m);mesh.position.set(x,y,0);mesh.castShadow=true;g.add(mesh);}
    part(new THREE.CylinderGeometry(0.075,0.065,0.82,12),M.pants,0.085,0.41);part(new THREE.CylinderGeometry(0.075,0.065,0.82,12),M.pants,-0.085,0.41);
    part(new THREE.CylinderGeometry(0.19,0.16,0.62,14),M.cloth,0,1.13);
    part(new THREE.CylinderGeometry(0.05,0.045,0.6,10),M.cloth,0.24,1.12);part(new THREE.CylinderGeometry(0.05,0.045,0.6,10),M.cloth,-0.24,1.12);
    part(new THREE.SphereGeometry(0.11,18,14),M.skin,0,1.64);
    g.position.set(p[0],0,-p[1]);g.rotation.y=yawU+Math.PI/2;G.people.add(g);})();
  (function(){var p=uv(-1.55,0),g=new THREE.Group();var fr=new THREE.Mesh(new THREE.BoxGeometry(2.0,0.3,1.6),M.bedframe);fr.position.y=0.15;
    var mt=new THREE.Mesh(new THREE.BoxGeometry(1.96,0.22,1.56),M.bed);mt.position.y=0.41;fr.castShadow=mt.castShadow=true;fr.receiveShadow=mt.receiveShadow=true;g.add(fr);g.add(mt);
    g.position.set(p[0],0,-p[1]);g.rotation.y=yawU;G.people.add(g);})();

  // ---- estado y filtros
  var maxStep=DATA.steps.length-1;
  var st={f:{A:true,B:true,C:true,door:true},color:'acero',step:maxStep,sel:null};
  function barOn(b){return st.f[grp(b.s.code)]&&b.s.step<=st.step;}
  function nodeOn(o){return nodeStep[o.n.id]<=st.step;}
  function baseMat(s){return st.color==='tipo'?M['t'+grp(s.code)]:(s.sq?M.frame:M.steel);}
  function apply(){var full=st.step>=maxStep;
    bars.forEach(function(b){b.m.visible=barOn(b);
      b.m.material=(st.sel&&st.sel.kind==='bar'&&st.sel.k===b.k)?M.sel:(!full&&b.s.step===st.step?M.now:baseMat(b.s));});
    var hubsOn=$('t-hub').checked;nodes.forEach(function(o){if(o.hub)o.hub.visible=hubsOn&&nodeOn(o);});
    G.mem.visible=$('t-mem').checked&&full;G.door.visible=$('t-leaf').checked&&full;
    G.plat.visible=$('t-plat').checked;var und=$('t-und').checked;G.under.visible=und;
    ground.material.opacity=und?0.35:1;ground.material.depthWrite=!und;
    G.people.visible=$('t-people').checked;
    var sn=DATA.steps[st.step];
    $('stepname').innerHTML=full?'<b>Completo</b> · los '+(maxStep+1)+' pasos armados':
      '<b>Paso '+st.step+' de '+maxStep+'</b> · '+sn.name+' · '+sn.bars+' barras nuevas, en amarillo';
    render();}
  // ---- tocar una barra o un nodo
  var ray=new THREE.Raycaster(),ndc=new THREE.Vector2();
  function pickAt(x,y){var r=cvs.getBoundingClientRect();ndc.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);ray.setFromCamera(ndc,camera);
    var objs=[];bars.forEach(function(b){if(barOn(b))objs.push(b.p);});nodes.forEach(function(o){if(nodeOn(o))objs.push(o.p);});
    var hit=ray.intersectObjects(objs,false);return hit.length?hit[0].object.userData:null;}
  function sbIdx(){var b=document.querySelector('.segbtn[aria-pressed="true"]');return b?+b.getAttribute('data-sb'):1;}
  function chip(c){var ok=/^[ABC]$/.test(c);return '<span class="code" style="--c:'+({A:'var(--sA)',B:'var(--sB)',C:'var(--sC)'}[c]||'var(--door)')+(ok?'':';color:var(--page)')+'">'+c+'</span>';}
  var X='<button type="button" class="pk-x" aria-label="Cerrar">×</button>';
  function showPick(u){st.sel=u;var el=$('pick');
    if(!u){el.hidden=true;marker.visible=false;apply();return;}
    var h;
    if(u.kind==='bar'){var s=bars[u.k].s,inf=DATA.info[s.code],i=sbIdx(),sn=DATA.steps[s.step];
      h='<div class="pk-h">'+chip(s.code)+'<b>Pieza '+s.id+'</b>'+X+'</div><div class="pk-d">'+inf.desc+' · '+inf.section+'</div><dl>'+
        '<dt>Une</dt><dd>#'+s.i[0]+' → #'+s.i[1]+'</dd><dt>Centro a centro</dt><dd>'+(s.L*100).toFixed(2)+' cm</dd>'+
        '<dt>Cortar a</dt><dd>'+(inf.cut[i]*100).toFixed(2)+' cm'+(/^[PD]$/.test(s.code)?'':' <span class="muted">(retiro '+(DATA.sb[i]*100).toFixed(1)+' cm)</span>')+'</dd>'+
        '<dt>Se arma en</dt><dd>paso '+s.step+' · '+sn.name+'</dd></dl>'+(inf.note?'<div class="small muted" style="margin-top:6px">'+inf.note+'</div>':'');
      marker.visible=false;}
    else{var n=nodes[u.k].n,labs=DATA.struts.filter(function(s){return s.i[0]===n.id||s.i[1]===n.id;}).map(function(s){return s.code;}).sort();
      h='<div class="pk-h"><b>Nodo #'+n.id+'</b><span class="code" style="--c:var(--accent);color:var(--page)">'+n.tt+'</span>'+X+'</div><div class="pk-d">'+n.d+'</div><dl>'+
        '<dt>Altura</dt><dd>'+n.p[2].toFixed(3)+' m sobre la base</dd><dt>Barras</dt><dd>'+labs.length+': '+labs.join(' ')+'</dd>'+
        '<dt>Se coloca en</dt><dd>paso '+nodeStep[n.id]+' · '+DATA.steps[nodeStep[n.id]].name+'</dd></dl>';
      marker.position.copy(V3(n.p));marker.visible=true;}
    el.innerHTML=h;el.hidden=false;el.querySelector('.pk-x').addEventListener('click',function(){showPick(null);});apply();}
  var down=null;
  cvs.addEventListener('pointerdown',function(e){down={x:e.clientX,y:e.clientY};});
  cvs.addEventListener('pointerup',function(e){if(!down)return;var d=Math.hypot(e.clientX-down.x,e.clientY-down.y);down=null;if(d<=6)showPick(pickAt(e.clientX,e.clientY));});
  var ht=$('hubTip'),raf=0,last=null;
  cvs.addEventListener('pointermove',function(e){if(e.pointerType!=='mouse'||e.buttons){ht.hidden=true;return;}last=e;
    if(raf)return;raf=requestAnimationFrame(function(){raf=0;var u=pickAt(last.clientX,last.clientY);
      if(!u){ht.hidden=true;cvs.style.cursor='';return;}
      var r=host.getBoundingClientRect();
      ht.textContent=u.kind==='bar'?(bars[u.k].s.id+' · '+bars[u.k].s.code+' · '+(bars[u.k].s.L*100).toFixed(2)+' cm'):('#'+nodes[u.k].n.id+' · '+nodes[u.k].n.tt);
      ht.hidden=false;ht.style.left=(last.clientX-r.left+14)+'px';ht.style.top=(last.clientY-r.top+10)+'px';cvs.style.cursor='pointer';});});
  cvs.addEventListener('pointerleave',function(){ht.hidden=true;});
  document.querySelectorAll('.segbtn').forEach(function(b){b.addEventListener('click',function(){if(st.sel)showPick(st.sel);});});
  // ---- vistas y zoom
  function view(name){var d=new THREE.Vector3(DATA.u[0],0,-DATA.u[1]),side=new THREE.Vector3().crossVectors(d,UP);
    var k=camera.aspect<1.3?Math.min(2.4,1.25/camera.aspect):1,tgt,eye;   // pantallas angostas: alejar para que quepa todo
    if(name==='frente'){tgt=new THREE.Vector3(0,1.0,0);eye=d.clone().multiplyScalar(11);eye.y=1.6;}
    else if(name==='lado'){tgt=d.clone().multiplyScalar(1.0);tgt.y=1.0;eye=side.clone().multiplyScalar(-12).add(d);eye.y=1.6;}
    else if(name==='planta'){tgt=d.clone().multiplyScalar(0.9);eye=tgt.clone();eye.y=15;eye.x+=0.001;}
    else if(name==='adentro'){eye=d.clone().multiplyScalar(-0.4).add(side.clone().multiplyScalar(1.25));eye.y=1.6;tgt=d.clone().multiplyScalar(2.9);tgt.y=1.15;k=1;}
    else{tgt=d.clone().multiplyScalar(1.1);tgt.y=0.7;eye=d.clone().multiplyScalar(8.6).add(side.clone().multiplyScalar(-5.6));eye.y=4.6;}
    controls.target.copy(tgt);camera.position.copy(tgt.clone().add(eye.clone().sub(tgt).multiplyScalar(k)));controls.update();render();}
  document.querySelectorAll('.vbtn[data-view]').forEach(function(b){b.addEventListener('click',function(){view(b.getAttribute('data-view'));});});
  function zoomBy(f){var off=camera.position.clone().sub(controls.target);off.setLength(Math.max(controls.minDistance,Math.min(controls.maxDistance,off.length()*f)));
    camera.position.copy(controls.target).add(off);controls.update();render();}
  $('z-in').addEventListener('click',function(){zoomBy(0.75);});
  $('z-out').addEventListener('click',function(){zoomBy(1/0.75);});
  $('z-fit').addEventListener('click',function(){view('tres');});
  var vw=$('viewer'),fs=$('z-full');
  if((vw.requestFullscreen||vw.webkitRequestFullscreen)&&(document.fullscreenEnabled||document.webkitFullscreenEnabled))fs.hidden=false;
  fs.addEventListener('click',function(){var r;
    if(document.fullscreenElement||document.webkitFullscreenElement)r=(document.exitFullscreen||document.webkitExitFullscreen).call(document);
    else r=(vw.requestFullscreen||vw.webkitRequestFullscreen).call(vw);
    if(r&&r.catch)r.catch(function(){});});
  ['fullscreenchange','webkitfullscreenchange'].forEach(function(ev){document.addEventListener(ev,function(){setTimeout(resize,60);});});
  // ---- controles de filtro
  document.querySelectorAll('input[data-f]').forEach(function(cb){cb.addEventListener('change',function(){st.f[cb.getAttribute('data-f')]=cb.checked;
    if(st.sel&&st.sel.kind==='bar'&&!barOn(bars[st.sel.k]))showPick(null);else apply();});});
  ['t-hub','t-num','t-leaf','t-mem','t-plat','t-und','t-people'].forEach(function(id){$(id).addEventListener('change',apply);});
  var cbtns=document.querySelectorAll('.cmode button');
  cbtns.forEach(function(b){b.addEventListener('click',function(){st.color=b.getAttribute('data-c');cbtns.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});apply();});});
  var rng=$('t-step'),playBtn=$('t-play'),play=null;
  function setStep(n){st.step=n;rng.value=n;var u=st.sel;
    if(u&&((u.kind==='bar'&&!barOn(bars[u.k]))||(u.kind==='node'&&!nodeOn(nodes[u.k])))){st.sel=null;$('pick').hidden=true;marker.visible=false;}
    apply();}
  function stopPlay(){if(play){clearInterval(play);play=null;playBtn.textContent='▶ animar';}}
  rng.addEventListener('input',function(){stopPlay();setStep(+rng.value);});
  playBtn.addEventListener('click',function(){if(play){stopPlay();return;}var n=0;setStep(0);playBtn.textContent='■ detener';
    play=setInterval(function(){n++;if(n>maxStep){stopPlay();return;}setStep(n);},1300);});
  function resize(){var w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}
  function render(){renderer.render(scene,camera);placeLabels();}
  controls.addEventListener('change',render);
  scene.background=new THREE.Color(cssv('--scene')||'#dfe6ea');
  var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(resize,120);});
  if(window.matchMedia)window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){scene.background=new THREE.Color(cssv('--scene'));render();});
  resize();view('tres');apply();
}
start3d();
})();
"""


if __name__ == "__main__":
    out = os.path.join(HERE, "domo-3v-cucuchica.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build_page())
    print("Escrito:", out)
