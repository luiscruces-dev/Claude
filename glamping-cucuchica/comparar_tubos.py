"""
Compara el tubo de las barras del domo: el redondo 32x2 del diseno (1 1/4")
contra otros tubos estructurales que se consiguen: redondo de 1 1/4" y de 2"
con pared de 1.8 mm, y cuadrado de 1" x 1" (25.4 mm) de 0.9 a 2.0 mm.

Corre: `python3 comparar_tubos.py`

Para cada tubo se vuelve a resolver el domo con puerta como armadura espacial
con los mismos 39 casos de carga de dome_door.py (peso propio, 100 kg en el
apice, 100 kg colgando del dintel y viento de 100 km/h en 12 direcciones con
la puerta abierta y cerrada). Se revisa:
  - compresion: la barra mas exigida contra su capacidad AISC 360 (E3);
  - flexion: 100 kg parados a mitad de una barra A (el caso del montaje);
  - pandeo local de la pared (AISC 360, tabla B4.1);
  - peso de las barras.
Se usa el mismo acero conservador que el resto del proyecto (Fy 228 MPa). El
marco de la puerta (50x50x2) no cambia.
"""

import math

import dome_door as door

G = 9.81
FY = 228e6
E = 200e9
KEY = "tubo32x2"        # la seccion que usan todas las barras redondas del domo


def round_tube(d_mm, t_mm):
    d, t = d_mm/1000, t_mm/1000
    A = math.pi/4*(d**2 - (d - 2*t)**2)
    I = math.pi/64*(d**4 - (d - 2*t)**4)
    return {"A": A, "I": I, "c": d/2, "lam": d/t, "lam_r": 0.11*E/FY, "lam_p": 0.07*E/FY}


def square_tube(b_mm, t_mm):
    b, t = b_mm/1000, t_mm/1000
    A = b**2 - (b - 2*t)**2
    I = (b**4 - (b - 2*t)**4)/12
    return {"A": A, "I": I, "c": b/2, "lam": (b - 3*t)/t, "lam_r": 1.40*math.sqrt(E/FY), "lam_p": 1.12*math.sqrt(E/FY)}


CANDIDATES = [
    ("redondo 32×2 (diseño, 1¼\")", 2.0, round_tube(32.0, 2.0)),
    ("redondo 1¼\" × 1.8 mm", 1.8, round_tube(31.75, 1.8)),
    ("redondo 2\" × 1.8 mm", 1.8, round_tube(50.8, 1.8)),
    ("cuadrado 1×1 × 0.9 mm", 0.9, square_tube(25.4, 0.9)),
    ("cuadrado 1×1 × 1.1 mm", 1.1, square_tube(25.4, 1.1)),
    ("cuadrado 1×1 × 1.5 mm", 1.5, square_tube(25.4, 1.5)),
    ("cuadrado 1×1 × 2.0 mm", 2.0, square_tube(25.4, 2.0)),
]


def evaluate(sec):
    """Resuelve el domo con esta seccion en todas las barras redondas."""
    sec = dict(sec)
    sec["r"] = math.sqrt(sec["I"]/sec["A"]); sec["S"] = sec["I"]/sec["c"]; sec["kg_m"] = sec["A"]*7850
    saved = dict(door.SECTIONS[KEY])
    door.SECTIONS[KEY].clear(); door.SECTIONS[KEY].update(sec)
    try:
        D = door.build_dome_with_door()
        results, _ = door.run_structure(D, verbose=False)
        env, _, dmax = door.envelope(D, results)
        worst = None
        for e in D.edges:
            if door.MEMBER_INFO[D.edge_label[e]][0] != KEY:
                continue
            cap, sl = door.aisc_phiPn(sec, D.edge_len[e], Fy=FY, E=E)
            ut = env[e]["comp"]/cap
            if worst is None or ut > worst["ut"]:
                worst = {"ut": ut, "edge": e, "label": D.edge_label[e], "comp": env[e]["comp"], "cap": cap, "kl_r": sl}
        L_A = max(D.edge_len[e] for e in D.edges if D.edge_label[e] == "A")
        cap_A, sl_A = door.aisc_phiPn(sec, L_A, Fy=FY, E=E)
        M = 100*G*L_A/4                                    # 100 kg a media barra, apoyos simples
        steel_m = sum(D.edge_len[e] for e in D.edges if door.MEMBER_INFO[D.edge_label[e]][0] == KEY)
    finally:
        door.SECTIONS[KEY].clear(); door.SECTIONS[KEY].update(saved)
    return {"A_mm2": sec["A"]*1e6, "r_mm": sec["r"]*1000, "kg_m": sec["kg_m"], "kg": sec["kg_m"]*steel_m,
            "cap_A_kgf": cap_A/G, "kl_r_A": sl_A, "worst": worst, "dmax_mm": dmax*1000,
            "sigma_person": M/sec["S"]/1e6,
            "wall_ok": sec["lam"] <= sec["lam_p"], "lam": sec["lam"], "lam_p": sec["lam_p"]}


def compare():
    return [dict(evaluate(sec), name=name, t=t) for name, t, sec in CANDIDATES]


def main():
    rows = compare()
    ref = rows[0]
    print("Barras del domo con puerta: redondo 32x2 del diseno contra otros tubos estructurales")
    print(f"Acero Fy {FY/1e6:.0f} MPa (conservador), 39 casos de carga de dome_door.py\n")
    print(f"{'tubo':28s} {'kg/m':>5s} {'kg barras':>9s} {'KL/r A':>6s} {'cap. A':>8s} {'mas cargada':>12s} {'uso':>5s} "
          f"{'100 kg a media barra':>21s} {'pared':>7s}")
    for r in rows:
        w = r["worst"]
        person = f"{r['sigma_person']:.0f} MPa ({r['sigma_person']/(FY/1e6)*100:.0f}% Fy)"
        print(f"{r['name']:28s} {r['kg_m']:5.2f} {r['kg']:9.0f} {r['kl_r_A']:6.0f} {r['cap_A_kgf']:6.0f} kgf "
              f"{w['comp']/G:7.0f} kgf {w['ut']*100:4.0f}% {person:>21s} {'ok' if r['wall_ok'] else 'delgada':>7s}")
    print("\nLectura:")
    for r in rows[1:]:
        cap = r["cap_A_kgf"]/ref["cap_A_kgf"]*100
        print(f"  {r['name']}: {cap:.0f}% de la capacidad a compresion del redondo, barra mas cargada al "
              f"{r['worst']['ut']*100:.0f}% de su capacidad; una persona a media barra la lleva a "
              f"{r['sigma_person']/(FY/1e6)*100:.0f}% de la fluencia"
              f"{' (queda doblada)' if r['sigma_person'] > FY/1e6 else ' (en el limite)'}; "
              f"desplazamiento maximo {r['dmax_mm']:.2f} mm.")


if __name__ == "__main__":
    main()
