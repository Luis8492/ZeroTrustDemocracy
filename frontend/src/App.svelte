<script lang="ts">
  import { onMount } from 'svelte';
  import Router, { link, push, location } from 'svelte-spa-router';
  import { evaluatedCount, initStores } from './lib/stores';
  import { getOnboardingCompleted, setOnboardingCompleted, countEvaluations } from './lib/db';
  import Home from './routes/Home.svelte';
  import Result from './routes/Result.svelte';
  import EvalHistory from './routes/EvalHistory.svelte';
  import Settings from './routes/Settings.svelte';
  import About from './routes/About.svelte';
  import Onboarding from './routes/Onboarding.svelte';

  const routes = {
    '/': Home,
    '/onboarding': Onboarding,
    '/result': Result,
    '/history': EvalHistory,
    '/settings': Settings,
    '/about': About,
  };

  let ready = $state(false);
  let menuOpen = $state(false);

  // ルート変更時はメニューを閉じる（モバイルで遷移後にメニューが残らないように）。
  $effect(() => {
    $location;
    menuOpen = false;
  });

  function toggleMenu() {
    menuOpen = !menuOpen;
  }
  function closeMenu() {
    menuOpen = false;
  }

  onMount(async () => {
    // IndexedDB が何らかの理由でハング/拒否しても画面が固まらないように、
    // 安全弁として 4 秒で強制的に描画開始する。
    const safety = window.setTimeout(() => {
      if (!ready) {
        console.error('App init timeout — rendering anyway');
        ready = true;
      }
    }, 4000);

    let shouldRedirectOnboarding = false;
    try {
      await initStores();
      // 初回訪問者をオンボーディングへ誘導する。
      const completed = await getOnboardingCompleted();
      if (!completed) {
        // オンボーディング機能導入前から使っている既存ユーザーは
        // 評価済み件数で判定して、ツアーをスキップする。
        const existing = await countEvaluations();
        if (existing > 0) {
          await setOnboardingCompleted(true);
        } else {
          const hash = window.location.hash;
          const isRoot = hash === '' || hash === '#' || hash === '#/';
          if (isRoot) shouldRedirectOnboarding = true;
        }
      }
    } catch (e) {
      console.error('App init failed:', e);
    } finally {
      window.clearTimeout(safety);
      if (shouldRedirectOnboarding) push('/onboarding');
      ready = true;
    }
  });
</script>

<header class="appbar">
  <a href="/" use:link class="brand" onclick={closeMenu}>世田谷区議会QAナビ</a>
  <nav class="links" class:open={menuOpen} id="primary-nav">
    <a href="/" use:link onclick={closeMenu}>評価</a>
    <a href="/result" use:link onclick={closeMenu}>統計</a>
    <a href="/history" use:link onclick={closeMenu}>評価履歴</a>
    <a href="/settings" use:link onclick={closeMenu}>設定</a>
    <a href="/about" use:link onclick={closeMenu}>このサイトについて</a>
  </nav>
  <span class="counter" title="累積評価数">
    <span class="counter-label">評価済み</span>
    <span class="counter-num">{$evaluatedCount}</span>
  </span>
  <button
    type="button"
    class="menu-toggle"
    class:open={menuOpen}
    aria-label="メニュー"
    aria-expanded={menuOpen}
    aria-controls="primary-nav"
    onclick={toggleMenu}
  >
    <span class="bar"></span>
    <span class="bar"></span>
    <span class="bar"></span>
  </button>
</header>
{#if menuOpen}
  <button
    type="button"
    class="menu-scrim"
    aria-label="メニューを閉じる"
    onclick={closeMenu}
  ></button>
{/if}

<main class="page">
  {#if ready}
    <Router {routes} />
  {:else}
    <p>初期化中…</p>
  {/if}
</main>

<footer class="sitefoot">
  <p class="source">
    データ出典: <a href="https://www.city.setagaya.lg.jp/gikai/index.html" target="_blank" rel="noopener noreferrer">世田谷区議会 会議録</a>
    ／
    <a href="https://kugi.city.setagaya.tokyo.jp/voices/" target="_blank" rel="noopener noreferrer">世田谷区議会 会議録検索システム</a>
  </p>
  <p class="disclaimer">
    本サービスは有志によるもので、世田谷区および世田谷区議会の公式見解・公式サービスではありません。
    会議録の構造化処理上、原文と異なる表示や誤りを含む可能性があります。
    正確な内容は出典元をご確認ください。
    詳しくは <a href="#/about">このサイトについて</a> をご覧ください。
  </p>
  <p class="contact">
    削除依頼・誤り報告・お問い合わせは
    <a href="https://github.com/Luis8492/ZeroTrustDemocracy/issues" target="_blank" rel="noopener noreferrer">GitHub Issues</a>
    までお願いします。
  </p>
</footer>

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
    display: inline-flex;
    align-items: baseline;
    gap: 0.4rem;
    font-family: var(--font-display);
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--text);
    font-variant-numeric: tabular-nums;
  }
  .counter-num {
    color: var(--accent);
  }

  /* ハンバーガーボタン: モバイル時のみ表示する */
  .menu-toggle {
    display: none;
    width: 40px;
    height: 40px;
    padding: 0;
    margin-left: 0.25rem;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    position: relative;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 5px;
    transition: background 120ms ease, border-color 120ms ease;
  }
  .menu-toggle:hover {
    background: var(--accent-soft, transparent);
    border-color: var(--accent);
  }
  .menu-toggle .bar {
    display: block;
    width: 20px;
    height: 2px;
    background: var(--text);
    border-radius: 2px;
    transition: transform 180ms ease, opacity 180ms ease;
  }
  .menu-toggle.open .bar:nth-child(1) {
    transform: translateY(7px) rotate(45deg);
  }
  .menu-toggle.open .bar:nth-child(2) {
    opacity: 0;
  }
  .menu-toggle.open .bar:nth-child(3) {
    transform: translateY(-7px) rotate(-45deg);
  }

  /* メニューの背後タップ領域 (モバイルのみ表示) */
  .menu-scrim {
    display: none;
    position: fixed;
    inset: 0;
    background: transparent;
    border: 0;
    padding: 0;
    z-index: 8;
    cursor: default;
  }

  @media (max-width: 720px) {
    .appbar {
      gap: 0.5rem;
      padding: 0.6rem 0.75rem;
    }
    .brand {
      font-size: 0.95rem;
    }
    .counter {
      margin-left: auto;
      font-size: 0.85rem;
    }
    .counter-label {
      display: none;
    }
    .counter-num::before {
      content: '★ ';
      color: var(--accent);
    }
    .menu-toggle {
      display: flex;
    }
    .menu-scrim {
      display: block;
    }
    .links {
      position: absolute;
      top: 100%;
      right: 0.5rem;
      left: auto;
      margin-left: 0;
      flex-direction: column;
      align-items: stretch;
      gap: 0.15rem;
      min-width: 12rem;
      padding: 0.5rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
      transform-origin: top right;
      transform: scale(0.96) translateY(-4px);
      opacity: 0;
      pointer-events: none;
      transition: transform 140ms ease, opacity 140ms ease;
      z-index: 9;
    }
    .links.open {
      transform: scale(1) translateY(0);
      opacity: 1;
      pointer-events: auto;
    }
    .links :global(a) {
      padding: 0.6rem 0.75rem;
      border-radius: 6px;
      font-size: 0.95rem;
    }
  }
  .page {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 1.5rem 1rem 4rem;
    position: relative;
    z-index: 2;
  }

  .sitefoot {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 1.25rem 1rem 2rem;
    border-top: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.8rem;
    line-height: 1.6;
    position: relative;
    z-index: 2;
  }
  .sitefoot p {
    margin: 0.25rem 0;
  }
  .sitefoot a {
    color: var(--text-muted);
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  .sitefoot a:hover {
    color: var(--accent);
  }
  .sitefoot .disclaimer {
    opacity: 0.85;
  }

  /* HUD theme footer tweaks */
  :global([data-theme='hud']) .sitefoot {
    font-family: var(--font-mono);
    border-top-color: var(--accent);
    color: var(--text-muted);
  }
  :global([data-theme='hud']) .sitefoot a {
    color: var(--accent);
  }

  /* Scroll theme footer tweaks */
  :global([data-theme='scroll']) .sitefoot {
    font-family: var(--font-display);
    letter-spacing: 0.04em;
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
    font-family: var(--font-display);
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.95rem;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
  }
  :global([data-theme='hud']) .counter-num {
    color: var(--accent-2);
    text-shadow: 0 0 10px rgba(255, 43, 214, 0.6);
  }
  :global([data-theme='scroll']) .counter {
    font-family: var(--font-display);
    letter-spacing: 0.12em;
  }

  /* ---------- メニューボタン: テーマ別 ---------- */
  :global([data-theme='hud']) .menu-toggle {
    border-color: var(--accent);
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.25);
  }
  :global([data-theme='hud']) .menu-toggle .bar {
    background: var(--accent);
    box-shadow: 0 0 6px rgba(0, 240, 255, 0.5);
  }
  :global([data-theme='hud']) .menu-toggle:hover {
    background: rgba(0, 240, 255, 0.08);
  }
  :global([data-theme='scroll']) .menu-toggle {
    border-color: var(--border);
  }
  :global([data-theme='scroll']) .menu-toggle .bar {
    background: var(--text);
  }

  /* ---------- ドロップダウン: テーマ別 ---------- */
  @media (max-width: 720px) {
    :global([data-theme='hud']) .links {
      background: rgba(7, 2, 15, 0.95);
      border-color: var(--accent);
      box-shadow: 0 0 24px rgba(0, 240, 255, 0.35);
    }
    :global([data-theme='scroll']) .links {
      background: var(--surface);
      border-color: var(--border);
      box-shadow: 0 6px 18px rgba(120, 80, 30, 0.18);
    }
  }
</style>
