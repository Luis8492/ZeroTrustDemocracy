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
  - `scroll`: 縦書き和紙、右から左へ巻物のように読む
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
| 配信 | 開発時は Vite (`npm run dev`), 本番は Nginx (`Dockerfile.frontend` 多段ビルド) |

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
生成し、静的配信サーバーから配信してください (Docker Compose ではこれを Nginx で
配信します)。

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

#### Docker 経由での実行

Docker Compose を使う場合は、環境変数でコンテナ起動時に自動的に取得・解析を行えます。

```bash
INIT_DB_ON_START=true RUN_FETCH_ON_START=true MUNICIPALITY=setagaya docker compose up --build
```

---

## 🐳 Docker での実行

ローカル環境に Python や Playwright を直接インストールせずに動作を確認したい場合は、リポジトリに含めた Docker 設定を利用できます。

### 必要なファイル

- `Dockerfile`: FastAPI バックエンド用のイメージを定義する。Playwright の公式 Python イメージをベースにし、依存関係をインストールしたうえで非 root ユーザー（`appuser`）でプロセスを実行する。
- `Dockerfile.frontend`: フロントエンドの静的ファイルを Nginx で配信するためのイメージです。
- `docker-compose.yml`: バックエンドとフロントエンドの 2 コンテナをまとめて起動する。アプリケーションのログ、SQLite データベース、取得した議事録、生成物はホスト側ディレクトリへマウントされ、永続化される。
- `scripts/start-backend.sh`: バックエンドコンテナのエントリポイントです。環境変数で初期化やスクレイピング処理の有無を切り替えられます。


### 永続化されるディレクトリ

`docker-compose.yml` では、以下のディレクトリをバックエンドコンテナへバインドマウントしている。

| ホスト側 | コンテナ側 | 用途 |
|---|---|---|
| `./logs` | `/app/logs` | バックエンドログ |
| `./db` | `/app/db` | SQLite データベース |
| `./app/raw_minutes` | `/app/app/raw_minutes` | 取得した生議事録ファイル |
| `./app/exports` | `/app/app/exports` | 加工結果などの生成物 |
| `./config` | `/app/config` | 外部設定ファイル（`config.yaml`, `<municipality>.yaml` など） |

`app/exports/` は生成物の保存先として追加している。必要に応じて、解析結果の JSON や CSV などをこのディレクトリに出力するとよい。

`./config` を `/app/config` にマウントすることで、コンテナ外で管理する設定を優先的に読み込める。`CONFIG_DIR` または `CONFIG_PATH` を指定すると、デフォルトの同梱設定より外部設定を優先する実装である。

### 別コンテナから参照する方法

同一 `docker compose` プロジェクト内であれば、同じホスト側パスを別サービスにもマウントすることで参照できる。

```yaml
services:
  worker:
    image: python:3.12-slim
    volumes:
      - ./app/raw_minutes:/work/raw_minutes:ro
      - ./app/exports:/work/exports
```

- `:ro` を付与すると読み取り専用マウントになるため、安全に参照だけを行える。
- 書き込みが必要な場合は `:ro` を外し、共有ディレクトリとして利用する。

### ヘルスチェックと起動順制御

`docker-compose.yml` では `backend` / `frontend` の両サービスに `healthcheck` を設定している。

- `backend`: `http://localhost:8000/openapi.json` へコンテナ内部からアクセスし、API が応答可能かを確認する。
- `frontend`: `http://localhost/` への HTTP アクセスで Nginx の応答可否を確認する。
- `frontend` は `depends_on` の `condition: service_healthy` を使い、`backend` のヘルスチェック成功後に起動する。

状態確認は以下で行える。

```bash
docker compose ps
```

### 起動手順

```bash
# 変更を反映したイメージをビルドしつつ起動
docker compose up --build

# バックグラウンドで起動したい場合
docker compose up --build -d
```

- FastAPI バックエンド: http://localhost:8000
- フロントエンド: http://localhost:8001

ブラウザでフロントエンドにアクセスすると、ホストの `localhost:8000` に公開された API を利用します。

### オプション

以下の環境変数は `docker-compose.yml` で設定済みですが、必要に応じて上書きできます。

| 変数名 | 役割 | 既定値 |
|--------|------|--------|
| `MUNICIPALITY` | 処理対象の議会を指定します。本リポジトリでは `setagaya` のみ。 | `setagaya` |
| `INIT_DB_ON_START` | コンテナ起動時に `scripts/init_db.py` を実行するかどうか。 | `false` |
| `RUN_FETCH_ON_START` | コンテナ起動時に `app/fetch.py` と `app/minute_analyzer.py` を実行するか。 | `false` |
| `UVICORN_HOST` / `UVICORN_PORT` | Uvicorn サーバーのホスト・ポート。 | `0.0.0.0` / `8000` |
| `CONFIG_DIR` | 自治体設定や `config.yaml` を置く外部設定ディレクトリ。 | `/app/config` |
| `CONFIG_PATH` | グローバル設定ファイルの絶対パス（`CONFIG_DIR` より優先）。 | 未設定 |


外部設定を利用する場合の例は以下のとおりである。

```bash
# docker-compose.yml で ./config:/app/config をマウント済みの場合
# /app/config/config.yaml, /app/config/setagaya.yaml などが優先される
docker compose up --build

# グローバル設定だけ別パスを使う場合
CONFIG_PATH=/app/config/production.yaml docker compose up --build
```

自治体向けの SQLite データベースを事前に用意したい場合は、起動後に以下のように実行してください。

```bash
# setagaya の DB を初期化 (委員会・定例会共用)
docker compose run --rm backend python scripts/init_db.py setagaya
```
