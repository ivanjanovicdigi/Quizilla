<script lang="ts">
  import { onMount } from 'svelte';
  // Personal statistics (ranks, tiers, per-topic points / accuracy / unlocks / trend).
  // Used by the Statistics page (Profile), the "Mine" tab of the Leaderboard and the admin
  // student detail (with `source`: loads another student's stats; null = no stats yet).
  import Icon from './Icon.svelte';
  import RankBadge, { rankImage } from './RankBadge.svelte';
  import TrendChart from './TrendChart.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { pct, signed } from '../lib/util';
  import type { Progress, Stats } from '../lib/types';

  let { source, onError }: {
    source?: () => Promise<Stats | null>;
    /** Called with the error code when `source` fails (e.g. admin session expired). */
    onError?: (code: string) => void;
  } = $props();

  let data = $state<Stats | null>(null);
  let empty = $state(false); // source returned null (never logged in)
  let error = $state('');

  async function load() {
    error = '';
    try {
      if (source) {
        const r = await source();
        empty = r === null;
        data = r;
      } else {
        data = await api.getStats(session.student!.id, null); // all time
      }
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (source) onError?.(code);
      else if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    }
  }

  onMount(load);

  /** Current level (highest unlocked) and progress toward unlocking the next one. */
  function unlockInfo(p: Progress) {
    const levels = p.levels;
    let i = 0;
    levels.forEach((l, k) => { if (l.unlocked) i = k; });
    const cur = levels[i];
    const next = levels[i + 1] ?? null;
    const min = p.unlock_min_answers;
    const need = Math.round(p.unlock_accuracy * 100);
    return {
      level: cur?.level ?? 1,
      count: levels.length,
      next,
      answers: cur?.total_answers ?? 0,
      min,
      acc: pct(cur?.recent_correct ?? 0, cur?.recent_total ?? 0),
      need,
      answersPct: Math.min(100, ((cur?.total_answers ?? 0) / Math.max(min, 1)) * 100)
    };
  }

  // Admin view (`source` set): neutral wording instead of "my / your".
  const admin = $derived(!!source);

  const unlockAcc = $derived(data?.topics.find((x) => x.progress)?.progress?.unlock_accuracy ?? 0.8);
</script>

<div class="stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if empty}
    <p class="muted center">{t('stats.never_logged_in')}</p>
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
      <p class="small muted">{t(admin ? 'rank.min_admin' : 'rank.min', { n: data.rank.min_answers })}</p>
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
              {tier.unlocked ? t('tier.passed', { p: tier.passed_count, n: tier.topic_count }) : t(admin ? 'tier.locked_admin' : 'tier.locked', { n: tier.tier - 1 })}
            </div>
          </div>
        </div>
      {/each}
    </section>

    <!-- per topic: points, accuracy, unlock progress, running-accuracy trend -->
    <h3>{t(admin ? 'stats.topics_admin' : 'stats.topics')}</h3>
    <p class="small muted">{t(admin ? 'stats.trend_info_admin' : 'stats.trend_info', { pct: Math.round(unlockAcc * 100) })}</p>

    <div class="stack">
      {#each data.topics as topic (topic.id)}
        {@const pts = topic.points ?? null}
        <section class="card topic stack">
          <h3>{pick(topic.name_sk, topic.name_en)}</h3>

          <div class="kpis">
            <div>
              <!-- "–" if the server sends no points (old get_stats) instead of a misleading 0 -->
              <strong class:plus={pts !== null && pts > 0} class:minus={pts !== null && pts < 0}>{pts === null ? '–' : signed(pts)}</strong>
              <span class="small muted">{t('stats.points')}</span>
            </div>
            <div>
              <strong>{topic.answers ? `${pct(topic.correct, topic.answers)} %` : '–'}</strong>
              <span class="small muted">{t('stats.rate')}</span>
            </div>
            <div>
              <strong>{topic.answers}</strong>
              <span class="small muted">{t('stats.answers')}</span>
            </div>
          </div>

          {#if topic.tier_unlocked === false}
            <p class="small muted lock"><Icon name="lock" size={14} /> {t('stats.tier_locked', { n: topic.tier })}</p>
          {:else if topic.progress && topic.progress.levels.length}
            {@const u = unlockInfo(topic.progress)}
            <div class="unlock-box small">
              <div class="row">
                <strong>{t('stats.level_of', { n: u.level, m: u.count })}</strong>
                <span class="spacer"></span>
                {#if u.next}
                  <span class="muted">{t('stats.next_unlock', { n: u.next.level })}</span>
                {:else}
                  <span class="done"><Icon name="check" size={14} /> {t('stats.all_unlocked')}</span>
                {/if}
              </div>
              {#if u.next}
                <div class="need">
                  <span>{t('stats.need_answers', { a: Math.min(u.answers, u.min), min: u.min })}</span>
                  <div class="bar" class:ok={u.answers >= u.min}><i style:width={`${u.answersPct}%`}></i></div>
                </div>
                <div class="need">
                  <span>{t('stats.need_acc', { pct: u.answers ? u.acc : 0, need: u.need })}</span>
                  <div class="bar acc" class:ok={u.answers > 0 && u.acc >= u.need}>
                    <i style:width={`${u.answers ? u.acc : 0}%`}></i>
                    <b style:left={`${u.need}%`}></b>
                  </div>
                </div>
              {/if}
            </div>
          {/if}

          {#if topic.trend?.length}
            <TrendChart trend={topic.trend} threshold={topic.progress?.unlock_accuracy ?? unlockAcc} />
          {:else}
            <p class="small muted empty">{t('stats.no_data')}</p>
          {/if}
        </section>
      {/each}
    </div>
  {/if}
</div>

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
  .empty { margin: 0; }
  .kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; }
  .kpis div { display: flex; flex-direction: column; padding: 8px 4px; border-radius: 12px; background: var(--surface-2); }
  .kpis strong { font-size: 1.15rem; }
  .kpis .plus { color: var(--ok); }
  .kpis .minus { color: var(--bad); }
  .lock { display: flex; align-items: center; gap: 6px; margin: 0; }
  .unlock-box { display: flex; flex-direction: column; gap: 8px; }
  .done { color: var(--ok); display: inline-flex; align-items: center; gap: 4px; font-weight: 700; }
  .need { display: flex; flex-direction: column; gap: 3px; }
  .need .bar.ok i { background: var(--ok); }
  .bar.acc { position: relative; }
  .bar.acc b { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--text); opacity: .55; }
</style>
