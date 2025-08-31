# Parsers

議事録を構造化データに変換するパーサーの実装を含みます。
自治体ごとに `BaseMinuteParser` を継承したクラスを作成し、
テキストから発言者や発言内容などを抽出してデータ化します。

- `base_minute_parser.py` - 共通の基底クラス。`extract_meeting_data`、`extract_topic_section`、`extract_speeches` を実装して拡張します。
- `setagaya_parser.py` - 世田谷区議会向けの具体的な実装例。

新しい自治体に対応させる場合は同様の構成でパーサーを追加してください。
