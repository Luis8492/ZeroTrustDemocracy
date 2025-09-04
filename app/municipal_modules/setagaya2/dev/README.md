# pattern_classifier

`pattern_classifier.py` は世田谷区議会の議事録 HTML を構造的に分析し、以下の3パターンに分類するツールです。

## 対応パターン
1. **Pattern1: ネスト型（外側li＋内側ul/li）**
   `<li>` がトピックを表し、その中の `<ul><li>` に `<strong>質問</strong>` と `<strong>回答者</strong>` が並ぶ二段構造。
2. **Pattern2: 単一li＋強調タグ連結型**
   `<li><strong>Topic<br>質問</strong>本文<br><strong>回答者</strong>回答</li>` のように、冒頭の `<strong>` がトピックと質問を同時に含む。
3. **Pattern3: 単一li＋強調タグ分離型**
   `<li><strong>Topic</strong><br><strong>質問</strong>本文<br><strong>回答者</strong>回答</li>` と、トピック・質問・回答がそれぞれ独立した `<strong>` タグで囲まれる。

## 使い方
```bash
python pattern_classifier.py path/to/minutes.html [another.html ...]
```
各ファイルについて `Pattern1` `Pattern2` `Pattern3` `Unknown` のいずれかを出力します。
