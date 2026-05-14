<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    threshold: number;
    currentCount: number;
    description?: string;
    children?: Snippet;
  }

  let {
    title,
    threshold,
    currentCount,
    description,
    children,
  }: Props = $props();

  let locked = $derived(currentCount < threshold);
  let remaining = $derived(Math.max(0, threshold - currentCount));
  let percent = $derived(
    threshold === 0 ? 100 : Math.min(100, (currentCount / threshold) * 100),
  );
</script>

<div class="locked-wrap" class:locked>
  <div class="content" aria-hidden={locked ? 'true' : 'false'}>
    {@render children?.()}
  </div>

  {#if locked}
    <div class="overlay" role="status" aria-live="polite">
      <div class="lock-card">
        <div class="icon" aria-hidden="true">🔒</div>
        <div class="title-row">{title}</div>
        {#if description}
          <p class="desc">{description}</p>
        {/if}
        <div class="bar" aria-hidden="true">
          <div class="fill" style:width={`${percent}%`}></div>
        </div>
        <div class="hint">
          あと <strong>{remaining}</strong> 件の評価で解放
          <span class="frac">（{currentCount} / {threshold}）</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .locked-wrap {
    position: relative;
  }
  .content {
    transition: filter 240ms ease, opacity 240ms ease;
  }
  .locked .content {
    filter: blur(9px) saturate(0.55);
    opacity: 0.55;
    pointer-events: none;
    user-select: none;
  }
  .overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .lock-card {
    background: color-mix(in srgb, var(--surface) 88%, transparent);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-card);
    padding: 1.1rem 1.4rem 1.2rem;
    min-width: 260px;
    max-width: 88%;
    text-align: center;
    backdrop-filter: blur(6px) saturate(140%);
    -webkit-backdrop-filter: blur(6px) saturate(140%);
  }
  .icon {
    font-size: 1.7rem;
    margin-bottom: 0.35rem;
    filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.15));
  }
  .title-row {
    font-family: var(--font-display);
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 0.55rem;
    color: var(--text);
  }
  .desc {
    margin: 0 0 0.7rem;
    font-size: 0.8rem;
    color: var(--text-muted);
    line-height: 1.5;
  }
  .bar {
    width: 100%;
    height: 6px;
    background: var(--surface-alt);
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 0.45rem;
  }
  .fill {
    height: 100%;
    background: linear-gradient(90deg,
      color-mix(in srgb, var(--accent) 70%, transparent),
      var(--accent));
    border-radius: inherit;
    transition: width 420ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }
  .hint {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }
  .hint strong {
    color: var(--accent);
    font-weight: 700;
    font-size: 1.1em;
    margin: 0 0.1em;
  }
  .frac {
    opacity: 0.75;
    margin-left: 0.15rem;
  }

  /* ---------- HUD theme ---------- */
  :global([data-theme='hud']) .lock-card {
    background: rgba(7, 2, 15, 0.72);
    border-color: var(--accent);
    box-shadow: 0 0 22px rgba(0, 240, 255, 0.28),
      inset 0 0 12px rgba(0, 240, 255, 0.08);
  }
  :global([data-theme='hud']) .title-row {
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.55);
  }
  :global([data-theme='hud']) .icon {
    color: var(--accent-2);
    filter: drop-shadow(0 0 6px rgba(255, 43, 214, 0.6));
  }
  :global([data-theme='hud']) .fill {
    background: linear-gradient(90deg, var(--accent-2), var(--accent));
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
  }
  :global([data-theme='hud']) .hint strong {
    color: var(--accent-2);
    text-shadow: 0 0 6px rgba(255, 43, 214, 0.5);
  }

  /* ---------- Scroll (和紙) theme ---------- */
  :global([data-theme='scroll']) .lock-card {
    border: 1px solid var(--border);
    border-radius: 2px;
  }
  :global([data-theme='scroll']) .title-row {
    letter-spacing: 0.12em;
  }
  :global([data-theme='scroll']) .fill {
    background: var(--accent);
  }
</style>
