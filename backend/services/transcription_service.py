"""Transkription gespeicherter Audiodateien.

V1: deterministische Dummy-Ausgabe.
TODO: OpenAI Whisper API, Azure Speech, oder lokales Modell (z. B. faster-whisper / whisper.cpp)
      anbinden; Sprache/Timeouts/Fehlerbehandlung definieren.
"""


def transcribe_audio(audio_path: str) -> str:
    """Liest eine Audiodatei und liefert Transkript-Text.

    Aktuell wird der Inhalt noch nicht analysiert (`audio_path` nur für spätere Integration).
    """
    _ = audio_path
    return (
        "Dies ist eine simulierte Transkription. Echte Transkription folgt mit OpenAI Whisper."
    )
