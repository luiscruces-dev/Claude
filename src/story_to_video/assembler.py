"""Ensamblaje final con ffmpeg: sincroniza audio+video por escena y concatena.

Los clips de video generados por IA suelen tener una duración fija (p. ej.
8s) que rara vez coincide exactamente con la narración. Este módulo:

  1. Empareja cada clip de video con su audio de narración, congelando el
     último frame del video si el audio dura más (`tpad`), o recortando el
     video si dura menos.
  2. Concatena todas las escenas ya emparejadas en un único video final.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List


class AssemblyError(RuntimeError):
    pass


def _run(cmd: List[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise AssemblyError(
            f"Comando falló ({' '.join(cmd)}):\n{result.stderr[-2000:]}"
        )


def probe_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssemblyError(f"ffprobe falló para {path}:\n{result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def build_scene_clip(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    """Combina `video_path` + `audio_path` ajustando la duración del video
    a la del audio (narración manda la duración de la escena)."""

    video_duration = probe_duration_seconds(video_path)
    audio_duration = probe_duration_seconds(audio_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if audio_duration > video_duration:
        pad_seconds = audio_duration - video_duration
        video_filter = f"tpad=stop_mode=clone:stop_duration={pad_seconds:.3f}"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-shortest",
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-t",
            f"{audio_duration:.3f}",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(out_path),
        ]

    _run(cmd)
    return out_path


def concatenate_scenes(scene_paths: List[Path], out_path: Path) -> Path:
    if not scene_paths:
        raise AssemblyError("No hay escenas para concatenar.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    filelist_path = out_path.with_suffix(".filelist.txt")
    filelist_path.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in scene_paths), encoding="utf-8"
    )
    try:
        _run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(filelist_path),
                "-c",
                "copy",
                str(out_path),
            ]
        )
    finally:
        filelist_path.unlink(missing_ok=True)
    return out_path
