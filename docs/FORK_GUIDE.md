# 他議会への対応 (フォーク手順)

本リポジトリは現状、世田谷区議会専用の配布物として整備されています。別議会
(板橋区、横浜市、都道府県議会など) に対応させる場合は、このリポジトリを
**フォークして編集する**運用を想定しています。プラグイン抽象 (`BaseMinuteFetcher`,
`BaseMinuteParser`, `available_municipalities()`) は維持されているため、以下の
手順で新議会向けの配布物を作れます。

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

世田谷区の `setagaya/committee/` (委員会、テキスト形式) と `setagaya/regular/`
(定例会、HTML 形式) が参考実装です。1 session しかない議会なら session サブ
パッケージを 1 つだけ作ればよく、複数 session ある議会なら同じ階層に並べます。

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

- `app/PIIs/` 配下に新議会向けの議員名・会派名リストを置き、`<新議会>.yaml` の
  `pii_files` で参照する。世田谷区専用の `partyNames.txt` は削除して構いません。
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

`frontend/main.js` と `frontend/result.html` の `MUNICIPALITY` 定数を新議会名に変更
します。ブランディング (タイトル、説明文) も同時に書き換えると配布物として
完結します。

## 9. (任意) 世田谷区モジュールを削除

フォーク先で世田谷区関連を残す必要がなければ、以下を一括削除して配布物を
スリムにできます:

- `app/municipal_modules/setagaya/`
- `app/raw_minutes/Setagaya*`
- `tests/test_setagaya_participants.py`, `tests/test_pattern_classifier.py`
- `scripts/{display,list,quality_check}_setagaya_*` などの補助スクリプト

---

## 議事録形式別の実装方針

実装してから挫折しがちなのは、議会によって質疑応答の構造が大きく異なる点です。

- **委員会形式** (Q→A→Q→A の対話): 比較的そのまま QA 化可能。`setagaya` の
  状態機械パーサーが参考になります。
- **本会議形式** (一括質問→一括答弁): 1 議員あたり「議題ごとの Q/A ペア」を
  HTML 構造から抽出する `setagaya2` 方式が現実的です。
- **都道府県議会クラス**: 過去に都議会で「議員ごとの単発 QA」化に挫折した実績
  あり。フォーマット調査を Phase 0 として独立に走らせることを推奨します。
