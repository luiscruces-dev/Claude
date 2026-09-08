"""Orquesta el pipeline completo: cuento (texto) -> video final (mp4)."""

from __future__ import annotations

from pathlib import Path
from typing import List

import anthropic

from . import assembler, narration
from .config import NarrationConfig, ScriptConfig, VideoConfig
from .script_breakdown import Screenplay, generate_screenplay
from .video_providers.base import VideoProvider


def estimate_total_cost_usd(
    screenplay: Screenplay,
    *,
    narration_price_per_1k_chars_usd: float,
    video_price_per_second_usd: float,
) -> float:
    total = 0.0
    for scene in screenplay.scenes:
        total += narration.estimate_cost_usd(
            scene.narration_text,
            price_per_1k_chars_usd=narration_price_per_1k_chars_usd,
        )
        total += scene.duration_hint_seconds * video_price_per_second_usd
    return total


def break_story_into_screenplay(
    story_text: str, script_config: ScriptConfig, *, scene_seconds: int = 8
) -> Screenplay:
    client = anthropic.Anthropic(api_key=script_config.anthropic_api_key)
    return generate_screenplay(
        client, story_text, model=script_config.model, scene_seconds=scene_seconds
    )


def render_video(
    screenplay: Screenplay,
    *,
    video_provider: VideoProvider,
    narration_config: NarrationConfig,
    work_dir: Path,
    output_path: Path,
    aspect_ratio: str = "16:9",
) -> Path:
    """Genera narración + clip por escena, los empareja y concatena todo."""

    work_dir.mkdir(parents=True, exist_ok=True)
    scene_clip_paths: List[Path] = []

    for scene in screenplay.scenes:
        scene_id = f"scene_{scene.scene_number:03d}"

        audio_path = work_dir / f"{scene_id}_narration.mp3"
        narration.synthesize_speech(
            scene.narration_text,
            api_key=narration_config.elevenlabs_api_key,
            voice_id=narration_config.voice_id,
            out_path=audio_path,
            model_id=narration_config.model_id,
        )

        raw_video_path = work_dir / f"{scene_id}_raw.mp4"
        video_provider.generate_clip(
            scene.visual_prompt,
            duration_seconds=scene.duration_hint_seconds,
            out_path=raw_video_path,
            aspect_ratio=aspect_ratio,
        )

        final_scene_path = work_dir / f"{scene_id}_final.mp4"
        assembler.build_scene_clip(raw_video_path, audio_path, final_scene_path)
        scene_clip_paths.append(final_scene_path)

    return assembler.concatenate_scenes(scene_clip_paths, output_path)
