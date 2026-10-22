import type { AdminSession, Student } from './types';
import { load, save } from './storage';

const KEY = 'quizilla.student';
const ADMIN_KEY = 'quizilla.admin';

function loadAdmin(): AdminSession | null {
  const a = load<AdminSession | null>(ADMIN_KEY, null);
  return a && Date.parse(a.expires_at) > Date.now() ? a : null;
}

// guest = trying the app without the roster. Kept in memory only (never saved),
// so every new visit starts at the login page with nothing remembered.
// admin = admin session token (017_admin.sql), remembered on the device until it expires.
export const session = $state<{ student: Student | null; guest: boolean; admin: AdminSession | null }>({
  student: load<Student | null>(KEY, null),
  guest: false,
  admin: loadAdmin()
});

export function setStudent(s: Student | null) {
  session.student = s;
  if (s) session.guest = false;
  save(KEY, s);
}

export function setGuest(on: boolean) {
  session.guest = on;
}

export function setAdmin(a: AdminSession | null) {
  session.admin = a;
  if (a) {
    session.guest = false;
    setStudent(null);
  }
  save(ADMIN_KEY, a);
}
