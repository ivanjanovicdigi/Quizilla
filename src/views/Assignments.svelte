<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { loadCompiler } from '../lib/assignments/runner';
  import type { AssignmentSummary } from '../lib/types';

  let list = $state<AssignmentSummary[] | null>(null);
  let error = $state('');

  async function load() {
    error = '';
    try {
      list = await api.assignments(session.student?.id ?? null);
      // start downloading the compiler in the background – the student will probably open one
      loadCompiler().catch(() => {});
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    }
  }
  onMount(load);
</script>

<TopBar title={t('assign.title')} back="#/" />

<main class="page stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !list}
    <div class="spinner"></div>
  {:else}
    <p class="muted small">{t('assign.list_info')}</p>
    <p class="muted small mobile-only"><Icon name="code" size={14} /> {t('assign.desktop_note')}</p>
    {#if list.length === 0}
      <p class="muted center">{t('assign.empty')}</p>
    {/if}
    {#each list as a (a.id)}
      {@const done = a.latest && a.latest.score === a.latest.max_points}
      <a class="card tappable item" href={`#/assignment/${a.id}`}>
        <div class="row">
          <span class="ico" class:done><Icon name={done ? 'check' : 'code'} size={22} /></span>
          <div class="grow">
            <h3>{pick(a.title_sk, a.title_en)}</h3>
            <p class="small muted">
              {#if a.latest}
                {t('assign.submissions', { n: a.submissions })}
              {:else}
                {t('assign.not_tried')}
              {/if}
            </p>
          </div>
          {#if a.latest && !session.guest}
            <span class="pill" class:ok={done} class:gold={!done && a.latest.score > 0}>
              {t('assign.score', { score: a.latest.score, max: a.latest.max_points })}
            </span>
          {/if}
          <span class="chev"><Icon name="chevron" size={18} /></span>
        </div>
      </a>
    {/each}
  {/if}
</main>

<style>
  .item { text-decoration: none; color: inherit; }
  .item p { margin: 2px 0 0; }
  .grow { flex: 1; min-width: 0; }
  .ico { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 12px; background: var(--info-soft); color: var(--info); flex: none; }
  .ico.done { background: var(--ok-soft); color: var(--ok); }
  .chev { color: var(--muted); }
  .mobile-only { display: none; align-items: center; gap: 6px; }
  @media (max-width: 700px) { .mobile-only { display: flex; } }
</style>
