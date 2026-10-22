import type {
  AnswerResult, Catalog, ClassInfo, ClassRow, GuestCheck, GuestSubject, Question, Stats, Student, Topic
} from './types';

const BASE = ((import.meta.env.VITE_SUPABASE_URL as string | undefined) ?? '').replace(/\/+$/, '');
const KEY = (import.meta.env.VITE_SUPABASE_KEY as string | undefined) ?? '';

export class ApiError extends Error {
  constructor(public code: string) {
    super(code);
  }
}

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (KEY) {
    h.apikey = KEY;
    // Legacy anon keys are JWTs and may also go in Authorization; new sb_publishable_ keys must not.
    if (!KEY.startsWith('sb_')) h.Authorization = `Bearer ${KEY}`;
  }
  return h;
}

/** "Report a bug" → Supabase Edge Function report-bug → GitHub issue. Returns the issue number. */
export async function reportBug(payload: Record<string, unknown>): Promise<number> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/functions/v1/report-bug`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(payload)
    });
  } catch {
    throw new ApiError('network');
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(typeof body?.error === 'string' ? body.error : 'server');
  return body.number as number;
}

async function rpc<T>(fn: string, args: Record<string, unknown> = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/rest/v1/rpc/${fn}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(args)
    });
  } catch {
    throw new ApiError('network');
  }
  if (!res.ok) {
    let code = 'server';
    try {
      const body = await res.json();
      if (body?.code === 'P0001' && typeof body.message === 'string') code = body.message;
    } catch {
      /* ignore */
    }
    throw new ApiError(code);
  }
  return (await res.json()) as T;
}

export const api = {
  listClasses: () => rpc<ClassInfo[]>('list_classes'),
  /** Login with the school email only – the student must be in the roster (quiz.roster). */
  login: (email: string) => rpc<Student>('login_student', { p_email: email }),
  getStudent: (id: string) => rpc<Student | null>('get_student', { p_student_id: id }),
  getCatalog: (id: string) => rpc<Catalog>('get_catalog', { p_student_id: id }),
  getTopic: (id: string, topicId: number) =>
    rpc<Topic>('get_topic', { p_student_id: id, p_topic_id: topicId }),
  getQuestions: (id: string, topicId: number, difficulty: number, limit = 10) =>
    rpc<Question[]>('get_questions', {
      p_student_id: id, p_topic_id: topicId, p_difficulty: difficulty, p_limit: limit
    }),
  submitAnswer: (id: string, questionId: number, chosen: number) =>
    rpc<AnswerResult>('submit_answer', { p_student_id: id, p_question_id: questionId, p_chosen: chosen }),
  /** Learning mode – checks the answer, nothing is recorded. */
  checkAnswer: (id: string, questionId: number, chosen: number) =>
    rpc<AnswerResult>('check_answer', { p_student_id: id, p_question_id: questionId, p_chosen: chosen }),
  getStats: (id: string, days: number | null) => rpc<Stats>('get_stats', { p_student_id: id, p_days: days }),
  // Guest mode (016_guest_mode.sql) – no student, nothing is recorded on the server.
  guestCatalog: () => rpc<GuestSubject[]>('get_guest_catalog'),
  guestQuestions: (topicId: number, difficulty: number, limit: number, seen: number[]) =>
    rpc<Question[]>('get_guest_questions', {
      p_topic_id: topicId, p_difficulty: difficulty, p_limit: limit, p_seen: seen
    }),
  guestCheck: (questionId: number, chosen: number) =>
    rpc<GuestCheck>('check_guest_answer', { p_question_id: questionId, p_chosen: chosen }),
  /** Class totals (all time), visible to everyone. */
  classLeaderboard: () => rpc<ClassRow[]>('get_class_leaderboard')
};

export const emailDomain = (import.meta.env.VITE_EMAIL_DOMAIN as string | undefined) || 'lyceum.sk';
