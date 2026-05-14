# Zero Trust Democracy — 世田谷区議会版

**ZeroTrustDemocracy** は、議会の議事録を分かりやすい形でユーザーに提示することで、
民主的な意思決定への市民参加を支援するプロジェクトです。本リポジトリは
**世田谷区議会**向けに整備された配布物です。

別議会向けにフォークする場合は [`docs/FORK_GUIDE.md`](docs/FORK_GUIDE.md) を
参照してください。

---

## 🎯 プロジェクトの目的
- 世田谷区議会の議事録を自動的に解析し、議員の発言を「質疑応答ペア (QA)」として構造化。
- ユーザーが QA を匿名で評価し、自分の評価傾向を統計的に分析・可視化。
- 評価データはクライアント (IndexedDB) にのみ保持し、サーバーには一切送信しない。

## コンセプトの課題
- 議事録部分：
  - 発言していることについてしか評価できない。「発言しなかったこと」も評価対象であるはず。
  - 口が上手いだけの議員が評価される可能性がある。
  - 議事録における発言に同意できるかどうか、とその発言の行政における重要度は必ずしも比例しない。(e.g. ある議員の発言には悉く同意できても、あまり重要でない分野でしか発言していない可能性もある。)
- 議事録以外の部分
  - 会議での発言がすべてではない。
---

## 🧩 機能概要

### ✅ 議事録抽出・解析（Pythonスクリプト）
- 議会議事録テキストから以下を抽出：
  - 会議情報（日時、委員会名）
  - トピック単位の発言群
  - 質問者・答弁者の発言を分離しQA化
  - 個人情報を匿名化（`anonymizer.py`）

- SQLite3にメタデータ（会議情報、質問者、topic_introなど）を保存

---

### ✅ APIサーバー（FastAPI）
- **`POST /api/qa/meta`**: 評価済みIDのQAメタ情報を返す（会議名と日次を含む）
- **`POST /api/qa/next`**: ユーザー未評価のQAをランダムに1件返す
  - 各レスポンスには `uuid` を含む
- **`GET /api/qa`**: `uuid` を指定してQAを取得する
  - 詳しい入出力仕様は[APIドキュメント](API.md)を参照してください。

---

### ✅ フロントエンド (Svelte 5 + Vite + TypeScript)
- ハッシュルーティングの SPA。`/` (評価)、`/result` (統計)、`/settings` (テーマ選択)
- 評価ページで `/api/qa/next` から未評価 QA を取得し、-3〜+3 で評価
- 評価データは IndexedDB (`EvalDB`) に保存され、サーバーには送信されない
- ヘッダに累積評価カウンタを常時表示
- 委員会名をタグとして表示

### ✅ 統計ページ (`/result`)
- 議員別 / 会派別の平均評価バーチャート (95% 信頼区間付き)
- **論点マップ** (SVG): 委員会を円で、評価数=サイズ、平均評価=色、同一議員が登場する委員会同士をエッジで結ぶ
- 議員 / 会派でのフィルタ、CSV エクスポート/インポート

### ✅ テーマ機構
- `<html data-theme="...">` + CSS 変数で見た目を切替
- 同梱テーマ:
  - `plain`: 標準
  - `chat`: 質問者=右側青吹き出し / 答弁者=左側 / 委員長=中央システムメッセージ
  - `scroll`: 和紙風の古文書テーマ
  - `hud`: シアン基調のグラスモーフィズム SF UI
- 選択はユーザーごとに IndexedDB に保存

---

### ✅ 匿名性・セキュリティ配慮
- 評価データやユーザーID等の情報は**一切サーバーに送信しない**
- ユーザーごとのローカルストレージ（IndexedDB）で管理
- CORS設定済み、POSTベースのAPI設計で安全性向上

---

## 🛠️ 技術スタック

| 分類 | 技術 |
|------|------|
| バックエンド | Python 3, FastAPI, SQLite3, Playwright |
| フロントエンド | Svelte 5, Vite, TypeScript |
| クライアントDB | [idb](https://github.com/jakearchibald/idb) (IndexedDB ラッパー) |
| グラフ描画 | Chart.js + chartjs-chart-error-bars (議員/会派別評価), SVG 直書き (論点マップ) |
| ルーティング | svelte-spa-router (hash-based) |
| 匿名化 | `anonymizer.py`（PIIリストによる置換） |
| 配信 | 開発時は Vite (`npm run dev`), 本番は Cloudflare Pages (静的) |

---

## 📁 ディレクトリ構成

- `app/` - バックエンドスクリプトと解析ツール
  - `municipal_modules/setagaya/` - 世田谷区議会モジュール (統合)
    - `committee/` - 委員会議事録 (`SetagayaCommitteeFetcher`)
    - `regular/` - 定例会議事録 (`SetagayaRegularFetcher`)
  - `municipal_modules/base/` - 共有の基底クラス
- `frontend/` - Svelte 5 + Vite SPA (`src/`、ビルド成果物は `dist/`)
- `scripts/` - メンテナンス用の補助スクリプト
- `db/` - SQLite データベースを格納するディレクトリ
- `docs/` - 開発者向けドキュメント (`FORK_GUIDE.md` 等)

---

## 📦 ローカル開発

### 初回セットアップ

```bash
# 1) Python 依存をインストール
pip install -r requirements.txt
playwright install chromium      # 議事録取得時のみ必要

# 2) API サーバーを起動 (リポジトリルートで)
python -m uvicorn app.feederAPI:app --host 0.0.0.0 --port 8000

# 3) フロントエンド (別ターミナル / Node 20+ 必須)
cd frontend
npm install
npm run dev
# => http://localhost:8001/ （/api/* は :8000 にプロキシ）
```

フロントを本番モードで配信する場合は `npm run build` で `frontend/dist/` を
生成し、静的配信サーバー (Cloudflare Pages 等) から配信してください。

### データベース初期化

議事録を取得する前に、各自治体の SQLite データベースを初期化する必要があります。

```bash
# 委員会・定例会共用の DB を作成 (db/setagaya.db)
python scripts/init_db.py setagaya
```

`scripts/init_db.py` は `minutes`, `meetings`, `downloaded_minutes_url_helper`, `questions` などのテーブルを生成し、`minutes.uuid` と `questions.uuid` を含める構成である。

### 議事録データの取得・解析

データベースを初期化したら、以下の手順で議事録データを取得・解析できます。

#### 1. 議事録の取得（フェッチ）

```bash
python app/fetch.py --municipality setagaya
```

Playwright を使って議会議事録サイトからテキストをスクレイピングし、`app/raw_minutes/` に保存します。取得した各 URL は `minutes` テーブルに `analyzed=0` として記録されます。

> Playwright のブラウザが必要です。ローカル実行の場合は事前に `playwright install chromium` を実行してください。

#### 2. 議事録の解析（パース）

```bash
python app/minute_analyzer.py --municipality setagaya
```

未解析の行（`analyzed=0`）を読み取り、パーサーで構造化された質疑応答ペア（QA）を生成して `questions` テーブルに書き込みます。`--municipality` を省略するとすべての自治体を処理します。

#### 3. 静的 JSON へのエクスポート

```bash
python scripts/export_static_data.py
```

DB を匿名化済みの静的 JSON にダンプし、`frontend/public/data/` 配下へ出力します。
フロントエンドはここを直接読みに行きます。

---

## 🚀 本番デプロイ (Cloudflare Pages + GitHub Actions)

本リポジトリは **完全静的サイト** としてデプロイできるように構成されている。
評価データはクライアント側 IndexedDB に閉じているため、サーバーは不要。

### 構成図

```
[GitHub Actions cron 週次]
   ├─ fetch.py + minute_analyzer.py で db/setagaya.db を更新
   ├─ export_static_data.py で frontend/public/data/*.json を再生成
   └─ 変更を main に commit & push
        │
        ▼
[Cloudflare Pages]
   └─ push を検知して npm run build → CDN 配信
```

### データのエクスポート (ローカル確認用)

```bash
python scripts/export_static_data.py
# => frontend/public/data/index.json + meetings/*.json を生成
```

### Cloudflare Pages の初期設定 (一度きり)

1. Cloudflare ダッシュボード → Workers & Pages → Create application → Pages → Connect to Git
2. リポジトリを選択し、Production branch = `main`
3. Build settings:
   - **Framework preset**: `None` (Vite を手動指定)
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Build output directory**: `frontend/dist`
   - **Root directory**: 空欄 (リポジトリルート)
4. 環境変数は不要 (デフォルトで `/data` 配下を見にいく)
5. Save and Deploy

カスタムドメインを設定する場合は Pages の "Custom domains" タブから追加。

### GitHub Actions の有効化

`.github/workflows/update-data.yml` がリポジトリに含まれている。
GitHub リポジトリの Settings → Actions → General で:

- **Workflow permissions** を **Read and write permissions** に
- (任意) 即座に動作確認したい場合は Actions タブから `Update assembly data` ワークフローを手動実行 (`workflow_dispatch`)

実行スケジュールは毎週月曜 03:00 JST。Actions が DB と JSON を commit して push すると Cloudflare Pages が自動でビルドし、CDN へ反映される。

### 議事録ファイルの取り扱い

| パス | git 追跡 | 備考 |
|---|---|---|
| `db/setagaya.db` | ✅ | Actions が更新 / 約 14MB から徐々に増加 |
| `frontend/public/data/` | ✅ | エクスポート結果。CF Pages のビルドに必要 |
| `app/raw_minutes/*.txt` | ❌ (.gitignore) | フェッチで再生成可能。サイズ抑制のため除外 |

### API サーバー版を使いたい場合

`app/feederAPI.py` は引き続き動作する。VPS 等で API + フロントエンドを動かす運用も可能だが、その場合は `frontend/src/lib/api.ts` を `fetch('/api/...')` 版に書き戻す必要がある (現在はリポジトリ上は静的版のみ)。
