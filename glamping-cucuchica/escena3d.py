"""
Datos de la escena 3D del domo con puerta y plataforma, compartidos por el
plano de taller (dome_viewer.py) y la maqueta (maqueta/maqueta.py).

Las coordenadas van como en el modelo (x, y, z con z hacia arriba, en metros);
cada pagina las pasa a su sistema de three.js. Asi las dos vistas 3D dibujan
exactamente la misma geometria.

Tambien numera las piezas en el orden de la secuencia de armado
(codigo paso.numero), para que el plano de taller y las etiquetas de la
maqueta usen los mismos codigos.
"""

import math

import dome_door as door
import dome_platform as plat


def _r(p, n=4):
    return [round(c, n) for c in p]


def sequence_pieces(D, steps):
    """Una entrada por pieza, en el orden de armado: id "paso.numero", paso,
    nodo de donde sale (ya colocado) y nodo al que llega (nuevo en ese paso)."""
    out = []
    for s in steps:
        new = set(s["new_hubs"]) if s["kind"] != "fundacion" else set()
        for i, e in enumerate(s["edges"], start=1):
            a, b = e["a"], e["b"]
            if a in new and b not in new:
                a, b = b, a
            out.append({"id": f"{s['ring']}.{i:02d}", "step": s["ring"], "from": a, "to": b})
    return out


def scene_data(D, PL):
    """Barras, nodos, paneles, puerta y plataforma listos para three.js."""
    P = D.verts
    struts = [{"a": _r(P[a]), "b": _r(P[b]), "code": D.edge_label[(a, b)],
               "sq": door.MEMBER_INFO[D.edge_label[(a, b)]][0] == "cuad50x2"} for a, b in D.edges]
    nodes = []
    for v in D.active:
        n = [P[v][k] - D.center[k] for k in range(3)]
        L = math.sqrt(sum(x*x for x in n))
        nodes.append({"id": v, "p": _r(P[v]), "n": [round(x/L, 4) for x in n], "t": D.type_of[v]})
    # discos de nodo: todos menos los topes del marco (PE), donde el dintel llega a tope
    hubs = [{"p": n["p"], "n": n["n"]} for n in nodes if n["t"] != "PE"]
    tris = [[_r(P[i]) for i in t] for t in D.triangles]
    dd = D.door
    quad = [_r(P[i]) for i in (dd["a"], dd["b"], dd["Tb"], dd["Ta"])]

    def xy(u, v): return _r(PL.to_xy(u, v))
    lv = PL.levels
    platd = {
        "outer": [xy(*q) for q in PL.outer], "inner": [xy(*q) for q in PL.inner],
        "piles": [{"x": round(p["x"], 4), "y": round(p["y"], 4), "kind": p["kind"], "id": p["id"],
                   "top": lv["ring_bottom"] if p["kind"] == "perimetral" else lv["beam_bottom"]} for p in PL.piles],
        "beams": [{"a": xy(b["u0"], b["v"]), "b": xy(b["u1"], b["v"])} for b in PL.beams] +
                 [{"a": xy(PL.landing["beam_u"], PL.landing["v0"]), "b": xy(PL.landing["beam_u"], PL.landing["v1"])}],
        "joists": [{"a": xy(j["u"], j["v0"]), "b": xy(j["u"], j["v1"])} for j in PL.joists] +
                  [{"a": xy(j["u0"], j["v"]), "b": xy(j["u1"], j["v"])} for j in PL.landing_joists],
        "landing": [xy(PL.landing["u0"], PL.landing["v0"]), xy(PL.landing["u1"], PL.landing["v0"]),
                    xy(PL.landing["u1"], PL.landing["v1"]), xy(PL.landing["u0"], PL.landing["v1"])],
        "steps": [{"c": [xy(s["u0"], s["v0"]), xy(s["u1"], s["v0"]), xy(s["u1"], s["v1"]), xy(s["u0"], s["v1"])],
                   "top": s["z"] + plat.STEP_RISE} for s in PL.steps],
        "levels": lv, "ped": plat.PED, "foot": plat.FOOT, "footT": plat.FOOT_T, "ringH": plat.RING_H,
        "beamH": plat.BEAM_H, "beamB": plat.BEAM_B, "joistB": plat.JOIST_B, "joistH": plat.JOIST_H, "deckT": plat.DECK_T,
    }
    return {"struts": struts, "hubs": hubs, "tris": tris, "door": quad, "center": _r(D.center), "nodes": nodes,
            "u": [round(dd["u"][0], 5), round(dd["u"][1], 5)], "v": [round(dd["v"][0], 5), round(dd["v"][1], 5)],
            "plat": platd}
