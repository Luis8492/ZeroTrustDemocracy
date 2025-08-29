# Zero Trust Democracy

**ZeroTrustDemocracy**は、議会の議事録等のデータをより分かりやすい形でユーザーに提示することで、民主的な意思決定への市民参加を支援することを目的としています。

---

## 🎯 プロジェクトの目的
現在は第一段階にありますが、将来的にはこのリポジトリはより大きなプロジェクトの一部となる予定です。
- 地方議会の議事録を自動的に解析し、議員の発言を「質疑応答ペア（QA）」として構造化。
- ユーザーがそれらのQAを匿名で評価し、政治家の姿勢や論点に対する自身の反応を統計的に分析・可視化。
- クライアントサイドにデータを保持することで、ユーザーのプライバシーを最大限に尊重。

---

## 🧩 機能概要

### ✅ 議事録抽出・解析（Pythonスクリプト）
- 議会議事録テキストから以下を抽出：
  - 会議情報（日時、委員会名）
  - トピック単位の発言群
  - 質問者・答弁者の発言を分離しQA化
  - 個人情報を匿名化（`anonymizer.py`）

- SQLite3にメタデータ（会議情報、質問者、topic_introなど）を保存

---

### ✅ APIサーバー（FastAPI）
- **`POST /api/qa/meta`**: 評価済みIDのQAメタ情報を返す（会議名と日次を含む）
- **`POST /api/qa/next`**: ユーザー未評価のQAをランダムに1件返す
  - 詳しい入出力仕様は[APIドキュメント](API.md)を参照してください。

---

### ✅ フロントエンド（Vanilla JS + IndexedDB）
- ページ表示時に`/api/qa/next`を呼び出し、QAを表示
- ユーザーが-3～+3で評価 → IndexedDBに保存（評価はクライアントにのみ保持）
- 評価済みIDはIndexedDBから取得し、APIに渡して未評価QAを取得
- (未実装)ある程度評価がたまってきたら、評価済みのQAのメタ情報をサーバーから取得し、評価結果と併せてユーザーの評価傾向を可視化(e.g.○○党の主張には賛成傾向)

---

### ✅ 匿名性・セキュリティ配慮
- 評価データやユーザーID等の情報は**一切サーバーに送信しない**
- ユーザーごとのローカルストレージ（IndexedDB）で管理
- CORS設定済み、POSTベースのAPI設計で安全性向上

---

## 🛠️ 技術スタック

| 分類 | 技術 |
|------|------|
| バックエンド | Python 3, FastAPI, SQLite3 |
| フロントエンド | HTML, JavaScript (ES Modules), IndexedDB |
| クライアントDB | [idb](https://github.com/jakearchibald/idb) (IndexedDB wrapper) |
| ローカルサーバー | `python3 -m http.server 8000` など |
| 匿名化 | `anonymizer.py`（PIIリストによる置換） |
| データ変換 | 議事録を構造化JSONへ変換するPythonスクリプト |

---

## 📦 ローカル開発

### 初回セットアップ

```bash
# Python側 API サーバーを起動
cd ZeroTrustDemocracy
python3 -m uvicorn app.feederAPI:app --host 0.0.0.0 --port 8000

# フロントエンド（別ターミナル）
cd frontend
python3 -m http.server 8001
# => アクセス: http://localhost:8001/index.html
