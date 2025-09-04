# base

BaseMinuteFetcher と BaseMinuteParser のインターフェースを定義するディレクトリです。
世田谷区の実装 `app/municipal_modules/setagaya` を参考に、各メソッドが受け取る入力と出力の形式を以下に示します。

## フェッチャー (BaseMinuteFetcher)

派生クラスでは次のメソッドを実装します。

- `extract_minutes_urls(page) -> list[str]`
  - **入力**: Playwright の `page` オブジェクト。
  - **出力**: ダウンロード対象となる議事録ページの URL のリスト。必要に応じて本メソッド内で検索条件の指定や検索実行を行う。

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

外部には `convert(text: str) -> Dict[str, Any]` のみを公開し、
このメソッドが議事録テキストを構造化データへ変換します。
`convert` の具体的な実装は派生クラスで行い、必要に応じて
会議メタ情報の抽出やトピック分割、発言抽出などのヘルパー
メソッドを定義してください。

## 参考実装

`app/municipal_modules/setagaya` 以下に、上記メソッドを実装した具体例があります。
新しい自治体を追加する際はこのディレクトリを参考にしてください。

