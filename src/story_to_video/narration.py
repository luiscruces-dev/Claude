"""Síntesis de voz (narración) usando la API REST de ElevenLabs.

Se usa la API REST directamente (en vez del SDK oficial) para no depender de
una versión concreta del paquete `elevenlabs`: el endpoint de texto-a-voz es
estable desde hace años. Verifica https://elevenlabs.io/docs/api-reference
si algo cambia.
"""

from __future__ import annotations

from pathlib import Path

import requests

API_BASE = "https://api.elevenlabs.io/v1"


class NarrationError(RuntimeError):
    pass


def synthesize_speech(
    text: str,
    *,
    api_key: str,
    voice_id: str,
    out_path: Path,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> Path:
    """Genera un audio de narración y lo guarda en `out_path` (mp3)."""

    url = f"{API_BASE}/text-to-speech/{voice_id}"
    response = requests.post(
        url,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        },
        timeout=120,
    )
    if response.status_code != 200:
        raise NarrationError(
            f"ElevenLabs devolvió {response.status_code}: {response.text[:500]}"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)
    return out_path


def estimate_cost_usd(text: str, *, price_per_1k_chars_usd: float) -> float:
    return (len(text) / 1000.0) * price_per_1k_chars_usd
