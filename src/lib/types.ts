export interface Student {
  id: string;
  email: string;
  name: string;
  class_id: number;
  class_name: string;
}

export interface Level {
  level: number;
  difficulty: number;
  question_count: number;
  unlocked: boolean;
  met: boolean;
  total_answers: number;
  recent_total: number;
  recent_correct: number;
  mastered: number;
  points: number;
}

export interface Progress {
  topic_id: number;
  unlock_min_answers: number;
  unlock_window: number | null; // null = all answers on the level
  unlock_accuracy: number;
  completed: boolean;
  points: number;
  levels: Level[];
}

export interface Pass {
  min_answers: number;
  min_difficulty: number;
  accuracy: number;
  answers: number; // testing answers on min_difficulty or harder
  correct: number;
  passed: boolean;
}

export type MedalKey = 'bronze' | 'silver' | 'gold' | 'grand_master';

/** Topic Grand Master (018_topic_grand_master.sql): gold + accuracy on every level, not sticky. */
export interface TopicGrandMaster {
  min_answers: number;
  accuracy: number; // 0–1
  earned: boolean;
  levels: { level: number; difficulty: number; answers: number; correct: number }[];
}

export interface Topic {
  id: number;
  slug: string;
  subject_id: number;
  tier: number;
  tier_unlocked?: boolean; // only from get_topic
  pass: Pass;
  medal?: MedalKey | null; // from 012_topic_medals.sql
  levels_cleared?: number;
  /** Rule for clearing a level (medals), 025. Separate from the unlock rule. */
  medal_rule?: { min_answers: number; accuracy: number } | null;
  grand_master?: TopicGrandMaster | null;
  name_sk: string;
  name_en: string | null;
  description_sk: string | null;
  description_en: string | null;
  question_count: number;
  progress: Progress;
}

export interface Subject {
  id: number;
  slug: string;
  name_sk: string;
  name_en: string | null;
  topics: Topic[];
}

export interface TierState {
  tier: number;
  unlocked: boolean;
  topic_count: number;
  passed_count: number;
  answers: number;
  correct: number;
}

export type RankKey = 'padawan' | 'jedi' | 'master' | 'grand_master';

export interface RankRow {
  key: RankKey;
  difficulty: number | null;
  accuracy: number; // needed accuracy (0–1)
  answers: number;
  correct: number;
  earned: boolean;
}

export interface RankInfo {
  current: RankKey | null;
  min_answers: number;
  ranks: RankRow[];
}

export interface Catalog {
  student: Student;
  points: number;
  tiers: TierState[];
  rank: RankInfo;
  subjects: Subject[];
}

export interface StatsDay {
  day: string; // YYYY-MM-DD
  answers: number;
  correct: number;
}

export interface StatsTopic {
  id: number;
  slug: string;
  tier: number;
  name_sk: string;
  name_en: string | null;
  answers: number;
  correct: number;
  days: StatsDay[];
  // from 014_topic_stats.sql (all time)
  points?: number;
  tier_unlocked?: boolean;
  progress?: Progress;
  trend?: [number, number][]; // [answer number, correct so far]
}

export interface Stats {
  tiers: TierState[];
  rank: RankInfo;
  topics: StatsTopic[];
  // 032: coding assignments; null/missing = no access and no submissions
  assignments?: AssignmentStats | null;
}

export interface AssignmentStats {
  points: number;
  max_points: number;
  done: number;
  tried: number;
  count: number;
  items: {
    id: number;
    slug: string;
    title_sk: string;
    title_en: string;
    score: number | null;
    max_points: number;
    submissions: number;
    submitted_at: string | null;
  }[];
}

export type Mode = 'learn' | 'test';

export interface Question {
  id: number;
  difficulty: number;
  body: string;
  answers: string[];
  body_en: string | null;
  answers_en: string[] | null;
}

export interface AnswerResult {
  correct: boolean;
  correct_index: number;
  explanation: string | null;
  explanation_en: string | null;
  points: number; // real point change: +5/+10/+20, 0, or a (floored) penalty
  total?: number; // student's new total (submit_answer only, from 013_scoring.sql)
  newly_unlocked: number[];
  newly_passed: boolean;
  progress: Progress;
}

// Guest mode (016_guest_mode.sql)
export interface GuestTopic {
  id: number;
  slug: string;
  subject_id: number;
  tier: number;
  name_sk: string;
  name_en: string | null;
  description_sk: string | null;
  description_en: string | null;
  question_count: number;
  unlock_min_answers: number;
  unlock_window: number | null;
  unlock_accuracy: number;
  levels: { level: number; difficulty: number; question_count: number }[];
}

export interface GuestSubject {
  id: number;
  slug: string;
  name_sk: string;
  name_en: string | null;
  topics: GuestTopic[];
}

export interface GuestCheck {
  correct: boolean;
  correct_index: number;
  explanation: string | null;
  explanation_en: string | null;
}

// Admin (017_admin.sql)
export interface AdminSession {
  token: string;
  expires_at: string;
}

export type AdminLoginResult =
  | { ok: true; token: string; expires_at: string }
  | { ok: false; error: 'invalid' | 'too_many_attempts' };

export interface AdminUser {
  email: string;
  name: string;
  class_id: number;
  class_name: string;
  is_active: boolean;
  student_id: string | null;
  logged_in: boolean;
  last_seen_at: string | null;
  answers: number;
  points: number;               // quiz + coding assignment points (032)
  assignment_points?: number;
}

export interface ClassInfo {
  id: number;
  name: string;
}

export interface ClassRow {
  class_id: number;
  name: string;
  points: number; // sum of all-time points of the class's roster students
  rank: number;
}

/** Final results of the competition (027_final_results.sql) – only answers before the cutoff. */
export interface FinalResults {
  cutoff: string; // first moment that no longer counts
  now: string;
  is_final: boolean; // now >= cutoff
  last: { answered_at: string; name: string; class: string }[]; // Bratislava time with ms, newest first
  top: { place: number; name: string; class: string; points: number; answers: number; correct: number }[];
  classes: { place: number; name: string; points: number; students: number; players: number }[];
}

// ------------------------------------------------------------------ coding assignments (030)

export interface AssignmentSummary {
  id: number;
  slug: string;
  title_sk: string;
  title_en: string;
  max_points: number;
  scenario_count: number;
  latest: { score: number; max_points: number; submitted_at: string } | null;
  submissions: number;
}

export interface AssignmentScenario {
  index: number;
  name_sk: string;
  name_en: string;
  input: string;
  expected: string;
  points: number;
}

/** One scenario of a saved submission, as stored by the server. */
export interface SubmissionRow {
  scenario: number;
  passed: boolean;
  points: number;
  actual: string;
}

export interface CompileError {
  line: number | null;
  column: number | null;
  id: string | null;
  message: string;
}

export interface Submission {
  id: number;
  assignment_id: number;
  submitted_at: string;
  compiled: boolean;
  score: number;
  max_points: number;
  passed: number;
  scenarios: number;
  // only with code (latest submission, one submission, submit result)
  code?: string;
  compile_errors?: CompileError[];
  results?: SubmissionRow[];
  // only in the submit result
  previous_score?: number | null;
  points_change?: number;
}

export interface AssignmentDetail {
  id: number;
  slug: string;
  title_sk: string;
  title_en: string;
  brief_sk: string;
  brief_en: string;
  max_points: number;
  time_limit_ms: number;
  scenarios: AssignmentScenario[];
  latest: Submission | null;
}
