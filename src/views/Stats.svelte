<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import RankBadge, { rankImage } from '../components/RankBadge.svelte';
  import AccuracyChart from '../components/AccuracyChart.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { load as loadPref, save as savePref } from '../lib/storage';
  import { pct } from '../lib/util';
  import type { Stats } from '../lib/types';

  const PASS = 0.75; // matches topic_pass_accuracy in quiz.config (dashed line in the charts)

  let data = $state<Stats | null>(null);
  let error = $state('');
  let loading = $state(false);
  let days = $state<number | null>(loadPref<number | null>('quizilla.stats.days', 30));

  async function load() {
    loading = true;
    error = '';
    try {
      data = await api.getStats(session.student!.id, days);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    } finally {
      loading = false;
    }
  }

  function setDays(d: number | null) {
    days = d;
    savePref('quizilla.stats.days', d);
    load();
  }

  onMount(load);
</script>

<TopBar title={t('stats.title')} back="#/profile" />

<main class="page stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !data}
    <div class="spinner"></div>
  {:else}
    <!-- ranks -->
    <section class="card stack">
      <div class="row">
        <h3 class="grow">{t('stats.ranks')}</h3>
        <RankBadge rank={data.rank.current} />
      </div>
      {#each data.rank.ranks as r (r.key)}
        {@const need = Math.round(r.accuracy * 100)}
        {@const enough = r.key === 'grand_master'
          ? data.rank.ranks.filter((x) => x.difficulty !== null).every((x) => x.answers >= data!.rank.min_answers)
          : r.answers >= data.rank.min_answers}
        <div class="rank-row" class:earned={r.earned}>
          <span class="rank-ico">
            <img src={rankImage(r.key)} alt="" width="30" height="30" />
          </span>
          <div class="grow">
            <strong>{t(`rank.${r.key}`)}</strong>
            <div class="small muted">{t(`rank.rule.${r.key}`, { pct: need })}</div>
          </div>
          <div class="small right">
            <strong>{r.answers ? `${pct(r.correct, r.answers)} %` : '–'}</strong>
            <div class="muted">
              {r.key === 'grand_master'
                ? `${r.answers}`
                : `${Math.min(r.answers, data.rank.min_answers)}/${data.rank.min_answers}`}
              {#if !enough}<Icon name="lock" size={12} />{/if}
            </div>
          </div>
        </div>
      {/each}
      <p class="small muted">{t('rank.min', { n: data.rank.min_answers })}</p>
    </section>

    <!-- tiers -->
    <section class="card stack">
      <h3>{t('stats.tiers')}</h3>
      {#each data.tiers as tier (tier.tier)}
        {@const r = pct(tier.correct, tier.answers)}
        <div class="tier-row">
          <span class="tier-no" class:locked={!tier.unlocked}>
            {#if tier.unlocked}{tier.tier}{:else}<Icon name="lock" size={16} />{/if}
          </span>
          <div class="grow">
            <div class="row small">
              <strong>{t('tier.name', { n: tier.tier })}</strong>
              <span class="spacer"></span>
              <strong>{tier.answers ? `${r} %` : '–'}</strong>
            </div>
            <div class="bar"><i style:width={`${r}%`}></i></div>
            <div class="small muted">
              {tier.unlocked ? t('tier.passed', { p: tier.passed_count, n: tier.topic_count }) : t('tier.locked', { n: tier.tier - 1 })}
            </div>
          </div>
        </div>
      {/each}
    </section>

    <!-- per topic over time -->
    <div class="row">
      <h3 class="grow">{t('stats.topics')}</h3>
    </div>
    <div class="segmented">
      <button class:active={days === 30} onclick={() => setDays(30)}>{t('stats.days30')}</button>
      <button class:active={days === 90} onclick={() => setDays(90)}>{t('stats.days90')}</button>
      <button class:active={days === null} onclick={() => setDays(null)}>{t('stats.all')}</button>
    </div>
    <p class="small muted">{t('stats.chart_info', { pct: Math.round(PASS * 100) })}</p>

    <div class="stack" class:dim={loading}>
      {#each data.topics as topic (topic.id)}
        <section class="card topic">
          <div class="row">
            <h3 class="grow">{pick(topic.name_sk, topic.name_en)}</h3>
            {#if topic.answers}
              <span class="small muted">{t('stats.summary', { a: topic.answers, pct: pct(topic.correct, topic.answers) })}</span>
            {/if}
          </div>
          {#if topic.days.length}
            <AccuracyChart days={topic.days} threshold={PASS} />
          {:else}
            <p class="small muted empty">{t('stats.no_data')}</p>
          {/if}
        </section>
      {/each}
    </div>
  {/if}
</main>

<style>
  .grow { flex: 1; min-width: 0; }
  .right { text-align: right; }
  .right .muted { display: inline-flex; align-items: center; gap: 3px; }
  .rank-row { display: flex; align-items: center; gap: 12px; }
  .rank-ico {
    width: 36px; height: 36px; border-radius: 10px; flex: none; display: grid; place-items: center;
    background: var(--surface-2); color: var(--lock);
  }
  .earned .rank-ico { background: var(--gold-soft); color: var(--gold); }
  .rank-ico img { display: block; object-fit: contain; }
  .rank-row:not(.earned) .rank-ico img { filter: grayscale(1); opacity: .45; }
  .tier-row { display: flex; align-items: center; gap: 12px; }
  .tier-row .bar { margin: 4px 0; }
  .tier-no {
    width: 36px; height: 36px; border-radius: 10px; flex: none; display: grid; place-items: center;
    font-weight: 800; background: var(--accent-soft); color: var(--accent-strong);
  }
  .tier-no.locked { background: var(--surface-2); color: var(--lock); }
  .topic h3 { margin: 0; }
  .topic :global(.chart) { margin-top: 28px; }
  .empty { margin: 8px 0 0; }
  .dim { opacity: .5; transition: opacity .2s; }
</style>
