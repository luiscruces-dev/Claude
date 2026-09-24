"""
Genera domo-3v-cucuchica.html: el plano de taller del domo con puerta.

Corre: `python3 dome_viewer.py`  (Python estandar; usa dome_model.py,
dome_door.py y dome_build_sequence.py).

Todo lo que muestra la pagina sale de esos modulos al momento de generarla:
vista 3D, piezas y plan de corte (para 3 retiros posibles), plantillas de
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
import dome_platform as plat
from dome_model import v_sub, v_norm

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
SETBACKS = (0.035, 0.050, 0.065)
DOOR_CODES = {"P", "D", "V", "K1", "K2"}


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


def platform_lines3d(P):
    """Segmentos de la plataforma para la vista 3D, en coordenadas del visor (X, Z, -Y)."""
    lv = P.levels
    segs = []
    def pt(u, v, z):
        x, y = P.to_xy(u, v)
        return [round(x, 3), round(z, 3), round(-y, 3)]
    def seg(a, b, k): segs.append(a + b + [k])
    for poly in (P.outer, P.inner):
        for z in (0.0, lv["ring_bottom"]):
            for i in range(len(poly)):
                seg(pt(*poly[i], z), pt(*poly[(i+1) % len(poly)], z), "ring")
    for p in P.piles:
        top = lv["ring_bottom"] if p["kind"] == "perimetral" else lv["beam_bottom"]
        for dv, du in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            seg(pt(p["u"]+du*plat.PED/2, p["v"]+dv*plat.PED/2, top), pt(p["u"]+du*plat.PED/2, p["v"]+dv*plat.PED/2, lv["footing_top"]), "pile")
        c = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        for i in range(4):
            (a1, b1), (a2, b2) = c[i], c[(i+1) % 4]
            seg(pt(p["u"]+a1*plat.FOOT/2, p["v"]+b1*plat.FOOT/2, lv["footing_top"]), pt(p["u"]+a2*plat.FOOT/2, p["v"]+b2*plat.FOOT/2, lv["footing_top"]), "zap")
    zb = (lv["beam_top"] + lv["beam_bottom"])/2
    for bm in P.beams:
        seg(pt(bm["u0"], bm["v"], zb), pt(bm["u1"], bm["v"], zb), "beam")
    L = P.landing
    seg(pt(L["beam_u"], L["v0"], zb), pt(L["beam_u"], L["v1"], zb), "beam")
    zj = (lv["joist_top"] + lv["beam_top"])/2
    for j in P.joists:
        seg(pt(j["u"], j["v0"], zj), pt(j["u"], j["v1"], zj), "joist")
    for lj in P.landing_joists:
        seg(pt(lj["u0"], lj["v"], zj), pt(lj["u1"], lj["v"], zj), "joist")
    rect = [(L["u0"], L["v0"]), (L["u1"], L["v0"]), (L["u1"], L["v1"]), (L["u0"], L["v1"])]
    for i in range(4):
        seg(pt(*rect[i], 0.0), pt(*rect[(i+1) % 4], 0.0), "land")
    for st in P.steps:
        r = [(st["u0"], st["v0"]), (st["u1"], st["v0"]), (st["u1"], st["v1"]), (st["u0"], st["v1"])]
        for i in range(4):
            seg(pt(*r[i], st["z"]), pt(*r[(i+1) % 4], st["z"]), "step")
    for i in range(48):
        a0, a1 = 2*math.pi*i/48, 2*math.pi*(i+1)/48
        seg([round(4.6*math.cos(a0), 3), lv["ground"], round(4.6*math.sin(a0), 3)],
            [round(4.6*math.cos(a1), 3), lv["ground"], round(4.6*math.sin(a1), 3)], "ground")
    return segs


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

    # ---- 3D data (y hacia arriba)
    data3d = {"v": [[round(p[0], 4), round(p[2], 4), round(-p[1], 4)] if i in D.active else None for i, p in enumerate(P)],
              "e": [[a, b, D.edge_label[(a, b)]] for a, b in D.edges],
              "t": [list(t) for t in D.triangles],
              "type": {str(v): seq.hub_type_of(D, v) for v in D.active},
              "deg": {str(v): sum(1 for e in D.edges if v in e) for v in D.active},
              "door": [dd["a"], dd["b"], dd["Tb"], dd["Ta"]],
              # direccion de la puerta en coordenadas del visor (x, z) = (X, -Y)
              "dir": [round(dd["u"][0], 4), round(-dd["u"][1], 4)],
              "pl": platform_lines3d(PL)}

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
        desc = {"H1": "interior", "H2": "interior", "H3": "interior, incluye el ápice", "H4": "base, nodo bajo", "H5": "base, nodo alto (+4.86 cm)",
                "PA": "base, lleva el poste de la puerta", "PB": "junto a la puerta, amarre bajo K1", "PC": "junto a la puerta, amarre alto K2",
                "PD": "sobre el vestíbulo, recibe las 2 vigas V"}.get(name, "")
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
  <p class="sec-sub">Arrastre para girar; rueda o pellizco para acercar. Pase el cursor sobre un nodo para ver su número y tipo, iguales a los de la secuencia de armado.</p>
  <div class="viewer"><div class="viewer-rel"><canvas id="c3d" aria-label="Vista 3D del domo con la puerta"></canvas><div id="hubTip" hidden></div></div>
    <div class="viewer-foot">
      <div class="legend"><span><i class="sw" style="background:var(--sA)"></i>A 125.59</span><span><i class="sw" style="background:var(--sB)"></i>B 122.89</span><span><i class="sw" style="background:var(--sC)"></i>C 106.16</span><span><i class="sw" style="background:var(--door)"></i>puerta (P D V K)</span><span><i class="sw" style="background:var(--conc)"></i>concreto</span><span><i class="sw" style="background:var(--wood)"></i>madera</span></div>
      <div class="ctrls"><label class="toggle"><input type="checkbox" id="plt" checked> plataforma</label><label class="toggle"><input type="checkbox" id="mem"> membrana</label><button class="ghost" id="reset" type="button">Vista inicial</button></div>
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

<footer>Maqueta 1:10 y vista 3D realista: <a href="https://claude.ai/artifact/QzhQ4UyVbxqeMXogM7poM6">maqueta del domo</a> (en el repositorio: <span class="mono">maqueta/maqueta.html</span>).<br>Generado por <span class="mono">dome_viewer.py</span> desde <span class="mono">dome_model.py</span>, <span class="mono">dome_door.py</span> y <span class="mono">dome_build_sequence.py</span>. Verificación de la geometría: <span class="mono">dome_verify.py</span> y <span class="mono">auditoria/</span>. Verificación de la puerta: <span class="mono">python3 dome_door.py</span>.</footer>
</div>
<div id="tip" hidden></div>
<script>{js}</script>
"""


CSS = """
:root{
  --page:#f5f6f3; --surface:#fcfcfa; --surface-2:#eceeea; --ink:#121517; --ink-2:#4a5156; --muted:#7c8388;
  --grid:#dfe2de; --line:#c1c6c2; --accent:#2b5a78; --door:#3b3f44;
  --sA:#2a78d6; --sB:#eb6834; --sC:#1baf7a; --warn:#b3302f; --warn-wash:rgba(208,59,59,.10); --warn2-wash:rgba(236,131,90,.16);
  --passage:rgba(42,120,214,.12); --open:rgba(124,131,136,.12);
  --conc:#8e9599; --conc-wash:rgba(142,149,153,.20); --steel:#4a5a6a; --wood:#b0804a; --soil:rgba(150,120,80,.14);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --door:#d6d9d6;
  --sA:#3987e5; --sB:#d95926; --sC:#199e70; --warn:#ec7070; --warn-wash:rgba(208,59,59,.18); --warn2-wash:rgba(236,131,90,.20);
  --passage:rgba(57,135,229,.18); --open:rgba(193,198,195,.10);
  --conc:#8a9195; --conc-wash:rgba(138,145,149,.22); --steel:#9fb2c4; --wood:#c89a62; --soil:rgba(170,140,95,.14);
}}
:root[data-theme="dark"]{
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --door:#d6d9d6;
  --sA:#3987e5; --sB:#d95926; --sC:#199e70; --warn:#ec7070; --warn-wash:rgba(208,59,59,.18); --warn2-wash:rgba(236,131,90,.20);
  --passage:rgba(57,135,229,.18); --open:rgba(193,198,195,.10);
  --conc:#8a9195; --conc-wash:rgba(138,145,149,.22); --steel:#9fb2c4; --wood:#c89a62; --soil:rgba(170,140,95,.14);
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
.viewer-rel{position:relative}
canvas#c3d{display:block; width:100%; height:460px; touch-action:none; cursor:grab; background:var(--surface-2)}
.viewer-foot{display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; padding:10px 14px; border-top:1px solid var(--grid)}
.legend{display:flex; gap:14px; flex-wrap:wrap; font-size:12.5px; color:var(--ink-2)} .legend span{display:inline-flex; gap:6px; align-items:center}
.sw{width:16px; height:3px; border-radius:2px; display:inline-block} .swb{width:11px; height:11px; border-radius:50%; display:inline-block}
.ctrls{display:flex; gap:12px; align-items:center}
label.toggle{font-size:12.5px; color:var(--ink-2); display:flex; gap:6px; align-items:center}
button.ghost{font:inherit; font-size:12.5px; color:var(--ink-2); background:transparent; border:1px solid var(--line); border-radius:6px; padding:5px 10px; cursor:pointer}
#hubTip,#tip{position:absolute; pointer-events:none; background:var(--ink); color:var(--page); font:12px/1.4 "IBM Plex Mono",monospace; padding:6px 8px; border-radius:5px; max-width:280px; z-index:5}
#tip{position:fixed}
.tbl{overflow-x:auto; border:1px solid var(--grid); border-radius:8px; background:var(--surface); margin-top:12px}
.tbl.narrow{max-width:620px}
.planpanel{max-width:480px; margin-top:12px}
table{border-collapse:collapse; width:100%; font-size:13.5px}
th,td{text-align:left; padding:7px 10px; border-bottom:1px solid var(--grid); vertical-align:top}
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
var TH0=Math.atan2(-DATA.dir[0],DATA.dir[1])+0.5;   /* puerta de frente, girada un poco */
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
/* ---- vista 3D ---- */
var cv=document.getElementById('c3d'), ctx=cv.getContext('2d');
var V=DATA.v, E=DATA.e, T=DATA.t, PL=DATA.pl||[], act=[], showPl=true;
V.forEach(function(p,i){if(p)act.push(i);});
var mn=[1e9,1e9,1e9],mx=[-1e9,-1e9,-1e9];
act.forEach(function(i){for(var k=0;k<3;k++){mn[k]=Math.min(mn[k],V[i][k]);mx[k]=Math.max(mx[k],V[i][k]);}});
PL.forEach(function(s){for(var k=0;k<3;k++){mn[k]=Math.min(mn[k],s[k],s[k+3]);mx[k]=Math.max(mx[k],s[k],s[k+3]);}});
var ctr=[(mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2];
var st={th:TH0,ph:0.32,zoom:1}, dpr=Math.min(window.devicePixelRatio||1,2), showMem=false, proj=[];
function cam(p){var x=p[0]-ctr[0],y=p[1]-ctr[1],z=p[2]-ctr[2];var c=Math.cos(st.th),s=Math.sin(st.th);
  var x1=x*c+z*s,z1=-x*s+z*c;var cp=Math.cos(st.ph),sp=Math.sin(st.ph);var y2=y*cp-z1*sp,z2=y*sp+z1*cp;var f=22/(22-z2);return [x1*f,y2*f,z2];}
function colorOf(l){return {A:cssv('--sA'),B:cssv('--sB'),C:cssv('--sC')}[l]||cssv('--door');}
function draw(){var W=cv.width,H=cv.height;ctx.clearRect(0,0,W,H);
  var cs={};act.forEach(function(i){cs[i]=cam(V[i]);});
  var sc=Math.min(W,H)/7.4*st.zoom;
  act.forEach(function(i){var c=cs[i];proj[i]=[W/2+c[0]*sc,H/2-c[1]*sc+H*0.02,c[2]];});
  if(showPl){var sty={ring:['--conc',2.2],pile:['--conc',1.6],zap:['--conc',1],beam:['--steel',2],joist:['--wood',0.9],land:['--wood',1.6],step:['--conc',1],ground:['--line',1]};
    PL.forEach(function(s){var a=cam([s[0],s[1],s[2]]),b=cam([s[3],s[4],s[5]]),y=sty[s[6]];ctx.beginPath();
      ctx.moveTo(W/2+a[0]*sc,H/2-a[1]*sc+H*0.02);ctx.lineTo(W/2+b[0]*sc,H/2-b[1]*sc+H*0.02);ctx.strokeStyle=cssv(y[0]);ctx.globalAlpha=0.75;ctx.lineWidth=y[1]*dpr;ctx.stroke();ctx.globalAlpha=1;});}
  if(showMem){T.map(function(t){return {t:t,d:(proj[t[0]][2]+proj[t[1]][2]+proj[t[2]][2])/3};}).sort(function(a,b){return a.d-b.d;}).forEach(function(o){
    var t=o.t;ctx.beginPath();ctx.moveTo(proj[t[0]][0],proj[t[0]][1]);ctx.lineTo(proj[t[1]][0],proj[t[1]][1]);ctx.lineTo(proj[t[2]][0],proj[t[2]][1]);ctx.closePath();
    ctx.fillStyle='color-mix(in srgb, '+cssv('--ink-2')+' 9%, transparent)';ctx.fill();});
    var d=DATA.door;ctx.beginPath();ctx.moveTo(proj[d[0]][0],proj[d[0]][1]);for(var k=1;k<4;k++)ctx.lineTo(proj[d[k]][0],proj[d[k]][1]);ctx.closePath();
    ctx.fillStyle='color-mix(in srgb, '+cssv('--sA')+' 22%, transparent)';ctx.fill();}
  var zs=act.map(function(i){return proj[i][2];}),zmin=Math.min.apply(null,zs),zmax=Math.max.apply(null,zs);
  function dep(z){return (z-zmin)/((zmax-zmin)||1);}
  E.map(function(e){return {e:e,d:(proj[e[0]][2]+proj[e[1]][2])/2};}).sort(function(a,b){return a.d-b.d;}).forEach(function(o){
    var e=o.e,a=proj[e[0]],b=proj[e[1]],dd=dep(o.d),door=!/^[ABC]$/.test(e[2]);
    ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.strokeStyle=colorOf(e[2]);ctx.globalAlpha=0.35+dd*0.65;
    ctx.lineWidth=((door?2.4:1.1)+dd*1.6)*dpr;ctx.lineCap='round';ctx.stroke();ctx.globalAlpha=1;});
  act.slice().sort(function(a,b){return proj[a][2]-proj[b][2];}).forEach(function(i){var p=proj[i],dd=dep(p[2]);
    ctx.beginPath();ctx.arc(p[0],p[1],(1.8+DATA.deg[i]*0.55)*(0.6+dd*0.5)*dpr,0,Math.PI*2);ctx.fillStyle=cssv('--ink-2');ctx.globalAlpha=0.35+dd*0.6;ctx.fill();ctx.globalAlpha=1;});}
function resize(){cv.width=Math.round(cv.clientWidth*dpr);cv.height=Math.round(cv.clientHeight*dpr);draw();}
var drag=false,lx=0,ly=0,ht=document.getElementById('hubTip');
cv.addEventListener('pointerdown',function(e){drag=true;lx=e.clientX;ly=e.clientY;cv.setPointerCapture(e.pointerId);});
cv.addEventListener('pointerup',function(){drag=false;}); cv.addEventListener('pointercancel',function(){drag=false;});
cv.addEventListener('pointermove',function(e){if(drag){st.th+=(e.clientX-lx)*0.008;st.ph=Math.max(-1.4,Math.min(1.4,st.ph+(e.clientY-ly)*0.008));lx=e.clientX;ly=e.clientY;ht.hidden=true;draw();return;}
  var r=cv.getBoundingClientRect(),mx=(e.clientX-r.left)*dpr,my=(e.clientY-r.top)*dpr,best=-1,bd=22*dpr;
  act.forEach(function(i){var d=Math.hypot(proj[i][0]-mx,proj[i][1]-my);if(d<bd){bd=d;best=i;}});
  if(best<0){ht.hidden=true;return;}
  var labs=E.filter(function(x){return x[0]===best||x[1]===best;}).map(function(x){return x[2];}).sort().join(' ');
  ht.textContent='#'+best+' · '+DATA.type[best]+' · '+labs;ht.hidden=false;ht.style.left=(e.clientX-r.left+14)+'px';ht.style.top=(e.clientY-r.top+10)+'px';});
cv.addEventListener('pointerleave',function(){ht.hidden=true;});
cv.addEventListener('wheel',function(e){e.preventDefault();st.zoom=Math.max(0.5,Math.min(3,st.zoom*(1-e.deltaY*0.001)));draw();},{passive:false});
document.getElementById('mem').addEventListener('change',function(e){showMem=e.target.checked;draw();});
document.getElementById('plt').addEventListener('change',function(e){showPl=e.target.checked;draw();});
document.getElementById('reset').addEventListener('click',function(){st.th=TH0;st.ph=0.32;st.zoom=1;draw();});
var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(resize,120);});
if(window.matchMedia)window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
resize();
})();
"""


if __name__ == "__main__":
    out = os.path.join(HERE, "domo-3v-cucuchica.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build_page())
    print("Escrito:", out)
