# Scripts

補助的な Python スクリプトをまとめています。

## copy_setagaya_db.py

`app/db/minutes.db` を `app/db/setagaya.db` にコピーするスクリプトです。

### 使い方
```bash
python scripts/copy_setagaya_db.py
```
実行すると `Copied db/minutes.db -> db/setagaya.db` と表示されます。

## init_db.py

設定ファイルに基づいて SQLite データベースの空テーブルを作成します。

### 使い方
```bash
python scripts/init_db.py [municipality]
```
`municipality` を省略した場合は `setagaya` が使用されます。

## add_fetcher_column.py

`minutes` テーブルに `fetcher` 列を追加し、既存のファイル名にもフェッチャ名をプレフィックスとして付与します。

### 使い方
```bash
python scripts/add_fetcher_column.py [municipality]
```
`municipality` を省略した場合は `setagaya` が使用されます。

## remove_non_question_qas.py

設定ファイルに基づいて SQLite データベースから質問になっていない QA を削除します。

### 使い方
```bash
python scripts/remove_non_question_qas.py [municipality]
```
`municipality` を省略した場合は `setagaya` が使用されます。
実行すると削除した件数がログに表示されます。
