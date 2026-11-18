<script lang="ts">
  // The tests of an assignment: before the first run just the list (input + expected output on
  // click), after a run pass/fail per test with expected and actual output side by side.
  // Compile errors, design tips and the next step are shown by Coach, not here.
  import Icon from './Icon.svelte';
  import { pick, t } from '../lib/i18n.svelte';
  import { outputDiff, visibleLines } from '../lib/assignments/diff';
  import type { Feedback } from '../lib/assignments/feedback';
  import type { AssignmentScenario } from '../lib/types';

  let {
    feedback,
    scenarios,
    timeLimitMs,
  }: {
    feedback: Feedback | null;   // null = the tests have not run yet
    scenarios: AssignmentScenario[];
    timeLimitMs: number;
  } = $props();

  const byIndex = $derived(new Map((feedback?.rows ?? []).map((r) => [r.index, r])));
  const ran = $derived(feedback != null && feedback.compiled);
  let open = $state<Record<number, boolean>>({});

  function shortException(name: string | undefined) {
    return (name ?? '').replace(/^System\./, '');
  }
</script>

<section class="card stack fb">
  <div class="row head">
    <div class="grow">
      <h2>{t('assign.tests', { n: scenarios.length })}</h2>
      {#if feedback?.submitted_at}
        <p class="small muted">{t(feedback.latest ? 'assign.last_result' : 'assign.submission_at', { date: new Date(feedback.submitted_at).toLocaleString() })}</p>
      {/if}
    </div>
    {#if feedback}
      <div class="score" class:full={feedback.score === feedback.max_points}>
        {t('assign.points_total', { score: feedback.score, max: feedback.max_points })}
      </div>
    {/if}
  </div>

  {#if !feedback}
    <p class="small muted">{t('assign.tests_info')}</p>
  {:else if !feedback.compiled}
    <p class="small note bad">{t('assign.compile_failed')}</p>
  {/if}

  <ul class="tests">
    {#each scenarios as s (s.index)}
      {@const r = byIndex.get(s.index)}
      {@const passed = ran && (r?.passed ?? false)}
      {@const failed = ran && !passed}
      {@const expanded = open[s.index] ?? false}
      <li class:passed class:failed>
        <button class="test-head" onclick={() => (open[s.index] = !expanded)} aria-expanded={expanded}>
          <span class="mark">{#if ran}<Icon name={passed ? 'check' : 'x'} size={16} />{/if}</span>
          <span class="grow name">{pick(s.name_sk, s.name_en)}</span>
          <span class="pts">{#if ran}{r?.points ?? 0} / {/if}{s.points}</span>
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
            {#if ran && r}
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
            {:else}
              <div>
                <h4>{t('assign.expected')}</h4>
                <pre class="out">{visibleLines(s.expected).join('\n')}</pre>
              </div>
            {/if}
          </div>
        {/if}
      </li>
    {/each}
  </ul>
</section>

<style>
  .head { align-items: flex-start; }
  .head p { margin: 2px 0 0; }
  .grow { flex: 1; min-width: 0; }
  .score { font-weight: 700; color: var(--muted); white-space: nowrap; font-variant-numeric: tabular-nums; }
  .score.full { color: var(--ok); }
  .tests { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .tests li { border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
  .tests li.passed { border-color: color-mix(in srgb, var(--ok) 35%, var(--border)); }
  .tests li.failed { border-color: color-mix(in srgb, var(--bad) 35%, var(--border)); }
  .test-head { display: flex; align-items: center; gap: 10px; width: 100%; padding: 8px 12px; border: 0; background: var(--surface); text-align: left; cursor: pointer; font-size: .92rem; }
  .mark { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; flex: none; background: var(--surface-2); }
  .passed .mark { background: var(--ok-soft); color: var(--ok); }
  .failed .mark { background: var(--bad-soft); color: var(--bad); }
  .name { font-weight: 600; }
  .pts { font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--muted); }
  .passed .pts { color: var(--ok); }
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
