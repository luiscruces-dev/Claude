"""Prueba generate_screenplay() con un cliente falso (sin llamar a la API real)."""

from types import SimpleNamespace

from story_to_video.script_breakdown import Screenplay, generate_screenplay


class _FakeParseResponse:
    def __init__(self, parsed_output: Screenplay) -> None:
        self.parsed_output = parsed_output


class _FakeMessages:
    def __init__(self, screenplay: Screenplay) -> None:
        self._screenplay = screenplay
        self.last_call_kwargs: dict = {}

    def parse(self, **kwargs):
        self.last_call_kwargs = kwargs
        return _FakeParseResponse(self._screenplay)


def _make_fake_client(screenplay: Screenplay):
    return SimpleNamespace(messages=_FakeMessages(screenplay))


def test_generate_screenplay_returns_parsed_output():
    expected = Screenplay.model_validate(
        {
            "title": "El zorro y las estrellas de papel",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration_text": "Había una vez un zorro llamado Fuego.",
                    "visual_prompt": "Zorro rojo bajo un cielo estrellado, estilo cuento ilustrado.",
                    "duration_hint_seconds": 8,
                }
            ],
        }
    )
    client = _make_fake_client(expected)

    result = generate_screenplay(client, "texto del cuento", scene_seconds=8)

    assert result == expected
    assert client.messages.last_call_kwargs["output_format"] is Screenplay
    assert client.messages.last_call_kwargs["messages"][0]["content"] == "texto del cuento"
    assert "8 segundos" in client.messages.last_call_kwargs["system"]
