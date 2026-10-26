<script lang="ts">
  import { onMount, tick } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import ClassBoard from '../components/ClassBoard.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setAdmin } from '../lib/session.svelte';
  import { errorText, i18n, t } from '../lib/i18n.svelte';
  import type { AdminUser } from '../lib/types';

  // Admin (017_admin.sql): list roster users, activate / deactivate, reset progress.
  // Tap "Statistics" on a user → their full statistics, as they see them (024).
  // "Leaderboard" tab: the class leaderboard students see + a student ranking (admin only).
  let users = $state<AdminUser[] | null>(null);
  let error = $state('');
  let notice = $state('');
  let busyEmail = $state<string | null>(null);
  let query = $state('');
  let filter = $state<string>('all'); // 'all' | 'inactive' | class name
  let viewing = $state<AdminUser | null>(null); // user whose statistics are open
  let section = $state<'users' | 'board'>('users');
  let listScroll = 0;

  function openStats(u: AdminUser) {
    listScroll = window.scrollY;
    viewing = u;
    window.scrollTo(0, 0);
  }

  async function closeStats() {
    viewing = null;
    await tick();
    window.scrollTo(0, listScroll);
  }

  const token = () => session.admin!.token;

  function fail(e: unknown) {
    const code = e instanceof ApiError ? e.code : 'server';
    if (code === 'not_admin') {
      setAdmin(null); // session expired → back to login
      return;
    }
    error = code === 'unknown_user' ? t('admin.unknown_user') : errorText(code);
  }

  async function load() {
    error = '';
    try {
      users = await api.adminUsers(token());
    } catch (e) {
      fail(e);
    }
  }
  onMount(load);

  // Student ranking by all-time points (only users with answers).
  const ranking = $derived(
    (users ?? []).filter((u) => u.answers > 0).sort((a, b) => b.points - a.points || b.answers - a.answers)
  );

  const classes = $derived([...new Set((users ?? []).map((u) => u.class_name))]);
  const shown = $derived.by(() => {
    const q = query.trim().toLowerCase();
    return (users ?? []).filter((u) => {
      if (filter === 'inactive' && u.is_active) return false;
      if (filter !== 'all' && filter !== 'inactive' && u.class_name !== filter) return false;
      return !q || u.name.toLowerCase().includes(q) || u.email.includes(q);
    });
  });

  async function toggleActive(u: AdminUser) {
    const next = !u.is_active;
    if (!confirm(t(next ? 'admin.confirm_activate' : 'admin.confirm_deactivate', { name: u.name }))) return;
    busyEmail = u.email;
    error = '';
    notice = '';
    try {
      await api.adminSetActive(token(), u.email, next);
      notice = t(next ? 'admin.done_activate' : 'admin.done_deactivate', { name: u.name });
      await load();
    } catch (e) {
      fail(e);
    } finally {
      busyEmail = null;
    }
  }

  async function reset(u: AdminUser) {
    if (!confirm(t('admin.confirm_reset', { name: u.name }))) return;
    busyEmail = u.email;
    error = '';
    notice = '';
    try {
      const r = await api.adminResetProgress(token(), u.email);
      notice = t('admin.done_reset', { name: u.name, n: r.answers });
      await load();
    } catch (e) {
      fail(e);
    } finally {
      busyEmail = null;
    }
  }

  async function logout() {
    try {
      await api.adminLogout(token());
    } catch {
      /* ignore – the session is dropped on this device anyway */
    }
    setAdmin(null);
    location.hash = '#/';
  }

  function seen(d: string | null) {
    if (!d) return t('admin.never');
    return new Date(d).toLocaleString(i18n.lang === 'sk' ? 'sk-SK' : 'en-GB', { dateStyle: 'short', timeStyle: 'short' });
  }
</script>

<TopBar title={viewing ? viewing.name : t('admin.title')} />

{#if viewing}
  <main class="page stack">
    <div class="row head">
      <button class="btn small secondary" onclick={closeStats}><Icon name="back" size={16} /> {t('admin.back_to_list')}</button>
      <span class="grow"></span>
      <span class="pill">{viewing.class_name}</span>
    </div>
    <div class="small muted">
      <span class="email">{viewing.email}</span> ·
      {t('admin.stats', { a: viewing.answers, p: viewing.points })}
    </div>
    {#key viewing.email}
      <StatsPanel source={() => api.adminStudentStats(token(), viewing!.email)} onError={(c) => fail(new ApiError(c))} />
    {/key}
  </main>
{:else}
<main class="page stack">
  <div class="row head">
    <p class="small muted grow">{t('admin.info')}</p>
    <button class="btn small secondary" onclick={logout}>{t('admin.logout')}</button>
  </div>

  {#if error}<div class="error" role="alert">{error}</div>{/if}
  {#if notice}<div class="notice small" role="status"><Icon name="check" size={16} /> {notice}</div>{/if}

  <div class="segmented">
    <button class:active={section === 'users'} onclick={() => (section = 'users')}>{t('admin.tab_users')}</button>
    <button class:active={section === 'board'} onclick={() => (section = 'board')}>{t('nav.leaderboard')}</button>
  </div>

  {#if section === 'board'}
    <ClassBoard />
    <h3>{t('admin.ranking')}</h3>
    <p class="small muted">{t('admin.ranking_info')}</p>
    {#if !users}
      {#if !error}<div class="spinner"></div>{/if}
    {:else if !ranking.length}
      <p class="muted center">{t('lb.empty')}</p>
    {:else}
      <section class="card ranking">
        {#each ranking as u, i (u.email)}
          <button class="rank-row" onclick={() => openStats(u)}>
            <span class="no">{i + 1}.</span>
            <span class="grow">
              <strong>{u.name}</strong>
              <span class="small muted">{u.class_name}{u.is_active ? '' : ` · ${t('admin.inactive_one')}`}</span>
            </span>
            <span class="right">
              <strong>{u.points}</strong>
              <span class="small muted">{t('admin.answers_n', { n: u.answers })}</span>
            </span>
          </button>
        {/each}
      </section>
    {/if}
  {:else if !users}
    {#if !error}<div class="spinner"></div>{/if}
  {:else}
    <label class="field">
      <span>{t('admin.search')}</span>
      <input bind:value={query} type="search" autocomplete="off" placeholder={t('admin.search_hint')} />
    </label>
    <div class="chips">
      <button class:active={filter === 'all'} onclick={() => (filter = 'all')}>{t('admin.all')} ({users.length})</button>
      {#each classes as c (c)}
        <button class:active={filter === c} onclick={() => (filter = c)}>{c}</button>
      {/each}
      <button class:active={filter === 'inactive'} onclick={() => (filter = 'inactive')}>{t('admin.inactive')}</button>
    </div>

    {#each shown as u (u.email)}
      <section class="card user" class:off={!u.is_active}>
        <div class="row">
          <div class="grow">
            <strong>{u.name}</strong>
            <div class="small muted email">{u.email}</div>
          </div>
          <span class="pill">{u.class_name}</span>
        </div>
        <div class="small muted meta">
          {#if !u.is_active}<span class="pill bad">{t('admin.inactive_one')}</span>{/if}
          {t('admin.stats', { a: u.answers, p: u.points })} ·
          {u.last_seen_at ? t('admin.last_seen', { d: seen(u.last_seen_at) }) : t('admin.never')}
        </div>
        <div class="row actions">
          <button class="btn small" disabled={!u.logged_in} onclick={() => openStats(u)}>
            <Icon name="chart" size={16} /> {t('admin.view_stats')}
          </button>
          <button class="btn small secondary" disabled={busyEmail === u.email} onclick={() => toggleActive(u)}>
            {u.is_active ? t('admin.deactivate') : t('admin.activate')}
          </button>
          <button class="btn small danger" disabled={busyEmail === u.email || u.answers === 0} onclick={() => reset(u)}>
            {t('admin.reset')}
          </button>
        </div>
      </section>
    {:else}
      <p class="muted center">{t('admin.none')}</p>
    {/each}
  {/if}
</main>
{/if}

<style>
  .head { gap: 12px; align-items: center; }
  .head p { margin: 0; }
  .grow { flex: 1; min-width: 0; }
  .notice {
    display: flex; align-items: center; gap: 6px; padding: 10px 12px; border-radius: 12px;
    background: var(--ok-soft); color: var(--ok); font-weight: 600;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chips button {
    border: 1px solid var(--border); background: var(--surface); color: var(--muted);
    border-radius: 999px; padding: 6px 12px; font: inherit; font-size: .85rem; cursor: pointer;
  }
  .chips button.active { background: var(--accent-soft); color: var(--accent-strong); border-color: transparent; font-weight: 700; }
  .user { display: flex; flex-direction: column; gap: 8px; }
  .user.off { opacity: .75; }
  .email { overflow-wrap: anywhere; }
  .meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
  .pill.bad { background: var(--bad-soft); color: var(--bad); }
  .actions { gap: 8px; flex-wrap: wrap; }
  .ranking { display: flex; flex-direction: column; padding: 4px 0; }
  .rank-row {
    display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 14px;
    border: 0; border-top: 1px solid var(--border); background: none; color: var(--text);
    font: inherit; text-align: left; cursor: pointer;
  }
  .rank-row:first-child { border-top: 0; }
  .rank-row .no { width: 2.2em; flex: none; color: var(--muted); font-variant-numeric: tabular-nums; }
  .rank-row .grow { display: flex; flex-direction: column; }
  .rank-row .right { display: flex; flex-direction: column; align-items: flex-end; font-variant-numeric: tabular-nums; }
</style>
