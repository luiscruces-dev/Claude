"""Interfaz común para proveedores de generación de video (Veo, Runway, Kling...).

Nueva IA de video = una clase nueva que implemente `generate_clip`; el resto
del pipeline (guion, narración, ensamblaje) no cambia.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class VideoProviderError(RuntimeError):
    pass


class VideoProvider(ABC):
    @abstractmethod
    def generate_clip(
        self,
        prompt: str,
        *,
        duration_seconds: int,
        out_path: Path,
        aspect_ratio: str = "16:9",
    ) -> Path:
        """Genera un clip de video para `prompt` y lo guarda en `out_path`."""

    @abstractmethod
    def estimate_cost_usd(self, duration_seconds: int) -> float:
        """Estimación de costo en USD para un clip de esa duración."""
