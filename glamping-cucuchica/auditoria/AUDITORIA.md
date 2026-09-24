# Auditoría independiente — Domo 3V Cucuchica

**Fecha:** 2026-09-24 · **Alcance:** todo lo que hay en `glamping-cucuchica/`:
`domo-3v-cucuchica.md`, el visor HTML, `dome_model.py`, `dome_verify.py`,
`dome_build_sequence.py`, `secuencia_de_armado.md` y `reporte_verificacion.txt`.

**Cómo se hizo:** se escribió un programa nuevo,
[`auditoria_independiente.py`](./auditoria_independiente.py), que **no** usa
`dome_model.py`. Construye el icosaedro por otro camino, subdivide, corta, escala y
recalcula todo desde cero. Además resuelve el domo como armadura espacial por el
método de rigidez directa, con equilibrio verificado, usando las mismas cargas
ilustrativas del documento. La salida completa está en
[`auditoria_salida.txt`](./auditoria_salida.txt) y los datos en
`auditoria_datos.json`.

```bash
cd glamping-cucuchica/auditoria
python3 auditoria_independiente.py     # Python estándar, sin instalar nada, ~2 s
python3 reporte_visual.py              # regenera reporte_auditoria.html (reporte visual)
```

> **Actualización (mismo día):** después de la auditoría se **diseñó la puerta**
> (`../dome_door.py`, §11 del documento) y se **rehízo el plano de taller**
> (`../domo-3v-cucuchica.html`, generado con `../dome_viewer.py`) con todas las
> correcciones y la puerta incluida. El jacuzzi va en la terraza exterior con fundación
> propia. Los hallazgos de abajo describen el domo tal como estaba publicado, sin puerta.

---

## Veredicto en una línea

**La geometría es correcta, pero con los documentos anteriores el domo no se podía
fabricar ni armar sin errores.** Los ángulos para marcar los discos de nodo, el retiro
de corte de los tubos y las alturas de armado estaban mal, y la membrana estaba
subpresupuestada. Todo eso ya se corrigió. Quedan sin diseñar ni calcular la puerta,
la plataforma y los pilotes: hay que resolverlos antes de comprometer dinero.

| | Cantidad |
|---|---|
| ✅ Datos confirmados como correctos | Toda la geometría y la aritmética de cargas (tabla de §1) |
| 🔴 Errores altos (bloquean fabricación o seguridad) | 4 (E1–E4), todos corregidos |
| 🟠 Errores medios (dinero o riesgo) | 5 (E5–E9), corregidos o anotados |
| 🟡 Errores bajos (textos o cifras sin impacto físico) | 3 (E10–E12), corregidos o anotados |
| ⚪ Cosas que no están calculadas y cuestan dinero | 8 |

---

## 1. Lo que está bien (confirmado de forma independiente)

Todos estos valores del `.md` los reprodujo el cálculo independiente, con diferencias
por debajo de 0.1 mm o 0.01 m²:

| Dato | Publicado | Recalculado | |
|---|---|---|---|
| Radio de la esfera R | 3.0452 m | 3.0452 m | ✅ |
| Altura del ápice sobre el piso | 2.5225 m | 2.5225 m | ✅ |
| Barra A (cantidad) | 125.59 cm (50) | 125.587 cm (50) | ✅ |
| Barra B (cantidad) | 122.89 cm (40) | 122.888 cm (40) | ✅ |
| Barra C (cantidad) | 106.16 cm (30) | 106.160 cm (30) | ✅ |
| Tubo total | 143.80 m | 143.797 m | ✅ |
| Nodos H1/H2/H3/H4/H5 | 20/5/6/10/5 | 20/5/6/10/5 | ✅ |
| Paneles P1/P2 | 45/30 | 45/30 | ✅ |
| Área de membrana | 46.24 m² | 46.243 m² | ✅ |
| Área de piso | 28.274 m² | 28.274 m² | ✅ |
| Desnivel del zigzag | 4.86 cm | 4.858 cm | ✅ |
| Radio de los nodos altos | 2.9911 m | 2.9911 m | ✅ |
| Perímetro del borde | 18.70 m | 18.703 m | ✅ |
| Inclinación de barras A/B/C | 11.90°/11.64°/10.04° | ídem | ✅ |
| Ángulos 3D entre barras | 54.63°/60.71°/58.58°/70.73° | ídem | ✅ (pero ver E1) |
| Lista de corte en barras de 12 m | 13 barras | 13 (es el óptimo) | ✅ |
| Peso del domo | 278 kg | 278.4 kg (suma de reacciones) | ✅ |
| Viento: q, empuje lateral, succión | 473 Pa · 330 kgf · 1091 kgf | ídem | ✅ aritmética |
| Sismo: 0.30 × W | 83.5 kgf | ídem | ✅ aritmética |
| Perno M12 a fluencia | 2078 kgf | ≈2062 kgf | ✅ (diferencia de 1%) |

Los números coinciden con las tablas estándar de un domo 3V de 3/8 de esfera (46
nodos, 120 barras, 75 caras; factores de cuerda 0.41241 / 0.40355 / 0.34862 × R).
**La geometría no tiene errores.**

---

## 2. Errores encontrados

### 🔴 E1 — Ángulos para marcar el disco del nodo (§3 del .md y diagramas del HTML)

**Qué decía:** que los ángulos entre barras (54.63°, 60.71°, 58.58°, 70.73°) "son
directamente los ángulos a marcar alrededor del disco". El HTML los dibujaba como
plantilla "transportable con transportador", con una cuña de "cierre cónico" para lo
que sobraba.

**Por qué está mal:** esos son ángulos **3D** entre dos tubos, medidos en el plano que
forman los dos tubos. Como los tubos bajan 10–12° respecto al disco, esos ángulos suman
menos de 360° (entre 351.5° y 353.7°) y en un disco plano no cierran. En un disco
tangente a la esfera se marca el **azimut** (el ángulo proyectado sobre el disco), que
suma exactamente 360°.

| Nodo | Ángulo 3D (publicado) | **Azimut a marcar (correcto)** | Error por pestaña |
|---|---|---|---|
| H1 | 54.63 / 60.71 | **55.69 / 62.15** | +1.06° / +1.45° |
| H2 | 58.58 | **60.00** | +1.42° |
| H3 | 70.73 | **72.00** | +1.27° |
| H4 | 54.63 / 60.71 | **55.69 / 62.15** | +1.06° / +1.45° |
| H5 | 58.58 | **60.00** | +1.42° |

**Impacto:** 1.45° de error en una pestaña desplaza unos **3.2 cm** el otro extremo de
una barra A. Con 46 discos fabricados así, el domo no cierra sin forzar o recortar, y se
pierden las 46 piezas y su soldadura.

**Corregido en:** §3 del `.md` (tabla nueva de azimuts), diagramas del HTML (ahora
dibujan el azimut y el 3D queda solo como dato de verificación).

### 🔴 E2 — Retiro de corte en cada extremo del tubo (§2)

**Qué decía:** que al largo de centro a centro hay que restarle "típicamente entre 1 y
3 cm por extremo".

**Por qué está mal:** con tubo de 32 mm, donde dos barras forman 54.63° (nodos H1 y H4)
los tubos se tocan hasta **3.1 cm** del centro del nodo. Un retiro de 1–3 cm hace que los
tubos choquen físicamente. Con el disco de ⌀13 cm propuesto en §3, el tubo empieza en el
borde del disco, a unos **6.5 cm**.

| Retiro por extremo | Corte A | Corte B | Corte C |
|---|---|---|---|
| 3.5 cm (mínimo práctico) | 118.59 cm | 115.89 cm | 99.16 cm |
| 5.0 cm | 115.59 cm | 112.89 cm | 96.16 cm |
| 6.5 cm (disco de ⌀13 cm) | 112.59 cm | 109.89 cm | 93.16 cm |

**Impacto:** si se corta siguiendo el documento, las 120 barras quedan largas. Recortarlas
cuesta tiempo, y si el retiro se estima mal hacia el otro lado, se pierde material.

**Acción:** diseñar el conector **antes** de cortar un solo tubo. Corregido en §2 del
`.md` y en el HTML.

### 🔴 E3 — Alturas de armado 52.3 cm más altas (`secuencia_de_armado.md`)

**Qué decía:** "Paso 1 — Anillo a 1.362 m de altura" … "Paso 6 — Anillo a 3.045 m".

**Por qué está mal:** el generador medía la altura desde el **centro de la esfera**, no
desde el piso. El piso está 52.27 cm por encima de ese centro. El mismo documento decía
en el paso 6 que el ápice está a 3.045 m, y en §1 que está a 2.5225 m.

| Paso | Decía | **Altura real sobre el piso** |
|---|---|---|
| 1 | 1.362 m | **0.839 m** |
| 2 | 1.568 m | **1.045 m** |
| 3 | 2.214 m | **1.691 m** |
| 4 | 2.420 m | **1.897 m** |
| 5 | 2.860 m | **2.337 m** |
| 6 (ápice) | 3.045 m | **2.522 m** |

**Impacto:** puntales, andamios o gálibos de armado preparados con esas cifras quedan
medio metro fuera de lugar.

**Corregido en:** `dome_build_sequence.py`, y `secuencia_de_armado.md` regenerado.

### 🔴 E4 — "0 nodos necesitan sujeción temporal" es falso (§8.3 y secuencia)

**Qué decía:** que en cada paso cada nodo nuevo queda fijo por "al menos 2 barras no
paralelas" y que por eso el domo se arma sin apuntalar.

**Por qué está mal:** ese criterio sirve en 2D. En 3D un nodo articulado sostenido por 2
barras es una **bisagra**: gira alrededor de la línea entre sus dos apoyos. Hacen falta 3
barras no coplanares.

**Resultado con el criterio correcto:** en el paso 1, los 5 triángulos que se levantan
sobre la base (nodos H3 #0, #3, #7, #13 y #20) quedan colgando como aletas: pueden caer
hacia adentro o hacia afuera hasta que el paso 2 los amarre. Los demás nodos sí quedan
fijos, aunque con barras muy tendidas (entre 9° y 17° fuera del plano de sus apoyos).
Conviene apuntalar hasta cerrar cada anillo.

**Impacto:** seguridad del personal el día del armado (un triángulo de acero que cae) y
logística (hacen falta 5 puntales o cuerdas).

**Corregido en:** `dome_build_sequence.py`, que ahora exige 3 barras no coplanares,
marca los 5 nodos y numera bien "1ª de 2", "2ª de 2". Antes todas las filas decían "2ª
barra". También en §8.3 del `.md`.

### 🟠 E5 — Faltaba el replanteo de los 15 anclajes (§9.2)

**Qué decía:** que las posiciones angulares de los 15 nodos estaban en
`secuencia_de_armado.md` (Paso 0). **No estaban:** esa tabla solo traía el número de nodo,
el tipo y la altura relativa.

**Corregido:** el Paso 0 ahora trae azimut, radio y coordenadas X/Y de cada anclaje. Los
valores coinciden al milímetro con el cálculo independiente:

| Tipo | Azimut | Radio | X | Y | Altura sobre el piso |
|---|---|---|---|---|---|
| H5 alto | 0° · 72° · 144° · 216° · 288° | 2.9911 m | — | — | +4.86 cm |
| H4 bajo | 24.181° · 47.819° · 96.181° · 119.819° · 168.181° · 191.819° · 240.181° · 263.819° · 312.181° · 335.819° | 3.0000 m | — | — | 0 |

Las coordenadas X/Y de cada uno están en `secuencia_de_armado.md`.

### 🟠 E6 — La membrana no alcanza (§5)

**Qué decía:** 46.24 m² × 1.12 = **51.79 m²** a comprar, cortando 75 paneles con 2
plantillas "más el margen de costura".

**Por qué está mal:** cada panel mide unos 3.5 m de perímetro. El solape de costura o de
soldadura de alta frecuencia se suma en todo ese perímetro:

| Solape por lado | Área de las piezas cortadas | vs. los 51.79 m² presupuestados |
|---|---|---|
| 0 cm | 46.2 m² | 89% |
| 2 cm | 51.8 m² | 100% (no deja nada para el desperdicio del rollo) |
| 3 cm | 54.7 m² | **106%** |
| 5 cm | 60.7 m² | **117%** |

Eso sin contar el desperdicio al acomodar los triángulos en un rollo de ancho fijo.
**Presupuestar ~60–67 m²** o pedir cotización al fabricante con su propio patronaje.

**Tampoco estaban en la lista de materiales:** aislante, forro interior, ventanas
(PVC transparente), puerta con cierre, ni el faldón perimetral que tapa el hueco de
4.86 cm bajo el zigzag.

### 🟠 E7 — Viento: reparto real por anclaje y presión interna (§6.2 y §9.4)

La aritmética del `.md` está bien. Lo que falta:

1. **Presión interna.** Todas las normas de viento suman la presión interna a la
   externa. Una puerta o ventana abierta hacia el viento presuriza el domo desde adentro
   (Cpi ≈ +0.55) y eso se suma a la succión de la cresta. El `.md` no la considera.
2. **Cp de cresta −0.8.** Para cúpulas rebajadas como esta (flecha/diámetro ≈ 0.42) los
   valores habituales en la cresta son del orden de −1.0 a −1.2.
3. **El reparto entre los 15 anclajes no es parejo.** La auditoría resolvió la
   armadura con un patrón de cúpula (barlovento +0.6, cresta −1.1, sotavento −0.4). Ese
   patrón da exactamente el mismo empuje lateral total del `.md` (330.8 kgf), así que es
   coherente con sus supuestos:

| Caso (V = 100 km/h) | Arranque máx. por anclaje | Corte máx. por anclaje | Arranque neto total |
|---|---|---|---|
| `.md`: succión uniforme −0.8 | 70.5 kgf | 6.8 kgf | 1057 kgf |
| Patrón de cúpula | 80.5 kgf | **56.4 kgf** | 791 kgf |
| Patrón de cúpula + presión interna +0.55 | **128.9 kgf** | **56.9 kgf** | **1517 kgf** |
| 0.9 × peso propio + lo anterior | 112.1 kgf | 56.1 kgf | 1267 kgf |

**Comparado con la base de diseño de §9.4** (mismos factores de seguridad del `.md`):

| | §9.4 decía | Con presión interna y reparto real |
|---|---|---|
| Arranque de diseño por perno | 274 kgf | **≈322 kgf** (128.9 × 2.5) |
| Corte de diseño por perno | 66 kgf | **≈113 kgf** (56.4 × 2.0) |

**Lo que no cambia:** el perno M12 sigue sobrando por resistencia del acero (≈2000 kgf).
**Lo que sí cambia:** la longitud embebida, el arranque del concreto y, sobre todo, que
los pilotes y la viga pesen lo suficiente para no levantarse. El arranque neto de
**1.3–1.5 t** es comparable al peso de los 10 pilotes de 25×25×130 cm (≈1.95 t). No hay
margen de sobra: lo tiene que verificar el ingeniero.

### 🟠 E8 — Lista de corte en barras de 6 m (§2.1)

- El patrón publicado **9×[B,B,B,B,C] deja solo 7.9 mm de sobra por barra.** Una barra
  comercial que venga en 5.99 m, un extremo dañado o un disco de corte más grueso y la
  quinta pieza sale corta.
- Con largos de centro a centro, el óptimo matemático son 25 barras, pero depende de
  ese mismo patrón ajustado. Exigiendo 20 mm de holgura en cada barra, **27 es
  correcto.**
- **Con el largo real de corte** (E2), bastan **23 barras de 6 m** con al menos 20 mm
  de holgura en cada una. Son 4 barras menos (24 m de tubo, unos 35 kg). Ejemplo con 3.5
  cm de retiro: 10×[A,B,B,B,B] · 8×[A×5] · 5×[C×6]. Recalcular cuando el conector
  esté definido.

### 🟠 E9 — Galvanizado contra soldadura en sitio (§6)

El `.md` dice "galvanizar después de soldar" y la secuencia de armado dice que el domo
se **suelda en sitio**, anillo por anillo. Las dos cosas no pueden ser ciertas a la vez:
las uniones soldadas en obra quedan sin zinc. Hay que elegir entre:

- Uniones **empernadas**, con piezas galvanizadas en caliente después de soldar en
  taller.
- Soldadura en sitio con reparación en frío (pintura rica en zinc) en cada unión.

Además, los tubos cerrados necesitan **agujeros de venteo** para el baño en caliente. Un
tubo sellado puede reventar dentro de la cuba.

### 🟡 E10 — "2.7 toneladas" no es una capacidad de diseño (§6)

Es la carga crítica **elástica** de Euler. Con esbeltez KL/r ≈ 118, la barra A pandea en
rango inelástico. La capacidad de diseño según AISC 360 es **≈1.3–2.1 t**, según el
método (ASD o LRFD) y el acero (Fy 228–290 MPa). **Conclusión práctica sin cambios:** la
armadura resuelta da como máximo ≈121 kgf de compresión (peso propio más una persona en
el ápice), un 5% de la capacidad. La sección 32×2 alcanza como barra axial.

**Pero ojo con la flexión:** una persona de 100 kg parada a media barra A la lleva a
≈231 MPa, prácticamente en fluencia. **Nadie puede caminar sobre las barras** durante el
armado ni al instalar la membrana. Hace falta andamio. Esto quedó escrito en la
secuencia.

### 🟡 E11 — Afirmaciones del verificador que no son ciertas (§8)

- "Dos implementaciones distintas del mismo método": `dome_verify.py` y
  `dome_build_sequence.py` importan el **mismo** `dome_model.py`. La primera
  verificación realmente independiente es esta auditoría.
- "Si alguien edita un número en este `.md` a mano, este chequeo lo detectaría": falso.
  `dome_verify.py` compara contra números copiados dentro del script y no lee el `.md`.
- `reporte_verificacion.txt` informa sumas de ángulos de 352.00° / 351.60° / 353.50°
  porque suma ángulos redondeados a 0.1°. El `.md` dice 352.10° / 351.48° / 353.65°. No es
  un error de geometría, pero confunde.

### 🟡 E12 — Otros detalles de texto

- "La diferencia de **12–19 cm** entre tipos": en realidad es de 2.70 cm (A−B), 16.73 cm
  (B−C) y 19.43 cm (A−C). Corregido.
- "Volumen interior 44.07 m³" es el del casquete **esférico**. El poliedro real, de caras
  planas, encierra **41.2 m³** (−6.5%). Anotado aquí, sin impacto en la estructura.
- La numeración interna de nodos del visor HTML **no coincide** con la de
  `secuencia_de_armado.md`. El visor no muestra números, así que el taller no se va a
  confundir, pero para el taller vale solo la numeración de la secuencia. Advertido en
  el HTML.
- La plancha de "~0.6 m²" cubre solo los 46 discos. Las 240 pestañas (2 por barra) suman
  unos 0.77 m² más si son de 40×80 mm.

---

## 3. Lo que no está calculado y cuesta dinero (antes de firmar o comprar)

Esta es la lista de lo que el proyecto **todavía no ha calculado ni diseñado**:

1. **Puerta** — ✅ **resuelto después de la auditoría.** Portal con marco de 50×50×2
   sobre los anclajes existentes #6 y #14, techo de vestíbulo hasta el nodo #26 y vano
   libre de 117.9 × 207.5 cm. Se quitan los nodos #3 y #27 (10 barras) y se agregan 9
   piezas. Está verificado en `../dome_door.py`: paso libre, estabilidad, y armadura con
   viento en 12 direcciones y puerta abierta o cerrada. La barra más exigida trabaja al 9%.
   El corte en los anclajes de los postes sube de 59 a 94 kgf y el perno M12 sigue
   sobrando. **Altura útil:** sin cambios. Solo 9.1 m² (32% del piso) tienen 2.0 m o más.
   Si hiciera falta más espacio de pie, las opciones siguen siendo 5/8, 4V o un muro de
   arranque.
2. **Plataforma y pilotes** — ✅ **resuelto después de la auditoría** (`../dome_platform.py`,
   §9.6 del documento). Son 23 pilotes con zapata: uno bajo cada anclaje, 6 interiores y 2
   del descanso de entrada. Llevan viga de anillo de concreto 25×30, vigas de tubo
   100×50×3 y viguetas 2×4" cada 40 cm, con 200 kgf/m² en la habitación. El jacuzzi va
   afuera, con fundación propia. Queda pendiente el estudio de suelo: la capacidad de 1.0
   kgf/cm² y la profundidad de zapata son supuestos.
3. **Arranque de pilotes** — ✅ **resuelto con el mismo diseño.** El peso que sujeta cada
   anclaje (viga de anillo, pilote, zapata y relleno) es ≈5.9 veces el arranque del viento
   con puerta.
4. **Diseño del conector (hub).** De él dependen el retiro de corte (E2), la lista de
   corte (E8), el galvanizado (E9) y la resistencia de las uniones. Es probable que la
   unión sea el eslabón débil, no el tubo, y **no está calculada.**
5. **Lista de materiales incompleta:** pestañas, soldadura, pernos de unión y de anclaje
   con placas y tuercas, tacos de 4.86 cm, concreto (≈0.8 m³ de pilotes con las medidas de §9.3, más la viga de
   anillo, ≈0.9 m³ si es de 20×25 cm), madera o deck, aislante, forro, ventanas, puerta y faldón.
6. **Grado real del tubo local.** El cálculo supone acero estructural tipo ASTM A500.
   Hay que confirmar con el proveedor el Fy, el espesor real de pared (con su
   tolerancia de fabricación) y el diámetro exacto disponible (por ejemplo, 1¼" = 31.75
   mm).
7. **Datos oficiales de viento y sismo** (COVENIN-MINDUR 2003 y COVENIN 1756) para
   Tovar, incluyendo el efecto de la topografía de montaña sobre el viento. En sismo, el
   modelo de barras da un período de ≈0.02 s: el domo es tan rígido que el `Ao × W` del
   `.md` es un orden de magnitud razonable. Donde el sismo importa es en la
   **plataforma** (jacuzzi y pilotes cortos), y eso no está calculado.
8. **Revisión de un ingeniero estructural matriculado**, como ya decía el `.md`. Esta
   auditoría confirma y corrige números. No reemplaza esa firma.

---

## 4. Qué se cambió en el repositorio

| Archivo | Cambio |
|---|---|
| `auditoria/auditoria_independiente.py` | **Nuevo.** Verificación independiente, armadura espacial, azimuts, corte óptimo, replanteo, membrana, altura útil. |
| `auditoria/AUDITORIA.md` | **Nuevo.** Este informe. |
| `auditoria/auditoria_salida.txt`, `auditoria_datos.json` | **Nuevos.** Salida del programa. |
| `auditoria/reporte_visual.py`, `reporte_auditoria.html` | **Nuevos.** Reporte visual con diagramas a escala (discos de nodo, choque de tubos, alturas, planta de anclajes, membrana, viento por anclaje, lista de corte, altura libre), generado a partir de los datos. |
| `dome_build_sequence.py` | Alturas desde el piso; estabilidad 3D (3 barras no coplanares); ordinal correcto ("1ª de 2"); tabla de replanteo en el Paso 0; aviso de no pisar barras. |
| `secuencia_de_armado.md` | Regenerado con lo anterior. |
| `domo-3v-cucuchica.md` | Recuadro de auditoría al inicio y correcciones marcadas en el texto (§2, §2.1, §3, §4, §5, §6, §6.2, §8, §8.3, §9.2, §9.3, §9.4, §10). |
| `domo-3v-cucuchica.html` | **Rehecho como plano de taller** y generado por `dome_viewer.py`: vista 3D con puerta, piezas y plan de corte para 3 retiros, plantillas de todos los discos de nodo (estándar y de puerta), dibujos de la puerta, replanteo, armado, cubierta, cargas y notas. |
| `dome_door.py` | **Nuevo.** Diseño y verificación de la puerta (portal de acceso). |
| `dome_viewer.py` | **Nuevo.** Generador del plano de taller. |
| `dome_platform.py` | **Nuevo.** Diseño y verificación de la plataforma y los 23 pilotes, con replanteo y materiales. |
| `dome_build_sequence.py` (2ª pasada) | Arma el domo con puerta por defecto (`--sin-puerta` para el cerrado). Distingue si un nodo bisagra se sujeta hasta el paso siguiente o solo hasta soldar las barras del mismo paso. |

No se tocó `dome_model.py`: su geometría es correcta. `dome_verify.py` y
`reporte_verificacion.txt` quedan igual y siguen pasando.

## 5. Límites de esta auditoría

- El análisis de armadura supone **nodos articulados y apoyos fijos**, sin la rigidez de
  la membrana. Da el orden de magnitud de las fuerzas en barras y anclajes, no el diseño
  de las uniones.
- El patrón de presiones de viento es una aproximación típica de cúpulas, ajustada para
  dar el mismo empuje total que el `.md`. **No es un cálculo de norma.** V = 100 km/h
  sigue siendo el valor ilustrativo del `.md`, no el dato oficial del sitio.
- La capacidad de las barras se calculó con AISC 360 como referencia, con Fy de 228 y
  290 MPa. La norma venezolana aplicable la definirá el ingeniero.
