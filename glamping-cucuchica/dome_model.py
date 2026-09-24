"""
Motor geometrico del domo geodesico 3V — Cucuchica.

Pure Python (sin numpy/scipy) para que corra en cualquier maquina sin instalar
nada: `python3 dome_model.py`. Es la unica fuente de verdad de la geometria;
dome_verify.py y dome_build_sequence.py importan build_dome() de aqui en vez
de repetir numeros a mano, para que un cambio en el modelo se propague solo.

Metodo: icosaedro regular -> subdivision de frecuencia N (Clase I,
"alternate", proyeccion radial) -> corte por encima del ecuador -> escalado
al diametro de base deseado -> clasificacion de aristas (struts) y nodos
(hubs) por longitud/angulo real en 3D.
"""

import math
from collections import defaultdict, Counter

PHI = (1 + 5 ** 0.5) / 2


# ---------- vector helpers (tuplas de 3, sin numpy) ----------

def v_add(a, b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def v_sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def v_scale(a, s): return (a[0]*s, a[1]*s, a[2]*s)
def v_dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
def v_cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def v_norm(a): return math.sqrt(v_dot(a, a))
def v_normalize(a):
    n = v_norm(a)
    return (a[0]/n, a[1]/n, a[2]/n)
def v_angle_deg(a, b):
    c = v_dot(a, b) / (v_norm(a) * v_norm(b))
    c = max(-1.0, min(1.0, c))
    return math.degrees(math.acos(c))


# ---------- icosaedro base (mismas coordenadas/orden verificadas contra
# scipy.spatial.ConvexHull — ver seccion 7 del .md para el metodo) ----------

_ICOSA_RAW = [
    (0, 1, PHI), (PHI, 0, 1), (1, PHI, 0), (0, -1, PHI), (PHI, 0, -1),
    (-1, PHI, 0), (0, 1, -PHI), (-PHI, 0, 1), (1, -PHI, 0), (0, -1, -PHI),
    (-PHI, 0, -1), (-1, -PHI, 0),
]
_ICOSA_VERTS = [v_normalize(p) for p in _ICOSA_RAW]
_ICOSA_FACES = [
    (3, 8, 1), (5, 2, 6), (4, 2, 1), (4, 8, 1), (4, 2, 6), (4, 9, 6),
    (4, 9, 8), (11, 3, 7), (11, 9, 8), (11, 3, 8), (0, 2, 1), (0, 3, 7),
    (0, 3, 1), (0, 5, 2), (0, 5, 7), (10, 9, 6), (10, 5, 6), (10, 5, 7),
    (10, 11, 9), (10, 11, 7),
]


def subdivide_icosahedron(freq):
    """Subdivision Clase I ('alternate'): grilla baricentrica por cara,
    proyectada radialmente sobre la esfera unitaria. Devuelve (vertices,
    triangulos, apex_index)."""
    vert_map = {}
    verts = []

    def get_index(p):
        p = v_normalize(p)
        key = tuple(round(x, 9) for x in p)
        if key not in vert_map:
            vert_map[key] = len(verts)
            verts.append(p)
        return vert_map[key]

    triangles = []
    for f in _ICOSA_FACES:
        A, B, C = (_ICOSA_VERTS[i] for i in f)
        grid = {}
        for i in range(freq + 1):
            for j in range(freq + 1 - i):
                k = freq - i - j
                p = v_add(v_add(v_scale(A, k), v_scale(B, i)), v_scale(C, j))
                grid[(i, j)] = get_index(v_scale(p, 1.0/freq))
        for i in range(freq):
            for j in range(freq - i):
                k = freq - i - j
                v0, v1, v2 = grid[(i, j)], grid[(i+1, j)], grid[(i, j+1)]
                triangles.append((v0, v1, v2))
                if k > 1:
                    v3 = grid[(i+1, j+1)]
                    triangles.append((v1, v3, v2))

    apex_index = get_index(_ICOSA_VERTS[0])
    return verts, triangles, apex_index


# ---------- construccion del domo (corte + escala + clasificacion) ----------

class Dome:
    pass


def build_dome(freq=3, base_diameter_m=6.0, cut_row_index=7,
               strut_tol_m=0.003, angle_tol_deg=0.5):
    verts_unit, tris_full, apex_index = subdivide_icosahedron(freq)
    axis = v_normalize(verts_unit[apex_index])
    heights = [v_dot(v, axis) for v in verts_unit]

    rows = sorted(set(round(h, 6) for h in heights), reverse=True)
    if cut_row_index >= len(rows):
        raise ValueError(f"cut_row_index {cut_row_index} fuera de rango, solo hay {len(rows)} filas")
    target_h = rows[cut_row_index]

    rho_ring = math.sqrt(max(0.0, 1 - target_h**2))
    R = (base_diameter_m/2) / rho_ring

    verts = [v_scale(v, R) for v in verts_unit]
    heights_scaled = [h*R for h in heights]

    keep = [h >= target_h - 1e-6 for h in heights]
    cap_tris = [t for t in tris_full if all(keep[i] for i in t)]
    used = sorted({i for t in cap_tris for i in t})
    remap = {old: new for new, old in enumerate(used)}
    verts2 = [verts[i] for i in used]
    heights2 = [heights_scaled[i] for i in used]
    tris2 = [tuple(remap[i] for i in t) for t in cap_tris]

    edges = sorted({(min(a, b), max(a, b)) for t in tris2 for a, b in
                    [(t[0], t[1]), (t[1], t[2]), (t[2], t[0])]})
    edge_len = {e: v_norm(v_sub(verts2[e[0]], verts2[e[1]])) for e in edges}

    # clasificar longitudes de barra por cercania (tolerancia strut_tol_m)
    classes = []
    for e in sorted(edges, key=lambda e: -edge_len[e]):
        L = edge_len[e]
        placed = False
        for c in classes:
            if abs(c["len"] - L) < strut_tol_m:
                c["edges"].append(e); placed = True; break
        if not placed:
            classes.append({"len": L, "edges": [e]})
    labels = "ABCDEFG"
    edge_label = {}
    strut_summary = {}
    for i, c in enumerate(classes):
        lab = labels[i]
        mean_len = sum(edge_len[e] for e in c["edges"]) / len(c["edges"])
        for e in c["edges"]:
            edge_label[e] = lab
        strut_summary[lab] = {"length_m": mean_len, "count": len(c["edges"])}

    def label_of(i, j):
        return edge_label[(min(i, j), max(i, j))]

    # nodos (hubs): recorrer triangulos por vertice para ordenar el abanico
    vert_tris = defaultdict(list)
    for t in tris2:
        for v in t:
            vert_tris[v].append(t)

    hubs = {}
    for v in range(len(verts2)):
        tris_here = vert_tris[v]
        if not tris_here:
            continue
        pairs = [tuple(x for x in t if x != v) for t in tris_here]
        adj = defaultdict(list)
        for a, b in pairs:
            adj[a].append(b); adj[b].append(a)
        nbrs = {x for pair in pairs for x in pair}
        ends = [n for n in nbrs if len(adj[n]) == 1]
        start = ends[0] if ends else next(iter(nbrs))
        order = [start]
        prev, cur = None, start
        while True:
            nxts = [x for x in adj[cur] if x != prev]
            if not nxts or nxts[0] in order:
                break
            order.append(nxts[0]); prev, cur = cur, nxts[0]

        is_closed = any({order[-1], order[0]} <= set(x for x in t if x != v) for t in tris_here) and len(order) > 2
        m = len(order)
        angles = []
        pair_count = m if is_closed else m - 1
        for k in range(pair_count):
            a, b = order[k], order[(k+1) % m]
            angles.append(v_angle_deg(v_sub(verts2[a], verts2[v]), v_sub(verts2[b], verts2[v])))
        struts = [{"neighbor": n, "label": label_of(v, n), "length_m": edge_len[(min(v, n), max(v, n))]} for n in order]
        hubs[v] = {"degree": m, "closed": is_closed, "struts": struts,
                   "angles": angles, "height": heights2[v]}

    sig_groups = defaultdict(list)
    for v, h in hubs.items():
        sig = (h["degree"], h["closed"], tuple(sorted(s["label"] for s in h["struts"])),
               tuple(sorted(round(a, 1) for a in h["angles"])))
        sig_groups[sig].append(v)
    hub_types = []
    for sig, ids in sorted(sig_groups.items(), key=lambda kv: (-kv[0][0], kv[0][1])):
        example = hubs[ids[0]]
        hub_types.append({
            "degree": sig[0], "closed": sig[1], "strut_labels": sig[2],
            "angles": sig[3], "count": len(ids), "hub_ids": ids, "example": example,
        })
    for i, t in enumerate(hub_types):
        t["name"] = f"H{i+1}"

    tri_area_total = 0.0
    for t in tris2:
        a, b, c = (verts2[i] for i in t)
        area = 0.5 * v_norm(v_cross(v_sub(b, a), v_sub(c, a)))
        tri_area_total += area

    boundary_count = Counter()
    for e in edges:
        pass
    edge_tri_count = Counter()
    for t in tris2:
        for a, b in [(t[0], t[1]), (t[1], t[2]), (t[2], t[0])]:
            edge_tri_count[(min(a, b), max(a, b))] += 1
    boundary_edges = [e for e, c in edge_tri_count.items() if c == 1]
    boundary_verts = sorted({i for e in boundary_edges for i in e})

    apex_h = max(heights2)
    base_low_h = min(heights2[i] for i in boundary_verts)
    apex_height_above_base = apex_h - base_low_h

    floor_radius = base_diameter_m/2
    floor_area = math.pi * floor_radius**2

    d = Dome()
    d.freq = freq
    d.R = R
    d.base_diameter_m = base_diameter_m
    d.apex_index_in_verts2 = remap[apex_index] if apex_index in remap else None
    d.verts = verts2
    d.heights = heights2
    d.triangles = tris2
    d.edges = edges
    d.edge_len = edge_len
    d.edge_label = edge_label
    d.strut_summary = strut_summary
    d.hubs = hubs
    d.hub_types = hub_types
    d.membrane_area_m2 = tri_area_total
    d.boundary_edges = boundary_edges
    d.boundary_verts = boundary_verts
    d.apex_height_m = apex_height_above_base
    d.floor_area_m2 = floor_area
    d.total_strut_length_m = sum(v["length_m"]*v["count"] for v in strut_summary.values())
    return d


if __name__ == "__main__":
    dome = build_dome()
    print(f"3V, R={dome.R:.4f} m, base={dome.base_diameter_m} m")
    print(f"vertices={len(dome.verts)} triangulos={len(dome.triangles)} aristas={len(dome.edges)}")
    print(f"tipos de barra={len(dome.strut_summary)} tipos de nodo={len(dome.hub_types)}")
    print(f"longitud total de tubo={dome.total_strut_length_m:.2f} m")
    print(f"area de membrana={dome.membrane_area_m2:.2f} m2")
    print(f"altura del apice={dome.apex_height_m:.4f} m  area de piso={dome.floor_area_m2:.3f} m2")
