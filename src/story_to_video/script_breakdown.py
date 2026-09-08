"""Convierte el texto de un cuento en un guion escena por escena usando Claude.

Cada escena trae el texto exacto que se narrará en voz alta y una descripción
visual pensada como prompt para un generador de video (Veo/Runway/Kling...).
"""

from __future__ import annotations

from typing import List, Protocol

import anthropic
from pydantic import BaseModel, Field

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_SCENE_SECONDS = 8

SYSTEM_PROMPT = """\
Eres un guionista experto en adaptar cuentos infantiles/narrativos a video.
Dado el texto completo de un cuento, lo divides en escenas cortas pensadas \
para generar un clip de video por escena con un modelo de IA (tipo Veo/Runway).

Reglas:
- Cada escena debe durar aproximadamente {scene_seconds} segundos de narración \
hablada (ajusta el texto de narración a ese ritmo, ni más largo ni más corto).
- "narration_text" es el texto EXACTO que se leerá en voz alta para esa escena \
(en el mismo idioma del cuento original). No resumas de más: conserva el tono \
y las palabras clave del cuento.
- "visual_prompt" describe la escena para un generador de video: personajes, \
acción, ambientación, iluminación, estilo visual y encuadre. Sé concreto y \
visual, no repitas la narración.
- Mantén consistencia de apariencia de personajes y escenario entre escenas \
(descríbelos con los mismos detalles clave cada vez que aparezcan).
- No incluyas texto en pantalla ni diálogos leídos por otro locutor: todo el \
audio hablado sale de "narration_text" como narración en off.
"""


class Scene(BaseModel):
    scene_number: int = Field(description="Número de escena, empezando en 1")
    narration_text: str = Field(description="Texto exacto a narrar en esta escena")
    visual_prompt: str = Field(
        description="Prompt visual detallado para el generador de video"
    )
    duration_hint_seconds: int = Field(
        description="Duración objetivo aproximada de la escena en segundos"
    )


class Screenplay(BaseModel):
    title: str
    scenes: List[Scene]


class MessagesParseClient(Protocol):
    """Lo mínimo que necesitamos de un cliente Anthropic (facilita el testeo)."""

    messages: object


def generate_screenplay(
    client: anthropic.Anthropic,
    story_text: str,
    *,
    model: str = DEFAULT_MODEL,
    scene_seconds: int = DEFAULT_SCENE_SECONDS,
) -> Screenplay:
    """Pide a Claude que divida `story_text` en un `Screenplay` estructurado."""

    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT.format(scene_seconds=scene_seconds),
        messages=[{"role": "user", "content": story_text}],
        output_format=Screenplay,
    )
    return response.parsed_output
