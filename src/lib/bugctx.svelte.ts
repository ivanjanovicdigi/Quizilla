// What the "Report a bug" button sends about the current quiz question.
// Quiz.svelte keeps this up to date and clears it when the quiz screen closes.
export interface QuizContext {
  topic_id: number;
  topic: string;
  level: number;
  difficulty: number;
  mode: string;
  question_id: number;
  question: string; // as shown (current UI language)
  selected: string | null; // selected answer as shown
  answered: boolean;
  correct: boolean | null;
  score: string; // round points, signed
  progress: string; // e.g. "4/10, 2 correct"
}

export const bugCtx = $state<{ quiz: QuizContext | null }>({ quiz: null });
