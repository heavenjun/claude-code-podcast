"""Entrypoint: orchestrate research → script → TTS → upload for one new version."""

import json
import os
import sys
import traceback

from config import DRIVE_FOLDER_NAME, OUTPUT_DIR
from version_tracker import get_unprocessed_release, save_processed_version
from researcher import research_version
from script_generator import generate_script
from tts_generator import generate_audio_chunks
from audio_processor import combine_chunks_to_mp3
from drive_uploader import upload_podcast


def _write_github_env(key: str, value: str) -> None:
    env_file = os.environ.get("GITHUB_ENV")
    if env_file:
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def _write_github_output(key: str, value: str) -> None:
    out_file = os.environ.get("GITHUB_OUTPUT")
    if out_file:
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    gemini_api_key = os.environ["GEMINI_API_KEY"]
    client_id = os.environ["GOOGLE_CLIENT_ID"]
    client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
    refresh_token = os.environ["GOOGLE_REFRESH_TOKEN"]

    # ── 1. Check for new version ──────────────────────────────────────────
    print("Checking for unprocessed Claude Code releases…")
    release = get_unprocessed_release()
    if release is None:
        print("No new versions found. Nothing to do.")
        _write_github_output("new_version", "false")
        return

    version = release["tag_name"]
    release_notes = release.get("body") or ""
    published_at = (release.get("published_at") or "")[:10]  # YYYY-MM-DD
    folder_name = f"{version}_{published_at}" if published_at else version

    print(f"New version: {version}  (published: {published_at})")
    _write_github_env("VERSION", version)
    _write_github_env("OUTPUT_FOLDER", folder_name)
    _write_github_output("new_version", "true")

    output_dir = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # ── 2. Research ───────────────────────────────────────────────────────
    research_path = os.path.join(output_dir, "research.json")
    script_path = os.path.join(output_dir, "script.json")
    mp3_path = os.path.join(output_dir, "podcast.mp3")

    try:
        print("Step 1/5 – Researching release…")
        research_data = research_version(version, release_notes, gemini_api_key)
        with open(research_path, "w", encoding="utf-8") as f:
            json.dump(research_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {research_path}")

        # ── 3. Script ─────────────────────────────────────────────────────
        print("Step 2/5 – Generating podcast script…")
        script = generate_script(research_data, gemini_api_key)
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {script_path}  ({len(script)} turns)")

        # ── 4. TTS ────────────────────────────────────────────────────────
        print("Step 3/5 – Generating audio chunks via TTS…")
        chunk_paths = generate_audio_chunks(script, output_dir, gemini_api_key)
        print(f"  Generated {len(chunk_paths)} audio chunk(s).")

        # ── 5. Combine ────────────────────────────────────────────────────
        print("Step 4/5 – Combining chunks into MP3…")
        combine_chunks_to_mp3(chunk_paths, mp3_path)

        # ── 6. Drive upload ───────────────────────────────────────────────
        print("Step 5/5 – Uploading to Google Drive…")
        result = upload_podcast(mp3_path, folder_name, client_id, client_secret, refresh_token)
        _write_github_env("DRIVE_LINK", result.get("webViewLink", ""))

        # ── 7. Mark as processed ──────────────────────────────────────────
        save_processed_version(version)
        print(f"\nDone! Podcast for {version} generated and uploaded.")

    except Exception:
        print("\n[ERROR] Pipeline failed. Intermediate files (if any) are preserved.")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
