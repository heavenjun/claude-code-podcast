"""Generate a podcast dialogue script from research data using Gemini."""

import json
from google import genai
from google.genai import types
from config import SPEAKERS, PODCAST_TOPIC, GEMINI_SCRIPT_MODEL


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()


def generate_script(research: dict, api_key: str) -> list[dict]:
    client = genai.Client(api_key=api_key)

    host = SPEAKERS[0]["name"]  # 田中
    guest = SPEAKERS[1]["name"]  # 鈴木
    version = research.get("version", "最新版")

    research_text = json.dumps(research, ensure_ascii=False, indent=2)

    prompt = f"""
あなたはポッドキャスト台本ライターです。
以下の調査データをもとに、{host}と{guest}の2人による自然な対話形式の
ポッドキャスト台本を作成してください。

【調査データ】
{research_text}

【登場人物】
- {host}（男性）：技術に詳しいエンジニア。{PODCAST_TOPIC}の機能を分かりやすく解説する役
- {guest}（女性）：技術に興味があるが詳しくない。聴衆の代わりに質問する役

【要件】
- テーマ：{PODCAST_TOPIC} {version} のアップデート内容
- 対話の長さ：30〜40ターン（約1000〜1500語）
- 冒頭に番組紹介、末尾にまとめと次回予告を含める
- 技術的な内容も聴きやすく噛み砕いて説明する
- 自然な会話のテンポ（相槌・驚き・質問を交えて）
- 重要な機能は具体的なユースケースで説明する

以下のJSON配列形式のみで出力してください（余計な説明不要）：
[
  {{"speaker": "{host}", "text": "セリフ"}},
  {{"speaker": "{guest}", "text": "セリフ"}},
  ...
]
"""

    response = client.models.generate_content(
        model=GEMINI_SCRIPT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
        ),
    )

    raw = response.text
    if not raw:
        raise ValueError("Script model returned empty response.")

    raw = _strip_fences(raw)

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Script model did not return valid JSON: {e}\n\nRaw output:\n{raw[:500]}"
        ) from e

    # Validate and filter turns
    valid = []
    speaker_names = {s["name"] for s in SPEAKERS}
    for turn in script:
        if isinstance(turn, dict) and "speaker" in turn and "text" in turn:
            if turn["speaker"] in speaker_names:
                valid.append({"speaker": turn["speaker"], "text": turn["text"]})

    if not valid:
        raise ValueError(
            f"Script generation returned no valid turns. "
            f"Got {len(script)} raw turns with speakers: "
            f"{list({t.get('speaker') for t in script if isinstance(t, dict)})}"
        )

    return valid
