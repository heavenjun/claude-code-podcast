# Claude Code Podcast Generator

Claude Code の最新バージョンを自動調査し、2人による対話形式ポッドキャストを生成して Google Drive にアップロードする GitHub Actions ワークフローです。

---

## アーキテクチャ

```
GitHub Actions (週次 or 手動)
  │
  ├─ version_tracker.py  ─── GitHub Releases API / npm registry でバージョン確認
  ├─ researcher.py        ─── Gemini + Google Search Grounding で変更点を調査
  ├─ script_generator.py ─── Gemini で対話台本を生成
  ├─ tts_generator.py    ─── Gemini TTS (MultiSpeaker) で音声チャンクを生成
  ├─ audio_processor.py  ─── pydub + FFmpeg でチャンクを結合して MP3 化
  └─ drive_uploader.py   ─── OAuth2 で Google Drive の Podcasts フォルダにアップロード
```

**出力先**

| 種別 | 場所 |
|------|------|
| research.json / script.json | リポジトリ `output/{version}_{date}/` |
| podcast.mp3 | Google Drive `Podcasts/{version}_{date}/podcast.mp3` |

---

## セットアップ手順

### 前提

- Google Cloud Platform アカウント
- Google アカウント（Google Drive 使用）

---

### Step 1 — Gemini API キーを取得

1. [Google AI Studio](https://aistudio.google.com/) にアクセス
2. **「Get API key」** → API キーを作成
3. 後で GitHub Secret `GEMINI_API_KEY` に登録

---

### Step 2 — GCP で OAuth2.0 クライアントを作成

1. [GCP コンソール](https://console.cloud.google.com/) → 対象プロジェクトを選択
2. **「APIとサービス」→「ライブラリ」** で **「Google Drive API」** を有効化
3. **「APIとサービス」→「認証情報」** → 「認証情報を作成」→「OAuth クライアント ID」
   - アプリケーションの種類：**ウェブアプリケーション**
   - 承認済みリダイレクト URI に追加：`https://developers.google.com/oauthplayground`
4. **クライアント ID** と **クライアント シークレット** を控える

> **重要 — 本番環境への昇格**
>
> 「OAuth 同意画面」でアプリの公開ステータスを **「本番環境」** に設定してください。
> テスト環境のままだと **リフレッシュトークンが 7 日で失効** します。
> 公開ステータスの変更：「OAuth 同意画面」→「アプリを公開」ボタンをクリック

---

### Step 3 — OAuth2.0 Playground でリフレッシュトークンを取得

1. [OAuth 2.0 Playground](https://developers.google.com/oauthplayground) を開く
2. 右上の **歯車アイコン（Settings）** をクリック
   - 「Use your own OAuth credentials」にチェック
   - Client ID / Client Secret を入力
3. **Step 1「Select & authorize APIs」** で以下のスコープを入力・選択：
   ```
   https://www.googleapis.com/auth/drive.file
   ```
   ※ このスコープ以外は使用不可
4. **「Authorize APIs」** → Google アカウントにサインインして許可
5. **Step 2「Exchange authorization code for tokens」** → 「Exchange authorization code for tokens」をクリック
6. 表示された **Refresh token** を控える

---

### Step 4 — GitHub Secrets を登録（この順番で）

GitHub リポジトリの **Settings → Secrets and variables → Actions → New repository secret** から登録。

| 登録順 | Secret 名 | 値 |
|--------|-----------|-----|
| 1 | `GEMINI_API_KEY` | Google AI Studio で取得した API キー |
| 2 | `GOOGLE_CLIENT_ID` | GCP で作成した OAuth クライアント ID |
| 3 | `GOOGLE_CLIENT_SECRET` | GCP で作成した OAuth クライアント シークレット |
| 4 | `GOOGLE_REFRESH_TOKEN` | OAuth2.0 Playground で取得したリフレッシュトークン |

---

## ワークフローの実行

### 手動実行

1. リポジトリの **Actions** タブを開く
2. 左サイドバーから **「Claude Code Podcast Generator」** を選択
3. **「Run workflow」** → **「Run workflow」** ボタンをクリック

### 定期実行（自動）

毎週月曜日 09:00 JST（00:00 UTC）に自動実行されます。
スケジュールを変更する場合は `.github/workflows/podcast.yml` の `cron` 値を編集してください。

---

## 話者設定

`config.py` で変更可能。

| 話者 | 性別 | 声（Gemini TTS） | 役割 |
|------|------|------------------|------|
| 田中 | 男性 | Charon | 技術解説役 |
| 鈴木 | 女性 | Aoede | 視聴者目線で質問役 |

---

## 中間成果物

失敗時もコミット済みの成果物からデバッグ可能です。

| ファイル | 内容 | 保存先 |
|----------|------|--------|
| `research.json` | Gemini による調査結果 | リポジトリ |
| `script.json` | 生成した対話台本 | リポジトリ |
| `chunk_*.wav` | TTS 音声チャンク | ローカルのみ（.gitignore） |
| `podcast.mp3` | 最終ポッドキャスト | Google Drive |

---

## ライセンス

MIT
