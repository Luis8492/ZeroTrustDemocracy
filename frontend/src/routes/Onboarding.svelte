<script lang="ts">
  import { onDestroy } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { setOnboardingCompleted } from '../lib/db';
  import { celebrate } from '../lib/confetti';
  import SpeechList from '../components/SpeechList.svelte';
  import EvalControls from '../components/EvalControls.svelte';
  import type { Speech } from '../lib/types';

  type Stage = 'intro' | 'demo' | 'submitted';

  let stage = $state<Stage>('intro');
  let evalValue = $state(0);
  let importanceValue = $state(0);
  let marked = false;

  const demoSpeeches: Speech[] = [
    {
      mark: '◆',
      role: '委員',
      name: 'デモ 議員',
      comment:
        '区民から要望が出ているコミュニティバスの増便について、区はどのように対応していくのか伺います。',
    },
    {
      mark: '◎',
      role: '担当部長',
      comment:
        '現在の利用実態と財政負担を踏まえ、ルートと運行頻度の最適化を含め、慎重に検討してまいります。',
    },
  ];

  async function markComplete() {
    if (marked) return;
    marked = true;
    await setOnboardingCompleted(true);
  }

  function startDemo() {
    stage = 'demo';
  }

  function handleSubmit() {
    stage = 'submitted';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    celebrate();
  }

  async function goStats() {
    await markComplete();
    push('/result');
  }

  async function skip() {
    await markComplete();
    push('/');
  }

  // Insurance: mark complete even if the user navigates away via the header.
  onDestroy(() => {
    if (!marked) {
      void setOnboardingCompleted(true);
    }
  });
</script>

<section class="onboarding" aria-live="polite">
  {#if stage === 'intro'}
    <div class="card">
      <p class="step-label">はじめての方へ</p>
      <h1>世田谷区議会QAナビへようこそ</h1>
      <p>
        本サイトでは、世田谷区議会の質疑応答（QA）を1問ずつ評価し、
        あなたの政治的な関心や立場を可視化します。
      </p>
      <p class="zero-trust">
        <strong>評価データはお使いのブラウザの中だけに保存されます。</strong>
        サーバーには一切送信されません（Zero Trust）。
      </p>
      <p>まずは1問だけ、使い方をご紹介します（約30秒）。</p>
      <div class="actions">
        <button type="button" class="primary" onclick={startDemo}>
          ツアーを始める →
        </button>
        <button type="button" class="ghost" onclick={skip}>スキップ</button>
      </div>
    </div>
  {:else if stage === 'demo'}
    <div class="card">
      <p class="step-label">STEP 1 / 2 — 質疑を読んで評価する</p>
      <h2>これはデモの質疑応答です</h2>
      <p class="hint">
        実際のQAは下のような形式で表示されます。読んだら下の「同意度」「重要度」を選んで、
        <strong>「評価して次へ」</strong>を押してみましょう。
      </p>
      <div class="demo-qa">
        <SpeechList speeches={demoSpeeches} />
      </div>
      <div class="eval-wrap">
        <EvalControls
          bind:evalValue
          bind:importanceValue
          onSubmit={handleSubmit}
        />
      </div>
    </div>
  {:else}
    <div class="card success">
      <p class="step-label">STEP 2 / 2 — 評価結果を見る</p>
      <h2>評価できました！</h2>
      <p class="hint">
        ※ これはデモのため、今の評価データは保存されません。
        実際に評価ページで操作すると、ブラウザ内に蓄積されていきます。
      </p>
      <p>
        蓄積された評価は「<strong>統計</strong>」ページで集計され、
        会派別・議員別の傾向や論点マップとして可視化されます
        （評価数に応じて段階的にアンロックされます）。
      </p>
      <p class="hint">下のボタン、または上部メニューの「統計」を押してツアーを完了しましょう。</p>
      <div class="actions">
        <button type="button" class="primary big" onclick={goStats}>
          統計ページへ進む →
        </button>
      </div>
    </div>
  {/if}
</section>

<style>
  .onboarding {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow: var(--shadow-card);
  }
  .card h1,
  .card h2 {
    margin: 0;
  }
  .card h1 {
    font-size: 1.5rem;
    line-height: 1.4;
  }
  .card h2 {
    font-size: 1.2rem;
  }
  .step-label {
    margin: 0;
    color: var(--accent);
    font-weight: 700;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .zero-trust {
    background: var(--accent-soft, color-mix(in srgb, var(--accent) 12%, transparent));
    border-left: 3px solid var(--accent);
    padding: 0.7rem 0.9rem;
    border-radius: var(--radius);
    margin: 0;
  }
  .hint {
    margin: 0;
    color: var(--text-muted);
    font-size: 0.9rem;
    line-height: 1.7;
  }
  .demo-qa {
    border-radius: var(--radius);
    background: var(--surface-alt);
    padding: 0.75rem 1rem;
  }
  .eval-wrap {
    border-top: 1px dashed var(--border);
    padding-top: 1rem;
  }
  .actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    align-items: center;
  }
  .primary.big {
    padding: 0.7rem 1.4rem;
    font-size: 1rem;
    font-weight: 700;
  }
  .ghost {
    background: transparent;
    border: none;
    color: var(--text-muted);
    text-decoration: underline;
    cursor: pointer;
    padding: 0.4rem 0.6rem;
  }
  p {
    margin: 0;
    line-height: 1.7;
  }
</style>
