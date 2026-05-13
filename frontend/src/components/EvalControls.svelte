<script lang="ts">
  interface Props {
    value: number;
    disabled?: boolean;
    onSubmit: (value: number) => void;
  }

  let { value = $bindable(), disabled = false, onSubmit }: Props = $props();

  const values = [-3, -2, -1, 0, 1, 2, 3];
</script>

<div class="eval">
  <div class="scale" role="radiogroup" aria-label="評価">
    {#each values as v (v)}
      <label class="slot" class:checked={value === v}>
        <input
          type="radio"
          name="eval"
          value={v}
          checked={value === v}
          {disabled}
          onchange={() => (value = v)}
        />
        <span>{v > 0 ? `+${v}` : v}</span>
      </label>
    {/each}
  </div>
  <button class="primary" type="button" {disabled} onclick={() => onSubmit(value)}>
    評価して次へ
  </button>
</div>

<style>
  .eval {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-items: stretch;
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
