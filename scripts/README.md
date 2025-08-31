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
