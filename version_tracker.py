"""Track which Claude Code versions have already been processed."""

import json
import os
import requests
from config import GITHUB_REPO, PROCESSED_VERSIONS_FILE


def _get_releases_from_github() -> list | None:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=15,
        )
        if resp.status_code == 200:
            releases = resp.json()
            if releases:
                return releases
        print(f"GitHub Releases returned status {resp.status_code}")
    except Exception as e:
        print(f"GitHub Releases API error: {e}")
    return None


def _get_releases_from_npm() -> list:
    """Fallback: derive version list from npm registry."""
    url = "https://registry.npmjs.org/@anthropic-ai/claude-code"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        time_map = data.get("time", {})

        releases = []
        for version in sorted(data.get("versions", {}).keys(), reverse=True):
            published_raw = time_map.get(version, "")
            published_at = (published_raw[:10] + "T00:00:00Z") if published_raw else "1970-01-01T00:00:00Z"
            releases.append(
                {
                    "tag_name": f"v{version}",
                    "name": f"Claude Code v{version}",
                    "published_at": published_at,
                    "body": data.get("versions", {}).get(version, {}).get("description", ""),
                }
            )
        return releases[:30]
    except Exception as e:
        print(f"npm registry API error: {e}")
    return []


def get_all_releases() -> list:
    releases = _get_releases_from_github()
    if releases is None:
        print("Falling back to npm registry for version info…")
        releases = _get_releases_from_npm()
    return releases


def load_processed_versions() -> list:
    if os.path.exists(PROCESSED_VERSIONS_FILE):
        with open(PROCESSED_VERSIONS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_processed_version(version: str) -> None:
    processed = load_processed_versions()
    if version not in processed:
        processed.append(version)
    with open(PROCESSED_VERSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)
    print(f"Marked {version} as processed.")


def get_unprocessed_release() -> dict | None:
    """Return the latest release that has not yet been processed, or None."""
    releases = get_all_releases()
    processed = load_processed_versions()
    for release in releases:
        if release["tag_name"] not in processed:
            return release
    return None
