# Frontend

Vite + Svelte 5 + TypeScript で構築された SPA。評価は IndexedDB に保存され、
サーバーには送信されません。

## 開発

```bash
npm install
npm run dev   # http://localhost:8001
```

`vite.config.ts` の `server.proxy` 設定により、`/api/*` は `localhost:8000` の
FastAPI バックエンドへフォワードされます。直接 `http://localhost:8000` を
叩く場合は `.env.local` で `VITE_API_BASE` を上書きできます。

## ビルド

```bash
npm run build      # dist/ に静的アセットを出力
npm run preview    # ビルド結果を 8001 番で配信
```

## 主な構造

- `src/main.ts` — エントリ
- `src/App.svelte` — レイアウト + ルーティング
- `src/routes/` — 画面 (`Home`, `Result`, `Settings`)
- `src/components/` — 再利用部品 (`SpeechList`, `EvalControls`)
- `src/lib/` — API クライアント / IndexedDB / 統計ロジック / 設定 store
- `src/themes/themes.css` — CSS 変数定義。`<html data-theme="...">` で切替

## テーマ

`Settings.svelte` で選択。現状は `plain` のみ有効。`chat`, `scroll`, `hud` は
Phase 2/3 で実装。
