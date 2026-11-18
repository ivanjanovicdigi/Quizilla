<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import AssignmentBrief from '../components/AssignmentBrief.svelte';
  import CodeEditor from '../components/CodeEditor.svelte';
  import AssignmentFeedback from '../components/AssignmentFeedback.svelte';
  import Coach from '../components/Coach.svelte';
  import AssignmentTour from '../components/AssignmentTour.svelte';
  import { TOUR_STEPS, markTourSeen, tourSeen } from '../lib/assignments/tour';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { load as loadStored, save as saveStored } from '../lib/storage';
  import { signed } from '../lib/util';
  import { analyzeCode, checkCode, compilerStatus, loadCompiler, type CheckProgress, type CompilerStatus, type DesignReview, type Diagnostic } from '../lib/assignments/runner';
  import { errorsForServer, fromCheck, fromSubmission, type Feedback } from '../lib/assignments/feedback';
  import type { AssignmentDetail, Submission } from '../lib/types';

  let { assignmentId }: { assignmentId: number } = $props();

  const MAX_CODE = 100_000;
  const studentId = session.student?.id ?? null;
  // drafts are kept per assignment and student in this browser; guests keep nothing
  const draftKey = $derived(studentId ? `quizilla.draft.${studentId}.${assignmentId}` : null);

  let detail = $state<AssignmentDetail | null>(null);
  let error = $state('');
  let code = $state('');
  let feedback = $state<Feedback | null>(null);
  let testedCode = $state<string | null>(null);   // the code the feedback belongs to (for the coach)
  let progress = $state<CheckProgress | null>(null);
  let checkError = $state('');
  let compiler = $state<CompilerStatus>(compilerStatus().status);
  let save = $state<{ state: 'idle' | 'saving' | 'saved' | 'failed'; change?: number | null; error?: string }>({ state: 'idle' });
  let pending: Parameters<typeof api.submitAssignment> | null = null;
  let history = $state<Submission[]>([]);
  let editor: ReturnType<typeof CodeEditor> | undefined = $state();
  let fileInput: HTMLInputElement | undefined = $state();

  const sub = compilerStatus((s) => (compiler = s));
  onDestroy(() => sub.unsubscribe());

  const busy = $derived(progress !== null);

  // First visit: a short tour of the page. Skippable; "How it works" opens it again.
  let tour = $state<number | null>(null);                 // index into TOUR_STEPS
  const spot = $derived(tour == null ? null : TOUR_STEPS[tour]);
  function closeTour() {
    tour = null;
    markTourSeen();
  }
  $effect(() => {
    // bring the highlighted part into view (matters when the columns are stacked)
    if (spot && spot !== 'intro') document.querySelector('.spot')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });

  // Live design guide: a moment after the student stops typing the code is compiled in the
  // browser (no tests, nothing stored) → compile errors + design review for Coach.
  let review = $state<DesignReview | null>(null);        // of the last version that compiled
  let liveErrors = $state<Diagnostic[] | null>(null);    // null = not analysed yet
  let analysing = $state(false);
  let analyseTimer: ReturnType<typeof setTimeout> | undefined;
  let analyseSeq = 0;
  const errorsOnly = (d: Diagnostic[]) => d.filter((x) => x.severity === 'error');
  const shownErrors = $derived(liveErrors ?? errorsOnly(feedback?.diagnostics ?? []));
  const errorLines = $derived(new Set(shownErrors.filter((d) => d.line).map((d) => d.line)));

  $effect(() => {
    const c = code;
    const idle = compiler === 'ready' && !busy && detail != null;
    clearTimeout(analyseTimer);
    if (!idle) return;
    if (!c.trim()) { analyseSeq++; review = null; liveErrors = null; analysing = false; return; }
    if (c.length > MAX_CODE) return;
    analyseTimer = setTimeout(async () => {
      const seq = ++analyseSeq;
      analysing = true;
      const r = await analyzeCode(c);
      if (seq !== analyseSeq) return;
      analysing = false;
      if (!r) return;
      liveErrors = errorsOnly(r.diagnostics);
      if (r.design) review = r.design;
    }, 900);
  });
  onDestroy(() => clearTimeout(analyseTimer));

  async function load() {
    error = '';
    try {
      detail = await api.assignment(assignmentId, studentId);
      const draft = draftKey ? loadStored<string | null>(draftKey, null) : null;
      code = draft ?? detail.latest?.code ?? '';
      if (detail.latest) { feedback = fromSubmission(detail.latest); testedCode = detail.latest.code ?? null; }
      if (!tourSeen()) tour = 0;
      loadHistory();
    } catch (e) {
      const c = e instanceof ApiError ? e.code : 'server';
      if (c === 'unknown_student') setStudent(null);
      error = errorText(c);
    }
  }

  async function loadHistory() {
    if (!studentId) return;
    try {
      history = await api.assignmentSubmissions(studentId, assignmentId);
    } catch {
      /* history is optional */
    }
  }

  onMount(() => {
    load();
    loadCompiler().catch(() => {}); // start the big download right away (status is shown)
  });

  // keep the draft in this browser (debounced)
  let draftTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const c = code;
    if (!draftKey || !detail) return;
    clearTimeout(draftTimer);
    draftTimer = setTimeout(() => saveStored(draftKey, c.trim() ? c : null), 500);
  });

  async function check() {
    if (!detail || busy) return;
    checkError = '';
    if (!code.trim()) { checkError = t('assign.empty_code'); return; }
    if (code.length > MAX_CODE) { checkError = errorText('invalid_code'); return; }
    progress = { phase: 'loading' };
    save = { state: 'idle' };
    const checked = code;
    try {
      const r = await checkCode(checked, detail.scenarios, detail.time_limit_ms, (p) => (progress = p));
      feedback = fromCheck(r);
      testedCode = checked;
      analyseSeq++; // the check is newer than any analysis still on its way
      analysing = false;
      liveErrors = errorsOnly(r.diagnostics);
      if (r.design) review = r.design;
      if (studentId) {
        pending = [
          studentId, assignmentId, code, r.compiled, errorsForServer(r.diagnostics),
          r.results.map((x) => ({ scenario: x.index, passed: x.passed, actual: x.actual.slice(0, 4000) })),
        ];
        await submit();
      }
    } catch (e) {
      checkError = t('assign.compiler_error');
      console.error(e);
    } finally {
      progress = null;
    }
  }

  async function submit() {
    if (!pending) return;
    save = { state: 'saving' };
    try {
      const s = await api.submitAssignment(...pending);
      pending = null;
      save = { state: 'saved', change: s.previous_score == null ? null : s.points_change };
      if (feedback) feedback = { ...feedback, score: s.score, max_points: s.max_points }; // the server's score counts
      loadHistory();
    } catch (e) {
      const c = e instanceof ApiError ? e.code : 'server';
      if (c === 'unknown_student') setStudent(null);
      save = { state: 'failed', error: errorText(c) };
    }
  }

  async function onFile(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    let text = '';
    try {
      if (file.size > MAX_CODE * 2) throw new Error('too big');
      text = (await file.text()).replace(/^﻿/, '').replace(/\r\n?/g, '\n');
      if (text.length > MAX_CODE || text.includes('\u0000')) throw new Error('bad');
    } catch {
      checkError = t('assign.upload_bad');
      return;
    }
    if (code.trim() && code !== text && !confirm(t('assign.upload_replace', { name: file.name }))) return;
    code = text;
    checkError = '';
  }

  async function openSubmission(id: number) {
    if (!studentId) return;
    if (code.trim() && !confirm(t('assign.history_replace'))) return;
    try {
      const s = await api.assignmentSubmission(studentId, id);
      code = s.code ?? '';
      feedback = fromSubmission(s, id === history[0]?.id);
      testedCode = s.code ?? null;
      save = { state: 'idle' };
    } catch (e) {
      checkError = errorText(e instanceof ApiError ? e.code : 'server');
    }
  }

  function progressText(p: CheckProgress) {
    if (p.phase === 'loading') return t('assign.loading_compiler');
    if (p.phase === 'compiling') return t('assign.compiling');
    return t('assign.running', { i: Math.min((p.done ?? 0) + 1, p.total ?? 1), n: p.total ?? 0 });
  }
</script>

<TopBar title={detail ? pick(detail.title_sk, detail.title_en) : t('assign.title')} back="#/assignments" />

<main class="page wide stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !detail}
    <div class="spinner"></div>
  {:else}
    <p class="muted small mobile-only"><Icon name="code" size={14} /> {t('assign.desktop_note')}</p>

    <div class="cols">
      <div class="left" class:spot={spot === 'brief'}>
        <section class="card brief">
          <h2>{t('assign.brief')}</h2>
          <AssignmentBrief text={pick(detail.brief_sk, detail.brief_en)} />
        </section>
      </div>

      <div class="stack mid" class:spot={spot === 'code'}>
        <section class="card stack">
          <div class="row head">
            <h2 class="grow">{t('assign.code')}</h2>
            <button class="btn small ghost" onclick={() => (tour = 0)}>{t('tour.open')}</button>
            {#if history.length > 1}
              <details class="menu">
                <summary class="btn small ghost">{t('assign.history_short')} ({history.length})</summary>
                <ul class="hist">
                  {#each history as h (h.id)}
                    <li>
                      <span class="muted small">{new Date(h.submitted_at).toLocaleString()}</span>
                      <span class="grow"></span>
                      <strong>{h.score} / {h.max_points}</strong>
                      <button class="btn small ghost" onclick={() => openSubmission(h.id)}>{t('assign.history_open')}</button>
                    </li>
                  {/each}
                </ul>
              </details>
            {/if}
            <button class="btn small secondary" onclick={() => fileInput?.click()} disabled={busy}>
              <Icon name="upload" size={16} /> {t('assign.upload')}
            </button>
            <input bind:this={fileInput} type="file" accept=".cs,text/plain" hidden onchange={onFile} />
          </div>
          <CodeEditor bind:this={editor} bind:value={code} {errorLines} placeholder={t('assign.placeholder')} label={t('assign.code')} />
          {#if draftKey}<p class="small muted">{t('assign.draft_note')}</p>{/if}

          <div class="row actions">
            <button class="btn" onclick={check} disabled={busy || compiler === 'loading' && !progress}>
              <Icon name="play" size={16} /> {session.guest ? t('assign.check_guest') : t('assign.check')}
            </button>
            <span class="small status" class:bad={compiler === 'error'}>
              {#if progress}
                <span class="dot spin"></span> {progressText(progress)}
              {:else if compiler === 'loading'}
                <span class="dot spin"></span> {t('assign.loading_compiler')}
              {:else if compiler === 'ready'}
                <span class="dot ok"></span> {t('assign.compiler_ready')}
              {:else if compiler === 'error'}
                {t('assign.compiler_error')}
              {/if}
            </span>
          </div>
          {#if session.guest}<p class="small muted">{t('assign.guest_note')}</p>{/if}
          {#if checkError}<div class="error">{checkError}</div>{/if}
          {#if save.state === 'saving'}
            <p class="small muted">{t('assign.saving')}</p>
          {:else if save.state === 'saved'}
            <p class="small saved"><Icon name="check" size={16} />
              {save.change == null ? t('assign.saved') : t('assign.saved_change', { change: signed(save.change) })}</p>
          {:else if save.state === 'failed'}
            <div class="error row">
              <span class="grow">{t('assign.save_failed')} {save.error}</span>
              <button class="btn small secondary" onclick={submit}>{t('common.retry')}</button>
            </div>
          {/if}
        </section>

      </div>

      <div class="stack right">
        <div class="part" class:spot={spot === 'guide'}>
          <Coach {code} {review} errors={shownErrors} {feedback} {testedCode} scenarios={detail.scenarios} {analysing}
            buttonLabel={session.guest ? t('assign.check_guest') : t('assign.check')}
            onJump={(line, col) => editor?.focusLine(line, col)} />
        </div>
        <div class="part" class:spot={spot === 'tests'}>
          <AssignmentFeedback {feedback} scenarios={detail.scenarios} timeLimitMs={detail.time_limit_ms} />
        </div>
      </div>
    </div>

    {#if tour != null}
      <AssignmentTour step={tour} onStep={(s) => (tour = s)} onClose={closeTour} />
    {/if}
  {/if}
</main>

<style>
  /* phone: one column · laptop: brief on top, code | guide · wide: brief | code | guide + tests */
  .page.wide { max-width: 1680px; }
  .cols { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; align-items: start; }
  .cols > .stack { margin-top: 0; }
  /* tour: the part being explained sits above the dimmed backdrop (z-index 30) */
  .left, .mid, .part { position: relative; }
  .spot { z-index: 31; border-radius: var(--radius); outline: 3px solid var(--accent); outline-offset: 4px; }
  @media (min-width: 900px) {
    .cols { grid-template-columns: minmax(0, 7fr) minmax(0, 5fr); }
    .left { grid-column: 1 / -1; }
  }
  @media (min-width: 1280px) {
    .cols { grid-template-columns: minmax(300px, 7fr) minmax(0, 11fr) minmax(320px, 8fr); }
    .left { grid-column: auto; position: sticky; top: 72px; max-height: calc(100vh - 88px); overflow: auto; border-radius: var(--radius); }
    .mid :global(.editor) { height: min(68vh, 760px); }
  }
  .brief h2 { margin-bottom: 10px; }
  .head { flex-wrap: wrap; }
  .menu { position: relative; }
  .menu summary { list-style: none; }
  .menu summary::-webkit-details-marker { display: none; }
  .menu .hist { position: absolute; right: 0; top: calc(100% + 4px); z-index: 5; margin: 0; min-width: 340px; max-height: 320px; overflow: auto;
    padding: 8px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow); }
  .grow { flex: 1; min-width: 0; }
  .actions { flex-wrap: wrap; }
  .status { display: inline-flex; align-items: center; gap: 8px; color: var(--muted); }
  .status.bad { color: var(--bad); }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--border); flex: none; }
  .dot.ok { background: var(--ok); }
  .dot.spin { border: 2px solid var(--border); border-top-color: var(--accent); background: none; animation: spin .8s linear infinite; }
  .saved { color: var(--ok); display: flex; align-items: center; gap: 6px; margin: 0; }
  .hist { list-style: none; display: flex; flex-direction: column; gap: 4px; }
  .hist li { display: flex; align-items: center; gap: 10px; }
  summary { cursor: pointer; }
  .mobile-only { display: none; align-items: center; gap: 6px; }
  @media (max-width: 700px) { .mobile-only { display: flex; } }
</style>
