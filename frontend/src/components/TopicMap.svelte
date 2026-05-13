<script lang="ts">
  import type { QAMeta } from '../lib/types';

  interface Props {
    items: (QAMeta & { eval?: number })[];
  }

  let { items }: Props = $props();

  interface Node {
    name: string;
    short: string;
    count: number;
    avgEval: number;
    questioners: Set<string>;
    x: number;
    y: number;
    size: number;
  }

  interface Edge {
    a: Node;
    b: Node;
    weight: number;
  }

  const WIDTH = 720;
  const HEIGHT = 480;

  function shortenCommittee(name: string): string {
    return name
      .replace(/常任委員会|特別委員会|委員会/g, '')
      .replace(/区議会/g, '')
      .trim() || name;
  }

  function layout(): { nodes: Node[]; edges: Edge[] } {
    const map = new Map<string, Node>();
    for (const item of items) {
      const name = item.committee_name || '(委員会不明)';
      if (!map.has(name)) {
        map.set(name, {
          name,
          short: shortenCommittee(name),
          count: 0,
          avgEval: 0,
          questioners: new Set(),
          x: 0,
          y: 0,
          size: 0,
        });
      }
      const node = map.get(name)!;
      node.count += 1;
      if (item.eval !== undefined) node.avgEval += item.eval;
      if (item.questioner) node.questioners.add(item.questioner);
    }
    const nodes = [...map.values()].sort((a, b) => b.count - a.count);
    for (const n of nodes) {
      n.avgEval = n.count ? n.avgEval / n.count : 0;
    }

    // Circular layout, scaled by count
    const cx = WIDTH / 2;
    const cy = HEIGHT / 2;
    const minRadius = 80;
    const maxRadius = Math.min(WIDTH, HEIGHT) / 2 - 60;
    const maxCount = Math.max(1, ...nodes.map((n) => n.count));
    nodes.forEach((n, i) => {
      const angle = (i / Math.max(1, nodes.length)) * Math.PI * 2 - Math.PI / 2;
      // Heaviest committee closer to center; rare ones pushed outward.
      const radius = minRadius + (1 - n.count / maxCount) * (maxRadius - minRadius);
      n.x = cx + Math.cos(angle) * radius;
      n.y = cy + Math.sin(angle) * radius;
      n.size = 12 + Math.sqrt(n.count) * 6;
    });

    // Edges: link committees that share at least one questioner.
    const edges: Edge[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        let shared = 0;
        const a = nodes[i];
        const b = nodes[j];
        a.questioners.forEach((q) => {
          if (b.questioners.has(q)) shared++;
        });
        if (shared > 0) edges.push({ a, b, weight: shared });
      }
    }
    return { nodes, edges };
  }

  let view = $derived(layout());
  let totalCount = $derived(view.nodes.reduce((acc, n) => acc + n.count, 0));

  function evalColor(avg: number): string {
    // Map -3..+3 to red/blue with neutral grey
    if (avg > 0) {
      const t = Math.min(1, avg / 3);
      return `rgba(37, 99, 235, ${0.3 + 0.5 * t})`;
    }
    if (avg < 0) {
      const t = Math.min(1, -avg / 3);
      return `rgba(220, 38, 38, ${0.3 + 0.5 * t})`;
    }
    return 'rgba(120, 120, 120, 0.35)';
  }
</script>

<section class="topic-map">
  <h3>論点マップ</h3>
  <p class="hint">
    委員会ごとの評価数を円のサイズで、同じ議員が登場する委員会同士を線で結びます。
    現在 {view.nodes.length} 委員会・{totalCount} 件を集計中。
  </p>
  {#if view.nodes.length === 0}
    <p>マップに描画するデータがありません。</p>
  {:else}
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="委員会論点マップ">
      {#each view.edges as edge (edge.a.name + '-' + edge.b.name)}
        <line
          x1={edge.a.x}
          y1={edge.a.y}
          x2={edge.b.x}
          y2={edge.b.y}
          stroke="currentColor"
          stroke-opacity={Math.min(0.5, 0.1 + edge.weight * 0.08)}
          stroke-width={Math.min(3, 0.5 + edge.weight * 0.4)}
        />
      {/each}
      {#each view.nodes as node (node.name)}
        <g transform={`translate(${node.x}, ${node.y})`}>
          <circle
            r={node.size}
            fill={evalColor(node.avgEval)}
            stroke="currentColor"
            stroke-opacity="0.55"
          />
          <text
            text-anchor="middle"
            dominant-baseline="central"
            font-size={Math.max(11, Math.min(18, node.size * 0.6))}
            fill="currentColor"
          >{node.short}</text>
          <text
            text-anchor="middle"
            y={node.size + 14}
            font-size="11"
            opacity="0.7"
            fill="currentColor"
          >n={node.count} 平均{node.avgEval.toFixed(1)}</text>
        </g>
      {/each}
    </svg>
  {/if}
</section>

<style>
  .topic-map {
    margin: 1.5rem 0;
    color: var(--text);
  }
  .topic-map h3 {
    margin: 0 0 0.5rem;
    font-family: var(--font-display);
  }
  .hint {
    margin: 0 0 0.75rem;
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  svg {
    width: 100%;
    height: auto;
    max-height: 70vh;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
  }
</style>
