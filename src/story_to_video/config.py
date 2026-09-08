"""Carga de configuración desde variables de entorno / archivo .env."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class MissingConfigError(RuntimeError):
    """Falta una variable de entorno requerida para el paso solicitado."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingConfigError(
            f"Falta la variable de entorno {name}. Copia .env.example a .env y complétala."
        )
    return value


@dataclass(frozen=True)
class ScriptConfig:
    anthropic_api_key: str
    model: str = "claude-opus-5"

    @classmethod
    def from_env(cls) -> "ScriptConfig":
        return cls(anthropic_api_key=_require("ANTHROPIC_API_KEY"))


@dataclass(frozen=True)
class NarrationConfig:
    elevenlabs_api_key: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    price_per_1k_chars_usd: float = 0.10

    @classmethod
    def from_env(cls) -> "NarrationConfig":
        return cls(
            elevenlabs_api_key=_require("ELEVENLABS_API_KEY"),
            voice_id=_require("ELEVENLABS_VOICE_ID"),
            price_per_1k_chars_usd=float(
                os.environ.get("ELEVENLABS_PRICE_PER_1K_CHARS_USD", "0.10")
            ),
        )


@dataclass(frozen=True)
class VideoConfig:
    google_api_key: str
    model: str
    price_per_second_usd: float = 0.40

    @classmethod
    def from_env(cls) -> "VideoConfig":
        return cls(
            google_api_key=_require("GOOGLE_API_KEY"),
            model=_require("GOOGLE_VEO_MODEL"),
            price_per_second_usd=float(
                os.environ.get("VEO_PRICE_PER_SECOND_USD", "0.40")
            ),
        )
