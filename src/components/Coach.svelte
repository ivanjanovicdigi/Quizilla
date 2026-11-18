<script lang="ts">
  // "What to do next": ONE step for the student, updated while they type and after every test run
  // (logic in lib/assignments/coach.ts). Title + one sentence, the place in the code, and for a
  // test the one line that differs. The reason and an example are folded away. Never part of the score.
  import Icon from './Icon.svelte';
  import Rich from './Rich.svelte';
  import { pick, t, type Key } from '../lib/i18n.svelte';
  import { buildCoach, COACH_EXAMPLES, DESIGN_STEPS } from '../lib/assignments/coach';
  import { DESIGN_EXAMPLES, type DesignCheckId } from '../lib/assignments/guide';
  import type { DesignReview, Diagnostic } from '../lib/assignments/protocol';
  import type { Feedback } from '../lib/assignments/feedback';
  import type { AssignmentScenario } from '../lib/types';

  let {
    code,
    review,
    errors,
    feedback,
    testedCode,
    scenarios,
    analysing,
    buttonLabel,
    onJump,
  }: {
    code: string;
    review: DesignReview | null;     // the last review of code that compiled
    errors: Diagnostic[];            // compile errors of the code as it is now
    feedback: Feedback | null;       // last test run
    testedCode: string | null;       // the code that test run belongs to
    scenarios: AssignmentScenario[];
    analysing: boolean;
    buttonLabel: string;             // the "run tests" button, named in a hint
    onJump: (line: number, column: number) => void;
  } = $props();

  const coach = $derived(buildCoach({ code, errors, review, feedback, testedCode, scenarios }));
  const step = $derived(coach.step);
  const isDesign = $derived(DESIGN_STEPS.has(step.id));
  const isTest = $derived(step.id.startsWith('test_'));
  const vars = $derived({ ...step.vars, button: buttonLabel, name: step.test ? pick(step.test.name_sk, step.test.name_en) : '' });

  const title = $derived(isTest ? t('coach.test.title', vars) : t(`coach.${step.id}.title` as Key, vars));
  const text = $derived(
    step.id === 'compile' ? String(step.vars.message)
      : isDesign ? t(`design.${step.id}.fail` as Key, vars)
      : t(`coach.${step.id}.text` as Key, vars));
  const why = $derived(
    isDesign ? t(`design.${step.id}.why` as Key)
      : ['compile', 'input_read', 'input_loop', 'input_exit'].includes(step.id) ? t(`coach.${step.id}.why` as Key)
      : '');
  const example = $derived(DESIGN_EXAMPLES[step.id as DesignCheckId] ?? COACH_EXAMPLES[step.id] ?? '');
  const pct = $derived(Math.round((coach.done / coach.total) * 100));
</script>

<section class="card coach">
  <div class="row head">
    <h2 class="grow">{t('coach.title')}</h2>
    {#if analysing}<span class="dot spin" title={t('guide.analysing')}></span>{/if}
    <span class="small muted">{t('coach.progress', { done: coach.done, total: coach.total })}</span>
  </div>
  <div class="bar" aria-hidden="true"><span style:width="{pct}%"></span></div>

  <div class="step" class:done={step.id === 'done'} class:bad={step.id === 'compile' || isTest}>
    <h3>
      {#if step.id === 'done'}<Icon name="check" size={18} />{/if}
      {title}
    </h3>
    <p class="what">{text}</p>

    {#if step.id === 'compile'}
      <button class="linkish" onclick={() => step.jump && onJump(step.jump.line, step.jump.column)} disabled={!step.jump?.line}>
        {t('assign.line', { line: step.vars.line })}
      </button>
      {#if Number(step.vars.more) > 0}<p class="small muted">{t('coach.compile.more', vars)}</p>{/if}
    {/if}

    {#if step.items?.length}
      <div class="items">
        {#each step.items as it, i (i)}
          <button class="linkish" onclick={() => onJump(it.line, 1)} disabled={!it.line}>
            <code>{it.name}</code>{#if it.line}&nbsp;· {t('assign.line', { line: it.line })}{/if}
          </button>
        {/each}
      </div>
    {/if}

    {#if step.test && (step.test.expected != null || step.test.actual != null)}
      <dl class="cmp">
        {#if step.test.expected != null}
          <dt>{t('coach.expected')}</dt><dd><code>{step.test.expected}</code></dd>
        {/if}
        {#if step.id !== 'test_silent' && step.id !== 'test_missing'}
          <dt>{t('coach.actual')}</dt><dd><code class:none={step.test.actual == null}>{step.test.actual ?? t('assign.no_output')}</code></dd>
        {/if}
      </dl>
    {/if}
    {#if step.test}
      <details>
        <summary>{t('coach.test_input')}</summary>
        <pre class="out">{step.test.input.join('\n')}</pre>
      </details>
    {/if}
    {#if coach.staleTests && (isTest || step.id === 'run_tests')}
      <p class="small muted">{t('coach.stale')}</p>
    {/if}

    {#if why}
      <details>
        <summary>{example ? t('coach.why') : t('coach.why_only')}</summary>
        <p class="why">{why}</p>
        {#if example}<Rich text={'```csharp\n' + example + '\n```'} />{/if}
      </details>
    {/if}
  </div>
</section>

<style>
  .grow { flex: 1; min-width: 0; }
  .head { align-items: center; gap: 10px; }
  .bar { height: 6px; border-radius: 3px; background: var(--border); overflow: hidden; margin: 8px 0 14px; }
  .bar span { display: block; height: 100%; background: var(--ok); transition: width .3s; }
  .dot { width: 12px; height: 12px; border-radius: 50%; flex: none; border: 2px solid var(--border); border-top-color: var(--accent); animation: spin .8s linear infinite; }
  .step { border: 1px solid color-mix(in srgb, var(--gold) 45%, var(--border)); background: var(--gold-soft); border-radius: 12px; padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; }
  .step.bad { border-color: color-mix(in srgb, var(--bad) 35%, var(--border)); background: var(--bad-soft); }
  .step.done { border-color: color-mix(in srgb, var(--ok) 45%, var(--border)); background: var(--ok-soft); }
  h3 { margin: 0; font-size: 1.05rem; display: flex; align-items: center; gap: 6px; }
  .done h3 { color: var(--ok); }
  .what { margin: 0; }
  .why { margin: 6px 0; font-size: .9rem; }
  .items { display: flex; flex-wrap: wrap; gap: 4px 12px; }
  .linkish { align-self: flex-start; border: 0; background: none; padding: 0; color: var(--gold); font-weight: 600; cursor: pointer; text-decoration: underline; white-space: nowrap; }
  .bad .linkish { color: var(--bad); }
  .linkish:disabled { cursor: default; text-decoration: none; }
  .linkish code { font-size: .85rem; }
  .cmp { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 10px; margin: 0; align-items: baseline; font-size: .9rem; }
  .cmp dt { font-weight: 700; color: var(--muted); }
  .cmp dd { margin: 0; overflow-wrap: anywhere; }
  .cmp code { background: var(--surface); padding: 1px 6px; border-radius: 6px; }
  .cmp code.none { color: var(--muted); }
  details { font-size: .9rem; }
  summary { cursor: pointer; font-weight: 600; color: var(--muted); }
  details :global(pre) { margin: 6px 0 0; }
  pre.out { white-space: pre-wrap; }
</style>
