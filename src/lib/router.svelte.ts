// Tiny hash router – works on GitHub Pages without server rewrites and keeps
// the phone's back gesture working.
export type Route =
  | { name: 'home' }
  | { name: 'topic'; topicId: number }
  | { name: 'quiz'; topicId: number; difficulty: number; mode: 'learn' | 'test' }
  | { name: 'leaderboard' }
  | { name: 'profile' }
  | { name: 'stats' };

function parse(hash: string): Route {
  const parts = hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  const num = (v: string | undefined) => (v && /^\d+$/.test(v) ? Number(v) : NaN);
  switch (parts[0]) {
    case 'topic': {
      const id = num(parts[1]);
      if (!isNaN(id)) return { name: 'topic', topicId: id };
      break;
    }
    case 'quiz': {
      const id = num(parts[1]);
      const d = num(parts[2]);
      const mode = parts[3] === 'learn' ? 'learn' : 'test';
      if (!isNaN(id) && !isNaN(d)) return { name: 'quiz', topicId: id, difficulty: d, mode };
      break;
    }
    case 'leaderboard':
      return { name: 'leaderboard' };
    case 'profile':
      return { name: 'profile' };
    case 'stats':
      return { name: 'stats' };
  }
  return { name: 'home' };
}

export const router = $state<{ route: Route }>({ route: parse(location.hash) });

window.addEventListener('hashchange', () => {
  router.route = parse(location.hash);
  window.scrollTo(0, 0);
});

export function go(path: string) {
  location.hash = path.startsWith('#') ? path : `#${path}`;
}
