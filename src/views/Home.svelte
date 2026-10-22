<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import MedalBadge from '../components/MedalBadge.svelte';
  import RankBadge from '../components/RankBadge.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { pct } from '../lib/util';
  import type { Catalog, TierState, Topic } from '../lib/types';

  let data = $state<Catalog | null>(null);
  let error = $state('');

  async function load() {
    error = '';
    try {
      data = await api.getCatalog(session.student!.id);
      setStudent(data.student);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    }
  }
  onMount(load);

  function summary(topic: Topic) {
    const levels = topic.progress.levels;
    const current = levels.filter((l) => l.unlocked).length;
    const met = levels.filter((l) => l.met).length;
    return { current, total: levels.length, pct: levels.length ? (met / levels.length) * 100 : 0 };
  }

  function tierOf(n: number): TierState | undefined {
    return data?.tiers.find((x) => x.tier === n);
  }

  /** Topics of a subject grouped by tier, in tier order. */
  function groups(topics: Topic[] | null) {
    const map = new Map<number, Topic[]>();
    for (const tp of topics ?? []) {
      if (!map.has(tp.tier)) map.set(tp.tier, []);
      map.get(tp.tier)!.push(tp);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }
</script>

<TopBar title="Quizilla" />

<main class="page stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !data}
    <div class="spinner"></div>
  {:else}
    <section class="card hello">
      <div>
        <h2>{t('home.hello', { name: data.student.name.split(' ')[0] })}</h2>
        <p class="muted small">{t('home.class', { name: data.student.class_name })}</p>
        <a class="rank-link" href="#/stats"><RankBadge rank={data.rank.current} /></a>
      </div>
      <div class="score">
        <Icon name="star" size={20} />
        <strong>{data.points}</strong>
        <span class="muted small">{t('home.points')}</span>
      </div>
    </section>

    {#if data.subjects.length === 0}
      <p class="muted center">{t('home.empty')}</p>
    {/if}

    {#each data.subjects as subject (subject.id)}
      <section class="stack">
        <h2 class="subject">{pick(subject.name_sk, subject.name_en)}</h2>

        {#each groups(subject.topics) as [tierNo, topics] (tierNo)}
          {@const tier = tierOf(tierNo)}
          {@const locked = !tier?.unlocked}
          <section class="tier" class:locked>
            <div class="tier-head">
              <div class="grow">
                <h3>{t('tier.name', { n: tierNo })}</h3>
                {#if locked}
                  <p class="small muted"><Icon name="lock" size={14} /> {t('tier.locked', { n: tierNo - 1 })}</p>
                {:else if tier}
                  <p class="small muted">{t('tier.passed', { p: tier.passed_count, n: tier.topic_count })}</p>
                {/if}
              </div>
              {#if tier && !locked}
                <div class="acc">
                  <strong>{tier.answers ? `${pct(tier.correct, tier.answers)} %` : '–'}</strong>
                  <span class="muted small">{t('tier.accuracy')}</span>
                </div>
              {/if}
            </div>

            {#each topics as topic (topic.id)}
              {@const s = summary(topic)}
              <a class="card tappable topic" class:disabled={locked} href={locked ? undefined : `#/topic/${topic.id}`}>
                <div class="row">
                  <MedalBadge medal={locked ? null : topic.medal} size={44} />
                  <div class="grow">
                    <h3>{pick(topic.name_sk, topic.name_en)}</h3>
                    {#if topic.description_sk || topic.description_en}
                      <p class="muted small desc">{pick(topic.description_sk, topic.description_en)}</p>
                    {/if}
                  </div>
                  <span class="chev"><Icon name={locked ? 'lock' : 'chevron'} size={18} /></span>
                </div>
                {#if !locked}
                  <div class="bar"><i style:width={`${s.pct}%`}></i></div>
                  <div class="row small meta">
                    {#if topic.pass.passed}
                      <span class="pill ok"><Icon name="check" size={14} /> {t('pass.done')}</span>
                    {:else}
                      <span class="pill">{t('home.levels', { current: s.current, total: s.total })}</span>
                    {/if}
                    <span class="spacer"></span>
                    <span class="muted">{t('topic.points', { n: topic.progress.points })}</span>
                  </div>
                {/if}
              </a>
            {/each}
          </section>
        {/each}
      </section>
    {/each}
  {/if}
</main>

<style>
  .hello { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .hello p { margin: 2px 0 6px; }
  .rank-link { text-decoration: none; }
  .score { display: flex; align-items: center; gap: 6px; color: var(--gold); font-size: 1.25rem; }
  .score span { color: var(--muted); }
  .subject { margin-top: 20px; font-size: .85rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
  .tier { display: flex; flex-direction: column; gap: 10px; margin-top: 18px; }
  .tier-head { display: flex; align-items: center; gap: 12px; }
  .tier-head p { margin: 2px 0 0; display: flex; align-items: center; gap: 4px; }
  .acc { display: flex; flex-direction: column; align-items: flex-end; }
  .acc strong { font-size: 1.25rem; line-height: 1.1; }
  .topic { text-decoration: none; color: inherit; }
  .topic.disabled { cursor: default; opacity: .6; box-shadow: none; }
  .topic.disabled:active { transform: none; }
  .topic .desc { margin: 2px 0 0; }
  .topic .row { gap: 12px; }
  .topic .bar { margin: 12px 0 10px; }
  .grow { flex: 1; min-width: 0; }
  .chev { color: var(--muted); }
  .meta { gap: 8px; }
</style>
