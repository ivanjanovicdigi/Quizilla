<script lang="ts">
  let { name, size = 22 }: { name: string; size?: number } = $props();
  const paths: Record<string, string> = {
    home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z',
    trophy: 'M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4',
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
    lock: 'M6 11h12v10H6zM8 11V8a4 4 0 0 1 8 0v3',
    check: 'M5 12.5 10 17 19 7',
    x: 'M6 6l12 12M18 6 6 18',
    back: 'M15 5l-7 7 7 7',
    chevron: 'M9 5l7 7-7 7',
    star: 'm12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9z',
    play: 'M8 5v14l11-7z',
    globe: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9c-2.5-2.5-3.8-5.5-3.8-9S9.5 5.5 12 3z',
    unlock: 'M6 11h12v10H6zM8 11V8a4 4 0 0 1 7.5-2'
  };
  const filled = new Set(['star', 'play']);
</script>

<svg
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill={filled.has(name) ? 'currentColor' : 'none'}
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"><path d={paths[name] ?? ''} /></svg>
