<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { neededCorrect } from '../lib/util';
  import type { Topic } from '../lib/types';

  let { topicId }: { topicId: number } = $props();

  let topic = $state<Topic | null>(null);
  let error = $state('');

  async function load() {
    error = '';
    try {
      topic = await api.getTopic(session.student!.id, topicId);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'unknown_student') setStudent(null);
      error = errorText(code);
    }
  }
  onMount(load);

  const p = $derived(topic?.progress);
  const need = $derived(p ? neededCorrect(p.unlock_window, p.unlock_accuracy) : 0);
</script>

<TopBar title={topic ? pick(topic.name_sk, topic.name_en) : ''} back="#/" />

<main class="page stack">
  {#if error}
    <div class="error">{error}</div>
    <button class="btn secondary" onclick={load}>{t('common.retry')}</button>
  {:else if !topic || !p}
    <div class="spinner"></div>
  {:else}
    {#if topic.description_sk || topic.description_en}
      <p class="muted">{pick(topic.description_sk, topic.description_en)}</p>
    {/if}
    <p class="small muted rule">
      {t('topic.rule', { min: p.unlock_min_answers, window: p.unlock_window, need })}
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
              {t('topic.questions', { n: lvl.question_count })} · {t('topic.points', { n: lvl.points })}
            </p>
          </div>
          {#if lvl.unlocked}
            <a class="btn small" href={`#/quiz/${topic.id}/${lvl.difficulty}`}>
              <Icon name="play" size={14} /> {lvl.met ? t('topic.train') : t('topic.play')}
            </a>
          {/if}
        </div>

        {#if !lvl.unlocked}
          <p class="small muted lockmsg">{t('topic.locked', { n: lvl.level - 1 })}</p>
        {:else}
          <div class="stats">
            <div>
              <span class="muted small">{t('topic.answered')}</span>
              <strong>{Math.min(lvl.total_answers, p.unlock_min_answers)}/{p.unlock_min_answers}</strong>
              <div class="bar"><i style:width={`${Math.min(100, (lvl.total_answers / p.unlock_min_answers) * 100)}%`}></i></div>
            </div>
            <div>
              <span class="muted small">{t('topic.recent', { window: p.unlock_window })}</span>
              <strong>{lvl.recent_correct}/{need}</strong>
              <div class="bar"><i style:width={`${Math.min(100, (lvl.recent_correct / Math.max(need, 1)) * 100)}%`}></i></div>
            </div>
            <div>
              <span class="muted small">{t('topic.mastered')}</span>
              <strong>{lvl.mastered}/{lvl.question_count}</strong>
              <div class="bar"><i style:width={`${(lvl.mastered / Math.max(lvl.question_count, 1)) * 100}%`}></i></div>
            </div>
          </div>
        {/if}
      </section>
    {/each}
  {/if}
</main>

<style>
  .rule { background: var(--surface-2); border-radius: 12px; padding: 10px 12px; }
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
  .btn.small { text-decoration: none; }
</style>
