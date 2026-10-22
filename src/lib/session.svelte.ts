import type { Student } from './types';
import { load, save } from './storage';

const KEY = 'quizilla.student';

// guest = trying the app without the roster. Kept in memory only (never saved),
// so every new visit starts at the login page with nothing remembered.
export const session = $state<{ student: Student | null; guest: boolean }>({
  student: load<Student | null>(KEY, null),
  guest: false
});

export function setStudent(s: Student | null) {
  session.student = s;
  if (s) session.guest = false;
  save(KEY, s);
}

export function setGuest(on: boolean) {
  session.guest = on;
}
