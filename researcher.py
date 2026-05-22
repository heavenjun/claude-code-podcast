"""Research a Claude Code release using Gemini + Google Search Grounding."""

import json
from google import genai
from google.genai import types
from config import PODCAST_TOPIC, GEMINI_RESEARCH_MODEL


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def research_version(version: str, release_notes: str, api_key: str) -> dict:
    client = genai.Client(api_key=api_key)

    prompt = f"""
あなたは技術リサーチャーです。{PODCAST_TOPIC} {version} について以下の観点から徹底的に調査し、
日本語で詳細なレポートを作成してください。

【公式リリースノート】
{release_notes or "（リリースノート未取得）"}

【調査項目】
1. 主な新機能と変更点（具体的なコマンドや設定があれば含める）
2. バグ修正・安定性の改善
3. パフォーマンス・UXの改善
4. 開発者・エンジニアコミュニティの反応（X/Twitterの投稿、技術ブログ、Reddit等）
5. このバージョンの意義・前バージョンとの違い
6. 実際の開発ワークフローへの影響

最新のWeb情報を検索して、できるだけ具体的な情報を含めてください。
以下のJSON形式で出力してください（余計なマークダウン記法は不要）：

{{
  "summary": "このバージョンの概要（2〜3文）",
  "key_features": [
    {{"title": "機能名", "detail": "詳細説明"}}
  ],
  "bug_fixes": ["修正内容1", "修正内容2"],
  "improvements": ["改善内容1", "改善内容2"],
  "community_reactions": [
    {{"source": "情報源（X/Twitter、ブログ等）", "reaction": "反応の要約"}}
  ],
  "significance": "このバージョンの技術的・開発体験上の意義",
  "impact_on_workflow": "開発ワークフローへの具体的な影響"
}}
"""

    response = client.models.generate_content(
        model=GEMINI_RESEARCH_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    raw_text = response.text
    if not raw_text:
        print("Warning: research model returned empty text response.")
        return {"version": version, "release_notes": release_notes, "raw_research": ""}

    raw_text = _strip_fences(raw_text)

    try:
        parsed = json.loads(raw_text)
    except Exception:
        parsed = {"raw_research": raw_text}

    return {
        "version": version,
        "release_notes": release_notes,
        **parsed,
    }
