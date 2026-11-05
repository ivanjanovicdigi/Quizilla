<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import Rich from '../components/Rich.svelte';
  import CodeEditor from '../components/CodeEditor.svelte';
  import AssignmentFeedback from '../components/AssignmentFeedback.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { load as loadStored, save as saveStored } from '../lib/storage';
  import { signed } from '../lib/util';
  import { checkCode, compilerStatus, loadCompiler, type CheckProgress, type CompilerStatus } from '../lib/assignments/runner';
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
  const errorLines = $derived(new Set((feedback?.diagnostics ?? []).filter((d) => d.severity === 'error' && d.line).map((d) => d.line)));

  async function load() {
    error = '';
    try {
      detail = await api.assignment(assignmentId, studentId);
      const draft = draftKey ? loadStored<string | null>(draftKey, null) : null;
      code = draft ?? detail.latest?.code ?? '';
      if (detail.latest) feedback = fromSubmission(detail.latest);
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
    try {
      const r = await checkCode(code, detail.scenarios, detail.time_limit_ms, (p) => (progress = p));
      feedback = fromCheck(r);
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
      <div class="stack left">
        <section class="card brief">
          <h2>{t('assign.brief')}</h2>
          <Rich text={pick(detail.brief_sk, detail.brief_en)} />
        </section>

        <section class="card">
          <h3>{t('assign.tests', { n: detail.scenarios.length })}</h3>
          <p class="small muted">{t('assign.tests_info')}</p>
          <ul class="scen">
            {#each detail.scenarios as s (s.index)}
              <li><span>{pick(s.name_sk, s.name_en)}</span><span class="muted">{s.points} b.</span></li>
            {/each}
          </ul>
        </section>
      </div>

      <div class="stack right">
        <section class="card stack">
          <div class="row">
            <h2 class="grow">{t('assign.code')}</h2>
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

        {#if feedback}
          <AssignmentFeedback {feedback} scenarios={detail.scenarios} timeLimitMs={detail.time_limit_ms}
            onJump={(line, col) => editor?.focusLine(line, col)} />
        {/if}

        {#if history.length > 1}
          <details class="card">
            <summary><strong>{t('assign.history')}</strong> <span class="muted small">({history.length})</span></summary>
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
      </div>
    </div>
  {/if}
</main>

<style>
  .page.wide { max-width: 1200px; }
  .cols { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 16px; align-items: start; }
  .cols > .stack { margin-top: 0; }
  @media (max-width: 960px) { .cols { grid-template-columns: minmax(0, 1fr); } }
  .left { position: sticky; top: 72px; }
  @media (max-width: 960px) { .left { position: static; } }
  .brief h2 { margin-bottom: 10px; }
  .scen { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 4px; font-size: .9rem; }
  .scen li { display: flex; justify-content: space-between; gap: 12px; }
  .grow { flex: 1; min-width: 0; }
  .actions { flex-wrap: wrap; }
  .status { display: inline-flex; align-items: center; gap: 8px; color: var(--muted); }
  .status.bad { color: var(--bad); }
  .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--border); flex: none; }
  .dot.ok { background: var(--ok); }
  .dot.spin { border: 2px solid var(--border); border-top-color: var(--accent); background: none; animation: spin .8s linear infinite; }
  .saved { color: var(--ok); display: flex; align-items: center; gap: 6px; margin: 0; }
  .hist { list-style: none; margin: 10px 0 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .hist li { display: flex; align-items: center; gap: 10px; }
  summary { cursor: pointer; }
  .mobile-only { display: none; align-items: center; gap: 6px; }
  @media (max-width: 700px) { .mobile-only { display: flex; } }
</style>
