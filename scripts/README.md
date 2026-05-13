# Scripts

補助 Python スクリプト一覧です。`MUNICIPALITY` 引数を取るものは現状 `setagaya`
のみ受け付けます (定例会用は `--fetcher SetagayaRegularFetcher` で個別指定)。

## init_db.py

```bash
python scripts/init_db.py [municipality]
```
`<municipality>.yaml:db_path` で指定された SQLite ファイルにスキーマを作成します。

## add_fetcher_column.py / add_participants_column.py

旧スキーマからのマイグレーション補助。新規 DB では `utils/db.py:ensure_schema`
が同等処理を実行するため、通常は不要です。

## remove_non_question_qas.py / remove_duplicates.py

DB クリーンアップ用ユーティリティ。

## quality_check_setagaya_regular.py

`SetagayaRegularFetcher` が取得した HTML ファイルを `SetagayaRegularParser` に
かけて、Pattern1/2/3/Unknown の分布と抽出トピック数を集計します。Phase 0a で
利用したもの。

```bash
PYTHONIOENCODING=utf-8 python scripts/quality_check_setagaya_regular.py
```

## display_setagaya_minute.py / display_setagaya_regular_minute.py

指定した raw 議事録ファイルをパースして JSON で出力する開発用ツール。

```bash
python scripts/display_setagaya_minute.py SetagayaCommitteeFetcher_*.txt
python scripts/display_setagaya_regular_minute.py SetagayaRegularFetcher_*.html
```

## list_setagaya_regular_urls.py

定例会ページから議事録 URL を一覧表示します (Playwright)。
