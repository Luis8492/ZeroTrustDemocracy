# municipal_modules

世田谷区議会の議事録を扱うモジュール群です。

現在の配布物には世田谷区のみが含まれます。1 自治体 (`setagaya`) の下に **session
type** ごとのサブパッケージを配置する構造を採用しています。

```
setagaya/
├── __init__.py            # PARSERS / FETCHERS dict を export
├── config/
│   ├── setagaya.yaml      # 共有設定 + fetchers.<NAME> ごとの上書き
│   ├── name-party-table.csv
│   └── party_names.csv
├── committee/             # 委員会セッション (SetagayaCommitteeFetcher/Parser)
└── regular/               # 定例会セッション (SetagayaRegularFetcher/Parser)
```

別議会への対応はリポジトリをフォークして上記構造ごと置き換える形を想定して
います。詳細な手順は `docs/FORK_GUIDE.md` を参照してください。

## モジュール構成のルール

- `setagaya/__init__.py` は `PARSERS = {fetcher_name: parser_class}` と
  `FETCHERS = {fetcher_name: fetcher_class}` を export する。
- 各 session サブパッケージは `BaseMinuteFetcher` と `BaseMinuteParser` の
  サブクラスを 1 組ずつ保持する。
- `FETCHER_NAME` (Parser/Fetcher 両方の class attribute) は session を識別する
  キー。raw_minutes のファイル名 prefix、`minutes.fetcher` カラム、設定 YAML の
  `fetchers.<NAME>` キーで一致させる。

## 設定ファイル

`setagaya/config/setagaya.yaml` は共有フィールドを top-level に、session 個別の
`fetch_url` / `encoding` を `fetchers.<FETCHER_NAME>` 配下に置きます。
`config_loader.load_for_fetcher(municipality, fetcher_name)` がこれをマージして
平坦な dict を返すため、フェッチャや analyzer は session 単位の値を意識します。

`config_loader.available_municipalities()` は `<name>/config/<name>.yaml` の存在を
起点に自動検出するため、ハードコードされた一覧は存在しません。
