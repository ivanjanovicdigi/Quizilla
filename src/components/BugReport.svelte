<script lang="ts">
  import Icon from './Icon.svelte';
  import { ApiError, reportBug } from '../lib/api';
  import { session } from '../lib/session.svelte';
  import { router } from '../lib/router.svelte';
  import { bugCtx } from '../lib/bugctx.svelte';
  import { errorText, i18n, t } from '../lib/i18n.svelte';

  // Small "Report a bug" button in the lower left corner. Sends the description plus the
  // current question / screen to the Edge Function report-bug, which opens a GitHub issue.
  // The issue is public: it never contains the student's name or email (see the function).
  const MIN = 5;
  const MAX = 2000;

  let open = $state(false);
  let text = $state('');
  let busy = $state(false);
  let error = $state('');
  let issue = $state<number | null>(null);

  const quiz = $derived(bugCtx.quiz);

  function show() {
    open = true;
    error = '';
    issue = null;
  }

  function close() {
    open = false;
    if (issue) text = '';
  }

  async function send(ev: SubmitEvent) {
    ev.preventDefault();
    const description = text.trim();
    if (description.length < MIN) {
      error = t('bug.too_short', { n: MIN });
      return;
    }
    busy = true;
    error = '';
    try {
      issue = await reportBug({
        description,
        student_id: session.student?.id,
        guest: session.guest || undefined,
        context: {
          screen: router.route.name,
          url: location.hash || '#/',
          lang: i18n.lang,
          time: new Date().toISOString(),
          app_version: __APP_VERSION__,
          quiz: bugCtx.quiz
        }
      });
      text = '';
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      error = code === 'rate_limited' ? t('bug.rate_limited') : errorText(code);
    } finally {
      busy = false;
    }
  }

  function onKey(e: KeyboardEvent) {
    if (open && e.key === 'Escape') close();
  }
</script>

<svelte:window onkeydown={onKey} />

{#if !open}
  <button class="fab" class:above-next={router.route.name === 'quiz'} onclick={show} aria-label={t('bug.button')} title={t('bug.button')}>
    <Icon name="bug" size={18} />
  </button>
{:else}
  <div class="backdrop" role="presentation" onclick={close}></div>
  <div class="sheet card" role="dialog" aria-modal="true" aria-labelledby="bug-title">
    {#if issue}
      <div class="stack center">
        <span class="ok-ico"><Icon name="check" size={28} /></span>
        <h3 id="bug-title">{t('bug.thanks')}</h3>
        <p class="small muted">{t('bug.sent', { n: issue })}</p>
        <button class="btn block" onclick={close}>{t('bug.close')}</button>
      </div>
    {:else}
      <form class="stack" onsubmit={send}>
        <div class="row">
          <h3 id="bug-title" class="grow">{t('bug.title')}</h3>
          <button type="button" class="x" onclick={close} aria-label={t('bug.close')}><Icon name="x" size={20} /></button>
        </div>
        {#if quiz}
          <p class="small ctx">{t('bug.about_question', { id: quiz.question_id, topic: quiz.topic, level: quiz.level })}</p>
        {/if}
        <label class="field">
          <span>{t('bug.label')}</span>
          <!-- svelte-ignore a11y_autofocus -->
          <textarea bind:value={text} rows="4" maxlength={MAX} placeholder={t('bug.placeholder')} autofocus></textarea>
        </label>
        <p class="small muted">{t('bug.public_note')}</p>
        {#if error}<div class="error" role="alert">{error}</div>{/if}
        <button class="btn block" type="submit" disabled={busy}>{busy ? t('common.loading') : t('bug.send')}</button>
      </form>
    {/if}
  </div>
{/if}

<style>
  .fab {
    position: fixed; z-index: 20; left: 12px;
    bottom: calc(72px + env(safe-area-inset-bottom));
    width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center;
    background: var(--surface); color: var(--muted); border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(0, 0, 0, .18); opacity: .85; cursor: pointer;
  }
  .fab.above-next { bottom: calc(86px + env(safe-area-inset-bottom)); }
  .fab:hover, .fab:focus-visible { opacity: 1; color: var(--text); }
  .backdrop { position: fixed; inset: 0; z-index: 30; background: rgba(0, 0, 0, .45); }
  .sheet {
    position: fixed; z-index: 31; left: 50%; transform: translateX(-50%);
    bottom: calc(12px + env(safe-area-inset-bottom));
    width: min(560px, calc(100% - 24px)); max-height: calc(100% - 24px); overflow-y: auto;
  }
  .sheet h3 { margin: 0; }
  .grow { flex: 1; }
  .x { background: none; border: 0; color: var(--muted); cursor: pointer; padding: 4px; display: grid; }
  .ctx { margin: 0; background: var(--surface-2); border-radius: 10px; padding: 8px 10px; }
  .sheet p { margin: 0; }
  textarea {
    width: 100%; box-sizing: border-box; resize: vertical; min-height: 96px; font: inherit;
    padding: 10px 12px; border-radius: 12px; border: 1px solid var(--border);
    background: var(--surface-2); color: var(--text);
  }
  .ok-ico {
    width: 52px; height: 52px; border-radius: 50%; margin: 0 auto; display: grid; place-items: center;
    background: var(--ok-soft); color: var(--ok);
  }
</style>
