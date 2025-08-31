# Frontend

Vanilla JS と IndexedDB を用いた静的フロントエンドです。

## 主なファイル
- `index.html` - 評価画面のエントリーポイント
- `main.js` - 初期化処理とイベントハンドラ
- `api.js` - API 通信用のヘルパー
- `db.js` - IndexedDB へのアクセス
- `result.html` - 評価結果表示ページ
- `stats.js` - 結果ページの描画ロジック
- `components/` - UI コンポーネント群

## 開発用サーバーの起動
```bash
cd frontend
python3 -m http.server 8001
```
