<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, t } from '../lib/i18n.svelte';
  import { load as loadPref, save as savePref } from '../lib/storage';
  import type { ClassRanking, ClassRow } from '../lib/types';

  type Tab = 'classes' | 'mine';
  let tab = $state<Tab>(loadPref<Tab>('quizilla.lb.tab', 'classes'));
  let days = $state<number | null>(loadPref<number | null>('quizilla.lb.days', 7));

  let classes = $state<ClassRow[] | null>(null);
  let ranking = $state<ClassRanking | null>(null);
  let error = $state('');
  let loading = $state(false);

  async function load() {
    loading = true;
    error = '';
    try {
      if (tab === 'classes') classes = await api.classLeaderboard(days);
      else ranking = await api.classRanking(session.student!.id, days);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    savePref('quizilla.lb.tab', tab);
    savePref('quizilla.lb.days', days);
    load();
  });

  const myClassId = $derived(session.student?.class_id);
</script>

<TopBar title={t('nav.leaderboard')} />

<main class="page stack">
  <div class="segmented">
    <button class:active={tab === 'classes'} onclick={() => (tab = 'classes')}>{t('lb.classes')}</button>
    <button class:active={tab === 'mine'} onclick={() => (tab = 'mine')}>{t('lb.my_class')}</button>
  </div>
  <div class="segmented period">
    <button class:active={days === 7} onclick={() => (days = 7)}>{t('lb.week')}</button>
    <button class:active={days === null} onclick={() => (days = null)}>{t('lb.all')}</button>
  </div>

  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if loading && !(tab === 'classes' ? classes : ranking)}
    <div class="spinner"></div>
  {:else if tab === 'classes' && classes}
    <p class="small muted">{t('lb.how')}</p>
    <ol class="list card">
      {#each classes as c (c.class_id)}
        <li class:me={c.class_id === myClassId}>
          <span class="rank r{c.rank}">{c.rank}</span>
          <div class="grow">
            <strong>{c.name}</strong>
            <div class="small muted">{t('lb.students', { active: c.active_students, total: c.students })}</div>
          </div>
          <div class="right">
            <strong>{t('lb.avg', { n: c.avg_points })}</strong>
            <div class="small muted">{t('lb.points', { n: c.points })}</div>
          </div>
        </li>
      {:else}
        <li class="muted">{t('lb.empty')}</li>
      {/each}
    </ol>
  {:else if tab === 'mine' && ranking}
    <h2>{ranking.class_name}</h2>
    <ol class="list card">
      {#each ranking.students as s, i (i)}
        <li class:me={s.is_me}>
          <span class="rank r{s.rank}">{s.rank}</span>
          <div class="grow"><strong>{s.name}</strong>{#if s.is_me} <span class="pill ok">{t('lb.me')}</span>{/if}</div>
          <strong class="right">{t('lb.points', { n: s.points })}</strong>
        </li>
      {:else}
        <li class="muted">{t('lb.empty')}</li>
      {/each}
    </ol>
  {/if}
</main>

<style>
  .period { max-width: 280px; }
  .list { list-style: none; margin: 0; padding: 4px 0; }
  .list li { display: flex; align-items: center; gap: 12px; padding: 12px 16px; }
  .list li + li { border-top: 1px solid var(--border); }
  .list li.me { background: var(--accent-soft); }
  .grow { flex: 1; min-width: 0; }
  .right { text-align: right; white-space: nowrap; }
  .rank {
    width: 32px; height: 32px; border-radius: 50%; flex: none;
    display: grid; place-items: center; font-weight: 800; font-size: .9rem;
    background: var(--surface-2); color: var(--muted);
  }
  .rank.r1 { background: #fbbf24; color: #422006; }
  .rank.r2 { background: #cbd5e1; color: #1e293b; }
  .rank.r3 { background: #d6a477; color: #3b2412; }
</style>
