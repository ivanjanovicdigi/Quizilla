<script lang="ts">
  import { onMount } from 'svelte';
  import TopBar from '../components/TopBar.svelte';
  import Icon from '../components/Icon.svelte';
  import Rich from '../components/Rich.svelte';
  import { api, ApiError } from '../lib/api';
  import { session, setStudent } from '../lib/session.svelte';
  import { errorText, pick, t } from '../lib/i18n.svelte';
  import { shuffledIndices } from '../lib/util';
  import type { AnswerResult, Progress, Question, Topic } from '../lib/types';

  let { topicId, difficulty }: { topicId: number; difficulty: number } = $props();

  const LETTERS = ['A', 'B', 'C', 'D'];

  let topic = $state<Topic | null>(null);
  let questions = $state<Question[]>([]);
  let orders = $state<number[][]>([]); // display order of answers per question
  let index = $state(0);
  let chosen = $state<number | null>(null); // original answer index
  let result = $state<AnswerResult | null>(null);
  let busy = $state(false);
  let loading = $state(true);
  let error = $state('');
  let finished = $state(false);

  let correctCount = $state(0);
  let pointsEarned = $state(0);
  let unlockedLevels = $state<number[]>([]);
  let progress = $state<Progress | null>(null);

  const studentId = () => session.student!.id;

  function handleError(e: unknown) {
    const code = e instanceof ApiError ? e.code : 'server';
    if (code === 'unknown_student') setStudent(null);
    error = errorText(code);
  }

  async function start() {
    loading = true;
    error = '';
    finished = false;
    index = 0;
    chosen = null;
    result = null;
    correctCount = 0;
    pointsEarned = 0;
    unlockedLevels = [];
    try {
      const [tp, qs] = await Promise.all([
        topic ? Promise.resolve(topic) : api.getTopic(studentId(), topicId),
        api.getQuestions(studentId(), topicId, difficulty, 10)
      ]);
      topic = tp;
      progress = tp.progress;
      questions = qs;
      orders = qs.map((q) => shuffledIndices(q.answers.length));
    } catch (e) {
      handleError(e);
    } finally {
      loading = false;
    }
  }
  onMount(start);

  const current = $derived(questions[index]);
  const levelNo = $derived(progress?.levels.find((l) => l.difficulty === difficulty)?.level ?? 1);
  const nextLevel = $derived.by(() => {
    if (!progress) return null;
    const i = progress.levels.findIndex((l) => l.difficulty === difficulty);
    const n = progress.levels[i + 1];
    return n && n.unlocked ? n : null;
  });

  async function answer(original: number) {
    if (busy || result || !current) return;
    chosen = original;
    busy = true;
    try {
      const r = await api.submitAnswer(studentId(), current.id, original);
      result = r;
      progress = r.progress;
      if (r.correct) correctCount++;
      pointsEarned += r.points;
      if (r.newly_unlocked.length) unlockedLevels = [...unlockedLevels, ...r.newly_unlocked];
      navigator.vibrate?.(r.correct ? 15 : [30, 40, 30]);
    } catch (e) {
      chosen = null;
      handleError(e);
    } finally {
      busy = false;
    }
  }

  function next() {
    if (index + 1 >= questions.length) {
      finished = true;
    } else {
      index++;
      chosen = null;
      result = null;
      error = '';
    }
    window.scrollTo({ top: 0 });
  }

  function stateOf(original: number): string {
    if (!result) return chosen === original ? 'pending' : '';
    if (original === result.correct_index) return 'right';
    if (original === chosen) return 'wrong';
    return 'dim';
  }
</script>

<TopBar
  title={topic ? `${pick(topic.name_sk, topic.name_en)} · ${t('topic.level', { n: levelNo })}` : ''}
  back={`#/topic/${topicId}`} />

<main class="page stack quiz">
  {#if loading}
    <div class="spinner"></div>
  {:else if error && !current}
    <div class="error">{error}</div>
    <a class="btn secondary" href={`#/topic/${topicId}`}>{t('quiz.back')}</a>
  {:else if questions.length === 0}
    <p class="muted center">{t('quiz.empty')}</p>
    <a class="btn secondary" href={`#/topic/${topicId}`}>{t('quiz.back')}</a>
  {:else if finished}
    <section class="card center summary stack">
      <h2>{t('quiz.summary')}</h2>
      <div class="big">{correctCount}<span class="muted">/{questions.length}</span></div>
      <p class="muted">{t('quiz.score', { c: correctCount, n: questions.length })}</p>
      <p class="gold"><Icon name="star" size={18} /> {t('quiz.earned', { n: pointsEarned })}</p>
      {#each unlockedLevels as n (n)}
        <div class="unlock"><Icon name="unlock" /> {t('quiz.unlocked', { n })}</div>
      {/each}
    </section>
    <div class="stack">
      {#if nextLevel}
        <a class="btn block" href={`#/quiz/${topicId}/${nextLevel.difficulty}`}>
          {t('quiz.next_level', { n: nextLevel.level })}
        </a>
      {/if}
      <button class="btn block" class:secondary={!!nextLevel} onclick={start}>{t('quiz.again')}</button>
      <a class="btn block ghost" href={`#/topic/${topicId}`}>{t('quiz.back')}</a>
    </div>
  {:else if current}
    <div class="row progress">
      <span class="small muted">{t('quiz.of', { i: index + 1, n: questions.length })}</span>
      <div class="bar grow"><i style:width={`${((index + (result ? 1 : 0)) / questions.length) * 100}%`}></i></div>
      <span class="small gold"><Icon name="star" size={14} /> {pointsEarned}</span>
    </div>

    <section class="card question">
      <Rich text={pick(current.body, current.body_en)} />
    </section>

    <div class="answers">
      {#each orders[index] as original, pos (original)}
        <button
          class="answer {stateOf(original)}"
          disabled={busy || !!result}
          onclick={() => answer(original)}>
          <span class="letter">
            {#if stateOf(original) === 'right'}<Icon name="check" size={16} />
            {:else if stateOf(original) === 'wrong'}<Icon name="x" size={16} />
            {:else}{LETTERS[pos]}{/if}
          </span>
          <span class="text"><Rich text={pick(current.answers[original], current.answers_en?.[original])} short /></span>
        </button>
      {/each}
    </div>

    {#if error}<div class="error">{error}</div>{/if}

    {#if result}
      <section class="feedback card" class:ok={result.correct} class:bad={!result.correct}>
        <div class="row">
          <strong>{result.correct ? t('quiz.correct') : t('quiz.wrong')}</strong>
          <span class="spacer"></span>
          {#if result.correct}
            <span class="small">{result.points > 0 ? t('quiz.points', { n: result.points }) : t('quiz.no_points')}</span>
          {/if}
        </div>
        {#if result.explanation || result.explanation_en}
          <div class="small expl"><Rich text={pick(result.explanation, result.explanation_en)} short /></div>
        {/if}
        {#each result.newly_unlocked as n (n)}
          <div class="unlock"><Icon name="unlock" /> {t('quiz.unlocked', { n })}</div>
        {/each}
      </section>
      <div class="next-bar">
        <button class="btn block" onclick={next}>
          {index + 1 >= questions.length ? t('quiz.finish') : t('quiz.next')}
        </button>
      </div>
    {/if}
  {/if}
</main>

<style>
  .quiz { padding-bottom: calc(100px + env(safe-area-inset-bottom)); }
  .progress { gap: 10px; }
  .grow { flex: 1; }
  .gold { color: var(--gold); display: inline-flex; align-items: center; gap: 4px; font-weight: 700; }
  .question { font-size: 1.05rem; }

  .answers { display: grid; gap: 10px; }
  .answer {
    display: flex; align-items: center; gap: 12px; text-align: left;
    min-height: 56px; padding: 10px 14px; width: 100%;
    background: var(--surface); border: 2px solid var(--border); border-radius: 14px;
    cursor: pointer; transition: border-color .12s ease, background .12s ease, transform .08s ease;
    overflow: hidden;
  }
  .answer:not(:disabled):active { transform: scale(.985); }
  .answer:disabled { cursor: default; color: inherit; }
  .answer .letter {
    flex: none; width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
    background: var(--surface-2); font-weight: 800; font-size: .85rem; color: var(--muted);
  }
  .answer .text { flex: 1; min-width: 0; overflow-x: auto; }
  .answer.pending { border-color: var(--accent); }
  .answer.right { border-color: var(--ok); background: var(--ok-soft); }
  .answer.right .letter { background: var(--ok); color: #fff; }
  .answer.wrong { border-color: var(--bad); background: var(--bad-soft); }
  .answer.wrong .letter { background: var(--bad); color: #fff; }
  .answer.dim { opacity: .55; }

  .feedback.ok { border-color: var(--ok); }
  .feedback.bad { border-color: var(--bad); }
  .feedback.ok strong { color: var(--ok); }
  .feedback.bad strong { color: var(--bad); }
  .expl { margin-top: 8px; }

  .unlock {
    margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 10px; border-radius: 12px; background: var(--gold-soft); color: var(--gold); font-weight: 700;
    animation: pop .35s ease;
  }
  @keyframes pop { from { transform: scale(.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }

  .next-bar {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 5;
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
    background: linear-gradient(to top, var(--bg) 70%, transparent);
  }
  .next-bar .btn { max-width: 608px; margin: 0 auto; display: flex; }

  .summary .big { font-size: 3rem; font-weight: 800; line-height: 1; }
  .summary .big span { font-size: 1.5rem; }
  a.btn { text-decoration: none; }
</style>
