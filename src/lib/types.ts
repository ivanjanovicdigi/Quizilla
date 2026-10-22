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

export type MedalKey = 'bronze' | 'silver' | 'gold';

export interface Topic {
  id: number;
  slug: string;
  subject_id: number;
  tier: number;
  tier_unlocked?: boolean; // only from get_topic
  pass: Pass;
  medal?: MedalKey | null; // from 012_topic_medals.sql
  levels_cleared?: number;
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
}

export interface Stats {
  tiers: TierState[];
  rank: RankInfo;
  topics: StatsTopic[];
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
  points: number;
  newly_unlocked: number[];
  newly_passed: boolean;
  progress: Progress;
}

export interface ClassInfo {
  id: number;
  name: string;
}

export interface ClassRow {
  class_id: number;
  name: string;
  students: number;
  active_students: number;
  points: number;
  avg_points: number;
  rank: number;
}

export interface ClassRanking {
  class_id: number;
  class_name: string;
  students: { name: string; points: number; rank: number; is_me: boolean }[];
}
