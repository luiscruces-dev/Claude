"""
Simulador de secuencia de armado del domo geodesico 3V — Cucuchica.

Corre: `python3 dome_build_sequence.py`

Que hace: simula el armado del domo anillo por anillo, de la base hacia el
apice (metodo realista para construir en sitio sin grua: cada pieza nueva se
suelda apoyada en estructura ya fija, nunca al aire). En cada paso valida que
cada nodo nuevo quede geometricamente fijo en 3D: hacen falta al menos 3
barras no coplanares hacia estructura ya fija (con 2 barras el nodo queda
como una bisagra y gira alrededor de la linea entre sus 2 apoyos). Si no
llega a 3, lo marca como que necesita sujecion temporal (puntal, cuerda, un
ayudante) hasta que el paso siguiente lo triangule.

Alturas: se miden desde el nivel de los 10 nodos bajos (el piso), no desde
el centro de la esfera.

Por defecto arma el domo CON la puerta (dome_door.py): se omiten los 2 nodos
y 10 barras que ocupa el vano, y se agregan el marco y sus amarres. Con
`--sin-puerta` genera la secuencia del domo cerrado.

Escribe el checklist pieza por pieza en secuencia_de_armado.md, listo para
imprimir y usar en taller.
"""

import math
import sys
from collections import defaultdict
from dome_model import build_dome, v_sub, v_cross, v_norm, v_dot, v_normalize, v_scale

MIN_SUPPORTS_3D = 3

WARNINGS = []


def build_sequence(dome):
    boundary = set(dome.boundary_verts)
    placed = set(boundary)
    installed = set()
    steps = []

    # paso 0: anclaje de los 15 nodos de fundacion + barras del anillo base
    base_edges = [e for e in dome.edges if e[0] in boundary and e[1] in boundary]
    step0 = {"ring": 0, "kind": "fundacion", "new_hubs": sorted(boundary),
             "edges": [], "notes": "Los 15 nodos se fijan por topografia/anclaje, no por soldadura de barras."}
    for e in base_edges:
        step0["edges"].append(_edge_record(dome, e, rigid_support=None))
        installed.add(e)
    steps.append(step0)

    # anillos siguientes: por nivel de altura ascendente (excluyendo el borde)
    floor_h = min(dome.heights[b] for b in boundary)
    nodes = getattr(dome, "active", range(len(dome.verts)))
    heights_by_hub = {v: round(dome.heights[v] - floor_h, 4) for v in nodes if v not in boundary}
    levels = sorted(set(heights_by_hub.values()))

    adj = defaultdict(list)
    for e in dome.edges:
        adj[e[0]].append(e[1]); adj[e[1]].append(e[0])

    for ring_i, lv in enumerate(levels, start=1):
        new_hubs = sorted(v for v, h in heights_by_hub.items() if h == lv)

        # chequeo de rigidez 3D: cuantas barras de cada nodo nuevo llegan a nodos YA
        # fijos (antes de este paso) y si hay 3 de ellas no coplanares
        rigidity = {}
        for v in new_hubs:
            support_nbrs = [u for u in adj[v] if u in placed]
            rigidity[v] = support_nbrs
            if len(support_nbrs) == 0:
                WARNINGS.append(f"Nodo {v} (anillo {ring_i}) no tiene NINGUNA barra hacia estructura ya fija — error de secuencia.")
            elif not _fixed_in_3d(dome, v, support_nbrs):
                WARNINGS.append(f"Nodo {v} (anillo {ring_i}) solo tiene {len(support_nbrs)} barra(s) hacia estructura ya fija — "
                                f"queda como bisagra, necesita sujecion temporal.")

        placed_before = set(placed)
        placed |= set(new_hubs)

        # instalar toda arista que ahora tiene sus 2 extremos ya colocados y no se ha instalado
        ring_edges = []
        for e in dome.edges:
            if e in installed:
                continue
            if e[0] in placed and e[1] in placed:
                rigid = None
                if e[0] in new_hubs:
                    rigid = len(rigidity[e[0]])
                elif e[1] in new_hubs:
                    rigid = len(rigidity[e[1]])
                ring_edges.append(_edge_record(dome, e, rigid_support=rigid))
                installed.add(e)

        # al terminar el paso: que nodos nuevos ya quedaron fijos (iterando, porque un
        # nodo recien fijado puede fijar a su vecino del mismo anillo)
        fixed = set(placed_before)
        changed = True
        while changed:
            changed = False
            for v in new_hubs:
                if v not in fixed and _fixed_in_3d(dome, v, [u for u in adj[v] if u in fixed]):
                    fixed.add(v); changed = True
        steps.append({"ring": ring_i, "kind": "anillo", "new_hubs": new_hubs,
                      "edges": ring_edges, "height_m": lv,
                      "needs_bracing": [v for v, s in rigidity.items() if not _fixed_in_3d(dome, v, s)],
                      "unfixed_at_end": [v for v in new_hubs if v not in fixed]})

    missing = set(dome.edges) - installed
    return steps, missing


def _fixed_in_3d(dome, v, support_nbrs, min_det=1e-3):
    """Un nodo articulado queda fijo en 3D si al menos 3 de sus barras hacia
    estructura ya fija son no coplanares (determinante de sus direcciones != 0)."""
    if len(support_nbrs) < MIN_SUPPORTS_3D:
        return False
    dirs = [v_normalize(v_sub(dome.verts[u], dome.verts[v])) for u in support_nbrs]
    for i in range(len(dirs)):
        for j in range(i+1, len(dirs)):
            for k in range(j+1, len(dirs)):
                if abs(v_dot(dirs[i], v_cross(dirs[j], dirs[k]))) > min_det:
                    return True
    return False


def setting_out(dome):
    """Replanteo de los nodos de fundacion: azimut en planta (0° en el primer
    nodo alto H5, sentido antihorario visto desde arriba), radio desde el eje
    y coordenadas X/Y en metros, con origen en el centro del domo."""
    boundary = dome.boundary_verts
    axis = v_normalize(dome.verts[dome.apex_index_in_verts2])
    floor_h = min(dome.heights[b] for b in boundary)

    def planar(v):
        p = dome.verts[v]
        return v_sub(p, v_scale(axis, v_dot(p, axis)))

    first_high = min((b for b in boundary if dome.heights[b] - floor_h > 1e-6), key=lambda b: b)
    e1 = v_normalize(planar(first_high))
    e2 = v_cross(axis, e1)
    rows = []
    for b in boundary:
        q = planar(b)
        az = math.degrees(math.atan2(v_dot(q, e2), v_dot(q, e1))) % 360
        rows.append({"node": b, "az": az, "r": v_norm(q), "x": v_dot(q, e1), "y": v_dot(q, e2),
                     "dz": dome.heights[b] - floor_h})
    return sorted(rows, key=lambda r: r["az"])


def _edge_record(dome, e, rigid_support):
    return {"a": e[0], "b": e[1], "label": dome.edge_label[e],
            "length_cm": dome.edge_len[e]*100, "rigid_support": rigid_support}


PIECE_NAMES = {"P": "P · poste del marco", "D": "D · dintel del marco", "V": "V · viga del techo",
               "K1": "K1 · amarre bajo", "K2": "K2 · amarre alto"}


def hub_type_of(dome, v):
    side = getattr(dome, "side", {}).get(v)
    for t in dome.hub_types:
        if v in t["hub_ids"]:
            return t["name"] + (f"-{side}" if side else "")
    return "?"


def write_markdown(dome, steps, missing, path):
    lines = []
    door = getattr(dome, "door", None)
    lines.append("# Secuencia de armado paso a paso — domo 3V Cucuchica" + (" (con puerta)" if door else "") + "\n")
    lines.append("Generado por `dome_build_sequence.py` a partir de la geometria de "
                  "`dome_model.py`" + (" y `dome_door.py`" if door else "") + ". Orden: de la base hacia el apice, anillo por anillo, "
                  "para que cada pieza nueva siempre se apoye en estructura ya fija.\n")
    if door:
        lines.append(f"**Puerta** centrada a {door['azimuth_deg']:.1f}° (donde estaba el nodo #{door['hub']}). Postes sobre los "
                     f"anclajes #{door['a']} (izquierda, mirando la puerta desde afuera) y #{door['b']} (derecha). Los nodos "
                     f"#{door['removed_nodes'][0]} y #{door['removed_nodes'][1]} **no existen** en esta versión. Códigos de "
                     "pieza: A/B/C barras del domo · P poste del marco (50×50×2) · D dintel (50×50×2) · V viga del techo "
                     "del vestíbulo · K1 amarre bajo · K2 amarre alto (32×2). Tipos de nodo PA–PE: nodos especiales "
                     "alrededor de la puerta; la versión \"-der\" es la imagen espejo de la \"-izq\".\n")
    total_pieces = sum(len(s["edges"]) for s in steps)
    lines.append(f"**{len(steps)} anillos · {total_pieces} barras · {sum(len(s['new_hubs']) for s in steps)} nodos**\n")
    lines.append("Todas las alturas se miden **desde el piso** (nivel de los 10 nodos bajos H4), no desde "
                 "el centro de la esfera.\n")
    if WARNINGS:
        lines.append(f"\n> ⚠ {len(WARNINGS)} nodo(s) quedan como **bisagra** en el momento en que aparecen: tienen "
                      "menos de 3 barras no coplanares hacia estructura ya fija, así que pueden girar alrededor "
                      "de la línea entre sus apoyos. Necesitan sujeción temporal (puntal, cuerda, un ayudante) "
                      "hasta que quedan triangulados: cada paso indica si es en ese mismo paso o en el siguiente. "
                      "Es normal en un armado anillo por anillo, pero hay que preverlo en la logística del día de "
                      "armado.\n")
    lines.append("\n> ⚠ No caminar ni pararse sobre las barras: una persona de 100 kg a media barra lleva el "
                 "tubo de 32×2 mm al límite de fluencia. Armar y cubrir desde andamio o escalera.\n")

    for s in steps:
        if s["kind"] == "fundacion":
            lines.append(f"\n## Paso 0 — Fundación (15 nodos de anclaje)\n")
            lines.append(s["notes"] + "\n")
            lines.append("**Replanteo de los anclajes** (origen en el centro del domo; azimut 0° en el primer "
                         "nodo alto, creciendo en sentido antihorario visto desde arriba; X/Y en metros):\n")
            lines.append("| Nodo | Tipo | Azimut | Radio | X | Y | Altura sobre el piso |\n|---|---|---|---|---|---|---|")
            for r in setting_out(dome):
                v = r["node"]
                lines.append(f"| #{v} | {hub_type_of(dome,v)} | {r['az']:.3f}° | {r['r']:.4f} m | {r['x']:+.4f} | "
                             f"{r['y']:+.4f} | {r['dz']:+.4f} m |")
            lines.append("\n**Barras del anillo base a soldar en este paso:**\n")
            lines.append("| De | A | Tipo | Longitud |\n|---|---|---|---|")
            for e in s["edges"]:
                lines.append(f"| #{e['a']} | #{e['b']} | {e['label']} | {e['length_cm']:.2f} cm |")
        else:
            nn = len(s['new_hubs'])
            frame = door and set(s["new_hubs"]) == {door["Ta"], door["Tb"]}
            title = "Marco de la puerta" if frame else "Anillo"
            lines.append(f"\n## Paso {s['ring']} — {title} a {s['height_m']:.3f} m sobre el piso ({nn} nodo{'s' if nn != 1 else ''} nuevo{'s' if nn != 1 else ''})\n")
            if frame:
                lines.append("El marco (2 postes P + dintel D) se suelda **en taller** como una sola pieza, a escuadra y "
                             "con el vano libre medido. En obra se presenta sobre los anclajes "
                             f"#{door['a']} y #{door['b']}, se aploma y se amarra al domo con las barras K1 y K2 de este "
                             "paso. Las vigas V del techo del vestíbulo entran en el paso siguiente.\n")
            later = [v for v in s["needs_bracing"] if v in s["unfixed_at_end"]]
            within = [v for v in s["needs_bracing"] if v not in s["unfixed_at_end"]]
            if later:
                names = ", ".join(f"#{v} ({hub_type_of(dome,v)})" for v in later)
                lines.append(f"⚠ Sujetar temporalmente **hasta el paso siguiente** (quedan como bisagra): {names}\n")
            if within:
                names = ", ".join(f"#{v} ({hub_type_of(dome,v)})" for v in within)
                lines.append(f"⚠ Sujetar temporalmente **hasta soldar todas las barras de este paso** (aparecen como "
                             f"bisagra y las amarra un vecino del mismo anillo): {names}\n")
            lines.append("| Barra | De | A | Tipo | Longitud | Fijación |\n|---|---|---|---|---|---|")
            nth = defaultdict(int)
            for i, e in enumerate(s["edges"], start=1):
                a, b = e["a"], e["b"]
                a_new, b_new = a in s["new_hubs"], b in s["new_hubs"]
                if b_new and not a_new:
                    end1, end2 = a, b
                    nth[b] += 1
                    fix = f"{nth[b]}ª de {e['rigid_support']} barras que fijan #{b} (nuevo)"
                elif a_new and not b_new:
                    end1, end2 = b, a
                    nth[a] += 1
                    fix = f"{nth[a]}ª de {e['rigid_support']} barras que fijan #{a} (nuevo)"
                elif a_new and b_new:
                    end1, end2 = a, b
                    fix = "arriostre entre 2 nodos nuevos de este mismo anillo"
                else:
                    end1, end2 = a, b
                    fix = "arriostre (ambos extremos ya estaban fijos)"
                lab = PIECE_NAMES.get(e["label"], e["label"])
                lines.append(f"| {i} | #{end1} ({hub_type_of(dome,end1)}) | #{end2} ({hub_type_of(dome,end2)}) | {lab} | {e['length_cm']:.2f} cm | {fix} |")

    lines.append(f"\n\n## Verificación de cobertura\n")
    lines.append(f"- Barras totales en el modelo: {len(dome.edges)}\n"
                  f"- Barras instaladas en la secuencia: {sum(len(s['edges']) for s in steps)}\n"
                  f"- Barras sin asignar (deberían ser 0): {len(missing)}\n")
    if missing:
        lines.append(f"\n⚠ ERROR: quedaron {len(missing)} barras sin secuenciar: {sorted(missing)}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    if "--sin-puerta" in sys.argv:
        dome = build_dome()
    else:
        from dome_door import build_dome_with_door
        dome = build_dome_with_door()
    steps, missing = build_sequence(dome)

    total_edges_in_seq = sum(len(s["edges"]) for s in steps)
    print(f"Anillos: {len(steps)}")
    print(f"Barras secuenciadas: {total_edges_in_seq} / {len(dome.edges)}")
    print(f"Nodos que necesitan sujecion temporal (menos de 3 barras no coplanares al aparecer): "
          f"{sum(len(s.get('needs_bracing', [])) for s in steps)}")
    print(f"Barras sin asignar (debe ser 0): {len(missing)}")

    assert total_edges_in_seq == len(dome.edges), "no todas las barras quedaron en la secuencia"
    assert len(missing) == 0, f"barras huerfanas: {missing}"

    out_path = "secuencia_de_armado.md"
    write_markdown(dome, steps, missing, out_path)
    print(f"\nEscrito: {out_path}")

    if WARNINGS:
        print(f"\n{len(WARNINGS)} avisos de sujecion temporal (normal en armado anillo por anillo, ver el .md):")
        for w in WARNINGS[:8]:
            print(f"  - {w}")
        if len(WARNINGS) > 8:
            print(f"  ... y {len(WARNINGS)-8} mas (ver secuencia_de_armado.md)")
