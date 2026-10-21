import type { Student } from './types';
import { load, save } from './storage';

const KEY = 'quizilla.student';

export const session = $state<{ student: Student | null }>({
  student: load<Student | null>(KEY, null)
});

export function setStudent(s: Student | null) {
  session.student = s;
  save(KEY, s);
}
