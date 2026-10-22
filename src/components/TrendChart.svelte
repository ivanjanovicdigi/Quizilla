<script lang="ts">
  import { t } from '../lib/i18n.svelte';
  import { pct } from '../lib/util';

  // Running accuracy over all answers (one series): line + last value, dashed unlock threshold,
  // crosshair + tooltip on hover / tap, table view for accessibility.
  // trend = [[answer number, correct so far], …] (downsampled by the server).
  let { trend, threshold = 0.8 }: { trend: [number, number][]; threshold?: number } = $props();

  const H = 150;
  const PAD = { top: 12, right: 40, bottom: 22, left: 34 };
  let width = $state(320);
  let active = $state<number | null>(null);

  const points = $derived.by(() => {
    if (!trend.length) return [];
    const n0 = trend[0][0];
    const n1 = trend[trend.length - 1][0];
    const span = Math.max(n1 - n0, 1);
    const w = Math.max(width - PAD.left - PAD.right, 10);
    const h = H - PAD.top - PAD.bottom;
    return trend.map(([n, c]) => {
      const rate = n ? c / n : 0;
      const x = trend.length === 1 ? PAD.left + w / 2 : PAD.left + ((n - n0) / span) * w;
      return { n, c, x, y: PAD.top + (1 - rate) * h };
    });
  });

  const y = (v: number) => PAD.top + (1 - v) * (H - PAD.top - PAD.bottom);
  const path = $derived(points.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(''));
  const last = $derived(points[points.length - 1]);
  const tip = $derived(active !== null ? points[active] : null);

  function pick(ev: PointerEvent) {
    const svg = ev.currentTarget as SVGElement;
    const x = ev.clientX - svg.getBoundingClientRect().left;
    let best = 0;
    for (let i = 1; i < points.length; i++) {
      if (Math.abs(points[i].x - x) < Math.abs(points[best].x - x)) best = i;
    }
    active = points.length ? best : null;
  }
</script>

<div class="chart" bind:clientWidth={width}>
  <svg
    width={width}
    height={H}
    role="img"
    aria-label={t('stats.trend_info', { pct: Math.round(threshold * 100) })}
    onpointermove={pick}
    onpointerdown={pick}
    onpointerleave={() => (active = null)}>
    {#each [0, 0.5, 1] as g (g)}
      <line class="grid" x1={PAD.left} x2={width - PAD.right} y1={y(g)} y2={y(g)} />
      <text class="axis" x={PAD.left - 6} y={y(g) + 4} text-anchor="end">{g * 100}</text>
    {/each}
    <line class="threshold" x1={PAD.left} x2={width - PAD.right} y1={y(threshold)} y2={y(threshold)} />

    {#if tip}
      <line class="cross" x1={tip.x} x2={tip.x} y1={PAD.top} y2={H - PAD.bottom} />
      <circle class="dot" cx={tip.x} cy={tip.y} r="5" />
    {/if}

    {#if points.length > 1}
      <path class="line" d={path} />
    {/if}
    {#if last}
      <circle class="dot" cx={last.x} cy={last.y} r="4" />
    {/if}

    {#if last && active === null}
      <text class="value" x={last.x + 8} y={last.y + 4}>{pct(last.c, last.n)} %</text>
    {/if}

    {#if points.length}
      <text class="axis" x={points[0].x} y={H - 6} text-anchor={points.length === 1 ? 'middle' : 'start'}>{points[0].n}</text>
      {#if points.length > 1}
        <text class="axis" x={last.x} y={H - 6} text-anchor="end">{last.n}</text>
      {/if}
    {/if}
  </svg>

  {#if tip}
    <div class="tip" style:left={`${Math.min(Math.max(tip.x, 70), width - 70)}px`}>
      <strong>{t('stats.after', { n: tip.n })}</strong>
      <span>{pct(tip.c, tip.n)} % · {t('stats.tip', { c: tip.c, a: tip.n })}</span>
    </div>
  {/if}
</div>

<details class="table small">
  <summary class="muted">{t('stats.table')}</summary>
  <table>
    <thead><tr><th>{t('stats.answer_no')}</th><th>{t('stats.answers')}</th><th>{t('stats.rate')}</th></tr></thead>
    <tbody>
      {#each trend as [n, c] (n)}
        <tr><td>{n}</td><td>{c}/{n}</td><td>{pct(c, n)} %</td></tr>
      {/each}
    </tbody>
  </table>
</details>

<style>
  .chart { position: relative; width: 100%; touch-action: pan-y; }
  svg { display: block; overflow: visible; }
  .grid { stroke: var(--border); stroke-width: 1; }
  .threshold { stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 4 4; }
  .cross { stroke: var(--muted); stroke-width: 1; opacity: .6; }
  .line { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .dot { fill: var(--accent); stroke: var(--surface); stroke-width: 2; }
  .axis { fill: var(--muted); font-size: 11px; }
  .value { fill: var(--text); font-size: 12px; font-weight: 700; }
  .tip {
    position: absolute; top: -6px; transform: translate(-50%, -100%);
    background: var(--text); color: var(--bg); border-radius: 8px; padding: 4px 8px;
    font-size: .75rem; white-space: nowrap; pointer-events: none;
    display: flex; flex-direction: column; align-items: center;
  }
  .table summary { cursor: pointer; margin-top: 6px; }
  table { width: 100%; border-collapse: collapse; margin-top: 6px; }
  th, td { text-align: left; padding: 3px 6px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; }
</style>
