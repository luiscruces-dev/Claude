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

### 5.1 Patronaje de los paneles

Aunque hay 75 triángulos, cada uno queda totalmente definido por sus 3 lados (A/B/C),
así que **solo existen 2 formas de panel distintas** en todo el domo:

| Panel | Lados | Ángulos (opuestos a cada lado) | Área | Cantidad | Área total |
|---|---|---|---|---|---|
| **P1** | A · A · B = 125.59 · 125.59 · 122.89 cm | 60.71° · 60.71° · 58.58° | 0.6730 m² | 45 | 30.29 m² |
| **P2** | B · C · C = 122.89 · 106.16 · 106.16 cm | 70.73° · 54.63° · 54.63° | 0.5319 m² | 30 | 15.96 m² |
| **Total** | | | | **75** | **46.24 m²** ✓ (coincide con el área de superficie de §5) |

Ambos paneles son triángulos isósceles. Con solo 2 plantillas de corte (más el margen
de costura/pegado en cada borde) se cubren los 75 paneles del domo — no hace falta
un patrón distinto para cada uno.

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

## 6.1 Peso de la estructura y carga sobre la fundación

Cálculo de peso propio (dead load) — este sí es 100% calculable con lo que ya
tenemos, sin datos externos:

| Componente | Cálculo | Peso |
|---|---|---|
| 120 barras de tubo (32mm×2mm, 143.80 m) | sección 188.5 mm² × 7850 kg/m³ = 1.480 kg/m | **212.8 kg** |
| 46 discos de nodo (⌀13cm × 5mm, supuesto de diseño) | 0.521 kg c/u × 46 | **24.0 kg** |
| **Subtotal estructura de acero** | | **236.7 kg** |
| Membrana (46.24 m² × 900 g/m², punto medio del rango 850–950 GSM) | | **41.6 kg** |
| **PESO TOTAL DEL DOMO** | | **≈ 278 kg (0.28 t)** |

Repartido entre los 15 nodos de fundación (§4): **≈18.6 kg (182 N) por nodo en
promedio**, solo por peso propio. Este número es deliberadamente pequeño — para una
estructura ligera de tubo + membrana como esta, el **peso propio casi nunca es la
carga que gobierna el diseño de la fundación**; el viento sí lo es (una cubierta
liviana como esta se comporta más como una vela que como una losa pesada, así que la
succión/empuje de viento sobre el anclaje puede superar varias veces el peso propio).
Por eso el chequeo de viento de abajo no es opcional.

*(Este peso es solo el de la estructura del domo — cama, muebles, jacuzzi y el
huésped cargan sobre la plataforma/deck, no sobre los nodos del domo, y se calculan
aparte cuando se diseñe esa plataforma.)*

## 6.2 Viento — estimación ilustrativa (⚠ NO reemplaza COVENIN-MINDUR 2003)

No hay velocidad de diseño oficial (mapa de zonificación COVENIN-MINDUR 2003) para
Tovar todavía, así que este cálculo usa un **valor ilustrativo, elegido a propósito
"medio agresivo"** a partir de la referencia dada: viento de temporada capaz de
arrancar árboles (aprox. Beaufort 10–11). Sirve para tener un orden de magnitud y
saber qué tan en serio hay que tomar el anclaje — **no es un cálculo de código, y no
sustituye la verificación de un ingeniero estructural con el dato real del sitio.**

**Supuesto:** V = 100 km/h (27.78 m/s), como velocidad de ráfaga ilustrativa.

| Paso | Cálculo | Resultado |
|---|---|---|
| Presión dinámica | q = 0.613 × V² | **473 Pa** (48.2 kgf/m²) |
| Área de silueta frontal del domo | segmento circular del corte (R=3.045 m, cresta a 2.52 m) | **11.40 m²** |
| Coeficiente de arrastre (Cd) | valor típico para cúpula de superficie rugosa (membrana) | 0.6 (supuesto) |
| **Empuje lateral total** | q × Cd × A_frontal | **≈ 3 235 N (330 kgf)** |
| Coeficiente de succión en la cresta (Cp) | típico de domos, zona de succión máxima | −0.8 (supuesto) |
| **Succión local máxima** | q × \|Cp\| | **≈ 378 Pa (38.6 kgf/m²)** |

**Lo que esto confirma, incluso como estimación:**
- El empuje lateral de viento (**330 kgf**) ya es **mayor que el peso propio del domo
  completo** (278 kgf) a esta velocidad ilustrativa — 1.18×.
- La succión en la cresta, aplicada sobre el área de piso como referencia gruesa, da
  **≈1 091 kgf** — casi **4 veces el peso propio**. Aunque este número no es una
  fuerza neta real (la succión no actúa uniforme sobre toda el área a la vez), confirma
  que el domo **puede tender a levantarse**, no solo a deslizar.
- **Conclusión práctica:** los 15 nodos de fundación necesitan un anclaje mecánico
  positivo (perno de anclaje embebido, no solo apoyo por peso), diseñado para
  **tensión (arranque/uplift), no solo compresión.** Esto aplica sobre todo a los
  nodos H5 (los 5 "altos" del zigzag — ver §4), que quedan más expuestos por estar en
  la cresta del zigzag de la base.
- Fuerza lateral promedio por nodo: ≈22 kgf. Succión ilustrativa promedio por nodo:
  ≈73 kgf — este segundo número es el que debería usarse para dimensionar el perno de
  anclaje, con el factor de seguridad que indique el ingeniero.

## 6.3 Sismo — estimación ilustrativa (⚠ NO reemplaza COVENIN 1756)

**Nota sobre el dato de entrada:** el promotor reportó que el último sismo sentido en
la zona fue hace varios años y no superó magnitud 6. Ese dato describe sismicidad
*sentida reciente*, no el peligro sísmico de diseño — en una zona de falla activa como
la de Boconó, que atraviesa el estado Mérida, un sismo grande tiene un período de
retorno de décadas a siglos, así que "no ha pasado nada fuerte en memoria reciente" no
implica que la zona sea de bajo peligro sísmico según el mapa de zonificación. Por eso
este cálculo **no usa un factor bajo** solo porque no se ha sentido un sismo fuerte
recientemente — usa un valor ilustrativo típico de la clasificación real de la región
andina venezolana (zona de peligro alto por la falla de Boconó), no del reporte
subjetivo.

**Supuesto:** coeficiente sísmico ilustrativo Ao = 0.30 (30% de g), representativo de
una zona sísmica alta en Venezuela — valor de referencia, no tomado del mapa oficial
vigente de COVENIN 1756 para Tovar específicamente.

Cálculo estático equivalente simplificado (fuerza horizontal ≈ Ao × peso, sin factores
de reducción por ductilidad ni de amplificación de suelo — ambos requieren la norma
completa):

| Paso | Cálculo | Resultado |
|---|---|---|
| Peso total del domo | de §6.1 | 278.4 kg (2 731 N) |
| Coeficiente sísmico ilustrativo | Ao | 0.30 |
| **Fuerza sísmica horizontal** | Ao × W | **≈819 N (83.5 kgf)** |
| Promedio por nodo de fundación (15 nodos) | | **≈55 N (5.6 kgf)** |

**Lectura del resultado:** la fuerza sísmica ilustrativa (83.5 kgf) es **unas 4 veces
menor que el empuje lateral de viento** ya calculado en §6.2 (330 kgf). Esto es
consistente con lo esperado para una estructura tan liviana: la fuerza sísmica escala
con la masa (y este domo pesa muy poco), mientras que la fuerza de viento escala con
el área expuesta. **El viento gobierna el diseño lateral de este domo, no el sismo.**
Donde el sismo sí importa es en el **anclaje** — el ingeniero debe revisar la
combinación de cargas (viento + sismo + peso propio no actúan por separado) y, sobre
todo, que la conexión a la fundación tenga ductilidad suficiente para no fallar frágil
ante un movimiento del suelo, incluso si la fuerza sísmica absoluta es menor que la de
viento.

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

Herramientas: Python puro (sin dependencias externas) — ver §8, donde este mismo
método quedó reimplementado como programa ejecutable y verificado de forma
independiente.

---

## 8. Programa de verificación y simulación de armado

Todo lo anterior se validó con un programa real, en Python puro (sin `numpy` ni
`scipy`, corre con `python3 archivo.py` en cualquier máquina), guardado en este
mismo directorio del repositorio. La idea: no confiar en los números de este
documento porque "salieron de un cálculo" — poder **reproducirlos, verificarlos y
simular el armado pieza por pieza** de forma independiente.

### 8.1 `dome_model.py` — motor geométrico (fuente única de verdad)

Reimplementación completa, desde cero, del método descrito en §7 (icosaedro →
subdivisión 3V → corte → escalado → clasificación). Se corrió de forma independiente
del cálculo original y **reprodujo exactamente los mismos números** publicados en
este documento (R, altura del ápice, área de piso, longitud total de tubo, área de
membrana) — es la primera verificación real: dos implementaciones distintas del
mismo método, mismo resultado.

### 8.2 `dome_verify.py` — batería de chequeos automáticos

Corre `dome_model.py` y valida, con PASS/FAIL explícito por cada chequeo:

- **Geometría de la esfera completa:** fórmula de Euler (V−E+F=2), y que la
  subdivisión 3V dé exactamente 92 vértices / 180 triángulos / 270 aristas (el
  número estándar de la industria para este método — si no coincide, hay un bug).
- **Los 75 paneles:** que ningún triángulo sea degenerado (desigualdad triangular) y
  que sus 3 ángulos internos sumen 180° en todos los casos.
- **Las 120 barras:** que la longitud recalculada de cada arista coincida con su
  clase declarada (±1 mm) — atrapa errores de redondeo o de clasificación.
- **Regresión contra este documento:** recalcula altura del ápice, área de piso,
  área de membrana, longitud total de tubo, R, y las 3 longitudes de barra con sus
  cantidades — y verifica que coincidan con los valores publicados en §1–§2. Si
  alguien edita un número en este `.md` a mano y se equivoca, este chequeo lo
  detectaría.
- **Los 46 nodos:** exactamente 5 tipos geométricos, que la suma de nodos por tipo
  dé 46, que la suma de grados de todos los nodos sea el doble del número de
  aristas (chequeo de consistencia del grafo), y que la suma de ángulos en cada tipo
  de nodo cerrado sea menor a 360° (la curvatura tiene que ser positiva en toda
  esfera real — si diera ≥360° en algún nodo, la geometría estaría mal).
- **El anillo base:** que sean 15 nodos de borde (no 10 — la corrección de §4), que
  formen exactamente 2 niveles de altura, y que el desnivel sea 4.86 cm.
- **Pandeo (Euler) de las 3 barras:** que las 3 —no solo la más larga, como en el
  chequeo manual original— tengan capacidad crítica por encima de un mínimo
  aceptado.

**Resultado de la última corrida: todos los chequeos pasaron** (ver
`reporte_verificacion.txt` en este directorio, generado con
`python3 dome_verify.py > reporte_verificacion.txt`).

Lo que este programa **no** hace, para que quede claro el alcance: no es un
análisis estructural (FEA / método matricial de rigidez), y no reemplaza el chequeo
de viento/sismo con datos oficiales de sitio (§6.2/6.3) — verifica consistencia
geométrica y de datos, no seguridad estructural bajo carga real. Eso sigue
necesitando al ingeniero.

### 8.3 `dome_build_sequence.py` — simulación de armado pieza por pieza

Este es el que responde "¿en qué orden corto y suelto esto para que se pueda armar
de verdad?". Simula el armado **de la base hacia el ápice, anillo por anillo** (el
método realista para construir en sitio sin grúa: cada pieza nueva se suelda
apoyada en estructura ya fija, nunca al aire), y en cada paso valida que cada nodo
nuevo quede geométricamente fijo por **al menos 2 barras no paralelas** antes de
seguir — si un nodo quedara sostenido por una sola barra, el programa lo marca como
que necesita sujeción temporal (gato, cuerda, un ayudante) hasta que la segunda
barra lo triangule.

**Resultado de la simulación:**
- **7 anillos** de armado, de la fundación al ápice.
- **120/120 barras** quedan asignadas a un paso — ninguna barra "huérfana" sin
  lugar en la secuencia (el programa aborta con error si esto llegara a pasar).
- **0 nodos necesitan sujeción temporal** — cada nodo nuevo, en los 7 anillos,
  queda triangulado (≥2 barras a estructura ya fija) en el mismo paso en que
  aparece. Esto es una propiedad real y verificada del diseño, no una suposición:
  el domo se puede armar anillo por anillo sin andamiaje de soporte temporal para
  los nodos, más allá de lo normal para sostener al soldador.

El checklist completo, barra por barra, con qué nodo va a qué nodo y con qué queda
fijado cada uno, está en **`secuencia_de_armado.md`** (generado automáticamente,
120 barras + 15 anclajes de fundación, listo para imprimir y llevar al taller).

### 8.4 Cómo correr esto

```bash
cd glamping-cucuchica
python3 dome_verify.py               # imprime el reporte de verificación
python3 dome_build_sequence.py       # regenera secuencia_de_armado.md
```

Sin instalar nada — los 3 scripts son Python estándar. Si en algún momento cambia
un parámetro (por ejemplo, el diámetro de base o la frecuencia del domo), se edita
`build_dome(...)` en `dome_model.py` y los otros dos scripts recalculan todo solos.

---

## 9. Pendientes / próximos pasos

**Cálculo puro — resuelto en este documento:**
- [x] Peso total de la estructura y carga por nodo de fundación (§6.1)
- [x] Patronaje de los paneles de membrana — solo 2 formas distintas (§5.1)
- [x] Empuje y succión de viento — **estimación ilustrativa** con V=100 km/h supuesta, no con el dato oficial de sitio (§6.2)
- [x] Fuerza sísmica horizontal — **estimación ilustrativa** con Ao=0.30 supuesto, no con el mapa oficial de zonificación (§6.3)
- [x] Verificación independiente de toda la geometría y los totales publicados, con programa reproducible (§8) — todos los chequeos pasan
- [x] Simulación de secuencia de armado pieza por pieza, con checklist barra por barra (§8.3, `secuencia_de_armado.md`)

**Con esto, todos los cálculos puramente geométricos y de carga que identificamos
como posibles con la información disponible están resueltos.** Lo que queda ya no es
"cálculo pendiente" sino datos de sitio oficiales + decisiones de diseño + verificación profesional:

- [ ] Reemplazar los valores ilustrativos de viento (§6.2) y sismo (§6.3) por los datos oficiales de COVENIN-MINDUR 2003 y COVENIN 1756 para Tovar en cuanto estén disponibles
- [ ] Verificación estructural final por ingeniero matriculado (incluye combinación de cargas viento+sismo+peso propio, y diseño del anclaje a tensión)

**Decisión de diseño — no es cálculo, requiere elegir entre opciones:**
- [ ] Diseño físico del hub plate (diámetro de disco, patrón de pernos o muñones, espesor final — los ángulos ya están en §3)
- [ ] Diseño de la plataforma/deck y anillo de fundación (incluye estudio de suelo — ver riesgo de escorrentías/agua mencionado en el análisis de ubicación)
- [ ] Altura del riser/taco en los 5 nodos altos (H5) — el desnivel exacto (4.86 cm) ya está calculado en §4, falta decidir si se resuelve con muro de arranque, taco soldado o pies regulables

**No es cálculo — investigación de mercado:**
- [ ] Cotización real de tubo galvanizado 32×2mm y de la membrana (PVC/poliéster) en talleres venezolanos

---

*Documento generado a partir de cálculo geométrico numérico verificado (icosaedro →
subdivisión 3V → proyección esférica → corte y clasificación de aristas/nodos). Todas
las cifras de este documento son consistentes entre sí y con el visor HTML adjunto,
que usa exactamente los mismos datos.*
