"""
Plataforma del piso y pilotes del domo 3V — Cucuchica.

Corre: `python3 dome_platform.py`  (Python estandar; usa dome_model.py,
dome_door.py y dome_build_sequence.py).

Sistema (de abajo hacia arriba):
- 15 pilotes perimetrales, uno bajo cada anclaje del domo (el perno de cada
  nodo baja directo a su pilote), mas 6 pilotes interiores y 2 del descanso de
  entrada. Cada pilote es un pedestal de concreto armado de 25x25 cm sobre una
  zapata de 50x50x20 cm.
- Viga de anillo de concreto armado de 25x30 cm siguiendo el poligono de los
  15 anclajes. Su cara superior es el piso terminado (nivel 0.00, el de los
  nodos bajos). Amarra la base del domo y su peso resiste el arranque del viento.
- 3 vigas principales de tubo rectangular 100x50x3, paralelas al eje de la
  puerta, apoyadas en la viga de anillo y en los pilotes interiores.
- Viguetas de pino tratado 2x4" cada 40 cm, perpendiculares a las vigas.
- Entablado machihembrado de 1".
- Descanso de entrada de 1.80 x 1.20 m frente a la puerta, con 3 escalones.
- El jacuzzi NO va aqui: va en la terraza, con fundacion propia.

Chequeos (PASS/FAIL, exit 1 si algo falla): viguetas, vigas principales,
entablado, viga de anillo, presion bajo zapatas, arranque por viento en cada
pilote (con las reacciones del domo con puerta de dome_door.py) y sismo
lateral en los pedestales. Supuestos ilustrativos marcados: la capacidad del
suelo y la profundidad de las zapatas los define el estudio de suelo, y el
diseno final lo firma el ingeniero.
"""

import math
import sys
from collections import defaultdict

import dome_build_sequence as seq
import dome_door as door

G = 9.81

# ---------------------------------------------------------------- parametros
# niveles en metros; 0.00 = piso terminado = nivel de los nodos bajos del domo
FREEBOARD = 0.50            # piso sobre el terreno natural (crecidas y ventilacion)
FOOTING_DEPTH = 1.00        # fondo de zapata bajo el terreno — A CONFIRMAR con estudio de suelo
RING_B, RING_H = 0.25, 0.30  # viga de anillo de concreto armado
PED = 0.25                  # pedestal 25x25
FOOT, FOOT_T = 0.50, 0.20   # zapata 50x50x20
DECK_T = 0.025              # tablas machihembradas 1"
JOIST_B, JOIST_H, JOIST_S = 0.038, 0.089, 0.40   # vigueta 2x4" cada 40 cm
BEAM_H, BEAM_B, BEAM_T = 0.100, 0.050, 0.003     # tubo rectangular 100x50x3
BEAM_LINES = (-1.5, 0.0, 1.5)     # posicion transversal (v) de las vigas principales
INNER_PILE_U = (-1.0, 1.0)        # pilotes interiores a lo largo de cada viga
LANDING_W, LANDING_D = 1.80, 1.20
LANDING_PILE_V = 0.75
STEP_RISE, STEP_RUN, STEP_W = FREEBOARD/3, 0.28, 1.20

# cargas (kgf/m2)
LIVE_ROOM = 200.0           # habitacion (personas, cama, muebles)
LIVE_LANDING = 300.0        # acceso
DEAD_FLOOR = 60.0           # tablas + viguetas + acabados + aislante
GAMMA_C, GAMMA_S = 2400.0, 1600.0
Q_ADM = 10000.0             # kgf/m2 = 1.0 kgf/cm2 — SUPUESTO conservador, a confirmar
# materiales
WOOD_FB, WOOD_E = 8.0e6, 9.0e9     # pino tratado estructural (conservador)
STEEL_FY, STEEL_E = 250e6, 200e9
REBAR_FY = 4200.0                  # kgf/cm2
SEISMIC_CS = 0.30*2.5              # Ao x meseta del espectro, sin reduccion (conservador)

FAILS = []
RESULTS = []
VERBOSE = True


def say(*a):
    if VERBOSE:
        print(*a)


def check(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})
    say(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)
    return ok


# ---------------------------------------------------------------- geometria

def rect_tube(h, b, t):
    A = h*b - (h-2*t)*(b-2*t)
    I = (b*h**3 - (b-2*t)*(h-2*t)**3)/12
    return {"A": A, "I": I, "S": I/(h/2), "kg_m": A*7850}


BEAM = rect_tube(BEAM_H, BEAM_B, BEAM_T)
JOIST = {"A": JOIST_B*JOIST_H, "I": JOIST_B*JOIST_H**3/12, "S": JOIST_B*JOIST_H**2/6, "kg_m": JOIST_B*JOIST_H*550}


def offset_polygon(pts, d):
    """Desplaza un poligono convexo (antihorario) d hacia adentro (d>0) o afuera (d<0)."""
    n = len(pts)
    lines = []
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i+1) % n]
        dx, dy = x2-x1, y2-y1
        L = math.hypot(dx, dy)
        nx, ny = -dy/L, dx/L          # normal hacia adentro para poligono antihorario
        lines.append(((x1+nx*d, y1+ny*d), (dx, dy)))
    out = []
    for i in range(n):
        (p, r), (q, s) = lines[i-1], lines[i]
        den = r[0]*s[1] - r[1]*s[0]
        t = ((q[0]-p[0])*s[1] - (q[1]-p[1])*s[0])/den
        out.append((p[0]+t*r[0], p[1]+t*r[1]))
    return out


def chord_range(poly, axis, value):
    """Interseccion de la recta {axis = value} (axis 0 = u, 1 = v) con un
    poligono convexo en coordenadas (u, v): devuelve (min, max) de la otra coord."""
    other = 1-axis
    hits = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i+1) % n]
        if (a[axis]-value)*(b[axis]-value) <= 0 and a[axis] != b[axis]:
            t = (value-a[axis])/(b[axis]-a[axis])
            hits.append(a[other] + t*(b[other]-a[other]))
    return (min(hits), max(hits)) if len(hits) >= 2 else None


def poly_area(poly):
    return abs(sum(poly[i][0]*poly[(i+1) % len(poly)][1] - poly[(i+1) % len(poly)][0]*poly[i][1] for i in range(len(poly))))/2


def simple_span(L, points, w=0.0):
    """Viga simplemente apoyada de largo L con cargas puntuales [(a, P)] y
    uniforme w. Devuelve (R_izq, R_der, M_max, delta_centro_por_EI)."""
    Rb = sum(P*a for a, P in points)/L + w*L/2
    Ra = sum(P for _, P in points) + w*L - Rb
    xs = sorted({0.0, L/2, L} | {a for a, _ in points})
    M = 0.0
    for x in xs:
        m = Ra*x - w*x*x/2 - sum(P*(x-a) for a, P in points if a < x)
        M = max(M, m)
    # flecha al centro (x = L/2) por superposicion, dividida por EI
    d = 5*w*L**4/384
    for a, P in points:
        b = L - a
        aa, bb = (a, b) if a >= b else (b, a)
        x = L/2
        # formula de viga simple con carga P a distancia bb del apoyo mas cercano
        d += P*bb*x*(L*L - bb*bb - x*x)/(6*L)
    return Ra, Rb, M, d


# ---------------------------------------------------------------- diseno

class Platform:
    pass


def build_platform():
    D = door.build_dome_with_door()
    rows = seq.setting_out(D)
    u3, v3 = D.door["u"], D.door["v"]
    U, V = (u3[0], u3[1]), (v3[0], v3[1])

    def to_uv(x, y): return (x*U[0] + y*U[1], x*V[0] + y*V[1])
    def to_xy(u, v): return (u*U[0] + v*V[0], u*U[1] + v*V[1])

    ring = [to_uv(r["x"], r["y"]) for r in rows]          # eje de la viga de anillo (antihorario)
    # asegurar orientacion antihoraria en (u, v)
    if sum(ring[i][0]*ring[(i+1) % 15][1] - ring[(i+1) % 15][0]*ring[i][1] for i in range(15)) < 0:
        ring = ring[::-1]; rows = rows[::-1]
    inner = offset_polygon(ring, RING_B/2)
    outer = offset_polygon(ring, -RING_B/2)

    P = Platform()
    P.D = D; P.rows = rows; P.to_uv = to_uv; P.to_xy = to_xy
    P.ring, P.inner, P.outer = ring, inner, outer

    # -------- pilotes
    piles = []
    for r, (u, v) in zip(rows, ring):
        piles.append({"kind": "perimetral", "anchor": r["node"], "u": u, "v": v})
    for b in BEAM_LINES:
        for uu in INNER_PILE_U:
            piles.append({"kind": "interior", "anchor": None, "u": uu, "v": b})
    a_idx, b_idx = D.door["a"], D.door["b"]
    ua = ring[[r["node"] for r in rows].index(a_idx)][0]
    u_face_out = ua + RING_B/2                 # cara exterior de la viga en la puerta (aprox.)
    u_land_beam = u_face_out + LANDING_D - BEAM_B/2
    for sv in (-LANDING_PILE_V, LANDING_PILE_V):
        piles.append({"kind": "descanso", "anchor": None, "u": u_land_beam, "v": sv})
    # numerar en orden: perimetrales por azimut (el orden del replanteo), luego interiores y descanso
    for i, p in enumerate(piles, start=1):
        p["id"] = i
        p["x"], p["y"] = to_xy(p["u"], p["v"])
    P.piles = piles
    P.landing = {"u0": u_face_out, "u1": u_face_out + LANDING_D, "v0": -LANDING_W/2, "v1": LANDING_W/2,
                 "beam_u": u_land_beam}
    P.steps = [{"u0": P.landing["u1"] + k*STEP_RUN, "u1": P.landing["u1"] + (k+1)*STEP_RUN,
                "z": -(k+1)*STEP_RISE, "v0": -STEP_W/2, "v1": STEP_W/2} for k in range(2)]

    # -------- viguetas (a lo largo de v, cada 40 cm en u)
    u_min = min(p[0] for p in inner); u_max = max(p[0] for p in inner)
    k0 = math.ceil((u_min + 0.15)/JOIST_S); k1 = math.floor((u_max - 0.15)/JOIST_S)
    joists = []
    for k in range(k0, k1+1):
        uk = k*JOIST_S
        rng = chord_range(inner, 0, uk)
        if not rng or rng[1]-rng[0] < 0.3:
            continue
        sup = [rng[0]] + [b for b in BEAM_LINES if rng[0]+0.1 < b < rng[1]-0.1] + [rng[1]]
        joists.append({"u": uk, "v0": rng[0], "v1": rng[1], "supports": sup})
    P.joists = joists

    # -------- vigas principales (a lo largo de u)
    beams = []
    for b in BEAM_LINES:
        rng = chord_range(inner, 1, b)
        sup = [rng[0]] + [uu for uu in INNER_PILE_U if rng[0]+0.1 < uu < rng[1]-0.1] + [rng[1]]
        beams.append({"v": b, "u0": rng[0], "u1": rng[1], "supports": sup})
    P.beams = beams
    P.landing_joists = [{"v": vv, "u0": u_face_out, "u1": u_land_beam} for vv in (-0.8, -0.4, 0.0, 0.4, 0.8)]
    P.levels = {"deck_top": 0.0, "joist_top": -DECK_T, "beam_top": -DECK_T-JOIST_H,
                "beam_bottom": -DECK_T-JOIST_H-BEAM_H, "ring_bottom": -RING_H,
                "ground": -FREEBOARD, "footing_top": -FREEBOARD-FOOTING_DEPTH+FOOT_T,
                "footing_bottom": -FREEBOARD-FOOTING_DEPTH}
    return P


# ---------------------------------------------------------------- cargas

def distribute(P, q_room, q_landing, self_weight):
    """Baja las cargas del piso hasta los pilotes. q en kgf/m2. Devuelve
    reacciones por pilote (kgf) y esfuerzos maximos de cada elemento."""
    out = {"pile": defaultdict(float), "joist": [], "beam": [], "ring": [], "landing_joist": [], "landing_beam": None}
    ring_pts = []           # cargas puntuales sobre la viga de anillo: (u, v, kgf)
    w_j = q_room*JOIST_S + (JOIST["kg_m"] if self_weight else 0.0)
    joist_load_total = 0.0
    beam_pts = defaultdict(list)
    for j in P.joists:
        s = j["supports"]
        for a, b in zip(s[:-1], s[1:]):
            L = b-a
            Ra, Rb, M, dEI = simple_span(L, [], w_j)
            joist_load_total += w_j*L
            out["joist"].append({"u": j["u"], "L": L, "M": M, "d_EI": dEI})
            for vv, R in ((a, Ra), (b, Rb)):
                if vv in BEAM_LINES and vv not in (s[0], s[-1]):
                    beam_pts[vv].append((j["u"], R))
                else:
                    ring_pts.append((j["u"], vv, R))
    # piso que no cae sobre viguetas (franjas junto al anillo): directo al anillo
    area_in = poly_area(P.inner)
    floor_total = q_room*area_in + (JOIST["kg_m"]*sum(j["v1"]-j["v0"] for j in P.joists) if self_weight else 0.0)
    residual = floor_total - joist_load_total
    # vigas principales
    for bm in P.beams:
        s = bm["supports"]
        w = BEAM["kg_m"] if self_weight else 0.0
        for a, b in zip(s[:-1], s[1:]):
            L = b-a
            pts = [(u-a, R) for u, R in beam_pts[bm["v"]] if a <= u < b]
            Ra, Rb, M, dEI = simple_span(L, pts, w)
            out["beam"].append({"v": bm["v"], "L": L, "M": M, "d_EI": dEI})
            for uu, R in ((a, Ra), (b, Rb)):
                if uu in INNER_PILE_U and uu not in (s[0], s[-1]):
                    pid = next(p["id"] for p in P.piles if p["kind"] == "interior" and p["v"] == bm["v"] and p["u"] == uu)
                    out["pile"][pid] += R
                else:
                    ring_pts.append((uu, bm["v"], R))
    # descanso de entrada
    lj = P.landing_joists
    wl = q_landing*(LANDING_W/len(lj)) + (JOIST["kg_m"] if self_weight else 0.0)
    land_beam_pts = []
    for j in lj:
        L = j["u1"]-j["u0"]
        Ra, Rb, M, dEI = simple_span(L, [], wl)
        out["landing_joist"].append({"L": L, "M": M, "d_EI": dEI})
        ring_pts.append((j["u0"] - RING_B/2, j["v"], Ra))
        land_beam_pts.append((j["v"], Rb))
    # viga del descanso entre sus 2 pilotes (voladizos cortos a cada lado: se reparten a los pilotes)
    lp = [p for p in P.piles if p["kind"] == "descanso"]
    wlb = BEAM["kg_m"] if self_weight else 0.0
    L = 2*LANDING_PILE_V
    pts = [(v + LANDING_PILE_V, R) for v, R in land_beam_pts if -LANDING_PILE_V <= v <= LANDING_PILE_V]
    over = sum(R for v, R in land_beam_pts if abs(v) > LANDING_PILE_V) + wlb*(LANDING_W - L)
    Ra, Rb, M, dEI = simple_span(L, pts, wlb)
    # franja del descanso que no cubren las viguetas (entre la viga y el borde): a la viga
    covered = sum(q_landing*(LANDING_W/len(lj))*(j["u1"]-j["u0"]) for j in lj)
    rest = q_landing*LANDING_W*LANDING_D - covered
    out["landing_beam"] = {"L": L, "M": M, "d_EI": dEI}
    out["pile"][lp[0]["id"]] += Ra + over/2 + rest/2
    out["pile"][lp[1]["id"]] += Rb + over/2 + rest/2
    # viga de anillo: tramos entre pilotes perimetrales
    ring = P.ring
    per = [p for p in P.piles if p["kind"] == "perimetral"]
    seg_pts = defaultdict(list)
    for (u, v, R) in ring_pts:
        best = None
        for i in range(15):
            (x1, y1), (x2, y2) = ring[i], ring[(i+1) % 15]
            dx, dy = x2-x1, y2-y1
            L2 = dx*dx+dy*dy
            t = max(0.0, min(1.0, ((u-x1)*dx + (v-y1)*dy)/L2))
            d = math.hypot(x1+t*dx-u, y1+t*dy-v)
            if best is None or d < best[0]:
                best = (d, i, t)
        _, i, t = best
        seg_pts[i].append((t, R))
    perim = sum(math.hypot(ring[(i+1) % 15][0]-ring[i][0], ring[(i+1) % 15][1]-ring[i][1]) for i in range(15))
    for i in range(15):
        (x1, y1), (x2, y2) = ring[i], ring[(i+1) % 15]
        L = math.hypot(x2-x1, y2-y1)
        w = (RING_B*RING_H*GAMMA_C if self_weight else 0.0) + residual/perim
        pts = [(t*L, R) for t, R in seg_pts[i]]
        Ra, Rb, M, _ = simple_span(L, pts, w)
        out["ring"].append({"i": i, "L": L, "M": M})
        out["pile"][per[i]["id"]] += Ra
        out["pile"][per[(i+1) % 15]["id"]] += Rb
    out["floor_total"] = floor_total
    return out


def pile_self(P, p):
    """Peso propio del pilote (pedestal + zapata) y del relleno sobre la zapata, kgf."""
    lv = P.levels
    top = lv["ring_bottom"] if p["kind"] == "perimetral" else lv["beam_bottom"]
    ped_h = top - lv["footing_top"]
    ped = PED*PED*ped_h*GAMMA_C
    foot = FOOT*FOOT*FOOT_T*GAMMA_C
    soil = (FOOT*FOOT - PED*PED)*(lv["ground"] - lv["footing_top"])*GAMMA_S
    return ped, foot, soil, ped_h


def analyse(P):
    dead = distribute(P, DEAD_FLOOR, DEAD_FLOOR, True)
    live = distribute(P, LIVE_ROOM, LIVE_LANDING, False)
    # domo con puerta: reacciones por anclaje (peso propio y envolvente de viento)
    D = P.D
    res, q = door.run_structure(D)
    env, anc, _ = door.envelope(D, res)
    dome_dead = res["peso propio"][1]
    R = {"dead": dead, "live": live, "anc": anc, "dome_dead": dome_dead}
    rows = []
    for p in P.piles:
        ped, foot, soil, ped_h = pile_self(P, p)
        d = dead["pile"][p["id"]]
        l = live["pile"][p["id"]]
        dome_d = dome_dead[p["anchor"]][2]/G if p["anchor"] is not None else 0.0
        up = anc[p["anchor"]]["up"]/G if p["anchor"] is not None else 0.0
        sh = anc[p["anchor"]]["shear"]/G if p["anchor"] is not None else 0.0
        service = d + l + dome_d + ped + foot + soil
        pressure = service/(FOOT*FOOT)
        resist = 0.9*(d + dome_d + ped + foot + soil)
        rows.append(dict(p, D=d, L=l, dome=dome_d, ped=ped, foot=foot, soil=soil, ped_h=ped_h,
                         service=service, pressure=pressure, uplift=up, shear=sh, resist=resist))
    R["piles"] = rows
    R["q"] = q
    return R


# ---------------------------------------------------------------- materiales

def quantities(P, R):
    rows = R["piles"]
    ring_len = sum(math.hypot(P.ring[(i+1) % 15][0]-P.ring[i][0], P.ring[(i+1) % 15][1]-P.ring[i][1]) for i in range(15))
    conc = {"zapatas": len(rows)*FOOT*FOOT*FOOT_T,
            "pedestales": sum(PED*PED*r["ped_h"] for r in rows),
            "viga de anillo": ring_len*RING_B*RING_H}
    # acero de refuerzo (estimado): viga 4 Ø12 + estribos Ø8 c/15; pedestal 4 Ø12 con anclaje + estribos Ø8 c/15;
    # zapata parrilla Ø10 c/15 en 2 direcciones
    kg12, kg10, kg8 = 0.888, 0.617, 0.395
    stir_ring = 2*((RING_B-0.08)+(RING_H-0.08)) + 0.10
    stir_ped = 4*(PED-0.08) + 0.10
    rebar = {"Ø12 (viga de anillo)": 4*ring_len*1.10*kg12,
             "Ø8 estribos viga (c/15 cm)": math.ceil(ring_len/0.15)*stir_ring*kg8,
             "Ø12 pedestales": sum(4*(r["ped_h"] + 0.30 + 0.20)*kg12 for r in rows),
             "Ø8 estribos pedestales (c/15 cm)": sum(math.ceil(r["ped_h"]/0.15)*stir_ped*kg8 for r in rows),
             "Ø10 parrillas de zapata (c/15 cm)": len(rows)*2*4*(FOOT-0.10)*kg10}
    # acero estructural
    beam_pieces = [bm["u1"]-bm["u0"] for bm in P.beams] + [LANDING_W]
    bars100 = first_fit(beam_pieces, 6.0)
    ledger = sum(math.hypot(P.inner[(i+1) % 15][0]-P.inner[i][0], P.inner[(i+1) % 15][1]-P.inner[i][1]) for i in range(15)) + LANDING_W
    steel = {"tubo rectangular 100×50×3 (vigas)": {"piezas": beam_pieces, "barras6m": len(bars100)},
             "angular L 50×50×5 (apoyo de viguetas en la viga de anillo)": {"m": ledger, "barras6m": math.ceil(ledger*1.05/6)},
             "placas embebidas 150×150×8 con 2 pernos (cabeza de pilotes interiores y del descanso)": {"n": 8},
             "asientos de viga L 75×75×6 × 15 cm (extremos de vigas en el anillo)": {"n": 2*len(P.beams)}}
    # madera
    joist_pieces = []
    for j in P.joists:
        mid = 0.0 if j["v0"] < 0 < j["v1"] else None
        if mid is None:
            joist_pieces.append(j["v1"]-j["v0"])
        else:
            joist_pieces += [0.0 - j["v0"], j["v1"] - 0.0]
    joist_pieces += [lj["u1"]-lj["u0"] for lj in P.landing_joists]
    boards_2x4 = first_fit(joist_pieces, 3.05)
    deck_area = poly_area(P.inner) + LANDING_W*LANDING_D
    wood = {"vigueta 2×4\" pino tratado": {"piezas": joist_pieces, "tablas_10pies": len(boards_2x4)},
            "entablado machihembrado 1\"": {"m2": deck_area, "m2_con_desperdicio": deck_area*1.15}}
    return {"concrete": conc, "rebar": rebar, "steel": steel, "wood": wood, "ring_len": ring_len}


def first_fit(pieces, stock, kerf=0.004):
    bars = []
    for p in sorted(pieces, reverse=True):
        for b in bars:
            if sum(b) + len(b)*kerf + p + kerf <= stock:
                b.append(p); break
        else:
            bars.append([p])
    return bars


# ---------------------------------------------------------------- main

def evaluate(verbose=True):
    """Construye, analiza y verifica. Devuelve (P, R, Q, RESULTS)."""
    global VERBOSE
    VERBOSE = verbose
    FAILS.clear(); RESULTS.clear()
    P = build_platform()
    R = analyse(P)
    dead, live = R["dead"], R["live"]
    say(f"Plataforma: {sum(1 for p in P.piles if p['kind']=='perimetral')} pilotes perimetrales, "
          f"{sum(1 for p in P.piles if p['kind']=='interior')} interiores, {sum(1 for p in P.piles if p['kind']=='descanso')} del descanso "
          f"= {len(P.piles)}. {len(P.joists)} lineas de viguetas, {len(P.beams)} vigas principales.")
    lv = P.levels
    say(f"Niveles: piso 0.00 · tope de vigas {lv['beam_top']:+.3f} · fondo de vigas {lv['beam_bottom']:+.3f} · "
          f"fondo viga de anillo {lv['ring_bottom']:+.2f} · terreno {lv['ground']:+.2f} · fondo de zapata {lv['footing_bottom']:+.2f} m\n")

    # equilibrio: todo lo que baja tiene que llegar a pilotes
    area = poly_area(P.inner)
    tot_live = LIVE_ROOM*area + LIVE_LANDING*LANDING_W*LANDING_D
    got_live = sum(live["pile"].values())
    check("equilibrio: la carga viva total llega completa a los pilotes", abs(got_live - tot_live) < 1.0,
          f"{got_live:.0f} de {tot_live:.0f} kgf")

    say("\n== Viguetas 2x4\" cada 40 cm ==")
    jmax = max(dead["joist"], key=lambda j: j["L"])
    M = max(d["M"] + l["M"] for d, l in zip(dead["joist"], live["joist"]))*G
    sig = M/JOIST["S"]
    Lj = jmax["L"]
    dl = max(l["d_EI"] for l in live["joist"])*G/(WOOD_E*JOIST["I"])
    check("flexion de viguetas (muerta + viva) < Fb 8 MPa", sig < WOOD_FB, f"luz max {Lj:.2f} m, {sig/1e6:.1f} MPa")
    check("flecha de viguetas por carga viva < L/360", dl < Lj/360, f"{dl*1000:.1f} mm (limite {Lj/360*1000:.1f} mm)")
    lm = max(d["M"] + l["M"] for d, l in zip(dead["landing_joist"], live["landing_joist"]))*G
    check("viguetas del descanso (300 kgf/m2) < Fb", lm/JOIST["S"] < WOOD_FB, f"{lm/JOIST['S']/1e6:.1f} MPa")

    say("\n== Entablado 1\" sobre viguetas cada 40 cm ==")
    wd = (DEAD_FLOOR + LIVE_ROOM)*G
    Md = wd*JOIST_S**2/8
    Sd = 1.0*DECK_T**2/6
    check("flexion del entablado (franja de 1 m) < Fb", Md/Sd < WOOD_FB, f"{Md/Sd/1e6:.2f} MPa")

    say("\n== Vigas principales, tubo 100x50x3 ==")
    Mb = max(d["M"] + l["M"] for d, l in zip(dead["beam"], live["beam"]))*G
    Lb = max(b["L"] for b in dead["beam"])
    db = max(l["d_EI"] for l in live["beam"])*G/(STEEL_E*BEAM["I"])
    check("flexion de vigas < 0.6 Fy (150 MPa)", Mb/BEAM["S"] < 0.6*STEEL_FY, f"luz max {Lb:.2f} m, {Mb/BEAM['S']/1e6:.0f} MPa")
    check("flecha de vigas por carga viva < L/360", db < Lb/360, f"{db*1000:.1f} mm")
    lb = dead["landing_beam"]; lbl = live["landing_beam"]
    Ml = (lb["M"] + lbl["M"])*G
    check("viga del descanso < 0.6 Fy", Ml/BEAM["S"] < 0.6*STEEL_FY, f"{Ml/BEAM['S']/1e6:.0f} MPa")

    say("\n== Viga de anillo 25x30 con 2 Ø12 por cara ==")
    Mr = max(1.2*d["M"] + 1.6*l["M"] for d, l in zip(dead["ring"], live["ring"]))    # kgf·m mayorado
    d_eff = RING_H - 0.05
    As = 2*1.131                                   # cm2, 2 Ø12
    a = As*REBAR_FY/(0.85*210*RING_B*100)          # cm, f'c 210
    phiMn = 0.9*As*REBAR_FY*(d_eff*100 - a/2)/100  # kgf·m
    check("flexion de la viga de anillo (1.2D+1.6L) < phi·Mn", Mr < phiMn, f"Mu {Mr:.0f} kgf·m, phiMn {phiMn:.0f} kgf·m")
    As_min = 14/REBAR_FY*RING_B*100*d_eff*100
    check("acero minimo por cara (14/fy·b·d)", As >= As_min*0.99, f"{As:.2f} cm2 >= {As_min:.2f} cm2")

    say("\n== Pilotes (pedestal 25x25 sobre zapata 50x50x20) ==")
    rows = R["piles"]
    pmax = max(rows, key=lambda r: r["pressure"])
    check(f"presion bajo zapata (servicio) < {Q_ADM/1e4:.1f} kgf/cm2 supuesto", pmax["pressure"] < Q_ADM,
          f"max {pmax['pressure']/1e4:.2f} kgf/cm2 en pilote {pmax['id']} ({pmax['kind']})")
    per = [r for r in rows if r["kind"] == "perimetral"]
    worst_up = min(per, key=lambda r: r["resist"]/max(r["uplift"], 1e-6))
    fs_up = worst_up["resist"]/worst_up["uplift"]
    check("arranque por viento en cada anclaje: 0.9 x peso que lo retiene >= 1.5 x arranque", fs_up >= 1.5,
          f"peor: pilote {worst_up['id']} (anclaje #{worst_up['anchor']}), retiene {worst_up['resist']:.0f} kgf contra "
          f"{worst_up['uplift']:.0f} kgf -> FS {fs_up:.1f}")
    # sismo lateral: cada pilote toma la inercia de su propia carga (muerta + 25% viva), en voladizo desde la zapata
    Wtot = sum(r["D"] + 0.25*r["L"] + r["dome"] + r["ped"] for r in rows)
    Mmax = max(SEISMIC_CS*(r["D"] + 0.25*r["L"] + r["dome"] + r["ped"]/2)*r["ped_h"] for r in rows)
    As_p = 2*1.131
    phiMp = 0.9*As_p*REBAR_FY*(PED*100 - 6)/100
    check("sismo lateral (Cs 0.75, sin reduccion) en pedestales 4 Ø12", Mmax < phiMp,
          f"M max {Mmax:.0f} kgf·m, phiMn {phiMp:.0f} kgf·m; peso sismico total {Wtot/1000:.1f} t")
    say(f"   carga maxima por pilote en servicio: {max(r['service'] for r in rows):.0f} kgf; "
          f"piso completo (muerta + viva): {(dead['floor_total'] + live['floor_total'])/1000:.1f} t")

    Q = quantities(P, R)
    say("\n== Cantidades ==")
    say("   concreto (m3):", {k: round(v, 2) for k, v in Q["concrete"].items()}, f"total {sum(Q['concrete'].values()):.2f} m3")
    say("   acero de refuerzo (kg):", {k: round(v) for k, v in Q["rebar"].items()}, f"total {sum(Q['rebar'].values()):.0f} kg")
    for k, v in Q["steel"].items():
        say(f"   {k}: {v}")
    for k, v in Q["wood"].items():
        vv = dict(v); vv.pop("piezas", None)
        say(f"   {k}: {vv}")

    R["metrics"] = {"joist_sig": sig, "joist_L": Lj, "joist_d": dl, "beam_sig": Mb/BEAM["S"], "beam_L": Lb, "beam_d": db,
                    "ring_Mu": Mr, "ring_phiMn": phiMn, "p_max": pmax["pressure"], "fs_up": fs_up, "worst_up": worst_up,
                    "seis_M": Mmax, "seis_phiMn": phiMp, "W_seis": Wtot}
    return P, R, Q, list(RESULTS)


def main():
    evaluate(verbose=True)
    print("\n" + "="*60)
    if FAILS:
        print(f"RESULTADO: {len(FAILS)} chequeo(s) FALLARON: {FAILS}")
        sys.exit(1)
    print("RESULTADO: la plataforma pasa todos los chequeos (suelo y cargas de sitio a confirmar).")


if __name__ == "__main__":
    main()
