"""
Maqueta a escala del domo Cucuchica: palos chinos y pega loca.

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
from dome_model import v_sub, v_norm, v_dot  # noqa: E402

SCALE = 10              # escala recomendada 1:10 (plantillas impresas)
STICK_D = 5.0           # mm, palo chino tipico en la parte recta
STICK_USABLE = 220.0    # mm, parte recta aprovechable de un palo chino de 24 cm (sin la punta)
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


def collect():
    D = door.build_dome_with_door()
    PL, PR, PQ, _ = plat.evaluate(verbose=False)
    P = D.verts
    members = build_members(D)
    sec = {e: door.MEMBER_INFO[D.edge_label[e]][0] for e in D.edges}
    struts = [{"a": [round(c, 4) for c in P[a]], "b": [round(c, 4) for c in P[b]], "code": D.edge_label[(a, b)],
               "sq": sec[(a, b)] == "cuad50x2"} for a, b in D.edges]
    hubs = []
    for v in D.active:
        if D.type_of[v] == "PE":
            continue
        n = [P[v][k] - D.center[k] for k in range(3)]
        L = math.sqrt(sum(x*x for x in n))
        hubs.append({"p": [round(c, 4) for c in P[v]], "n": [round(x/L, 4) for x in n]})
    tris = [[[round(c, 4) for c in P[i]] for i in t] for t in D.triangles]
    dd = D.door
    quad = [[round(c, 4) for c in P[i]] for i in (dd["a"], dd["b"], dd["Tb"], dd["Ta"])]

    def xy(u, v): return [round(c, 4) for c in PL.to_xy(u, v)]
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
    data = {"struts": struts, "hubs": hubs, "tris": tris, "door": quad, "center": [round(c, 4) for c in D.center],
            "u": [round(dd["u"][0], 5), round(dd["u"][1], 5)], "v": [round(dd["v"][0], 5), round(dd["v"][1], 5)],
            "plat": platd,
            "members": [{"code": m["code"], "L": round(m["L"], 5), "ta": None if m["ta"] is None else round(m["ta"], 3),
                         "tb": None if m["tb"] is None else round(m["tb"], 3)} for m in members],
            "real": {"diam": 6.0, "apex": round(max(p[2] for p in P), 4), "clear_w": round(door.bending_door_frame(D, 1)["clear_w"], 4),
                     "clear_h": round(door.bending_door_frame(D, 1)["clear_h"], 4), "freeboard": plat.FREEBOARD,
                     "extent_u": round(PL.steps[-1]["u1"], 3), "ring_len": round(PQ["ring_len"], 3),
                     "head_z": dd["head_z"], "zig": 0.0486}}
    return D, PL, members, data


# ---------------------------------------------------------------- pagina

def build_page(D, PL, members, data):
    groups = cut_groups(members, SCALE, STICK_D)
    js = JS.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    return f"""<title>Maqueta Domo Cucuchica</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="hero">
  <div class="eyebrow">Glamping Cucuchica · maqueta a escala exacta · palos chinos y pega loca</div>
  <h1>Maqueta 1:{SCALE} del domo con su puerta y su plataforma</h1>
  <p class="lede">Primero, cómo se ve la unidad terminada, con los materiales reales. Después, todo para armarla en pequeño: la escala, qué material usar para cada parte, el largo exacto de cada palito según su grosor, las plantillas para imprimir a tamaño real y el orden de armado. Las medidas salen del mismo modelo verificado del plano de taller.</p>
  <div class="statgrid" id="sizes"></div>
</header>

<section id="vista">
  <h2>Así se ve</h2>
  <p class="sub">Arrastre para girar, pellizco o rueda para acercar. La persona mide 1.75 m y la cama es de 1.60 × 2.00 m, para dar la escala. Con "maqueta" activado, los tubos se dibujan del grueso de los palitos, para ver cómo va a quedar la maqueta.</p>
  <div class="scene-wrap">
    <div id="scene" role="img" aria-label="Vista 3D del domo con puerta y plataforma"><div id="nogl" hidden>Este navegador no pudo abrir la vista 3D (WebGL). El resto de la página funciona igual.</div></div>
    <div class="scene-bar">
      <div class="views" role="group" aria-label="Vistas">
        <button type="button" class="vbtn" data-view="tres">3/4</button><button type="button" class="vbtn" data-view="frente">Frente</button><button type="button" class="vbtn" data-view="planta">Planta</button><button type="button" class="vbtn" data-view="adentro">Adentro</button>
      </div>
      <div class="toggles">
        <label><input type="checkbox" id="t-mem" checked> membrana</label>
        <label><input type="checkbox" id="t-door" checked> puerta</label>
        <label><input type="checkbox" id="t-plat" checked> plataforma</label>
        <label><input type="checkbox" id="t-people" checked> persona y cama</label>
        <label><input type="checkbox" id="t-under"> bajo tierra</label>
        <label class="strong"><input type="checkbox" id="t-model"> maqueta</label>
      </div>
    </div>
  </div>
</section>

<section id="escala">
  <h2>La escala</h2>
  <div>
    <div>
      <p>Recomendado: <b>1:10</b>. El domo queda de 60 cm de diámetro y 25 cm de alto, cabe en una mesa y cada barra sale de un palo chino. A esa escala, un palo chino de 5 mm es exactamente el tubo cuadrado de 50 mm del marco de la puerta. Las barras del domo (tubo de 32 mm) quedan 1.6 veces más gruesas que las reales; si quiere el grosor exacto, use <b>palitos de brocheta de 3 mm</b> para el domo y palos chinos para el marco.</p>
      <p>Los largos y los ángulos son exactos a cualquier escala. Lo que cambia es cuánto se nota el grosor del palito.</p>
    </div>
    <div class="tbl"><table><thead><tr><th>Escala</th><th class="num">Domo</th><th class="num">Barra A</th><th class="num">Palito de 5 mm equivale a</th><th>Comentario</th></tr></thead><tbody id="scaletab"></tbody></table></div>
  </div>
</section>

<section id="corte">
  <h2>Largo de cada palito</h2>
  <p class="sub">Cambie la escala, el grosor del palito y el largo aprovechable (sin la punta delgada): la tabla se recalcula. "Retiro" es lo que se descuenta en cada punta para que los palitos no choquen en el nodo; así el eje de cada palito sigue apuntando al centro exacto del nodo.</p>
  <div class="calc">
    <label>Escala 1:<select id="c-n"><option value="10" selected>10</option><option value="15">15</option><option value="20">20</option></select></label>
    <label>Grosor del palito <input id="c-d" type="number" min="2" max="8" step="0.5" value="{STICK_D}"> mm</label>
    <label>Largo aprovechable <input id="c-l" type="number" min="100" max="300" step="5" value="{STICK_USABLE:.0f}"> mm</label>
  </div>
  <div class="tbl"><table><thead><tr><th>Pieza</th><th>Qué es</th><th class="num">Cantidad</th><th class="num">Centro a centro</th><th class="num">Retiros</th><th class="num">Cortar a</th></tr></thead><tbody id="cuttab"></tbody></table></div>
  <p class="sum" id="cutsum"></p>
</section>

<section id="plataforma">
  <h2>Plataforma y demás piezas a escala</h2>
  <p class="sub">Medidas para la escala elegida arriba. La plataforma de la maqueta se simplifica en bloques y una placa: lo que se ve por fuera queda igual al real.</p>
  <div class="tbl"><table><thead><tr><th>Parte</th><th>Real</th><th>En la maqueta</th><th>Material sugerido</th></tr></thead><tbody id="partstab"></tbody></table></div>
</section>

<section id="plantillas">
  <h2>Plantillas para imprimir</h2>
  <p>El archivo <span class="mono">maqueta_plantillas.pdf</span>, a escala 1:10 y con palitos de 5 mm, trae:</p>
  <ol class="steps">
    <li><b>Portada</b> con una barra de control de 10 cm. Hay que imprimir <b>al 100% (tamaño real)</b>, sin "ajustar a la página", y medir esa barra con una regla antes de seguir.</li>
    <li><b>Planta base en 12 hojas</b> (3 × 4) que se unen con cinta, con 1 cm de solape y cruces de alineación. Trae la placa del piso, los 15 anclajes numerados, los 23 pilotes, la puerta y los ejes.</li>
    <li><b>Descanso y escalones</b> por separado.</li>
    <li><b>Triángulos</b> P1, P2 y V1–V4 a escala. Sirven para comprobar los triángulos armados y para cortar la cubierta en papel mantequilla, con una pestaña de 5 mm para pegar.</li>
    <li><b>Reglas de corte</b>: una barra impresa del largo exacto de cada tipo de palito, para marcar sin medir.</li>
  </ol>
</section>

<section id="armado">
  <h2>Paso a paso</h2>
  <ol class="steps">
    <li><b>Imprima y controle la escala</b>: la barra de 10 cm tiene que medir 10 cm.</li>
    <li><b>Base.</b> Pegue la planta en un cartón o anime firme. Pegue los 23 bloques de pilote sobre sus cuadrados y la placa del piso encima. La tira del borde imita la viga de anillo.</li>
    <li><b>Corte todos los palitos</b> con la tabla o con las reglas impresas. Lije las puntas planas. Separe los palitos por tipo y márquelos con color: A azul, B naranja, C verde.</li>
    <li><b>Anillo de base.</b> Pegue los 15 palitos del borde sobre la placa, de anclaje en anclaje. Bajo los 5 nodos altos (H5) va un taco de 4.9 mm: sirve una rodaja de palito.</li>
    <li><b>Arme anillo por anillo</b>, en el mismo orden que la secuencia real. En el paso 1 los 4 triángulos quedan sueltos como bisagra: sosténgalos con plastilina o cinta hasta el paso 2. Igual que en la obra real.</li>
    <li><b>Marco de la puerta.</b> Pegue los 2 postes y el dintel sobre la plantilla, a escuadra, y colóquelo en el paso 5 sobre los anclajes #6 y #14. Después van los amarres K1 y K2 y las vigas V del techo. Los postes son las piezas más largas (21.5 cm a 1:10): si sus palos chinos no llegan, empalme dos pedazos con pega loca y un palito de refuerzo por detrás.</li>
    <li><b>Cubierta (opcional).</b> Corte los triángulos en papel mantequilla con la pestaña de 5 mm y péguelos por fuera. El vano de la puerta queda abierto.</li>
  </ol>
  <div class="note"><h3>Con pega loca</h3><p>Una gota en el nodo y una pizca de bicarbonato encima: endurece al instante y rellena el hueco entre palitos. Use pinzas, trabaje ventilado y proteja la mesa. Si un palito queda corto o largo, no lo fuerce: significa que un nodo anterior quedó corrido, y conviene corregirlo antes de seguir.</p></div>
</section>

<footer>Plano de taller del domo real (cortes, nodos, puerta, plataforma, armado): <a href="https://claude.ai/artifact/79tfRK3Jq2uPU6B5nhH5p8">plano de taller</a> (en el repositorio: <span class="mono">domo-3v-cucuchica.html</span>).<br>Generado por <span class="mono">maqueta/maqueta.py</span> desde <span class="mono">dome_model.py</span>, <span class="mono">dome_door.py</span> y <span class="mono">dome_platform.py</span>. Vista 3D con three.js r128.</footer>
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
  $('cutsum').innerHTML='<b>'+pieces.length+' palitos cortados</b> ('+fmt(total/1000,2)+' m en total). Con palos de '+p.L+' mm aprovechables salen de <b>'+sticks.length+' palos chinos</b>'+(tooLong?(' <span style="color:var(--warn)">· '+tooLong+' piezas no caben en un solo palo: use una escala más chica o palos más largos</span>'):'')+'. Compre un paquete de 150 para tener repuesto.';
  sizes(p);parts(p);
  if(window.__setModel)window.__setModel(p);
}
function sizes(p){var R=MQ.real,N=p.N;
  $('sizes').innerHTML=[['Diámetro',R.diam*1000/N,'mm'],['Alto del domo',(R.apex+R.freeboard)*1000/N,'mm sobre la base'],['Vano de la puerta',Math.floor(R.clear_w*1000/N)+'×'+Math.floor(R.clear_h*1000/N),'mm'],['Largo total con escalones',(R.extent_u+3.125)*1000/N,'mm']]
  .map(function(s){return '<div class="stat"><div class="v">'+(typeof s[1]==='number'?fmt(s[1],0):s[1])+'<span class="u">'+s[2]+'</span></div><div class="l">'+s[0]+' a escala 1:'+N+'</div></div>';}).join('');
  var sc=[[10,'Recomendada: cada barra sale de un palo; cabe en una mesa'],[15,'Más chica; el palito se ve 2.3 veces más grueso que el tubo'],[20,'Muy chica; los nodos quedan apretados']];
  $('scaletab').innerHTML=sc.map(function(r){var n=r[0];return '<tr'+(n===p.N?' style="font-weight:700"':'')+'><td>1:'+n+'</td><td class="num">'+fmt(6000/n,0)+' mm</td><td class="num">'+fmt(1255.9/n,1)+' mm</td><td class="num">'+fmt(5*n/10,1)+' cm</td><td>'+r[1]+'</td></tr>';}).join('');}
function parts(p){var N=p.N,pl=MQ.plat,lv=pl.levels,d=p.d,plate=3;
  function mm(x){return fmt(x*1000/N,1)+' mm';}
  var rows=[
    ['Terreno (base)','—','tablero de '+fmt(9000/N/10,0)+' × '+fmt(9000/N/10,0)+' cm o más','cartón piedra, anime o MDF'],
    ['Pilotes (23)','25 × 25 cm, piso a '+fmt(MQ.real.freeboard*100,0)+' cm del suelo',mm(pl.ped)+' × '+mm(pl.ped)+', alto '+fmt(MQ.real.freeboard*1000/N-plate,1)+' mm (con placa de 3 mm)','listón cuadrado de madera o anime'],
    ['Viga de anillo (canto)','25 × 30 cm, 15 tramos, '+fmt(MQ.real.ring_len,2)+' m','tira de '+mm(pl.ringH)+' de alto, '+fmt(MQ.real.ring_len*1000/N,0)+' mm de largo','cartulina gris pegada al borde de la placa'],
    ['Placa del piso + descanso','entablado de 1"','placa de 3 mm cortada con la plantilla','cartón gris, MDF 3 mm o anime'],
    ['Escalones (2)','contrahuella 16.7 cm, huella 28 cm, ancho 1.20 m',mm(1.2)+' × '+mm(0.28)+', altos '+mm(0.1667*2)+' y '+mm(0.1667),'bloques de anime o madera'],
    ['Barras del domo','tubo redondo 32 mm',fmt(32/N,1)+' mm de grosor','palo chino ('+d+' mm) o brocheta de 3 mm para el grosor exacto'],
    ['Marco de la puerta','tubo cuadrado 50 × 50',fmt(50/N,1)+' mm','palo chino'],
    ['Tacos de los nodos altos (5)','4.86 cm',mm(MQ.real.zig),'rodaja de palito'],
    ['Cubierta','PVC blanco','triángulos con pestaña de 5 mm','papel mantequilla o acetato']];
  $('partstab').innerHTML=rows.map(function(r){return '<tr><td>'+r[0]+'</td><td>'+r[1]+'</td><td class="mono">'+r[2]+'</td><td>'+r[3]+'</td></tr>';}).join('');}
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
  MQ.struts.forEach(function(s){
    var m=s.sq?along(s.a,s.b,function(L){return new THREE.BoxGeometry(0.05,L,0.05);},M.frame):along(s.a,s.b,function(L){return new THREE.CylinderGeometry(0.016,0.016,L,12);},M.steel);
    if(!s.sq)rods.push(m);G.dome.add(m);});
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
    else{camera.position.copy(d.clone().multiplyScalar(8.2).add(side.clone().multiplyScalar(-5.2)).add(new THREE.Vector3(0,4.3,0)));controls.target.set(0,0.8,0);}
    controls.update();render();}
  document.querySelectorAll('.vbtn').forEach(function(b){b.addEventListener('click',function(){view(b.getAttribute('data-view'));});});
  function vis(){G.mem.visible=$('t-mem').checked;G.door.visible=$('t-door').checked;G.plat.visible=$('t-plat').checked;
    G.people.visible=$('t-people').checked;var und=$('t-under').checked;G.under.visible=und;M.ground.opacity=und?0.35:1;M.ground.depthWrite=!und;
    var model=$('t-model').checked;G.hubs.visible=!model;var p=params();var f=model?(p.d*p.N/1000/2)/0.016:1;
    rods.forEach(function(r){r.scale.x=f;r.scale.z=f;r.material=model?M.stick:M.steel;});render();}
  ['t-mem','t-door','t-plat','t-people','t-under','t-model'].forEach(function(id){$(id).addEventListener('change',vis);});
  window.__setModel=function(){vis();};
  function resize(){var w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}
  function render(){renderer.render(scene,camera);}
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


def plan_content(PL, D, N):
    """Planta de la maqueta en mm, eje de la puerta hacia arriba (x = v, y = -u)."""
    def P(u, v): return (v*1000/N, -u*1000/N)
    o = []
    for p in PL.piles:
        x, y = P(p["u"], p["v"]); h = plat.PED*1000/N/2
        o.append(f'<rect x="{f(x-h,2)}" y="{f(y-h,2)}" width="{f(2*h,2)}" height="{f(2*h,2)}" class="pile"/>')
        o.append(f'<text x="{f(x,2)}" y="{f(y+1.2,2)}" class="pid">{p["id"]}</text>')
    o.append('<polygon points="' + " ".join(f"{f(P(u, v)[0], 2)},{f(P(u, v)[1], 2)}" for u, v in PL.outer) + '" class="plate"/>')
    o.append('<polygon points="' + " ".join(f"{f(P(u, v)[0], 2)},{f(P(u, v)[1], 2)}" for u, v in PL.inner) + '" class="inner"/>')
    for k in range(-3, 4):
        for axis in (0, 1):
            if axis == 0:
                x, y = P(0, k); o.append(f'<line x1="{f(x,2)}" y1="{f(y-1.5,2)}" x2="{f(x,2)}" y2="{f(y+1.5,2)}" class="tick"/>')
            else:
                x, y = P(k, 0); o.append(f'<line x1="{f(x-1.5,2)}" y1="{f(y,2)}" x2="{f(x+1.5,2)}" y2="{f(y,2)}" class="tick"/>')
    x0, y0 = P(0, -3.2); x1, y1 = P(0, 3.2); o.append(f'<line x1="{f(x0,2)}" y1="{f(y0,2)}" x2="{f(x1,2)}" y2="{f(y1,2)}" class="axis"/>')
    x0, y0 = P(-3.2, 0); x1, y1 = P(3.2, 0); o.append(f'<line x1="{f(x0,2)}" y1="{f(y0,2)}" x2="{f(x1,2)}" y2="{f(y1,2)}" class="axis"/>')
    o.append('<circle cx="0" cy="0" r="2" class="center"/><text x="3" y="-3" class="lbl">centro</text>')
    for r, (u, v) in zip(PL.rows, PL.ring):
        x, y = P(u, v)
        high = r["dz"] > 1e-6
        o.append(f'<circle cx="{f(x,2)}" cy="{f(y,2)}" r="2.5" class="{"anc-h" if high else "anc"}"/>')
        nx, ny = x*1.075, y*1.075
        o.append(f'<text x="{f(nx,2)}" y="{f(ny+1.5,2)}" class="nodel">#{r["node"]}{" +4.9" if high else ""}</text>')
    nodes = [r["node"] for r in PL.rows]
    (ua, va), (ub, vb) = PL.ring[nodes.index(D.door["a"])], PL.ring[nodes.index(D.door["b"])]
    xa, ya = P(ua, va); xb, yb = P(ub, vb)
    o.append(f'<line x1="{f(xa,2)}" y1="{f(ya,2)}" x2="{f(xb,2)}" y2="{f(yb,2)}" class="doorl"/>')
    o.append(f'<text x="0" y="{f(ya+9,2)}" class="doort">PUERTA (postes en #{D.door["a"]} y #{D.door["b"]})</text>')
    x, y = P(-1.6, 0)
    o.append(f'<text x="{f(x,2)}" y="{f(y,2)}" class="lbl" text-anchor="middle">u ↑ eje de la puerta</text>')
    return "".join(o)


def page(inner, landscape=True):
    return f'<section class="page">{inner}</section>'


def scale_bar(x, y, L=100):
    t = "".join(f'<line x1="{x+i*10}" y1="{y}" x2="{x+i*10}" y2="{y + (4 if i % 5 == 0 else 2.5)}" class="tb"/>' for i in range(int(L/10)+1))
    return (f'<line x1="{x}" y1="{y}" x2="{x+L}" y2="{y}" class="bar"/>{t}'
            f'<text x="{x+L/2}" y="{y-2}" class="bl" text-anchor="middle">{L/10:.0f} cm: mida esta barra</text>')


def build_templates(D, PL, members):
    N = SCALE
    pages = []
    W, H = PAGE_W - 2*MARGIN, PAGE_H - 2*MARGIN
    DRAW_H = H - 10
    OV = 10.0
    step_x, step_y = W - OV, DRAW_H - OV
    ext = max(max(abs(p["u"]), abs(p["v"])) for p in PL.piles if p["kind"] != "descanso") + plat.PED/2 + 0.05
    span = 2*ext*1000/N
    cols = math.ceil((span - OV)/step_x); rows = math.ceil((span - OV)/step_y)
    x0 = -(cols*step_x + OV)/2; y0 = -(rows*step_y + OV)/2
    content = plan_content(PL, D, N)
    groups = cut_groups(members, N, STICK_D)

    # portada
    idx = "".join(f'<rect x="{150 + c*14}" y="{86 + r*11}" width="13" height="10" class="mini"/><text x="{156.5 + c*14}" y="{92.5 + r*11}" class="minil">{chr(65+c)}{r+1}</text>'
                  for r in range(rows) for c in range(cols))
    cover = f"""<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">
<text x="0" y="12" class="h1">Maqueta 1:{N} · domo Cucuchica con puerta y plataforma</text>
<text x="0" y="20" class="p">Plantillas a tamaño real. Palitos de {STICK_D:.0f} mm. Generado desde el modelo verificado (maqueta/maqueta.py).</text>
<text x="0" y="34" class="h2">1. Antes que nada: imprimir al 100% ("tamaño real"), sin "ajustar a la página"</text>
{scale_bar(0, 48)}
<line x1="240" y1="70" x2="240" y2="170" class="bar"/>{"".join(f'<line x1="240" y1="{70+i*10}" x2="{244 if i % 5 == 0 else 242.5}" y2="{70+i*10}" class="tb"/>' for i in range(11))}
<text x="246" y="122" class="bl">10 cm</text>
<text x="0" y="62" class="p">Si alguna barra no mide exactamente 10 cm, revise la opción de escala de la impresora.</text>
<text x="0" y="76" class="h2">2. Contenido</text>
<text x="0" y="84" class="p">· Planta base en {rows*cols} hojas ({chr(64+cols)}1 a {chr(64+cols)}{rows}), mapa a la derecha</text>
<text x="0" y="91" class="p">· Descanso de entrada y escalones</text>
<text x="0" y="98" class="p">· Triángulos P1, P2, V1–V4 (comprobar y cortar cubierta)</text>
<text x="0" y="105" class="p">· Reglas de corte de los palitos ({len(groups)} largos)</text>
<text x="0" y="119" class="h2">3. Unir la planta</text>
<text x="0" y="127" class="p">Recorte cada hoja por su borde fino (arriba e izquierda). Apóyela sobre la franja</text>
<text x="0" y="134" class="p">gris de la hoja vecina haciendo coincidir las cruces, y pegue con cinta.</text>
<text x="150" y="80" class="h2">Mapa de hojas</text>
{idx}
</svg>"""
    pages.append(page(cover))

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
                   f'solape gris de 1 cm a la derecha y abajo · eje de la puerta hacia arriba</div>')
            pages.append(page(svg))

    # descanso y escalones
    L = PL.landing
    s = 1000/N
    lw, ld = (L["v1"]-L["v0"])*s, (L["u1"]-L["u0"])*s
    X0 = 4
    sx0 = X0 + lw + 10
    st = ""
    for k in range(len(PL.steps)):
        xk = sx0 + k*(plat.STEP_RUN*s + 10)
        st += (f'<rect x="{xk}" y="30" width="{plat.STEP_RUN*s}" height="{plat.STEP_W*s}" class="plate"/>'
               f'<text transform="translate({xk + plat.STEP_RUN*s/2 + 1.2},{30 + plat.STEP_W*s/2}) rotate(-90)" class="lbl" text-anchor="middle">'
               f'escalón {k+1}: {plat.STEP_W*s:.0f} × {plat.STEP_RUN*s:.0f} mm, alto {(plat.FREEBOARD - (k+1)*plat.STEP_RISE)*s:.1f} mm</text>')
    st += (f'<text x="{sx0}" y="{30 + plat.STEP_W*s + 8}" class="lbl">el 1 va contra el descanso,</text>'
           f'<text x="{sx0}" y="{30 + plat.STEP_W*s + 13}" class="lbl">el 2 delante del 1;</text>'
           f'<text x="{sx0}" y="{30 + plat.STEP_W*s + 18}" class="lbl">el tercero es el terreno</text>')
    land = f"""<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">
<text x="0" y="10" class="h2">Descanso de entrada y escalones · 1:{N}</text>
<rect x="{X0}" y="30" width="{lw}" height="{ld}" class="plate"/>
<text x="{X0+lw/2}" y="{30+ld/2}" class="lbl" text-anchor="middle">descanso {lw:.0f} × {ld:.0f} mm (placa del piso)</text>
<text x="{X0+lw/2}" y="26" class="lbl" text-anchor="middle">este borde va contra la viga de anillo, entre #{D.door['a']} y #{D.door['b']}</text>
{"".join(f'<rect x="{X0 + lw/2 + sv*s - plat.PED*s/2}" y="{30 + (L["beam_u"]-L["u0"])*s - plat.PED*s/2}" width="{plat.PED*s}" height="{plat.PED*s}" class="pile"/>' for sv in (-plat.LANDING_PILE_V, plat.LANDING_PILE_V))}
{st}
{scale_bar(W-110, H-6)}
</svg>"""
    pages.append(page(land))

    # triangulos
    tri_types = []
    seen = {}
    for t in D.triangles:
        sides = tuple(sorted(round(v_norm(v_sub(D.verts[t[i]], D.verts[t[(i+1) % 3]])), 3) for i in range(3)))
        seen.setdefault(sides, 0); seen[sides] += 1
    new = [tuple(sorted(round(v_norm(v_sub(D.verts[t[i]], D.verts[t[(i+1) % 3]])), 3) for i in range(3))) for t in D.new_triangles]
    k = 0
    for sides, n in sorted(seen.items(), key=lambda kv: (kv[0] in new, -kv[1])):
        if sides in new:
            k += 1; name = f"V{k}"
        else:
            name = "P1" if n > 35 else "P2"
        tri_types.append((name, sides, n))

    def tri_svg(name, sides, n, ox, oy):
        a, b, c = [x*1000/N for x in sides]          # c el mas largo
        # base c horizontal, tercer vertice por ley de cosenos
        x = (a*a - b*b + c*c)/(2*c); y = math.sqrt(max(0.0, a*a - x*x))
        pts = [(0, 0), (c, 0), (x, -y)]
        def off(poly, dd):
            # contorno exterior a dd mm (pestaña): desplazar cada lado hacia afuera
            n_ = len(poly); lines = []
            cx = sum(p[0] for p in poly)/3; cy = sum(p[1] for p in poly)/3
            for i in range(n_):
                (x1, y1), (x2, y2) = poly[i], poly[(i+1) % n_]
                dx, dy = x2-x1, y2-y1; L = math.hypot(dx, dy); nx, ny = dy/L, -dx/L
                if (x1+nx-cx)*nx + (y1+ny-cy)*ny < 0: nx, ny = -nx, -ny
                lines.append(((x1+nx*dd, y1+ny*dd), (dx, dy)))
            outp = []
            for i in range(n_):
                (p_, r_), (q_, s_) = lines[i-1], lines[i]
                den = r_[0]*s_[1] - r_[1]*s_[0]
                t_ = ((q_[0]-p_[0])*s_[1] - (q_[1]-p_[1])*s_[0])/den
                outp.append((p_[0]+t_*r_[0], p_[1]+t_*r_[1]))
            return outp
        tab = off(pts, 5.0)
        g = f'<g transform="translate({f(ox,2)},{f(oy,2)})">'
        g += '<polygon points="' + " ".join(f"{f(px,2)},{f(py,2)}" for px, py in tab) + '" class="tab"/>'
        g += '<polygon points="' + " ".join(f"{f(px,2)},{f(py,2)}" for px, py in pts) + '" class="tri"/>'
        for px, py in pts:
            g += f'<circle cx="{f(px,2)}" cy="{f(py,2)}" r="1.4" class="anc"/>'
        g += f'<text x="{f(c/2,2)}" y="5.5" class="lbl" text-anchor="middle">{c:.1f}</text>'
        g += f'<text x="{f(x/2-3,2)}" y="{f(-y/2,2)}" class="lbl" text-anchor="end">{a:.1f}</text>'
        g += f'<text x="{f((x+c)/2+3,2)}" y="{f(-y/2,2)}" class="lbl">{b:.1f}</text>'
        g += f'<text x="{f(x,2)}" y="{f(-y/2+2,2)}" class="h2" text-anchor="middle">{name} ×{n}</text></g>'
        return g, c, y

    head = (f'<text x="0" y="10" class="h2">Triángulos a escala 1:{N} (centro de nodo a centro de nodo, mm)</text>'
            f'<text x="0" y="17" class="p">Línea negra: triángulo para comprobar. Línea gris: pestaña de 5 mm para cortar la cubierta en papel mantequilla.</text>')
    tri_pages, cur = [], ""
    cursor_x, cursor_y, rowh = 8, 30, 0
    for name, sides, n in tri_types:
        _, w, h = tri_svg(name, sides, n, 0, 0)
        if cursor_x > 8 and cursor_x + w + 8 > W:
            cursor_x = 8; cursor_y += rowh + 16; rowh = 0
        if cursor_y + h + 8 > H - 10 and cur:
            tri_pages.append(cur); cur = ""; cursor_x, cursor_y, rowh = 8, 30, 0
        g, _, _ = tri_svg(name, sides, n, cursor_x, cursor_y + h)
        cur += g
        cursor_x += w + 16; rowh = max(rowh, h)
    if cur:
        tri_pages.append(cur)
    for tp in tri_pages:
        pages.append(page(f'<svg viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">{head}{tp}{scale_bar(W-110, H-6)}</svg>'))

    # reglas de corte
    names = {"A": "barra A", "B": "barra B", "C": "barra C", "P": "poste marco", "D": "dintel", "V": "viga techo", "K1": "amarre bajo", "K2": "amarre alto"}
    rl = f'<text x="0" y="10" class="h2">Reglas de corte · escala 1:{N} · palitos de {STICK_D:.0f} mm</text>'
    rl += '<text x="0" y="17" class="p">Apoye el palito sobre la barra, con la punta en el tope izquierdo, y marque en el tope derecho.</text>'
    y = 28
    colors = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
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

    css = f"""@page {{ size: {PAGE_W}mm {PAGE_H}mm; margin: 0 }}
*{{box-sizing:border-box}} html,body{{margin:0; padding:0; background:#fff}}
body{{font-family:"DejaVu Sans","Helvetica","Arial",sans-serif; color:#111}}
.page{{width:{PAGE_W}mm; height:{PAGE_H}mm; padding:{MARGIN}mm; page-break-after:always; break-after:page; overflow:hidden; position:relative}}
.page:last-child{{page-break-after:auto; break-after:auto}}
svg{{display:block}}
.foot{{font-size:3.2mm; color:#333; margin-top:2mm}}
.h1{{font-size:7px; font-weight:700}} .h2{{font-size:4.6px; font-weight:700}} .p{{font-size:3.6px}} .lbl{{font-size:3px; fill:#333}}
.bl{{font-size:3.2px; fill:#111}} .bar{{stroke:#111; stroke-width:.5}} .tb{{stroke:#111; stroke-width:.35}}
.pile{{fill:#d9d9d4; stroke:#777; stroke-width:.3}} .pid{{font-size:2.6px; text-anchor:middle; fill:#222}}
.plate{{fill:none; stroke:#111; stroke-width:.5}} .inner{{fill:none; stroke:#999; stroke-width:.3}}
.axis{{stroke:#bbb; stroke-width:.25}} .tick{{stroke:#999; stroke-width:.3}} .center{{fill:#111}}
.anc{{fill:#fff; stroke:#111; stroke-width:.4}} .anc-h{{fill:#2a78d6; stroke:#111; stroke-width:.4}}
.nodel{{font-size:3px; text-anchor:middle; fill:#111; font-weight:700}}
.doorl{{stroke:#111; stroke-width:1.6}} .doort{{font-size:3.4px; text-anchor:middle; font-weight:700}}
.cross{{stroke:#111; stroke-width:.3; fill:none}} .edge{{fill:none; stroke:#666; stroke-width:.3}} .ov{{fill:#000; fill-opacity:.07}}
.mini{{fill:#f1f1ee; stroke:#777; stroke-width:.3}} .minil{{font-size:3.2px; text-anchor:middle}}
.tri{{fill:none; stroke:#111; stroke-width:.4}} .tab{{fill:none; stroke:#aaa; stroke-width:.3}}
.stop{{stroke:#111; stroke-width:.5}} .rl{{font-size:3.4px}}
"""
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Plantillas maqueta 1:{N}</title><style>{css}</style></head>
<body>{''.join(pages)}</body></html>""", len(pages), rows*cols


def main():
    D, PL, members, data = collect()
    with open(os.path.join(HERE, "maqueta.html"), "w", encoding="utf-8") as fh:
        fh.write(build_page(D, PL, members, data))
    tpl, npages, ntiles = build_templates(D, PL, members)
    with open(os.path.join(HERE, "maqueta_plantillas.html"), "w", encoding="utf-8") as fh:
        fh.write(tpl)
    groups = cut_groups(members, SCALE, STICK_D)
    print(f"Escrito: maqueta.html y maqueta_plantillas.html ({npages} paginas, planta en {ntiles} hojas)")
    print(f"Cortes a 1:{SCALE} con palitos de {STICK_D:.0f} mm:")
    for (code, L), n in groups:
        print(f"   {code:>2} x{n:<3} cortar a {L:6.1f} mm")


if __name__ == "__main__":
    main()
