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

### ✅ フロントエンド（Vanilla JS + IndexedDB）
- ページ表示時に`/api/qa/next`を呼び出し、QAを表示
- ユーザーが-3～+3で評価 → IndexedDBに保存（評価はクライアントにのみ保持）
- 評価済みIDはIndexedDBから取得し、APIに渡して未評価QAを取得
- (未実装)ある程度評価がたまってきたら、評価済みのQAのメタ情報をサーバーから取得し、評価結果と併せてユーザーの評価傾向を可視化(e.g.○○党の主張には賛成傾向)

---

### ✅ 匿名性・セキュリティ配慮
- 評価データやユーザーID等の情報は**一切サーバーに送信しない**
- ユーザーごとのローカルストレージ（IndexedDB）で管理
- CORS設定済み、POSTベースのAPI設計で安全性向上

---

## 🛠️ 技術スタック

| 分類 | 技術 |
|------|------|
| バックエンド | Python 3, FastAPI, SQLite3 |
| フロントエンド | HTML, JavaScript (ES Modules), IndexedDB |
| クライアントDB | [idb](https://github.com/jakearchibald/idb) (IndexedDB wrapper) |
| ローカルサーバー | `python3 -m http.server 8000` など |
| 匿名化 | `anonymizer.py`（PIIリストによる置換） |
| データ変換 | 議事録を構造化JSONへ変換するPythonスクリプト |

---

## 📁 ディレクトリ構成

- `app/` - バックエンドスクリプトと解析ツール
  - `municipal_modules/setagaya/` - 世田谷区議会モジュール (統合)
    - `committee/` - 委員会議事録 (`SetagayaCommitteeFetcher`)
    - `regular/` - 定例会議事録 (`SetagayaRegularFetcher`)
  - `municipal_modules/base/` - 共有の基底クラス
- `frontend/` - クライアントサイドの HTML と JavaScript
- `scripts/` - メンテナンス用の補助スクリプト
- `db/` - SQLite データベースを格納するディレクトリ
- `docs/` - 開発者向けドキュメント (`FORK_GUIDE.md` 等)

---

## 📦 ローカル開発

### 初回セットアップ

```bash
# 依存関係をインストール
pip install -r requirements.txt

# Python側 API サーバーを起動
cd ZeroTrustDemocracy
python3 -m uvicorn app.feederAPI:app --host 0.0.0.0 --port 8000

# フロントエンド（別ターミナル / Node 20+ 必須）
cd frontend
npm install
npm run dev
# => アクセス: http://localhost:8001/
```

### データベース初期化

議事録を取得する前に、各自治体の SQLite データベースを初期化する必要があります。

```bash
# 委員会・定例会共用の DB を作成 (db/setagaya.db)
python scripts/init_db.py setagaya
```

`scripts/init_db.py` は `minutes`, `meetings`, `downloaded_minutes_url_helper`, `questions` などのテーブルを生成し、`minutes.uuid` と `questions.uuid` を含める構成である。

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
| `MUNICIPALITY` | 処理対象の自治体を指定します (`setagaya` または `setagaya2`)。 | `setagaya` |
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
