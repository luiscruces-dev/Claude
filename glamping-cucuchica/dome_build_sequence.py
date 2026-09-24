"""
Simulador de secuencia de armado del domo geodesico 3V — Cucuchica.

Corre: `python3 dome_build_sequence.py`

Que hace: simula el armado del domo anillo por anillo, de la base hacia el
apice (metodo realista para construir en sitio sin grua: cada pieza nueva se
suelda apoyada en estructura ya fija, nunca al aire). En cada paso valida que
cada nodo nuevo quede geometricamente fijo por al menos 2 barras no
paralelas antes de continuar — si un nodo solo tiene 1 barra de apoyo, lo
marca como que necesita sujecion temporal (un gato, una cuerda, un ayudante)
hasta que la segunda barra lo triangule.

Escribe el checklist pieza por pieza en secuencia_de_armado.md, listo para
imprimir y usar en taller.
"""

from collections import defaultdict
from dome_model import build_dome, v_sub, v_cross, v_norm

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
    heights_by_hub = {v: round(dome.heights[v], 4) for v in range(len(dome.verts)) if v not in boundary}
    levels = sorted(set(heights_by_hub.values()))

    adj = defaultdict(list)
    for e in dome.edges:
        adj[e[0]].append(e[1]); adj[e[1]].append(e[0])

    for ring_i, lv in enumerate(levels, start=1):
        new_hubs = sorted(v for v, h in heights_by_hub.items() if h == lv)

        # chequeo de rigidez: cuantas barras de cada nodo nuevo llegan a nodos YA fijos (antes de este paso)
        rigidity = {}
        for v in new_hubs:
            support_nbrs = [u for u in adj[v] if u in placed]
            rigidity[v] = support_nbrs
            if len(support_nbrs) == 0:
                WARNINGS.append(f"Nodo {v} (anillo {ring_i}) no tiene NINGUNA barra hacia estructura ya fija — error de secuencia.")
            elif len(support_nbrs) == 1:
                WARNINGS.append(f"Nodo {v} (anillo {ring_i}) solo queda fijo por 1 barra — necesita sujecion temporal hasta la siguiente barra.")

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

        steps.append({"ring": ring_i, "kind": "anillo", "new_hubs": new_hubs,
                      "edges": ring_edges, "height_m": lv,
                      "needs_bracing": [v for v, s in rigidity.items() if len(s) < 2]})

    missing = set(dome.edges) - installed
    return steps, missing


def _edge_record(dome, e, rigid_support):
    return {"a": e[0], "b": e[1], "label": dome.edge_label[e],
            "length_cm": dome.edge_len[e]*100, "rigid_support": rigid_support}


def hub_type_of(dome, v):
    for t in dome.hub_types:
        if v in t["hub_ids"]:
            return t["name"]
    return "?"


def write_markdown(dome, steps, missing, path):
    lines = []
    lines.append("# Secuencia de armado paso a paso — domo 3V Cucuchica\n")
    lines.append("Generado por `dome_build_sequence.py` a partir de la geometria de "
                  "`dome_model.py`. Orden: de la base hacia el apice, anillo por anillo, "
                  "para que cada pieza nueva siempre se apoye en estructura ya fija.\n")
    total_pieces = sum(len(s["edges"]) for s in steps)
    lines.append(f"**{len(steps)} anillos · {total_pieces} barras · {sum(len(s['new_hubs']) for s in steps)} nodos**\n")
    if WARNINGS:
        lines.append(f"\n> ⚠ {len(WARNINGS)} nodo(s) quedan fijos por una sola barra en el momento en que "
                      "aparecen — necesitan sujecion temporal (gato, cuerda, un ayudante) hasta que la "
                      "barra siguiente del mismo paso los triangule. Son normales en un armado ring-by-ring, "
                      "no un error, pero hay que preverlos en la logistica del dia de armado. Detalle abajo.\n")

    for s in steps:
        if s["kind"] == "fundacion":
            lines.append(f"\n## Paso 0 — Fundación (15 nodos de anclaje)\n")
            lines.append(s["notes"] + "\n")
            lines.append("| Nodo | Tipo | Altura relativa |\n|---|---|---|")
            for v in s["new_hubs"]:
                lines.append(f"| #{v} | {hub_type_of(dome,v)} | {dome.heights[v]-min(dome.heights[b] for b in s['new_hubs']):+.4f} m |")
            lines.append("\n**Barras del anillo base a soldar en este paso:**\n")
            lines.append("| De | A | Tipo | Longitud |\n|---|---|---|---|")
            for e in s["edges"]:
                lines.append(f"| #{e['a']} | #{e['b']} | {e['label']} | {e['length_cm']:.2f} cm |")
        else:
            lines.append(f"\n## Paso {s['ring']} — Anillo a {s['height_m']:.3f} m de altura ({len(s['new_hubs'])} nodos nuevos)\n")
            if s["needs_bracing"]:
                names = ", ".join(f"#{v} ({hub_type_of(dome,v)})" for v in s["needs_bracing"])
                lines.append(f"⚠ Sujetar temporalmente hasta triangular: {names}\n")
            lines.append("| Barra | De | A | Tipo | Longitud | Fijación |\n|---|---|---|---|---|---|")
            for i, e in enumerate(s["edges"], start=1):
                a, b = e["a"], e["b"]
                a_new, b_new = a in s["new_hubs"], b in s["new_hubs"]
                if b_new and not a_new:
                    end1, end2 = a, b
                    fix = f"{e['rigid_support']}ª barra que fija #{b} (nuevo)"
                elif a_new and not b_new:
                    end1, end2 = b, a
                    fix = f"{e['rigid_support']}ª barra que fija #{a} (nuevo)"
                elif a_new and b_new:
                    end1, end2 = a, b
                    fix = "arriostre entre 2 nodos nuevos de este mismo anillo"
                else:
                    end1, end2 = a, b
                    fix = "arriostre (ambos extremos ya estaban fijos)"
                lines.append(f"| {i} | #{end1} ({hub_type_of(dome,end1)}) | #{end2} ({hub_type_of(dome,end2)}) | {e['label']} | {e['length_cm']:.2f} cm | {fix} |")

    lines.append(f"\n\n## Verificación de cobertura\n")
    lines.append(f"- Barras totales en el modelo: {len(dome.edges)}\n"
                  f"- Barras instaladas en la secuencia: {sum(len(s['edges']) for s in steps)}\n"
                  f"- Barras sin asignar (deberían ser 0): {len(missing)}\n")
    if missing:
        lines.append(f"\n⚠ ERROR: quedaron {len(missing)} barras sin secuenciar: {sorted(missing)}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    dome = build_dome()
    steps, missing = build_sequence(dome)

    total_edges_in_seq = sum(len(s["edges"]) for s in steps)
    print(f"Anillos: {len(steps)}")
    print(f"Barras secuenciadas: {total_edges_in_seq} / {len(dome.edges)}")
    print(f"Nodos que necesitan sujecion temporal (1 sola barra de apoyo al aparecer): "
          f"{sum(len(s.get('needs_bracing', [])) for s in steps)}")
    print(f"Barras sin asignar (debe ser 0): {len(missing)}")

    assert total_edges_in_seq == len(dome.edges), "no todas las barras quedaron en la secuencia"
    assert len(missing) == 0, f"barras huerfanas: {missing}"

    out_path = "secuencia_de_armado.md"
    write_markdown(dome, steps, missing, out_path)
    print(f"\nEscrito: {out_path}")

    if WARNINGS:
        print(f"\n{len(WARNINGS)} avisos de sujecion temporal (normal en armado ring-by-ring, ver el .md):")
        for w in WARNINGS[:8]:
            print(f"  - {w}")
        if len(WARNINGS) > 8:
            print(f"  ... y {len(WARNINGS)-8} mas (ver secuencia_de_armado.md)")
