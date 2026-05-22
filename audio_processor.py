"""Combine WAV chunks into a single MP3 using pydub + FFmpeg."""

import glob
import os

from pydub import AudioSegment


def combine_chunks_to_mp3(chunk_paths: list[str], output_path: str) -> str:
    if not chunk_paths:
        raise ValueError("No audio chunks to combine.")

    combined = AudioSegment.empty()
    for path in sorted(chunk_paths):
        segment = AudioSegment.from_wav(path)
        combined += segment

    combined.export(output_path, format="mp3", bitrate="128k")
    size_kb = os.path.getsize(output_path) // 1024
    duration_sec = len(combined) // 1000
    print(f"  Combined {len(chunk_paths)} chunks → {output_path} "
          f"({duration_sec}s, {size_kb}KB)")
    return output_path
