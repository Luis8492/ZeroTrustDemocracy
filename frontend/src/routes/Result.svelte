<script lang="ts">
  import { onMount, tick } from 'svelte';
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
  import Locked from '../components/Locked.svelte';

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

  type MetaWithEval = QAMeta & { eval?: number; importance?: number };

  // Progressive unlock thresholds (件数).
  const TH_PARTY = 3;
  const TH_COMMITTEE = 5;
  const TH_QUESTIONER = 15;
  const TH_TOPIC_MAP = 30;

  // ロック中のグラフ背面に置くダミーデータ。実値は読めない（ブラー＋オーバーレイ）
  // ので、形状だけそれっぽく見せれば十分。
  const DUMMY_PARTY_STATS: GroupStat[] = [
    { key: '◆会派', mean: 1.6, ci: 0.5, count: 8 },
    { key: '◇会派', mean: 0.7, ci: 0.4, count: 6 },
    { key: '□会派', mean: -0.4, ci: 0.6, count: 5 },
    { key: '△会派', mean: -1.3, ci: 0.7, count: 4 },
  ];
  const DUMMY_COMMITTEE_STATS: GroupStat[] = [
    { key: '総務', mean: 2.2, ci: 0.3, count: 11 },
    { key: '福祉保健', mean: 1.7, ci: 0.4, count: 9 },
    { key: '都市整備', mean: 1.3, ci: 0.5, count: 7 },
    { key: '区民生活', mean: 0.9, ci: 0.4, count: 5 },
    { key: '文教', mean: 0.5, ci: 0.5, count: 4 },
  ];
  const DUMMY_QUESTIONER_STATS: GroupStat[] = [
    { key: '議員A', mean: 1.9, ci: 0.4, count: 6 },
    { key: '議員B', mean: 1.2, ci: 0.5, count: 5 },
    { key: '議員C', mean: 0.4, ci: 0.6, count: 4 },
    { key: '議員D', mean: -0.7, ci: 0.7, count: 4 },
    { key: '議員E', mean: -1.6, ci: 0.6, count: 3 },
  ];

  function makeDummyTopicItems(): MetaWithEval[] {
    const committees = ['総務委員会', '福祉保健委員会', '都市整備委員会', '区民生活委員会', '文教委員会', '企画総務委員会'];
    const questioners = ['議員 A', '議員 B', '議員 C', '議員 D'];
    const items: MetaWithEval[] = [];
    let id = -1;
    committees.forEach((c, ci) => {
      const n = 4 - (ci % 3);
      for (let i = 0; i < n; i++) {
        items.push({
          id: id--,
          uuid: `dummy-${ci}-${i}`,
          questioner: questioners[(ci + i) % questioners.length],
          questioner_party: '',
          committee_date: '',
          committee_name: c,
          topic_intro: [],
          QA: [],
          eval: ((ci + i) % 5) - 2,
          importance: (ci + i) % 4,
        });
      }
    });
    return items;
  }
  const DUMMY_TOPIC_ITEMS = makeDummyTopicItems();

  let count = $state(0);
  let busy = $state(true);
  let error = $state<string | null>(null);
  let allData = $state<MetaWithEval[]>([]);
  let questionerCanvas: HTMLCanvasElement | undefined = $state();
  let partyCanvas: HTMLCanvasElement | undefined = $state();
  let topicImportanceCanvas: HTMLCanvasElement | undefined = $state();
  let questionerChart: Chart | undefined;
  let partyChart: Chart | undefined;
  let topicImportanceChart: Chart | undefined;

  async function load() {
    busy = true;
    error = null;
    try {
      const evaluations: EvaluationRecord[] = await listEvaluations();
      count = evaluations.length;
      if (count === 0) {
        allData = [];
      } else {
        const ids = evaluations.map((e) => e.QA_id);
        const metas = await fetchMetaData(ids);
        const evalMap = new Map(evaluations.map((e) => [e.QA_id, e]));
        allData = metas.map((m) => {
          const rec = evalMap.get(m.id);
          return { ...m, eval: rec?.eval, importance: rec?.importance };
        });
      }
    } catch (e) {
      error = (e as Error).message;
    } finally {
      busy = false;
    }
    await tick();
    renderCharts();
  }

  function renderCharts() {
    const partyStats =
      count < TH_PARTY
        ? DUMMY_PARTY_STATS
        : computeGroupedStats(
            allData.filter((m) => m.questioner_party),
            (m) => m.eval,
            (m) => m.questioner_party,
          );
    renderChart(
      partyCanvas,
      partyChart,
      partyStats,
      '会派別平均同意度',
      { min: -3, max: 3 },
      'rgba(37, 99, 235, 0.4)',
      'rgba(37, 99, 235, 1)',
      (c) => { partyChart = c; },
    );

    const topicImportanceStats =
      count < TH_COMMITTEE
        ? DUMMY_COMMITTEE_STATS
        : computeGroupedStats(
            allData,
            (m) => m.importance,
            (m) => m.committee_name || '(委員会不明)',
          );
    renderChart(
      topicImportanceCanvas,
      topicImportanceChart,
      topicImportanceStats,
      '委員会別平均重要度',
      { min: 0, max: 3 },
      'rgba(217, 119, 6, 0.4)',
      'rgba(217, 119, 6, 1)',
      (c) => { topicImportanceChart = c; },
    );

    const questionerStats =
      count < TH_QUESTIONER
        ? DUMMY_QUESTIONER_STATS
        : computeGroupedStats(
            allData,
            (m) => m.eval,
            (m) => m.questioner,
          );
    renderChart(
      questionerCanvas,
      questionerChart,
      questionerStats,
      '議員別平均同意度',
      { min: -3, max: 3 },
      'rgba(37, 99, 235, 0.4)',
      'rgba(37, 99, 235, 1)',
      (c) => { questionerChart = c; },
    );
  }

  function renderChart(
    canvas: HTMLCanvasElement | undefined,
    existing: Chart | undefined,
    stats: GroupStat[],
    label: string,
    yRange: { min: number; max: number },
    bg: string,
    border: string,
    assign: (c: Chart) => void,
  ) {
    if (!canvas) return;
    if (existing) existing.destroy();
    const labels = stats.map((s) => `${s.key} (n=${s.count})`);
    // n=1 は標本分散が未定義なので、CI を 0 にすると「ピタリ測れた」ように
    // 見えてしまう。代わりに誤差棒を Y 軸の上下端まで伸ばし、
    // 「不確実性が大きい」ことを視覚化する。
    const data = stats.map((s) => ({
      y: s.mean,
      yMin: s.count === 1 ? yRange.min : s.mean - s.ci,
      yMax: s.count === 1 ? yRange.max : s.mean + s.ci,
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
            backgroundColor: bg,
            borderColor: border,
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: { y: { min: yRange.min, max: yRange.max } },
      },
    };
    const chart = new Chart(canvas, config as unknown as ChartConfiguration);
    assign(chart);
  }

  async function exportCSV() {
    const evaluations = await listEvaluations();
    if (!evaluations.length) return;
    const csv =
      'QA_id,eval,importance\n' +
      evaluations
        .map((e) => `${e.QA_id},${e.eval},${e.importance}`)
        .join('\n');
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
      const [idStr, evalStr, importanceStr] = line.split(',');
      const id = Number(idStr);
      const value = Number(evalStr);
      const importance = Number(importanceStr);
      if (!Number.isNaN(id) && !Number.isNaN(value) && !Number.isNaN(importance)) {
        await saveEvaluation({ QA_id: id, eval: value, importance });
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
{:else}
  <section class="charts">
    <Locked
      title="会派別平均同意度"
      threshold={TH_PARTY}
      currentCount={count}
      description="質問者の会派ごとの平均同意度。"
    >
      <canvas bind:this={partyCanvas} width="800" height="320"></canvas>
    </Locked>

    <Locked
      title="委員会別平均重要度"
      threshold={TH_COMMITTEE}
      currentCount={count}
      description="委員会ごとに、あなたが重要と感じた度合いの平均。"
    >
      <canvas bind:this={topicImportanceCanvas} width="800" height="320"></canvas>
    </Locked>

    <Locked
      title="議員別平均同意度"
      threshold={TH_QUESTIONER}
      currentCount={count}
      description="質問者（議員）ごとの平均同意度。"
    >
      <canvas bind:this={questionerCanvas} width="800" height="320"></canvas>
    </Locked>

    <Locked
      title="論点マップ"
      threshold={TH_TOPIC_MAP}
      currentCount={count}
      description="委員会ごとの評価分布を俯瞰するネットワーク図。"
    >
      <TopicMap items={count < TH_TOPIC_MAP ? DUMMY_TOPIC_ITEMS : allData} />
    </Locked>
  </section>

  {#if count > 0}
    <p class="history-link"><a href="#/history">評価履歴で個別の発言を確認する →</a></p>
  {/if}
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
  .history-link {
    margin: 1.5rem 0;
  }
  .history-link a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
  .history-link a:hover {
    text-decoration: underline;
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
