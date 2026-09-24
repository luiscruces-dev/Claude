# Domo geodésico 3V — Cucuchica

Documentación técnica del domo geodésico para el proyecto de glamping en el balneario
de Cucuchica (municipio Tovar, estado Mérida, Venezuela). Este documento reúne todas
las medidas, ángulos y cálculos derivados de la geometría real del domo — no de tablas
genéricas de fabricantes.

**Plano de taller** con vista 3D, piezas y plan de corte, plantillas de nodo, puerta,
replanteo y armado: [`domo-3v-cucuchica.html`](./domo-3v-cucuchica.html), generado con
`python3 dome_viewer.py` a partir de los mismos módulos que este documento.

> **⚠ Auditoría independiente (2026-09-24) — leer antes de cortar, soldar o comprar.**
> La geometría (R, barras, nodos, paneles, áreas, perímetro, zigzag) se reprodujo con un
> cálculo independiente y **es correcta**. Estos puntos estaban mal y ya se corrigieron en
> este documento, en el visor HTML y en `secuencia_de_armado.md`:
> 1. **Ángulos a marcar en el disco del nodo (§3):** los ángulos 3D entre barras no son los
>    que se marcan en un disco plano. Se agregó la tabla de azimuts (55.69° / 62.15° /
>    60.00° / 72.00°), que sí suman 360°.
> 2. **Retiro de corte (§2):** "1 a 3 cm por extremo" es imposible con tubo de 32 mm; el
>    mínimo geométrico es 3.1 cm y con disco de ⌀13 cm ronda 6.5 cm.
> 3. **Alturas de armado:** la secuencia medía desde el centro de la esfera (+52.3 cm de
>    error). Ahora mide desde el piso.
> 4. **Estabilidad en el armado (§8.3):** decía "0 nodos necesitan sujeción temporal". En
>    3D, los 5 nodos del paso 1 quedan como bisagra y necesitan puntal.
> 5. **Replanteo de anclajes (§9.2):** decía que las posiciones angulares estaban en la
>    secuencia y no estaban. Ya están (azimut, radio, X, Y).
> 6. **Puerta (§11, nuevo):** ya está diseñada y verificada. Es un portal con marco de
>    50×50 sobre dos anclajes existentes y vano libre de 117.9 × 207.5 cm. Con la puerta,
>    las cantidades de §2 cambian a A 48, B 37 y C 25, más 9 piezas de la puerta.
>
> Riesgos de dinero o de seguridad que **no estaban calculados** (membrana con costuras,
> reparto real del viento por anclaje, presión interna, puerta, plataforma y pilotes, lista
> de corte óptima): ver [`auditoria/AUDITORIA.md`](./auditoria/AUDITORIA.md).

---

## 0. Contexto del proyecto

La idea es construir un pequeño complejo de glamping (domos geodésicos tipo
"habitación de hotel en la naturaleza") dentro de un balneario ya operativo en
Cucuchica, que cuenta con permisos turísticos vigentes y flujo de visitantes propio.
La ventaja central frente a un glamping construido desde cero es que el terreno, el
atractivo turístico, los accesos y la demanda ya existen — el domo añade una fuente de
ingresos por alojamiento sobre una operación que ya funciona.

Fase inicial propuesta: 2 unidades (una estándar, una "signature" con jacuzzi en la
terraza exterior, no dentro de la habitación), con
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
conector en cada extremo (ver §3). *(Corregido en la auditoría: decía "típicamente entre 1
y 3 cm por extremo", lo que es imposible con este tubo.)* Con tubo de 32 mm, en los nodos
donde dos barras forman 54.63° los tubos se tocan hasta **3.1 cm** del centro del nodo,
así que ese es el retiro mínimo absoluto. Con el disco de ⌀13 cm de §3 el tubo arranca en
el borde del disco: del orden de **6.5 cm por extremo**. Definir el conector **antes** de
cortar y recalcular la lista de corte con el largo real (ver `auditoria/AUDITORIA.md`).

### 2.1 Lista de corte (optimización de barras comerciales)

Cálculo de corte tipo *cutting-stock* (nesting) con 3 mm de pérdida por corte de sierra:

*(Auditoría: con largos de centro a centro el óptimo exacto son 25 barras de 6 m, pero
exige 10 barras con solo 7.9 mm de sobra. Exigiendo 20 mm de holgura, 27 es correcto. Con
el largo real de corte, restando el conector, bastan **23 barras de 6 m**. El patrón
9×[B,B,B,B,C] de abajo deja solo 7.9 mm de sobra por barra: cualquier barra de 5.99 m o
un extremo dañado arruina la quinta pieza.)*

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
comercial de "tubo aplastado + pernos" (que requiere prensa hidráulica).

**⚠ Corregido en la auditoría:** aquí decía que los ángulos de arriba "son directamente
los ángulos a marcar alrededor del disco". **No lo son.** Los ángulos de arriba son el
ángulo 3D entre dos tubos, medido en el plano que forman los dos tubos. Suman menos de
360°, así que en un disco plano no cierran. Marcándolos así, cada pestaña queda desviada
entre 1.06° y 1.45°, unos 3 cm en el otro extremo de una barra A, y el domo no cierra sin
forzar. En el disco se marca el **azimut** (el ángulo proyectado sobre el plano del disco)
y después cada pestaña se inclina hacia abajo lo que indica la tabla de inclinación de
arriba:

| Nodo | Barras en orden alrededor del disco | Azimut entre pestañas consecutivas (a marcar) | Suma |
|---|---|---|---|
| H1 (20) | C · B · A · B · A · B | 55.69° · 62.15° · 62.15° · 62.15° · 62.15° · 55.69° | 360° |
| H2 (5) | A × 6 | 60.00° × 6 | 360° |
| H3 (6) | C × 5 | 72.00° × 5 | 360° |
| H4 (10, borde) | B · C · B · A | 55.69° · 55.69° · 62.15° (+ 186.46° abierto hacia el borde) | 360° |
| H5 (5, borde) | A · A · A · A | 60.00° · 60.00° · 60.00° (+ 180.00° abierto hacia el borde) | 360° |

Los ángulos 3D de arriba siguen siendo útiles para **verificar** con transportador una
pieza ya armada, midiendo entre los dos tubos. Los azimuts están calculados en
`auditoria/auditoria_independiente.py` y son iguales en todos los nodos de cada tipo.

Material aproximado de plancha para los 46 discos (si se usan discos de ⌀13 cm × 5 mm):
**~0.6 m² de plancha de acero** (sin merma de corte). *(Auditoría: esto no incluye las 240
pestañas, 2 por barra. Con pestañas de 40×80 mm son ~0.77 m² más, o sea más que los
discos. Tampoco están en la lista la soldadura, los pernos si las uniones son empernadas,
ni los 15 pernos de anclaje con sus placas y tuercas.)*

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
- *(Auditoría: con el piso plano, el borde de la membrana queda 4.86 cm por encima del piso
  entre cada nodo alto y sus vecinos. Hace falta un faldón o sello perimetral para que no
  entren agua ni bichos.)*
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
| Con 12% de merma de corte/costura | **51.79 m²** a comprar — **⚠ insuficiente si se cortan 75 paneles con solape (ver nota)** |
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

**⚠ Auditoría — cantidad de membrana:** el 12% de merma no alcanza para cortar 75 paneles
con margen de costura. Solo las piezas cortadas, sin contar el desperdicio del rollo,
suman 54.7 m² con 3 cm de solape por lado y 60.7 m² con 5 cm. Presupuestar **~60–67 m²**
o pedir al fabricante la cotización con su propio patronaje. Tampoco están en la lista
de materiales el aislante, el forro interior, las ventanas ni la puerta, que en un domo de
glamping se compran aparte.

---

## 6. Especificación de tubo y notas de construcción

### Tubo recomendado
**Redondo, 32 mm de diámetro exterior × 2 mm de pared**, acero estructural
(equivalente a ASTM A500 o el tubo estructural local disponible), galvanizado.

**Chequeo de pandeo (Euler, apoyo simple, K=1)** sobre la barra más larga (tipo A,
125.59 cm):
- Momento de inercia I ≈ 2.13×10⁻⁸ m⁴
- Carga crítica de pandeo Pcr ≈ 26.6 kN (**~2.7 toneladas** de compresión axial)
  *(Auditoría: esa es la carga elástica teórica de Euler. Con esbeltez KL/r ≈ 118 la barra
  pandea en rango inelástico, y la capacidad de diseño según AISC 360 es ≈1.3–2.1 t,
  según el método y el acero. La auditoría resolvió además el domo como armadura espacial
  con las cargas de §6.1–6.2, cosa que este documento no hacía. La barra más comprimida
  llega a ≈0.12 t, un 5% de su capacidad, así que la sección sí alcanza como barra axial.)*
- *(Auditoría: lo que sí es crítico es la **flexión**. Una persona de 100 kg parada a
  media barra A la lleva a ≈231 MPa, en el límite de fluencia del tubo. Ni el armado ni
  la instalación de la membrana pueden hacerse caminando sobre las barras.)*
- Esto da un margen amplio frente a las cargas típicas de una estructura de este
  tamaño (peso propio + viento moderado). Se puede usar la misma sección en las 3
  longitudes de barra — la diferencia de 2.7–19.4 cm entre tipos *(corregido: decía
  "12–19 cm")* no justifica variar el calibre y simplifica el trabajo de taller.

### Galvanizado
**Galvanizar después de cortar, taladrar y soldar** — nunca antes. Si se suelda tubo
ya galvanizado, el zinc se quema justo en la unión, que es exactamente donde más
protección contra corrosión se necesita en un clima húmedo como el de Cucuchica.

*(Auditoría: esto choca con §8.3, donde el domo se arma **soldando en sitio**. Esas
uniones se sueldan después del galvanizado y hay que repararlas con galvanizado en frío
(pintura rica en zinc), o bien diseñar uniones empernadas. Además, los tubos cerrados
necesitan agujeros de venteo y drenaje para el baño en caliente: un tubo sellado puede
reventar dentro de la cuba.)*

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

*(Este peso es solo el de la estructura del domo. La cama, los muebles y el huésped
cargan sobre la plataforma, no sobre los nodos del domo, y se calculan aparte cuando se
diseñe esa plataforma. El jacuzzi va afuera, en la terraza, con fundación propia.)*

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

**⚠ Auditoría — reparto real por anclaje y presión interna.** La auditoría resolvió el
domo como armadura espacial con el mismo V = 100 km/h, usando un patrón de presiones
típico de cúpulas (barlovento +0.6, cresta −1.1, sotavento −0.4). Ese patrón da el mismo
empuje lateral total de 330 kgf que la tabla de arriba, pero el reparto entre anclajes no
es parejo:
- **Corte horizontal por anclaje:** hasta **56 kgf** en los nodos de los flancos, 2.6 veces
  el promedio de 22 kgf.
- **Arranque por anclaje:** hasta **81 kgf** sin presión interna, y hasta **129 kgf** si una
  puerta o ventana abierta a barlovento presuriza el interior (Cpi = +0.55). Todas las
  normas exigen sumar la presión interna, y este documento no la consideraba.
- **Cp de cresta:** −0.8 es menos exigente que los valores habituales para cúpulas
  rebajadas (−1.0 a −1.2).
El perno M12 sigue sobrando por acero. Lo que cambia es la base de diseño de §9.4, ver
`auditoria/AUDITORIA.md`.

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

*(Auditoría: `dome_verify.py` y `dome_build_sequence.py` importan el mismo
`dome_model.py`, así que no son independientes entre sí. La verificación realmente
independiente, que construye el icosaedro por otro camino, está en
`auditoria/auditoria_independiente.py`. También es falso que el chequeo de regresión
detecte cambios hechos a mano en este `.md`: compara contra números copiados dentro del
script y no lee este archivo.)*

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

**⚠ Corregido en la auditoría:** el punto anterior es falso en 3D. El programa original
consideraba fijo un nodo con 2 barras, pero en el espacio un nodo con 2 barras queda
como una bisagra y gira alrededor de la línea entre sus 2 apoyos. Hacen falta 3 barras no
coplanares. Con el criterio correcto, **los 5 nodos H3 del paso 1 (#0, #3, #7, #13, #20)
necesitan puntal o cuerda** hasta que el paso 2 los amarre. El resto de los nodos sí queda
fijo al aparecer, aunque de forma muy plana (entre 9° y 17° fuera del plano de sus
apoyos), así que conviene apuntalar hasta cerrar el anillo. Además, las alturas de la
secuencia estaban medidas desde el centro de la esfera, no desde el piso: todas tenían
52.3 cm de más. Ambas cosas ya están corregidas en `dome_build_sequence.py`.

El checklist completo, barra por barra, con qué nodo va a qué nodo y con qué queda
fijado cada uno, está en **`secuencia_de_armado.md`** (generado automáticamente,
con los 15 anclajes de fundación, listo para imprimir y llevar al taller). Con la puerta
de §11 son 119 piezas en 8 pasos; con `--sin-puerta`, 120 barras en 7 pasos.

### 8.4 Cómo correr esto

```bash
cd glamping-cucuchica
python3 dome_verify.py               # imprime el reporte de verificación
python3 dome_door.py                 # verifica la puerta (§11)
python3 dome_build_sequence.py       # regenera secuencia_de_armado.md (con puerta; --sin-puerta para el domo cerrado)
python3 dome_viewer.py               # regenera el plano de taller domo-3v-cucuchica.html
```

Sin instalar nada — los 3 scripts son Python estándar. Si en algún momento cambia
un parámetro (por ejemplo, el diámetro de base o la frecuencia del domo), se edita
`build_dome(...)` en `dome_model.py` y los otros dos scripts recalculan todo solos.

---

## 9. Plataforma y anclaje (diseño conceptual)

Diseño de primera pasada, usando directamente las cargas de §6. No sustituye el
estudio de suelo pendiente (§10) — es la base de partida para que el ingeniero
afine, no el diseño final.

### 9.1 Concepto general

**Plataforma elevada sobre pilotes**, no losa a nivel de piso. Dos razones, ambas ya
identificadas antes en el proyecto:
1. El anclaje tiene que resistir **tracción** (succión de viento, §6.2), no solo
   compresión — una losa apoyada directo en tierra no da forma fácil de anclar a
   tracción; un pilote de concreto con perno embebido sí.
2. Cucuchica tiene riesgo real de escorrentías y crecidas (quebradas, lluvia fuerte
   de montaña — ver el análisis de ubicación original). Elevar la plataforma es la
   misma solución que ya se había planteado para ese riesgo, y ahora además resuelve
   el anclaje.

Estructura: **pilotes de concreto** (fundación puntual) + **viga de anillo**
(cadena de amarre continua seteando los 15 nodos) + **entablado de madera o deck
compuesto** sobre vigas secundarias.

### 9.2 Geometría del anillo de fundación

Ya calculada en §4 — se reutiliza directo, sin volver a derivarla:

| | Valor |
|---|---|
| Nodos de anclaje | 15 (10 "bajos" H4 + 5 "altos" H5, zigzag) |
| Diámetro del anillo (nodos bajos) | 6.00 m exacto |
| Perímetro del anillo | 18.70 m |
| Desnivel bajo→alto | 4.86 cm |

Las posiciones angulares exactas de los 15 nodos están en `secuencia_de_armado.md`
(Paso 0: azimut, radio y coordenadas X/Y). *(Corregido en la auditoría: antes la tabla
no traía posiciones, solo la altura relativa.)* — son las mismas coordenadas que usa la
estructura de acero, así que el anclaje queda garantizado a coincidir con el domo
sin tener que volver a medir en campo desde cero (se replantea desde el centro con
los ángulos ya calculados).

### 9.3 Pilotes

*(Auditoría: este dimensionamiento considera solo el domo, ≈0.28 t. Pero los pilotes y
las vigas también cargan el piso: huéspedes, muebles y cama, unos 200 kgf/m², o sea
cerca de 6 t sobre los 28 m². Esa carga es unas 20 veces la del domo y no está
calculada. El jacuzzi va afuera, en la terraza: 1–2 t de agua con su propia fundación,
sin cargar la viga de anillo ni los pilotes del domo, y con el desagüe lejos de ellos. Con pilotes solo en el perímetro, las vigas del piso tendrían que salvar unos
6 m. Casi seguro hacen falta pilotes interiores. Además, el arranque neto de viento (hasta
≈1.3–1.5 t con presión interna) tiene que resistirse con el peso de pilotes y viga más la
fricción del suelo, y eso tampoco está verificado.)*

**10 pilotes de concreto**, no los 15 — un pilote en cada uno de los 5 nodos "altos"
(H5, obligatorio: son los más expuestos a succión de viento según §6.2) más 5
alternados de los 10 nodos "bajos" (H4). Los 5 nodos H4 restantes cuelgan de la viga
de anillo entre dos pilotes (luces de 1.2–2.5 m, triviales para una viga de amarre
reforzada con las cargas tan bajas de §6 — esto es carga de un domo liviano, no de
una losa pesada).

- Pilote: concreto, sección mínima sugerida 25×25 cm, profundidad según el estudio
  de suelo pendiente — como punto de partida razonable en terreno de montaña con
  buena capacidad portante, 60–80 cm; en terreno con relleno o cercano a la quebrada,
  más profundo y a confirmar por el ingeniero.
- Cabeza del pilote por encima del nivel de terreno/crecida esperado (freeboard) —
  valor a definir con el estudio hidrológico pendiente de la ubicación exacta dentro
  del balneario; como referencia de partida, no menos de 40–60 cm sobre el nivel de
  suelo circundante.

### 9.4 Anclaje mecánico (perno por nodo)

Con las cargas ilustrativas de §6.2/6.3 y factores de seguridad conservadores
(2.5 a tracción, 2.0 a corte, más un factor de concentración 1.5× sobre el promedio
para no diseñar todos los nodos por el caso promedio):

| | Valor |
|---|---|
| Succión de diseño por perno (nodo crítico) | ≈274 kgf (2 685 N) — *auditoría: con presión interna, 129 kgf × 2.5 ≈ **322 kgf*** |
| Corte lateral de diseño por perno (nodo crítico) | ≈66 kgf (647 N) — *auditoría: con el reparto real, 56 kgf × 2.0 ≈ **113 kgf*** |
| Perno recomendado | M12 galvanizado, con gancho en L o placa/tuerca de anclaje en el extremo embebido (**no** un perno recto liso — la resistencia a arranque de un perno liso depende solo de fricción, mucho menos confiable) |
| Capacidad a fluencia del acero del perno (verificación) | ≈2 078 kgf — **7.6× el uplift de diseño** |

El acero del perno no es lo que limita — un M12 sobra por resistencia propia. Lo que
sí gobierna es el **arranque del concreto** (cuánto perno queda embebido, y con qué
resistencia del concreto), que depende de `f'c` real y de la geometría del pilote —
esto es justo lo que falta cerrar con el ingeniero. Como punto de partida: embebido
mínimo 20–25 cm con gancho/placa, nunca un perno recto solo por fricción.

Los 5 nodos H5 (los altos del zigzag) llevan además el **taco/riser de 4.86 cm**
definido en §4, soldado entre la cabeza del pilote y el nodo del domo.

### 9.5 Entablado (deck)

Superficie plana a nivel de los 10 nodos "bajos", con los 5 tacos de 4.86 cm de
§4 sobresaliendo en los nodos H5 — así el entablado se instala plano y parejo, y
solo los 5 puntos de anclaje del domo quedan un poco más altos, no toda una zona
del deck.

- Vigas secundarias entre pilotes, entablado de madera tratada o deck compuesto por
  encima.
- Dejar una zona de transición/borde alrededor del anillo de 6.00 m para que el
  entablado no termine exactamente en el borde del domo — da margen para ajuste en
  obra y para la terraza/fogatero exterior ya contemplada en el concepto original.

### 9.6 Pendiente antes de construir

- [ ] Estudio de suelo (capacidad portante, nivel freático, cercanía a la quebrada) — define profundidad y sección real de los pilotes
- [ ] Estudio hidrológico puntual del sitio exacto dentro del balneario — define el freeboard real, no el valor ilustrativo de §9.3
- [ ] `f'c` real del concreto a usar — define el embebido real del perno de anclaje (§9.4)
- [ ] Revisión del ingeniero estructural, integrando esto con las cargas combinadas viento+sismo+peso propio (§6.2/6.3) y el diseño del anclaje del domo a la plataforma

---

## 10. Pendientes / próximos pasos

**Cálculo puro — resuelto en este documento:**
- [x] Peso total de la estructura y carga por nodo de fundación (§6.1)
- [x] Patronaje de los paneles de membrana — solo 2 formas distintas (§5.1)
- [x] Empuje y succión de viento — **estimación ilustrativa** con V=100 km/h supuesta, no con el dato oficial de sitio (§6.2)
- [x] Fuerza sísmica horizontal — **estimación ilustrativa** con Ao=0.30 supuesto, no con el mapa oficial de zonificación (§6.3)
- [x] Verificación independiente de toda la geometría y los totales publicados, con programa reproducible (§8) — todos los chequeos pasan
- [x] Simulación de secuencia de armado pieza por pieza, con checklist barra por barra (§8.3, `secuencia_de_armado.md`)

**Con esto, todos los cálculos puramente geométricos y de carga que identificamos
como posibles con la información disponible están resueltos, y hay un concepto de
plataforma/anclaje (§9).** Lo que queda ya no es "cálculo pendiente" sino datos de
sitio oficiales + decisiones de diseño + verificación profesional:

- [ ] Reemplazar los valores ilustrativos de viento (§6.2) y sismo (§6.3) por los datos oficiales de COVENIN-MINDUR 2003 y COVENIN 1756 para Tovar en cuanto estén disponibles
- [ ] Estudio de suelo y estudio hidrológico puntual del sitio (§9.6) — definen profundidad de pilotes, freeboard real y `f'c` del concreto
- [ ] Verificación estructural final por ingeniero matriculado (incluye combinación de cargas viento+sismo+peso propio, y el anclaje a tensión de §9.4)

**Detectado en la auditoría — no estaba en ninguna lista (ver `auditoria/AUDITORIA.md`):**
- [x] **Puerta.** Diseñada y verificada en §11: portal con techo de vestíbulo, vano
      libre de 117.9 × 207.5 cm.
- [ ] **Altura útil.** Solo el 32% del piso (9.1 m²) tiene 2.0 m o más de altura libre.
      Los domos comerciales de glamping de 6 m suelen ser más altos (5/8 de esfera o
      montados sobre un muro).
- [ ] **Carga de la plataforma** (personas, cama y muebles, unos 200 kgf/m², cerca de 6 t) y
      pilotes interiores. El jacuzzi va afuera, con fundación propia.
- [ ] **Arranque de pilotes** frente al levantamiento neto de viento con presión interna.

**Decisión de diseño — no es cálculo, requiere elegir entre opciones:**
- [ ] En cuál de los 5 tramos iguales va la puerta (hacia la terraza; §11.1)
- [ ] Diseño físico del hub plate (diámetro de disco, patrón de pernos o muñones, espesor final — los ángulos ya están en §3)
- [ ] Altura del riser/taco en los 5 nodos altos (H5) — el desnivel exacto (4.86 cm) ya está calculado en §4 y el concepto de pilote+taco en §9.4, falta solo la decisión final de detalle de fijación

**No es cálculo — investigación de mercado:**
- [ ] Cotización real de tubo galvanizado 32×2mm y de la membrana (PVC/poliéster) en talleres venezolanos

## 11. Puerta — portal de acceso (diseño)

Diseño completo en `dome_door.py`, que además lo verifica (`python3 dome_door.py`). El
plano de taller (`domo-3v-cucuchica.html`, generado con `python3 dome_viewer.py`) tiene
los dibujos, las plantillas de nodo y el plan de corte con la puerta incluida.

### 11.1 Concepto

El domo mide 2.52 m en el centro y baja hasta el piso en el borde, así que una puerta de
2 m no cabe en la superficie. La solución es un **marco de puerta vertical** con un
pequeño **techo de vestíbulo** que entra al domo hasta donde el techo ya pasa de 2 m:

- **Ubicación:** centrada sobre uno de los 5 nodos H3 del primer anillo. Los 5 lugares
  son idénticos por simetría. En los planos va a 36°, sobre el nodo #3.
  Elegir el que mire a la terraza del jacuzzi y, si se puede, que no quede de frente al
  viento dominante.
- **Postes:** verticales, sobre los anclajes **#6 y #14 que ya existen**. No hay anclajes
  nuevos. Entre ejes quedan 122.89 cm, el largo de una barra B.
- **Dintel:** eje a 210 cm del piso. El marco (2 postes y dintel) es de
  **tubo cuadrado 50×50×2**, soldado en taller como una sola pieza.
- **Umbral:** la barra B del piso entre #6 y #14 se conserva. Amarra la base de los postes.
- **Se quitan** los nodos #3 (H3) y #27 (H1) y sus 10 barras (2 A, 3 B, 5 C).
- **Se agregan** 2 vigas V del techo, desde las esquinas del marco hasta el nodo
  #26, y 4 amarres (K1 al nodo lateral bajo y K2 al lateral alto, de cada lado),
  en tubo 32×2.
- **Vano libre** entre caras del marco: **117.9 × 207.5 cm**. Entra una puerta de 100 × 200 cm con
  su marco y un fijo lateral de unos 15 cm, o una puerta a medida de unos 115 × 205 cm.
- **Techo del vestíbulo:** cae 13% hacia la puerta. Lleva gotero o canalito sobre el dintel.

### 11.2 Todas las piezas con la puerta (centro a centro, y corte con 5 cm de retiro como ejemplo)

| Pieza | Qué es | Tubo | Cant. | Centro a centro (cm) | Corte (cm) |
|---|---|---|---|---|---|
| A | barra A del domo | tubo redondo 32x2 | 48 | 125.59 | 115.59 |
| B | barra B del domo | tubo redondo 32x2 | 37 | 122.89 | 112.89 |
| C | barra C del domo | tubo redondo 32x2 | 25 | 106.16 | 96.16 |
| V | viga del techo del vestíbulo | tubo redondo 32x2 | 2 | 200.25 | 190.25 |
| K1 | amarre marco–nodo lateral bajo | tubo redondo 32x2 | 2 | 123.68 | 113.68 |
| K2 | amarre marco–nodo lateral alto | tubo redondo 32x2 | 2 | 152.97 | 142.97 |
| P | poste del marco | tubo cuadrado 50x50x2 | 2 | 210.00 | 212.50 |
| D | dintel del marco | tubo cuadrado 50x50x2 | 1 | 122.89 | 117.89 |

El poste se mide desde el eje del nodo de anclaje hasta el tope del marco: hay que restar
el detalle de la placa base. El dintel va entre las caras interiores de los postes.

**Tubo necesario con la puerta** (barras de 6 m, 3 mm de disco, al menos 20 mm de
sobra en cada barra): 24 barras de 32×2 con 3.5 cm de retiro,
23 con 5.0 cm y 23 con 6.5 cm, más **1 barra de 50×50×2** para el marco. El
plan barra por barra está en el plano de taller.

### 11.3 Nodos especiales

Con la puerta, 7 nodos del domo cambian y aparecen 2 esquinas de marco. Quedan H1 ×16,
H2 ×3, H3 ×5, H4 ×8 y H5 ×5. Los especiales se hacen de a pares: el "-der" es la imagen
espejo del "-izq", mirando la puerta desde afuera. Inclinación positiva = la pestaña sale
hacia afuera del disco.

| Tipo | Nodos | Barras en orden alrededor del disco (inclinación) | Azimut a marcar entre pestañas |
|---|---|---|---|
| PA | #6-izq, #14-der | B (-11.6°) · P (+9.9°) · B (-11.6°) · A (-11.9°) | 87.94° · 23.44° · 62.15° (+ abierto) |
| PB | #2-izq, #16-der | K1 (+42.4°) · A (-11.9°) · B (-11.6°) · A (-11.9°) · B (-11.6°) | 57.75° · 62.15° · 62.15° · 62.15° · 115.78° |
| PC | #29-der, #36-izq | K2 (+27.2°) · A (-11.9°) · A (-11.9°) · A (-11.9°) · A (-11.9°) · A (-11.9°) | 34.63° · 60.00° · 60.00° · 60.00° · 60.00° · 85.37° |
| PD | #26 | V (+12.3°) · V (+12.3°) · A (-11.9°) · B (-11.6°) · C (-10.0°) · B (-11.6°) · A (-11.9°) | 36.60° · 43.85° · 62.15° · 55.69° · 55.69° · 62.15° · 43.85° |

**PE, esquinas del marco (#46-izq, #47-der).** No llevan disco: las pestañas se
sueldan a la esquina del marco. El ángulo en planta se mide desde el dintel, girando
hacia adentro del domo; la pendiente, respecto a la horizontal.

| Pieza | Va a | Largo c-c (cm) | En planta | Pendiente |
|---|---|---|---|---|
| K1 | #2 | 123.68 | 126.0° | -58.5° |
| P | #6 | 210.00 | vertical | -90.0° |
| V | #26 | 200.25 | 72.0° | +6.8° |
| K2 | #36 | 152.97 | 108.1° | -7.6° |
| D | #47 | 122.89 | 0.0° | +0.0° |

### 11.4 Verificación (`python3 dome_door.py`)

- **Paso libre:** se revisó barra por barra (como tubos) y panel por panel. Nada invade
  el paso de 117 cm × 207 cm desde la puerta hasta donde el domo ya da esa altura.
- **Membrana:** queda cerrada. Se quitan 9 paneles (5.35 m²) y se agregan 7 del vestíbulo
  (5.95 m²), en total 46.84 m² netos. El plano de taller trae los lados de cada panel nuevo.
- **Estabilidad:** cada nodo no anclado tiene 3 barras o más no coplanares, y la matriz de
  rigidez no es singular.
- **Armadura espacial:** peso propio, 100 kg en el ápice o colgados del dintel, y viento
  ilustrativo de 100 km/h desde 12 direcciones, con la puerta cerrada (interna ±0.18) y
  abierta (interna = 0.9 × la externa en el vano). La barra más exigida llega al
  **9% de su capacidad**. El desplazamiento máximo es de 0.6 mm.
- **Anclajes:** con la puerta, el arranque máximo pasa de 113 a **128 kgf** y el corte
  máximo de 59 a **94 kgf**, en los anclajes de los postes. El perno M12 sigue
  sobrando unas 8 veces por acero. El embebido y el peso de los pilotes los define el
  ingeniero.
- **Flexión del marco** por viento sobre la puerta cerrada: 23 MPa en los postes de
  50×50. En tubo redondo 32×2 serían unos 104 MPa: por eso el marco va en tubo cuadrado.

### 11.5 Armado

La secuencia (`secuencia_de_armado.md`) ya incluye la puerta. En el paso 5, a
2.10 m, se presenta el marco soldado en taller, se aploma y se amarra con K1 y K2.
Las vigas V entran en el paso 6. Con la puerta, los nodos #2 y #16 del paso 2 aparecen como
bisagra hasta que se suelda la barra hacia su vecino del mismo anillo: hay que sujetarlos
mientras tanto.

---

*Documento generado a partir de cálculo geométrico numérico verificado (icosaedro →
subdivisión 3V → proyección esférica → corte y clasificación de aristas/nodos). La
geometría se reprodujo de forma independiente en la auditoría del 2026-09-24. Las
correcciones de esa auditoría están marcadas en el texto y resumidas en
`auditoria/AUDITORIA.md`.*
