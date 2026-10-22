<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import MedalBadge from '../components/MedalBadge.svelte';
  import { api, ApiError } from '../lib/api';
  import { guest } from '../lib/guest';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { neededCorrect, pct as rateOf } from '../lib/util';
  import { load as loadPref, save as savePref } from '../lib/storage';
  import { LEARNING_ENABLED, QUIZ_SIZE } from '../lib/modes';
  import type { Mode, Topic } from '../lib/types';

  let { topicId }: { topicId: number } = $props();

  let topic = $state<Topic | null>(null);
  let error = $state('');
  let mode = $state<Mode>(LEARNING_ENABLED && loadPref<Mode>('quizilla.mode', 'test') === 'learn' ? 'learn' : 'test');

  function setMode(m: Mode) {
    mode = m;
    savePref('quizilla.mode', m);
  }

  const isGuest = $derived(session.guest);

  async function load() {
    error = '';
    try {
      topic = session.guest ? await guest.topic(topicId) : await api.getTopic(session.student!.id, topicId);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    }
  }
  onMount(load);

  const p = $derived(topic?.progress);
  const need = $derived(p?.unlock_window ? neededCorrect(p.unlock_window, p.unlock_accuracy) : 0);
  const pct = $derived(p ? Math.round(p.unlock_accuracy * 100) : 0);
  // success rate in % (rounded down, so 79.5 % shows as 79 – not yet enough for 80 %)
  const rate = rateOf;
  const pass = $derived(topic?.pass);
  const passPct = $derived(pass ? Math.round(pass.accuracy * 100) : 0);
  const passRate = $derived(pass ? rate(pass.correct, pass.answers) : 0);
  const cleared = $derived(topic?.levels_cleared ?? 0);
  const gm = $derived(topic?.grand_master ?? null);
  const levelCount = $derived(p?.levels.length ?? 0);
  const levelOf = (difficulty: number) => p?.levels.find((l) => l.difficulty === difficulty)?.level ?? difficulty;
</script>

<TopBar title={topic ? pick(topic.name_sk, topic.name_en) : ''} back="#/" />

<main class="page stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !topic || !p}
    <div class="spinner"></div>
  {:else if topic.tier_unlocked === false}
    <div class="card center stack">
      <Icon name="lock" size={28} />
      <p>{t('tier.locked_topic', { n: topic.tier, prev: topic.tier - 1 })}</p>
      <a class="btn secondary nolink" href="#/">{t('common.back')}</a>
    </div>
  {:else}
    {#if topic.description_sk || topic.description_en}
      <p class="muted">{pick(topic.description_sk, topic.description_en)}</p>
    {/if}
    {#if isGuest}
      <p class="small guest-note"><Icon name="user" size={14} /> {t('guest.topic_note')}</p>
    {:else}
    <section class="card medal-card">
      <MedalBadge medal={topic.medal} size={64} />
      <div class="grow">
        <h3>{t(`medal.${topic.medal ?? 'none'}`)}</h3>
        <p class="small muted">
          {t('medal.cleared', { c: Math.min(cleared, levelCount), n: levelCount })} ·
          {cleared >= levelCount ? t('medal.all') : t('medal.next', { n: cleared + 1 })}
        </p>
      </div>
    </section>

    {#if gm && cleared >= levelCount}
      {@const need = Math.round(gm.accuracy * 100)}
      <section class="card gm" class:done={gm.earned}>
        <div class="row">
          <h3 class="grow">{t('gm.title')}</h3>
          {#if gm.earned}<span class="pill ok"><Icon name="check" size={14} /> {t('gm.earned')}</span>{/if}
        </div>
        <p class="small muted">{t('gm.rule', { pct: need, min: gm.min_answers })}</p>
        {#each gm.levels as l (l.difficulty)}
          {@const r = rate(l.correct, l.answers)}
          {@const ok = l.answers >= gm.min_answers && l.correct >= l.answers * gm.accuracy}
          <div class="gm-level small">
            <span class="grow">{t('topic.level', { n: l.level })}</span>
            <span class="muted">{t('gm.answers', { a: Math.min(l.answers, gm.min_answers), min: gm.min_answers })}</span>
            <strong class:ok>{l.answers ? `${r} %` : '–'}</strong>
          </div>
        {/each}
        {#if !gm.earned}<p class="small muted">{t('gm.note')}</p>{/if}
      </section>
    {/if}

    {#if pass}
      <section class="card pass" class:done={pass.passed}>
        <div class="row">
          <h3 class="grow">{t('pass.title')}</h3>
          {#if pass.passed}<span class="pill ok"><Icon name="check" size={14} /> {t('pass.done')}</span>{/if}
        </div>
        <p class="small muted">
          {t('pass.rule', { min: pass.min_answers - 1, level: levelOf(pass.min_difficulty), pct: passPct })}
        </p>
        <div class="stats two">
          <div>
            <span class="muted small">{t('pass.answers', { level: levelOf(pass.min_difficulty) })}</span>
            <strong>{Math.min(pass.answers, pass.min_answers)}/{pass.min_answers}</strong>
            <div class="bar"><i style:width={`${Math.min(100, (pass.answers / pass.min_answers) * 100)}%`}></i></div>
          </div>
          <div>
            <span class="muted small">{t('pass.rate', { pct: passPct })}</span>
            <strong>{pass.answers ? `${passRate} %` : '–'}</strong>
            <div class="bar"><i style:width={`${Math.min(100, (passRate / Math.max(passPct, 1)) * 100)}%`}></i></div>
          </div>
        </div>
      </section>
    {/if}
    {/if}

    {#if !LEARNING_ENABLED}
      <p class="small muted play-info">
        <Icon name="play" size={14} />
        {isGuest ? t('guest.test_info', { n: QUIZ_SIZE.test }) : t('mode.test_info', { n: QUIZ_SIZE.test })}
      </p>
    {:else}
    <section class="card stack">
      <h3>{t('mode.title')}</h3>
      <div class="segmented">
        <button class:active={mode === 'learn'} onclick={() => setMode('learn')}>
          <Icon name="book" size={16} /> {t('mode.learn')}
        </button>
        <button class:active={mode === 'test'} onclick={() => setMode('test')}>
          <Icon name="target" size={16} /> {t('mode.test')}
        </button>
      </div>
      <p class="small muted">
        {mode === 'learn'
          ? t('mode.learn_info', { n: QUIZ_SIZE.learn })
          : isGuest
            ? t('guest.test_info', { n: QUIZ_SIZE.test })
            : t('mode.test_info', { n: QUIZ_SIZE.test })}
      </p>
    </section>
    {/if}

    <p class="small muted rule">
      {#if p.unlock_window}
        {t('topic.rule', { min: p.unlock_min_answers, window: p.unlock_window, need })}
      {:else}
        {t('topic.rule_all', { min: p.unlock_min_answers, pct })}
      {/if}
    </p>

    {#each p.levels as lvl (lvl.difficulty)}
      <section class="card level" class:locked={!lvl.unlocked} class:met={lvl.met}>
        <div class="row">
          <div class="badge">
            {#if !lvl.unlocked}<Icon name="lock" size={20} />
            {:else if lvl.met}<Icon name="check" size={20} />
            {:else}{lvl.level}{/if}
          </div>
          <div class="grow">
            <h3>{t('topic.level', { n: lvl.level })}</h3>
            <p class="muted small">
              {t('topic.questions', { n: lvl.question_count })}{#if !isGuest} · {t('topic.points', { n: lvl.points })}{/if}
            </p>
          </div>
          {#if lvl.unlocked}
            <a class="btn small" class:secondary={mode === 'learn'} href={`#/quiz/${topic.id}/${lvl.difficulty}/${mode}`}>
              <Icon name={mode === 'learn' ? 'book' : 'play'} size={14} /> {mode === 'learn' ? t('mode.learn') : LEARNING_ENABLED && lvl.met ? t('topic.train') : t('topic.play')}
            </a>
          {/if}
        </div>

        {#if !lvl.unlocked}
          <p class="small muted lockmsg">{t('topic.locked', { n: lvl.level - 1 })}</p>
        {:else}
          <div class="stats two">
            <div>
              <span class="muted small">{t('topic.answered')}</span>
              <strong>{Math.min(lvl.total_answers, p.unlock_min_answers)}/{p.unlock_min_answers}</strong>
              <div class="bar"><i style:width={`${Math.min(100, (lvl.total_answers / p.unlock_min_answers) * 100)}%`}></i></div>
            </div>
            {#if p.unlock_window}
              <div>
                <span class="muted small">{t('topic.recent', { window: p.unlock_window })}</span>
                <strong>{lvl.recent_correct}/{need}</strong>
                <div class="bar"><i style:width={`${Math.min(100, (lvl.recent_correct / Math.max(need, 1)) * 100)}%`}></i></div>
              </div>
            {:else}
              {@const r = rate(lvl.recent_correct, lvl.recent_total)}
              <div>
                <span class="muted small">{t('topic.rate', { pct })}</span>
                <strong>{lvl.recent_total ? `${r} %` : '–'}</strong>
                <div class="bar"><i style:width={`${Math.min(100, (r / Math.max(pct, 1)) * 100)}%`}></i></div>
              </div>
            {/if}
          </div>
        {/if}
      </section>
    {/each}
  {/if}
</main>

<style>
  .medal-card { display: flex; align-items: center; gap: 14px; }
  .medal-card h3 { margin: 0; }
  .medal-card p { margin: 4px 0 0; }
  .gm { display: flex; flex-direction: column; gap: 8px; }
  .gm h3, .gm p { margin: 0; }
  .gm.done { border-color: var(--gold); }
  .gm-level { display: flex; align-items: center; gap: 10px; }
  .gm-level strong { min-width: 3.5em; text-align: right; }
  .gm-level strong.ok { color: var(--ok); }
  .rule { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
  .play-info { display: flex; align-items: center; gap: 6px; margin: 0; }
  .guest-note {
    display: flex; align-items: center; gap: 6px; margin: 0;
    background: var(--info-soft); color: var(--info); border-radius: 12px; padding: 10px 12px;
  }
  .level h3 { margin: 0; }
  .level p { margin: 2px 0 0; }
  .level.locked { opacity: .7; box-shadow: none; }
  .badge {
    width: 40px; height: 40px; border-radius: 12px; flex: none;
    display: grid; place-items: center; font-weight: 800;
    background: var(--accent-soft); color: var(--accent-strong);
  }
  .locked .badge { background: var(--surface-2); color: var(--lock); }
  .met .badge { background: var(--accent); color: var(--on-accent); }
  .grow { flex: 1; min-width: 0; }
  .lockmsg { margin-top: 10px !important; }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
  .stats > div { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
  .stats span { line-height: 1.2; min-height: 2.4em; }
  .stats strong { font-size: 1.05rem; }
  .btn.small, .nolink { text-decoration: none; }
  .pass h3 { margin: 0; }
  .pass p { margin: 6px 0 0; }
  .pass.done { border-color: var(--ok); }
  .stats.two { grid-template-columns: repeat(2, 1fr); }
  .segmented button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; }
</style>
