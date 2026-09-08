"""Ejercita ffmpeg de verdad: genera video/audio de prueba localmente (sin red)
y valida que build_scene_clip / concatenate_scenes produzcan la duración
esperada."""

import subprocess

import pytest

from story_to_video import assembler


def _make_test_video(path, seconds: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=duration={seconds}:size=320x240:rate=24",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def _make_test_audio(path, seconds: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={seconds}",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


@pytest.fixture()
def tmp_media(tmp_path):
    video_short = tmp_path / "video_3s.mp4"
    audio_long = tmp_path / "audio_6s.mp3"
    video_long = tmp_path / "video_6s.mp4"
    audio_short = tmp_path / "audio_3s.mp3"
    _make_test_video(video_short, 3)
    _make_test_audio(audio_long, 6)
    _make_test_video(video_long, 6)
    _make_test_audio(audio_short, 3)
    return {
        "video_short": video_short,
        "audio_long": audio_long,
        "video_long": video_long,
        "audio_short": audio_short,
    }


def test_build_scene_clip_pads_video_when_audio_is_longer(tmp_path, tmp_media):
    out_path = tmp_path / "scene_final.mp4"
    assembler.build_scene_clip(tmp_media["video_short"], tmp_media["audio_long"], out_path)

    assert out_path.exists()
    duration = assembler.probe_duration_seconds(out_path)
    assert duration == pytest.approx(6.0, abs=0.2)


def test_build_scene_clip_trims_video_when_video_is_longer(tmp_path, tmp_media):
    out_path = tmp_path / "scene_final.mp4"
    assembler.build_scene_clip(tmp_media["video_long"], tmp_media["audio_short"], out_path)

    assert out_path.exists()
    duration = assembler.probe_duration_seconds(out_path)
    assert duration == pytest.approx(3.0, abs=0.2)


def test_concatenate_scenes_joins_clips(tmp_path, tmp_media):
    scene_a = tmp_path / "scene_a.mp4"
    scene_b = tmp_path / "scene_b.mp4"
    assembler.build_scene_clip(tmp_media["video_short"], tmp_media["audio_long"], scene_a)
    assembler.build_scene_clip(tmp_media["video_long"], tmp_media["audio_short"], scene_b)

    out_path = tmp_path / "final.mp4"
    assembler.concatenate_scenes([scene_a, scene_b], out_path)

    assert out_path.exists()
    duration = assembler.probe_duration_seconds(out_path)
    assert duration == pytest.approx(9.0, abs=0.4)
