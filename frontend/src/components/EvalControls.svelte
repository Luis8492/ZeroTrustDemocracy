<script lang="ts">
  interface Props {
    evalValue: number;
    importanceValue: number;
    disabled?: boolean;
    onSubmit: (evalValue: number, importanceValue: number) => void;
  }

  let {
    evalValue = $bindable(),
    importanceValue = $bindable(),
    disabled = false,
    onSubmit,
  }: Props = $props();

  const evalValues = [-3, -2, -1, 0, 1, 2, 3];
  const importanceValues = [0, 1, 2, 3];
</script>

<div class="eval">
  <div class="row">
    <div class="row-head">
      <strong>同意度</strong>
      <span class="hint">-3 (強く反対) 〜 +3 (強く賛成)</span>
    </div>
    <div class="scale" role="radiogroup" aria-label="同意度">
      {#each evalValues as v (v)}
        <label class="slot" class:checked={evalValue === v}>
          <input
            type="radio"
            name="eval"
            value={v}
            checked={evalValue === v}
            {disabled}
            onchange={() => (evalValue = v)}
          />
          <span>{v > 0 ? `+${v}` : v}</span>
        </label>
      {/each}
    </div>
  </div>

  <div class="row">
    <div class="row-head">
      <strong>重要度</strong>
      <span class="hint">0 (重要でない) 〜 3 (非常に重要)</span>
    </div>
    <div class="scale" role="radiogroup" aria-label="重要度">
      {#each importanceValues as v (v)}
        <label class="slot" class:checked={importanceValue === v}>
          <input
            type="radio"
            name="importance"
            value={v}
            checked={importanceValue === v}
            {disabled}
            onchange={() => (importanceValue = v)}
          />
          <span>{v}</span>
        </label>
      {/each}
    </div>
  </div>

  <button
    class="primary"
    type="button"
    {disabled}
    onclick={() => onSubmit(evalValue, importanceValue)}
  >
    評価して次へ
  </button>
</div>

<style>
  .eval {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  .row {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .row-head {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    flex-wrap: wrap;
  }
  .row-head .hint {
    color: var(--text-muted);
    font-size: 0.8rem;
  }
  .scale {
    display: flex;
    gap: 0.25rem;
    justify-content: space-between;
  }
  .slot {
    flex: 1;
    text-align: center;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.5rem 0;
    cursor: pointer;
    background: var(--surface);
    font-variant-numeric: tabular-nums;
    user-select: none;
  }
  .slot input { display: none; }
  .slot.checked {
    background: var(--accent);
    color: var(--accent-contrast);
    border-color: var(--accent);
  }
</style>
