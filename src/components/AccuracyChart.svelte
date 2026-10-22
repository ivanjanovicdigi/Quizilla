<script lang="ts">
  import { t } from '../lib/i18n.svelte';
  import { pct } from '../lib/util';
  import type { StatsDay } from '../lib/types';

  // Accuracy per day (one series): line + markers, dashed pass threshold,
  // crosshair + tooltip on hover / tap, table view for accessibility.
  let { days, threshold = 0.75 }: { days: StatsDay[]; threshold?: number } = $props();

  const H = 150;
  const PAD = { top: 12, right: 40, bottom: 22, left: 34 };
  let width = $state(320);
  let active = $state<number | null>(null);

  const DAY = 86_400_000;
  const toTime = (d: string) => Date.parse(`${d}T00:00:00Z`);
  const fmt = (d: string) => {
    const [, m, dd] = d.split('-');
    return `${Number(dd)}. ${Number(m)}.`;
  };

  const points = $derived.by(() => {
    if (!days.length) return [];
    const t0 = toTime(days[0].day);
    const t1 = toTime(days[days.length - 1].day);
    const span = Math.max(t1 - t0, DAY);
    const w = Math.max(width - PAD.left - PAD.right, 10);
    const h = H - PAD.top - PAD.bottom;
    return days.map((d) => {
      const rate = d.answers ? d.correct / d.answers : 0;
      const x = days.length === 1 ? PAD.left + w / 2 : PAD.left + ((toTime(d.day) - t0) / span) * w;
      return { ...d, rate, x, y: PAD.top + (1 - rate) * h };
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
    aria-label={t('stats.chart_info', { pct: Math.round(threshold * 100) })}
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
    {/if}

    {#if points.length > 1}
      <path class="line" d={path} />
    {/if}
    {#each points as p, i (p.day)}
      <circle class="dot" class:on={active === i} cx={p.x} cy={p.y} r={active === i ? 5 : 4} />
    {/each}

    {#if last && active === null}
      <text class="value" x={last.x + 8} y={last.y + 4}>{pct(last.correct, last.answers)} %</text>
    {/if}

    {#if points.length}
      <text class="axis" x={points[0].x} y={H - 6} text-anchor={points.length === 1 ? 'middle' : 'start'}>{fmt(points[0].day)}</text>
      {#if points.length > 1}
        <text class="axis" x={last.x} y={H - 6} text-anchor="end">{fmt(last.day)}</text>
      {/if}
    {/if}
  </svg>

  {#if tip}
    <div class="tip" style:left={`${Math.min(Math.max(tip.x, 70), width - 70)}px`}>
      <strong>{fmt(tip.day)}</strong>
      <span>{pct(tip.correct, tip.answers)} % · {t('stats.tip', { c: tip.correct, a: tip.answers })}</span>
    </div>
  {/if}
</div>

<details class="table small">
  <summary class="muted">{t('stats.table')}</summary>
  <table>
    <thead><tr><th>{t('stats.day')}</th><th>{t('stats.answers')}</th><th>{t('stats.rate')}</th></tr></thead>
    <tbody>
      {#each days as d (d.day)}
        <tr><td>{fmt(d.day)}</td><td>{d.correct}/{d.answers}</td><td>{pct(d.correct, d.answers)} %</td></tr>
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
