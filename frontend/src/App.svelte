<script lang="ts">
  import { onMount } from 'svelte';
  import Router, { link } from 'svelte-spa-router';
  import { evaluatedCount, initStores } from './lib/stores';
  import Home from './routes/Home.svelte';
  import Result from './routes/Result.svelte';
  import EvalHistory from './routes/EvalHistory.svelte';
  import Settings from './routes/Settings.svelte';

  const routes = {
    '/': Home,
    '/result': Result,
    '/history': EvalHistory,
    '/settings': Settings,
  };

  let ready = $state(false);

  onMount(async () => {
    await initStores();
    ready = true;
  });
</script>

<header class="appbar">
  <a href="/" use:link class="brand">世田谷区議会QAナビ</a>
  <nav class="links">
    <a href="/" use:link>評価</a>
    <a href="/result" use:link>統計</a>
    <a href="/history" use:link>評価履歴</a>
    <a href="/settings" use:link>設定</a>
  </nav>
  <span class="counter" title="累積評価数">評価済 {$evaluatedCount}</span>
</header>

<main class="page">
  {#if ready}
    <Router {routes} />
  {:else}
    <p>初期化中…</p>
  {/if}
</main>

<style>
  .appbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    background: color-mix(in srgb, var(--surface) 80%, transparent);
    position: sticky;
    top: 0;
    z-index: 10;
    backdrop-filter: blur(10px) saturate(140%);
    -webkit-backdrop-filter: blur(10px) saturate(140%);
  }
  .brand {
    font-weight: 700;
    text-decoration: none;
    color: var(--text);
    font-family: var(--font-display);
    letter-spacing: 0.02em;
  }
  .links {
    display: flex;
    gap: 0.75rem;
    margin-left: 1rem;
  }
  .links :global(a) {
    color: var(--text-muted);
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    transition: color 120ms ease, background 120ms ease;
  }
  .links :global(a:hover) {
    color: var(--accent);
    background: var(--accent-soft, transparent);
  }
  .counter {
    margin-left: auto;
    font-variant-numeric: tabular-nums;
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  .page {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 1.5rem 1rem 4rem;
    position: relative;
    z-index: 2;
  }

  /* ---------- Scroll theme: 和紙 chrome ---------- */
  :global([data-theme='scroll']) .appbar {
    border-bottom: 1px solid var(--border);
    box-shadow: 0 2px 0 rgba(120, 80, 30, 0.08);
  }
  :global([data-theme='scroll']) .brand {
    font-family: var(--font-display);
    letter-spacing: 0.12em;
  }
  :global([data-theme='scroll']) .brand::before {
    content: '〠 ';
    color: var(--accent);
  }

  /* ---------- HUD theme: neon chrome ---------- */
  :global([data-theme='hud']) .appbar {
    background: linear-gradient(180deg,
      rgba(7, 2, 15, 0.85),
      rgba(7, 2, 15, 0.55));
    border-bottom: 1px solid var(--accent);
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.25);
  }
  :global([data-theme='hud']) .brand {
    font-family: var(--font-display);
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.95rem;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
  }
  :global([data-theme='hud']) .brand::before {
    content: '◣ ';
    color: var(--accent-2);
  }
  :global([data-theme='hud']) .links :global(a) {
    font-family: var(--font-mono);
    text-transform: uppercase;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    color: var(--text-muted);
  }
  :global([data-theme='hud']) .links :global(a:hover) {
    color: var(--accent);
    background: rgba(0, 240, 255, 0.08);
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
  }
  :global([data-theme='hud']) .counter {
    font-family: var(--font-mono);
    color: var(--accent-2);
    text-shadow: 0 0 6px rgba(255, 43, 214, 0.4);
  }
</style>
