# Cuentos a Video

Pipeline en Python que convierte un cuento en texto en un video narrado con
IA:

```
cuento.txt --(Claude)--> guion por escenas --(ElevenLabs)--> narración
                                            --(Google Veo)--> clip de video
                                            --(ffmpeg)------> video final
```

1. **Guion por escenas** ([`script_breakdown.py`](src/story_to_video/script_breakdown.py)):
   Claude (`claude-opus-5`) divide el cuento en escenas cortas, cada una con
   el texto exacto a narrar y un prompt visual detallado, manteniendo
   consistencia de personajes/escenario entre escenas.
2. **Narración** ([`narration.py`](src/story_to_video/narration.py)): cada
   texto de escena se convierte a voz con la API de ElevenLabs (voz fija de
   narrador, o una voz clonada).
3. **Video por escena** ([`video_providers/veo.py`](src/story_to_video/video_providers/veo.py)):
   cada prompt visual se convierte en un clip con Google Veo (vía la API de
   Gemini). El proveedor de video está detrás de una interfaz
   ([`video_providers/base.py`](src/story_to_video/video_providers/base.py))
   para poder agregar Runway/Kling/etc. sin tocar el resto del pipeline.
4. **Ensamblaje** ([`assembler.py`](src/story_to_video/assembler.py)): con
   `ffmpeg`, cada clip de video se ajusta a la duración de su narración
   (congelando el último frame si el audio dura más, recortando si dura
   menos) y luego se concatenan todas las escenas en el video final.

## Por qué estos proveedores

- **Claude**: ya lo tenemos disponible en este entorno; es un buen "director
  de guion" porque entiende narrativa y puede mantener consistencia de
  personajes entre escenas si se le pide explícitamente.
- **ElevenLabs**: el estándar de facto en narración por voz con IA; permite
  clonar una voz de narrador y reutilizarla en todos los cuentos.
- **Google Veo**: al momento de escribir esto, el modelo con mejor
  seguimiento de instrucciones y el único con audio nativo sincronizado
  entre los grandes generadores de video (Veo, Runway, Kling, Seedance).
  Runway Gen-4.5 (más control creativo) o Kling 3.0 (mejor para 9:16 /
  redes sociales) son alternativas razonables — cambiar de proveedor solo
  requiere implementar `VideoProvider` para ese servicio.

**Nota sobre Sora**: la API de Sora de OpenAI se discontinúa el 24 de
septiembre de 2026, por lo que no se incluyó como opción.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements-dev.txt   # o requirements.txt sin dev
```

Necesitas también `ffmpeg` instalado en el sistema (`apt-get install ffmpeg`
en Debian/Ubuntu).

## Configuración

```bash
cp .env.example .env
```

Completa en `.env`:

| Variable | De dónde sale |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` | [elevenlabs.io](https://elevenlabs.io) |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `GOOGLE_VEO_MODEL` | ID exacto del modelo Veo — **verifícalo en la [documentación de video de Gemini](https://ai.google.dev/gemini-api/docs/video)**, cambia entre versiones (Veo 2/3/3.1...) |

## Uso

**Paso 1 - probar el guion sin gastar dinero en video/audio** (`--dry-run`
solo llama a Claude, que es barato, y muestra el desglose de escenas + costo
estimado del video completo):

```bash
python -m story_to_video.cli --story stories/ejemplo.txt --dry-run
```

**Paso 2 - generar el video completo** (esto sí gasta en ElevenLabs y Veo):

```bash
python -m story_to_video.cli --story stories/mi_cuento.txt --output output/mi_cuento.mp4
```

Los archivos intermedios (audio y video por escena) quedan en
`output/mi_cuento_work/` por si quieres revisarlos o reusarlos.

Opciones útiles: `--scene-seconds` (duración objetivo por escena, default 8),
`--aspect-ratio 9:16` (para redes sociales verticales, default `16:9`).

## Costos aproximados (referencia, verifica precios actuales)

| Servicio | Precio aprox. |
|---|---|
| Claude (guion) | Centavos por cuento — el texto de entrada/salida es pequeño |
| ElevenLabs (narración) | ~$0.05–$0.10 por cada 1,000 caracteres narrados |
| Google Veo Standard (video) | ~$0.40 por segundo de clip generado |
| Google Veo Lite (video) | ~$0.05–$0.08 por segundo |

Ejemplo: un cuento de 6 escenas de 8s (48s de video) con Veo Standard ronda
los **$19 USD** solo en video; con Veo Lite baja a **~$3–4 USD**. Ajusta
`VEO_PRICE_PER_SECOND_USD` en `.env` si usas un tier distinto.

## Pruebas

```bash
python -m pytest -v
```

- `tests/test_script_breakdown.py` prueba la lógica de guion con un cliente
  Claude simulado (no llama a la API real).
- `tests/test_assembler.py` ejercita `ffmpeg` de verdad, generando clips de
  audio/video de prueba localmente (sin red) para validar el ensamblaje.

No hay pruebas automáticas contra ElevenLabs ni Google Veo reales: requieren
claves de API de pago y no están cubiertas aquí para evitar gastos
accidentales. Antes de usar el pipeline en serio, corre `--dry-run` primero
y genera un cuento corto de prueba (1-2 escenas) para validar tus claves y
el ID de modelo de Veo.

## Agregar otro proveedor de video (Runway, Kling, ...)

Implementa `VideoProvider` (`generate_clip`, `estimate_cost_usd`) en
`src/story_to_video/video_providers/`, siguiendo el patrón de `veo.py`, y
pásalo a `render_video()` en vez de `VeoProvider`. El resto del pipeline
(guion, narración, ensamblaje) no cambia.
