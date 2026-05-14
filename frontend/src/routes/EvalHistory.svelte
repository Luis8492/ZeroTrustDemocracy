<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchMetaData } from '../lib/api';
  import { clearEvaluations, listEvaluations } from '../lib/db';
  import { refreshEvaluatedCount } from '../lib/stores';
  import type { QAMeta, EvaluationRecord } from '../lib/types';

  type MetaWithEval = QAMeta & { eval?: number; importance?: number };

  let count = $state(0);
  let busy = $state(true);
  let error = $state<string | null>(null);
  let allData = $state<MetaWithEval[]>([]);
  let questionerFilter = $state('');
  let partyFilter = $state('');

  async function load() {
    busy = true;
    error = null;
    try {
      const evaluations: EvaluationRecord[] = await listEvaluations();
      count = evaluations.length;
      if (count === 0) {
        allData = [];
        return;
      }
      const ids = evaluations.map((e) => e.QA_id);
      const metas = await fetchMetaData(ids);
      const evalMap = new Map(evaluations.map((e) => [e.QA_id, e]));
      allData = metas.map((m) => {
        const rec = evalMap.get(m.id);
        return { ...m, eval: rec?.eval, importance: rec?.importance };
      });
    } catch (e) {
      error = (e as Error).message;
    } finally {
      busy = false;
    }
  }

  function filtered(): MetaWithEval[] {
    return allData.filter(
      (d) =>
        (questionerFilter === '' || d.questioner === questionerFilter) &&
        (partyFilter === '' || d.questioner_party === partyFilter),
    );
  }

  function uniqueSorted(values: (string | undefined)[]): string[] {
    return [...new Set(values.filter((v): v is string => Boolean(v)))].sort();
  }

  async function handleClear() {
    if (count === 0) return;
    const ok = window.confirm(
      `評価履歴 ${count} 件をすべて削除します。この操作は取り消せません。よろしいですか？`,
    );
    if (!ok) return;
    await clearEvaluations();
    await refreshEvaluatedCount();
    await load();
  }

  onMount(load);
</script>

<h2>評価履歴</h2>

{#if busy}
  <p>読み込み中…</p>
{:else if error}
  <p class="error">エラー: {error}</p>
{:else if count === 0}
  <p>まだ評価がありません。<a href="#/">評価ページ</a>から始めてください。</p>
{:else}
  <div class="summary">
    <p>評価済みの発言 <strong>{count}</strong> 件</p>
    <button type="button" class="danger" onclick={handleClear}>
      評価履歴を削除
    </button>
  </div>

  <section class="filters">
    <label>
      議員
      <select bind:value={questionerFilter}>
        <option value="">すべて</option>
        {#each uniqueSorted(allData.map((d) => d.questioner)) as q (q)}
          <option value={q}>{q}</option>
        {/each}
      </select>
    </label>
    <label>
      会派
      <select bind:value={partyFilter}>
        <option value="">すべて</option>
        {#each uniqueSorted(allData.map((d) => d.questioner_party)) as p (p)}
          <option value={p}>{p}</option>
        {/each}
      </select>
    </label>
  </section>

  <section class="qa-list">
    {#each filtered() as item (item.id)}
      <article class="qa-card">
        <header>
          <strong>{item.questioner || '不明'}</strong>
          {#if item.questioner_party}<span class="party">{item.questioner_party}</span>{/if}
          <span class="eval">
            {#if item.eval !== undefined}同意 {item.eval > 0 ? `+${item.eval}` : item.eval}{/if}
            {#if item.importance !== undefined}<span class="importance">重要度 {item.importance}</span>{/if}
          </span>
        </header>
        <p class="committee">
          <span class="tag">{item.committee_name}</span>
          <span class="date">{item.committee_date}</span>
        </p>
        <ul>
          {#each item.QA as q, i (i)}
            <li>{q.mark}{q.comment}</li>
          {/each}
        </ul>
      </article>
    {:else}
      <p>該当する QA はありません</p>
    {/each}
  </section>
{/if}

<style>
  .summary {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: space-between;
    margin: 1rem 0 0.5rem;
  }
  .summary p { margin: 0; }
  .danger {
    background: transparent;
    color: #b00020;
    border: 1px solid #b00020;
    border-radius: var(--radius);
    padding: 0.4rem 0.9rem;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .danger:hover {
    background: #b00020;
    color: #fff;
  }
  .filters {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 1rem 0;
  }
  .filters select {
    margin-left: 0.25rem;
  }
  .qa-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .qa-card {
    border: 1px solid var(--border);
    background: var(--surface);
    border-radius: var(--radius);
    padding: 1rem;
    box-shadow: var(--shadow-card);
    transition: transform 120ms ease, box-shadow 120ms ease;
  }
  .qa-card:hover {
    box-shadow: var(--shadow-card-hover);
  }
  :global([data-theme='scroll']) .qa-card {
    border-radius: 2px;
    border-left: 4px double var(--accent);
  }
  :global([data-theme='hud']) .qa-card {
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-left: 3px solid var(--accent);
  }
  :global([data-theme='hud']) .qa-card .eval {
    font-family: var(--font-mono);
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
  }
  .qa-card header {
    display: flex;
    gap: 0.75rem;
    align-items: baseline;
    flex-wrap: wrap;
  }
  .party { color: var(--text-muted); font-size: 0.9rem; }
  .eval { color: var(--accent); font-weight: 600; margin-left: auto; display: inline-flex; gap: 0.6rem; align-items: baseline; }
  .importance { color: rgb(217, 119, 6); font-weight: 600; }
  .committee {
    margin: 0.25rem 0 0.75rem;
    color: var(--text-muted);
    font-size: 0.9rem;
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .committee .tag {
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    background: var(--accent);
    color: var(--accent-contrast);
    font-weight: 600;
    font-size: 0.78rem;
  }
  .committee .date { color: var(--text-muted); }
  .qa-card ul {
    margin: 0;
    padding-left: 1.25rem;
    list-style: '・ ';
  }
  .qa-card li {
    margin-bottom: 0.25rem;
    white-space: pre-wrap;
  }
  .error { color: #b00020; }
</style>
