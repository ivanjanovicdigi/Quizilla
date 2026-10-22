import { load, save } from './storage';

export type Lang = 'sk' | 'en';

const sk = {
  'app.tagline': 'Precvičuj, odomykaj úrovne a pomôž svojej triede vyhrať.',
  'nav.home': 'Domov',
  'nav.leaderboard': 'Rebríček',
  'nav.profile': 'Profil',

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
  'quiz.not_saved': 'Režim učenia – toto kolo sa neukladá.',

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

  'tier.name': 'Stupeň {n}',
  'tier.locked': 'Zamknuté – najprv splň všetky témy stupňa {n}',
  'tier.passed': 'Splnené témy: {p}/{n}',
  'tier.accuracy': 'Úspešnosť',
  'tier.locked_topic': 'Táto téma je v stupni {n}, ktorý je ešte zamknutý. Najprv splň všetky témy stupňa {prev}.',

  'medal.none': 'Zatiaľ bez medaily',
  'medal.bronze': 'Bronzová medaila',
  'medal.silver': 'Strieborná medaila',
  'medal.gold': 'Zlatá medaila',
  'medal.cleared': 'Zvládnuté úrovne: {c}/{n}',
  'medal.next': 'ďalšia medaila za zvládnutie úrovne {n}',
  'medal.all': 'všetky úrovne zvládnuté',

  'pass.title': 'Splnenie témy',
  'pass.rule': 'Tému splníš, keď v teste odpovieš na viac ako {min} otázok na úrovni {level} alebo vyššej a aspoň {pct} % bude správne.',
  'pass.answers': 'Odpovede (úroveň {level}+)',
  'pass.rate': 'Úspešnosť (treba {pct} %)',
  'pass.done': 'Téma splnená',
  'pass.new': 'Splnil si tému!',

  'mode.title': 'Režim',
  'mode.learn': 'Učenie',
  'mode.test': 'Test',
  'mode.learn_info': '{n} otázok · výsledky sa neukladajú',
  'mode.test_info': '{n} otázok · body, úrovne a štatistiky',
  'mode.learn_note': 'Režim učenia – odpovede sa nezapočítavajú.',

  'rank.none': 'Bez hodnosti',
  'rank.padawan': 'Padawan',
  'rank.jedi': 'Jedi',
  'rank.master': 'Majster',
  'rank.grand_master': 'Veľmajster',
  'rank.rule.padawan': '{pct} % správne na úrovni 1',
  'rank.rule.jedi': '{pct} % správne na úrovni 2',
  'rank.rule.master': '{pct} % správne na úrovni 3',
  'rank.rule.grand_master': '{pct} % správne na každej úrovni',
  'rank.min': 'Hodnosť sa počíta z testov vo všetkých témach, treba aspoň {n} odpovedí na úrovni.',
  'rank.progress': '{a}/{min} odpovedí · {pct}',

  'stats.title': 'Štatistiky',
  'stats.open': 'Moje štatistiky',
  'stats.open_info': 'Hodnosti, úspešnosť a graf zlepšovania',
  'stats.ranks': 'Hodnosti',
  'stats.tiers': 'Úspešnosť podľa stupňov',
  'stats.topics': 'Vývoj v témach',
  'stats.chart_info': 'Úspešnosť za každý deň, v ktorom si robil test. Prerušovaná čiara = {pct} % na splnenie témy.',
  'stats.no_data': 'Zatiaľ žiadne odpovede v teste.',
  'stats.days30': '30 dní',
  'stats.days90': '90 dní',
  'stats.all': 'Všetko',
  'stats.summary': '{a} odpovedí · {pct} %',
  'stats.tip': '{c}/{a} správne',
  'stats.table': 'Zobraziť tabuľku',
  'stats.day': 'Deň',
  'stats.answers': 'Odpovede',
  'stats.rate': 'Úspešnosť',

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
  'err.tier_locked': 'Tento stupeň je ešte zamknutý.',
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
  'quiz.not_saved': 'Learning mode – this round is not saved.',

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

  'tier.name': 'Tier {n}',
  'tier.locked': 'Locked – pass all topics of tier {n} first',
  'tier.passed': 'Topics passed: {p}/{n}',
  'tier.accuracy': 'Accuracy',
  'tier.locked_topic': 'This topic is in tier {n}, which is still locked. Pass all topics of tier {prev} first.',

  'medal.none': 'No medal yet',
  'medal.bronze': 'Bronze medal',
  'medal.silver': 'Silver medal',
  'medal.gold': 'Gold medal',
  'medal.cleared': 'Levels cleared: {c}/{n}',
  'medal.next': 'next medal for clearing level {n}',
  'medal.all': 'all levels cleared',

  'pass.title': 'Passing the topic',
  'pass.rule': 'You pass the topic after more than {min} test answers on level {level} or higher with at least {pct} % correct.',
  'pass.answers': 'Answers (level {level}+)',
  'pass.rate': 'Accuracy (need {pct} %)',
  'pass.done': 'Topic passed',
  'pass.new': 'You passed the topic!',

  'mode.title': 'Mode',
  'mode.learn': 'Learning',
  'mode.test': 'Test',
  'mode.learn_info': '{n} questions · results are not saved',
  'mode.test_info': '{n} questions · points, levels and statistics',
  'mode.learn_note': 'Learning mode – answers do not count.',

  'rank.none': 'No rank yet',
  'rank.padawan': 'Padawan',
  'rank.jedi': 'Jedi',
  'rank.master': 'Master',
  'rank.grand_master': 'Grand Master',
  'rank.rule.padawan': '{pct} % correct on level 1',
  'rank.rule.jedi': '{pct} % correct on level 2',
  'rank.rule.master': '{pct} % correct on level 3',
  'rank.rule.grand_master': '{pct} % correct on every level',
  'rank.min': 'Ranks count test answers in all topics; you need at least {n} answers on the level.',
  'rank.progress': '{a}/{min} answers · {pct}',

  'stats.title': 'Statistics',
  'stats.open': 'My statistics',
  'stats.open_info': 'Ranks, accuracy and progress chart',
  'stats.ranks': 'Ranks',
  'stats.tiers': 'Accuracy per tier',
  'stats.topics': 'Progress per topic',
  'stats.chart_info': 'Accuracy for each day you took a test. Dashed line = {pct} % needed to pass the topic.',
  'stats.no_data': 'No test answers yet.',
  'stats.days30': '30 days',
  'stats.days90': '90 days',
  'stats.all': 'All',
  'stats.summary': '{a} answers · {pct} %',
  'stats.tip': '{c}/{a} correct',
  'stats.table': 'Show table',
  'stats.day': 'Day',
  'stats.answers': 'Answers',
  'stats.rate': 'Accuracy',

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
  'err.tier_locked': 'This tier is still locked.',
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
