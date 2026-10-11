# Nike — "TOO LATE" · spot de 15 s

**Entregable:** `nike_jdi_15s.mp4`. H.264 High, 1080×1920, 60 fps, 900 fotogramas, 15,000 s, AAC estéreo a 320 kbps y 48 kHz, −11,6 LUFS.
**Origen:** todo sale de código Python (skia para el vector, numpy/scipy para el audio y ffmpeg solo para codificar). No se usó ninguna skill, ningún modelo generativo ni ningún sample.

---

## 1. La idea

**Las excusas se acaban cuando aparece el swoosh.**

Un corazón late solo en negro. Las excusas van entrando con el pulso, cada vez más rápido: *TOO EARLY · TOO COLD · TOO TIRED · TOO LATE*. Justo antes del drop hay una semicorchea de silencio total. Entonces el swoosh entra y **corta "TOO LATE" por la mitad**, y las dos mitades salen despedidas. A partir de ahí el spot es movimiento puro (pista, bote, aceleración) hasta llegar a **JUST / DO / IT.**, una palabra por golpe. El punto final de "IT." es **el mismo punto que latía en el primer fotograma**: vuelve a latir una vez y el swoosh firma el cierre.

El subtexto ("nunca es demasiado tarde") no aparece escrito en ningún momento. Lo cuenta el corte.

## 2. Estructura (150 BPM)

Elegí 150 BPM porque así la semicorchea dura exactamente 0,1 s, es decir, **6 fotogramas enteros a 60 fps**. Todos los golpes caen sobre un fotograma exacto sin redondear.

| Tiempo | Pasos | Plano | Audio | Qué se sincroniza |
|---|---|---|---|---|
| 0,0–1,6 s | 0–15 | Latido: punto blanco y anillos | Latido "lub-dub" sintetizado y dron oscuro | Cada lub/dub hincha el punto y emite un anillo |
| 1,6–3,1 s | 16–30 | 4 excusas, cada una en su plano | Tick metálico FM, latido al doble de tempo, redoble y riser | Corte por palabra. El temblor crece con cada semicorchea del redoble |
| 3,1 s | 31 | Negro | **Silencio absoluto** (también se corta la reverb) | Respiración |
| 3,2 s | 32 | **DROP**: el swoosh volt corta "TOO LATE" | Bombo grande, 808 y crash | Corte, shake y aberración cromática en el fotograma 192 |
| 3,6 s | 36 | Inversión a fondo volt | Palmada | Inversión de color |
| 3,8 s | 38 | Las mitades salen despedidas | Bombo | Aceleración de salida |
| 4,2 s | 42 | El swoosh sale disparado | Bombo | Látigo de salida |
| 4,4–6,4 s | 44–63 | Pista en perspectiva con tu calle en volt | Groove completo | **Bombo = zancada** (empujón de velocidad y bajada de cámara). **Palmada = una línea de meta llega a cámara justo en ese fotograma**, con flash |
| 6,4–8,0 s | 64–79 | Pelota sobre volt | Groove sobre Db | **Cada bote cae en un bombo** (squash). Palmada = inversión de color. Al final la pelota viene a cámara y tapa el cuadro |
| 8,0–9,4 s | 80–93 | Montaje de swooshes: rejilla, macro, columna, giro, túnel | Subida: bombo a negras, redoble y riser | Corte cada corchea y después **cada semicorchea** (6 fotogramas) |
| 9,4 s | 94–95 | Negro | Silencio | Respiración |
| 9,6 / 10,0 / 10,4 s | 96 / 100 / 104 | **JUST / DO / IT.** | Tres stabs: Db → Eb → Fm | Cada palabra golpea en su stab |
| 10,8 s | 108 | El punto de "IT." late | Latido (callback) | Pulso del punto y anillo |
| 11,2 s | 112 | Firma: el swoosh se dibuja con flash y onda expansiva | Whoosh, impacto, boom y acorde de **Fa mayor** (cadencia picarda) | Fotograma 672 |
| 12,0 s | 120 | "JUST DO IT." sube letra a letra | Pluck brillante | Fotograma 720 |
| 12–15 s | — | Cierre con push-in lento | Cola de reverb hasta el final | — |

Audio y vídeo leen los eventos de **un único archivo, `timeline.py`**. Así la sincronía es correcta por construcción y no depende de ajustarla a mano.

## 3. Decisiones de diseño

- **Paleta:** negro, blanco y Volt (#D4FF00), el amarillo eléctrico de Nike. Solo tres colores, para que cada inversión de color funcione como un golpe.
- **Logo:** `./brand/nike-swoosh.svg` no existía en el repo. **Redibujé el swoosh en vector** con trazado SVG fiel (gancho, vientre y hoja afilada), lo guardé en `brand/nike-swoosh.svg` y todo el spot lee ese archivo. Escribí un parser SVG propio (`svgpath.py`) que admite arcos.
- **Tipografía:** no hay ninguna Futura Condensed instalada y no quise descargar fuentes. **Dibujé en código un alfabeto propio** (`font.py`): una grotesca geométrica condensada ultra-negra con contraste real entre verticales (0,225) y horizontales (0,165), y kerning manual (LA, AT, LY…). Solo dibujé las 13 letras que el guion necesita.
- **Wordmark "NIKE":** lo descarté a propósito. Hoy el cierre de Nike es el swoosh solo, más "JUST DO IT.". Añadir el wordmark habría restado fuerza al final.
- **El punto como hilo conductor:** el latido inicial, el indicador bajo las excusas y el punto de "IT." son el mismo objeto.
- **El corte:** la línea de corte es exactamente el filo superior de la hoja del swoosh. Las mitades del texto resbalan a lo largo de ese filo y el swoosh queda encajado entre ellas.
- **Pista:** tu calle va en volt y el resto en blanco ("your lane"). La velocidad se lee en las marcas de escalonado, que con motion blur dejan estela.

## 4. Motion blur real, sin mezclar planos

- Cada fotograma integra **24 submuestras temporales** dentro de un obturador de **216°** (0,6 fotograma). Se acumulan **en luz lineal** (LUT sRGB→lineal→sRGB), no en sRGB, para que las estelas tengan la densidad correcta.
- Todos los cortes caen en el límite exacto de un fotograma. Las 24 submuestras de cada fotograma se evalúan **siempre con el plano de ese fotograma**, así que ningún fotograma mezcla dos planos. Lo verifiqué extrayendo del MP4 final los pares de fotogramas anterior y posterior a los 21 cortes.
- Extras de acabado: aberración cromática solo en los 5 impactos, camera shake con ruido suave, y grano fino que también sirve de dithering contra el banding.

## 5. Música (sintetizada desde cero en `music.py`)

- **Instrumentos:** bombo (seno con barrido de pitch y click), 808 con glide y saturación, palmada (4 ráfagas de ruido filtrado), hats, redoble, latido, tick metálico FM, supersaws limitados en banda con filtro de envolvente, pad, riser, whoosh, boom y crash.
- **Reverb:** convolución con una respuesta al impulso **sintetizada** (ruido filtrado con decaimiento exponencial). No se usó ningún IR grabado.
- **Mezcla:** sidechain de la música con cada bombo, ensanche Haas en los agudos, silencios absolutos antes de los dos drops y saturación tanh normalizada. Resultado: −11,6 LUFS integrados.
- **Armonía:** Fa menor durante el groove (Fm7 → Fm → Db → Eb). La tagline sube Db → Eb → Fm y el cierre resuelve en **Fa mayor add9**. Esa cadencia picarda es el momento de optimismo del spot.

## 6. Descartado

- **Fuente descargada** (Anton, Oswald…): la cambié por rotulación propia, para que todo fuera código y tuviera más carácter.
- **Copy en castellano** ("DEMASIADO TARDE"): las palabras son demasiado largas para dos líneas justificadas en 9:16, y la tagline de la marca es en inglés.
- **Línea de ECG** en el intro: es un cliché. Me quedé con el punto y los anillos.
- **Pista naranja de tartán:** introducía un cuarto color. La pista es negra con tu calle en volt.
- **Wordmark NIKE en el cierre** (ver arriba).
- **Fundido de whoosh antes del drop:** el silencio total golpea más.
- **Cortes desde el negro al inicio:** el spot arranca ya en el primer latido, en el fotograma 0.

## 7. Iteraciones

1. **Swoosh:** primer dibujo vectorial y comparación visual con la silueta oficial.
2. **Alfabeto:** la D tenía un escalón junto al asta. Lo corregí con un radio del 80 % y añadí pares de kerning.
3. **Primera hoja de contactos:** las excusas salían duplicadas ("TOO / TOO EARLY") y el volt se veía **cian** porque skia trabaja en BGRA. Arreglé las dos cosas forzando RGBA.
4. **Aberración cromática:** `np.roll` repetía píxeles del borde opuesto. La cambié por un desplazamiento que replica el borde.
5. **El corte:** en la v1 solo se veía la hoja fina y parecía una cuña sin marca. En la v2 el swoosh era más grande, pero el vientre seguía fuera de cuadro. En la **v3** el swoosh entra entero (1180 px, rotado 12°) y corta la frase entre las dos líneas.
6. **Túnel:** estaba anclado en el centro geométrico y quedaba descentrado. Lo anclé en el vientre del swoosh y ahora se lee como un vórtice.
7. **Audio v1:** −6,4 LUFS, convertido en un ladrillo; los silencios previos a los drops se llenaban de reverb y los stabs se solapaban. En la **v2** muteé el bus master en los silencios (reverb incluida), sequé los stabs y bajé la saturación hasta −11,6 LUFS.
8. **Impacto final:** el primer fotograma de la firma era casi negro. Añadí un flash blanco seco de unos 3 fotogramas, una onda expansiva y una entrada del swoosh más rápida (0,13 s).
9. **Revisión del MP4 final:**
   - ffprobe: 1080×1920, 60/1, 900 fotogramas, 15,000 s.
   - Decodificación completa sin errores.
   - Hoja de contactos de todo el spot.
   - Pares de fotogramas en cada corte.
   - `check_sync.py`, que detecta transitorios de audio y saltos de imagen alrededor de cada evento:
     - **Audio:** 28 de 31 eventos caen a ±1 fotograma en el MP4. Los 3 restantes (100, 104 y 108) los marca el detector porque la cola del stab anterior enmascara el ataque. Medidos directamente en el WAV, los onsets de 96/100/104 caen a ≤7 ms del instante previsto y el de 108 a unos −21 ms, todavía dentro de ±1 fotograma.
     - **Imagen:** todos los cortes caen a 0 fotogramas. Los eventos marcados (0, 8, 42, 58, 74, 108 y 120) son de movimiento sin corte (latidos, zancada, botes, salida en *ease-in* del swoosh, revelado escalonado de letras): ahí el golpe arranca en su fotograma, pero el mayor cambio de píxeles llega 2–3 fotogramas después. El corte de 80 sale de un zoom que ya tapa el cuadro antes del corte.

## 8. Tiempo total

**~37 minutos** de reloj, de 21:28 a 22:05 UTC, incluyendo los dos renders completos de unos 8 minutos cada uno (4 núcleos, 21.600 renders vectoriales por pasada).

## 9. Reproducir

```bash
pip install skia-python numpy scipy pillow   # y ffmpeg en el sistema
python3 music.py music.wav
python3 render.py music.wav nike_jdi_15s.mp4
python3 check_sync.py nike_jdi_15s.mp4
```
