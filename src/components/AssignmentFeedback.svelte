<script lang="ts">
  // Result of a check: score, compiler errors (click → jump to the line), and per test pass/fail
  // with input, expected and actual output side by side for failed tests.
  import Icon from './Icon.svelte';
  import { pick, t } from '../lib/i18n.svelte';
  import { outputDiff, visibleLines } from '../lib/assignments/diff';
  import type { Feedback } from '../lib/assignments/feedback';
  import type { AssignmentScenario } from '../lib/types';

  let {
    feedback,
    scenarios,
    timeLimitMs,
    onJump,
  }: {
    feedback: Feedback;
    scenarios: AssignmentScenario[];
    timeLimitMs: number;
    onJump: (line: number, column: number) => void;
  } = $props();

  const errors = $derived(feedback.diagnostics.filter((d) => d.severity === 'error'));
  const warnings = $derived(feedback.diagnostics.filter((d) => d.severity === 'warning'));
  const byIndex = $derived(new Map(feedback.rows.map((r) => [r.index, r])));
  let open = $state<Record<number, boolean>>({});

  function shortException(name: string | undefined) {
    return (name ?? '').replace(/^System\./, '');
  }
</script>

<section class="card stack fb">
  <div class="row head">
    <div class="grow">
      <h2>{t('assign.result')}</h2>
      {#if feedback.submitted_at}
        <p class="small muted">{t(feedback.latest ? 'assign.last_result' : 'assign.submission_at', { date: new Date(feedback.submitted_at).toLocaleString() })}</p>
      {/if}
    </div>
    <div class="score" class:full={feedback.score === feedback.max_points} class:zero={feedback.score === 0}>
      {t('assign.points_total', { score: feedback.score, max: feedback.max_points })}
    </div>
  </div>

  {#if !feedback.compiled}
    <div class="error">{t('assign.compile_failed')}</div>
  {/if}

  {#if errors.length}
    <div>
      <h3>{t('assign.errors')}</h3>
      <ul class="diags">
        {#each errors as d, i (i)}
          <li>
            <button class="linkish" onclick={() => onJump(d.line, d.column)} disabled={!d.line}>
              {d.line ? t('assign.line', { line: d.line }) : '–'}
            </button>
            <code class="id">{d.id}</code>
            <span>{d.message}</span>
          </li>
        {/each}
      </ul>
    </div>
  {/if}

  {#if warnings.length}
    <details>
      <summary class="small muted">{t('assign.warnings', { n: warnings.length })}</summary>
      <ul class="diags warn">
        {#each warnings as d, i (i)}
          <li>
            <button class="linkish" onclick={() => onJump(d.line, d.column)}>{t('assign.line', { line: d.line })}</button>
            <code class="id">{d.id}</code>
            <span>{d.message}</span>
          </li>
        {/each}
      </ul>
    </details>
  {/if}

  {#if feedback.compiled}
    <ul class="tests">
      {#each scenarios as s (s.index)}
        {@const r = byIndex.get(s.index)}
        {@const passed = r?.passed ?? false}
        {@const expanded = open[s.index] ?? false}
        <li class:passed class:failed={!passed}>
          <button class="test-head" onclick={() => (open[s.index] = !expanded)} aria-expanded={expanded}>
            <span class="mark"><Icon name={passed ? 'check' : 'x'} size={18} /></span>
            <span class="grow name">{pick(s.name_sk, s.name_en)}</span>
            <span class="pts">{r?.points ?? 0} / {s.points}</span>
            <span class="chev" class:rot={expanded}><Icon name="chevron" size={16} /></span>
          </button>
          {#if expanded}
            <div class="detail stack">
              {#if r?.timed_out}
                <p class="note bad"><Icon name="clock" size={16} /> {t('assign.timeout', { s: Math.round(timeLimitMs / 100) / 10 })}</p>
              {:else if r?.output_limit}
                <p class="note bad">{t('assign.output_limit')}</p>
              {/if}
              {#if r?.exception}
                <p class="note bad">{t('assign.crashed', { name: shortException(r.exception), message: r.exception_message ?? '' })}</p>
              {/if}
              <div class="io">
                <div>
                  <h4>{t('assign.input')}</h4>
                  <pre class="out">{visibleLines(s.input).join('\n')}</pre>
                </div>
              </div>
              {#if r}
                {@const diff = outputDiff(r.actual, s.expected)}
                <div class="cmp">
                  <h4>{t('assign.expected')}</h4>
                  <h4>{t('assign.actual')}</h4>
                  {#each diff.rows as row, i (i)}
                    <div class="cell" class:diff={!row.same}>{row.expected ?? ''}</div>
                    <div class="cell" class:diff={!row.same}>{row.actual ?? ''}</div>
                  {/each}
                  {#if diff.rows.length === 0 || visibleLines(r.actual).length === 0}
                    <div class="cell"></div>
                    <div class="cell muted">{t('assign.no_output')}</div>
                  {/if}
                  {#if diff.more}
                    <div class="cell muted">… +{diff.more}</div><div class="cell"></div>
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .fb h3 { margin-bottom: 6px; }
  .head { align-items: flex-start; }
  .head p { margin: 2px 0 0; }
  .grow { flex: 1; min-width: 0; }
  .score { font-size: 1.25rem; font-weight: 800; color: var(--gold); white-space: nowrap; }
  .score.full { color: var(--ok); }
  .score.zero { color: var(--bad); }
  .diags { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: .9rem; }
  .diags li { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
  .diags .id { font-size: .8rem; color: var(--muted); }
  .warn { margin-top: 8px; }
  .linkish { border: 0; background: none; padding: 0; color: var(--bad); font-weight: 700; cursor: pointer; text-decoration: underline; white-space: nowrap; }
  .warn .linkish { color: var(--gold); }
  .linkish:disabled { cursor: default; text-decoration: none; }
  .tests { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
  .tests li { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .tests li.passed { border-color: color-mix(in srgb, var(--ok) 35%, var(--border)); }
  .tests li.failed { border-color: color-mix(in srgb, var(--bad) 35%, var(--border)); }
  .test-head { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; border: 0; background: var(--surface); text-align: left; cursor: pointer; }
  .mark { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; flex: none; }
  .passed .mark { background: var(--ok-soft); color: var(--ok); }
  .failed .mark { background: var(--bad-soft); color: var(--bad); }
  .name { font-weight: 600; }
  .pts { font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .passed .pts { color: var(--ok); }
  .failed .pts { color: var(--muted); }
  .chev { color: var(--muted); transition: transform .15s ease; }
  .chev.rot { transform: rotate(90deg); }
  .detail { padding: 4px 12px 12px; border-top: 1px solid var(--border); background: var(--surface-2); }
  h4 { margin: 8px 0 4px; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
  .note { margin: 8px 0 0; display: flex; align-items: center; gap: 6px; font-size: .9rem; }
  .note.bad { color: var(--bad); }
  pre.out, .cell { font: 13px/1.5 ui-monospace, "Cascadia Code", Consolas, monospace; }
  pre.out { margin: 0; padding: 8px 10px; border-radius: 8px; background: var(--code-bg); border: 1px solid var(--border); white-space: pre-wrap; overflow-x: auto; }
  .cmp { display: grid; grid-template-columns: 1fr 1fr; column-gap: 8px; }
  .cmp h4 { margin-top: 4px; }
  .cell { padding: 1px 8px; background: var(--code-bg); white-space: pre-wrap; word-break: break-word; min-height: 1.5em; }
  .cell.diff { background: var(--bad-soft); color: var(--bad); }
  @media (max-width: 560px) { .cmp { grid-template-columns: 1fr; } .cmp h4:nth-child(2) { display: none; } }
</style>
