# App

議会議事録の解析やAPIサーバーを含むバックエンドコードを格納しています。

## 主なファイルとディレクトリ

- `feederAPI.py` - FastAPI アプリケーション
- `minute_converter.py` - 議事録を構造化データに変換
- `minute_analyzer.py` - 解析用スクリプト
- `anonymizer.py` - `PIIs/` 内のリストを用いて個人情報を匿名化
- `parsers/` - 議事録パーサーの実装
- `PIIs/` - 個人情報リスト
- `raw_minutes/` - サンプル議事録テキスト
- `name-party-table.csv` - 氏名と所属政党の対応表

## GET /api/qa/next へのレスポンス例
```json
{
    "id": 253,
    "committee_date": "2025年06月06日01号",
    "committee_name": "企画総務常任委員会",
    "topic_intro": [
        {
            "mark": "○",
            "role": "委員長",
            "comment": "次に、４閉会中の特定事件審査（調査）事項についてお諮りいたします。\n1.　区政の総合的企画及び調整について\n2.　行財政運営について\nとすることに御異議ございませんでしょうか。\n〔「異議なし」と呼ぶ者あり〕"
        },
        {
            "mark": "○",
            "role": "委員長",
            "comment": "異議なしと認め、そのように決定いたします。"
        }
    ],
    "QA": [],
    "eval_target": "◆"
}
```
