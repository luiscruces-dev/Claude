"""
Suite de verificacion del domo geodesico 3V — Cucuchica.

Corre: `python3 dome_verify.py`  (solo necesita dome_model.py al lado, sin
dependencias externas).

Que hace y que NO hace, para que quede claro el alcance:
- SI verifica: consistencia geometrica interna (triangulos validos, aristas
  que coinciden con las longitudes declaradas, angulos que cierran bien,
  simetria de los 5 tipos de nodo, que los totales publicados en el .md no
  se hayan transcrito mal) y un chequeo de pandeo Euler por tipo de barra.
- NO reemplaza un analisis estructural real (FEA / metodo matricial de
  rigidez) ni el chequeo de viento/sismo con datos oficiales de sitio — eso
  sigue siendo trabajo del ingeniero, como ya se documento en el .md.

Cada chequeo imprime PASS o FAIL con el detalle. Si algo falla, el programa
termina con exit code 1 para que se pueda usar en un pipeline de CI si se
quiere.
"""

import math
import sys
from dome_model import build_dome, v_sub, v_norm, v_dot

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)
    return condition


def approx(a, b, tol):
    return abs(a - b) <= tol


def main():
    dome = build_dome()
    print(f"Domo 3V construido: R={dome.R:.4f} m, base={dome.base_diameter_m} m\n")

    print("== 1. Geometria de la esfera completa (Euler) ==")
    verts_full, tris_full, _ = __import__("dome_model").subdivide_icosahedron(3)
    edges_full = {(min(a, b), max(a, b)) for t in tris_full for a, b in
                  [(t[0], t[1]), (t[1], t[2]), (t[2], t[0])]}
    V, E, F = len(verts_full), len(edges_full), len(tris_full)
    check("V - E + F = 2 (formula de Euler, esfera completa)", V - E + F == 2,
          f"V={V} E={E} F={F}")
    check("esfera completa tiene 92 vertices / 180 triangulos / 270 aristas (3V estandar)",
          (V, F, E) == (92, 180, 270), f"(V,F,E)=({V},{F},{E})")

    print("\n== 2. Triangulos del casquete construido (los 75 paneles) ==")
    bad_tri = 0
    angle_sum_bad = 0
    for t in dome.triangles:
        a, b, c = (dome.verts[i] for i in t)
        sa, sb, sc = v_norm(v_sub(b, c)), v_norm(v_sub(a, c)), v_norm(v_sub(a, b))
        sides = sorted([sa, sb, sc])
        if sides[0] + sides[1] <= sides[2] + 1e-9:
            bad_tri += 1
        # ley de cosenos para los 3 angulos internos, deben sumar 180
        def ang(opp, x, y):
            v = (x*x + y*y - opp*opp) / (2*x*y)
            v = max(-1.0, min(1.0, v))
            return math.degrees(math.acos(v))
        A = ang(sa, sb, sc); B = ang(sb, sa, sc); C = ang(sc, sa, sb)
        if not approx(A + B + C, 180.0, 0.05):
            angle_sum_bad += 1
    check("triangulos totales = 75", len(dome.triangles) == 75, f"{len(dome.triangles)}")
    check("los 75 paneles cumplen la desigualdad triangular (ningun panel degenerado)",
          bad_tri == 0, f"{bad_tri} paneles invalidos")
    check("los 3 angulos internos de cada panel suman 180°",
          angle_sum_bad == 0, f"{angle_sum_bad} paneles con suma fuera de tolerancia")

    print("\n== 3. Barras (struts): consistencia de longitud declarada vs. real ==")
    mismatches = 0
    for e in dome.edges:
        real_len = dome.edge_len[e]
        lab = dome.edge_label[e]
        declared = dome.strut_summary[lab]["length_m"]
        if not approx(real_len, declared, 0.001):
            mismatches += 1
    check("las 120 aristas recalculadas coinciden con su clase declarada (±1mm)",
          mismatches == 0, f"{mismatches} discrepancias")
    check("solo existen 3 clases de longitud de barra",
          len(dome.strut_summary) == 3, f"{len(dome.strut_summary)} clases")
    total_struts = sum(v["count"] for v in dome.strut_summary.values())
    check("120 barras en total", total_struts == 120, f"{total_struts}")

    print("\n== 4. Regresion contra los valores publicados en domo-3v-cucuchica.md ==")
    published = {
        "apex_height_m": 2.5225,
        "floor_area_m2": 28.274,
        "membrane_area_m2": 46.24,
        "total_strut_length_m": 143.80,
        "R_m": 3.0452,
    }
    check("altura del apice = 2.5225 m", approx(dome.apex_height_m, published["apex_height_m"], 0.001),
          f"{dome.apex_height_m:.4f} m")
    check("area de piso = 28.274 m2", approx(dome.floor_area_m2, published["floor_area_m2"], 0.001),
          f"{dome.floor_area_m2:.3f} m2")
    check("area de membrana = 46.24 m2", approx(dome.membrane_area_m2, published["membrane_area_m2"], 0.01),
          f"{dome.membrane_area_m2:.2f} m2")
    check("longitud total de tubo = 143.80 m", approx(dome.total_strut_length_m, published["total_strut_length_m"], 0.01),
          f"{dome.total_strut_length_m:.2f} m")
    check("radio de esfera R = 3.0452 m", approx(dome.R, published["R_m"], 0.0001),
          f"{dome.R:.4f} m")

    A = dome.strut_summary["A"]; B = dome.strut_summary["B"]; C = dome.strut_summary["C"]
    check("tipo A = 125.59 cm x50", approx(A["length_m"]*100, 125.59, 0.01) and A["count"] == 50,
          f"{A['length_m']*100:.2f} cm x{A['count']}")
    check("tipo B = 122.89 cm x40", approx(B["length_m"]*100, 122.89, 0.01) and B["count"] == 40,
          f"{B['length_m']*100:.2f} cm x{B['count']}")
    check("tipo C = 106.16 cm x30", approx(C["length_m"]*100, 106.16, 0.01) and C["count"] == 30,
          f"{C['length_m']*100:.2f} cm x{C['count']}")

    print("\n== 5. Nodos (hubs): simetria y clasificacion ==")
    check("46 nodos en total", len(dome.hubs) == 46, f"{len(dome.hubs)}")
    check("exactamente 5 tipos de nodo geometricamente distintos",
          len(dome.hub_types) == 5, f"{len(dome.hub_types)}")
    counts = {t["name"]: t["count"] for t in dome.hub_types}
    total_hub_count = sum(counts.values())
    check("la suma de nodos por tipo da 46", total_hub_count == 46, f"suma={total_hub_count}, {counts}")

    degree_sum = sum(h["degree"] for h in dome.hubs.values())
    check("suma de grados de todos los nodos = 2 x numero de aristas (cada arista cuenta en sus 2 extremos)",
          degree_sum == 2*len(dome.edges), f"suma_grados={degree_sum}, 2*aristas={2*len(dome.edges)}")

    for t in dome.hub_types:
        if t["closed"]:
            s = sum(t["angles"])
            ok = s < 360.0 + 0.01
            check(f"nodo {t['name']} (cerrado, grado {t['degree']}): suma de angulos < 360° (curvatura positiva real)",
                  ok, f"suma={s:.2f}°")

    print("\n== 6. Anillo base (zigzag) ==")
    check("15 nodos en el borde del domo (10 bajos + 5 altos, no 10)",
          len(dome.boundary_verts) == 15, f"{len(dome.boundary_verts)}")
    heights_boundary = sorted(set(round(dome.heights[i] - min(dome.heights[j] for j in dome.boundary_verts), 4)
                                   for i in dome.boundary_verts))
    check("el borde tiene exactamente 2 niveles de altura (el zigzag)",
          len(heights_boundary) == 2, f"niveles relativos={heights_boundary}")
    if len(heights_boundary) == 2:
        delta = round((heights_boundary[1] - heights_boundary[0])*100, 2)
        check("desnivel del zigzag = 4.86 cm", approx(delta, 4.86, 0.02), f"{delta} cm")

    print("\n== 7. Chequeo de pandeo (Euler, apoyo simple K=1) por tipo de barra ==")
    OD, wall = 0.032, 0.002
    ID = OD - 2*wall
    I = math.pi/64 * (OD**4 - ID**4)
    E_steel = 200e9
    for lab in "ABC":
        L = dome.strut_summary[lab]["length_m"]
        Pcr = math.pi**2 * E_steel * I / L**2
        check(f"barra tipo {lab} ({L*100:.2f} cm): carga critica de pandeo > 500 kgf (margen minimo aceptado)",
              Pcr/9.81 > 500, f"Pcr={Pcr:.0f} N ({Pcr/9.81:.0f} kgf)")

    print("\n" + "="*60)
    if FAILURES:
        print(f"RESULTADO: {len(FAILURES)} chequeo(s) FALLARON:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("RESULTADO: todos los chequeos pasaron.")
        print("Esto verifica consistencia geometrica y de datos, NO sustituye")
        print("el analisis estructural (FEA) ni el chequeo de viento/sismo con")
        print("datos oficiales de sitio — ver domo-3v-cucuchica.md secciones 6.2/6.3.")


if __name__ == "__main__":
    main()
