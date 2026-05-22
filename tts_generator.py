"""Generate audio chunks from a podcast script using Gemini TTS multi-speaker."""

import io
import os
import wave

from google import genai
from google.genai import types

from config import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    AUDIO_SAMPLE_WIDTH,
    GEMINI_TTS_MODEL,
    SPEAKERS,
    TTS_CHUNK_SIZE,
)


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(AUDIO_CHANNELS)
        wf.setsampwidth(AUDIO_SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _parse_sample_rate(mime_type: str) -> int:
    if "rate=" in mime_type:
        try:
            return int(mime_type.split("rate=")[1].split(";")[0].strip())
        except ValueError:
            pass
    return AUDIO_SAMPLE_RATE


def _build_speaker_configs() -> list:
    return [
        types.SpeakerVoiceConfig(
            speaker=spk["name"],
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=spk["voice"]
                )
            ),
        )
        for spk in SPEAKERS
    ]


def _generate_chunk(turns: list[dict], client: genai.Client) -> bytes:
    text = "\n".join(f"{t['speaker']}: {t['text']}" for t in turns)

    response = client.models.generate_content(
        model=GEMINI_TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=_build_speaker_configs()
                )
            ),
        ),
    )

    part = response.candidates[0].content.parts[0]
    pcm_data: bytes = part.inline_data.data
    sample_rate = _parse_sample_rate(part.inline_data.mime_type)
    return _pcm_to_wav(pcm_data, sample_rate)


def generate_audio_chunks(
    script: list[dict], output_dir: str, api_key: str
) -> list[str]:
    """Split script into chunks, call TTS for each, save as WAV files."""
    client = genai.Client(api_key=api_key)
    chunk_paths = []

    for i in range(0, len(script), TTS_CHUNK_SIZE):
        chunk_turns = script[i : i + TTS_CHUNK_SIZE]
        chunk_idx = i // TTS_CHUNK_SIZE
        print(f"  Generating audio chunk {chunk_idx + 1} "
              f"(turns {i + 1}–{i + len(chunk_turns)})…")

        wav_bytes = _generate_chunk(chunk_turns, client)
        path = os.path.join(output_dir, f"chunk_{chunk_idx:03d}.wav")
        with open(path, "wb") as f:
            f.write(wav_bytes)
        chunk_paths.append(path)

    return chunk_paths
