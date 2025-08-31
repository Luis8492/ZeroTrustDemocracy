# Fetchers

議事録データをダウンロードするためのモジュール群です。
自治体ごとに `BaseMinuteFetcher` を継承したクラスを実装し、
検索条件の設定、議事録 URL の抽出、ファイルの保存処理を行います。

- `BaseMinuteFetcher.py` - フェッチャーの基本クラス。`set_search_setting_and_click_search`、`extract_minutes_urls`、`download_new_minutes` を実装して拡張します。
- `SetagayaFetcher.py` - 世田谷区議会の議事録を取得する実装例。

新しい自治体を追加する場合は同様のパターンでクラスを作成してください。
