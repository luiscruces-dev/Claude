# Domo geodésico 3V — Cucuchica

Documentación técnica del domo geodésico para el proyecto de glamping en el balneario
de Cucuchica (municipio Tovar, estado Mérida, Venezuela). Este documento reúne todas
las medidas, ángulos y cálculos derivados de la geometría real del domo — no de tablas
genéricas de fabricantes.

Visor 3D interactivo (mismo contenido, en formato navegable con vista 3D rotable y
diagramas de nodo): [`domo-3v-cucuchica.html`](./domo-3v-cucuchica.html)

---

## 0. Contexto del proyecto

La idea es construir un pequeño complejo de glamping (domos geodésicos tipo
"habitación de hotel en la naturaleza") dentro de un balneario ya operativo en
Cucuchica, que cuenta con permisos turísticos vigentes y flujo de visitantes propio.
La ventaja central frente a un glamping construido desde cero es que el terreno, el
atractivo turístico, los accesos y la demanda ya existen — el domo añade una fuente de
ingresos por alojamiento sobre una operación que ya funciona.

Fase inicial propuesta: 2 unidades (una estándar, una "signature" con jacuzzi), con
escalamiento a 4, 6 y 10 unidades según la ocupación real observada. El padre del
promotor es soldador con más de 20 años de experiencia (incluye trabajo en soldadura
submarina), lo que abre la posibilidad de fabricar la estructura de acero localmente
en vez de importar el domo completo — de ahí nace este documento: los cálculos de
material y geometría necesarios para que la estructura se pueda soldar en taller.

*(El análisis de mercado, tarifas, escenarios financieros y punto de equilibrio se
trabajó por separado en la conversación con Claude que originó este documento; este
archivo se enfoca exclusivamente en la ingeniería de la estructura.)*

---

## 1. Geometría elegida

**Domo geodésico de frecuencia 3V** (subdivisión icosaédrica Clase I, método
"alternate"), proyectado radialmente sobre una esfera y cortado **justo por encima del
ecuador** — es decir, sin voladizo. Se descartó el clásico corte "5/8 de esfera" (más
alto, con la pared curvándose hacia adentro en la base) porque un domo sin voladizo
apoya directo sobre una base plana, mucho más simple de anclar y de soldar para una
primera construcción.

| Parámetro | Valor |
|---|---|
| Frecuencia | 3V (subdivisión icosaédrica, Clase I) |
| Radio de la esfera completa | R = 3.0452 m |
| Diámetro de la base construida | **6.00 m** (exacto, anillo de nodos "bajos") |
| Diámetro equatorial teórico de la esfera completa | 6.09 m (no se construye, es solo referencia) |
| Altura del ápice sobre la base | **2.5225 m** |
| Área de piso / huella | **28.274 m²** |
| Volumen interior aproximado | **44.07 m³** |
| Vértices / nodos (hubs) | 46 |
| Caras triangulares | 75 |
| Aristas / barras (struts) | 120 |

El área de piso calculada (28.27 m²) coincide con la estimación genérica inicial de
"~28 m²" para un domo de 6 m — buena señal de que el cálculo está en línea con la
realidad comercial de este tipo de estructuras.

---

## 2. Barras de acero (struts)

120 barras en total, agrupadas en **solo 3 longitudes distintas** gracias a la
simetría icosaédrica del domo:

| Tipo | Longitud (centro de nodo a centro de nodo) | Cantidad | Metros totales |
|---|---|---|---|
| A | 125.59 cm | 50 | 62.795 m |
| B | 122.89 cm | 40 | 49.156 m |
| C | 106.16 cm | 30 | 31.848 m |
| **Total** | | **120** | **143.80 m** |

**Nota de fabricación:** estas longitudes son de centro de nodo a centro de nodo. La
longitud real de corte del tubo = esta medida **menos** lo que ocupe el diseño del
conector en cada extremo (ver §4). Ajustar según el diseño final del hub — típicamente
entre 1 y 3 cm por extremo.

### 2.1 Lista de corte (optimización de barras comerciales)

Cálculo de corte tipo *cutting-stock* (nesting) con 3 mm de pérdida por corte de sierra:

**Barras de 6 m:**
- **27 barras** necesarias → 162.00 m comprados, 143.80 m usados → **11.2% de desperdicio**
- Patrones de corte: 12×[A,A,A,A] · 9×[B,B,B,B,C] · 3×[C,C,C,C,C] · 1×[A,A,B,B] · 1×[B,B,C,C,C] · 1×[C,C,C]

**Barras de 12 m** (recomendado si está disponible — menos desperdicio):
- **13 barras** necesarias → 156.00 m comprados, 143.80 m usados → **7.8% de desperdicio**
- Patrones de corte: 5×[A×9] · 4×[B×9] · 2×[C×11] · 1×[A×5, B×4] · 1×[C×8]

---

## 3. Nodos (hubs) — 5 tipos geométricos, 46 hubs

Aunque hay 46 nodos, la simetría icosaédrica del domo los reduce a **solo 5
geometrías distintas**. Esto significa que solo se necesitan 5 plantillas/jigs de
soldadura, no 46.

Para cada barra, la **inclinación respecto al plano tangente** en el hub depende solo
del tipo de barra (no del hub específico) — es un dato útil si se diseña un hub tipo
"placa plana tangente a la esfera":

| Tipo de barra | Inclinación bajo el plano tangente |
|---|---|
| A (125.59 cm) | −11.90° |
| B (122.89 cm) | −11.64° |
| C (106.16 cm) | −10.04° |

### H1 — 20 nodos · grado 6 · interior (cerrado)
Barras concurrentes: A, A, B, B, B, C.
Ángulos entre barras consecutivas (orden cíclico): 54.63° · 60.71° · 60.71° · 60.71° · 60.71° · 54.63°
(suma = 352.10° — el defecto de ~7.9° respecto a 360° es la curvatura propia del domo en ese punto).

### H2 — 5 nodos · grado 6 · interior (cerrado)
Barras concurrentes: A, A, A, A, A, A (las 6 son tipo A).
Ángulos entre barras consecutivas: 58.58° (los 6, iguales). Suma = 351.48°.

### H3 — 6 nodos · grado 5 · interior (cerrado) — incluye el ápice
Barras concurrentes: C, C, C, C, C (las 5 son tipo C).
Ángulos entre barras consecutivas: 70.73° (los 5, iguales). Suma = 353.65°.

### H4 — 10 nodos · grado 4 · borde (abierto) — anillo base, nodos "bajos"
Barras concurrentes: A, B, B, C.
Ángulos entre barras consecutivas: 54.63° · 54.63° · 60.71° (solo 3 ángulos — el nodo
está "abierto" hacia el borde del domo, el lado que falta se conecta a la fundación).

### H5 — 5 nodos · grado 4 · borde (abierto) — anillo base, nodos "altos"
Barras concurrentes: A, A, A, A (las 4 son tipo A).
Ángulos entre barras consecutivas: 58.58° · 58.58° · 58.58°.

**Método de fabricación recomendado:** placa/disco de acero por nodo (hub plate) con
muñones o pestañas soldadas en el ángulo exacto de cada barra, en vez del sistema
comercial de "tubo aplastado + pernos" (que requiere prensa hidráulica). Los ángulos de
arriba son directamente los ángulos a marcar alrededor del disco.

Material aproximado de plancha para los 46 discos (si se usan discos de ⌀13 cm × 5 mm):
**~0.6 m² de plancha de acero** (sin merma de corte).

---

## 4. Anillo base y anclaje

**Corrección importante respecto a un cálculo preliminar:** el borde del domo **no**
es un anillo plano de 10 puntos. Es un **zigzag de 15 nodos**: 10 nodos "bajos" (tipo
H4) más 5 nodos "altos" (tipo H5), en un patrón que se repite 5 veces alrededor del
domo (bajo-bajo-alto, bajo-bajo-alto...). Este zigzag es normal en cualquier domo
geodésico real — es la manera en que la triangulación cierra el casquete esférico.

| | Nodos bajos (H4) | Nodos altos (H5) |
|---|---|---|
| Cantidad | 10 | 5 |
| Radio desde el eje central | 3.000 m | 2.9911 m |
| Altura relativa | 0 cm (referencia) | **+4.86 cm** |
| Diámetro circunscrito | **6.00 m exacto** | 5.982 m (prácticamente el mismo) |

- **Perímetro total del borde (zigzag):** 18.70 m — compuesto por 10 barras tipo A y
  5 barras tipo B, **ya incluidas** en el conteo de la sección 2 (no se necesita barra
  adicional para cerrar la base).
- **Solución constructiva recomendada:** soldar un taco/riser de **4.86 cm** bajo cada
  uno de los 5 nodos altos (tipo H5). Los 10 nodos bajos (tipo H4) apoyan directo, al
  ras, sobre el anillo de fundación / plataforma. No hace falta un muro de arranque
  completo con postes de dos alturas — basta con 5 tacos cortos.
- Alternativa aún más simple para una primera unidad de prueba: usar pies/calzos
  regulables en la plataforma, 5 de ellos 4.86 cm más altos que los otros 10.

---

## 5. Cubierta (membrana)

| | Valor |
|---|---|
| Área de superficie (75 paneles triangulares) | 46.24 m² |
| Con 12% de merma de corte/costura | **51.79 m²** a comprar |
| Material de referencia | poliéster de alta resistencia recubierto en PVC, ~850–950 GSM, resistente a UV, desgarro y moho |

Cada uno de los 75 triángulos tiene un patrón ligeramente distinto (varía con el tipo
de barra en sus 3 lados) — el patronaje detallado de cada panel es un cálculo
pendiente, no incluido en esta primera pasada.

---

## 6. Especificación de tubo y notas de construcción

### Tubo recomendado
**Redondo, 32 mm de diámetro exterior × 2 mm de pared**, acero estructural
(equivalente a ASTM A500 o el tubo estructural local disponible), galvanizado.

**Chequeo de pandeo (Euler, apoyo simple, K=1)** sobre la barra más larga (tipo A,
125.59 cm):
- Momento de inercia I ≈ 2.13×10⁻⁸ m⁴
- Carga crítica de pandeo Pcr ≈ 26.6 kN (**~2.7 toneladas** de compresión axial)
- Esto da un margen amplio frente a las cargas típicas de una estructura de este
  tamaño (peso propio + viento moderado). Se puede usar la misma sección en las 3
  longitudes de barra — la diferencia de 12–19 cm entre tipos no justifica variar el
  calibre y simplifica el trabajo de taller.

### Galvanizado
**Galvanizar después de cortar, taladrar y soldar** — nunca antes. Si se suelda tubo
ya galvanizado, el zinc se quema justo en la unión, que es exactamente donde más
protección contra corrosión se necesita en un clima húmedo como el de Cucuchica.

### ⚠ Verificación estructural pendiente
Este cálculo confirma que la sección elegida no falla por pandeo bajo cargas típicas,
pero **no reemplaza un chequeo de viento específico para Tovar/Mérida** según el
código venezolano (COVENIN-MINDUR 2003, "Acciones del viento sobre las
construcciones"). Se recomienda que un ingeniero estructural con matrícula revise el
diseño final antes de construir la unidad definitiva, dado que va a alojar personas.

---

## 7. Metodología de cálculo (para reproducibilidad)

1. Se construyó un icosaedro regular (12 vértices, 20 caras) de radio unitario.
2. Cada cara triangular se subdividió en una grilla de frecuencia 3 (9 triángulos por
   cara, barycéntrica), y cada punto nuevo se proyectó radialmente sobre la esfera
   (Clase I, método "alternate"). Resultado: esfera completa de 92 vértices, 180
   triángulos, 270 aristas — verificado contra la fórmula de Euler (V − E + F = 2).
3. Orientación **"vértice arriba"** (un vértice del icosaedro original apunta al
   ápice), que es la que da filas horizontales limpias de vértices — la orientación
   estándar de la industria para domos habitables.
4. Se identificó la fila de corte (justo sobre el ecuador) y se escaló la esfera
   (R = 3.0452 m) para que el anillo de nodos "bajos" tenga exactamente 6.00 m de
   diámetro circunscrito.
5. Se recortó el casquete (cara con sus 3 vértices dentro de la fila de corte o por
   encima), y se extrajeron aristas, triángulos y nodos de borde.
6. Longitudes de barra: se agruparon las 120 aristas por longitud (tolerancia 3 mm) →
   3 clases (A/B/C).
7. Ángulos de nodo: para cada vértice, se recorrieron los triángulos que lo contienen
   y se calculó el ángulo real en 3D en cada uno (arco-coseno del producto punto de
   los vectores de arista). Los nodos se clasificaron en tipos por firma geométrica
   (grado, ¿cerrado o abierto?, multiset de barras, multiset de ángulos) → 5 tipos
   (H1–H5).
8. Lista de corte: bin-packing (first-fit-decreasing) de las 120 barras contra barras
   comerciales de 6 m y 12 m, con 3 mm de pérdida por corte.

Herramientas: Python (`numpy`, `scipy.spatial.ConvexHull` para generar las caras del
icosaedro). Los scripts de cálculo no se conservaron en este repositorio — este
documento y el HTML adjunto contienen todos los resultados numéricos derivados de
ellos.

---

## 8. Pendientes / próximos pasos

- [ ] Verificación de viento (COVENIN-MINDUR 2003) por ingeniero estructural matriculado
- [ ] Diseño físico del hub plate (diámetro de disco, patrón de pernos o muñones, espesor final)
- [ ] Diseño de la plataforma/deck y anillo de fundación (incluye estudio de suelo — ver riesgo de escorrentías/agua mencionado en el análisis de ubicación)
- [ ] Patronaje individual de los 75 paneles de membrana para corte y costura
- [ ] Cotización real de tubo galvanizado 32×2mm y de la membrana (PVC/poliéster) en talleres venezolanos
- [ ] Decisión de altura del riser/taco en los 5 nodos altos (H5) — o alternativa de pies regulables

---

*Documento generado a partir de cálculo geométrico numérico verificado (icosaedro →
subdivisión 3V → proyección esférica → corte y clasificación de aristas/nodos). Todas
las cifras de este documento son consistentes entre sí y con el visor HTML adjunto,
que usa exactamente los mismos datos.*
