# APIドキュメント

本プロジェクトで提供されるAPIの入力と出力形式について説明します。

## POST /api/qa/next
評価済みIDのリストを受け取り、未評価のQAを1件返します。

### リクエスト
- メソッド: `POST`
- ヘッダー: `Content-Type: application/json`
- ボディ:
```json
{
  "evaled_ids": [1, 2, 3]
}
```
`evaled_ids` はすでに評価済みのQA IDを表す整数の配列です。

### レスポンス
- 未評価のQAが存在する場合:
```json
{
  "id": 253,
  "committee_date": "2025年06月06日01号",
  "committee_name": "企画総務常任委員会",
  "topic_intro": [
    {"mark": "○", "role": "委員長", "comment": "…"}
  ],
  "QA": [
    {"mark": "○", "role": "質問者", "comment": "…"}
  ],
  "eval_target": "◆"
}
```
- 全て評価済みの場合:
```json
{ "message": "全て評価済みです" }
```

## POST /api/qa/meta
評価済みIDのリストを受け取り、そのメタ情報を返します。

### リクエスト
- メソッド: `POST`
- ヘッダー: `Content-Type: application/json`
- ボディ:
```json
{
  "evaled_ids": [1, 2, 3]
}
```

### レスポンス
- 例:
```json
[
  {
    "id": 253,
    "questioner": "○○議員",
    "topic_intro": [
      {"mark": "○", "role": "委員長", "comment": "…"}
    ],
    "QA": [
      {"mark": "○", "role": "質問者", "comment": "…"}
    ]
  }
]
```
`evaled_ids` が空配列の場合は空のリスト `[]` が返ります。
