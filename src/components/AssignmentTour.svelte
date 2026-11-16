<script lang="ts">
  // Short introduction of the coding assignment page: a card that walks through the parts of
  // the page one by one. The page highlights the part of the current step (class "spot" in
  // Assignment.svelte); this component is the dimmed backdrop and the card. Can be skipped at
  // any step (button, Esc or a click outside).
  import { t, type Key } from '../lib/i18n.svelte';
  import { TOUR_STEPS } from '../lib/assignments/tour';

  let {
    step,
    onStep,
    onClose,
  }: {
    step: number;                       // index into TOUR_STEPS
    onStep: (step: number) => void;
    onClose: () => void;
  } = $props();

  const id = $derived(TOUR_STEPS[step]);
  const last = $derived(step === TOUR_STEPS.length - 1);
  let next: HTMLButtonElement | undefined = $state();

  // keyboard users land on "Next" at every step
  $effect(() => {
    void step;
    next?.focus();
  });

  function forward() {
    if (last) onClose();
    else onStep(step + 1);
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowRight') forward();
    else if (e.key === 'ArrowLeft' && step > 0) onStep(step - 1);
  }
</script>

<svelte:window onkeydown={onKeydown} />

<div class="backdrop" role="presentation" onclick={onClose}></div>
<div class="tour card" role="dialog" aria-modal="true" aria-labelledby="tour-title">
  <div class="row top">
    <span class="small muted count">{step + 1} / {TOUR_STEPS.length}</span>
    <span class="grow"></span>
    {#if !last}<button class="skip" onclick={onClose}>{t('tour.skip')}</button>{/if}
  </div>
  <h2 id="tour-title">{t(`tour.${id}.title` as Key)}</h2>
  <p>{t(`tour.${id}.text` as Key)}</p>
  <div class="row actions">
    <span class="dots" aria-hidden="true">
      {#each TOUR_STEPS as s, i (s)}<span class:on={i === step}></span>{/each}
    </span>
    <span class="grow"></span>
    {#if step > 0}<button class="btn small secondary" onclick={() => onStep(step - 1)}>{t('tour.back')}</button>{/if}
    <button bind:this={next} class="btn small" onclick={forward}>{t(last ? 'tour.done' : 'tour.next')}</button>
  </div>
</div>

<style>
  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(0, 0, 0, .55); }
  .tour {
    position: fixed; z-index: 32; left: 50%; transform: translateX(-50%);
    bottom: calc(84px + env(safe-area-inset-bottom));
    width: min(460px, calc(100vw - 24px));
    box-shadow: 0 12px 40px rgba(0, 0, 0, .35);
  }
  .grow { flex: 1; }
  .top { min-height: 24px; }
  .count { font-variant-numeric: tabular-nums; }
  .skip { border: 0; background: none; padding: 4px 0; color: var(--muted); font-weight: 600; cursor: pointer; text-decoration: underline; }
  h2 { margin: 6px 0; }
  p { margin: 0 0 14px; line-height: 1.5; }
  .actions { gap: 8px; }
  .dots { display: inline-flex; gap: 6px; }
  .dots span { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
  .dots span.on { background: var(--accent); }
</style>
