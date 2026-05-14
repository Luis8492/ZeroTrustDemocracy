<script lang="ts">
  import { theme } from '../lib/stores';
  import type { ThemeName } from '../lib/types';

  interface ThemeOption {
    value: ThemeName;
    label: string;
    description: string;
    enabled: boolean;
  }

  const options: ThemeOption[] = [
    {
      value: 'plain',
      label: 'プレーン',
      description: '装飾を抑えた既定の見た目。可読性重視。',
      enabled: true,
    },
    {
      value: 'chat',
      label: 'チャット風',
      description:
        '質問者と答弁者を吹き出しで表現。委員長の発言は中央にシステムメッセージ風で表示。',
      enabled: true,
    },
    {
      value: 'scroll',
      label: '和風',
      description:
        '和紙の風合いと明朝体、朱の差し色を用いた古文書風レイアウト。',
      enabled: true,
    },
    {
      value: 'hud',
      label: 'サイバーパンク',
      description:
        'ネオン・スキャンライン・グリッドで構成したダーク UI。シアン + マゼンタの二色アクセント。',
      enabled: true,
    },
  ];
</script>

<h2>設定</h2>

<section>
  <h3>テーマ</h3>
  <p class="hint">質疑表示の見た目を切り替えます。設定はブラウザ内に保存されます。</p>
  <ul class="themes">
    {#each options as opt (opt.value)}
      <li>
        <label class:disabled={!opt.enabled}>
          <input
            type="radio"
            name="theme"
            value={opt.value}
            checked={$theme === opt.value}
            disabled={!opt.enabled}
            onchange={() => ($theme = opt.value)}
          />
          <div>
            <strong>{opt.label}</strong>
            {#if !opt.enabled}<span class="badge">準備中</span>{/if}
            <p>{opt.description}</p>
          </div>
        </label>
      </li>
    {/each}
  </ul>
</section>

<style>
  .hint { color: var(--text-muted); font-size: 0.9rem; }
  .themes {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .themes label {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    background: var(--surface);
    cursor: pointer;
  }
  .themes label.disabled { opacity: 0.6; cursor: not-allowed; }
  .themes p { margin: 0.25rem 0 0; color: var(--text-muted); font-size: 0.9rem; }
  .badge {
    margin-left: 0.5rem;
    background: var(--surface-alt);
    color: var(--text-muted);
    padding: 0.1rem 0.5rem;
    font-size: 0.75rem;
    border-radius: 999px;
  }
</style>
