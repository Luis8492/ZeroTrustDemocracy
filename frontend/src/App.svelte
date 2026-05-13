<script lang="ts">
  import { onMount } from 'svelte';
  import Router, { link } from 'svelte-spa-router';
  import { evaluatedCount, initStores } from './lib/stores';
  import Home from './routes/Home.svelte';
  import Result from './routes/Result.svelte';
  import Settings from './routes/Settings.svelte';

  const routes = {
    '/': Home,
    '/result': Result,
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
    background: var(--surface);
    position: sticky;
    top: 0;
    z-index: 10;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }
  .brand {
    font-weight: 700;
    text-decoration: none;
    color: var(--text);
    font-family: var(--font-display);
  }
  .links {
    display: flex;
    gap: 0.75rem;
    margin-left: 1rem;
  }
  .links :global(a) {
    color: var(--text-muted);
    text-decoration: none;
  }
  .links :global(a:hover) {
    color: var(--accent);
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
  }
</style>
