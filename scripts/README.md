# Scripts

補助スクリプト一覧です。`--municipality` を取るスクリプトは `<municipality>.yaml`
(バンドルされた `sample/` または `MUNICIPAL_MODULES_PATH` 経由の外部プラグイン) を
解決して動作します。各スクリプトはリポジトリのルートから実行してください。

## DB 初期化

### init_db.py

`<municipality>.yaml:db_path` で指定された SQLite ファイルにスキーマを作成します。

```bash
python scripts/init_db.py [municipality]   # 省略時 sample
```

## 評価データ生成 (フロントエンドの統計画面テスト用)

### generate_mock_evaluations.py

DB 内の全 QA に対しランダムな同意度 (-3〜+3) と重要度 (0〜3) を割り当てた
CSV を生成します。出力ファイルは統計画面の「CSV で読み込み」から取り込めます。

```bash
python scripts/generate_mock_evaluations.py [--db db/sample.db] [-o mock_evaluations.csv] [--seed 42]
```

## DB クリーンアップ

### remove_duplicates.py

`minutes` / `meetings` / `downloaded_minutes_url_helper` / `questions` の各
テーブルから重複行を削除します。

```bash
python scripts/remove_duplicates.py [--municipality sample]
```

### remove_non_question_qas.py

`questions` テーブルから「◆」マーク (質問者発言) を含まない行を削除します。

```bash
python scripts/remove_non_question_qas.py [municipality]   # 省略時 sample
```

## 本番デプロイ用エクスポート

### export_static_data.py

SQLite から `frontend/public/data/` (または `--out` 指定先 / `EXPORT_OUTPUT_DIR`)
配下に静的 JSON (index + 会議別) を出力します。匿名化と政党解決はここで
適用されます。`index.json` には YAML config の `data_sources:` が転載され、
フロントエンドのフッター/Aboutに描画されます。

```bash
python scripts/export_static_data.py [--municipality sample] [--out <dir>]
```

## 議会固有のデバッグスクリプトについて

`display_*_minute.py` や `quality_check_*` のような議会固有のデバッグスクリプトは
**各 private 運用リポジトリ側に置く**運用です。本フレームワークには汎用のもの
だけを残しています。
