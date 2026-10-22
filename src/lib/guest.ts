// Guest mode: try the app without the roster. Nothing is saved anywhere – the server
// records nothing (016_guest_mode.sql) and this state lives in memory only (no localStorage),
// so a reload or a new visit starts from zero.
// Levels unlock with the same rule as for students (topic unlock_min_answers / unlock_window /
// unlock_accuracy), counting the guest's testing answers of this visit. Tiers are all open.
import { api, ApiError } from './api';
import type { AnswerResult, GuestSubject, GuestTopic, Level, Progress, Question, Subject, TierState, Topic } from './types';

interface LevelLog {
  results: boolean[]; // testing answers in order (true = correct)
  correctIds: Set<number>;
}

let catalog: GuestSubject[] | null = null;
const logs = new Map<string, LevelLog>();
const unlocked = new Set<string>(); // sticky unlocks, like quiz.unlocks

const key = (topicId: number, difficulty: number) => `${topicId}:${difficulty}`;

/** Forget everything (entering or leaving guest mode). */
export function resetGuest() {
  catalog = null;
  logs.clear();
  unlocked.clear();
}

async function loadCatalog(): Promise<GuestSubject[]> {
  if (!catalog) catalog = await api.guestCatalog();
  return catalog;
}

async function findTopic(topicId: number): Promise<GuestTopic> {
  for (const s of await loadCatalog()) {
    const t = s.topics?.find((x) => x.id === topicId);
    if (t) return t;
  }
  throw new ApiError('unknown_topic');
}

function progressOf(t: GuestTopic): Progress {
  let first = true;
  let prevUnlocked = true;
  let prevMet = true;
  const levels: Level[] = t.levels.map((l) => {
    const k = key(t.id, l.difficulty);
    const log = logs.get(k);
    const results = log?.results ?? [];
    const recent = t.unlock_window ? results.slice(-t.unlock_window) : results;
    const recentOk = recent.filter(Boolean).length;
    const isUnlocked = first || (prevUnlocked && prevMet) || unlocked.has(k);
    if (isUnlocked) unlocked.add(k);
    const met =
      results.length >= t.unlock_min_answers &&
      recent.length > 0 &&
      recentOk >= recent.length * t.unlock_accuracy - 1e-9;
    prevUnlocked = isUnlocked;
    prevMet = met;
    first = false;
    return {
      level: l.level,
      difficulty: l.difficulty,
      question_count: l.question_count,
      unlocked: isUnlocked,
      met,
      total_answers: results.length,
      recent_total: recent.length,
      recent_correct: recentOk,
      mastered: log?.correctIds.size ?? 0,
      points: 0
    };
  });
  return {
    topic_id: t.id,
    unlock_min_answers: t.unlock_min_answers,
    unlock_window: t.unlock_window,
    unlock_accuracy: t.unlock_accuracy,
    completed: levels.length > 0 && prevMet,
    points: 0,
    levels
  };
}

function toTopic(t: GuestTopic): Topic {
  return {
    id: t.id,
    slug: t.slug,
    subject_id: t.subject_id,
    tier: t.tier,
    tier_unlocked: true,
    pass: { min_answers: 0, min_difficulty: 0, accuracy: 0, answers: 0, correct: 0, passed: false },
    medal: null,
    levels_cleared: 0,
    name_sk: t.name_sk,
    name_en: t.name_en,
    description_sk: t.description_sk,
    description_en: t.description_en,
    question_count: t.question_count,
    progress: progressOf(t)
  };
}

export const guest = {
  /** Subjects with topics (progress of this visit) and tiers (all open). */
  async catalog(): Promise<{ subjects: Subject[]; tiers: TierState[] }> {
    const subjects = (await loadCatalog()).map((s) => ({
      id: s.id,
      slug: s.slug,
      name_sk: s.name_sk,
      name_en: s.name_en,
      topics: (s.topics ?? []).map(toTopic)
    }));
    const tierNos = [...new Set(subjects.flatMap((s) => s.topics.map((t) => t.tier)))].sort((a, b) => a - b);
    const tiers = tierNos.map((n) => ({ tier: n, unlocked: true, topic_count: 0, passed_count: 0, answers: 0, correct: 0 }));
    return { subjects, tiers };
  },

  async topic(topicId: number): Promise<Topic> {
    return toTopic(await findTopic(topicId));
  },

  async questions(topicId: number, difficulty: number, limit: number): Promise<Question[]> {
    const t = await findTopic(topicId);
    const lvl = progressOf(t).levels.find((l) => l.difficulty === difficulty);
    if (!lvl) throw new ApiError('unknown_level');
    if (!lvl.unlocked) throw new ApiError('level_locked');
    const seen = [...(logs.get(key(topicId, difficulty))?.correctIds ?? [])];
    return api.guestQuestions(topicId, difficulty, limit, seen);
  },

  /** Checks the answer on the server (nothing recorded there). Testing answers count
   *  toward unlocking levels during this visit; learning answers count for nothing. */
  async answer(topicId: number, question: Question, chosen: number, counts: boolean): Promise<AnswerResult> {
    const t = await findTopic(topicId);
    const before = progressOf(t);
    const r = await api.guestCheck(question.id, chosen);
    if (counts) {
      const k = key(topicId, question.difficulty);
      const log = logs.get(k) ?? { results: [], correctIds: new Set<number>() };
      log.results.push(r.correct);
      if (r.correct) log.correctIds.add(question.id);
      logs.set(k, log);
    }
    const after = progressOf(t);
    const newly = after.levels
      .filter((l) => l.unlocked && !before.levels.find((b) => b.difficulty === l.difficulty)?.unlocked)
      .map((l) => l.level);
    return { ...r, points: 0, newly_unlocked: newly, newly_passed: false, progress: after };
  }
};
