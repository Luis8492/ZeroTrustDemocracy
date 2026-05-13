<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchNextQA, isQA } from '../lib/api';
  import { listEvaluatedIDs, saveEvaluation } from '../lib/db';
  import { refreshEvaluatedCount } from '../lib/stores';
  import type { QA } from '../lib/types';
  import SpeechList from '../components/SpeechList.svelte';
  import EvalControls from '../components/EvalControls.svelte';

  let qa = $state<QA | null>(null);
  let allDone = $state(false);
  let evalValue = $state(0);
  let importanceValue = $state(0);
  let busy = $state(false);
  let error = $state<string | null>(null);

  async function loadNext() {
    busy = true;
    error = null;
    try {
      const ids = await listEvaluatedIDs();
      const res = await fetchNextQA(ids);
      if (isQA(res)) {
        qa = res;
        allDone = false;
        evalValue = 0;
        importanceValue = 0;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        qa = null;
        allDone = true;
      }
    } catch (e) {
      error = (e as Error).message;
    } finally {
      busy = false;
    }
  }

  async function submitEval(value: number, importance: number) {
    if (!qa) return;
    await saveEvaluation({ QA_id: qa.id, eval: value, importance });
    await refreshEvaluatedCount();
    await loadNext();
  }

  onMount(loadNext);
</script>

{#if error}
  <p class="error">エラー: {error}</p>
  <button type="button" onclick={loadNext}>再試行</button>
{:else if allDone}
  <p>すべての質疑を評価しました 🎉</p>
{:else if qa}
  <section class="qa">
    <header class="meta">
      <div class="tags">
        <span class="tag committee">{qa.committee_name}</span>
        <span class="tag date">{qa.committee_date}</span>
      </div>
    </header>

    {#if qa.topic_intro.length}
      <details class="intro" open>
        <summary>議題の前提</summary>
        <SpeechList speeches={qa.topic_intro} />
      </details>
    {/if}

    <section class="body">
      <h3>質疑応答</h3>
      <SpeechList speeches={qa.QA} emptyLabel="（質疑が含まれませんでした）" />
    </section>

    <section class="eval">
      <h3>評価</h3>
      <EvalControls
        bind:evalValue
        bind:importanceValue
        disabled={busy}
        onSubmit={submitEval}
      />
      <button class="skip" type="button" disabled={busy} onclick={loadNext}>
        スキップして別の質疑を表示
      </button>
    </section>
  </section>
{:else}
  <p>読み込み中…</p>
{/if}

<style>
  .qa {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  .tag {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.8rem;
    border: 1px solid var(--border);
    background: var(--surface-alt);
    color: var(--text-muted);
  }
  .tag.committee {
    background: var(--accent);
    color: var(--accent-contrast);
    border-color: var(--accent);
    font-weight: 600;
  }
  .intro summary {
    cursor: pointer;
    color: var(--text-muted);
    font-size: 0.95rem;
    padding: 0.25rem 0;
  }
  .body h3, .eval h3 {
    margin: 0 0 0.5rem;
    font-size: 1rem;
    color: var(--text-muted);
    font-weight: 600;
  }
  .skip {
    margin-top: 0.5rem;
    align-self: center;
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 0.85rem;
    cursor: pointer;
    text-decoration: underline;
  }
  .error { color: #b00020; }
</style>
