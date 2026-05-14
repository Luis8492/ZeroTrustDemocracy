👉 [Support the project](https://buymeacoffee.com/luis8492)

# Zero Trust Democracy

**ZeroTrustDemocracy** は、議会の議事録を「質疑応答ペア (QA)」単位に構造化し、
市民が一つひとつ匿名で評価できるようにする非公式ビューワーのフレームワーク
です。評価データはユーザーのブラウザ (IndexedDB) にだけ保存され、サーバーへは
一切送信されません — 名前の通り「サーバーを信用しない」設計です。

本リポジトリは **フレームワーク本体** であり、特定の議会のデータは含まれません。
リファレンス用に動作する `sample` プラグイン (架空議会・Playwright 不要) のみ
バンドルされており、実際の議会向けの運用は **private 運用リポジトリ** が本
リポジトリを git submodule として取り込み、独自の `municipal_modules/<name>/`
プラグインと議事録データを抱える構成を推奨します。

新しい議会を立てる手順は [`docs/FORK_GUIDE.md`](docs/FORK_GUIDE.md) を参照。

---

## 🎯 プロジェクトの目的
- 議会議事録を自動的に解析し、議員の発言を「質疑応答ペア (QA)」として構造化。
- ユーザーが QA を匿名で評価し、自分の評価傾向を統計的に分析・可視化。
- 評価データはクライアント (IndexedDB) にのみ保持し、サーバーには一切送信しない。

## コンセプトの課題
- 議事録部分:
  - 発言していることについてしか評価できない。「発言しなかったこと」も評価対象であるはず。
  - 口が上手いだけの議員が評価される可能性がある。
  - 議事録における発言に同意できるかどうか、とその発言の行政における重要度は必ずしも比例しない。
- 議事録以外の部分: 会議での発言がすべてではない。

---

## 🧩 機能概要

### ✅ 議事録抽出・解析 (Python パイプライン)
- 議会議事録テキストから以下を抽出:
  - 会議情報 (日時、委員会名)
  - トピック単位の発言群
  - 質問者・答弁者の発言を分離し QA 化
  - PII / 政党名を伏字化 (`anonymizer.py` で `***` に置換)
- SQLite3 に構造化済みデータを保存。

### ✅ 静的 JSON 配信
- `scripts/export_static_data.py` が SQLite を読み、`frontend/public/data/index.json`
  と `meetings/<file_name>.json` を生成。
- フロントエンドは API サーバーを介さず、この静的 JSON を直接読み取ります。

### ✅ フロントエンド (Svelte 5 + Vite + TypeScript)
- ハッシュルーティングの SPA。`/` (評価)、`/result` (統計)、`/settings` (テーマ選択)、`/about`
- 評価ページで未評価 QA を取得し、共感度 -3〜+3 と重要度 0〜3 で評価
- 評価データは IndexedDB (`EvalDB`) に保存され、サーバーには送信されない
- ヘッダに累積評価カウンタを常時表示
- データ出典リンク・サイト名・タグラインは index.json と `VITE_*` env で構成
  (詳細は `frontend/.env` 参照)

### ✅ 統計ページ (`/result`)
- 議員別 / 会派別の平均評価バーチャート (95% 信頼区間付き)
- **論点マップ** (SVG): 委員会を円で、評価数=サイズ、平均評価=色、同一議員が登場する委員会同士をエッジで結ぶ
- 議員 / 会派でのフィルタ、CSV エクスポート / インポート

### ✅ テーマ機構
- `<html data-theme="...">` + CSS 変数で見た目を切替
- 同梱テーマ: `plain` / `chat` / `scroll` (和紙風) / `hud` (シアン基調 SF UI)
- 選択はユーザーごとに IndexedDB に保存

### ✅ 匿名性・セキュリティ配慮
- 評価データやユーザーID等の情報は **一切サーバーに送信しない**
- ユーザーごとのローカルストレージ (IndexedDB) で管理
- CORS 設定済み、POST ベースの API 設計 (レガシー API を使う場合)

### ✅ レガシー API サーバー (任意)
- `app/feederAPI.py` (FastAPI) は引き続き動作するが、静的配信を前提とした現行
  フロントエンドはこれを使いません。
- 詳細は [API.md](API.md) を参照。

---

## 🛠️ 技術スタック

| 分類 | 技術 |
|------|------|
| バックエンド | Python 3, SQLite3, Playwright (実フェッチ用) |
| フロントエンド | Svelte 5, Vite, TypeScript |
| クライアント DB | [idb](https://github.com/jakearchibald/idb) (IndexedDB ラッパー) |
| グラフ描画 | Chart.js + chartjs-chart-error-bars, SVG 直書き (論点マップ) |
| ルーティング | svelte-spa-router (hash-based) |
| 匿名化 | `anonymizer.py` (PII / 政党名リストの伏字化) |
| 配信 | 開発時は Vite (`npm run dev`)、本番は Cloudflare Pages (静的) |

---

## 📁 ディレクトリ構成

- `app/` — バックエンドコードと解析ツール
  - `municipal_modules/sample/` — リファレンス用のサンプル議会プラグイン
  - `municipal_modules/base/` — 共有の基底クラス
- `frontend/` — Svelte 5 + Vite SPA (`src/`、ビルド成果物は `dist/`)
- `scripts/` — メンテナンス用の補助スクリプト
- `db/` — SQLite データベース (sample のみ同梱)
- `docs/` — 開発者向けドキュメント (`FORK_GUIDE.md` 等)

実議会のプラグイン (parser / fetcher / config / PII / DB / raw_minutes / 静的 JSON)
は **private 運用リポジトリ** 側に置きます (本リポジトリには持ち込みません)。

---

## 📦 ローカル開発 (sample で動作確認)

```bash
# 1) Python 依存をインストール
pip install -r requirements.txt
# 実フェッチを試す場合のみ:
playwright install chromium

# 2) sample プラグインで一通り回す
python scripts/init_db.py sample
python app/fetch.py --municipality sample           # ローカル fixture をコピーするだけ
python app/minute_analyzer.py --municipality sample
python scripts/export_static_data.py --municipality sample
# → frontend/public/data/index.json + meetings/*.json が生成される

# 3) フロントエンド (Node 20+)
cd frontend
npm install
npm run dev
# => http://localhost:8001/  (data は frontend/public/data/ から配信)
```

`pytest` で 18 テスト (sample + framework) が pass することを確認できます。

---

## 🚀 本番デプロイ

本リポジトリ単体ではデプロイしません。実議会向けの Cloudflare Pages 配信は
**private 運用リポジトリ** 側で行います。テンプレートの構成と手順は
[`docs/FORK_GUIDE.md`](docs/FORK_GUIDE.md) §A を参照。

private 側は以下のような構成になります:

```
your-assembly-repo/
├── framework/                  ← submodule (このリポジトリ)
├── municipal_modules/<name>/   ← 議会固有 parser/fetcher/config/PII
├── db/<name>.db                ← 解析済み構造化データ
├── raw_minutes/                ← 取得済み生議事録
├── frontend_data/data/         ← 匿名化済み配信 JSON (Pages 入力)
├── .github/workflows/          ← 議事録更新の週次 cron はここに置く
└── Makefile / run.ps1          ← framework を呼び出すグルー
```

---

## 📚 データ出典・免責

各議会の出典リンクは `municipal_modules/<name>/config/<name>.yaml` の
`data_sources:` に書き、`index.json` 経由でフロントエンドが表示します。
本フレームワーク自身は特定議会の公式サービスではありません。

誤った表示の指摘・削除依頼などは各 private 運用リポジトリ側の Issues、
またはフレームワーク側のバグであれば [GitHub Issues](https://github.com/Luis8492/ZeroTrustDemocracy/issues) までお願いします。
