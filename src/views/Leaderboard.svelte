<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import { api, ApiError } from '../lib/api';
  import { session } from '../lib/session.svelte';
  import { errorText, t } from '../lib/i18n.svelte';
  import type { ClassRow } from '../lib/types';

  // Global class leaderboard: one column per class with its all-time total points.
  // Students also get a "Mine" tab with their own statistics. Opens on "Class" every time.
  let tab = $state<'class' | 'mine'>('class');
  let classes = $state<ClassRow[] | null>(null);
  let error = $state('');

  async function load() {
    error = '';
    try {
      classes = await api.classLeaderboard();
    } catch (e) {
      error = errorText(e instanceof ApiError ? e.code : 'server');
    }
  }
  onMount(load);

  const myClassId = $derived(session.student?.class_id);
  const max = $derived(Math.max(1, ...(classes ?? []).map((c) => c.points)));
  const leader = (c: ClassRow) => c.rank === 1 && c.points > 0;
</script>

<TopBar title={t('nav.leaderboard')} />

<main class="page stack">
  {#if session.student}
    <div class="segmented">
      <button class:active={tab === 'class'} onclick={() => (tab = 'class')}>{t('lb.tab_class')}</button>
      <button class:active={tab === 'mine'} onclick={() => (tab = 'mine')}>{t('lb.tab_mine')}</button>
    </div>
  {/if}

  {#if tab === 'mine' && session.student}
    <StatsPanel />
  {:else if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !classes}
    <div class="spinner"></div>
  {:else if !classes.length}
    <p class="muted center">{t('lb.empty')}</p>
  {:else}
    <section class="card podium" style:--cols={classes.length}>
      {#each classes as c (c.class_id)}
        <div class="col" class:mine={c.class_id === myClassId} class:lead={leader(c)}>
          <div class="tag small">
            {#if leader(c)}<Icon name="trophy" size={14} /> {t('lb.leader')}{/if}
          </div>
          <strong class="pts">{c.points}</strong>
          <div class="track">
            <i style:height={`${Math.max(4, (c.points / max) * 100)}%`}></i>
          </div>
          <strong class="name">{c.name}</strong>
          <span class="small muted mine-tag">{c.class_id === myClassId ? t('lb.mine') : ''}</span>
        </div>
      {/each}
    </section>
    <p class="small muted center">{t('lb.how')}</p>
  {/if}
</main>

<style>
  .podium {
    display: grid; grid-template-columns: repeat(var(--cols), 1fr); gap: 10px;
    padding: 16px 12px;
  }
  .col {
    display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 0;
    padding: 8px 4px; border-radius: 14px;
  }
  .col.mine { background: var(--accent-soft); }
  .tag {
    min-height: 1.3em; display: inline-flex; align-items: center; gap: 4px;
    color: var(--gold); font-weight: 700;
  }
  .pts { font-size: 1.35rem; font-variant-numeric: tabular-nums; }
  .track {
    width: 100%; max-width: 64px; height: 160px; border-radius: 12px;
    background: var(--surface-2); display: flex; align-items: flex-end; overflow: hidden;
  }
  .track i { display: block; width: 100%; background: var(--accent); border-radius: 12px 12px 0 0; transition: height .4s ease; }
  .lead .track i { background: var(--gold); }
  .name { text-align: center; overflow-wrap: anywhere; }
  .mine-tag { min-height: 1.2em; text-align: center; }
</style>
