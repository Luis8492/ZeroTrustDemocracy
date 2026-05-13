<script lang="ts">
  import { onMount } from 'svelte';
  import {
    Chart,
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
    type ChartConfiguration,
  } from 'chart.js';
  import {
    BarWithErrorBarsController,
    BarWithErrorBar,
  } from 'chartjs-chart-error-bars';
  import { fetchMetaData } from '../lib/api';
  import { listEvaluations, saveEvaluation } from '../lib/db';
  import { refreshEvaluatedCount } from '../lib/stores';
  import { computeGroupedStats, type GroupStat } from '../lib/stats';
  import type { QAMeta, EvaluationRecord } from '../lib/types';
  import TopicMap from '../components/TopicMap.svelte';

  Chart.register(
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend,
    BarWithErrorBarsController,
    BarWithErrorBar,
  );

  type MetaWithEval = QAMeta & { eval?: number };

  let count = $state(0);
  let busy = $state(true);
  let error = $state<string | null>(null);
  let allData = $state<MetaWithEval[]>([]);
  let questionerFilter = $state('');
  let partyFilter = $state('');
  let questionerCanvas: HTMLCanvasElement | undefined = $state();
  let partyCanvas: HTMLCanvasElement | undefined = $state();
  let questionerChart: Chart | undefined;
  let partyChart: Chart | undefined;

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
      const evalMap = new Map(evaluations.map((e) => [e.QA_id, e.eval]));
      allData = metas.map((m) => ({ ...m, eval: evalMap.get(m.id) }));
      renderCharts();
    } catch (e) {
      error = (e as Error).message;
    } finally {
      busy = false;
    }
  }

  function renderCharts() {
    const questionerStats = computeGroupedStats(
      allData,
      (m) => m.eval,
      (m) => m.questioner,
    );
    renderChart(questionerCanvas, questionerChart, questionerStats, '議員別平均評価', (c) => {
      questionerChart = c;
    });

    const partyStats = computeGroupedStats(
      allData.filter((m) => m.questioner_party),
      (m) => m.eval,
      (m) => m.questioner_party,
    );
    renderChart(partyCanvas, partyChart, partyStats, '会派別平均評価', (c) => {
      partyChart = c;
    });
  }

  function renderChart(
    canvas: HTMLCanvasElement | undefined,
    existing: Chart | undefined,
    stats: GroupStat[],
    label: string,
    assign: (c: Chart) => void,
  ) {
    if (!canvas) return;
    if (existing) existing.destroy();
    const labels = stats.map((s) => `${s.key} (n=${s.count})`);
    const data = stats.map((s) => ({
      y: s.mean,
      yMin: s.mean - s.ci,
      yMax: s.mean + s.ci,
    }));
    // Chart.js extension types are loose; cast through unknown to avoid
    // false positives from the plugin's structural-typing leaks.
    const config = {
      type: 'barWithErrorBars',
      data: {
        labels,
        datasets: [
          {
            label,
            data,
            backgroundColor: 'rgba(37, 99, 235, 0.4)',
            borderColor: 'rgba(37, 99, 235, 1)',
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: { y: { min: -3, max: 3 } },
      },
    };
    const chart = new Chart(canvas, config as unknown as ChartConfiguration);
    assign(chart);
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

  async function exportCSV() {
    const evaluations = await listEvaluations();
    if (!evaluations.length) return;
    const csv = 'QA_id,eval\n' + evaluations.map((e) => `${e.QA_id},${e.eval}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'evaluations.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importCSV(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || !input.files.length) return;
    const text = await input.files[0].text();
    const lines = text.trim().split(/\r?\n/).slice(1);
    for (const line of lines) {
      const [idStr, evalStr] = line.split(',');
      const id = Number(idStr);
      const value = Number(evalStr);
      if (!Number.isNaN(id) && !Number.isNaN(value)) {
        await saveEvaluation({ QA_id: id, eval: value });
      }
    }
    await refreshEvaluatedCount();
    await load();
  }

  onMount(load);
</script>

<h2>評価結果</h2>

{#if busy}
  <p>集計中…</p>
{:else if error}
  <p class="error">エラー: {error}</p>
{:else if count === 0}
  <p>まだ評価がありません。<a href="#/">評価ページ</a>から始めてください。</p>
{:else}
  <p>累積評価数: <strong>{count}</strong></p>

  <section class="charts">
    <canvas bind:this={questionerCanvas} width="800" height="320"></canvas>
    <canvas bind:this={partyCanvas} width="800" height="320"></canvas>
  </section>

  <TopicMap items={allData} />

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
          {#if item.eval !== undefined}<span class="eval">評価 {item.eval > 0 ? `+${item.eval}` : item.eval}</span>{/if}
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

<section class="io">
  <h3>データ入出力</h3>
  <button type="button" onclick={exportCSV}>評価データを CSV で書き出し</button>
  <label class="import">
    CSV で読み込み
    <input type="file" accept=".csv" onchange={importCSV} />
  </label>
</section>

<style>
  .charts {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin: 1rem 0;
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
  }
  .qa-card header {
    display: flex;
    gap: 0.75rem;
    align-items: baseline;
    flex-wrap: wrap;
  }
  .party { color: var(--text-muted); font-size: 0.9rem; }
  .eval { color: var(--accent); font-weight: 600; margin-left: auto; }
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
  .io {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px dashed var(--border);
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }
  .import { display: inline-flex; gap: 0.5rem; align-items: center; }
  .error { color: #b00020; }
</style>
