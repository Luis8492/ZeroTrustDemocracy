# base

BaseMinuteFetcher と BaseMinuteParser のインターフェースを定義するディレクトリです。
世田谷区の実装 `app/municipal_modules/setagaya` を参考に、各メソッドが受け取る入力と出力の形式を以下に示します。

## フェッチャー (BaseMinuteFetcher)

派生クラスでは次のメソッドを実装します。

- `set_search_setting_and_click_search(page) -> None`
  - **入力**: Playwright の `page` オブジェクト。
  - **出力**: なし。サイト上で検索条件を指定し検索を実行する。

- `extract_minutes_urls(page) -> list[str]`
  - **入力**: 検索結果を表示した `page`。
  - **出力**: ダウンロード対象となる議事録ページの URL のリスト。

- `download_new_minutes(conn, context, url) -> None`
  - **入力**:
    - `conn`: `sqlite3.Connection`。`minutes` テーブルを操作する。
    - `context`: Playwright の `BrowserContext`。
    - `url`: 詳細ページの URL。
  - **出力**: なし。`raw_minutes/` にテキストファイルを保存し、`mark_as_downloaded` を通じて次の情報を `minutes` テーブルに登録する。
    - `url`: 議事録の URL。
    - `file_name`: 保存したファイル名。
    - `fetcher`: フェッチャーのクラス名。
    - `analyzed`: 解析済みフラグ (初期値 0)。
  - 既に登録済みの URL はスキップする。

## パーサー (BaseMinuteParser)

派生クラスでは次のメソッドを実装します。

- `extract_meeting_data(text: str) -> Dict[str, Any]`
  - **入力**: 議事録テキスト。
  - **出力**: 会議名や日付などのメタ情報を含む辞書。`minute_analyzer` で `meetings` テーブルに `file_name`, `date`, `name` が保存される。

- `extract_topic_section(text: str) -> List[str]`
  - **入力**: 議事録テキスト。
  - **出力**: トピックごとに分割した文字列のリスト。

- `extract_speeches(topic_text: str) -> List[Dict[str, Any]]`
  - **入力**: トピック部分のテキスト。
  - **出力**: 発言ごとの辞書のリスト。各辞書には `id`, `mark`, `name`, `role`, `comment`, `raw` などのキーを含む。

- `extract_QAs(minute: Dict[str, Any]) -> List[Any]`
  - **入力**: 上記メソッドで生成した minute 構造体。
  - **出力**: Q&A シークエンスのリスト。`minute_analyzer` を通じて `questions` テーブルに `file_name`, `topic_intro`, `QA`, `questioner` が保存される。

## 参考実装

`app/municipal_modules/setagaya` 以下に、上記メソッドを実装した具体例があります。新しい自治体を追加する際はこのディレクトリを参考にしてください。

