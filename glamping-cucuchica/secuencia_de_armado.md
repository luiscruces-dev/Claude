# Secuencia de armado paso a paso — domo 3V Cucuchica (con puerta)

Generado por `dome_build_sequence.py` a partir de la geometria de `dome_model.py` y `dome_door.py`. Orden: de la base hacia el apice, anillo por anillo, para que cada pieza nueva siempre se apoye en estructura ya fija.

**Puerta** centrada a 36.0° (donde estaba el nodo #3). Postes sobre los anclajes #6 (izquierda, mirando la puerta desde afuera) y #14 (derecha). Los nodos #3 y #27 **no existen** en esta versión. Códigos de pieza: A/B/C barras del domo · P poste del marco (50×50×2) · D dintel (50×50×2) · V viga del techo del vestíbulo · K1 amarre bajo · K2 amarre alto (32×2). Tipos de nodo PA–PE: nodos especiales alrededor de la puerta; la versión "-der" es la imagen espejo de la "-izq".

**8 anillos · 119 barras · 46 nodos**

Todas las alturas se miden **desde el piso** (nivel de los 10 nodos bajos H4), no desde el centro de la esfera.


> ⚠ 6 nodo(s) quedan como **bisagra** en el momento en que aparecen: tienen menos de 3 barras no coplanares hacia estructura ya fija, así que pueden girar alrededor de la línea entre sus apoyos. Necesitan sujeción temporal (puntal, cuerda, un ayudante) hasta que quedan triangulados: cada paso indica si es en ese mismo paso o en el siguiente. Es normal en un armado anillo por anillo, pero hay que preverlo en la logística del día de armado.


> ⚠ No caminar ni pararse sobre las barras: una persona de 100 kg a media barra lleva el tubo de 32×2 mm al límite de fluencia. Armar y cubrir desde andamio o escalera.


## Paso 0 — Fundación (15 nodos de anclaje)

Los 15 nodos se fijan por topografia/anclaje, no por soldadura de barras.

**Replanteo de los anclajes** (origen en el centro del domo; azimut 0° en el primer nodo alto, creciendo en sentido antihorario visto desde arriba; X/Y en metros):

| Nodo | Tipo | Azimut | Radio | X | Y | Altura sobre el piso |
|---|---|---|---|---|---|---|
| #5 | H5 | 0.000° | 2.9911 m | +2.9911 | +0.0000 | +0.0486 m |
| #6 | PA-izq | 24.181° | 3.0000 m | +2.7368 | +1.2289 | +0.0000 m |
| #14 | PA-der | 47.819° | 3.0000 m | +2.0144 | +2.2231 | +0.0000 m |
| #15 | H5 | 72.000° | 2.9911 m | +0.9243 | +2.8447 | +0.0486 m |
| #17 | H4 | 96.181° | 3.0000 m | -0.3230 | +2.9826 | +0.0000 m |
| #12 | H4 | 119.819° | 3.0000 m | -1.4918 | +2.6028 | +0.0000 m |
| #10 | H5 | 144.000° | 2.9911 m | -2.4199 | +1.7581 | +0.0486 m |
| #8 | H4 | 168.181° | 3.0000 m | -2.9364 | +0.6144 | +0.0000 m |
| #43 | H4 | 191.819° | 3.0000 m | -2.9364 | -0.6144 | +0.0000 m |
| #45 | H5 | 216.000° | 2.9911 m | -2.4199 | -1.7581 | +0.0486 m |
| #44 | H4 | 240.181° | 3.0000 m | -1.4918 | -2.6028 | +0.0000 m |
| #19 | H4 | 263.819° | 3.0000 m | -0.3230 | -2.9826 | +0.0000 m |
| #21 | H5 | 288.000° | 2.9911 m | +0.9243 | -2.8447 | +0.0486 m |
| #23 | H4 | 312.181° | 3.0000 m | +2.0144 | -2.2231 | +0.0000 m |
| #4 | H4 | 335.819° | 3.0000 m | +2.7368 | -1.2289 | +0.0000 m |

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

## Paso 1 — Anillo a 0.839 m sobre el piso (4 nodos nuevos)

⚠ Sujetar temporalmente **hasta el paso siguiente** (quedan como bisagra): #0 (H3), #7 (H3), #13 (H3), #20 (H3)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #4 (H4) | #0 (H3) | C | 106.16 cm | 1ª de 2 barras que fijan #0 (nuevo) |
| 2 | #23 (H4) | #0 (H3) | C | 106.16 cm | 2ª de 2 barras que fijan #0 (nuevo) |
| 3 | #8 (H4) | #7 (H3) | C | 106.16 cm | 1ª de 2 barras que fijan #7 (nuevo) |
| 4 | #43 (H4) | #7 (H3) | C | 106.16 cm | 2ª de 2 barras que fijan #7 (nuevo) |
| 5 | #12 (H4) | #13 (H3) | C | 106.16 cm | 1ª de 2 barras que fijan #13 (nuevo) |
| 6 | #17 (H4) | #13 (H3) | C | 106.16 cm | 2ª de 2 barras que fijan #13 (nuevo) |
| 7 | #19 (H4) | #20 (H3) | C | 106.16 cm | 1ª de 2 barras que fijan #20 (nuevo) |
| 8 | #44 (H4) | #20 (H3) | C | 106.16 cm | 2ª de 2 barras que fijan #20 (nuevo) |

## Paso 2 — Anillo a 1.045 m sobre el piso (10 nodos nuevos)

⚠ Sujetar temporalmente **hasta soldar todas las barras de este paso** (aparecen como bisagra y las amarra un vecino del mismo anillo): #2 (PB-izq), #16 (PB-der)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #0 (H3) | #1 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #1 (nuevo) |
| 2 | #0 (H3) | #24 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #24 (nuevo) |
| 3 | #1 (H1) | #2 (PB-izq) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 4 | #4 (H4) | #1 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #1 (nuevo) |
| 5 | #5 (H5) | #1 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #1 (nuevo) |
| 6 | #5 (H5) | #2 (PB-izq) | A | 125.59 cm | 1ª de 2 barras que fijan #2 (nuevo) |
| 7 | #6 (PA-izq) | #2 (PB-izq) | B | 122.89 cm | 2ª de 2 barras que fijan #2 (nuevo) |
| 8 | #7 (H3) | #9 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #9 (nuevo) |
| 9 | #7 (H3) | #42 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #42 (nuevo) |
| 10 | #8 (H4) | #9 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #9 (nuevo) |
| 11 | #10 (H5) | #9 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #9 (nuevo) |
| 12 | #9 (H1) | #11 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 13 | #10 (H5) | #11 (H1) | A | 125.59 cm | 1ª de 3 barras que fijan #11 (nuevo) |
| 14 | #12 (H4) | #11 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #11 (nuevo) |
| 15 | #13 (H3) | #11 (H1) | C | 106.16 cm | 3ª de 3 barras que fijan #11 (nuevo) |
| 16 | #13 (H3) | #18 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #18 (nuevo) |
| 17 | #14 (PA-der) | #16 (PB-der) | B | 122.89 cm | 1ª de 2 barras que fijan #16 (nuevo) |
| 18 | #15 (H5) | #16 (PB-der) | A | 125.59 cm | 2ª de 2 barras que fijan #16 (nuevo) |
| 19 | #15 (H5) | #18 (H1) | A | 125.59 cm | 2ª de 3 barras que fijan #18 (nuevo) |
| 20 | #16 (PB-der) | #18 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 21 | #17 (H4) | #18 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #18 (nuevo) |
| 22 | #19 (H4) | #22 (H1) | B | 122.89 cm | 1ª de 3 barras que fijan #22 (nuevo) |
| 23 | #20 (H3) | #22 (H1) | C | 106.16 cm | 2ª de 3 barras que fijan #22 (nuevo) |
| 24 | #20 (H3) | #41 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #41 (nuevo) |
| 25 | #21 (H5) | #22 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #22 (nuevo) |
| 26 | #21 (H5) | #24 (H1) | A | 125.59 cm | 2ª de 3 barras que fijan #24 (nuevo) |
| 27 | #22 (H1) | #24 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 28 | #23 (H4) | #24 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #24 (nuevo) |
| 29 | #41 (H1) | #42 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 30 | #44 (H4) | #41 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #41 (nuevo) |
| 31 | #45 (H5) | #41 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #41 (nuevo) |
| 32 | #43 (H4) | #42 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #42 (nuevo) |
| 33 | #45 (H5) | #42 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #42 (nuevo) |

## Paso 3 — Anillo a 1.691 m sobre el piso (4 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #0 (H3) | #35 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #35 (nuevo) |
| 2 | #1 (H1) | #35 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #35 (nuevo) |
| 3 | #7 (H3) | #39 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #39 (nuevo) |
| 4 | #9 (H1) | #39 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #39 (nuevo) |
| 5 | #11 (H1) | #30 (H1) | B | 122.89 cm | 1ª de 3 barras que fijan #30 (nuevo) |
| 6 | #13 (H3) | #30 (H1) | C | 106.16 cm | 2ª de 3 barras que fijan #30 (nuevo) |
| 7 | #18 (H1) | #30 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #30 (nuevo) |
| 8 | #20 (H3) | #32 (H1) | C | 106.16 cm | 1ª de 3 barras que fijan #32 (nuevo) |
| 9 | #22 (H1) | #32 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #32 (nuevo) |
| 10 | #24 (H1) | #35 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #35 (nuevo) |
| 11 | #41 (H1) | #32 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #32 (nuevo) |
| 12 | #42 (H1) | #39 (H1) | B | 122.89 cm | 3ª de 3 barras que fijan #39 (nuevo) |

## Paso 4 — Anillo a 1.897 m sobre el piso (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #1 (H1) | #36 (PC-izq) | A | 125.59 cm | 1ª de 3 barras que fijan #36 (nuevo) |
| 2 | #2 (PB-izq) | #36 (PC-izq) | A | 125.59 cm | 2ª de 3 barras que fijan #36 (nuevo) |
| 3 | #9 (H1) | #38 (H2) | A | 125.59 cm | 1ª de 4 barras que fijan #38 (nuevo) |
| 4 | #11 (H1) | #38 (H2) | A | 125.59 cm | 2ª de 4 barras que fijan #38 (nuevo) |
| 5 | #16 (PB-der) | #29 (PC-der) | A | 125.59 cm | 1ª de 3 barras que fijan #29 (nuevo) |
| 6 | #18 (H1) | #29 (PC-der) | A | 125.59 cm | 2ª de 3 barras que fijan #29 (nuevo) |
| 7 | #22 (H1) | #34 (H2) | A | 125.59 cm | 1ª de 4 barras que fijan #34 (nuevo) |
| 8 | #24 (H1) | #34 (H2) | A | 125.59 cm | 2ª de 4 barras que fijan #34 (nuevo) |
| 9 | #30 (H1) | #29 (PC-der) | A | 125.59 cm | 3ª de 3 barras que fijan #29 (nuevo) |
| 10 | #30 (H1) | #38 (H2) | A | 125.59 cm | 3ª de 4 barras que fijan #38 (nuevo) |
| 11 | #32 (H1) | #34 (H2) | A | 125.59 cm | 3ª de 4 barras que fijan #34 (nuevo) |
| 12 | #32 (H1) | #40 (H2) | A | 125.59 cm | 1ª de 4 barras que fijan #40 (nuevo) |
| 13 | #35 (H1) | #34 (H2) | A | 125.59 cm | 4ª de 4 barras que fijan #34 (nuevo) |
| 14 | #35 (H1) | #36 (PC-izq) | A | 125.59 cm | 3ª de 3 barras que fijan #36 (nuevo) |
| 15 | #39 (H1) | #38 (H2) | A | 125.59 cm | 4ª de 4 barras que fijan #38 (nuevo) |
| 16 | #39 (H1) | #40 (H2) | A | 125.59 cm | 2ª de 4 barras que fijan #40 (nuevo) |
| 17 | #41 (H1) | #40 (H2) | A | 125.59 cm | 3ª de 4 barras que fijan #40 (nuevo) |
| 18 | #42 (H1) | #40 (H2) | A | 125.59 cm | 4ª de 4 barras que fijan #40 (nuevo) |

## Paso 5 — Marco de la puerta a 2.100 m sobre el piso (2 nodos nuevos)

El marco (2 postes P + dintel D) se suelda **en taller** como una sola pieza, a escuadra y con el vano libre medido. En obra se presenta sobre los anclajes #6 y #14, se aploma y se amarra al domo con las barras K1 y K2 de este paso. Las vigas V del techo del vestíbulo entran en el paso siguiente.

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #2 (PB-izq) | #46 (PE-izq) | K1 · amarre bajo | 123.68 cm | 1ª de 3 barras que fijan #46 (nuevo) |
| 2 | #6 (PA-izq) | #46 (PE-izq) | P · poste del marco | 210.00 cm | 2ª de 3 barras que fijan #46 (nuevo) |
| 3 | #14 (PA-der) | #47 (PE-der) | P · poste del marco | 210.00 cm | 1ª de 3 barras que fijan #47 (nuevo) |
| 4 | #16 (PB-der) | #47 (PE-der) | K1 · amarre bajo | 123.68 cm | 2ª de 3 barras que fijan #47 (nuevo) |
| 5 | #29 (PC-der) | #47 (PE-der) | K2 · amarre alto | 152.97 cm | 3ª de 3 barras que fijan #47 (nuevo) |
| 6 | #36 (PC-izq) | #46 (PE-izq) | K2 · amarre alto | 152.97 cm | 3ª de 3 barras que fijan #46 (nuevo) |
| 7 | #46 (PE-izq) | #47 (PE-der) | D · dintel del marco | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |

## Paso 6 — Anillo a 2.337 m sobre el piso (5 nodos nuevos)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #26 (PD) | #28 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 2 | #29 (PC-der) | #26 (PD) | A | 125.59 cm | 1ª de 4 barras que fijan #26 (nuevo) |
| 3 | #26 (PD) | #33 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 4 | #36 (PC-izq) | #26 (PD) | A | 125.59 cm | 2ª de 4 barras que fijan #26 (nuevo) |
| 5 | #46 (PE-izq) | #26 (PD) | V · viga del techo | 200.25 cm | 3ª de 4 barras que fijan #26 (nuevo) |
| 6 | #47 (PE-der) | #26 (PD) | V · viga del techo | 200.25 cm | 4ª de 4 barras que fijan #26 (nuevo) |
| 7 | #29 (PC-der) | #28 (H1) | A | 125.59 cm | 1ª de 3 barras que fijan #28 (nuevo) |
| 8 | #30 (H1) | #28 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #28 (nuevo) |
| 9 | #28 (H1) | #37 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 10 | #38 (H2) | #28 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #28 (nuevo) |
| 11 | #32 (H1) | #31 (H1) | B | 122.89 cm | 1ª de 3 barras que fijan #31 (nuevo) |
| 12 | #31 (H1) | #33 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 13 | #34 (H2) | #31 (H1) | A | 125.59 cm | 2ª de 3 barras que fijan #31 (nuevo) |
| 14 | #31 (H1) | #37 (H1) | B | 122.89 cm | arriostre entre 2 nodos nuevos de este mismo anillo |
| 15 | #40 (H2) | #31 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #31 (nuevo) |
| 16 | #34 (H2) | #33 (H1) | A | 125.59 cm | 1ª de 3 barras que fijan #33 (nuevo) |
| 17 | #35 (H1) | #33 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #33 (nuevo) |
| 18 | #36 (PC-izq) | #33 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #33 (nuevo) |
| 19 | #38 (H2) | #37 (H1) | A | 125.59 cm | 1ª de 3 barras que fijan #37 (nuevo) |
| 20 | #39 (H1) | #37 (H1) | B | 122.89 cm | 2ª de 3 barras que fijan #37 (nuevo) |
| 21 | #40 (H2) | #37 (H1) | A | 125.59 cm | 3ª de 3 barras que fijan #37 (nuevo) |

## Paso 7 — Anillo a 2.522 m sobre el piso (1 nodo nuevo)

| Barra | De | A | Tipo | Longitud | Fijación |
|---|---|---|---|---|---|
| 1 | #26 (PD) | #25 (H3) | C | 106.16 cm | 1ª de 5 barras que fijan #25 (nuevo) |
| 2 | #28 (H1) | #25 (H3) | C | 106.16 cm | 2ª de 5 barras que fijan #25 (nuevo) |
| 3 | #31 (H1) | #25 (H3) | C | 106.16 cm | 3ª de 5 barras que fijan #25 (nuevo) |
| 4 | #33 (H1) | #25 (H3) | C | 106.16 cm | 4ª de 5 barras que fijan #25 (nuevo) |
| 5 | #37 (H1) | #25 (H3) | C | 106.16 cm | 5ª de 5 barras que fijan #25 (nuevo) |


## Verificación de cobertura

- Barras totales en el modelo: 119
- Barras instaladas en la secuencia: 119
- Barras sin asignar (deberían ser 0): 0

