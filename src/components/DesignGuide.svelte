<script lang="ts">
  // The guide next to the editor: coaching on how the code is built, updated while the student
  // types. Shows ONE next step (with the reason and a small example), the other open tips folded
  // away, and what is already done. Never part of the score.
  import Icon from './Icon.svelte';
  import Rich from './Rich.svelte';
  import { t, type Key } from '../lib/i18n.svelte';
  import { buildGuide, DESIGN_EXAMPLES, type DesignCheckId } from '../lib/assignments/guide';
  import type { DesignCheck, DesignReview, Diagnostic } from '../lib/assignments/protocol';

  let {
    review,
    errors,
    hasCode,
    loading,
    analysing,
    onJump,
  }: {
    review: DesignReview | null;   // the last review of code that compiled
    errors: Diagnostic[];          // compile errors of the code as it is now
    hasCode: boolean;
    loading: boolean;              // the compiler is still downloading
    analysing: boolean;
    onJump: (line: number, column: number) => void;
  } = $props();

  const guide = $derived(buildGuide(review));
  const stale = $derived(errors.length > 0 && review != null);

  const text = (c: DesignCheck, kind: 'ok' | 'fail' | 'why') => t(`design.${c.id}.${kind}` as Key, { n: c.n ?? 0 });
  const example = (c: DesignCheck) => DESIGN_EXAMPLES[c.id as DesignCheckId];
</script>

{#snippet items(c: DesignCheck)}
  {#if c.items?.length}
    <span class="items">
      {#each c.items as it, i (i)}
        <button class="linkish" onclick={() => onJump(it.line, 1)} disabled={!it.line}>
          <code>{it.name}</code>{#if it.line}&nbsp;· {t('assign.line', { line: it.line })}{/if}
        </button>
      {/each}
    </span>
  {/if}
{/snippet}

<section class="card guide">
  <div class="row">
    <h2 class="grow">{t('guide.title')}</h2>
    {#if analysing}
      <span class="dot spin" title={t('guide.analysing')}></span>
    {:else if guide.total}
      <span class="pill" class:ok={!guide.next}>{guide.done.length} / {guide.total}</span>
    {/if}
  </div>
  <p class="small muted lead">{t('guide.note')}</p>

  {#if !hasCode}
    <p class="hint">{t('guide.empty')}</p>
  {:else if loading && !review}
    <p class="small muted">{t('assign.loading_compiler')}</p>
  {/if}

  {#if hasCode && errors.length}
    <div class="fix">
      <strong>{t('guide.errors')}</strong>
      <ul>
        {#each errors.slice(0, 3) as d, i (i)}
          <li>
            <button class="linkish bad" onclick={() => onJump(d.line, d.column)} disabled={!d.line}>
              {d.line ? t('assign.line', { line: d.line }) : '–'}
            </button>
            <span>{d.message}</span>
          </li>
        {/each}
      </ul>
      {#if errors.length > 3}<p class="small muted">{t('guide.errors_more', { n: errors.length - 3 })}</p>{/if}
    </div>
  {/if}

  {#if hasCode && review}
    <div class:stale>
      {#if stale}<p class="small muted">{t('guide.stale')}</p>{/if}

      {#if review.classes.length}
        <ul class="classes">
          {#each review.classes as c (c.name + c.line)}
            <li>
              <button class="linkish cls" onclick={() => onJump(c.line, 1)} disabled={!c.line}>{c.name}</button>
              <span class="small muted">{t('design.class_line', { data: c.properties + c.fields, methods: c.methods })}</span>
            </li>
          {/each}
        </ul>
      {/if}

      {#if guide.next}
        {@const c = guide.next}
        <div class="next">
          <span class="label">{t('guide.next')}</span>
          <p class="what">{text(c, 'fail')}</p>
          {@render items(c)}
          <p class="why">{text(c, 'why')}</p>
          {#if example(c)}
            <details>
              <summary>{t('guide.example')}</summary>
              <Rich text={'```csharp\n' + example(c) + '\n```'} />
            </details>
          {/if}
        </div>
      {:else if guide.total}
        <div class="next all">
          <span class="label"><Icon name="check" size={14} /> {t('guide.all_done_title')}</span>
          <p class="what">{t('guide.all_done')}</p>
        </div>
      {/if}

      {#if guide.more.length}
        <details class="fold">
          <summary>{t('guide.more', { n: guide.more.length })}</summary>
          <ul class="list">
            {#each guide.more as c (c.id)}
              <li>
                <span class="mark tip">!</span>
                <div class="grow"><span>{text(c, 'fail')}</span>{@render items(c)}</div>
              </li>
            {/each}
          </ul>
        </details>
      {/if}

      {#if guide.done.length}
        <details class="fold">
          <summary>{t('guide.done', { n: guide.done.length, total: guide.total })}</summary>
          <ul class="list">
            {#each guide.done as c (c.id)}
              <li><span class="mark"><Icon name="check" size={14} /></span><span class="grow">{text(c, 'ok')}</span></li>
            {/each}
          </ul>
        </details>
      {/if}
    </div>
  {/if}
</section>

<style>
  .grow { flex: 1; min-width: 0; }
  .lead { margin: 2px 0 12px; }
  .hint { margin: 0; }
  .stale { opacity: .6; }
  .dot { width: 12px; height: 12px; border-radius: 50%; flex: none; border: 2px solid var(--border); border-top-color: var(--accent); animation: spin .8s linear infinite; }
  .fix { border: 1px solid color-mix(in srgb, var(--bad) 35%, var(--border)); background: var(--bad-soft); border-radius: 12px; padding: 10px 12px; margin-bottom: 12px; font-size: .9rem; }
  .fix ul { list-style: none; margin: 6px 0 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .fix li { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
  .fix p { margin: 6px 0 0; }
  .classes { list-style: none; margin: 0 0 12px; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 14px; }
  .classes li { display: flex; align-items: baseline; gap: 6px; }
  .next { border: 1px solid color-mix(in srgb, var(--gold) 45%, var(--border)); background: var(--gold-soft); border-radius: 12px; padding: 12px 14px; }
  .next.all { border-color: color-mix(in srgb, var(--ok) 45%, var(--border)); background: var(--ok-soft); }
  .label { display: inline-flex; align-items: center; gap: 4px; font-size: .75rem; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; color: var(--gold); }
  .all .label { color: var(--ok); }
  .what { margin: 4px 0 0; font-weight: 600; }
  .why { margin: 8px 0 0; font-size: .9rem; }
  .next details { margin-top: 8px; font-size: .9rem; }
  .next details :global(pre) { margin: 6px 0 0; }
  summary { cursor: pointer; font-weight: 600; }
  .fold { margin-top: 12px; }
  .fold summary { color: var(--muted); font-size: .9rem; }
  .list { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; font-size: .9rem; }
  .list li { display: flex; gap: 10px; align-items: flex-start; }
  .mark { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; flex: none; background: var(--ok-soft); color: var(--ok); font-weight: 800; font-size: .8rem; }
  .mark.tip { background: var(--gold-soft); color: var(--gold); }
  .items { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 4px; }
  .linkish { border: 0; background: none; padding: 0; color: var(--gold); font-weight: 600; cursor: pointer; text-decoration: underline; white-space: nowrap; }
  .linkish.bad { color: var(--bad); }
  .linkish.cls { color: inherit; font-family: ui-monospace, "Cascadia Code", Consolas, monospace; }
  .linkish:disabled { cursor: default; text-decoration: none; }
  .linkish code { font-size: .85rem; }
</style>
