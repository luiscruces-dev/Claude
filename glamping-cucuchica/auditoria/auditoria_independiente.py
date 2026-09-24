"""
Auditoria independiente del domo 3V — Cucuchica.

Corre: `python3 auditoria_independiente.py`  (Python estandar, sin numpy).

Independiente a proposito: NO importa dome_model.py. Construye el icosaedro
por otro camino (vertice arriba directo en coordenadas cilindricas, anillos
de 5 vertices a z = +-1/sqrt(5)), subdivide, corta y escala por su cuenta, y
compara contra los valores publicados en domo-3v-cucuchica.md. Ademas calcula
lo que el documento original no calcula o calcula mal:

  1. Geometria base (R, barras, nodos, paneles, areas, volumen real del poliedro)
  2. Angulos de nodo: 3D (entre barras) vs. azimut en el plano tangente
     (lo que de verdad se marca en un disco plano) + inclinacion de pestana
  3. Retiro minimo de corte por choque de tubos en el nodo
  4. Lista de corte: optimo exacto para barras de 6 m y 12 m, y holgura real
  5. Alturas reales sobre el piso de cada anillo de armado
  6. Replanteo de los 15 anclajes (azimut, radio, X, Y)
  7. Estabilidad 3D de cada nodo durante el armado (2 barras no bastan en 3D)
  8. Pandeo: Euler vs. capacidad de diseno (AISC 360 cap. E)
  9. Analisis de armadura espacial (rigidez directa) con las cargas del .md
 10. Viento: sensibilidad a Cp de cresta y presion interna
 11. Membrana: area real con margen de costura
 12. Altura libre util (headroom) dentro del domo

Escribe auditoria_datos.json (lo usa el reporte visual) e imprime el reporte.
Nada de esto sustituye al ingeniero estructural: es una auditoria de los
numeros, con los mismos supuestos ilustrativos del documento original.
"""

import json
import math
import os
from collections import defaultdict, Counter
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81

# ---------------------------------------------------------------- vectores

def add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def mul(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a, a))
def unit(a):
    n = norm(a)
    return (a[0]/n, a[1]/n, a[2]/n)
def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(a, b)/(norm(a)*norm(b))))))


# ---------------------------------------------------------------- 1. geometria

def icosahedron_vertex_up():
    """Icosaedro con un vertice en +z, construido directo (no por permutaciones
    de PHI como dome_model.py): polo, anillo superior a z=1/sqrt5, anillo
    inferior girado 36 grados a z=-1/sqrt5, polo inferior."""
    z = 1/math.sqrt(5); r = 2/math.sqrt(5)
    top = (0.0, 0.0, 1.0); bot = (0.0, 0.0, -1.0)
    U = [(r*math.cos(math.radians(72*k)), r*math.sin(math.radians(72*k)), z) for k in range(5)]
    L = [(r*math.cos(math.radians(72*k+36)), r*math.sin(math.radians(72*k+36)), -z) for k in range(5)]
    faces = []
    for k in range(5):
        k1 = (k+1) % 5
        faces.append((top, U[k], U[k1]))
        faces.append((U[k], U[k1], L[k]))
        faces.append((L[k], L[k1], U[k1]))
        faces.append((bot, L[k1], L[k]))
    return faces


def build(freq=3, base_diameter=6.0):
    faces = icosahedron_vertex_up()
    pts, key2i, tris = [], {}, []

    def idx(p):
        p = unit(p)
        k = tuple(round(c, 8) for c in p)
        if k not in key2i:
            key2i[k] = len(pts); pts.append(p)
        return key2i[k]

    for A, B, C in faces:
        g = {}
        for i in range(freq+1):
            for j in range(freq+1-i):
                k = freq-i-j
                g[(i, j)] = idx(mul(add(add(mul(A, k), mul(B, i)), mul(C, j)), 1/freq))
        for i in range(freq):
            for j in range(freq-i):
                tris.append((g[(i, j)], g[(i+1, j)], g[(i, j+1)]))
                if i+j < freq-1:
                    tris.append((g[(i+1, j)], g[(i+1, j+1)], g[(i, j+1)]))

    full = {"V": len(pts), "F": len(tris),
            "E": len({tuple(sorted(e)) for t in tris for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))})}

    rows = sorted({round(p[2], 6) for p in pts}, reverse=True)
    # fila de corte: la primera fila por encima del ecuador que cierra el casquete
    # sin voladizo = la fila positiva mas baja (z>0)
    zc = min(r for r in rows if r > 1e-9)
    keep_t = [t for t in tris if all(pts[i][2] >= zc - 1e-7 for i in t)]
    used = sorted({i for t in keep_t for i in t})
    rm = {o: n for n, o in enumerate(used)}
    R = (base_diameter/2)/math.sqrt(1-zc*zc)
    P = [mul(pts[i], R) for i in used]
    T = [tuple(rm[i] for i in t) for t in keep_t]
    E = sorted({tuple(sorted(e)) for t in T for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))})
    z0 = zc*R  # plano de los nodos bajos
    return {"R": R, "P": P, "T": T, "E": E, "z0": z0, "full": full, "rows": rows}


def classify_lengths(d, tol=0.003):
    P, E = d["P"], d["E"]
    L = {e: norm(sub(P[e[0]], P[e[1]])) for e in E}
    groups = []
    for e in sorted(E, key=lambda e: -L[e]):
        for g in groups:
            if abs(g["L"] - L[e]) < tol:
                g["e"].append(e); break
        else:
            groups.append({"L": L[e], "e": [e]})
    lab = {}
    summary = {}
    for g, name in zip(groups, "ABCDEF"):
        for e in g["e"]:
            lab[e] = name
        summary[name] = {"L": sum(L[e] for e in g["e"])/len(g["e"]), "n": len(g["e"]),
                         "spread_mm": (max(L[e] for e in g["e"]) - min(L[e] for e in g["e"]))*1000}
    d["L"], d["lab"], d["struts"] = L, lab, summary


def polyhedron_volume(d):
    """Volumen real del poliedro (caras planas, no casquete esferico): el domo
    es un campo de alturas sobre el piso, asi que V = suma sobre caras de
    (area proyectada en planta) x (altura media de sus 3 vertices sobre el piso).
    Incluye la cuña bajo los 5 nodos altos del zigzag (cerrada con faldon)."""
    P, T, z0 = d["P"], d["T"], d["z0"]
    vol = 0.0
    for t in T:
        a, b, c = (P[i] for i in t)
        axy = abs((b[0]-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(b[1]-a[1]))/2
        vol += axy*((a[2]+b[2]+c[2])/3 - z0)
    # el poligono de borde en planta es algo menor que el circulo; el faldon
    # bajo el zigzag queda contado porque las caras se proyectan hasta z0
    return vol


# ---------------------------------------------------------------- 2. nodos

def hub_analysis(d):
    P, E, T, lab, L = d["P"], d["E"], d["T"], d["lab"], d["L"]
    adj = defaultdict(set)
    for a, b in E:
        adj[a].add(b); adj[b].add(a)
    edge_tris = Counter()
    for t in T:
        for e in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge_tris[tuple(sorted(e))] += 1
    boundary = sorted({i for e, c in edge_tris.items() if c == 1 for i in e})
    d["boundary"] = boundary
    hubs = {}
    for v in range(len(P)):
        n = unit(P[v])                         # normal radial = eje del disco
        ref = unit(sub((0, 0, 1), mul(n, n[2]))) if abs(n[2]) < 0.999 else (1.0, 0.0, 0.0)
        ref2 = cross(n, ref)
        rays = []
        for u in adj[v]:
            s = sub(P[u], P[v])
            tilt = math.degrees(math.asin(-dot(s, n)/norm(s)))   # bajo el plano tangente
            sp = sub(s, mul(n, dot(s, n)))
            az = math.degrees(math.atan2(dot(sp, ref2), dot(sp, ref))) % 360
            rays.append({"to": u, "label": lab[tuple(sorted((u, v)))], "az": az, "tilt": tilt, "vec": s})
        rays.sort(key=lambda r: r["az"])
        m = len(rays)
        closed = v not in boundary
        # para nodos de borde, arrancar el orden despues del hueco mas grande
        if not closed:
            gaps = [((rays[(k+1) % m]["az"] - rays[k]["az"]) % 360, k) for k in range(m)]
            gmax, kmax = max(gaps)
            rays = rays[kmax+1:] + rays[:kmax+1]
        npairs = m if closed else m-1
        az_gaps = [(rays[(k+1) % m]["az"] - rays[k]["az"]) % 360 for k in range(npairs)]
        ang3d = [ang(rays[k]["vec"], rays[(k+1) % m]["vec"]) for k in range(npairs)]
        hubs[v] = {"degree": m, "closed": closed, "labels": [r["label"] for r in rays],
                   "az_gaps": az_gaps, "ang3d": ang3d, "tilts": [r["tilt"] for r in rays],
                   "z": P[v][2], "rho": math.hypot(P[v][0], P[v][1]),
                   "azimuth_plan": math.degrees(math.atan2(P[v][1], P[v][0])) % 360}
    # tipos por firma
    sig = defaultdict(list)
    for v, h in hubs.items():
        s = (h["degree"], h["closed"], tuple(sorted(h["labels"])), tuple(sorted(round(a, 1) for a in h["ang3d"])))
        sig[s].append(v)
    d["hubs"], d["hub_sig"] = hubs, sig


def name_hub_types(d):
    """Mapea las firmas a los nombres H1..H5 del documento original por su
    descripcion (grado, cerrado/abierto, barras), no por orden de indice."""
    names = {}
    for s, ids in d["hub_sig"].items():
        deg, closed, labs, _ = s
        if deg == 6 and closed and labs == ("A", "A", "B", "B", "B", "C"): n = "H1"
        elif deg == 6 and closed and labs == ("A",)*6: n = "H2"
        elif deg == 5 and closed and labs == ("C",)*5: n = "H3"
        elif deg == 4 and not closed and labs == ("A", "B", "B", "C"): n = "H4"
        elif deg == 4 and not closed and labs == ("A",)*4: n = "H5"
        else: n = f"?{s}"
        names[n] = ids
    d["hub_types"] = names
    d["type_of"] = {v: n for n, ids in names.items() for v in ids}


# ---------------------------------------------------------------- 4. corte

def optimal_cutting(lengths, demand, stock, kerf, min_slack=0.0):
    """Minimo numero de barras comerciales (busqueda exacta por programacion
    dinamica sobre la demanda restante). Cada pieza consume su largo + 1 kerf."""
    names = list(lengths)
    maxn = [int(stock // (lengths[k]+kerf)) for k in names]
    pats = []
    for combo in product(*[range(m+1) for m in maxn]):
        if sum(combo) == 0: continue
        used = sum(c*(lengths[k]+kerf) for c, k in zip(combo, names))
        if used <= stock - min_slack + 1e-9:
            pats.append((combo, stock-used))
    # quitar patrones dominados
    pats = [p for p in pats if not any(all(q[0][i] >= p[0][i] for i in range(len(names))) and q[0] != p[0] for q in pats)]
    from functools import lru_cache
    @lru_cache(maxsize=None)
    def best(rem):
        if all(r <= 0 for r in rem):
            return (0, ())
        top = None
        # forzar a cubrir la primera pieza pendiente (rompe simetria)
        first = next(i for i, r in enumerate(rem) if r > 0)
        for combo, slack in pats:
            if combo[first] == 0: continue
            nxt = tuple(max(0, r-c) for r, c in zip(rem, combo))
            n, seq = best(nxt)
            if top is None or n+1 < top[0]:
                top = (n+1, seq + (combo,))
        return top
    n, seq = best(tuple(demand[k] for k in names))
    patt = Counter(seq)
    min_slack = min(stock - sum(c*(lengths[k]+kerf) for c, k in zip(combo, names)) for combo in patt)
    return {"bars": n, "patterns": [{"count": c, "pieces": dict(zip(names, combo))} for combo, c in patt.most_common()],
            "min_slack_mm": min_slack*1000}


def check_published_pattern(lengths, pattern, stock, kerf):
    used = sum(lengths[k]+kerf for k in pattern)
    return stock - used


# ---------------------------------------------------------------- 8/9. estructura

def aisc_compression(L, A, I, Fy, E=200e9, K=1.0):
    r = math.sqrt(I/A)
    slender = K*L/r
    Fe = math.pi**2*E/slender**2
    if Fy/Fe <= 2.25:
        Fcr = 0.658**(Fy/Fe)*Fy
    else:
        Fcr = 0.877*Fe
    Pn = Fcr*A
    return {"KL_r": slender, "Fe_MPa": Fe/1e6, "Fcr_MPa": Fcr/1e6, "Pn_N": Pn,
            "phiPn_N": 0.9*Pn, "Pn_over_omega_N": Pn/1.67,
            "euler_N": math.pi**2*E*I/(K*L)**2}


def solve_linear(Kmat, F):
    """Eliminacion gaussiana con pivoteo parcial (sistema denso, ~93 GDL)."""
    n = len(F)
    M = [row[:] + [F[i]] for i, row in enumerate(Kmat)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            raise ValueError("matriz singular: mecanismo en la estructura")
        M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        for r in range(c+1, n):
            f = M[r][c]/piv
            if f != 0.0:
                Mr, Mc = M[r], M[c]
                for k in range(c, n+1):
                    Mr[k] -= f*Mc[k]
    x = [0.0]*n
    for r in range(n-1, -1, -1):
        s = M[r][n] - sum(M[r][k]*x[k] for k in range(r+1, n))
        x[r] = s/M[r][r]
    return x


def truss_analysis(d, loads, supports, EA):
    """Armadura espacial articulada (metodo de rigidez directa). loads: {nodo:
    (Fx,Fy,Fz)} en N. supports: nodos con los 3 GDL fijos. Devuelve fuerza
    axial por barra (+ traccion, - compresion) y reacciones."""
    P, E = d["P"], d["E"]
    nn = len(P)
    free = [v for v in range(nn) if v not in supports]
    dof = {}
    for v in free:
        for k in range(3):
            dof[(v, k)] = len(dof)
    n = len(dof)
    K = [[0.0]*n for _ in range(n)]
    for a, b in E:
        dv = sub(P[b], P[a]); Lm = norm(dv); c = mul(dv, 1/Lm)
        k = EA/Lm
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
    disp = {v: tuple(u[dof[(v, k)]] if (v, k) in dof else 0.0 for k in range(3)) for v in range(nn)}
    forces = {}
    reac = defaultdict(lambda: [0.0, 0.0, 0.0])
    for a, b in E:
        dv = sub(P[b], P[a]); Lm = norm(dv); c = mul(dv, 1/Lm)
        N = EA/Lm*dot(c, sub(disp[b], disp[a]))
        forces[(a, b)] = N
        # fuerza que la barra ejerce sobre cada extremo
        for v, sgn in ((a, 1), (b, -1)):
            if v in supports:
                for k in range(3):
                    reac[v][k] -= sgn*N*c[k]
    for v in supports:
        f = loads.get(v, (0, 0, 0))
        for k in range(3):
            reac[v][k] -= f[k]
    return forces, {v: tuple(r) for v, r in reac.items()}, disp


def face_normal_out(d, t):
    P = d["P"]
    a, b, c = (P[i] for i in t)
    n = cross(sub(b, a), sub(c, a))
    cen = mul(add(add(a, b), c), 1/3)
    if dot(n, cen) < 0:
        n = mul(n, -1)
    area = norm(n)/2
    return unit(n), area, cen


def pressure_loads(d, cp_fun, q):
    """Presion de viento sobre cada panel (Cp>0 empuja hacia adentro, Cp<0
    succiona hacia afuera), repartida 1/3 a cada vertice."""
    loads = defaultdict(lambda: [0.0, 0.0, 0.0])
    for t in d["T"]:
        n, area, cen = face_normal_out(d, t)
        cp = cp_fun(n, cen)
        f = mul(n, -cp*q*area)   # cp>0 -> fuerza hacia adentro (-n)
        for v in t:
            for k in range(3):
                loads[v][k] += f[k]/3
    return {v: tuple(f) for v, f in loads.items()}


def gravity_loads(d, kg_per_m_tube, hub_kg, membrane_kg_m2):
    loads = defaultdict(lambda: [0.0, 0.0, 0.0])
    for e in d["E"]:
        w = d["L"][e]*kg_per_m_tube*G
        for v in e:
            loads[v][2] -= w/2
    for v in range(len(d["P"])):
        loads[v][2] -= hub_kg*G
    for t in d["T"]:
        _, area, _ = face_normal_out(d, t)
        for v in t:
            loads[v][2] -= membrane_kg_m2*area*G/3
    return {v: tuple(f) for v, f in loads.items()}


def combine(*cases, factors=None):
    out = defaultdict(lambda: [0.0, 0.0, 0.0])
    factors = factors or [1.0]*len(cases)
    for c, f in zip(cases, factors):
        for v, vec in c.items():
            for k in range(3):
                out[v][k] += f*vec[k]
    return {v: tuple(x) for v, x in out.items()}


# ---------------------------------------------------------------- 7. armado

def erection_stability(d):
    """Replica el orden anillo-por-anillo de dome_build_sequence.py y cuenta
    con cuantas barras hacia estructura YA fija queda cada nodo nuevo. En 3D
    un nodo articulado necesita 3 barras no coplanares; con 2 queda como una
    bisagra (gira alrededor de la linea entre sus 2 apoyos)."""
    P, E = d["P"], d["E"]
    bnd = set(d["boundary"])
    adj = defaultdict(set)
    for a, b in E:
        adj[a].add(b); adj[b].add(a)
    placed = set(bnd)
    levels = sorted({round(P[v][2], 4) for v in range(len(P)) if v not in bnd})
    out = []
    for i, lv in enumerate(levels, start=1):
        new = [v for v in range(len(P)) if v not in bnd and round(P[v][2], 4) == lv]
        sup = {v: sorted(u for u in adj[v] if u in placed) for v in new}
        # rigidez radial: con 3 apoyos, que tan "plano" queda el tripode
        # (angulo minimo de las barras respecto al plano de sus apoyos)
        rows = []
        for v in new:
            s = sup[v]
            info = {"node": v, "type": d["type_of"][v], "supports": len(s)}
            if len(s) >= 3:
                # menor angulo entre barra y el plano de los otros apoyos
                vecs = [unit(sub(P[u], P[v])) for u in s]
                nrm = unit(cross(sub(P[s[1]], P[s[0]]), sub(P[s[2]], P[s[0]])))
                info["tripod_out_of_plane_deg"] = min(abs(90 - ang(vv, nrm)) for vv in vecs)
            rows.append(info)
        placed |= set(new)
        out.append({"ring": i, "z_center_m": lv, "z_floor_m": lv - d["z0"], "nodes": rows})
    return out


# ---------------------------------------------------------------- main

def main():
    report = []
    def say(s=""):
        report.append(s); print(s)
    data = {}
    PUB = {"R": 3.0452, "apex": 2.5225, "floor": 28.274, "vol": 44.07, "membrane": 46.24,
           "tube": 143.80, "A": (125.59, 50), "B": (122.89, 40), "C": (106.16, 30),
           "hubs": {"H1": 20, "H2": 5, "H3": 6, "H4": 10, "H5": 5},
           "H5_rho": 2.9911, "zigzag_cm": 4.86, "perimeter": 18.70,
           "tilt": {"A": 11.90, "B": 11.64, "C": 10.04},
           "ang3d": {"H1": [54.63, 60.71, 60.71, 60.71, 60.71, 54.63], "H2": [58.58]*6,
                     "H3": [70.73]*5, "H4": [54.63, 54.63, 60.71], "H5": [58.58]*3}}

    d = build()
    classify_lengths(d)
    hub_analysis(d)
    name_hub_types(d)
    P, T, E, R, z0 = d["P"], d["T"], d["E"], d["R"], d["z0"]
    S = d["struts"]

    say("="*72)
    say("AUDITORIA INDEPENDIENTE — DOMO 3V CUCUCHICA")
    say("="*72)
    say("\n[1] GEOMETRIA (construccion independiente, sin dome_model.py)")
    say(f"  esfera completa: V={d['full']['V']} E={d['full']['E']} F={d['full']['F']}  (Euler V-E+F={d['full']['V']-d['full']['E']+d['full']['F']})")
    say(f"  casquete: nodos={len(P)} barras={len(E)} paneles={len(T)}  (disco: V-E+F={len(P)-len(E)+len(T)}, debe ser 1)")
    apex = max(p[2] for p in P) - z0
    area_m = sum(face_normal_out(d, t)[1] for t in T)
    tube = sum(d["L"].values())
    vol_poly = polyhedron_volume(d)
    h = apex
    vol_cap = math.pi*h*h*(3*R-h)/3
    checks = [
        ("R esfera (m)", R, PUB["R"], 0.0001),
        ("altura apice (m)", apex, PUB["apex"], 0.0005),
        ("area de piso (m2)", math.pi*9, PUB["floor"], 0.001),
        ("area membrana (m2)", area_m, PUB["membrane"], 0.005),
        ("tubo total (m)", tube, PUB["tube"], 0.005),
    ]
    for k in "ABC":
        checks.append((f"barra {k} (cm)", S[k]["L"]*100, PUB[k][0], 0.005))
    geo_ok = True
    for name, got, pub, tol in checks:
        ok = abs(got-pub) <= tol
        geo_ok &= ok
        say(f"  {'OK ' if ok else 'ERR'} {name:22s} calculado={got:10.4f}  publicado={pub}")
    for k in "ABC":
        ok = S[k]["n"] == PUB[k][1]
        geo_ok &= ok
        say(f"  {'OK ' if ok else 'ERR'} cantidad barra {k:9s} calculado={S[k]['n']:>6d}      publicado={PUB[k][1]}  (dispersion interna {S[k]['spread_mm']:.3f} mm)")
    for n, c in PUB["hubs"].items():
        got = len(d["hub_types"].get(n, []))
        geo_ok &= got == c
        say(f"  {'OK ' if got == c else 'ERR'} nodos {n:16s} calculado={got:>6d}      publicado={c}")
    low = [v for v in d["boundary"] if abs(P[v][2]-z0) < 1e-6]
    high = [v for v in d["boundary"] if v not in low]
    zig = (P[high[0]][2]-z0)*100
    rho_h = math.hypot(P[high[0]][0], P[high[0]][1])
    perim = sum(d["L"][e] for e in E if e[0] in d["boundary"] and e[1] in d["boundary"])
    say(f"  {'OK ' if abs(zig-PUB['zigzag_cm'])<0.01 else 'ERR'} desnivel zigzag (cm)   calculado={zig:10.4f}  publicado={PUB['zigzag_cm']}")
    say(f"  {'OK ' if abs(rho_h-PUB['H5_rho'])<0.0001 else 'ERR'} radio nodos altos (m)  calculado={rho_h:10.4f}  publicado={PUB['H5_rho']}")
    say(f"  {'OK ' if abs(perim-PUB['perimeter'])<0.005 else 'ERR'} perimetro borde (m)    calculado={perim:10.4f}  publicado={PUB['perimeter']}")
    say(f"  NOTA volumen: publicado {PUB['vol']} m3 es el del casquete ESFERICO ({vol_cap:.2f} m3);")
    say(f"       el poliedro real (caras planas) encierra {vol_poly:.2f} m3 ({(vol_poly/vol_cap-1)*100:+.1f}%). Diferencia menor.")
    data["geometry"] = {"R": R, "apex": apex, "membrane": area_m, "tube": tube, "vol_cap": vol_cap,
                        "vol_poly": vol_poly, "struts": {k: {"L_cm": v["L"]*100, "n": v["n"]} for k, v in S.items()},
                        "hub_counts": {n: len(v) for n, v in d["hub_types"].items()}, "all_ok": geo_ok}

    # diferencias entre tipos (el .md dice "12–19 cm")
    dif = sorted([(S["A"]["L"]-S["B"]["L"])*100, (S["A"]["L"]-S["C"]["L"])*100, (S["B"]["L"]-S["C"]["L"])*100])
    say(f"  ERR texto §6: dice que los tipos difieren '12–19 cm'; real: {dif[0]:.2f} / {dif[1]:.2f} / {dif[2]:.2f} cm (A-B / B-C / A-C)")

    # ---------------------------------------------------------- 2. angulos
    say("\n[2] ANGULOS DE NODO — lo que se marca en el disco vs. lo publicado")
    say("  El .md (§3) y el HTML dicen que los angulos 3D entre barras 'son directamente los")
    say("  angulos a marcar alrededor del disco'. En un disco plano tangente a la esfera lo que")
    say("  se marca es el AZIMUT (angulo proyectado en el plano del disco, suma 360°); luego cada")
    say("  pestana se inclina hacia abajo su 'tilt'. Los angulos 3D suman <360° y NO cierran.")
    hub_rows = {}
    for n in ["H1", "H2", "H3", "H4", "H5"]:
        v = d["hub_types"][n][0]
        hh = d["hubs"][v]
        # comprobar que todos los nodos del tipo tengan los mismos azimuts (en algun orden)
        spreads = []
        for w in d["hub_types"][n]:
            a = sorted(round(x, 2) for x in d["hubs"][w]["az_gaps"])
            spreads.append(tuple(a))
        uniform = len(set(spreads)) == 1
        hub_rows[n] = {"labels": hh["labels"], "az": hh["az_gaps"], "ang3d": hh["ang3d"],
                       "tilts": hh["tilts"], "closed": hh["closed"], "count": len(d["hub_types"][n]),
                       "uniform_across_type": uniform}
        say(f"  {n} ({len(d['hub_types'][n])} nodos, barras en orden: {'-'.join(hh['labels'])}{'' if hh['closed'] else ' | abierto hacia el borde'})")
        say(f"     angulo 3D publicado : {' · '.join(f'{x:6.2f}' for x in hh['ang3d'])}   suma {sum(hh['ang3d']):7.2f}°")
        say(f"     AZIMUT a marcar     : {' · '.join(f'{x:6.2f}' for x in hh['az_gaps'])}   suma {sum(hh['az_gaps']):7.2f}°")
        err = [a-b for a, b in zip(hh["az_gaps"], hh["ang3d"])]
        say(f"     error si se marca el 3D: {' · '.join(f'{x:+6.2f}' for x in err)}   (acumulado {sum(err):+.2f}°)")
        say(f"     inclinacion de cada pestana bajo el plano tangente: {' · '.join(f'{t:.2f}' for t in hh['tilts'])}°"
            f"  {'(igual en los ' + str(len(d['hub_types'][n])) + ' nodos)' if uniform else '(VARIA entre nodos del tipo!)'}")
    worst = max(abs(a-b) for n in hub_rows for a, b in zip(hub_rows[n]["az"], hub_rows[n]["ang3d"]))
    lat = math.radians(worst)*S["A"]["L"]*100
    say(f"  -> error maximo por angulo {worst:.2f}°: en el otro extremo de una barra A eso es ~{lat:.1f} cm de desvio lateral.")
    data["hubs"] = hub_rows
    tilt_pub_ok = all(abs(math.degrees(math.asin(S[k]["L"]/(2*R))) - PUB["tilt"][k]) < 0.01 for k in "ABC")
    say(f"  {'OK ' if tilt_pub_ok else 'ERR'} inclinaciones publicadas A/B/C = asin(L/2R): "
        + " / ".join(f"{math.degrees(math.asin(S[k]['L']/(2*R))):.2f}°" for k in "ABC"))

    # ---------------------------------------------------------- 3. retiro de corte
    say("\n[3] RETIRO MINIMO EN CADA EXTREMO (choque de tubos de 32 mm en el nodo)")
    r_tube = 0.016
    min_ang = min(min(h["ang3d"]) for h in d["hubs"].values())
    setback = r_tube/math.tan(math.radians(min_ang/2))
    say(f"  angulo minimo entre barras vecinas: {min_ang:.2f}°  -> los tubos se tocan hasta {setback*100:.1f} cm del centro del nodo")
    say(f"  El .md (§2) dice restar 'entre 1 y 3 cm por extremo'. Con tubo de 32 mm eso es FISICAMENTE")
    say(f"  imposible en H1/H4 (54.63°): los tubos chocarian. Con disco de ⌀13 cm (§3) el tubo arranca")
    say(f"  en el borde del disco: ~6.5 cm + holgura. El retiro real depende del diseno del conector.")
    for sb in (0.03, setback, 0.05, 0.065, 0.08):
        say(f"    retiro {sb*100:4.1f} cm/extremo -> corte A={S['A']['L']*100-2*sb*100:6.2f}  B={S['B']['L']*100-2*sb*100:6.2f}  C={S['C']['L']*100-2*sb*100:6.2f} cm")
    data["setback"] = {"min_angle": min_ang, "min_setback_cm": setback*100}

    # ---------------------------------------------------------- 4. corte
    say("\n[4] LISTA DE CORTE — optimo exacto (3 mm de sierra por pieza)")
    Ls = {k: S[k]["L"] for k in "ABC"}
    dem = {k: S[k]["n"] for k in "ABC"}
    cut = {}
    for stock in (6.0, 12.0):
        res = optimal_cutting(Ls, dem, stock, 0.003)
        cut[str(stock)] = res
        bought = res["bars"]*stock
        say(f"  barras de {stock:.0f} m: optimo = {res['bars']} barras ({bought:.0f} m, desperdicio {(1-tube/bought)*100:.1f}%)")
        for p in res["patterns"]:
            say(f"      {p['count']:2d} x {p['pieces']}")
    # patron publicado mas ajustado
    tight = check_published_pattern(Ls, ["B", "B", "B", "B", "C"], 6.0, 0.003)
    say(f"  Publicado 6 m: 27 barras. Patron 9x[B,B,B,B,C] deja solo {tight*1000:.1f} mm de sobra por barra:")
    say(f"  cualquier barra comercial de 5.99 m, un extremo danado o un disco de corte mas grueso")
    say(f"  arruina la quinta pieza. (Con el largo de corte real, restando conectores, sobra mas.)")
    safe = optimal_cutting(Ls, dem, 6.0, 0.003, min_slack=0.02)
    say(f"  Optimo 6 m exigiendo >=20 mm de sobra en cada barra: {safe['bars']} barras (holgura minima {safe['min_slack_mm']:.0f} mm)")
    for p in safe["patterns"]:
        say(f"      {p['count']:2d} x {p['pieces']}")
    say("  Con el largo REAL de corte (restando el conector en cada extremo), exigiendo >=20 mm de sobra:")
    real_cut = []
    for sb in (0.035, 0.05, 0.065):
        Lr = {k: Ls[k]-2*sb for k in Ls}
        r6 = optimal_cutting(Lr, dem, 6.0, 0.003, min_slack=0.02)
        tot_r = sum(Lr[k]*dem[k] for k in Lr)
        real_cut.append({"setback_cm": sb*100, "bars6": r6["bars"], "patterns": r6["patterns"], "tube_m": tot_r})
        say(f"    retiro {sb*100:.1f} cm/extremo: tubo neto {tot_r:6.2f} m -> {r6['bars']} barras de 6 m  "
            + "  ".join(f"{p['count']}x{p['pieces']}" for p in r6["patterns"]))
    pub12 = 13
    say(f"  Publicado 12 m: 13 barras -> {'coincide con el optimo' if cut['12.0']['bars'] == pub12 else 'NO es el optimo'}.")
    data["cutting"] = {"6": {"published": 27, "optimal": cut["6.0"]["bars"], "patterns": cut["6.0"]["patterns"], "tight_slack_mm": tight*1000,
                             "real_cut": real_cut, "safe_bars": safe["bars"], "safe_patterns": safe["patterns"], "safe_min_slack_mm": safe["min_slack_mm"]},
                       "12": {"published": 13, "optimal": cut["12.0"]["bars"], "patterns": cut["12.0"]["patterns"]}}

    # ---------------------------------------------------------- 5/7. armado
    say("\n[5] ALTURAS DE ARMADO — secuencia_de_armado.md mide desde el CENTRO DE LA ESFERA")
    seq = erection_stability(d)
    say(f"  El piso (nodos bajos) esta {z0:.4f} m por encima del centro de la esfera.")
    for s in seq:
        say(f"  Paso {s['ring']}: el .md dice {s['z_center_m']:.3f} m  ->  altura REAL sobre el piso {s['z_floor_m']:.3f} m  (error {z0*100:.1f} cm)")
    say("\n[7] ESTABILIDAD DE CADA NODO AL APARECER (3D necesita 3 barras no coplanares)")
    unstable = []
    for s in seq:
        sup = Counter(n["supports"] for n in s["nodes"])
        tri = [n.get("tripod_out_of_plane_deg") for n in s["nodes"] if "tripod_out_of_plane_deg" in n]
        extra = f", tripode {min(tri):.1f}°-{max(tri):.1f}° fuera de plano" if tri else ""
        say(f"  Paso {s['ring']}: {dict(sup)} (apoyos: nodos){extra}")
        unstable += [n for n in s["nodes"] if n["supports"] < 3]
    say(f"  -> {len(unstable)} nodos quedan como BISAGRA (2 barras) al aparecer: "
        + ", ".join(f"#{n['node']}({n['type']})" for n in unstable))
    say("     secuencia_de_armado.md y §8.3 afirman '0 nodos necesitan sujecion temporal'. En 3D es falso:")
    say("     los 5 triangulos del paso 1 pueden girar sobre su base hasta que el paso 2 los amarre.")
    data["erection"] = seq
    data["z0"] = z0

    # ---------------------------------------------------------- 6. replanteo
    say("\n[6] REPLANTEO DE LOS 15 ANCLAJES (no existe en el .md aunque §9.2 dice que si)")
    # rotar para que el primer nodo alto quede a 0°
    ring = sorted(d["boundary"], key=lambda v: d["hubs"][v]["azimuth_plan"])
    az0 = d["hubs"][high[0]]["azimuth_plan"]
    anchors = []
    for v in ring:
        hb = d["hubs"][v]
        az = (hb["azimuth_plan"] - az0) % 360
        anchors.append({"node": v, "type": d["type_of"][v], "az": az, "rho": hb["rho"],
                        "x": hb["rho"]*math.cos(math.radians(az)), "y": hb["rho"]*math.sin(math.radians(az)),
                        "dz_cm": (P[v][2]-z0)*100})
    anchors.sort(key=lambda a: a["az"])
    for a in anchors:
        say(f"  #{a['node']:>2} {a['type']}  azimut {a['az']:7.3f}°  radio {a['rho']:.4f} m  X={a['x']:+.4f}  Y={a['y']:+.4f}  dz={a['dz_cm']:+.2f} cm")
    data["anchors"] = anchors

    # ---------------------------------------------------------- 8. pandeo
    say("\n[8] PANDEO DE BARRAS — Euler (publicado) vs. capacidad de diseno AISC 360 cap. E")
    OD, t = 0.032, 0.002
    A = math.pi/4*(OD**2-(OD-2*t)**2)
    I = math.pi/64*(OD**4-(OD-2*t)**4)
    buck = {}
    for Fy, lbl in ((228e6, "Fy 228 MPa (A500 Gr.A redondo)"), (290e6, "Fy 290 MPa (A500 Gr.B redondo)")):
        say(f"  {lbl}:")
        for k in "ABC":
            c = aisc_compression(S[k]["L"], A, I, Fy)
            buck.setdefault(k, {})[lbl] = c
            say(f"    {k} L={S[k]['L']*100:6.2f} cm  KL/r={c['KL_r']:5.1f}  Euler={c['euler_N']/G:6.0f} kgf"
                f"  Pn={c['Pn_N']/G:6.0f} kgf  diseno LRFD phiPn={c['phiPn_N']/G:6.0f} kgf  ASD Pn/Ω={c['Pn_over_omega_N']/G:6.0f} kgf")
    say("  -> '2.7 toneladas' es la carga de pandeo ELASTICO teorica (Euler). Con KL/r≈118 la barra A pandea")
    say("     en rango inelastico: la capacidad de diseno es ~1.3-2.1 t segun metodo y acero, no 2.7 t.")
    say("     Sigue sobrando (ver [9]), pero el .md nunca calculo la fuerza real en las barras.")
    data["buckling"] = {k: {lbl: {kk: vv for kk, vv in c.items()} for lbl, c in v.items()} for k, v in buck.items()}

    # ---------------------------------------------------------- 9. armadura
    say("\n[9] ANALISIS DE ARMADURA ESPACIAL (15 apoyos articulados, nodos articulados)")
    EA = 200e9*A
    supports = set(d["boundary"])
    dead = gravity_loads(d, A*7850, 0.521, 0.9)
    V = 100/3.6
    q = 0.613*V*V
    def cp_uniform(n, cen): return -0.8
    def make_cp_dome(cpA, cpB, cpC, wind=(1.0, 0.0, 0.0)):
        # interpolacion lineal a lo largo del meridiano del viento: barlovento (A)
        # -> cresta (B) -> sotavento (C), constante en arcos perpendiculares al viento.
        def f(n, cen):
            s = dot(unit(cen), wind)      # -1 barlovento ... +1 sotavento (viento hacia +x)
            s = -s
            if s >= 0:   # lado de barlovento: s=1 borde, s=0 cresta
                return cpB + (cpA-cpB)*s
            return cpB + (cpC-cpB)*(-s)
        return f
    cases = {}
    cases["Peso propio"] = dead
    apex_node = max(range(len(P)), key=lambda v: P[v][2])
    cases["Peso propio + 1 persona (100 kg) en el apice"] = combine(dead, {apex_node: (0, 0, -100*G)})
    cases["Viento .md: succion uniforme Cp=-0.8 (sin peso propio)"] = pressure_loads(d, cp_uniform, q)
    cases["Viento: Cp barlovento +0.6 / cresta -1.1 / sotavento -0.4"] = pressure_loads(d, make_cp_dome(0.6, -1.1, -0.4), q)
    cases["Id. + presion interna +0.55 (puerta abierta a barlovento)"] = combine(
        pressure_loads(d, make_cp_dome(0.6, -1.1, -0.4), q), pressure_loads(d, lambda n, c: -0.55, q))
    cases["0.9 Peso propio + 1.0 viento c/ presion interna (arranque)"] = combine(
        dead, pressure_loads(d, make_cp_dome(0.6, -1.1, -0.4), q), pressure_loads(d, lambda n, c: -0.55, q),
        factors=[0.9, 1.0, 1.0])
    truss = {}
    for name, loads in cases.items():
        forces, reac, disp = truss_analysis(d, loads, supports, EA)
        cmin = min(forces.values()); tmax = max(forces.values())
        crit = min(forces, key=forces.get)
        k = d["lab"][crit]
        cap = buck[k]["Fy 228 MPa (A500 Gr.A redondo)"]["phiPn_N"]
        # reaccion z>0: el apoyo empuja el nodo hacia arriba (compresion en el anclaje)
        # reaccion z<0: el anclaje tiene que tirar del nodo hacia abajo (ARRANQUE)
        uplift = max(-r[2] for r in reac.values())
        down = max(r[2] for r in reac.values())
        horiz = max(math.hypot(r[0], r[1]) for r in reac.values())
        net_up = sum(r[2] for r in reac.values())
        net_h = (sum(r[0] for r in reac.values()), sum(r[1] for r in reac.values()))
        load_z = sum(f[2] for f in loads.values())
        assert abs(net_up + load_z) < 1e-6*max(1.0, abs(load_z)) + 1e-6, "equilibrio vertical no cierra"
        dmax = max(norm(u) for u in disp.values())
        truss[name] = {"max_comp_kgf": -cmin/G, "max_tens_kgf": tmax/G, "crit_label": k,
                       "util_comp": -cmin/cap if cmin < 0 else 0.0,
                       "max_uplift_per_node_kgf": max(0.0, uplift)/G, "max_down_per_node_kgf": max(0.0, down)/G,
                       "max_horiz_per_node_kgf": horiz/G, "sum_vertical_kgf": net_up/G, "sum_horizontal_kgf": math.hypot(*net_h)/G, "max_disp_mm": dmax*1000,
                       "reactions": {str(v): [x/G for x in r] for v, r in reac.items()}}
        say(f"  {name}:")
        say(f"     barra mas comprimida {-cmin/G:6.1f} kgf (tipo {k}; {(-cmin/cap if cmin<0 else 0)*100:4.1f}% de phiPn con Fy 228)  "
            f"traccion max {tmax/G:6.1f} kgf  desplaz. max {dmax*1000:.2f} mm")
        say(f"     reaccion por anclaje: arranque max {max(0, uplift)/G:6.1f} kgf  apoyo max {max(0, down)/G:6.1f} kgf  "
            f"horizontal max {horiz/G:6.1f} kgf")
        say(f"     totales (equilibrio verificado): vertical {net_up/G:+7.1f} kgf ({'arranque neto' if net_up < 0 else 'apoyo neto'})  horizontal {math.hypot(*net_h)/G:6.1f} kgf")
    util_max = max(v["util_comp"] for v in truss.values())
    say(f"  -> Barra mas exigida a compresion: {util_max*100:.0f}% de su capacidad de diseno. Como armadura, la")
    say(f"     seccion 32x2 SI alcanza con estos supuestos (el .md tenia razon en eso, sin haberlo calculado).")
    # flexion: una persona parada a media barra (montaje de membrana, soldador trepado)
    Sx = I/(OD/2); Zx = (OD**3-(OD-2*t)**3)/6
    bend = {}
    for k in "ABC":
        Lk = S[k]["L"]
        M = 100*G*Lk/4
        bend[k] = {"M_Nm": M, "sigma_MPa": M/Sx/1e6, "My_Nm_228": Sx*228e6, "Mp_Nm_228": Zx*228e6}
    say(f"  Flexion: 100 kg parados a mitad de una barra A -> M={bend['A']['M_Nm']:.0f} N·m, esfuerzo {bend['A']['sigma_MPa']:.0f} MPa")
    say(f"     (fluencia 228-290 MPa). Una persona sobre una barra la lleva al limite elastico: el armado")
    say(f"     y la instalacion de la membrana NO pueden hacerse caminando sobre las barras -> andamio.")
    data["bending_person"] = bend
    say("  -> El arranque por anclaje con Cp de cresta mas realista + presion interna es mayor que el")
    say("     promedio de 73 kgf/nodo del .md; comparar con 274 kgf de diseno en §9.4 (ver reporte).")
    data["truss"] = truss
    data["wind_q"] = q

    # ---------------------------------------------------------- 10. viento
    say("\n[10] VIENTO — succion de referencia segun Cp y presion interna")
    floor = math.pi*9
    rows = []
    for cp_ext, cpi, lbl in ((-0.8, 0.0, ".md (Cp -0.8, sin presion interna)"),
                             (-1.1, 0.0, "cresta -1.1 (tipico de cupulas rebajadas)"),
                             (-0.8, 0.18, ".md + interna cerrado +0.18"),
                             (-1.1, 0.55, "cresta -1.1 + interna parcialmente abierto +0.55")):
        p = q*(abs(cp_ext)+cpi)
        tot = p*floor/G
        rows.append({"label": lbl, "cp_ext": cp_ext, "cpi": cpi, "p_pa": p, "total_kgf": tot, "per_node_kgf": tot/15})
        say(f"  {lbl:50s}: {p:6.0f} Pa  total ref. {tot:6.0f} kgf  por nodo {tot/15:5.0f} kgf")
    data["wind_table"] = rows

    # ---------------------------------------------------------- 11. membrana
    say("\n[11] MEMBRANA — el .md compra 46.24 m2 x 1.12 = 51.79 m2 y a la vez dice cortar 75 paneles")
    pan = {}
    for n1, sides, cnt in (("P1", (S["A"]["L"], S["A"]["L"], S["B"]["L"]), 45), ("P2", (S["B"]["L"], S["C"]["L"], S["C"]["L"]), 30)):
        a, b, c = sides
        s2 = (a+b+c)/2
        area = math.sqrt(s2*(s2-a)*(s2-b)*(s2-c))
        angs = [math.degrees(math.acos((b*b+c*c-a*a)/(2*b*c))), math.degrees(math.acos((a*a+c*c-b*b)/(2*a*c))),
                math.degrees(math.acos((a*a+b*b-c*c)/(2*a*b)))]
        pan[n1] = {"area": area, "per": a+b+c, "angs": angs, "n": cnt}
    mem = []
    for allow in (0.0, 0.02, 0.03, 0.05):
        tot = 0.0
        for p in pan.values():
            cot = sum(1/math.tan(math.radians(x/2)) for x in p["angs"])
            tot += p["n"]*(p["area"] + p["per"]*allow + allow*allow*cot)
        mem.append({"allow_cm": allow*100, "m2": tot, "vs_budget": tot/51.79})
        say(f"  margen de costura {allow*100:3.0f} cm por lado -> {tot:5.1f} m2 de piezas cortadas (sin contar el desperdicio del rollo) = {tot/51.79*100:5.1f}% de lo presupuestado")
    say("  -> Con solape soldado/cosido de 3-5 cm, solo las piezas ya superan los 51.8 m2 presupuestados.")
    data["membrane"] = {"panels": pan, "allowances": mem, "budget_m2": 51.79}

    # ---------------------------------------------------------- 12. altura libre
    say("\n[12] ALTURA LIBRE UTIL (el domo mide 2.52 m en el centro)")
    head = []
    for hmin in (1.0, 1.5, 1.8, 2.0, 2.1):
        rr = math.sqrt(max(0.0, R*R-(hmin+z0)**2))
        head.append({"h": hmin, "r": rr, "area": math.pi*rr*rr, "pct": rr*rr/9})
        say(f"  altura >= {hmin:.1f} m: dentro de un radio de {rr:.2f} m -> {math.pi*rr*rr:5.1f} m2 ({rr*rr/9*100:4.1f}% del piso)")
    for r in (1.0, 1.5, 2.0, 2.5, 2.8, 2.95):
        say(f"    a {r:.2f} m del centro el techo esta a {math.sqrt(R*R-r*r)-z0:.2f} m")
    say("  -> Una puerta de 2.0 m no cabe en la superficie del domo: necesita portal/vestibulo o muro de")
    say("     arranque, y eso corta barras de la triangulacion. No esta disenado ni calculado.")
    data["headroom"] = head
    data["profile"] = [{"r": r/100, "h": math.sqrt(R*R-(r/100)**2)-z0} for r in range(0, 301, 10)]

    # geometria para el visor del reporte
    data["mesh"] = {"P": [[round(c, 4) for c in p] for p in P], "E": [[a, b, d["lab"][(a, b)]] for a, b in E],
                    "T": [list(t) for t in T], "z0": z0, "type_of": {str(v): n for v, n in d["type_of"].items()}}

    with open(os.path.join(HERE, "auditoria_datos.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(HERE, "auditoria_salida.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    say("\nEscrito: auditoria_datos.json, auditoria_salida.txt")


if __name__ == "__main__":
    main()
