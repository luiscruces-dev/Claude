"""CLI: convierte un cuento (.txt) en un video narrado.

Uso:
    python -m story_to_video.cli --story stories/ejemplo.txt --dry-run
    python -m story_to_video.cli --story stories/ejemplo.txt --output output/cuento.mp4
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import MissingConfigError, NarrationConfig, ScriptConfig, VideoConfig
from .pipeline import break_story_into_screenplay, estimate_total_cost_usd, render_video
from .video_providers.veo import VeoProvider


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story", required=True, type=Path, help="Ruta al .txt del cuento")
    parser.add_argument(
        "--output", type=Path, default=Path("output/cuento.mp4"), help="Video final"
    )
    parser.add_argument(
        "--scene-seconds", type=int, default=8, help="Duración objetivo por escena"
    )
    parser.add_argument(
        "--aspect-ratio", default="16:9", choices=["16:9", "9:16"], help="Formato del video"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo genera el guion y muestra el costo estimado, sin llamar a "
        "ElevenLabs ni a Veo (no gasta dinero en esos servicios).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.story.exists():
        print(f"No existe el archivo de cuento: {args.story}", file=sys.stderr)
        return 1
    story_text = args.story.read_text(encoding="utf-8")

    try:
        script_config = ScriptConfig.from_env()
    except MissingConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Generando guion escena por escena con Claude...")
    screenplay = break_story_into_screenplay(
        story_text, script_config, scene_seconds=args.scene_seconds
    )

    print(f"\nTítulo: {screenplay.title}")
    print(f"Escenas: {len(screenplay.scenes)}\n")
    for scene in screenplay.scenes:
        print(f"--- Escena {scene.scene_number} (~{scene.duration_hint_seconds}s) ---")
        print(f"Narración: {scene.narration_text}")
        print(f"Visual: {scene.visual_prompt}\n")

    # El costo de video se estima con el precio por defecto de Veo Standard;
    # ajústalo con VEO_PRICE_PER_SECOND_USD en .env si usas otro tier/proveedor.
    narration_price = float(os.environ.get("ELEVENLABS_PRICE_PER_1K_CHARS_USD", "0.10"))
    video_price = float(os.environ.get("VEO_PRICE_PER_SECOND_USD", "0.40"))
    estimated_cost = estimate_total_cost_usd(
        screenplay,
        narration_price_per_1k_chars_usd=narration_price,
        video_price_per_second_usd=video_price,
    )
    print(f"Costo estimado (narración + video): ~${estimated_cost:.2f} USD")

    if args.dry_run:
        print("\n--dry-run: no se generó audio ni video. Fin.")
        return 0

    try:
        narration_config = NarrationConfig.from_env()
        video_config = VideoConfig.from_env()
    except MissingConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    video_provider = VeoProvider(
        api_key=video_config.google_api_key,
        model=video_config.model,
        price_per_second_usd=video_config.price_per_second_usd,
    )

    work_dir = args.output.parent / f"{args.output.stem}_work"
    print(f"\nGenerando narración + clips de video por escena en {work_dir}...")
    final_path = render_video(
        screenplay,
        video_provider=video_provider,
        narration_config=narration_config,
        work_dir=work_dir,
        output_path=args.output,
        aspect_ratio=args.aspect_ratio,
    )
    print(f"\nListo: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
