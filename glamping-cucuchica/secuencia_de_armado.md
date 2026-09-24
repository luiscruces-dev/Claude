# Secuencia de armado paso a paso — domo 3V Cucuchica

Generado por `dome_build_sequence.py` a partir de la geometria de `dome_model.py`. Orden: de la base hacia el apice, anillo por anillo, para que cada pieza nueva siempre se apoye en estructura ya fija.

**7 anillos · 120 barras · 46 nodos**


## Paso 0 — Fundación (15 nodos de anclaje)

Los 15 nodos se fijan por topografia/anclaje, no por soldadura de barras.

| Nodo | Tipo | Altura relativa |
|---|---|---|
| #4 | H4 | +0.0000 m |
| #5 | H5 | +0.0486 m |
| #6 | H4 | +0.0000 m |
| #8 | H4 | +0.0000 m |
| #10 | H5 | +0.0486 m |
| #12 | H4 | +0.0000 m |
| #14 | H4 | +0.0000 m |
| #15 | H5 | +0.0486 m |
| #17 | H4 | +0.0000 m |
| #19 | H4 | +0.0000 m |
| #21 | H5 | +0.0486 m |
| #23 | H4 | +0.0000 m |
| #43 | H4 | +0.0000 m |
| #44 | H4 | +0.0000 m |
| #45 | H5 | +0.0486 m |

**Barras del anillo base a soldar en este paso:**

| De | A | Tipo | Longitud |
|---|---|---|---|
| #4 | #5 | A | 125.59 cm |
| #4 | #23 | B | 122.89 cm |
| #5 | #6 | A | 125.59 cm |
| #6 | #14 | B | 122.89 cm |
| #8 | #10 | A | 125.59 cm |
| #8 | #43 | B | 122.89 cm |
| #10 | #12 | A | 125.59 cm |
| #12 | #17 | B | 122.89 cm |
| #14 | #15 | A | 125.59 cm |
| #15 | #17 | A | 125.59 cm |
| #19 | #21 | A | 125.59 cm |
| #19 | #44 | B | 122.89 cm |
| #21 | #23 | A | 125.59 cm |
| #43 | #45 | A | 125.59 cm |
| #44 | #45 | A | 125.59 cm |

## Paso 1 — Anillo a 1.362 m de altura (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #4 (H4) | #0 (H3) | C | 106.16 cm | 2ª barra que fija #0 (nuevo) |
| 2 | #23 (H4) | #0 (H3) | C | 106.16 cm | 2ª barra que fija #0 (nuevo) |
| 3 | #6 (H4) | #3 (H3) | C | 106.16 cm | 2ª barra que fija #3 (nuevo) |
| 4 | #14 (H4) | #3 (H3) | C | 106.16 cm | 2ª barra que fija #3 (nuevo) |
| 5 | #8 (H4) | #7 (H3) | C | 106.16 cm | 2ª barra que fija #7 (nuevo) |
| 6 | #43 (H4) | #7 (H3) | C | 106.16 cm | 2ª barra que fija #7 (nuevo) |
| 7 | #12 (H4) | #13 (H3) | C | 106.16 cm | 2ª barra que fija #13 (nuevo) |
| 8 | #17 (H4) | #13 (H3) | C | 106.16 cm | 2ª barra que fija #13 (nuevo) |
| 9 | #19 (H4) | #20 (H3) | C | 106.16 cm | 2ª barra que fija #20 (nuevo) |
| 10 | #44 (H4) | #20 (H3) | C | 106.16 cm | 2ª barra que fija #20 (nuevo) |

## Paso 2 — Anillo a 1.568 m de altura (10 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #0 (H3) | #1 (H1) | C | 106.16 cm | 3ª barra que fija #1 (nuevo) |
| 2 | #0 (H3) | #24 (H1) | C | 106.16 cm | 3ª barra que fija #24 (nuevo) |
| 3 | #1 (H1) | #2 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 4 | #4 (H4) | #1 (H1) | B | 122.89 cm | 3ª barra que fija #1 (nuevo) |
| 5 | #5 (H5) | #1 (H1) | A | 125.59 cm | 3ª barra que fija #1 (nuevo) |
| 6 | #3 (H3) | #2 (H1) | C | 106.16 cm | 3ª barra que fija #2 (nuevo) |
| 7 | #5 (H5) | #2 (H1) | A | 125.59 cm | 3ª barra que fija #2 (nuevo) |
| 8 | #6 (H4) | #2 (H1) | B | 122.89 cm | 3ª barra que fija #2 (nuevo) |
| 9 | #3 (H3) | #16 (H1) | C | 106.16 cm | 3ª barra que fija #16 (nuevo) |
| 10 | #7 (H3) | #9 (H1) | C | 106.16 cm | 3ª barra que fija #9 (nuevo) |
| 11 | #7 (H3) | #42 (H1) | C | 106.16 cm | 3ª barra que fija #42 (nuevo) |
| 12 | #8 (H4) | #9 (H1) | B | 122.89 cm | 3ª barra que fija #9 (nuevo) |
| 13 | #10 (H5) | #9 (H1) | A | 125.59 cm | 3ª barra que fija #9 (nuevo) |
| 14 | #9 (H1) | #11 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 15 | #10 (H5) | #11 (H1) | A | 125.59 cm | 3ª barra que fija #11 (nuevo) |
| 16 | #12 (H4) | #11 (H1) | B | 122.89 cm | 3ª barra que fija #11 (nuevo) |
| 17 | #13 (H3) | #11 (H1) | C | 106.16 cm | 3ª barra que fija #11 (nuevo) |
| 18 | #13 (H3) | #18 (H1) | C | 106.16 cm | 3ª barra que fija #18 (nuevo) |
| 19 | #14 (H4) | #16 (H1) | B | 122.89 cm | 3ª barra que fija #16 (nuevo) |
| 20 | #15 (H5) | #16 (H1) | A | 125.59 cm | 3ª barra que fija #16 (nuevo) |
| 21 | #15 (H5) | #18 (H1) | A | 125.59 cm | 3ª barra que fija #18 (nuevo) |
| 22 | #16 (H1) | #18 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 23 | #17 (H4) | #18 (H1) | B | 122.89 cm | 3ª barra que fija #18 (nuevo) |
| 24 | #19 (H4) | #22 (H1) | B | 122.89 cm | 3ª barra que fija #22 (nuevo) |
| 25 | #20 (H3) | #22 (H1) | C | 106.16 cm | 3ª barra que fija #22 (nuevo) |
| 26 | #20 (H3) | #41 (H1) | C | 106.16 cm | 3ª barra que fija #41 (nuevo) |
| 27 | #21 (H5) | #22 (H1) | A | 125.59 cm | 3ª barra que fija #22 (nuevo) |
| 28 | #21 (H5) | #24 (H1) | A | 125.59 cm | 3ª barra que fija #24 (nuevo) |
| 29 | #22 (H1) | #24 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 30 | #23 (H4) | #24 (H1) | B | 122.89 cm | 3ª barra que fija #24 (nuevo) |
| 31 | #41 (H1) | #42 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 32 | #44 (H4) | #41 (H1) | B | 122.89 cm | 3ª barra que fija #41 (nuevo) |
| 33 | #45 (H5) | #41 (H1) | A | 125.59 cm | 3ª barra que fija #41 (nuevo) |
| 34 | #43 (H4) | #42 (H1) | B | 122.89 cm | 3ª barra que fija #42 (nuevo) |
| 35 | #45 (H5) | #42 (H1) | A | 125.59 cm | 3ª barra que fija #42 (nuevo) |

## Paso 3 — Anillo a 2.214 m de altura (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #0 (H3) | #35 (H1) | C | 106.16 cm | 3ª barra que fija #35 (nuevo) |
| 2 | #1 (H1) | #35 (H1) | B | 122.89 cm | 3ª barra que fija #35 (nuevo) |
| 3 | #2 (H1) | #27 (H1) | B | 122.89 cm | 3ª barra que fija #27 (nuevo) |
| 4 | #3 (H3) | #27 (H1) | C | 106.16 cm | 3ª barra que fija #27 (nuevo) |
| 5 | #7 (H3) | #39 (H1) | C | 106.16 cm | 3ª barra que fija #39 (nuevo) |
| 6 | #9 (H1) | #39 (H1) | B | 122.89 cm | 3ª barra que fija #39 (nuevo) |
| 7 | #11 (H1) | #30 (H1) | B | 122.89 cm | 3ª barra que fija #30 (nuevo) |
| 8 | #13 (H3) | #30 (H1) | C | 106.16 cm | 3ª barra que fija #30 (nuevo) |
| 9 | #16 (H1) | #27 (H1) | B | 122.89 cm | 3ª barra que fija #27 (nuevo) |
| 10 | #18 (H1) | #30 (H1) | B | 122.89 cm | 3ª barra que fija #30 (nuevo) |
| 11 | #20 (H3) | #32 (H1) | C | 106.16 cm | 3ª barra que fija #32 (nuevo) |
| 12 | #22 (H1) | #32 (H1) | B | 122.89 cm | 3ª barra que fija #32 (nuevo) |
| 13 | #24 (H1) | #35 (H1) | B | 122.89 cm | 3ª barra que fija #35 (nuevo) |
| 14 | #41 (H1) | #32 (H1) | B | 122.89 cm | 3ª barra que fija #32 (nuevo) |
| 15 | #42 (H1) | #39 (H1) | B | 122.89 cm | 3ª barra que fija #39 (nuevo) |

## Paso 4 — Anillo a 2.420 m de altura (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #1 (H1) | #36 (H2) | A | 125.59 cm | 4ª barra que fija #36 (nuevo) |
| 2 | #2 (H1) | #36 (H2) | A | 125.59 cm | 4ª barra que fija #36 (nuevo) |
| 3 | #9 (H1) | #38 (H2) | A | 125.59 cm | 4ª barra que fija #38 (nuevo) |
| 4 | #11 (H1) | #38 (H2) | A | 125.59 cm | 4ª barra que fija #38 (nuevo) |
| 5 | #16 (H1) | #29 (H2) | A | 125.59 cm | 4ª barra que fija #29 (nuevo) |
| 6 | #18 (H1) | #29 (H2) | A | 125.59 cm | 4ª barra que fija #29 (nuevo) |
| 7 | #22 (H1) | #34 (H2) | A | 125.59 cm | 4ª barra que fija #34 (nuevo) |
| 8 | #24 (H1) | #34 (H2) | A | 125.59 cm | 4ª barra que fija #34 (nuevo) |
| 9 | #27 (H1) | #29 (H2) | A | 125.59 cm | 4ª barra que fija #29 (nuevo) |
| 10 | #27 (H1) | #36 (H2) | A | 125.59 cm | 4ª barra que fija #36 (nuevo) |
| 11 | #30 (H1) | #29 (H2) | A | 125.59 cm | 4ª barra que fija #29 (nuevo) |
| 12 | #30 (H1) | #38 (H2) | A | 125.59 cm | 4ª barra que fija #38 (nuevo) |
| 13 | #32 (H1) | #34 (H2) | A | 125.59 cm | 4ª barra que fija #34 (nuevo) |
| 14 | #32 (H1) | #40 (H2) | A | 125.59 cm | 4ª barra que fija #40 (nuevo) |
| 15 | #35 (H1) | #34 (H2) | A | 125.59 cm | 4ª barra que fija #34 (nuevo) |
| 16 | #35 (H1) | #36 (H2) | A | 125.59 cm | 4ª barra que fija #36 (nuevo) |
| 17 | #39 (H1) | #38 (H2) | A | 125.59 cm | 4ª barra que fija #38 (nuevo) |
| 18 | #39 (H1) | #40 (H2) | A | 125.59 cm | 4ª barra que fija #40 (nuevo) |
| 19 | #41 (H1) | #40 (H2) | A | 125.59 cm | 4ª barra que fija #40 (nuevo) |
| 20 | #42 (H1) | #40 (H2) | A | 125.59 cm | 4ª barra que fija #40 (nuevo) |

## Paso 5 — Anillo a 2.860 m de altura (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #27 (H1) | #26 (H1) | B | 122.89 cm | 3ª barra que fija #26 (nuevo) |
| 2 | #26 (H1) | #28 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 3 | #29 (H2) | #26 (H1) | A | 125.59 cm | 3ª barra que fija #26 (nuevo) |
| 4 | #26 (H1) | #33 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 5 | #36 (H2) | #26 (H1) | A | 125.59 cm | 3ª barra que fija #26 (nuevo) |
| 6 | #29 (H2) | #28 (H1) | A | 125.59 cm | 3ª barra que fija #28 (nuevo) |
| 7 | #30 (H1) | #28 (H1) | B | 122.89 cm | 3ª barra que fija #28 (nuevo) |
| 8 | #28 (H1) | #37 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 9 | #38 (H2) | #28 (H1) | A | 125.59 cm | 3ª barra que fija #28 (nuevo) |
| 10 | #32 (H1) | #31 (H1) | B | 122.89 cm | 3ª barra que fija #31 (nuevo) |
| 11 | #31 (H1) | #33 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 12 | #34 (H2) | #31 (H1) | A | 125.59 cm | 3ª barra que fija #31 (nuevo) |
| 13 | #31 (H1) | #37 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 14 | #40 (H2) | #31 (H1) | A | 125.59 cm | 3ª barra que fija #31 (nuevo) |
| 15 | #34 (H2) | #33 (H1) | A | 125.59 cm | 3ª barra que fija #33 (nuevo) |
| 16 | #35 (H1) | #33 (H1) | B | 122.89 cm | 3ª barra que fija #33 (nuevo) |
| 17 | #36 (H2) | #33 (H1) | A | 125.59 cm | 3ª barra que fija #33 (nuevo) |
| 18 | #38 (H2) | #37 (H1) | A | 125.59 cm | 3ª barra que fija #37 (nuevo) |
| 19 | #39 (H1) | #37 (H1) | B | 122.89 cm | 3ª barra que fija #37 (nuevo) |
| 20 | #40 (H2) | #37 (H1) | A | 125.59 cm | 3ª barra que fija #37 (nuevo) |

## Paso 6 — Anillo a 3.045 m de altura (1 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #26 (H1) | #25 (H3) | C | 106.16 cm | 5ª barra que fija #25 (nuevo) |
| 2 | #28 (H1) | #25 (H3) | C | 106.16 cm | 5ª barra que fija #25 (nuevo) |
| 3 | #31 (H1) | #25 (H3) | C | 106.16 cm | 5ª barra que fija #25 (nuevo) |
| 4 | #33 (H1) | #25 (H3) | C | 106.16 cm | 5ª barra que fija #25 (nuevo) |
| 5 | #37 (H1) | #25 (H3) | C | 106.16 cm | 5ª barra que fija #25 (nuevo) |


## Verificación de cobertura

- Barras totales en el modelo: 120
- Barras instaladas en la secuencia: 120
- Barras sin asignar (deberían ser 0): 0

