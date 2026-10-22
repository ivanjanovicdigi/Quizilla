import { load, save } from './storage';

export type Lang = 'sk' | 'en';

const sk = {
  'app.tagline': 'Precvičuj, odomykaj úrovne a pomôž svojej triede vyhrať.',
  'nav.home': 'Domov',
  'nav.leaderboard': 'Rebríček',
  'nav.profile': 'Profil',

  'reg.title': 'Vitaj v Quizille',
  'reg.name': 'Meno a priezvisko',
  'reg.name.ph': 'Ján Novák',
  'reg.email': 'Školský e-mail',
  'reg.class': 'Trieda',
  'reg.class.ph': 'Vyber triedu',
  'reg.submit': 'Začať',
  'reg.note': 'Tvoje meno a body uvidí učiteľ. Spolužiaci uvidia meno v skrátenej podobe (napr. Ján N.).',
  'reg.again': 'Už si sa prihlásil na inom zariadení? Zadaj rovnaký e-mail – body ostanú zachované.',

  'home.hello': 'Ahoj, {name}',
  'home.points': 'bodov',
  'home.class': 'Trieda {name}',
  'home.empty': 'Zatiaľ tu nie sú žiadne otázky. Skús to neskôr.',
  'home.levels': 'Úroveň {current} z {total}',
  'home.done': 'Dokončené',

  'topic.levels': 'Úrovne',
  'topic.level': 'Úroveň {n}',
  'topic.questions': '{n} otázok',
  'topic.play': 'Hrať',
  'topic.train': 'Trénovať',
  'topic.locked': 'Zamknuté – najprv splň úroveň {n}',
  'topic.rule': 'Ďalšiu úroveň odomkneš, keď odpovieš aspoň na {min} otázok a z posledných {window} odpovedí bude správne aspoň {need}.',
  'topic.answered': 'Odpovede',
  'topic.recent': 'Správne z posledných {window}',
  'topic.rule_all': 'Ďalšiu úroveň odomkneš, keď odpovieš aspoň na {min} otázok a aspoň {pct} % tvojich odpovedí na tejto úrovni bude správnych.',
  'topic.rate': 'Úspešnosť (treba {pct} %)',
  'topic.mastered': 'Zvládnuté otázky',
  'topic.met': 'Splnené',
  'topic.points': '{n} b.',

  'quiz.of': '{i} / {n}',
  'quiz.next': 'Ďalej',
  'quiz.finish': 'Výsledky',
  'quiz.correct': 'Správne!',
  'quiz.wrong': 'Nesprávne',
  'quiz.points': '+{n} bodov',
  'quiz.no_points': 'Táto otázka už bola započítaná',
  'quiz.unlocked': 'Odomkol si úroveň {n}!',
  'quiz.summary': 'Výsledok kola',
  'quiz.score': '{c} z {n} správne',
  'quiz.earned': 'Získané body: {n}',
  'quiz.again': 'Ďalšie kolo',
  'quiz.next_level': 'Hrať úroveň {n}',
  'quiz.back': 'Späť na tému',
  'quiz.quit': 'Ukončiť kolo',
  'quiz.empty': 'Na tejto úrovni nie sú žiadne otázky.',

  'lb.classes': 'Triedy',
  'lb.my_class': 'Moja trieda',
  'lb.week': '7 dní',
  'lb.all': 'Celkovo',
  'lb.avg': 'Ø {n} b. na žiaka',
  'lb.students': '{active}/{total} aktívnych',
  'lb.points': '{n} b.',
  'lb.how': 'Triedy sa porovnávajú podľa priemeru bodov na zaregistrovaného žiaka – každý sa počíta.',
  'lb.me': 'ty',
  'lb.empty': 'Zatiaľ žiadne výsledky.',

  'profile.title': 'Profil',
  'profile.language': 'Jazyk',
  'profile.logout': 'Odhlásiť z tohto zariadenia',
  'profile.logout.confirm': 'Naozaj sa chceš odhlásiť? Prihlásiš sa späť rovnakým e-mailom.',
  'profile.class_note': 'Triedu môže zmeniť len učiteľ.',

  'common.loading': 'Načítavam…',
  'common.retry': 'Skúsiť znova',
  'common.back': 'Späť',

  'err.network': 'Nepodarilo sa spojiť so serverom. Skontroluj pripojenie.',
  'err.server': 'Nastala chyba na serveri. Skús to znova.',
  'err.invalid_email': 'Zadaj platný školský e-mail (@{domain}).',
  'err.invalid_name': 'Zadaj meno (aspoň 2 znaky).',
  'err.invalid_class': 'Vyber triedu.',
  'err.unknown_student': 'Tvoj profil sa nenašiel, prihlás sa znova.',
  'err.level_locked': 'Táto úroveň je ešte zamknutá.',
  'err.unknown_topic': 'Téma neexistuje.',
  'err.unknown_level': 'Úroveň neexistuje.',
  'err.unknown_question': 'Otázka už nie je dostupná.',
  'err.invalid_choice': 'Neplatná odpoveď.'
};

type Key = keyof typeof sk;

const en: Record<Key, string> = {
  'app.tagline': 'Practise, unlock levels and help your class win.',
  'nav.home': 'Home',
  'nav.leaderboard': 'Leaderboard',
  'nav.profile': 'Profile',

  'reg.title': 'Welcome to Quizilla',
  'reg.name': 'Full name',
  'reg.name.ph': 'John Smith',
  'reg.email': 'School email',
  'reg.class': 'Class',
  'reg.class.ph': 'Choose your class',
  'reg.submit': 'Start',
  'reg.note': 'Your teacher will see your name and points. Classmates see a shortened name (e.g. John S.).',
  'reg.again': 'Signed in on another device before? Use the same email – your points stay.',

  'home.hello': 'Hi, {name}',
  'home.points': 'points',
  'home.class': 'Class {name}',
  'home.empty': 'There are no questions yet. Try again later.',
  'home.levels': 'Level {current} of {total}',
  'home.done': 'Completed',

  'topic.levels': 'Levels',
  'topic.level': 'Level {n}',
  'topic.questions': '{n} questions',
  'topic.play': 'Play',
  'topic.train': 'Practise',
  'topic.locked': 'Locked – complete level {n} first',
  'topic.rule': 'You unlock the next level after answering at least {min} questions with at least {need} of your last {window} answers correct.',
  'topic.answered': 'Answers',
  'topic.recent': 'Correct of last {window}',
  'topic.rule_all': 'You unlock the next level after answering at least {min} questions with at least {pct} % of your answers on this level correct.',
  'topic.rate': 'Success rate (need {pct} %)',
  'topic.mastered': 'Questions mastered',
  'topic.met': 'Completed',
  'topic.points': '{n} pts',

  'quiz.of': '{i} / {n}',
  'quiz.next': 'Next',
  'quiz.finish': 'Results',
  'quiz.correct': 'Correct!',
  'quiz.wrong': 'Wrong',
  'quiz.points': '+{n} points',
  'quiz.no_points': 'This question was already counted',
  'quiz.unlocked': 'You unlocked level {n}!',
  'quiz.summary': 'Round result',
  'quiz.score': '{c} of {n} correct',
  'quiz.earned': 'Points earned: {n}',
  'quiz.again': 'Next round',
  'quiz.next_level': 'Play level {n}',
  'quiz.back': 'Back to topic',
  'quiz.quit': 'End round',
  'quiz.empty': 'There are no questions on this level.',

  'lb.classes': 'Classes',
  'lb.my_class': 'My class',
  'lb.week': '7 days',
  'lb.all': 'All time',
  'lb.avg': 'Ø {n} pts per student',
  'lb.students': '{active}/{total} active',
  'lb.points': '{n} pts',
  'lb.how': 'Classes are ranked by average points per registered student – everyone counts.',
  'lb.me': 'you',
  'lb.empty': 'No results yet.',

  'profile.title': 'Profile',
  'profile.language': 'Language',
  'profile.logout': 'Sign out on this device',
  'profile.logout.confirm': 'Really sign out? You can sign back in with the same email.',
  'profile.class_note': 'Only your teacher can change your class.',

  'common.loading': 'Loading…',
  'common.retry': 'Try again',
  'common.back': 'Back',

  'err.network': 'Could not reach the server. Check your connection.',
  'err.server': 'Something went wrong on the server. Please try again.',
  'err.invalid_email': 'Enter a valid school email (@{domain}).',
  'err.invalid_name': 'Enter your name (at least 2 characters).',
  'err.invalid_class': 'Choose your class.',
  'err.unknown_student': 'Your profile was not found, please sign in again.',
  'err.level_locked': 'This level is still locked.',
  'err.unknown_topic': 'This topic does not exist.',
  'err.unknown_level': 'This level does not exist.',
  'err.unknown_question': 'This question is no longer available.',
  'err.invalid_choice': 'Invalid answer.'
};

const dicts: Record<Lang, Record<Key, string>> = { sk, en };
const LANG_KEY = 'quizilla.lang';

function initialLang(): Lang {
  const stored = load<Lang | null>(LANG_KEY, null);
  if (stored === 'sk' || stored === 'en') return stored;
  return navigator.language?.toLowerCase().startsWith('en') ? 'en' : 'sk';
}

export const i18n = $state<{ lang: Lang }>({ lang: initialLang() });

$effect.root(() => {
  $effect(() => {
    document.documentElement.lang = i18n.lang;
  });
});

export function setLang(lang: Lang) {
  i18n.lang = lang;
  save(LANG_KEY, lang);
}

export function t(key: Key, params: Record<string, string | number> = {}): string {
  const text = dicts[i18n.lang][key] ?? sk[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, p) => (p in params ? String(params[p]) : `{${p}}`));
}

/** Error code from the API → translated message. */
export function errorText(code: string, params: Record<string, string | number> = {}): string {
  const key = `err.${code}` as Key;
  return key in sk ? t(key, params) : t('err.server');
}

/** Pick localized content field (English falls back to Slovak). */
export function pick(skText: string | null | undefined, enText: string | null | undefined): string {
  return (i18n.lang === 'en' ? enText || skText : skText || enText) ?? '';
}
