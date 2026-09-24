"""
Maqueta de la estructura del domo Cucuchica a escala: palos chinos y pega loca.

Para que sirve: comprobar con las manos que las medidas estan bien. Cada
palito se corta al largo que sale del modelo y lleva el mismo codigo de pieza
que la secuencia de armado real. Si todos cierran en su nodo sin forzar, los
largos estan bien; si ademas coinciden las mediciones de control (distancias
que no se usaron para cortar nada) y los discos de angulo, la geometria esta
comprobada.

Corre (desde glamping-cucuchica/maqueta):
    python3 maqueta.py            # genera maqueta.html y maqueta_plantillas.html
    node imprimir_pdf.js          # opcional: maqueta_plantillas.pdf (usa Chromium de Playwright)

Todo sale del mismo modelo verificado (dome_model.py, dome_door.py,
dome_platform.py), asi que la maqueta queda a escala exacta del diseno real.

Regla de corte de los palitos: el largo de centro de nodo a centro de nodo
a escala, menos un retiro en cada extremo para que los palitos no choquen en
el nodo. El retiro depende del grosor del palito y del angulo mas cerrado con
las otras barras de ese nodo: retiro = (d/2) / tan(angulo/2). Asi los ejes de
todos los palitos siguen apuntando al centro exacto del nodo, y la pega loca
(con bicarbonato) rellena el hueco. El marco de la puerta es la excepcion:
postes y dintel forman una esquina continua y son las otras barras las que se
recortan contra el.
"""

import html
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import dome_door as door            # noqa: E402
import dome_platform as plat        # noqa: E402
import escena3d                     # noqa: E402
from dome_model import v_sub, v_norm, v_dot  # noqa: E402

SCALE = 10              # escala recomendada 1:10 (plantillas impresas)
STICK_D = 5.0           # mm, palo chino tipico en la parte recta
STICK_LEN = 300.0       # mm, palo chino de 30 cm
STICK_USABLE = 240.0    # mm, parte pareja aprovechable: se descartan ~3 cm de cada punta
KERF = 1.0              # mm que se pierden por corte


def esc(s):
    return html.escape(str(s), quote=True)


def f(x, n=1):
    return f"{x:.{n}f}"


# ---------------------------------------------------------------- datos

def angle_at(P, v, a, b):
    x = v_sub(P[a], P[v]); y = v_sub(P[b], P[v])
    c = v_dot(x, y)/(v_norm(x)*v_norm(y))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def build_members(D):
    """Una entrada por barra con lo necesario para calcular su corte en la maqueta."""
    P = D.verts
    adj = defaultdict(list)
    for a, b in D.edges:
        adj[a].append(b); adj[b].append(a)

    def amin(v, other):
        return min(angle_at(P, v, other, o) for o in adj[v] if o != other)
    out = []
    for e in D.edges:
        a, b = e
        lab = D.edge_label[e]
        if lab == "P":
            base, top = (a, b) if P[a][2] < P[b][2] else (b, a)
            out.append({"code": "P", "L": D.door["head_z"], "ta": amin(base, top), "tb": None, "e": [base, top]})
        elif lab == "D":
            out.append({"code": "D", "L": D.edge_len[e], "ta": None, "tb": None, "e": [a, b]})
        else:
            out.append({"code": lab, "L": D.edge_len[e], "ta": amin(a, b), "tb": amin(b, a), "e": [a, b]})
    return out


def cut_mm(m, N, d):
    r = d/2
    def s(th): return 0.0 if th is None else r/math.tan(math.radians(th/2))
    if m["code"] == "P":            # poste: entero, de la placa al tope del marco (dintel entre postes);
        return m["L"]*1000/N + d    # las barras que llegan a su pie se recortan contra el
    if m["code"] == "D":            # dintel: entre caras interiores de los postes
        return m["L"]*1000/N - d
    return m["L"]*1000/N - s(m["ta"]) - s(m["tb"])


def cut_groups(members, N, d):
    g = Counter()
    for m in members:
        g[(m["code"], round(cut_mm(m, N, d)*2)/2)] += 1
    order = "ABCPDVK"
    return sorted(g.items(), key=lambda kv: (order.find(kv[0][0][0]), kv[0][0], -kv[1]))


def build_pieces(D, members):
    """Las piezas en el orden de la secuencia de armado, con su codigo paso.numero."""
    import dome_build_sequence as seq
    seq.WARNINGS.clear()
    steps, missing = seq.build_sequence(D)
    assert not missing
    mem_by_edge = {tuple(sorted(m["e"])): m for m in members}
    pieces, notes = [], []
    for s in steps:
        frame = bool(D.door) and set(s["new_hubs"]) == {D.door["Ta"], D.door["Tb"]}
        later = [v for v in s.get("needs_bracing", []) if v in s.get("unfixed_at_end", [])]
        within = [v for v in s.get("needs_bracing", []) if v not in s.get("unfixed_at_end", [])]
        notes.append({"step": s["ring"], "kind": s["kind"], "height": s.get("height_m", 0.0), "nodes": list(s["new_hubs"]),
                      "frame": frame, "later": later, "within": within, "n": len(s["edges"])})
    for sp in escena3d.sequence_pieces(D, steps):
        m = mem_by_edge[tuple(sorted((sp["from"], sp["to"])))]
        pieces.append(dict(sp, code=m["code"], L=round(m["L"], 5),
                           ta=None if m["ta"] is None else round(m["ta"], 3),
                           tb=None if m["tb"] is None else round(m["tb"], 3)))
    return pieces, notes


def control_checks(D):
    """Medidas que se pueden comprobar sobre la maqueta armada y que NO se usaron
    para cortar ningun palito. kind: dist (entre centros de nodo), height (desde el
    tablero), doorw / doorh (vano de la puerta)."""
    import itertools
    P = D.verts
    def dist(a, b): return v_norm(v_sub(P[a], P[b]))
    edges = {(min(e), max(e)) for e in D.edges}
    apex = max(D.active, key=lambda v: P[v][2])
    low = sorted(v for v in D.boundary_verts if P[v][2] < 1e-6)
    high = sorted(v for v in D.boundary_verts if P[v][2] > 1e-6)
    out = [{"what": "Del ápice a cada nodo bajo: los 10 tienen que dar igual", "where": f"#{apex} a " + ", ".join(f"#{v}" for v in low),
            "m": dist(apex, low[0]), "kind": "dist", "tol": 3},
           {"what": "Del ápice a cada nodo alto: los 5 iguales", "where": f"#{apex} a " + ", ".join(f"#{v}" for v in high),
            "m": dist(apex, high[0]), "kind": "dist", "tol": 3}]
    by_h = defaultdict(list)
    for v in D.active:
        if v not in D.boundary_verts:
            by_h[round(P[v][2], 4)].append(v)
    names = {}
    for k, h in enumerate(sorted(by_h), start=1):
        names[h] = k
    for h in sorted(by_h):
        nodes = sorted(by_h[h])
        if h == round(max(P[v][2] for v in D.active), 4):
            what = "Altura del ápice"
        elif D.door and set(nodes) == {D.door["Ta"], D.door["Tb"]}:
            continue
        else:
            what = f"Altura de los {len(nodes)} nodos a {h:.3f} m: todos iguales"
        out.append({"what": what, "where": ", ".join(f"#{v}" for v in nodes), "m": h, "kind": "height", "tol": 3})
    # entre nodos del mismo nivel que no estan unidos por un palito
    for h in sorted(by_h):
        nodes = sorted(by_h[h])
        pairs = [(dist(a, b), a, b) for a, b in itertools.combinations(nodes, 2) if (min(a, b), max(a, b)) not in edges]
        if not pairs:
            continue
        dmin = min(p[0] for p in pairs)
        near = [p for p in pairs if abs(p[0] - dmin) < 1e-3]
        far = max(pairs)
        if len(nodes) >= 4:
            out.append({"what": f"Entre nodos vecinos a {h:.3f} m que no llevan palito", "where": ", ".join(f"#{a}–#{b}" for _, a, b in near[:4]),
                        "m": dmin, "kind": "dist", "tol": 3})
            if abs(far[0] - dmin) > 0.05:
                out.append({"what": f"De lado a lado a {h:.3f} m", "where": f"#{far[1]}–#{far[2]}", "m": far[0], "kind": "dist", "tol": 3})
    if D.door:
        chord = D.edge_len[(min(D.door["a"], D.door["b"]), max(D.door["a"], D.door["b"]))]
        out.append({"what": "Vano de la puerta: ancho entre caras de los postes", "where": f"postes sobre #{D.door['a']} y #{D.door['b']}",
                    "m": chord, "kind": "doorw", "tol": 2})
        out.append({"what": "Vano de la puerta: del tablero a la cara de abajo del dintel", "where": "centro del vano",
                    "m": D.door["head_z"], "kind": "doorh", "tol": 2})
    out.append({"what": "Plomada: un hilo con peso desde cada nodo cae en su cruz", "where": "cruces finas de la planta",
                "m": 0.0, "kind": "plumb", "tol": 3})
    return out


def collect():
    D = door.build_dome_with_door()
    PL, PR, PQ, _ = plat.evaluate(verbose=False)
    P = D.verts
    members = build_members(D)
    scene = escena3d.scene_data(D, PL)
    dd = D.door
    pieces, notes = build_pieces(D, members)
    data = dict(scene, pieces=pieces, notes=notes, checks=control_checks(D))
    data.update({
        "members": [{"code": m["code"], "L": round(m["L"], 5), "ta": None if m["ta"] is None else round(m["ta"], 3),
                     "tb": None if m["tb"] is None else round(m["tb"], 3)} for m in members],
        "real": {"diam": 6.0, "apex": round(max(p[2] for p in P), 4), "clear_w": round(door.bending_door_frame(D, 1)["clear_w"], 4),
                 "clear_h": round(door.bending_door_frame(D, 1)["clear_h"], 4), "freeboard": plat.FREEBOARD,
                 "extent_u": round(PL.steps[-1]["u1"], 3), "ring_len": round(PQ["ring_len"], 3),
                 "head_z": dd["head_z"], "zig": 0.0486}})
    return D, PL, members, data


# ---------------------------------------------------------------- pagina

def build_page(D, PL, members, data):
    js = JS.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    # checklist pieza por pieza, agrupado por paso (los largos los llena el JS segun escala y grosor)
    blocks = []
    k = 0
    for nt in data["notes"]:
        rows = []
        while k < len(data["pieces"]) and data["pieces"][k]["step"] == nt["step"]:
            pc = data["pieces"][k]
            rows.append(f'<tr><td><input type="checkbox" class="pk" data-k="p{esc(pc["id"])}" aria-label="Pieza {esc(pc["id"])} lista"></td>'
                        f'<td class="mono strongc">{esc(pc["id"])}</td><td class="mono">#{pc["from"]} → #{pc["to"]}</td>'
                        f'<td><span class="code" data-code="{esc(pc["code"])}">{esc(pc["code"])}</span></td>'
                        f'<td class="num strongc" data-pc="{k}"></td></tr>')
            k += 1
        if nt["kind"] == "fundacion":
            title = "Paso 0 · anillo de base sobre la planta"
            hi = [v for v in D.boundary_verts if D.verts[v][2] > 1e-6]
            note = (f"Los {len(D.boundary_verts)} palitos del borde van sobre la planta impresa, de marca a marca. "
                    f"Bajo los {len(hi)} nodos altos ({', '.join('#' + str(v) for v in sorted(hi))}) va un taco de "
                    f"{max(D.verts[v][2] for v in hi)*1000/SCALE:.1f} mm (es el taco de {max(D.verts[v][2] for v in hi)*100:.2f} cm del domo real).")
        elif nt["frame"]:
            title = f"Paso {nt['step']} · marco de la puerta (dintel a {nt['height']:.2f} m reales)"
            note = "Pegue antes el marco (2 postes y el dintel) a escuadra sobre la mesa. Preséntelo sobre #%d y #%d y amárrelo con K1 y K2." % (D.door["a"], D.door["b"])
        else:
            title = (f"Paso {nt['step']} · cúspide (#{nt['nodes'][0]})" if len(nt['nodes']) == 1 else
                     f"Paso {nt['step']} · anillo de {len(nt['nodes'])} nodos a {nt['height']:.3f} m reales")
            note = ""
        if nt["later"]:
            note += (" " if note else "") + "▲ Sostenga con plastilina o cinta hasta el paso siguiente: " + ", ".join(f"#{v}" for v in nt["later"]) + " (quedan como bisagra)."
        if nt["within"]:
            note += (" " if note else "") + "◆ Sostenga hasta pegar todas las piezas de este paso: " + ", ".join(f"#{v}" for v in nt["within"]) + "."
        blocks.append(f'<details class="stepblk"{" open" if nt["step"] in (0, 1) else ""}><summary><b>{esc(title)}</b>'
                      f'<span class="muted"> · {nt["n"]} piezas</span><span class="prog" data-step="{nt["step"]}"></span></summary>'
                      f'{"<p class=note2>" + esc(note) + "</p>" if note else ""}'
                      f'<div class="tbl"><table><thead><tr><th></th><th>Código</th><th>De → a</th><th>Tipo</th><th class="num">Cortar a</th></tr></thead>'
                      f'<tbody>{"".join(rows)}</tbody></table></div></details>')

    check_rows = "".join(
        f'<tr><td><input type="checkbox" class="pk" data-k="c{i}" aria-label="Medición {i+1} comprobada"></td><td>{esc(c["what"])}</td>'
        f'<td class="mono small">{esc(c["where"])}</td><td class="num strongc" data-ck="{i}"></td><td class="num">±{c["tol"]} mm</td></tr>'
        for i, c in enumerate(data["checks"]))

    return f"""<title>Maqueta de la estructura</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="hero">
  <div class="eyebrow">Glamping Cucuchica · prueba a escala de la estructura · palos chinos y pega loca</div>
  <h1>Maqueta de la estructura 1:{SCALE} con palos chinos</h1>
  <p class="lede">Cada palito se corta al largo que sale de los cálculos y lleva el mismo código que la pieza real en la secuencia de armado. Si los 119 palitos cierran en su nodo sin forzar, y las mediciones de control coinciden, las medidas quedan comprobadas con las manos, no por confianza.</p>
  <div class="statgrid" id="sizes"></div>
</header>

<section id="idea">
  <h2>Cómo prueba las medidas</h2>
  <div class="cards">
    <div class="card"><h3>Los largos cierran</h3><p>Cada triángulo tiene 3 palitos cortados por separado. Si un solo largo estuviera mal, al llegar al nodo el palito sobraría o faltaría. Que los 119 cierren sin forzar confirma los largos.</p></div>
    <div class="card"><h3>Medidas que no se usaron para cortar</h3><p>La distancia del ápice a los 10 nodos bajos, la altura de cada anillo y la distancia entre nodos que no llevan palito salen solas de la geometría. Si dan lo que dice la tabla, la forma completa está bien.</p></div>
    <div class="card"><h3>Los ángulos del nodo</h3><p>Los discos impresos se apoyan sobre un nodo terminado, mirando desde afuera: los palitos tienen que caer sobre las líneas. Es la prueba de los ángulos que se marcan en los discos de acero.</p></div>
  </div>
</section>

<section id="vista">
  <h2>La estructura que va a armar</h2>
  <p class="sub">Así queda con palitos a escala, con cada nodo numerado igual que en el checklist. Gire con el dedo o el mouse. Apague "palitos" para verla con los tubos reales.</p>
  <div class="scene-wrap">
    <div id="scene" role="img" aria-label="Vista 3D de la estructura con los nodos numerados"><div id="labels" aria-hidden="true"></div><div id="nogl" hidden>Este navegador no pudo abrir la vista 3D (WebGL). El resto de la página funciona igual.</div></div>
    <div class="scene-bar">
      <div class="views" role="group" aria-label="Vistas">
        <button type="button" class="vbtn" data-view="tres">3/4</button><button type="button" class="vbtn" data-view="frente">Frente</button><button type="button" class="vbtn" data-view="planta">Planta</button><button type="button" class="vbtn" data-view="adentro">Adentro</button>
      </div>
      <div class="toggles">
        <label class="strong"><input type="checkbox" id="t-num" checked> números</label>
        <label class="strong"><input type="checkbox" id="t-model" checked> palitos</label>
        <label><input type="checkbox" id="t-mem"> membrana</label>
        <label><input type="checkbox" id="t-door"> puerta</label>
        <label><input type="checkbox" id="t-plat"> plataforma</label>
        <label><input type="checkbox" id="t-people"> persona y cama</label>
      </div>
    </div>
  </div>
</section>

<section id="materiales">
  <h2>Qué necesita</h2>
  <div class="cards">
    <div class="card"><h3>Material</h3><ul class="plain">
      <li><b id="m-sticks">—</b> palos chinos de {STICK_LEN/10:.0f} cm, derechos y del mismo grosor (compre <b id="m-buy">—</b>, con repuesto para repetir cortes)</li>
      <li>Pega loca (cianoacrilato) y bicarbonato de sodio</li>
      <li>Tablero plano de 70 × 70 cm (cartón piedra, MDF o anime)</li>
      <li>Plastilina y cinta de papel para sostener</li>
      <li>Marcadores de 3 colores: azul (A), naranja (B), verde (C)</li>
      <li>Hilo y un peso pequeño (plomada)</li></ul></div>
    <div class="card"><h3>Herramienta</h3><ul class="plain">
      <li>Segueta fina o cortador de modelismo</li>
      <li>Lija fina sobre un taco, para dejar las puntas planas</li>
      <li>Regla metálica en milímetros y escuadra</li>
      <li>Pinzas, guantes y lugar ventilado</li>
      <li>Impresora para las plantillas (al 100%)</li></ul></div>
  </div>
</section>

<section id="corte">
  <h2>Largo de cada palito</h2>
  <p class="sub">Mida el grosor de sus palitos en la parte del medio, que es de donde se corta, y póngalo aquí; todo se recalcula, incluido el checklist. "Largo aprovechable" es la parte pareja del palito: en uno de {STICK_LEN/10:.0f} cm, descarte unos 3 cm de cada punta. "Retiro" es lo que se descuenta en cada punta para que los palitos no choquen en el nodo; así el eje de cada palito sigue apuntando al centro exacto del nodo.</p>
  <div class="calc">
    <label>Escala 1:<select id="c-n"><option value="10" selected>10</option><option value="15">15</option><option value="20">20</option></select></label>
    <label>Grosor del palito <input id="c-d" type="number" min="2" max="8" step="0.5" value="{STICK_D}"> mm</label>
    <label>Largo aprovechable <input id="c-l" type="number" min="100" max="300" step="5" value="{STICK_USABLE:.0f}"> mm</label>
  </div>
  <div class="tbl"><table><thead><tr><th>Pieza</th><th>Qué es</th><th class="num">Cantidad</th><th class="num">Centro a centro</th><th class="num">Retiros</th><th class="num">Cortar a</th></tr></thead><tbody id="cuttab"></tbody></table></div>
  <p class="sum" id="cutsum"></p>
</section>

<section id="piezas">
  <h2>Pieza por pieza</h2>
  <p class="sub">El mismo orden y los mismos códigos que <span class="mono">secuencia_de_armado.md</span>: armar la maqueta es ensayar el armado real. Marque cada pieza al pegarla; las marcas se guardan en este navegador. Las etiquetas impresas llevan el código de cada palito.</p>
  <div class="progress"><span id="prog-all"></span><button type="button" class="ghost" id="reset-checks">Borrar marcas</button></div>
  {"".join(blocks)}
</section>

<section id="control">
  <h2>Mediciones de control</h2>
  <p class="sub">Con la estructura terminada. Las distancias son entre centros de nodo, es decir, entre los centros de los puntos de pega. Las alturas se miden desde el tablero. Ninguna de estas medidas se usó para cortar: si coinciden, la geometría está bien. La hoja de control del PDF tiene una columna para anotar lo medido.</p>
  <div class="tbl"><table><thead><tr><th></th><th>Qué medir</th><th>Entre</th><th class="num">Tiene que dar</th><th class="num">Tolerancia</th></tr></thead><tbody>{check_rows}</tbody></table></div>
</section>

<section id="plantillas">
  <h2>Plantillas para imprimir</h2>
  <p>El archivo <span class="mono">maqueta_plantillas.pdf</span> está a escala 1:{SCALE} para palitos de {STICK_D:.0f} mm. Imprímalo <b>al 100% (tamaño real)</b> y mida la barra de 10 cm de la portada antes de seguir. Trae:</p>
  <ul class="plain">
    <li><b>Planta base en 12 hojas</b>, que se unen con cinta haciendo coincidir las cruces. Trae las 15 marcas de anclaje, los palitos del anillo de base con su código, los postes de la puerta y una marca con el número de cada nodo de arriba, para la prueba de la plomada.</li>
    <li><b>Etiquetas</b>: una banderita por palito con su código, sus nodos y su largo.</li>
    <li><b>Reglas de corte</b>: una barra impresa del largo exacto de cada tipo de palito.</li>
    <li><b>Discos de ángulo</b> de cada tipo de nodo, para la prueba de los ángulos.</li>
    <li><b>Hoja de control</b> para anotar las mediciones.</li>
  </ul>
</section>

<section id="armado">
  <h2>Paso a paso</h2>
  <ol class="steps">
    <li><b>Prepare la base.</b> Una las 12 hojas de la planta y péguelas sobre el tablero.</li>
    <li><b>Corte y etiquete.</b> Corte cada palito con la regla impresa o con la tabla, lije las puntas planas y péguele su banderita. Marque las puntas con su color: A azul, B naranja, C verde.</li>
    <li><b>Arme en el orden del checklist.</b> Paso 0 sobre la planta; después anillo por anillo. Cada palito va del nodo "De" al nodo "a". Si un palito no llega o sobra más de 1 mm, no lo fuerce: revise el nodo anterior antes de seguir.</li>
    <li><b>Sostenga los nodos bisagra</b> (▲ y ◆ en el checklist) con plastilina o cinta. Es exactamente lo que va a pasar en la obra real con los puntales.</li>
    <li><b>Marco de la puerta.</b> Péguelo aparte a escuadra: 2 postes enteros y el dintel entre ellos. Colóquelo en su paso sobre #{D.door['a']} y #{D.door['b']}.</li>
    <li><b>Compruebe.</b> Haga las mediciones de control y la prueba de la plomada, y apoye los discos de ángulo sobre varios nodos. Anote todo en la hoja de control.</li>
  </ol>
  <div class="note"><h3>Con pega loca</h3><p>Una gota en el nodo y una pizca de bicarbonato encima: endurece al instante y rellena el hueco entre las puntas. Use pinzas, trabaje ventilado y proteja la mesa. Pegue primero con poca pega; cuando el anillo completo cierre, refuerce todos sus nodos.</p></div>
</section>

<footer>Plano de taller del domo real (cortes, nodos, puerta, plataforma, armado): <a href="https://claude.ai/artifact/79tfRK3Jq2uPU6B5nhH5p8">plano de taller</a> (en el repositorio: <span class="mono">domo-3v-cucuchica.html</span>).<br>Generado por <span class="mono">maqueta/maqueta.py</span> desde <span class="mono">dome_model.py</span>, <span class="mono">dome_door.py</span> y <span class="mono">dome_build_sequence.py</span>. Vista 3D con three.js r128.</footer>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>{js}</script>
"""


CSS = """
:root{
  --page:#f4f3ef; --surface:#fcfbf8; --surface-2:#ecebe6; --ink:#15171a; --ink-2:#4b5055; --muted:#7d8287;
  --grid:#dfded8; --line:#c4c3bb; --accent:#2b5a78; --sA:#2a78d6; --sB:#eb6834; --sC:#1baf7a; --door:#3b3f44;
  --scene:#dfe6ea; --warn:#b3302f;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --sA:#3987e5; --sB:#d95926; --sC:#199e70; --door:#d6d9d6; --scene:#1d2328; --warn:#ec7070;
}}
:root[data-theme="dark"]{
  color-scheme:dark; --page:#0f1112; --surface:#1b1d1f; --surface-2:#25282a; --ink:#f1f2f0; --ink-2:#c1c6c3; --muted:#8b9296;
  --grid:#2b2f31; --line:#3b4043; --accent:#86b5d6; --sA:#3987e5; --sB:#d95926; --sC:#199e70; --door:#d6d9d6; --scene:#1d2328; --warn:#ec7070;
}
*{box-sizing:border-box}
body{background:var(--page); color:var(--ink); font:15px/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; padding-inline:16px; padding-block:0 40px}
.wrap{max-width:1040px; margin:0 auto}
h1,h2,h3{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif; text-wrap:balance}
h1{font-size:clamp(28px,4.4vw,40px); line-height:1.08; margin:0 0 10px}
h2{font-size:23px; margin:0 0 6px} h3{font-size:16px; margin:0 0 6px}
p{max-width:72ch; margin:0 0 10px}
.mono,.num{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace; font-variant-numeric:tabular-nums}
.hero{padding-block:30px 10px}
.eyebrow{font:600 11.5px "IBM Plex Mono",monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin-bottom:10px}
.lede{color:var(--ink-2); font-size:16px}
.statgrid{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1px; background:var(--grid); border:1px solid var(--grid); border-radius:8px; overflow:hidden; margin-top:16px}
@media (max-width:640px){.statgrid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat{background:var(--surface); padding:12px 14px} .stat .v{font:600 21px "IBM Plex Mono",monospace} .stat .u{font-size:11px; color:var(--muted); margin-left:2px} .stat .l{font-size:12px; color:var(--ink-2)}
section{padding-block:32px; border-top:1px solid var(--grid)}
.sub{color:var(--ink-2); font-size:14px}
.scene-wrap{border:1px solid var(--grid); border-radius:10px; overflow:hidden; background:var(--surface)}
#scene{position:relative; width:100%; height:min(72vh,560px); background:var(--scene); touch-action:none}
#scene canvas{display:block; width:100%; height:100%}
#nogl{position:absolute; inset:0; display:grid; place-items:center; padding:20px; color:var(--ink-2); text-align:center}
#nogl[hidden]{display:none}
#scene canvas{position:relative; z-index:1}
#labels{position:absolute; inset:0; pointer-events:none; overflow:hidden; z-index:2}
#labels[hidden]{display:none}
.nlab{position:absolute; left:0; top:0; font:600 10.5px "IBM Plex Mono",monospace; color:#fff; background:rgba(21,23,26,.78); padding:1px 4px; border-radius:3px; white-space:nowrap}
.nlab-d{background:rgba(179,48,47,.88)}
.cards{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); gap:12px; margin-top:12px}
.card{background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:12px 16px} .card p{margin:0; font-size:14px; color:var(--ink-2)}
ul.plain{margin:0; padding-left:18px; display:grid; gap:5px; font-size:14px; max-width:78ch}
details.stepblk{border:1px solid var(--grid); border-radius:8px; background:var(--surface); margin-top:10px}
details.stepblk summary{cursor:pointer; padding:10px 14px; list-style:none}
details.stepblk summary::-webkit-details-marker{display:none}
details.stepblk summary::before{content:"▸ "; color:var(--muted)} details.stepblk[open] summary::before{content:"▾ "}
details.stepblk .tbl{margin:0 12px 12px}
.note2{margin:0 14px 8px; font-size:13.5px; color:var(--ink-2)}
.code[data-code="A"]{background:var(--sA)} .code[data-code="B"]{background:var(--sB)} .code[data-code="C"]{background:var(--sC)}
.code[data-code="P"],.code[data-code="D"],.code[data-code="V"],.code[data-code="K1"],.code[data-code="K2"]{background:var(--door); color:var(--page)}
.progress{display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-top:8px; font:600 13px "IBM Plex Mono",monospace}
button.ghost{font:inherit; font-size:12.5px; color:var(--ink-2); background:transparent; border:1px solid var(--line); border-radius:6px; padding:5px 10px; cursor:pointer}
.small{font-size:12.5px} .muted{color:var(--muted)}
input.pk{width:18px; height:18px; accent-color:var(--sC)}
.scene-bar{display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; padding:10px 12px; border-top:1px solid var(--grid)}
.views{display:flex; gap:6px; flex-wrap:wrap}
.vbtn{font:600 12.5px "IBM Plex Mono",monospace; color:var(--ink-2); background:var(--surface); border:1px solid var(--line); border-radius:6px; padding:6px 10px; cursor:pointer}
.vbtn:hover{color:var(--ink)}
.toggles{display:flex; gap:12px; flex-wrap:wrap; font-size:13px; color:var(--ink-2); align-items:center}
.toggles label{display:flex; gap:5px; align-items:center} .toggles .strong{color:var(--ink); font-weight:600}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.twocol{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.1fr); gap:20px; align-items:start}
@media (max-width:820px){.twocol{grid-template-columns:minmax(0,1fr)}}
.tbl{overflow-x:auto; border:1px solid var(--grid); border-radius:8px; background:var(--surface); margin-top:10px}
table{border-collapse:collapse; width:100%; font-size:13.5px}
th,td{text-align:left; padding:7px 10px; border-bottom:1px solid var(--grid); vertical-align:top}
th{font:600 10.5px "IBM Plex Mono",monospace; letter-spacing:.05em; text-transform:uppercase; color:var(--muted)}
th.num,td.num{text-align:right; white-space:nowrap} tr:last-child td{border-bottom:none}
td.strongc{font-weight:700}
.code{display:inline-block; min-width:26px; text-align:center; font:700 12px "IBM Plex Mono",monospace; border-radius:4px; padding:2px 5px; color:#fff}
.calc{display:flex; gap:16px; flex-wrap:wrap; font-size:14px; margin-top:8px}
.calc label{display:flex; gap:6px; align-items:center}
.calc input,.calc select{font:600 14px "IBM Plex Mono",monospace; width:78px; padding:5px 6px; border:1px solid var(--line); border-radius:6px; background:var(--surface); color:var(--ink)}
.calc select{width:auto}
.sum{margin-top:12px}
ol.steps{padding-left:22px; display:grid; gap:8px; max-width:78ch}
.note{background:var(--surface); border:1px solid var(--grid); border-radius:8px; padding:12px 16px; margin-top:14px} .note p{margin:0; color:var(--ink-2); font-size:14px}
footer a{color:var(--accent)}
footer{padding-block:24px; color:var(--muted); font-size:12.5px; border-top:1px solid var(--grid)}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
"use strict";
var MQ=__DATA__;
function $(id){return document.getElementById(id);}
function cssv(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim();}
var NAMES={A:'barra A del domo',B:'barra B del domo',C:'barra C del domo',P:'poste del marco',D:'dintel del marco',V:'viga del techo del vestíbulo',K1:'amarre bajo',K2:'amarre alto'};
function codeColor(c){return {A:'var(--sA)',B:'var(--sB)',C:'var(--sC)'}[c]||'var(--door)';}
function fmt(x,n){return x.toFixed(n===undefined?1:n);}

/* ---------------- calculadora de corte ---------------- */
function setback(th,r){return th==null?0:r/Math.tan(th*Math.PI/360);}
function cutOf(m,N,d){var r=d/2;
  if(m.code==='P')return m.L*1000/N+d;
  if(m.code==='D')return m.L*1000/N-d;
  return m.L*1000/N-setback(m.ta,r)-setback(m.tb,r);}
function params(){var N=+$('c-n').value||10,d=+$('c-d').value||5,L=+$('c-l').value||210;return {N:N,d:d,L:L};}
function recalc(){
  var p=params(),groups={},order='ABCPDVK';
  MQ.members.forEach(function(m){var c=Math.round(cutOf(m,p.N,p.d)*2)/2,key=m.code+'|'+c;
    var sa=m.code==='P'?0:setback(m.ta,p.d/2),sb=m.code==='P'?0:setback(m.tb,p.d/2);
    if(!groups[key])groups[key]={code:m.code,cut:c,n:0,cc:m.L*1000/p.N,sa:sa,sb:sb};groups[key].n++;});
  var rows=Object.keys(groups).map(function(k){return groups[k];}).sort(function(a,b){
    var oa=order.indexOf(a.code[0]),ob=order.indexOf(b.code[0]);return oa-ob||(a.code<b.code?-1:a.code>b.code?1:0)||b.n-a.n;});
  var html='',pieces=[];
  rows.forEach(function(g){
    var ret=g.code==='D'?('entre postes: −'+fmt(p.d)+' mm'):(g.code==='P'?'entero, de la placa al tope':(fmt(g.sa)+' · '+fmt(g.sb)+' mm'));
    html+='<tr><td><span class="code" style="background:'+codeColor(g.code)+';color:'+(/^[ABC]$/.test(g.code)?'#fff':cssv('--page'))+'">'+g.code+'</span></td><td>'+NAMES[g.code]+'</td><td class="num">'+g.n+'</td><td class="num">'+fmt(g.cc)+' mm</td><td class="num">'+ret+'</td><td class="num strongc">'+fmt(g.cut)+' mm</td></tr>';
    for(var i=0;i<g.n;i++)pieces.push(g.cut);});
  $('cuttab').innerHTML=html;
  // palitos necesarios: primero el mas largo que entre
  pieces.sort(function(a,b){return b-a;});var sticks=[],tooLong=0;
  pieces.forEach(function(x){if(x+1>p.L){tooLong++;return;}for(var i=0;i<sticks.length;i++){if(sticks[i]+x+1<=p.L){sticks[i]+=x+1;return;}}sticks.push(x+1);});
  var total=pieces.reduce(function(a,b){return a+b;},0);
  $('cutsum').innerHTML='<b>'+pieces.length+' palitos cortados</b> ('+fmt(total/1000,2)+' m en total). Con palos de '+p.L+' mm aprovechables salen de <b>'+sticks.length+' palos chinos</b>'+(tooLong?(' <span style="color:var(--warn)">· '+tooLong+' piezas no caben en un solo palo: empalme esas piezas o use palos más largos</span>'):'')+'. Compre '+buyOf(sticks.length+tooLong)+' para tener repuesto.';
  $('m-sticks').textContent=sticks.length+tooLong;$('m-buy').textContent=buyOf(sticks.length+tooLong);
  document.querySelectorAll('[data-pc]').forEach(function(td){var pc=MQ.pieces[+td.getAttribute('data-pc')];td.textContent=fmt(Math.round(cutOf(pc,p.N,p.d)*2)/2)+' mm';});
  document.querySelectorAll('[data-ck]').forEach(function(td){var c=MQ.checks[+td.getAttribute('data-ck')],v;
    if(c.kind==='dist')v=c.m*1000/p.N;else if(c.kind==='height')v=c.m*1000/p.N+p.d/2;else if(c.kind==='doorw')v=c.m*1000/p.N-p.d;else if(c.kind==='doorh')v=c.m*1000/p.N;else v=null;
    td.textContent=v===null?'sobre su marca':fmt(v)+' mm';});
  sizes(p,pieces.length,sticks.length+tooLong);
  if(window.__setModel)window.__setModel(p);
}
function buyOf(n){return Math.ceil(n*1.25/10)*10;}   // 25% de repuesto, redondeado a la decena
function sizes(p,np,ns){var R=MQ.real,N=p.N;
  $('sizes').innerHTML=[['Palitos cortados',np,'',''],['Palos chinos',ns,'','con '+p.L+' mm aprovechables · comprar '+buyOf(ns)],['Diámetro de la base',fmt(R.diam*1000/N,0),'mm','a escala 1:'+N],['Alto hasta el ápice',fmt(R.apex*1000/N,0),'mm','sobre la base']]
  .map(function(s){return '<div class="stat"><div class="v">'+s[1]+'<span class="u">'+s[2]+'</span></div><div class="l">'+s[0]+(s[3]?' · '+s[3]:'')+'</div></div>';}).join('');}
/* ---------------- marcas de avance (se guardan en este navegador) ---------------- */
var STORE='mq-cucuchica-marcas',marks={};
try{marks=JSON.parse(localStorage.getItem(STORE)||'{}')||{};}catch(e){marks={};}
function saveMarks(){try{localStorage.setItem(STORE,JSON.stringify(marks));}catch(e){}}
function progress(){var tot=0,done=0,by={};
  MQ.pieces.forEach(function(pc){tot++;var ok=!!marks['p'+pc.id];if(ok)done++;by[pc.step]=by[pc.step]||[0,0];by[pc.step][1]++;if(ok)by[pc.step][0]++;});
  $('prog-all').textContent=done+' de '+tot+' piezas pegadas';
  document.querySelectorAll('.prog').forEach(function(el){var b=by[el.getAttribute('data-step')]||[0,0];el.textContent=' · '+b[0]+'/'+b[1]+(b[0]===b[1]&&b[1]?' ✓':'');});}
document.querySelectorAll('input.pk').forEach(function(cb){var k=cb.getAttribute('data-k');cb.checked=!!marks[k];
  cb.addEventListener('change',function(){if(cb.checked)marks[k]=1;else delete marks[k];saveMarks();progress();});});
$('reset-checks').addEventListener('click',function(){marks={};saveMarks();document.querySelectorAll('input.pk').forEach(function(cb){cb.checked=false;});progress();});
progress();
['c-n','c-d','c-l'].forEach(function(id){$(id).addEventListener('input',recalc);$(id).addEventListener('change',recalc);});

/* ---------------- vista 3D ---------------- */
function start3d(){
  var host=$('scene');
  if(!window.THREE||!THREE.OrbitControls){$('nogl').hidden=false;return;}
  var renderer;
  try{renderer=new THREE.WebGLRenderer({antialias:true});}catch(e){$('nogl').hidden=false;return;}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.outputEncoding=THREE.sRGBEncoding;
  host.appendChild(renderer.domElement);
  var scene=new THREE.Scene();
  var camera=new THREE.PerspectiveCamera(38,1,0.05,300);
  var controls=new THREE.OrbitControls(camera,renderer.domElement);
  controls.target.set(0,0.9,0);controls.maxPolarAngle=Math.PI*0.96;controls.minDistance=1.2;controls.maxDistance=40;
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
    stick:mat(0xd9b98a,{roughness:0.85})};
  var G={dome:new THREE.Group(),hubs:new THREE.Group(),mem:new THREE.Group(),door:new THREE.Group(),plat:new THREE.Group(),under:new THREE.Group(),people:new THREE.Group()};
  Object.keys(G).forEach(function(k){scene.add(G[k]);});
  var UP=new THREE.Vector3(0,1,0), rods=[];
  function along(a,b,geo,m){var A=V3(a),B=V3(b),dir=B.clone().sub(A),len=dir.length();var mesh=new THREE.Mesh(geo(len),m);
    mesh.position.copy(A.clone().add(B).multiplyScalar(0.5));mesh.quaternion.setFromUnitVectors(UP,dir.normalize());mesh.castShadow=true;mesh.receiveShadow=true;return mesh;}
  var squares=[];
  MQ.struts.forEach(function(s){
    var m=s.sq?along(s.a,s.b,function(L){return new THREE.BoxGeometry(0.05,L,0.05);},M.frame):along(s.a,s.b,function(L){return new THREE.CylinderGeometry(0.016,0.016,L,12);},M.steel);
    if(!s.sq)rods.push(m);else squares.push(m);G.dome.add(m);});
  // tablero de la maqueta (a escala real: 7 x 7 m = 70 x 70 cm a 1:10)
  var board=new THREE.Mesh(new THREE.BoxGeometry(7,0.1,7),mat(0xd8c9ad,{roughness:0.9}));board.receiveShadow=true;scene.add(board);
  // numeros de nodo
  var labelsHost=$('labels'),labels=MQ.nodes.map(function(n){var el=document.createElement('span');el.className='nlab'+(n.t[0]==='P'?' nlab-d':'');el.textContent=n.id;labelsHost.appendChild(el);return {el:el,p:V3(n.p),n:V3(n.n).normalize()};});
  function placeLabels(){var show=$('t-num').checked;labelsHost.hidden=!show;if(!show)return;var w=host.clientWidth,h=host.clientHeight;
    labels.forEach(function(L){var toCam=camera.position.clone().sub(L.p);var front=toCam.dot(L.n)>-0.05*toCam.length();var v=L.p.clone().project(camera);
      if(!front||v.z>1||v.x<-1.05||v.x>1.05||v.y<-1.05||v.y>1.05){L.el.style.display='none';return;}
      L.el.style.display='';L.el.style.transform='translate('+((v.x+1)/2*w).toFixed(1)+'px,'+((1-v.y)/2*h).toFixed(1)+'px) translate(-50%,-130%)';});}
  MQ.hubs.forEach(function(h){var m=new THREE.Mesh(new THREE.CylinderGeometry(0.065,0.065,0.006,24),M.hub);
    m.position.copy(V3(h.p));m.quaternion.setFromUnitVectors(UP,V3(h.n).normalize());m.castShadow=true;G.hubs.add(m);});
  // membrana: un poco por fuera de los tubos
  var C=V3(MQ.center),pos=[];
  MQ.tris.forEach(function(t){t.forEach(function(p){var q=V3(p),dir=q.clone().sub(C).normalize();q.add(dir.multiplyScalar(0.03));pos.push(q.x,q.y,q.z);});});
  var mg=new THREE.BufferGeometry();mg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));mg.computeVertexNormals();
  var memMesh=new THREE.Mesh(mg,M.mem);memMesh.castShadow=true;memMesh.receiveShadow=true;G.mem.add(memMesh);
  // puerta: hoja de 1.00 con vidrio + fijo lateral
  (function(){var q=MQ.door.map(V3),a=q[0],b=q[1],ta=q[3];var w=b.clone().sub(a),wl=w.length(),wd=w.clone().normalize();
    var h=ta.y-a.y-0.025,fr=0.025,leafW=Math.min(1.0,wl-0.05-0.1);var n=new THREE.Vector3().crossVectors(wd,UP).normalize();
    var yaw=Math.atan2(-wd.z,wd.x);
    function panel(x0,x1,y0,y1,m,depth){var g=new THREE.BoxGeometry(x1-x0,y1-y0,depth||0.04);var mesh=new THREE.Mesh(g,m);
      var c=a.clone().add(wd.clone().multiplyScalar((x0+x1)/2)).add(new THREE.Vector3(0,(y0+y1)/2,0));mesh.position.copy(c);mesh.rotation.y=yaw;mesh.castShadow=true;return mesh;}
    var x0=fr,x1=fr+leafW;G.door.add(panel(x0,x1,0.01,h,M.doorw,0.045));G.door.add(panel(x0+0.12,x1-0.12,0.35,h-0.15,M.glass,0.05));
    G.door.add(panel(x1+0.01,wl-fr,0.01,h,M.glass,0.02));})();
  // plataforma
  var pl=MQ.plat,lv=pl.levels;
  function shapeOf(pts){var s=new THREE.Shape();pts.forEach(function(p,i){if(i===0)s.moveTo(p[0],p[1]);else s.lineTo(p[0],p[1]);});s.closePath();return s;}
  function slab(shape,bottom,thick,m){var g=new THREE.ExtrudeGeometry(shape,{depth:thick,bevelEnabled:false});var mesh=new THREE.Mesh(g,m);mesh.rotation.x=-Math.PI/2;mesh.position.y=bottom;mesh.castShadow=true;mesh.receiveShadow=true;return mesh;}
  var ringShape=shapeOf(pl.outer);var hole=new THREE.Path();pl.inner.forEach(function(p,i){if(i===0)hole.moveTo(p[0],p[1]);else hole.lineTo(p[0],p[1]);});ringShape.holes.push(hole);
  G.plat.add(slab(ringShape,-pl.ringH,pl.ringH,M.conc));
  G.plat.add(slab(shapeOf(pl.inner),-pl.deckT,pl.deckT,M.deck));
  G.plat.add(slab(shapeOf(pl.landing),-pl.deckT,pl.deckT,M.deck));
  var ux=MQ.u[0],uy=MQ.u[1],yawU=Math.atan2(uy,ux);
  function box(cx,cy,z0,z1,su,sv,m,grp){var g=new THREE.BoxGeometry(su,z1-z0,sv);var mesh=new THREE.Mesh(g,m);mesh.position.set(cx,(z0+z1)/2,-cy);mesh.rotation.y=yawU;mesh.castShadow=true;mesh.receiveShadow=true;(grp||G.plat).add(mesh);return mesh;}
  pl.piles.forEach(function(p){box(p.x,p.y,lv.ground-0.001,p.top,pl.ped,pl.ped,M.conc);box(p.x,p.y,lv.footing_top,lv.ground,pl.ped,pl.ped,M.conc,G.under);
    box(p.x,p.y,lv.footing_bottom,lv.footing_top,pl.foot,pl.foot,M.conc,G.under);});
  function beamAlong(a,b,z0,z1,w,m){var A=new THREE.Vector3(a[0],(z0+z1)/2,-a[1]),B=new THREE.Vector3(b[0],(z0+z1)/2,-b[1]);var dir=B.clone().sub(A),L=dir.length();
    var g=new THREE.BoxGeometry(L,z1-z0,w);var mesh=new THREE.Mesh(g,m);mesh.position.copy(A.add(B).multiplyScalar(0.5));mesh.rotation.y=Math.atan2(-dir.z,dir.x);mesh.castShadow=true;mesh.receiveShadow=true;G.plat.add(mesh);}
  pl.beams.forEach(function(b){beamAlong(b.a,b.b,lv.beam_bottom,lv.beam_top,pl.beamB,M.beam);});
  pl.joists.forEach(function(j){beamAlong(j.a,j.b,lv.beam_top,lv.joist_top,pl.joistB,M.joist);});
  pl.steps.forEach(function(s){var c=s.c;var cx=(c[0][0]+c[2][0])/2,cy=(c[0][1]+c[2][1])/2;
    var su=Math.hypot(c[1][0]-c[0][0],c[1][1]-c[0][1]),sv=Math.hypot(c[3][0]-c[0][0],c[3][1]-c[0][1]);box(cx,cy,lv.ground,s.top,su,sv,M.conc);});
  var ground=new THREE.Mesh(new THREE.CircleGeometry(14,64),M.ground);ground.rotation.x=-Math.PI/2;ground.position.y=lv.ground;ground.receiveShadow=true;scene.add(ground);
  window.__ground=ground;
  // persona 1.75 m y cama 1.60 x 2.00
  function uv(u,v){return [u*MQ.u[0]+v*MQ.v[0],u*MQ.u[1]+v*MQ.v[1]];}
  function person(u,v,face){var p=uv(u,v),g=new THREE.Group();
    function part(geo,m,y){var mesh=new THREE.Mesh(geo,m);mesh.position.y=y;mesh.castShadow=true;g.add(mesh);}
    part(new THREE.CylinderGeometry(0.075,0.065,0.82,12),M.pants,0.41);g.children[0].position.x=0.085;
    part(new THREE.CylinderGeometry(0.075,0.065,0.82,12),M.pants,0.41);g.children[1].position.x=-0.085;
    part(new THREE.CylinderGeometry(0.19,0.16,0.62,14),M.cloth,1.13);
    part(new THREE.CylinderGeometry(0.05,0.045,0.6,10),M.cloth,1.12);g.children[3].position.x=0.24;
    part(new THREE.CylinderGeometry(0.05,0.045,0.6,10),M.cloth,1.12);g.children[4].position.x=-0.24;
    part(new THREE.SphereGeometry(0.11,18,14),M.skin,1.64);
    g.position.set(p[0],0,-p[1]);g.rotation.y=face;G.people.add(g);}
  person(0.95,0.35,yawU+Math.PI/2);
  (function(){var p=uv(-1.55,0),g=new THREE.Group();var fr=new THREE.Mesh(new THREE.BoxGeometry(2.0,0.3,1.6),M.bedframe);fr.position.y=0.15;
    var mt=new THREE.Mesh(new THREE.BoxGeometry(1.96,0.22,1.56),M.bed);mt.position.y=0.41;fr.castShadow=mt.castShadow=true;fr.receiveShadow=mt.receiveShadow=true;g.add(fr);g.add(mt);
    g.position.set(p[0],0,-p[1]);g.rotation.y=yawU;G.people.add(g);})();
  // vistas
  function view(name){var d=new THREE.Vector3(MQ.u[0],0,-MQ.u[1]);var side=new THREE.Vector3().crossVectors(d,UP);
    if(name==='frente'){camera.position.copy(d.clone().multiplyScalar(11).add(new THREE.Vector3(0,1.6,0)));controls.target.set(0,1.0,0);}
    else if(name==='planta'){camera.position.set(0.001,13,0);controls.target.set(0,0,0);}
    else if(name==='adentro'){var eye=d.clone().multiplyScalar(-0.4).add(side.clone().multiplyScalar(1.25));camera.position.set(eye.x,1.6,eye.z);controls.target.copy(d.clone().multiplyScalar(2.9)).setY(1.15);}
    else{camera.position.copy(d.clone().multiplyScalar(7.0).add(side.clone().multiplyScalar(-4.4)).add(new THREE.Vector3(0,4.0,0)));controls.target.set(0,0.9,0);}
    controls.update();render();}
  document.querySelectorAll('.vbtn').forEach(function(b){b.addEventListener('click',function(){view(b.getAttribute('data-view'));});});
  function vis(){G.mem.visible=$('t-mem').checked;G.door.visible=$('t-door').checked;var plat=$('t-plat').checked;G.plat.visible=plat;
    G.people.visible=$('t-people').checked;G.under.visible=false;
    var model=$('t-model').checked;G.hubs.visible=!model;var p=params();var r=model?p.d*p.N/1000/2:0.016,f=r/0.016;
    rods.forEach(function(m){m.scale.x=f;m.scale.z=f;m.material=model?M.stick:M.steel;});
    squares.forEach(function(m){var g=model?(p.d*p.N/1000)/0.05:1;m.scale.x=g;m.scale.z=g;m.material=model?M.stick:M.frame;});
    board.visible=model&&!plat;board.position.y=-r-0.05;ground.visible=!board.visible;render();}
  ['t-mem','t-door','t-plat','t-people','t-model','t-num'].forEach(function(id){$(id).addEventListener('change',vis);});
  window.__setModel=function(){vis();};
  function resize(){var w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}
  function render(){renderer.render(scene,camera);placeLabels();}
  controls.addEventListener('change',render);
  scene.background=new THREE.Color(cssv('--scene')||'#dfe6ea');
  window.addEventListener('resize',resize);
  if(window.matchMedia)window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(){scene.background=new THREE.Color(cssv('--scene'));render();});
  view('tres');vis();resize();
}
recalc();
start3d();
})();
"""


# ---------------------------------------------------------------- plantillas imprimibles

PAGE_W, PAGE_H, MARGIN = 279.4, 215.9, 8.0      # carta horizontal, mm


def plan_content(PL, D, N, pieces):
    """Planta de la estructura en mm (1:N), eje de la puerta hacia arriba (x = v, y = -u):
    marcas de anclaje, palitos del anillo de base con su codigo, postes de la puerta y la
    proyeccion de cada nodo de arriba (para la prueba de la plomada)."""
    u3, v3 = D.door["u"], D.door["v"]
    def P(x, y):   # coordenadas del piso (X, Y) -> hoja
        u = x*u3[0] + y*u3[1]; v = x*v3[0] + y*v3[1]
        return (v*1000/N, -u*1000/N)
    Pv = D.verts
    o = []
    x0, y0 = P(-3.2*u3[0], -3.2*u3[1]); x1, y1 = P(3.2*u3[0], 3.2*u3[1])
    o.append(f'<line x1="{f(x0,2)}" y1="{f(y0,2)}" x2="{f(x1,2)}" y2="{f(y1,2)}" class="axis"/>')
    x0, y0 = P(-3.2*v3[0], -3.2*v3[1]); x1, y1 = P(3.2*v3[0], 3.2*v3[1])
    o.append(f'<line x1="{f(x0,2)}" y1="{f(y0,2)}" x2="{f(x1,2)}" y2="{f(y1,2)}" class="axis"/>')
    apex = [v for v in D.active if v not in D.boundary_verts and abs(Pv[v][0]) < 1e-6 and abs(Pv[v][1]) < 1e-6]
    ctext = f"centro = plomada de #{apex[0]} (cúspide)" if apex else "centro"
    o.append(f'<circle cx="0" cy="0" r="1.6" class="center"/><text x="3" y="-3" class="lbl">{ctext}</text>')
    # proyeccion de los nodos de arriba (plomada)
    for v in D.active:
        if v in D.boundary_verts or v in apex:
            continue
        x, y = P(Pv[v][0], Pv[v][1])
        o.append(f'<path d="M {f(x-2.2,2)} {f(y,2)} H {f(x+2.2,2)} M {f(x,2)} {f(y-2.2,2)} V {f(y+2.2,2)}" class="plumb"/>'
                 f'<text x="{f(x+2.6,2)}" y="{f(y-1.2,2)}" class="plumbl">{v}</text>')
    # palitos del anillo de base (paso 0) con su codigo
    for pc in pieces:
        if pc["step"] != 0:
            continue
        a, b = pc["from"], pc["to"]
        xa, ya = P(Pv[a][0], Pv[a][1]); xb, yb = P(Pv[b][0], Pv[b][1])
        o.append(f'<line x1="{f(xa,2)}" y1="{f(ya,2)}" x2="{f(xb,2)}" y2="{f(yb,2)}" class="basestick"/>')
        mx, my = (xa+xb)/2, (ya+yb)/2
        L = math.hypot(mx, my) or 1
        o.append(f'<text x="{f(mx + mx/L*7,2)}" y="{f(my + my/L*7 + 1.2,2)}" class="sid">{pc["id"]} {pc["code"]}</text>')
    for v in D.boundary_verts:
        x, y = P(Pv[v][0], Pv[v][1])
        high = Pv[v][2] > 1e-6
        o.append(f'<circle cx="{f(x,2)}" cy="{f(y,2)}" r="3" class="{"anc-h" if high else "anc"}"/>')
        L = math.hypot(x, y)
        o.append(f'<text x="{f(x + x/L*13,2)}" y="{f(y + y/L*13 + 1.5,2)}" class="nodel">#{v}{f" taco {Pv[v][2]*1000/N:.1f}" if high else ""}</text>')
    for v in (D.door["a"], D.door["b"]):
        x, y = P(Pv[v][0], Pv[v][1])
        o.append(f'<rect x="{f(x-2.5,2)}" y="{f(y-2.5,2)}" width="5" height="5" class="post"/>')
    xa, ya = P(Pv[D.door["a"]][0], Pv[D.door["a"]][1]); xb, yb = P(Pv[D.door["b"]][0], Pv[D.door["b"]][1])
    o.append(f'<text x="{f((xa+xb)/2,2)}" y="{f(ya-9,2)}" class="doort">PUERTA: postes sobre #{D.door["a"]} y #{D.door["b"]}</text>')
    x, y = P(-1.4*u3[0], -1.4*u3[1])
    o.append(f'<text x="{f(x,2)}" y="{f(y,2)}" class="lbl" text-anchor="middle">↑ eje de la puerta</text>')
    return "".join(o)


def page(inner, landscape=True):
    return f'<section class="page">{inner}</section>'


def scale_bar(x, y, L=100):
    t = "".join(f'<line x1="{x+i*10}" y1="{y}" x2="{x+i*10}" y2="{y + (4 if i % 5 == 0 else 2.5)}" class="tb"/>' for i in range(int(L/10)+1))
    return (f'<line x1="{x}" y1="{y}" x2="{x+L}" y2="{y}" class="bar"/>{t}'
            f'<text x="{x+L/2}" y="{y-2}" class="bl" text-anchor="middle">{L/10:.0f} cm: mida esta barra</text>')


def build_templates(D, PL, members, data):
    N = SCALE
    pages = []
    W, H = PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN
    DRAW_H = H - 10
    OV = 10.0
    step_x, step_y = W - OV, DRAW_H - OV
    span = 2*(3.0 + 0.30)*1000/N           # anillo de 3.00 m de radio + etiquetas
    cols = math.ceil((span - OV)/step_x); rows = math.ceil((span - OV)/step_y)
    x0 = -(cols*step_x + OV)/2; y0 = -(rows*step_y + OV)/2
    pieces = data["pieces"]
    content = plan_content(PL, D, N, pieces)
    groups = cut_groups(members, N, STICK_D)
    mem_by_edge = {tuple(sorted(m["e"])): m for m in members}

    # ---- portada
    idx = "".join(f'<rect x="{150 + c*14}" y="{86 + r*11}" width="13" height="10" class="mini"/><text x="{156.5 + c*14}" y="{92.5 + r*11}" class="minil">{chr(65+c)}{r+1}</text>'
                  for r in range(rows) for c in range(cols))
    cover = f"""<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">
<text x="0" y="12" class="h1">Maqueta de la estructura 1:{N} · domo Cucuchica con puerta</text>
<text x="0" y="20" class="p">Plantillas a tamaño real para palitos de {STICK_D:.0f} mm. Generado desde el modelo verificado (maqueta/maqueta.py).</text>
<text x="0" y="34" class="h2">1. Antes que nada: imprimir al 100% ("tamaño real"), sin "ajustar a la página"</text>
{scale_bar(0, 48)}
<line x1="240" y1="70" x2="240" y2="170" class="bar"/>{"".join(f'<line x1="240" y1="{70+i*10}" x2="{244 if i % 5 == 0 else 242.5}" y2="{70+i*10}" class="tb"/>' for i in range(11))}
<text x="246" y="122" class="bl">10 cm</text>
<text x="0" y="62" class="p">Si alguna barra no mide exactamente 10 cm, revise la opción de escala de la impresora.</text>
<text x="0" y="76" class="h2">2. Contenido</text>
<text x="0" y="84" class="p">· Planta base en {rows*cols} hojas (A1 a {chr(64+cols)}{rows}), mapa a la derecha</text>
<text x="0" y="91" class="p">· Etiquetas de los {len(pieces)} palitos</text>
<text x="0" y="98" class="p">· Reglas de corte ({len(groups)} largos)</text>
<text x="0" y="105" class="p">· Discos de ángulo de cada tipo de nodo</text>
<text x="0" y="112" class="p">· Hoja de control para anotar las mediciones</text>
<text x="0" y="126" class="h2">3. Unir la planta</text>
<text x="0" y="134" class="p">Recorte cada hoja por su borde fino (arriba e izquierda). Apóyela sobre la franja</text>
<text x="0" y="141" class="p">gris de la hoja vecina haciendo coincidir las cruces, y pegue con cinta.</text>
<text x="150" y="80" class="h2">Mapa de hojas</text>
{idx}
</svg>"""
    pages.append(page(cover))

    # ---- planta en mosaico
    for r in range(rows):
        for c in range(cols):
            vx, vy = x0 + c*step_x, y0 + r*step_y
            marks = ""
            for mx in (vx + OV/2, vx + step_x + OV/2):
                for my in (vy + OV/2, vy + step_y + OV/2):
                    marks += f'<path d="M {f(mx-4,2)} {f(my,2)} H {f(mx+4,2)} M {f(mx,2)} {f(my-4,2)} V {f(my+4,2)}" class="cross"/>'
            shade = (f'<rect x="{f(vx+step_x,2)}" y="{f(vy,2)}" width="{OV}" height="{f(DRAW_H,2)}" class="ov"/>'
                     f'<rect x="{f(vx,2)}" y="{f(vy+step_y,2)}" width="{f(W,2)}" height="{OV}" class="ov"/>')
            border = f'<rect x="{f(vx+0.15,2)}" y="{f(vy+0.15,2)}" width="{f(W-0.3,2)}" height="{f(DRAW_H-0.3,2)}" class="edge"/>'
            svg = (f'<svg viewBox="{f(vx,2)} {f(vy,2)} {f(W,2)} {f(DRAW_H,2)}" width="{W}mm" height="{DRAW_H}mm" class="tile">'
                   f'{shade}{content}{marks}{border}</svg>'
                   f'<div class="foot"><b>Hoja {chr(65+c)}{r+1}</b> · planta base 1:{N} · columna {chr(65+c)} de {chr(64+cols)}, fila {r+1} de {rows} · '
                   f'círculos: anclajes · cruces finas: dónde cae la plomada de cada nodo de arriba · eje de la puerta hacia arriba</div>')
            pages.append(page(svg))

    # ---- etiquetas (banderitas): se doblan alrededor del palito
    fw, fh, gap, top = 36.0, 9.0, 1.2, 17.0
    per_row = int((W + gap)//(fw + gap)); per_col = int((H - top + gap)//(fh + gap))
    colors = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
    lab_pages, cur, n_on = [], "", 0
    for k, pc in enumerate(pieces):
        m = mem_by_edge[tuple(sorted((pc["from"], pc["to"])))]
        L = round(cut_mm(m, N, STICK_D)*2)/2      # mismo redondeo que la regla y el checklist
        i = n_on % per_row; j = n_on // per_row
        x = i*(fw + gap); y = top + j*(fh + gap)
        col = colors.get(pc["code"], "#3b3f44")
        cur += (f'<rect x="{f(x,2)}" y="{f(y,2)}" width="{fw}" height="{fh}" class="flag"/>'
                f'<rect x="{f(x,2)}" y="{f(y,2)}" width="3" height="{fh}" fill="{col}"/>'
                f'<line x1="{f(x+fw/2,2)}" y1="{f(y,2)}" x2="{f(x+fw/2,2)}" y2="{f(y+fh,2)}" class="fold"/>')
        for tx in (x + 4.5, x + fw/2 + 2):
            cur += (f'<text x="{f(tx,2)}" y="{f(y+3.2,2)}" class="fl1">{pc["id"]} {pc["code"]}</text>'
                    f'<text x="{f(tx,2)}" y="{f(y+5.9,2)}" class="fl2">#{pc["from"]}→#{pc["to"]}</text>'
                    f'<text x="{f(tx,2)}" y="{f(y+8.3,2)}" class="fl3">{L:.1f} mm</text>')
        n_on += 1
        if n_on == per_row*per_col or k == len(pieces) - 1:
            lab_pages.append(cur); cur = ""; n_on = 0
    for lp in lab_pages:
        head = (f'<text x="0" y="6" class="h2">Etiquetas de los palitos · 1:{N} · palitos de {STICK_D:.0f} mm</text>'
                f'<text x="0" y="11" class="p">Recorte cada banderita, dóblela por la línea del medio alrededor del palito y péguela. Código = paso.número, igual que en el checklist</text>'
                f'<text x="0" y="14.6" class="p">y en la secuencia real. Debajo: los dos nodos que une y el largo de corte.</text>')
        pages.append(page(f'<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">{head}{lp}</svg>'))

    # ---- reglas de corte
    names = {"A": "barra A", "B": "barra B", "C": "barra C", "P": "poste marco", "D": "dintel", "V": "viga techo", "K1": "amarre bajo", "K2": "amarre alto"}
    rl = f'<text x="0" y="10" class="h2">Reglas de corte · escala 1:{N} · palitos de {STICK_D:.0f} mm</text>'
    rl += '<text x="0" y="17" class="p">Apoye el palito sobre la barra, con la punta en el tope izquierdo, y marque en el tope derecho.</text>'
    y = 28
    for (code, L), n in groups:
        colr = colors.get(code, "#3b3f44")
        rl += (f'<rect x="0" y="{y}" width="{L:.2f}" height="7" fill="{colr}" fill-opacity=".22" stroke="{colr}" stroke-width=".4"/>'
               f'<line x1="0" y1="{y-1.5}" x2="0" y2="{y+8.5}" class="stop"/><line x1="{L:.2f}" y1="{y-1.5}" x2="{L:.2f}" y2="{y+8.5}" class="stop"/>'
               + (f'<text x="{L+3:.2f}" y="{y+5.2}" class="rl"><tspan font-weight="700">{code}</tspan> {names[code]} · {L:.1f} mm · ×{n}</text>'
                  if L + 62 < W else
                  f'<text x="4" y="{y+5.2}" class="rl"><tspan font-weight="700">{code}</tspan> {names[code]} · {L:.1f} mm · ×{n}</text>'))
        y += 12.5
    rl += scale_bar(W-110, H-6)
    pages.append(page(f'<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">{rl}</svg>'))

    # ---- discos de angulo
    def disc(name, v, cx, cy, R=30.0):
        g = door.hub_geometry(D, v)
        mem, gaps = g["members"], g["az_gaps"]
        if not g["open"]:
            kk = next((i for i, m in enumerate(mem) if m["label"] in ("P", "K1", "K2", "V", "C")), 0)
            mem = mem[kk:] + mem[:kk]; gaps = gaps[kk:] + gaps[:kk]
        n = len(mem)
        cum = [0.0]
        for gg in gaps[:n-1]:
            cum.append(cum[-1] + gg)
        o = f'<circle cx="{cx}" cy="{cy}" r="{R}" class="disc"/>'
        for i, m in enumerate(mem):
            a = math.radians(cum[i] - 90)
            col = colors.get(m["label"], "#3b3f44")
            o += f'<line x1="{cx}" y1="{cy}" x2="{f(cx + R*math.cos(a),2)}" y2="{f(cy + R*math.sin(a),2)}" stroke="{col}" stroke-width=".7"/>'
            o += f'<text x="{f(cx + (R+4.5)*math.cos(a),2)}" y="{f(cy + (R+4.5)*math.sin(a) + 1.2,2)}" class="dl" fill="{col}">{m["label"]}</text>'
        arcs = n if not g["open"] else n - 1
        for i in range(arcs):
            a0 = cum[i]; a1 = cum[i+1] if i + 1 < n else 360.0
            am = math.radians((a0 + a1)/2 - 90)
            o += f'<text x="{f(cx + R*0.62*math.cos(am),2)}" y="{f(cy + R*0.62*math.sin(am) + 1,2)}" class="da">{gaps[i]:.1f}°</text>'
        o += f'<circle cx="{cx}" cy="{cy}" r="1.2" class="center"/>'
        ids = [t["hub_ids"] for t in D.hub_types if t["name"] == name][0]
        o += f'<text x="{cx}" y="{cy + R + 11}" class="dn">{name} · nodos {", ".join("#" + str(x) for x in ids[:6])}{"…" if len(ids) > 6 else ""}</text>'
        return o
    disc_types = [t["name"] for t in D.hub_types if t["name"] != "PE"]
    per_page = 6
    for pg in range(0, len(disc_types), per_page):
        body = (f'<text x="0" y="8" class="h2">Discos de ángulo (sirven a cualquier escala)</text>'
                f'<text x="0" y="14" class="p">Recorte el disco y apóyelo sobre el nodo terminado, mirando desde afuera del domo y con el centro sobre el punto de pega:</text>'
                f'<text x="0" y="18.4" class="p">cada palito tiene que caer sobre su línea. Son los mismos ángulos que se marcan en los discos de acero del domo real.</text>')
        for i, name in enumerate(disc_types[pg:pg+per_page]):
            v = [t["hub_ids"] for t in D.hub_types if t["name"] == name][0][0]
            cx = 45 + (i % 3)*88; cy = 62 + (i // 3)*84
            body += disc(name, v, cx, cy)
        pages.append(page(f'<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">{body}</svg>'))

    # ---- hoja de control
    rowsh = ""
    yy = 30
    for i, c in enumerate(data["checks"]):
        if c["kind"] == "dist": val = f"{c['m']*1000/N:.1f} mm"
        elif c["kind"] == "height": val = f"{c['m']*1000/N + STICK_D/2:.1f} mm"
        elif c["kind"] == "doorw": val = f"{c['m']*1000/N - STICK_D:.1f} mm"
        elif c["kind"] == "doorh": val = f"{c['m']*1000/N:.1f} mm"
        else: val = "sobre su cruz"
        where = c["where"] if len(c["where"]) < 44 else c["where"][:42].rstrip(", ") + "…"
        rowsh += (f'<text x="0" y="{yy}" class="ct">{i+1}. {esc(c["what"])}</text>'
                  f'<text x="112" y="{yy}" class="cw">{esc(where)}</text>'
                  f'<text x="192" y="{yy}" class="cv">{val}</text><text x="219" y="{yy}" class="cw">± {c["tol"]} mm</text>'
                  f'<line x1="236" y1="{yy+0.8}" x2="262" y2="{yy+0.8}" class="wline"/>')
        yy += 8.1
    sheet = (f'<text x="0" y="8" class="h2">Hoja de control · maqueta 1:{N} · palitos de {STICK_D:.0f} mm</text>'
             f'<text x="0" y="14" class="p">Distancias entre centros de nodo (centros de los puntos de pega). Alturas desde el tablero. Ninguna de estas medidas se usó para cortar.</text>'
             f'<text x="0" y="22" class="th">Qué medir</text><text x="112" y="22" class="th">Entre</text><text x="192" y="22" class="th">Debe dar</text>'
             f'<text x="219" y="22" class="th">Tol.</text><text x="236" y="22" class="th">Medido</text>{rowsh}')
    pages.append(page(f'<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">{sheet}</svg>'))

    css = f"""@page {{ size: {PAGE_W}mm {PAGE_H}mm; margin: 0 }}
*{{box-sizing:border-box}} html,body{{margin:0; padding:0; background:#fff}}
body{{font-family:"DejaVu Sans","Helvetica","Arial",sans-serif; color:#111}}
.page{{width:{PAGE_W}mm; height:{PAGE_H}mm; padding:{MARGIN}mm; page-break-after:always; break-after:page; overflow:hidden; position:relative}}
.page:last-child{{page-break-after:auto; break-after:auto}}
svg{{display:block}}
.foot{{font-size:3.2mm; color:#333; margin-top:2mm}}
.h1{{font-size:7px; font-weight:700}} .h2{{font-size:4.6px; font-weight:700}} .p{{font-size:3.3px}} .lbl{{font-size:3px; fill:#333}}
.bl{{font-size:3.2px; fill:#111}} .bar{{stroke:#111; stroke-width:.5}} .tb{{stroke:#111; stroke-width:.35}}
.axis{{stroke:#bbb; stroke-width:.25}} .center{{fill:#111}}
.anc{{fill:#fff; stroke:#111; stroke-width:.45}} .anc-h{{fill:#2a78d6; stroke:#111; stroke-width:.45}}
.nodel{{font-size:3px; text-anchor:middle; fill:#111; font-weight:700}}
.basestick{{stroke:#999; stroke-width:{STICK_D}; stroke-linecap:round; stroke-opacity:.35}}
.sid{{font-size:2.8px; text-anchor:middle; fill:#333; font-weight:700}}
.post{{fill:#3b3f44}} .doort{{font-size:3.4px; text-anchor:middle; font-weight:700}}
.plumb{{stroke:#555; stroke-width:.25; fill:none}} .plumbl{{font-size:2.5px; fill:#555}}
.cross{{stroke:#111; stroke-width:.3; fill:none}} .ov{{fill:#000; fill-opacity:.07}} .edge{{fill:none; stroke:#666; stroke-width:.3}}
.mini{{fill:#f1f1ee; stroke:#777; stroke-width:.3}} .minil{{font-size:3.2px; text-anchor:middle}}
.flag{{fill:#fff; stroke:#888; stroke-width:.25}} .fold{{stroke:#bbb; stroke-width:.2}}
.fl1{{font-size:2.9px; font-weight:700}} .fl2{{font-size:2.4px}} .fl3{{font-size:2.1px; fill:#555}}
.stop{{stroke:#111; stroke-width:.5}} .rl{{font-size:3.4px}}
.disc{{fill:none; stroke:#999; stroke-width:.3}} .dl{{font-size:3px; text-anchor:middle; font-weight:700}}
.da{{font-size:2.8px; text-anchor:middle; fill:#111}} .dn{{font-size:3.2px; text-anchor:middle; font-weight:700}}
.th{{font-size:3px; font-weight:700; fill:#555}} .ct{{font-size:3px}} .cw{{font-size:2.8px; fill:#444}} .cv{{font-size:3.2px; font-weight:700}}
.wline{{stroke:#999; stroke-width:.3}}
"""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Plantillas maqueta de la estructura 1:{N}</title><style>{css}</style></head>
<body>{''.join(pages)}</body></html>""", len(pages), rows*cols


def main():
    D, PL, members, data = collect()
    with open(os.path.join(HERE, "maqueta.html"), "w", encoding="utf-8") as fh:
        fh.write(build_page(D, PL, members, data))
    tpl, npages, ntiles = build_templates(D, PL, members, data)
    with open(os.path.join(HERE, "maqueta_plantillas.html"), "w", encoding="utf-8") as fh:
        fh.write(tpl)
    groups = cut_groups(members, SCALE, STICK_D)
    print(f"Escrito: maqueta.html y maqueta_plantillas.html ({npages} paginas, planta en {ntiles} hojas)")
    print(f"Cortes a 1:{SCALE} con palitos de {STICK_D:.0f} mm:")
    for (code, L), n in groups:
        print(f"   {code:>2} x{n:<3} cortar a {L:6.1f} mm")


if __name__ == "__main__":
    main()
