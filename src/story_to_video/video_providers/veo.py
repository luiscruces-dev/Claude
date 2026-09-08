"""Proveedor de video usando Google Veo a través de la API de Gemini.

Veo es un modelo de generación de video de larga duración: la API expone un
patrón de "operación asíncrona" (predictLongRunning + polling), documentado
en https://ai.google.dev/gemini-api/docs/video. Ese patrón es estable desde
Veo 2, pero el ID exacto del modelo y algunos nombres de campo cambian entre
versiones (Veo 2 -> Veo 3 -> Veo 3.1...) - por eso este módulo:

  1. No trae un modelo por defecto: se exige `GOOGLE_VEO_MODEL` en el entorno
     para forzar a verificar el ID actual en la documentación oficial.
  2. Falla con un error explícito (en vez de un KeyError críptico) si la
     respuesta de la API no trae la forma esperada, para que sea fácil
     ajustar el parseo si Google cambia el formato.

IMPORTANTE: antes de usar esto en serio, confirma en la documentación actual
de Google el nombre del modelo, los parámetros soportados (duración,
aspect ratio, audio nativo) y la forma exacta de la respuesta.
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

from .base import VideoProvider, VideoProviderError

API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class VeoProvider(VideoProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        price_per_second_usd: float = 0.40,
        poll_interval_seconds: float = 10.0,
        poll_timeout_seconds: float = 600.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.price_per_second_usd = price_per_second_usd
        self.poll_interval_seconds = poll_interval_seconds
        self.poll_timeout_seconds = poll_timeout_seconds

    def _headers(self) -> dict:
        return {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

    def generate_clip(
        self,
        prompt: str,
        *,
        duration_seconds: int,
        out_path: Path,
        aspect_ratio: str = "16:9",
    ) -> Path:
        operation_name = self._start_generation(prompt, duration_seconds, aspect_ratio)
        video_uri = self._poll_until_done(operation_name)
        self._download(video_uri, out_path)
        return out_path

    def estimate_cost_usd(self, duration_seconds: int) -> float:
        return duration_seconds * self.price_per_second_usd

    # -- pasos internos -----------------------------------------------------

    def _start_generation(
        self, prompt: str, duration_seconds: int, aspect_ratio: str
    ) -> str:
        url = f"{API_BASE}/models/{self.model}:predictLongRunning"
        body = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "aspectRatio": aspect_ratio,
                "durationSeconds": duration_seconds,
            },
        }
        resp = requests.post(url, headers=self._headers(), json=body, timeout=60)
        if resp.status_code != 200:
            raise VideoProviderError(
                f"Veo devolvió {resp.status_code} al iniciar la generación: "
                f"{resp.text[:500]}"
            )
        data = resp.json()
        operation_name = data.get("name")
        if not operation_name:
            raise VideoProviderError(
                f"Respuesta inesperada de Veo (sin 'name' de operación): {data}"
            )
        return operation_name

    def _poll_until_done(self, operation_name: str) -> str:
        url = f"{API_BASE}/{operation_name}"
        deadline = time.monotonic() + self.poll_timeout_seconds
        while True:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            if resp.status_code != 200:
                raise VideoProviderError(
                    f"Veo devolvió {resp.status_code} al consultar la operación: "
                    f"{resp.text[:500]}"
                )
            data = resp.json()
            if data.get("done"):
                if "error" in data:
                    raise VideoProviderError(f"Veo reportó un error: {data['error']}")
                return self._extract_video_uri(data)
            if time.monotonic() > deadline:
                raise VideoProviderError(
                    "Se agotó el tiempo de espera esperando el video de Veo."
                )
            time.sleep(self.poll_interval_seconds)

    @staticmethod
    def _extract_video_uri(operation_data: dict) -> str:
        try:
            samples = operation_data["response"]["generateVideoResponse"][
                "generatedSamples"
            ]
            return samples[0]["video"]["uri"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VideoProviderError(
                "No se pudo extraer la URL del video de la respuesta de Veo. "
                "Es probable que el formato de respuesta haya cambiado - revisa "
                f"https://ai.google.dev/gemini-api/docs/video. Respuesta cruda: "
                f"{operation_data}"
            ) from exc

    def _download(self, video_uri: str, out_path: Path) -> None:
        resp = requests.get(video_uri, headers=self._headers(), timeout=120)
        if resp.status_code != 200:
            raise VideoProviderError(
                f"No se pudo descargar el video generado ({resp.status_code})."
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.content)
