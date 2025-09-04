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
このメソッドが議事録テキストを構造化データ(`minute_json`)へ変換します。
`convert` の具体的な実装は派生クラスで行い、必要に応じて
会議メタ情報の抽出やトピック分割、発言抽出などのヘルパー
メソッドを定義してください。

### minutes_json のフォーマット

`SetagayaParser.convert()` は議事録テキストを解析し、以下のような `minutes_json` を返します。

```python
minutes_json = {
    "meeting": meeting_info,
    "topics": [topic1, topic2, ..., topicN],
    "QAs": [QAs_topic1, QAs_topic2, ..., QAs_topicN],
}
```

#### meeting_info

```python
meeting_info = {
    "date": "YYYY年M月D日N号",  # 議会開催日
    "name": "会議名称",
}
```

#### topic

```python
topic = {
    "topic_id": int,           # トピックの通し番号 (1始まり)
    "raw": str,                # トピック部分の原文
    "speeches": [speech1, ...] # 発言のリスト
}
```

#### speech

```python
speech = {
    "id": int,        # トピック内での発言通し番号
    "mark": str,      # 議事録における記号 (◆, ◎, ○ など)
    "name": str,      # 発言者名
    "role": str,      # 発言者の役職
    "comment": str,   # 発言内容
    "raw": str,       # 元のテキスト
}
```

#### QAs

`minutes_json["QAs"]` はトピックごとに質疑応答のまとまりを保持する二重配列です。
各要素は1トピック分で、先頭にトピック冒頭の発言リスト `intro` を持ち、
続いて質疑応答や会派ごとのコメントなどのシーケンスが発言のリストとして並びます。

```python
QAs_topic = [
    intro,    # 議題についての事前発現等 (List[speech])
    qa_seq1,  # 質疑応答の1シーケンス (List[speech])
    qa_seq2,
    ...
]
```
## 参考実装

`app/municipal_modules/setagaya` 以下に、上記メソッドを実装した具体例があります。
新しい自治体を追加する際はこのディレクトリを参考にしてください。
