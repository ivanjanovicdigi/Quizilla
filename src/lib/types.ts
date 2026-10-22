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

export interface Topic {
  id: number;
  slug: string;
  subject_id: number;
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

export interface Catalog {
  student: Student;
  points: number;
  subjects: Subject[];
}

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
