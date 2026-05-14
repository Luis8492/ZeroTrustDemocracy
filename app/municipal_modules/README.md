# municipal_modules

議会プラグインのコンテナです。1 議会 = 1 トップレベルパッケージ。1 自治体の下に
**session type** ごとのサブパッケージを配置する構造を採用しています。

```
<assembly>/
├── __init__.py            # PARSERS / FETCHERS dict を export
├── config/
│   ├── <assembly>.yaml    # 共有設定 + fetchers.<NAME> ごとの上書き / data_sources
│   ├── name-party-table.csv
│   └── ...
├── PIIs/                  # 匿名化対象の語彙ファイル (任意)
├── <session_a>/           # 例: regular  (SampleFetcher/SampleParser)
└── <session_b>/           # 例: committee (1 session しかなければ省略可)
```

本リポジトリにバンドルされているのはリファレンス用の **`sample/`** のみです
(架空議会、Playwright 不要のローカル fixture fetcher で動作)。
実議会のプラグインは **private 運用リポジトリ側** に置き、`MUNICIPAL_MODULES_PATH`
環境変数で外部から本フレームワークに発見させます。手順は `docs/FORK_GUIDE.md` §A
を参照してください。

## モジュール構成のルール

- `<assembly>/__init__.py` は `PARSERS = {fetcher_name: parser_class}` と
  `FETCHERS = {fetcher_name: fetcher_class}` を export する。
- 各 session サブパッケージは `BaseMinuteFetcher` と `BaseMinuteParser` の
  サブクラスを 1 組ずつ保持する。
- `FETCHER_NAME` (Parser/Fetcher 両方の class attribute) は session を識別する
  キー。raw_minutes のファイル名 prefix、`minutes.fetcher` カラム、設定 YAML の
  `fetchers.<NAME>` キーで一致させる。
- Playwright を必要としない fetcher は `REQUIRES_PLAYWRIGHT = False` を宣言する。
  `app/fetch.py` がブラウザ起動をスキップする (`sample` がこのパス)。

## 設定ファイル

`<assembly>/config/<assembly>.yaml` は共有フィールドを top-level に、session 個別の
`fetch_url` / `encoding` を `fetchers.<FETCHER_NAME>` 配下に置きます。
`config_loader.load_for_fetcher(municipality, fetcher_name)` がこれをマージして
平坦な dict を返すため、フェッチャや analyzer は session 単位の値を意識します。

`data_sources:` (任意、`[{name, url}, ...]` 配列) を書いておくと、exporter が
`index.json` に転載してフロントエンドのフッター/Aboutに表示します。

`config_loader.available_municipalities()` は `<name>/config/<name>.yaml` の存在を
起点に自動検出するため、ハードコードされた一覧は存在しません。
