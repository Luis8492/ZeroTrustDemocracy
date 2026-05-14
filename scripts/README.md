# Scripts

補助スクリプト一覧です。`MUNICIPALITY` 引数を取るものは現状 `setagaya` のみ
受け付けます。各スクリプトはリポジトリのルートから実行してください。

## DB 初期化

### init_db.py

`<municipality>.yaml:db_path` で指定された SQLite ファイルにスキーマを作成します。

```bash
python scripts/init_db.py [municipality]   # municipality は省略時 setagaya
```

## 評価データ生成 (フロントエンドの統計画面テスト用)

### generate_mock_evaluations.py

DB 内の全 QA に対しランダムな同意度 (-3〜+3) と重要度 (0〜3) を割り当てた
CSV を生成します。出力ファイルは統計画面の「CSV で読み込み」から取り込めます。

```bash
python scripts/generate_mock_evaluations.py [--db db/setagaya.db] [-o mock_evaluations.csv] [--seed 42]
```

## パーサ開発・デバッグ

### display_setagaya_minute.py / display_setagaya_regular_minute.py

指定した raw 議事録ファイルをパーサにかけて構造化 JSON を標準出力します。

```bash
python scripts/display_setagaya_minute.py SetagayaCommitteeFetcher_<...>.txt
python scripts/display_setagaya_regular_minute.py SetagayaRegularFetcher_<...>.html
```

ファイル名は `app/raw_minutes/` 配下の相対パスで指定します。

### quality_check_setagaya_regular.py

`app/raw_minutes/` 内の `SetagayaRegularFetcher_*.html` 全件を
`SetagayaRegularParser` にかけて Pattern1/2/3/Unknown の分布と抽出トピック数を
集計します。定例会パーサ改修時の回帰チェックに使えます。

```bash
PYTHONIOENCODING=utf-8 python scripts/quality_check_setagaya_regular.py
```

## DB クリーンアップ

### remove_duplicates.py

`minutes` / `meetings` / `downloaded_minutes_url_helper` / `questions` の各
テーブルから重複行を削除します。DB パスは `db/setagaya.db` 固定。

```bash
python scripts/remove_duplicates.py
```

### remove_non_question_qas.py

`questions` テーブルから「◆」マーク (質問者発言) を含まない行を削除します。

```bash
python scripts/remove_non_question_qas.py [municipality]   # 省略時 setagaya
```

## 本番デプロイ用エクスポート

### export_static_data.py

SQLite から `frontend/public/data/` 配下に静的 JSON (index + 会議別) を出力します。
匿名化と政党解決はここで適用されます。Cloudflare Pages へのデプロイは
この出力ディレクトリを `npm run build` 経由で配信します。

```bash
python scripts/export_static_data.py [--municipality setagaya] [--out <dir>]
```
