# 他議会への対応 (フォーク手順 / submodule 手順)

本リポジトリはフレームワーク本体です。実議会の議事録データを扱う運用リポジトリは、
本リポジトリを **submodule として取り込む** のが推奨構成です (議事録テキスト
や DB を public 履歴に混入させないため)。OSS 配布物として別議会版を提供したい
場合は従来通り **フォークして編集する** こともできます。

- **submodule 方式** → §A 〜 §C (運用リポジトリは private、本リポジトリは public OSS)
- **フォーク方式** → §1 〜 §9 (運用リポジトリそのものを公開する場合)

---

## A. submodule 方式 (推奨)

本フレームワークを取り込んだ private 運用リポジトリを別に用意し、議事録固有の
データ・プラグイン・config を private 側に置きます。フレームワーク側は議会固有の
情報を一切持たず、純粋な OSS として更新を受け続けられます。

### A-1. 推奨ディレクトリ構成

```
ZeroTrustDemocracy-<assembly>/        (private)
├── framework/                        ← git submodule → 本リポジトリ
├── municipal_modules/                ← MUNICIPAL_MODULES_PATH の指す先
│   └── <assembly>/
│       ├── __init__.py               # PARSERS / FETCHERS を export
│       ├── config/<assembly>.yaml
│       └── regular/, committee/, ... (session sub-packages)
├── db/<assembly>.db
├── raw_minutes/<assembly>/
├── frontend_data/                    ← export 出力先 (Cloudflare Pages の入力)
├── Makefile (or run.ps1 / run.sh)
└── .github/workflows/update-data.yml ← 週次 cron
```

### A-2. submodule の登録

```bash
git init ZeroTrustDemocracy-<assembly>
cd ZeroTrustDemocracy-<assembly>
git submodule add https://github.com/<you>/ZeroTrustDemocracy framework
git submodule update --init --recursive
```

### A-3. 環境変数で framework を private 側にバインド

| Env var | 説明 | 例 |
| --- | --- | --- |
| `MUNICIPAL_MODULES_PATH` | 外部プラグインを置いた**親ディレクトリ** (OS 区切り文字で複数指定可) | `<project>/municipal_modules` |
| `CONFIG_DIR` | YAML config のルート (省略すると `MUNICIPAL_MODULES_PATH` の親が使われる) | `<project>` |
| `RAW_MINUTES_DIR` | `raw_minutes/` の場所を YAML を介さず上書き | `<project>/raw_minutes/<assembly>` |
| `EXPORT_OUTPUT_DIR` | exporter (`scripts/export_static_data.py`) の出力ルート | `<project>/frontend_data` |
| `PYTHONPATH` | framework をモジュールとして import 可能にする | `<project>/framework` |

`<assembly>.yaml` 内の相対パス (`db_path`, `raw_minutes_dir` など) は、
`CONFIG_DIR` または `MUNICIPAL_MODULES_PATH` の親をプロジェクトルートとして解決
されます。

### A-4. グルースクリプト例 (Makefile)

```makefile
PROJECT := $(abspath .)
export MUNICIPAL_MODULES_PATH := $(PROJECT)/municipal_modules
export CONFIG_DIR             := $(PROJECT)
export EXPORT_OUTPUT_DIR      := $(PROJECT)/frontend_data
export PYTHONPATH             := $(PROJECT)/framework

ASSEMBLY ?= <assembly>

init:
	python framework/scripts/init_db.py $(ASSEMBLY)
fetch:
	python framework/app/fetch.py --municipality $(ASSEMBLY)
analyze:
	python framework/app/minute_analyzer.py --municipality $(ASSEMBLY)
export:
	python framework/scripts/export_static_data.py --municipality $(ASSEMBLY)
all: init fetch analyze export
```

### A-5. 動作確認

```bash
# framework 側で同梱されている sample プラグインを反対側 (= 外部経由) で
# 走らせて疎通確認する例:
MUNICIPAL_MODULES_PATH=framework/app/municipal_modules \
PYTHONPATH=framework \
python framework/scripts/init_db.py sample
```

`framework/app/municipal_modules/sample/` は架空のリファレンス実装です。Playwright
を使わないローカルファイル fetcher で構成されているので、submodule 取り込み
直後の疎通テストに使えます。

### A-6. 週次 cron は private 側に置く

`framework/.github/workflows/update-data.yml` は OSS リポジトリには **置きません** 。
週次 cron は private 側の `.github/workflows/` に作り、submodule を pin した状態で
fetch → analyze → export → commit を回します。

---

## B. submodule の更新フロー

```bash
# framework 側に新機能/修正が入ったら private 側で取り込み
cd framework && git pull origin main && cd ..
git add framework
git commit -m "Bump framework submodule"
```

CI で submodule pin の差分をチェックして PR を立てるのが堅実です。

---

## C. 問い合わせ窓口

利用者からの問い合わせは本フレームワークリポジトリ (public) の Issues / Discussions で
受け付けます。実議会のサイトに関する個別のフィードバック窓口を分けたい場合は、
Cloudflare Pages のフッターから別途 public な「フィードバック用リポジトリ」または
外部フォームへ誘導する構成が便利です。

---

## フォーク方式 (運用リポジトリそのものを OSS として公開する場合)

別議会版を OSS として丸ごと公開したい場合は、本リポジトリをそのままフォークして
編集する従来の方式が使えます。以下はその手順です。

## 1. リポジトリをフォーク

GitHub 上でフォークするか、`git clone --depth 1 <url>` でローカルに複製します。
ブランディング (リポジトリ名、README、フロントエンドのページタイトル) を新議会向け
に変更してください。

## 2. 新議会モジュールを追加

`app/municipal_modules/<新議会>/` を作成し、以下を配置:

```
app/municipal_modules/<新議会>/
├── __init__.py            # PARSERS / FETCHERS dict を export
├── config/
│   ├── <新議会>.yaml      # db_path / pii_files / party_table_path / fetchers.<NAME>.{fetch_url,encoding}
│   ├── name-party-table.csv
│   └── party_names.csv
├── <session_a>/           # 例: committee
│   ├── __init__.py        # fetcher + parser を export
│   ├── fetchers/
│   │   └── <NewAFetcher>.py
│   └── parsers/
│       └── <new_a_parser>.py
└── <session_b>/           # 例: regular (必要な session 数だけ追加)
    ├── ...
```

バンドルされている `sample/regular/` (架空議会、ローカルファイル fetcher) が
最小限の参考実装です。1 session しかない議会なら session サブパッケージを 1 つ
だけ作ればよく、複数 session ある議会なら同じ階層に並べます (`committee/` と
`regular/` のような対話形式と一括質問形式の二段構えなど)。

## 3. `__init__.py` で PARSERS / FETCHERS を宣言

`app/municipal_modules/<新議会>/__init__.py`:

```python
from .session_a import NewAFetcher, NewAParser
from .session_b import NewBFetcher, NewBParser

PARSERS = {
    NewAParser.FETCHER_NAME: NewAParser,
    NewBParser.FETCHER_NAME: NewBParser,
}
FETCHERS = {
    NewAFetcher.FETCHER_NAME: NewAFetcher,
    NewBFetcher.FETCHER_NAME: NewBFetcher,
}
```

これで `load_parsers_by_municipality()` / `load_fetchers_by_municipality()` が
新議会を自動検出します。`app/fetch.py` や `app/feederAPI.py` への追加編集は
**不要**です。

## 4. PII リスト / 会派表を差し替え

- `<新議会>/PIIs/` 配下に議員名・会派名リストを置き、`<新議会>.yaml` の
  `pii_files` で参照する (`sample/` の構成が最小例)。
- `name-party-table.csv` (`<新議会>/config/`) は議員名 → 会派の対応表。空でもよい。

## 5. データベースを初期化

```bash
python scripts/init_db.py <新議会>
```

`db/<新議会>.db` が `<新議会>.yaml:db_path` の指定通りに作成されます。
1 議会 = 1 DB が前提で、`minutes.fetcher` カラムで session を識別します。

## 6. 取得 → 解析

```bash
# 全 session を順に
python app/fetch.py --municipality <新議会>
python app/minute_analyzer.py --municipality <新議会>

# 個別 session のみ
python app/fetch.py --municipality <新議会> --fetcher <FETCHER_NAME>
```

## 7. API の動作確認

`config_loader.available_municipalities()` は `<新議会>/config/<新議会>.yaml` の
存在を見て自動で API に組み込みます。

```bash
python -m uvicorn app.feederAPI:app --host 0.0.0.0 --port 8000
curl 'http://localhost:8000/api/qa?municipality=<新議会>&uuid=...'
```

## 8. フロントエンドのデフォルト議会名を差し替え

`frontend/.env` (またはデプロイ環境変数) で以下を上書きします:

- `VITE_MUNICIPALITY` — `municipal_modules/<新議会>/config/<新議会>.yaml` と同じキー
- `VITE_ASSEMBLY_NAME` — フッターやページタイトルに出る人間向け表示名
- `VITE_SITE_TAGLINE` — 概要文 (OG 含む)
- (任意) `VITE_PROJECT_REPO_URL` — フィードバック窓口

データ出典リンク (フッター / About) は `<新議会>.yaml` の `data_sources:` から
`index.json` 経由でフロントへ渡されるので、コードを触らずに YAML だけ書き換え
ればよい構成です。

## 9. (任意) 同梱の sample プラグインを削除

実議会だけを残してフォーク先を軽くしたい場合、以下を削除できます:

- `app/municipal_modules/sample/`
- `tests/test_sample_parser.py`, `tests/test_external_plugin_discovery.py`
  (sample に依存している部分)

---

## 議事録形式別の実装方針

実装してから挫折しがちなのは、議会によって質疑応答の構造が大きく異なる点です。

- **委員会形式** (Q→A→Q→A の対話): 比較的そのまま QA 化可能。発言者マーク
  (`◆` 質問者 / `◎` 答弁者 / `○` 議長) を状態機械で追う方式が定石です。
- **本会議形式** (一括質問→一括答弁): 1 議員あたり「議題ごとの Q/A ペア」を
  HTML 構造から抽出する方式が現実的です (質問ブロックと答弁ブロックを別パスで
  集め、トピックキーでマージする)。
- **都道府県議会クラス**: 過去に都議会で「議員ごとの単発 QA」化に挫折した実績
  あり。フォーマット調査を Phase 0 として独立に走らせることを推奨します。
