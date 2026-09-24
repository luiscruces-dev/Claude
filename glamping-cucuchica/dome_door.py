"""
Puerta (portal de acceso) del domo geodesico 3V — Cucuchica.

Corre: `python3 dome_door.py`  (Python estandar, usa dome_model.py).

Por que hace falta un portal: el domo mide 2.52 m en el centro y la pared
baja hasta el piso, asi que una puerta de 2 m no cabe en la superficie del
domo. La solucion es un marco de puerta vertical con un pequeno techo de
vestibulo que se mete en el domo hasta donde el techo ya pasa de 2 m.

Diseno (todo sale de la geometria, no de numeros a mano):
- La puerta va centrada sobre uno de los 5 nodos H3 del primer anillo
  (DOOR_HUB). Los 5 lugares son identicos por simetria: se elige el que mire
  a la terraza.
- Los postes del marco son verticales y arrancan en los 2 anclajes H4 que ya
  existen a cada lado de ese tramo de la base (no hay anclajes nuevos). La
  barra B del piso entre ellos se queda: es el umbral.
- Dintel a HEAD_Z sobre el piso.
- Se quitan el nodo H3 y el nodo H1 que tiene encima (y sus 10 barras). El
  hueco se cierra con: 2 vigas de techo desde las esquinas del marco hasta el
  nodo de arriba, y 4 barras de amarre desde las esquinas del marco a los
  nodos del borde del hueco.

Verificaciones que corre (PASS/FAIL, exit 1 si algo falla):
- Paso libre: ninguna barra ni panel invade el paso de la puerta.
- Estabilidad 3D: cada nodo no anclado tiene >=3 barras no coplanares y la
  matriz de rigidez de la armadura no es singular.
- Superficie cerrada: cada arista de la membrana tiene 2 paneles (salvo el
  borde de la base y el vano de la puerta).
- Armadura espacial con peso propio, persona en el apice y viento (12
  direcciones, puerta abierta y cerrada) contra la capacidad de cada barra.
- Flexion de postes y dintel por viento sobre la puerta cerrada.

Igual que el resto: el viento es el valor ilustrativo de 100 km/h del .md,
no el dato oficial del sitio. No reemplaza al ingeniero.
"""

import math
import sys
from collections import defaultdict, Counter

from dome_model import build_dome, v_add, v_sub, v_scale, v_dot, v_cross, v_norm, v_normalize

G = 9.81

DOOR_HUB = 3            # nodo H3 (numeracion de secuencia_de_armado.md) que reemplaza la puerta
HEAD_Z = 2.10           # eje del dintel sobre el piso (m)
FRAME_B = 0.050         # tubo cuadrado del marco: 50 x 50 x 2 mm

# secciones: area (m2), inercia (m4), radio de giro (m), modulo resistente (m3), kg/m
SECTIONS = {
    "tubo32x2": {"A": math.pi/4*(0.032**2-0.028**2), "I": math.pi/64*(0.032**4-0.028**4), "c": 0.016},
    "cuad50x2": {"A": 0.050**2-0.046**2, "I": (0.050**4-0.046**4)/12, "c": 0.025},
}
for s in SECTIONS.values():
    s["r"] = math.sqrt(s["I"]/s["A"]); s["S"] = s["I"]/s["c"]; s["kg_m"] = s["A"]*7850

MEMBER_INFO = {
    "A": ("tubo32x2", "barra A del domo"), "B": ("tubo32x2", "barra B del domo"), "C": ("tubo32x2", "barra C del domo"),
    "P": ("cuad50x2", "poste del marco"), "D": ("cuad50x2", "dintel del marco"),
    "V": ("tubo32x2", "viga del techo del vestíbulo"),
    "K1": ("tubo32x2", "amarre marco–nodo lateral bajo"), "K2": ("tubo32x2", "amarre marco–nodo lateral alto"),
}

FAILS = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)
    return ok


# ------------------------------------------------------------------ geometria

class DoorDome:
    pass


def to_floor_frame(d):
    """Coordenadas con origen en el centro del piso, Z hacia arriba desde el
    nivel de los nodos bajos, X hacia el primer nodo alto H5 (igual que el
    replanteo de secuencia_de_armado.md)."""
    axis = v_normalize(d.verts[d.apex_index_in_verts2])
    floor_h = min(d.heights[b] for b in d.boundary_verts)
    def planar(p): return v_sub(p, v_scale(axis, v_dot(p, axis)))
    first_high = min(b for b in d.boundary_verts if d.heights[b]-floor_h > 1e-6)
    e1 = v_normalize(planar(d.verts[first_high])); e2 = v_cross(axis, e1)
    P = [(v_dot(p, e1), v_dot(p, e2), d.heights[i]-floor_h) for i, p in enumerate(d.verts)]
    return P, (0.0, 0.0, -floor_h)


def build_dome_plain():
    """El domo sin puerta con la misma interfaz, para comparar."""
    d = build_dome()
    P, center = to_floor_frame(d)
    D = DoorDome()
    D.base = d; D.verts = list(P); D.heights = [p[2] for p in P]; D.center = center; D.R = d.R
    D.edges = list(d.edges); D.edge_label = dict(d.edge_label)
    D.edge_len = {e: v_norm(v_sub(P[e[0]], P[e[1]])) for e in D.edges}
    D.triangles = list(d.triangles); D.boundary_verts = list(d.boundary_verts)
    D.apex_index_in_verts2 = d.apex_index_in_verts2
    D.active = sorted({v for e in D.edges for v in e}); D.door = None
    D.hub_types = [{"name": t["name"], "hub_ids": sorted(t["hub_ids"]), "count": t["count"]} for t in d.hub_types]
    D.type_of = {v: t["name"] for t in d.hub_types for v in t["hub_ids"]}
    return D


def build_dome_with_door(door_hub=DOOR_HUB, head_z=HEAD_Z):
    d = build_dome()
    P, center = to_floor_frame(d)
    adj = defaultdict(set)
    for a, b in d.edges:
        adj[a].add(b); adj[b].add(a)
    type_of = {v: t["name"] for t in d.hub_types for v in t["hub_ids"]}
    bnd = set(d.boundary_verts)
    assert type_of[door_hub] == "H3" and len(adj[door_hub] & bnd) == 2, "la puerta debe ir sobre un H3 del primer anillo"

    h = door_hub
    a, b = sorted(adj[h] & bnd, key=lambda v: math.atan2(P[v][1], P[v][0]))
    u = v_normalize((P[h][0], P[h][1], 0.0))           # hacia afuera, centro de la puerta
    vdir = v_cross((0.0, 0.0, 1.0), u)                 # derecha de quien mira la puerta desde afuera
    def uv(p): return (v_dot(p, u), v_dot(p, vdir), p[2])
    if uv(P[a])[1] > uv(P[b])[1]:
        a, b = b, a                                    # a = izquierda, b = derecha
    # nodo H1 justo encima de h en el mismo meridiano (barra C hacia arriba)
    above = max((n for n in adj[h] if n not in bnd), key=lambda n: P[n][2])
    top = max((n for n in adj[above] if n != h), key=lambda n: P[n][2])       # nodo sobre el vestibulo
    removed_nodes = {h, above}
    hole = sorted({n for r in removed_nodes for n in adj[r]} - removed_nodes)
    side_low = {s: next(n for n in hole if n in adj[s] and n in adj[h] and n not in bnd) for s in (a, b)}
    side_up = {s: next(n for n in hole if n in adj[side_low[s]] and n in adj[above] and n != top and n not in (side_low[a], side_low[b]))
               for s in (a, b)}

    verts = list(P)
    Ta = len(verts); verts.append((P[a][0], P[a][1], head_z))
    Tb = len(verts); verts.append((P[b][0], P[b][1], head_z))

    removed_edges = {e for e in d.edges if e[0] in removed_nodes or e[1] in removed_nodes}
    edges = [e for e in d.edges if e not in removed_edges]
    label = {e: d.edge_label[e] for e in edges}
    new = [(a, Ta, "P"), (b, Tb, "P"), (Ta, Tb, "D"), (Ta, top, "V"), (Tb, top, "V"),
           (Ta, side_low[a], "K1"), (Tb, side_low[b], "K1"), (Ta, side_up[a], "K2"), (Tb, side_up[b], "K2")]
    for x, y, lab in new:
        e = (min(x, y), max(x, y)); edges.append(e); label[e] = lab
    edges.sort()

    removed_tris = [t for t in d.triangles if set(t) & removed_nodes]
    tris = [t for t in d.triangles if not set(t) & removed_nodes]
    new_tris = []
    for s, T in ((a, Ta), (b, Tb)):
        new_tris += [(s, side_low[s], T), (side_low[s], side_up[s], T), (side_up[s], top, T)]
    new_tris.append((Ta, Tb, top))
    tris += new_tris

    D = DoorDome()
    D.base = d
    D.verts = verts
    D.heights = [p[2] for p in verts]
    D.center = center
    D.R = d.R
    D.edges = edges
    D.edge_label = label
    D.edge_len = {e: v_norm(v_sub(verts[e[0]], verts[e[1]])) for e in edges}
    D.triangles = tris
    D.new_triangles = new_tris
    D.removed_triangles = removed_tris
    D.boundary_verts = list(d.boundary_verts)
    D.apex_index_in_verts2 = d.apex_index_in_verts2
    D.active = sorted({v for e in edges for v in e})
    D.door = {"hub": h, "above": above, "top": top, "a": a, "b": b, "Ta": Ta, "Tb": Tb,
              "side_low": side_low, "side_up": side_up, "removed_nodes": sorted(removed_nodes),
              "removed_edges": sorted(removed_edges), "u": u, "v": vdir, "head_z": head_z,
              "azimuth_deg": math.degrees(math.atan2(u[1], u[0])) % 360,
              "opening": (a, b, Tb, Ta)}
    D.uv = uv
    # tipos de nodo: los estandar para los que no cambian, especiales alrededor de la puerta
    special = {a: "PA", b: "PA", side_low[a]: "PB", side_low[b]: "PB", side_up[a]: "PC", side_up[b]: "PC",
               top: "PD", Ta: "PE", Tb: "PE"}
    groups = defaultdict(list)
    for v in D.active:
        groups[special.get(v, type_of.get(v))].append(v)
    order = ["H1", "H2", "H3", "H4", "H5", "PA", "PB", "PC", "PD", "PE"]
    D.hub_types = [{"name": n, "hub_ids": sorted(groups[n]), "count": len(groups[n])} for n in order if groups.get(n)]
    D.type_of = {v: n for n, ids in groups.items() for v in ids}
    D.side = {a: "izq", side_low[a]: "izq", side_up[a]: "izq", Ta: "izq",
              b: "der", side_low[b]: "der", side_up[b]: "der", Tb: "der"}
    return D


# ------------------------------------------------------------------ angulos de nodo

def hub_geometry(D, v):
    """Para nodos sobre la esfera: azimut de cada barra en el plano tangente
    (lo que se marca en el disco) e inclinacion respecto a ese plano
    (negativo = hacia adentro del domo, positivo = hacia afuera). Para las
    esquinas del marco: direccion de cada barra en planta respecto al dintel
    y pendiente respecto a la horizontal."""
    P = D.verts
    nbrs = sorted({x for e in D.edges if v in e for x in e if x != v})
    if D.type_of[v] == "PE":
        rows = []
        for n in nbrs:
            du, dv, dz = D.uv(v_sub(P[n], P[v]))
            L = math.sqrt(du*du+dv*dv+dz*dz)
            plan = math.degrees(math.atan2(-du, dv if D.side[v] == "izq" else -dv)) if abs(du)+abs(dv) > 1e-9 else None
            slope = math.degrees(math.asin(dz/L))
            rows.append({"to": n, "label": D.edge_label[(min(v, n), max(v, n))], "len": L,
                         "plan_from_head_deg": plan, "slope_deg": slope, "uvz": (du/L, dv/L, dz/L)})
        return {"kind": "marco", "members": rows}
    nrm = v_normalize(v_sub(P[v], D.center))
    ref = v_normalize(v_sub((0, 0, 1), v_scale(nrm, nrm[2]))) if abs(nrm[2]) < 0.999 else (1.0, 0.0, 0.0)
    ref2 = v_cross(nrm, ref)
    rays = []
    for n in nbrs:
        s = v_sub(P[n], P[v])
        tilt = math.degrees(math.asin(v_dot(s, nrm)/v_norm(s)))
        sp = v_sub(s, v_scale(nrm, v_dot(s, nrm)))
        az = math.degrees(math.atan2(v_dot(sp, ref2), v_dot(sp, ref))) % 360
        rays.append({"to": n, "label": D.edge_label[(min(v, n), max(v, n))], "az": az, "tilt": tilt, "len": v_norm(s)})
    rays.sort(key=lambda r: r["az"])
    m = len(rays)
    gaps = [((rays[(k+1) % m]["az"] - rays[k]["az"]) % 360, k) for k in range(m)]
    gmax, kmax = max(gaps)
    if gmax > 120:   # nodo abierto (borde o junto al vano): empezar despues del hueco
        rays = rays[kmax+1:] + rays[:kmax+1]
    az_gaps = [(rays[(k+1) % m]["az"] - rays[k]["az"]) % 360 for k in range(m)]
    return {"kind": "disco", "members": rays, "az_gaps": az_gaps, "open": gmax > 120}


# ------------------------------------------------------------------ piezas y corte

def pieces(D, setback):
    """Lista de piezas a cortar. Barras redondas: largo centro a centro menos
    el retiro del conector en cada extremo. Marco (50x50): postes desde el eje
    del nodo de anclaje hasta el tope del marco; dintel entre caras de postes."""
    out = []
    groups = defaultdict(list)
    for e in D.edges:
        groups[D.edge_label[e]].append(D.edge_len[e])
    for lab in ["A", "B", "C", "V", "K1", "K2"]:
        if lab in groups:
            L = sum(groups[lab])/len(groups[lab])
            out.append({"code": lab, "desc": MEMBER_INFO[lab][1], "section": "tubo redondo 32x2",
                        "n": len(groups[lab]), "L_cc": L, "cut": L - 2*setback})
    if D.door:
        chord = D.edge_len[(min(D.door["a"], D.door["b"]), max(D.door["a"], D.door["b"]))]
        out.append({"code": "P", "desc": MEMBER_INFO["P"][1], "section": "tubo cuadrado 50x50x2", "n": 2,
                    "L_cc": D.door["head_z"], "cut": D.door["head_z"] + FRAME_B/2,
                    "note": "desde el eje del nodo de anclaje hasta el tope del marco; restar el detalle de la placa base"})
        out.append({"code": "D", "desc": MEMBER_INFO["D"][1], "section": "tubo cuadrado 50x50x2", "n": 1,
                    "L_cc": chord, "cut": chord - FRAME_B, "note": "va entre las caras interiores de los postes"})
    return out


def optimal_cutting(lengths, demand, stock, kerf, min_slack=0.02):
    """Minimo de barras comerciales (programacion dinamica exacta)."""
    from itertools import product
    from functools import lru_cache
    names = list(lengths)
    maxn = [int(stock // (lengths[k]+kerf)) for k in names]
    pats = []
    for combo in product(*[range(m+1) for m in maxn]):
        if sum(combo) and sum(c*(lengths[k]+kerf) for c, k in zip(combo, names)) <= stock - min_slack + 1e-9:
            pats.append(combo)
    pats = [p for p in pats if not any(q != p and all(q[i] >= p[i] for i in range(len(names))) for q in pats)]

    @lru_cache(maxsize=None)
    def best(rem):
        if all(r <= 0 for r in rem):
            return (0, ())
        first = next(i for i, r in enumerate(rem) if r > 0)
        top = None
        for combo in pats:
            if combo[first] == 0:
                continue
            n, seq = best(tuple(max(0, r-c) for r, c in zip(rem, combo)))
            if top is None or n+1 < top[0]:
                top = (n+1, seq + (combo,))
        return top
    n, seq = best(tuple(demand[k] for k in names))
    bars = []
    for combo in seq:
        pcs = []
        for c, k in zip(combo, names):
            pcs += [k]*c
        bars.append(pcs)
    # la DP puede cubrir de mas: quitar sobrantes
    need = dict(demand)
    for bar in bars:
        keep = []
        for k in bar:
            if need[k] > 0:
                keep.append(k); need[k] -= 1
        bar[:] = keep
    return bars


def cut_plan(D, setback, stock=6.0, kerf=0.003, min_slack=0.02):
    """Plan de corte del tubo redondo: barras del domo con el optimo exacto, y
    las 6 piezas redondas de la puerta acomodadas en los sobrantes (o en barras
    nuevas si no caben)."""
    pcs = {p["code"]: p for p in pieces(D, setback) if p["section"].startswith("tubo redondo")}
    dome_codes = [c for c in ("A", "B", "C") if c in pcs]
    L = {c: pcs[c]["cut"] for c in pcs}
    bars = optimal_cutting({c: L[c] for c in dome_codes}, {c: pcs[c]["n"] for c in dome_codes}, stock, kerf, min_slack)
    extra = sorted([c for c in pcs if c not in dome_codes for _ in range(pcs[c]["n"])], key=lambda c: -L[c])
    def slack(bar): return stock - sum(L[k]+kerf for k in bar)
    for c in extra:
        fit = [b for b in bars if slack(b) - (L[c]+kerf) >= min_slack]
        if fit:
            min(fit, key=slack).append(c)
        else:
            bars.append([c])
    used = sum(L[k] for b in bars for k in b)
    return {"bars": bars, "n_bars": len(bars), "lengths": L, "used_m": used,
            "waste_pct": (1 - used/(len(bars)*stock))*100, "min_slack_mm": min(slack(b) for b in bars)*1000}


def membrane_summary(D):
    areas = [tri_info(D, t)[1] for t in D.triangles]
    return {"panels": len(D.triangles), "area": sum(areas),
            "removed_area": sum(tri_info(D, t)[1] for t in getattr(D, "removed_triangles", [])),
            "new_area": sum(tri_info(D, t)[1] for t in getattr(D, "new_triangles", []))}


# ------------------------------------------------------------------ armadura

def solve_linear(K, F):
    n = len(F)
    M = [row[:] + [F[i]] for i, row in enumerate(K)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-9*max(1.0, abs(M[c][c])):
            raise ValueError("matriz singular: la estructura tiene un mecanismo")
        M[c], M[p] = M[p], M[c]
        for r in range(c+1, n):
            f = M[r][c]/M[c][c]
            if f:
                Mr, Mc = M[r], M[c]
                for k in range(c, n+1):
                    Mr[k] -= f*Mc[k]
    x = [0.0]*n
    for r in range(n-1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k]*x[k] for k in range(r+1, n)))/M[r][r]
    return x


def section_of(D, e):
    return SECTIONS[MEMBER_INFO[D.edge_label[e]][0]]


def truss(D, loads, E=200e9):
    P = D.verts
    sup = set(D.boundary_verts)
    free = [v for v in D.active if v not in sup]
    dof = {}
    for v in free:
        for k in range(3):
            dof[(v, k)] = len(dof)
    n = len(dof)
    K = [[0.0]*n for _ in range(n)]
    geo = {}
    for e in D.edges:
        a, b = e
        dv = v_sub(P[b], P[a]); L = v_norm(dv); c = v_scale(dv, 1/L)
        k = E*section_of(D, e)["A"]/L
        geo[e] = (c, k)
        for i, j, s in ((a, a, 1), (b, b, 1), (a, b, -1), (b, a, -1)):
            for p in range(3):
                for q in range(3):
                    if (i, p) in dof and (j, q) in dof:
                        K[dof[(i, p)]][dof[(j, q)]] += s*k*c[p]*c[q]
    F = [0.0]*n
    for v, f in loads.items():
        for k in range(3):
            if (v, k) in dof:
                F[dof[(v, k)]] += f[k]
    u = solve_linear(K, F)
    disp = {v: tuple(u[dof[(v, k)]] if (v, k) in dof else 0.0 for k in range(3)) for v in D.active}
    N = {}
    reac = defaultdict(lambda: [0.0, 0.0, 0.0])
    for e, (c, k) in geo.items():
        a, b = e
        N[e] = k*v_dot(c, v_sub(disp[b], disp[a]))
        for v, sg in ((a, 1), (b, -1)):
            if v in sup:
                for i in range(3):
                    reac[v][i] -= sg*N[e]*c[i]
    for v in sup:
        f = loads.get(v, (0, 0, 0))
        for i in range(3):
            reac[v][i] -= f[i]
    return N, dict(reac), disp


def tri_info(D, t):
    P = D.verts
    a, b, c = (P[i] for i in t)
    n = v_cross(v_sub(b, a), v_sub(c, a))
    cen = v_scale(v_add(v_add(a, b), c), 1/3)
    out = v_sub(cen, D.center)
    if v_dot(n, out) < 0:
        n = v_scale(n, -1)
    return v_normalize(n), v_norm(n)/2, cen


def dead_loads(D, door_leaf_kg=60.0):
    L = defaultdict(lambda: [0.0, 0.0, 0.0])
    for e in D.edges:
        w = D.edge_len[e]*section_of(D, e)["kg_m"]*G
        for v in e:
            L[v][2] -= w/2
    for v in D.active:
        L[v][2] -= 0.521*G
    for t in D.triangles:
        _, area, _ = tri_info(D, t)
        for v in t:
            L[v][2] -= 0.9*area*G/3
    if D.door:
        for v in (D.door["a"], D.door["Ta"]):
            L[v][2] -= door_leaf_kg*G/2
    return L


def cp_dome(D, cen, wind, cpA=0.6, cpB=-1.1, cpC=-0.4):
    s = -v_dot(v_normalize(v_sub(cen, D.center)), wind)   # +1 barlovento, 0 cresta, -1 sotavento
    return cpB + (cpA-cpB)*s if s >= 0 else cpB + (cpC-cpB)*(-s)


def wind_loads(D, wind, q, cpi, door_closed):
    L = defaultdict(lambda: [0.0, 0.0, 0.0])
    faces = list(D.triangles)
    door_tris = []
    if door_closed and D.door:
        a, b, Tb, Ta = D.door["opening"]
        door_tris = [(a, b, Tb), (a, Tb, Ta)]
    for t in faces + door_tris:
        n, area, cen = tri_info(D, t)
        cp = cp_dome(D, cen, wind) - cpi       # neto: externa menos interna (positivo empuja hacia adentro)
        f = v_scale(n, -cp*q*area)
        for v in t:
            for k in range(3):
                L[v][k] += f[k]/3
    return L


def combine(*cases, factors=None):
    out = defaultdict(lambda: [0.0, 0.0, 0.0])
    for c, fac in zip(cases, factors or [1.0]*len(cases)):
        for v, x in c.items():
            for k in range(3):
                out[v][k] += fac*x[k]
    return out


def aisc_phiPn(sec, L, Fy=228e6, E=200e9):
    sl = L/sec["r"]
    Fe = math.pi**2*E/sl**2
    Fcr = 0.658**(Fy/Fe)*Fy if Fy/Fe <= 2.25 else 0.877*Fe
    return 0.9*Fcr*sec["A"], sl


def run_structure(D, V_kmh=100.0, verbose=True):
    q = 0.613*(V_kmh/3.6)**2
    dead = dead_loads(D)
    cases = {"peso propio": dead,
             "peso propio + 100 kg en el apice": combine(dead, {max(D.active, key=lambda v: D.verts[v][2]): (0, 0, -100*G)})}
    if D.door:
        cases["peso propio + 100 kg colgando del dintel"] = combine(dead, {D.door["Ta"]: (0, 0, -50*G), D.door["Tb"]: (0, 0, -50*G)})
        u = D.door["u"]; vd = D.door["v"]
    else:
        # misma referencia angular que la version con puerta (azimut del nodo DOOR_HUB)
        u = v_normalize((D.verts[DOOR_HUB][0], D.verts[DOOR_HUB][1], 0.0)); vd = v_cross((0.0, 0.0, 1.0), u)
    for k in range(12):
        ang = math.radians(30*k)
        # direccion HACIA donde sopla el viento; k=0: viento de frente contra la puerta (sopla hacia -u)
        w = v_normalize(v_add(v_scale(u, -math.cos(ang)), v_scale(vd, -math.sin(ang))))
        if D.door:
            # puerta abierta: presion interna = 0.9 x presion externa en el vano
            a, b, Tb, Ta = D.door["opening"]
            cen_door = v_scale(v_add(v_add(D.verts[a], D.verts[b]), v_add(D.verts[Ta], D.verts[Tb])), 0.25)
            cpi_open = 0.9*cp_dome(D, cen_door, w)
        else:
            cpi_open = 0.55      # supuesto de la auditoria: una abertura a barlovento
        for closed, cpi, tag in ((True, 0.18, "cerrada, int +0.18"), (True, -0.18, "cerrada, int -0.18"), (False, cpi_open, f"abierta, int {cpi_open:+.2f}")):
            wl = wind_loads(D, w, q, cpi, closed)
            cases[f"viento {30*k:3d}° ({tag})"] = combine(dead, wl, factors=[0.9, 1.0])
    results = {}
    for name, loads in cases.items():
        N, reac, disp = truss(D, loads)
        results[name] = (N, reac, disp)
    return results, q


def envelope(D, results):
    env = {e: {"comp": 0.0, "tens": 0.0} for e in D.edges}
    anc = {v: {"up": 0.0, "down": 0.0, "shear": 0.0} for v in D.boundary_verts}
    dmax = 0.0
    for name, (N, reac, disp) in results.items():
        for e, n in N.items():
            env[e]["comp"] = max(env[e]["comp"], -n); env[e]["tens"] = max(env[e]["tens"], n)
        for v, r in reac.items():
            anc[v]["up"] = max(anc[v]["up"], -r[2]); anc[v]["down"] = max(anc[v]["down"], r[2])
            anc[v]["shear"] = max(anc[v]["shear"], math.hypot(r[0], r[1]))
        dmax = max(dmax, max(v_norm(x) for x in disp.values()))
    return env, anc, dmax


# ------------------------------------------------------------------ chequeos

def clearance(D, half_width=None, z_top=None):
    """Caja del paso libre: desde el plano de la puerta hacia adentro hasta
    donde el propio domo ya da la altura. Ninguna barra (como cilindro) ni
    panel puede entrar en ella."""
    P = D.verts
    a, b = D.door["a"], D.door["b"]
    u_door = D.uv(P[a])[0]
    chord_half = abs(D.uv(P[a])[1])
    half_width = half_width or (chord_half - FRAME_B/2 - 0.005)
    z_top = z_top or (D.door["head_z"] - FRAME_B/2 - 0.005)
    Rz = D.R; z0 = -D.center[2]
    # fin del paso: donde la esfera da z_top en el borde del paso
    rho_end = math.sqrt(Rz*Rz - (z_top+z0)**2)
    u_end = math.sqrt(max(0.0, rho_end**2 - half_width**2))
    box = (u_end, u_door - FRAME_B/2 - 0.005, -half_width, half_width, 0.02, z_top)

    def inside(p, pad=0.0):
        uu, vv, zz = D.uv(p)
        return (box[0]+pad < uu < box[1]-pad and box[2]+pad < vv < box[3]-pad and box[4]+pad < zz < box[5]-pad)

    bad = []
    for e in D.edges:
        r = section_of(D, e)["c"]
        for i in range(0, 201):
            p = v_add(P[e[0]], v_scale(v_sub(P[e[1]], P[e[0]]), i/200))
            # inflar: un punto a menos de r de la caja tambien choca
            uu, vv, zz = D.uv(p)
            if (box[0]-r < uu < box[1]+r and box[2]-r < vv < box[3]+r and box[4]-r < zz < box[5]+r) and \
               not (e in [(min(D.door['a'], D.door['b']), max(D.door['a'], D.door['b']))]):
                bad.append(("barra", e)); break
    for t in D.triangles:
        A, B, C = (P[i] for i in t)
        hit = False
        for i in range(0, 41):
            for j in range(0, 41-i):
                p = v_add(v_add(v_scale(A, 1-(i+j)/40), v_scale(B, i/40)), v_scale(C, j/40))
                if inside(p):
                    hit = True; break
            if hit: break
        if hit:
            bad.append(("panel", t))
    return box, bad


def closed_surface(D):
    cnt = Counter()
    for t in D.triangles:
        for x, y in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            cnt[(min(x, y), max(x, y))] += 1
    a, b, Tb, Ta = D.door["opening"]
    door_edges = {(min(x, y), max(x, y)) for x, y in ((a, Ta), (b, Tb), (Ta, Tb), (a, b))}
    base_edges = {e for e in D.edges if e[0] in D.boundary_verts and e[1] in D.boundary_verts}
    open_edges = [e for e, c in cnt.items() if c == 1 and e not in door_edges and e not in base_edges]
    over = [e for e, c in cnt.items() if c > 2]
    return open_edges, over


def fixed_in_3d(D, v, nbrs, tol=1e-3):
    dirs = [v_normalize(v_sub(D.verts[u], D.verts[v])) for u in nbrs]
    for i in range(len(dirs)):
        for j in range(i+1, len(dirs)):
            for k in range(j+1, len(dirs)):
                if abs(v_dot(dirs[i], v_cross(dirs[j], dirs[k]))) > tol:
                    return True
    return False


def bending_door_frame(D, q):
    """Viento sobre la puerta cerrada (Cp neto 0.6 + 0.18 interna, redondeado
    a 0.9 q) repartido a los 2 postes como carga uniforme; el dintel toma la
    franja de arriba. Simplemente apoyados (conservador)."""
    a, b, Tb, Ta = D.door["opening"]
    w_clear = D.edge_len[(min(a, b), max(a, b))] - FRAME_B
    h_clear = D.door["head_z"] - FRAME_B/2
    p = 0.9*q
    sec = SECTIONS["cuad50x2"]
    w_post = p*w_clear/2
    M_post = w_post*D.door["head_z"]**2/8
    w_head = p*h_clear/4
    M_head = w_head*w_clear**2/8
    return {"p_Pa": p, "M_post": M_post, "sig_post": M_post/sec["S"]/1e6,
            "M_head": M_head, "sig_head": M_head/sec["S"]/1e6,
            "clear_w": w_clear, "clear_h": h_clear}


def main():
    D = build_dome_with_door()
    dd = D.door
    P = D.verts
    print(f"Puerta sobre el nodo #{dd['hub']} (azimut {dd['azimuth_deg']:.1f}°). Postes en #{dd['a']} (izq) y #{dd['b']} (der).")
    print(f"Se quitan los nodos #{dd['removed_nodes'][0]} y #{dd['removed_nodes'][1]} y {len(dd['removed_edges'])} barras. "
          f"Esquinas del marco: #{dd['Ta']} (izq) y #{dd['Tb']} (der). Nodo sobre el vestibulo: #{dd['top']}.\n")

    print("== 1. Conteo ==")
    cnt = Counter(D.edge_label.values())
    print("   barras por tipo:", dict(sorted(cnt.items())))
    check("barras del domo tras la puerta: A48 B37 C25 (se quitan 2A 3B 5C)",
          (cnt["A"], cnt["B"], cnt["C"]) == (48, 37, 25), f"A{cnt['A']} B{cnt['B']} C{cnt['C']}")
    check("umbral: la barra B del piso entre los postes se conserva",
          (min(dd['a'], dd['b']), max(dd['a'], dd['b'])) in D.edge_label)

    print("\n== 2. Paso libre de la puerta ==")
    box, bad = clearance(D)
    a, b = dd["a"], dd["b"]
    fr = bending_door_frame(D, 1.0)
    print(f"   vano libre entre caras del marco: {fr['clear_w']*100:.1f} cm de ancho x {fr['clear_h']*100:.1f} cm de alto")
    print(f"   caja de paso revisada: de {box[1]:.3f} m a {box[0]:.3f} m del centro, ancho {2*box[3]:.3f} m, alto {box[5]:.3f} m")
    check("ninguna barra ni panel invade el paso de la puerta", not bad, f"{len(bad)} interferencias: {bad[:4]}")
    check("vano libre >= 1.10 x 2.05 m (cabe puerta de 1.00 x 2.00 con su marco)",
          fr["clear_w"] >= 1.10 and fr["clear_h"] >= 2.05, f"{fr['clear_w']:.3f} x {fr['clear_h']:.3f} m")

    print("\n== 3. Superficie y estabilidad ==")
    open_edges, over = closed_surface(D)
    check("membrana cerrada: cada arista con 2 paneles (salvo base y vano)", not open_edges and not over,
          f"abiertas {open_edges} · de mas {over}")
    loose = []
    for v in D.active:
        if v in D.boundary_verts:
            continue
        nb = [x for e in D.edges if v in e for x in e if x != v]
        if not fixed_in_3d(D, v, nb):
            loose.append(v)
    check("cada nodo no anclado tiene >=3 barras no coplanares", not loose, f"{loose}")

    print("\n== 4. Armadura espacial (peso propio, persona, viento 12 direcciones x puerta abierta/cerrada) ==")
    results, q = run_structure(D)
    env, anc, dmax = envelope(D, results)
    worst = None
    for e in D.edges:
        sec = section_of(D, e)
        phiPn, sl = aisc_phiPn(sec, D.edge_len[e])
        ut = env[e]["comp"]/phiPn
        if worst is None or ut > worst[0]:
            worst = (ut, e, env[e]["comp"], phiPn)
    check("matriz de rigidez no singular en todos los casos (sin mecanismos)", True, f"{len(results)} casos resueltos")
    print(f"   desplazamiento maximo {dmax*1000:.2f} mm")
    ut, e, c, cap = worst
    check("ninguna barra supera el 50% de su capacidad a compresion (AISC, Fy 228 MPa)", ut < 0.5,
          f"la mas exigida: #{e[0]}-#{e[1]} ({D.edge_label[e]}) {c/G:.0f} kgf de {cap/G:.0f} kgf = {ut*100:.0f}%")
    by_lab = defaultdict(float)
    for e in D.edges:
        by_lab[D.edge_label[e]] = max(by_lab[D.edge_label[e]], env[e]["comp"])
    print("   compresion maxima por tipo de pieza:", {k: round(v/G, 1) for k, v in sorted(by_lab.items())}, "kgf")
    # mismo barrido sobre el domo sin puerta, para ver cuanto cambia la puerta
    D0 = build_dome_plain()
    res0, _ = run_structure(D0)
    env0, anc0, _ = envelope(D0, res0)
    by_lab0 = defaultdict(float)
    for e0 in D0.edges:
        by_lab0[D0.edge_label[e0]] = max(by_lab0[D0.edge_label[e0]], env0[e0]["comp"])
    print("   mismo barrido SIN puerta, compresion maxima por tipo:", {k: round(v/G, 1) for k, v in sorted(by_lab0.items())}, "kgf")
    print("   anclajes (envolvente de los 39 casos, kgf):   con puerta            sin puerta")
    for v in sorted(D.boundary_verts, key=lambda v: -max(anc[v]["up"], anc[v]["shear"]))[:6]:
        tag = " poste" if v in (a, b) else "      "
        print(f"     #{v:>2}{tag}  arranque {anc[v]['up']/G:6.1f}  corte {anc[v]['shear']/G:6.1f}"
              f"   arranque {anc0[v]['up']/G:6.1f}  corte {anc0[v]['shear']/G:6.1f}")
    up = max(x["up"] for x in anc.values()); sh = max(x["shear"] for x in anc.values())
    up0 = max(x["up"] for x in anc0.values()); sh0 = max(x["shear"] for x in anc0.values())
    print(f"   maximos: arranque {up/G:.1f} kgf (sin puerta {up0/G:.1f}) · corte {sh/G:.1f} kgf (sin puerta {sh0/G:.1f})")
    # perno M12 A307 / 4.6 (AISC J3): phi Fnt Ab y phi Fnv Ab, contra la demanda con los FS del .md
    Ab = math.pi/4*0.012**2
    phiT = 0.75*310e6*Ab; phiV = 0.75*188e6*Ab
    check("perno M12 a traccion: arranque max x 2.5 < capacidad del acero", up*2.5 < phiT,
          f"{up*2.5/G:.0f} kgf < {phiT/G:.0f} kgf")
    check("perno M12 a corte: corte max x 2.0 < capacidad del acero", sh*2.0 < phiV,
          f"{sh*2.0/G:.0f} kgf < {phiV/G:.0f} kgf")
    print("   (el arrancamiento del concreto y el peso de los pilotes siguen siendo trabajo del ingeniero)")
    D.analysis = {"env": env, "anc": anc, "anc0": anc0, "env0": env0, "by_lab": dict(by_lab), "by_lab0": dict(by_lab0),
                  "up": up, "sh": sh, "up0": up0, "sh0": sh0, "worst": worst, "dmax": dmax, "q": q}

    print("\n== 5. Flexion del marco por viento sobre la puerta cerrada ==")
    fb = bending_door_frame(D, q)
    check("postes 50x50x2: esfuerzo por flexion < 0.6 Fy (137 MPa)", fb["sig_post"] < 137,
          f"M={fb['M_post']:.0f} N·m, {fb['sig_post']:.0f} MPa")
    check("dintel 50x50x2: esfuerzo por flexion < 0.6 Fy (137 MPa)", fb["sig_head"] < 137,
          f"M={fb['M_head']:.0f} N·m, {fb['sig_head']:.0f} MPa")
    alt = SECTIONS["tubo32x2"]
    print(f"   (con tubo redondo 32x2 los postes llegarian a {fb['M_post']/alt['S']/1e6:.0f} MPa: por eso el marco va en 50x50)")

    print("\n== 6. Piezas y corte (retiro de 5.0 cm por extremo como ejemplo) ==")
    for p_ in pieces(D, 0.05):
        print(f"   {p_['code']:>2} x{p_['n']:<3} {p_['section']:22s} centro a centro {p_['L_cc']*100:7.2f} cm   corte {p_['cut']*100:7.2f} cm")
    for sb in (0.035, 0.05, 0.065):
        cp = cut_plan(D, sb)
        print(f"   retiro {sb*100:.1f} cm: {cp['n_bars']} barras de 6 m de tubo 32x2 (desperdicio {cp['waste_pct']:.1f}%, "
              f"holgura minima {cp['min_slack_mm']:.0f} mm) + 1 barra de 6 m de 50x50x2 para el marco")
    ms = membrane_summary(D)
    print(f"   membrana: {ms['panels']} paneles, {ms['area']:.2f} m2 (se quitan {ms['removed_area']:.2f} m2, "
          f"se agregan {ms['new_area']:.2f} m2 del vestibulo)")

    print("\n" + "="*60)
    if FAILS:
        print(f"RESULTADO: {len(FAILS)} chequeo(s) FALLARON: {FAILS}")
        sys.exit(1)
    print("RESULTADO: la puerta pasa todos los chequeos (con los supuestos ilustrativos del .md).")


if __name__ == "__main__":
    main()
